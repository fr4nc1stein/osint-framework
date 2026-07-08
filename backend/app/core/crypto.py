"""
Symmetric authenticated encryption for secrets stored in PostgreSQL.
Uses pyaes (pure Python AES-CTR) + HMAC-SHA256 (stdlib) — no C extensions,
no AVX2/AVX512 requirement.

Envelope format (base64url):  VERSION(1) | IV(16) | HMAC(32) | CIPHERTEXT
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import struct

import pyaes


_VERSION = b"\x01"
_IV_LEN  = 16
_MAC_LEN = 32


def _get_keys() -> tuple[bytes, bytes]:
    """Derive separate AES and HMAC keys from APP_ENCRYPTION_KEY via HKDF-lite."""
    raw = os.getenv("APP_ENCRYPTION_KEY", "")
    if not raw:
        raise RuntimeError(
            "APP_ENCRYPTION_KEY is not set. "
            "Generate one with: python3 -c \"import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())\""
        )
    master = hashlib.sha256(raw.encode()).digest()  # 32 bytes
    aes_key  = hashlib.sha256(master + b"aes").digest()   # 32 bytes → AES-256
    hmac_key = hashlib.sha256(master + b"mac").digest()   # 32 bytes
    return aes_key, hmac_key


def encrypt(plaintext: str) -> str:
    """Encrypt plaintext string, return base64url token."""
    aes_key, hmac_key = _get_keys()
    iv = secrets.token_bytes(_IV_LEN)

    ctr   = pyaes.Counter(initial_value=int.from_bytes(iv, "big"))
    aes   = pyaes.AESModeOfOperationCTR(aes_key, counter=ctr)
    ciphertext = aes.encrypt(plaintext.encode("utf-8"))

    mac_input = _VERSION + iv + ciphertext
    mac = hmac.new(hmac_key, mac_input, hashlib.sha256).digest()

    payload = _VERSION + iv + mac + ciphertext
    return base64.urlsafe_b64encode(payload).decode()


def decrypt(token: str) -> str:
    """Decrypt a token produced by encrypt(), return plaintext string."""
    aes_key, hmac_key = _get_keys()
    try:
        payload = base64.urlsafe_b64decode(token.encode())
    except Exception as exc:
        raise ValueError("Invalid token encoding") from exc

    if len(payload) < 1 + _IV_LEN + _MAC_LEN + 1:
        raise ValueError("Token too short")

    version    = payload[:1]
    iv         = payload[1 : 1 + _IV_LEN]
    stored_mac = payload[1 + _IV_LEN : 1 + _IV_LEN + _MAC_LEN]
    ciphertext = payload[1 + _IV_LEN + _MAC_LEN:]

    if version != _VERSION:
        raise ValueError(f"Unknown token version: {version!r}")

    mac_input    = version + iv + ciphertext
    expected_mac = hmac.new(hmac_key, mac_input, hashlib.sha256).digest()
    if not hmac.compare_digest(stored_mac, expected_mac):
        raise ValueError("Decryption failed — key mismatch or corrupted token")

    ctr = pyaes.Counter(initial_value=int.from_bytes(iv, "big"))
    aes = pyaes.AESModeOfOperationCTR(aes_key, counter=ctr)
    return aes.decrypt(ciphertext).decode("utf-8")


def mask_hint(value: str) -> str:
    """Return last 4 chars prefixed with dots for UI display."""
    if not value or len(value) < 4:
        return "****"
    return f"...{value[-4:]}"
