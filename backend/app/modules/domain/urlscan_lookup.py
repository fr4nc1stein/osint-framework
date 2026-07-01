"""URLScan.io Domain/URL Analysis Module"""
import os
import httpx
from typing import List, ClassVar
from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class URLScanModule(BaseOSINTModule):
    """Analyze domain/URL using URLScan.io"""
    
    MODULE_ID: ClassVar[str] = "urlscan_lookup"
    DISPLAY_NAME: ClassVar[str] = "URLScan.io Analysis"
    DESCRIPTION: ClassVar[str] = "Scan and analyze URLs/domains for security threats"
    CATEGORY: ClassVar[str] = "domain"
    ACCEPTS: ClassVar[List[str]] = ["domain", "url"]
    REQUIRES_API_KEY: ClassVar[bool] = False  # Public API available
    
    # URLScan rate limit: 1 request per 2 seconds
    RATE_LIMIT_API: ClassVar[str] = "urlscan"
    CACHE_TTL: ClassVar[int] = 3600  # 1 hour
    
    async def execute(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute URLScan lookup"""
        
        discoveries = []
        
        try:
            # Search for existing scans of this domain
            search_url = "https://urlscan.io/api/v1/search/"
            params = {
                "q": f"domain:{target}",
                "size": 5  # Get last 5 scans
            }
            
            response = await http_client.get(
                search_url,
                params=params,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                for result in results:
                    page = result.get("page", {})
                    task = result.get("task", {})
                    
                    # Extract IPs
                    ip = page.get("ip")
                    if ip:
                        discoveries.append(DiscoveryResult(
                            src_value=target,
                            src_kind="domain",
                            dst_value=ip,
                            dst_kind="ip",
                            relationship="RESOLVES_TO",
                            confidence=0.92,
                            evidence={
                                "source": "urlscan",
                                "scan_date": task.get("time", "unknown")
                            },
                            source_module=self.MODULE_ID
                        ))
                    
                    # Extract server info
                    server = page.get("server")
                    if server:
                        discoveries.append(DiscoveryResult(
                            src_value=target,
                            src_kind="domain",
                            dst_value=server,
                            dst_kind="server",
                            relationship="RUNS_SERVER",
                            confidence=0.88,
                            evidence={
                                "source": "urlscan"
                            },
                            source_module=self.MODULE_ID
                        ))
                    
                    # Extract ASN
                    asn = page.get("asn")
                    if asn:
                        discoveries.append(DiscoveryResult(
                            src_value=target,
                            src_kind="domain",
                            dst_value=f"AS{asn}",
                            dst_kind="asn",
                            relationship="HOSTED_IN_ASN",
                            confidence=0.90,
                            evidence={
                                "source": "urlscan",
                                "asnname": page.get("asnname", "")
                            },
                            source_module=self.MODULE_ID
                        ))
                    
                    # Check for malicious verdict
                    verdicts = result.get("verdicts", {})
                    if verdicts.get("overall", {}).get("malicious"):
                        discoveries.append(DiscoveryResult(
                            src_value=target,
                            src_kind="domain",
                            dst_value="malicious",
                            dst_kind="threat",
                            relationship="FLAGGED_AS",
                            confidence=0.85,
                            evidence={
                                "source": "urlscan",
                                "categories": verdicts.get("overall", {}).get("categories", [])
                            },
                            source_module=self.MODULE_ID
                        ))
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f"URLScan rate limit exceeded")
            else:
                print(f"URLScan error: {e}")
        except Exception as e:
            print(f"URLScan lookup error for {target}: {e}")
        
        return discoveries
