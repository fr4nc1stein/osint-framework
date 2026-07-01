"""Module Registry API Endpoints"""
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.modules.registry import get_all_modules, get_module
from app.schemas.module import ModuleInfo

router = APIRouter()


@router.get("", response_model=List[ModuleInfo])
async def list_modules(category: str | None = None):
    """List all available OSINT modules"""
    modules = get_all_modules()
    if category:
        modules = [m for m in modules if m.category == category]
    return modules


@router.get("/suggest")
async def suggest_modules(node_type: str = "domain", configured_only: bool = False):
    """Return applicable modules for a given node type (must be before /{module_id})"""
    normalized_type = node_type.lower()
    modules = [
        module
        for module in get_all_modules()
        if normalized_type in [accepted.lower() for accepted in module.accepts]
    ]

    if configured_only:
        modules = [module for module in modules if module.api_key_configured]

    return [
        {
            "module_id": module.module_id,
            "name": module.display_name,
            "display_name": module.display_name,
            "description": module.description,
            "category": module.category,
            "accepts": module.accepts,
            "requires_api_key": module.requires_api_key,
            "api_key_configured": module.api_key_configured,
        }
        for module in modules
    ]


@router.get("/{module_id}", response_model=ModuleInfo)
async def get_module_info(module_id: str):
    """Get module details by ID"""
    module = get_module(module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {module_id} not found"
        )
    return module
