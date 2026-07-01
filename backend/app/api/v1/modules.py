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
