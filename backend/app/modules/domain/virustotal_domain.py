"""VirusTotal Domain Lookup Module"""
import os
import httpx
from typing import List, ClassVar
from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class VirusTotalDomainModule(BaseOSINTModule):
    """Scan domain reputation and relationships using VirusTotal"""
    
    MODULE_ID: ClassVar[str] = "virustotal_domain"
    DISPLAY_NAME: ClassVar[str] = "VirusTotal Domain Scan"
    DESCRIPTION: ClassVar[str] = "Check domain reputation, detected URLs, and relationships"
    CATEGORY: ClassVar[str] = "domain"
    ACCEPTS: ClassVar[List[str]] = ["domain"]
    REQUIRES_API_KEY: ClassVar[bool] = True
    API_KEY_ENV_VAR: ClassVar[str] = "VIRUSTOTAL_API_KEY"
    
    # Rate limiting (VirusTotal free tier: 4 requests/minute)
    RATE_LIMIT_API: ClassVar[str] = "virustotal"
    CACHE_TTL: ClassVar[int] = 7200  # 2 hours
    
    async def execute(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute VirusTotal domain lookup"""
        
        api_key = os.getenv(self.API_KEY_ENV_VAR)
        if not api_key:
            return []
        
        discoveries = []
        
        try:
            # Get domain report
            url = f"https://www.virustotal.com/api/v3/domains/{target}"
            headers = {"x-apikey": api_key}
            
            response = await http_client.get(url, headers=headers, timeout=15.0)
            
            if response.status_code == 200:
                data = response.json()
                attributes = data.get("data", {}).get("attributes", {})
                
                # Extract reputation score
                reputation = attributes.get("reputation", 0)
                last_analysis_stats = attributes.get("last_analysis_stats", {})
                malicious = last_analysis_stats.get("malicious", 0)
                suspicious = last_analysis_stats.get("suspicious", 0)
                
                # Create reputation indicator
                if malicious > 0 or suspicious > 0:
                    discoveries.append(DiscoveryResult(
                        src_value=target,
                        src_kind="domain",
                        dst_value=f"vt_reputation_{reputation}",
                        dst_kind="reputation",
                        relationship="HAS_REPUTATION",
                        confidence=0.90,
                        evidence={
                            "source": "virustotal",
                            "malicious": malicious,
                            "suspicious": suspicious,
                            "reputation": reputation
                        },
                        source_module=self.MODULE_ID
                    ))
                
                # Extract categories
                categories = attributes.get("categories", {})
                for category_source, category_name in list(categories.items())[:5]:
                    discoveries.append(DiscoveryResult(
                        src_value=target,
                        src_kind="domain",
                        dst_value=category_name,
                        dst_kind="category",
                        relationship="CATEGORIZED_AS",
                        confidence=0.85,
                        evidence={
                            "source": "virustotal",
                            "category_source": category_source
                        },
                        source_module=self.MODULE_ID
                    ))
                
                # Extract related domains (subdomains)
                # Note: This requires additional API call, skipping for now to save quota
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print(f"VirusTotal API key invalid")
            elif e.response.status_code == 404:
                print(f"Domain not found in VirusTotal: {target}")
            else:
                print(f"VirusTotal error: {e}")
        except Exception as e:
            print(f"VirusTotal lookup error for {target}: {e}")
        
        return discoveries
