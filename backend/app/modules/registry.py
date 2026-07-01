"""Module Registry with Auto-Discovery"""
import importlib
import pkgutil
from typing import Dict, Type, List
from app.modules.base import BaseOSINTModule
from app.schemas.module import ModuleInfo


# Global registry
PLUGIN_REGISTRY: Dict[str, Type[BaseOSINTModule]] = {}


def register_module(cls: Type[BaseOSINTModule]):
    """Decorator to auto-register modules"""
    if not hasattr(cls, 'MODULE_ID'):
        raise TypeError(f"Module {cls.__name__} must define MODULE_ID")
    
    PLUGIN_REGISTRY[cls.MODULE_ID] = cls
    return cls


def discover_modules() -> Dict[str, Type[BaseOSINTModule]]:
    """
    Auto-discover all modules in modules/ directory
    
    Walks through all Python files in the modules package and imports them,
    triggering the @register_module decorator to populate the registry.
    """
    import app.modules as modules_package
    
    # Clear registry
    PLUGIN_REGISTRY.clear()
    
    # Walk through all submodules
    for importer, modname, ispkg in pkgutil.walk_packages(
        modules_package.__path__,
        prefix=f"{modules_package.__name__}."
    ):
        # Skip base and registry modules
        if modname.endswith('.base') or modname.endswith('.registry'):
            continue
        
        try:
            importlib.import_module(modname)
        except Exception as e:
            print(f"Warning: Failed to import module {modname}: {e}")
    
    print(f"✅ Discovered {len(PLUGIN_REGISTRY)} OSINT modules")
    return PLUGIN_REGISTRY


def get_all_modules() -> List[ModuleInfo]:
    """Get all registered modules as ModuleInfo objects"""
    if not PLUGIN_REGISTRY:
        discover_modules()
    
    modules = []
    for module_id, module_class in PLUGIN_REGISTRY.items():
        modules.append(ModuleInfo(
            module_id=module_class.MODULE_ID,
            display_name=module_class.DISPLAY_NAME,
            description=module_class.DESCRIPTION,
            category=module_class.CATEGORY,
            accepts=module_class.ACCEPTS,
            requires_api_key=module_class.REQUIRES_API_KEY,
            api_key_configured=module_class().is_configured()
        ))
    
    return modules


def get_module(module_id: str) -> ModuleInfo | None:
    """Get module info by ID"""
    if not PLUGIN_REGISTRY:
        discover_modules()
    
    module_class = PLUGIN_REGISTRY.get(module_id)
    if not module_class:
        return None
    
    return ModuleInfo(
        module_id=module_class.MODULE_ID,
        display_name=module_class.DISPLAY_NAME,
        description=module_class.DESCRIPTION,
        category=module_class.CATEGORY,
        accepts=module_class.ACCEPTS,
        requires_api_key=module_class.REQUIRES_API_KEY,
        api_key_configured=module_class().is_configured()
    )


def get_module_class(module_id: str) -> Type[BaseOSINTModule] | None:
    """Get module class by ID"""
    if not PLUGIN_REGISTRY:
        discover_modules()
    
    return PLUGIN_REGISTRY.get(module_id)
