"""Base OSINT Module Class"""
from abc import ABC, abstractmethod
from typing import ClassVar, List, Optional
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
    
    # Caching configuration
    CACHE_ENABLED: ClassVar[bool] = True
    CACHE_TTL: ClassVar[int] = 3600  # 1 hour default
    
    # Rate limiting configuration (API name from rate_limiter.py)
    RATE_LIMIT_API: ClassVar[Optional[str]] = None
    
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
    
    async def execute_with_cache(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict,
        cache_service=None,
        use_cache: bool = True
    ) -> List[DiscoveryResult]:
        """
        Execute module with caching support
        
        This method wraps execute() with caching logic
        """
        
        # Check cache if enabled
        if use_cache and self.CACHE_ENABLED and cache_service:
            cached_results = await cache_service.get(self.MODULE_ID, target, kind)
            if cached_results:
                # Convert cached dicts back to DiscoveryResult objects
                return [DiscoveryResult(**r) for r in cached_results]
        
        # Execute module
        results = await self.execute(
            target,
            kind,
            http_client=http_client,
            config=config
        )
        
        # Cache results if enabled
        if use_cache and self.CACHE_ENABLED and cache_service and results:
            # Convert DiscoveryResult objects to dicts for caching
            cache_data = [r.model_dump() for r in results]
            await cache_service.set(
                self.MODULE_ID,
                target,
                kind,
                cache_data,
                ttl=self.CACHE_TTL
            )
        
        return results
