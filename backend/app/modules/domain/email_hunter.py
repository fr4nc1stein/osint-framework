"""Email Discovery Module using Tomba API"""
from typing import List, ClassVar
import os
import httpx

from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class EmailHunterModule(BaseOSINTModule):
    """Find email addresses for a domain using Tomba API"""
    
    MODULE_ID: ClassVar[str] = "email_hunter"
    DISPLAY_NAME: ClassVar[str] = "Email Hunter (Tomba)"
    DESCRIPTION: ClassVar[str] = "Discover email addresses associated with a domain"
    CATEGORY: ClassVar[str] = "domain"
    ACCEPTS: ClassVar[List[str]] = ["domain"]
    REQUIRES_API_KEY: ClassVar[bool] = True
    API_KEY_ENV_VAR: ClassVar[str] = "TOMBA_API_KEY"
    PROVIDER_ID: ClassVar[str] = "tomba"
    
    async def execute(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute email discovery"""
        results = []
        
        api_key = config.get('api_key') or os.getenv('TOMBA_API_KEY')
        secret_key = config.get('secret_key') or os.getenv('TOMBA_SECRET_KEY')

        if not api_key or not secret_key:
            return results  # Skip if not configured
        
        try:
            # Tomba domain search API
            url = "https://api.tomba.io/v1/domain-search"
            params = {
                "domain": target,
                "limit": 20
            }
            headers = {
                "X-Tomba-Key": api_key,
                "X-Tomba-Secret": secret_key
            }
            
            response = await http_client.get(url, params=params, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and 'emails' in data['data']:
                    for email_data in data['data']['emails'][:20]:
                        email = email_data.get('email')
                        
                        if email:
                            results.append(DiscoveryResult(
                                src_value=target,
                                src_kind="domain",
                                dst_value=email,
                                dst_kind="email",
                                relationship="has_email",
                                confidence=0.9,
                                evidence={
                                    "first_name": email_data.get('first_name'),
                                    "last_name": email_data.get('last_name'),
                                    "position": email_data.get('position'),
                                    "department": email_data.get('department'),
                                    "source": "tomba"
                                },
                                source_module=self.MODULE_ID
                            ))
        
        except Exception as e:
            # API errors are non-fatal
            pass
        
        return results
