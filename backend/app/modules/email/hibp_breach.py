"""Have I Been Pwned Breach Check Module"""
import httpx
from typing import List, ClassVar
from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class HIBPBreachModule(BaseOSINTModule):
    """Check if email has been in data breaches using Have I Been Pwned"""
    
    MODULE_ID: ClassVar[str] = "hibp_breach"
    DISPLAY_NAME: ClassVar[str] = "Have I Been Pwned"
    DESCRIPTION: ClassVar[str] = "Check email addresses against known data breaches"
    CATEGORY: ClassVar[str] = "email"
    ACCEPTS: ClassVar[List[str]] = ["email"]
    REQUIRES_API_KEY: ClassVar[bool] = False  # Free tier available
    
    # No strict rate limiting for HIBP, but be respectful
    CACHE_TTL: ClassVar[int] = 86400  # 24 hours
    
    async def execute(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute HIBP breach check"""
        
        discoveries = []
        
        try:
            # HIBP API v3 - breaches for account
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{target}"
            headers = {
                "User-Agent": "OSIF-Framework",
                "hibp-api-key": ""  # Free tier doesn't need key for breach check
            }
            
            response = await http_client.get(
                url,
                headers=headers,
                timeout=10.0,
                params={"truncateResponse": "false"}
            )
            
            if response.status_code == 200:
                breaches = response.json()
                
                for breach in breaches[:10]:  # Limit to 10 most recent
                    breach_name = breach.get("Name", "Unknown")
                    breach_date = breach.get("BreachDate", "Unknown")
                    data_classes = breach.get("DataClasses", [])
                    
                    discoveries.append(DiscoveryResult(
                        src_value=target,
                        src_kind="email",
                        dst_value=breach_name,
                        dst_kind="breach",
                        relationship="FOUND_IN_BREACH",
                        confidence=0.95,
                        evidence={
                            "source": "haveibeenpwned",
                            "breach_date": breach_date,
                            "data_classes": data_classes[:5],  # Limit data classes
                            "verified": breach.get("IsVerified", False)
                        },
                        source_module=self.MODULE_ID
                    ))
            
            elif response.status_code == 404:
                # No breaches found - this is good!
                print(f"No breaches found for {target}")
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f"HIBP rate limit exceeded")
            else:
                print(f"HIBP error: {e}")
        except Exception as e:
            print(f"HIBP lookup error for {target}: {e}")
        
        return discoveries
