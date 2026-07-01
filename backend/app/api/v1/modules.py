"""Module Registry API Endpoints"""
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.modules.registry import get_all_modules, get_module, PLUGIN_REGISTRY, discover_modules
from app.schemas.module import ModuleInfo

router = APIRouter()

NODE_MODULE_MAP = {
    "ip":       ["ip_geolocation", "abuseipdb", "shodan_lookup"],
    "domain":   ["dns_records", "whois_lookup", "subdomain_enum", "virustotal_domain", "urlscan_lookup"],
    "email":    ["hibp_breach", "email_domain"],
    "username": ["hibp_breach"],
    "phone":    [],
    "bitcoin":  [],
}


@router.get("", response_model=List[ModuleInfo])
async def list_modules(category: str | None = None):
    """List all available OSINT modules"""
    modules = get_all_modules()
    if category:
        modules = [m for m in modules if m.category == category]
    return modules


@router.get("/suggest")
async def suggest_modules(node_type: str = "domain"):
    """Return applicable modules for a given node type (must be before /{module_id})"""
    if not PLUGIN_REGISTRY:
        discover_modules()
    result = []
    for mod_id in NODE_MODULE_MAP.get(node_type.lower(), []):
        cls = PLUGIN_REGISTRY.get(mod_id)
        if cls:
            result.append({
                "module_id": cls.MODULE_ID,
                "name": cls.DISPLAY_NAME,
                "description": cls.DESCRIPTION,
                "requires_api_key": cls.REQUIRES_API_KEY,
            })
    return result


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
