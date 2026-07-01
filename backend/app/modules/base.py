"""Base OSINT Module Class"""
from abc import ABC, abstractmethod
from typing import ClassVar, List
import httpx
from app.schemas.module import DiscoveryResult


class BaseOSINTModule(ABC):
    """Abstract base class for all OSINT modules"""
    
    MODULE_ID: ClassVar[str]
    DISPLAY_NAME: ClassVar[str]
    DESCRIPTION: ClassVar[str]
    CATEGORY: ClassVar[str]  # domain, ip, email, blockchain, geolocation, etc.
    ACCEPTS: ClassVar[List[str]]  # Indicator kinds this module accepts
    REQUIRES_API_KEY: ClassVar[bool] = False
    API_KEY_ENV_VAR: ClassVar[str] = ""
    
    @abstractmethod
    async def execute(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """
        Execute OSINT collection and return discoveries
        
        Args:
            target: The target value to investigate
            kind: The indicator kind (domain, ip, email, etc.)
            http_client: Shared async HTTP client
            config: Module configuration
            
        Returns:
            List of DiscoveryResult objects
        """
        pass
    
    def validate_config(self, config: dict) -> bool:
        """Validate module configuration"""
        import os
        if self.REQUIRES_API_KEY:
            return bool(os.getenv(self.API_KEY_ENV_VAR))
        return True
    
    def is_configured(self) -> bool:
        """Check if module is properly configured"""
        import os
        if self.REQUIRES_API_KEY:
            return bool(os.getenv(self.API_KEY_ENV_VAR))
        return True
