"""Evidence object storage helpers."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import re
import uuid

import anyio
from fastapi import HTTPException, UploadFile, status
from minio import Minio
from minio.error import S3Error
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

ALLOWED_UPLOAD_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/json",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


@dataclass
class StoredEvidenceFile:
    file_name: str
    file_mime_type: str
    file_size: int
    file_sha256: str
    storage_backend: str
    storage_key: str
    thumbnail_storage_key: str | None = None


@dataclass
class RetrievedEvidenceFile:
    data: bytes
    content_type: str
    file_name: str


class EvidenceStorageService:
    """MinIO-backed storage for evidence originals and derived previews."""

    def __init__(self) -> None:
        endpoint = settings.S3_ENDPOINT_URL.removeprefix("http://").removeprefix("https://")
        secure = settings.S3_ENDPOINT_URL.startswith("https://")
        self.client = Minio(
            endpoint,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=secure,
            region=settings.S3_REGION,
        )
        self.bucket = settings.S3_BUCKET

    async def save_upload(self, case_id: uuid.UUID, evidence_id: uuid.UUID, upload: UploadFile) -> StoredEvidenceFile:
        content_type = upload.content_type or "application/octet-stream"
        if content_type not in ALLOWED_UPLOAD_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported evidence file type: {content_type}",
            )

        data = await upload.read()
        size = len(data)
        if size == 0:
            raise HTTPException(status_code=400, detail="Uploaded evidence file is empty")
        if size > settings.EVIDENCE_MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Uploaded evidence file exceeds the configured size limit")

        safe_name = self._safe_filename(upload.filename or "evidence")
        digest = sha256(data).hexdigest()
        storage_key = f"cases/{case_id}/evidence/{evidence_id}/original/{safe_name}"

        await self._put_object(storage_key, data, content_type)

        thumbnail_key = None
        thumbnail = self._make_thumbnail(data, content_type)
        if thumbnail:
            thumbnail_key = f"cases/{case_id}/evidence/{evidence_id}/thumbnail/{self._thumbnail_filename(safe_name)}"
            await self._put_object(thumbnail_key, thumbnail, "image/webp")

        return StoredEvidenceFile(
            file_name=safe_name,
            file_mime_type=content_type,
            file_size=size,
            file_sha256=digest,
            storage_backend="s3",
            storage_key=storage_key,
            thumbnail_storage_key=thumbnail_key,
        )

    async def get_file(self, key: str, content_type: str, file_name: str) -> RetrievedEvidenceFile:
        data = await anyio.to_thread.run_sync(self._get_object_bytes, key)
        return RetrievedEvidenceFile(data=data, content_type=content_type, file_name=file_name)

    async def delete_file(self, key: str | None) -> None:
        if not key:
            return
        await anyio.to_thread.run_sync(self._delete_object, key)

    async def _put_object(self, key: str, data: bytes, content_type: str) -> None:
        await anyio.to_thread.run_sync(self._put_object_sync, key, data, content_type)

    def _put_object_sync(self, key: str, data: bytes, content_type: str) -> None:
        try:
            self.client.put_object(
                self.bucket,
                key,
                BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
        except S3Error as exc:
            raise HTTPException(status_code=503, detail=f"Evidence storage upload failed: {exc.code}") from exc

    def _get_object_bytes(self, key: str) -> bytes:
        response = None
        try:
            response = self.client.get_object(self.bucket, key)
            return response.read()
        except S3Error as exc:
            raise HTTPException(status_code=404, detail="Evidence file not found in storage") from exc
        finally:
            if response:
                response.close()
                response.release_conn()

    def _delete_object(self, key: str) -> None:
        try:
            self.client.remove_object(self.bucket, key)
        except S3Error:
            # Evidence metadata deletion should not be blocked by an already-missing object.
            return

    @staticmethod
    def _safe_filename(filename: str) -> str:
        cleaned = SAFE_FILENAME_RE.sub("_", filename).strip("._")
        return cleaned[:180] or "evidence"

    @staticmethod
    def _thumbnail_filename(filename: str) -> str:
        base = filename.rsplit(".", 1)[0] if "." in filename else filename
        return f"{base[:160]}.webp"

    @staticmethod
    def _make_thumbnail(data: bytes, content_type: str) -> bytes | None:
        if content_type not in IMAGE_MIME_TYPES:
            return None
        try:
            with Image.open(BytesIO(data)) as image:
                image.thumbnail((420, 420))
                output = BytesIO()
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGB")
                image.save(output, format="WEBP", quality=82)
                return output.getvalue()
        except (UnidentifiedImageError, OSError):
            return None


def get_evidence_storage() -> EvidenceStorageService:
    return EvidenceStorageService()
