"""Shodan IP Lookup Module"""
import os
import httpx
from typing import List
from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class ShodanLookupModule(BaseOSINTModule):
    """Look up IP information using Shodan"""
    
    MODULE_ID = "shodan_lookup"
    DISPLAY_NAME = "Shodan IP Lookup"
    DESCRIPTION = "Get open ports, services, and vulnerabilities for an IP"
    CATEGORY = "ip"
    ACCEPTS = ["ip"]
    REQUIRES_KEY = True
    
    def validate_config(self, config: dict) -> bool:
        """Validate Shodan API key is present"""
        api_key = os.getenv("SHODAN_API_KEY")
        return bool(api_key)
    
    async def execute(
        self,
        target: str,
        kind: str,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute Shodan IP lookup"""
        
        api_key = os.getenv("SHODAN_API_KEY")
        if not api_key:
            return []
        
        discoveries = []
        
        try:
            url = f"https://api.shodan.io/shodan/host/{target}"
            params = {"key": api_key}
            
            response = await http_client.get(url, params=params, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract organization/ISP
                org = data.get("org")
                if org:
                    discoveries.append(DiscoveryResult(
                        src_value=target,
                        src_kind="ip",
                        dst_value=org,
                        dst_kind="organization",
                        relationship="BELONGS_TO",
                        confidence=0.90,
                        evidence={
                            "source": "shodan",
                            "organization": org
                        },
                        source_module=self.MODULE_ID
                    ))
                
                # Extract open ports and services
                for service in data.get("data", [])[:10]:  # Limit to 10
                    port = service.get("port")
                    product = service.get("product", "unknown")
                    version = service.get("version", "")
                    
                    service_name = f"{product} {version}".strip() if version else product
                    
                    discoveries.append(DiscoveryResult(
                        src_value=target,
                        src_kind="ip",
                        dst_value=f"{target}:{port}",
                        dst_kind="service",
                        relationship="RUNS_SERVICE",
                        confidence=0.95,
                        evidence={
                            "source": "shodan",
                            "port": port,
                            "service": service_name,
                            "banner": service.get("data", "")[:200]
                        },
                        source_module=self.MODULE_ID
                    ))
                
                # Extract hostnames
                hostnames = data.get("hostnames", [])
                for hostname in hostnames[:5]:
                    discoveries.append(DiscoveryResult(
                        src_value=target,
                        src_kind="ip",
                        dst_value=hostname,
                        dst_kind="domain",
                        relationship="RESOLVES_TO",
                        confidence=0.92,
                        evidence={
                            "source": "shodan"
                        },
                        source_module=self.MODULE_ID
                    ))
                
                # Extract vulnerabilities
                vulns = data.get("vulns", [])
                for vuln in vulns[:5]:
                    discoveries.append(DiscoveryResult(
                        src_value=target,
                        src_kind="ip",
                        dst_value=vuln,
                        dst_kind="vulnerability",
                        relationship="HAS_VULNERABILITY",
                        confidence=0.88,
                        evidence={
                            "source": "shodan",
                            "cve": vuln
                        },
                        source_module=self.MODULE_ID
                    ))
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print(f"Shodan API key invalid")
            elif e.response.status_code == 404:
                print(f"No Shodan data for {target}")
            else:
                print(f"Shodan error: {e}")
        except Exception as e:
            print(f"Shodan lookup error for {target}: {e}")
        
        return discoveries
