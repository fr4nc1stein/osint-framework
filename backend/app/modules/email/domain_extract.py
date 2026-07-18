"""Email Domain Extraction Module"""
from typing import List, ClassVar
import httpx

from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class EmailDomainModule(BaseOSINTModule):
    """Extract domain from email address"""
    
    MODULE_ID: ClassVar[str] = "email_domain"
    DISPLAY_NAME: ClassVar[str] = "Email Domain Extraction"
    DESCRIPTION: ClassVar[str] = "Extract and link domain from email address"
    CATEGORY: ClassVar[str] = "email"
    ACCEPTS: ClassVar[List[str]] = ["email"]
    REQUIRES_API_KEY: ClassVar[bool] = False
    
    async def execute(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute email domain extraction"""
        results = []
        
        try:
            if '@' in target:
                domain = target.split('@')[1]
                
                results.append(DiscoveryResult(
                    src_value=target,
                    src_kind="email",
                    dst_value=domain,
                    dst_kind="domain",
                    relationship="belongs_to",
                    confidence=1.0,
                    evidence={"extracted_from": "email"},
                    source_module=self.MODULE_ID
                ))
        
        except Exception:
            pass
        
        return results
