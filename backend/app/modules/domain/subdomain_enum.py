"""Subdomain Enumeration via Certificate Transparency"""
from typing import List, ClassVar
import httpx
import dns.resolver

from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class SubdomainEnumModule(BaseOSINTModule):
    """Enumerate subdomains using Certificate Transparency logs (crt.sh)"""
    
    MODULE_ID: ClassVar[str] = "subdomain_enum"
    DISPLAY_NAME: ClassVar[str] = "Subdomain Enumeration"
    DESCRIPTION: ClassVar[str] = "Find subdomains via Certificate Transparency logs"
    CATEGORY: ClassVar[str] = "domain"
    ACCEPTS: ClassVar[List[str]] = ["domain"]
    REQUIRES_API_KEY: ClassVar[bool] = False
    
    async def execute(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute subdomain enumeration"""
        results = []
        seen_hosts = set()
        
        try:
            # Query crt.sh for certificates
            crt_url = f"https://crt.sh/?q=%.{target}&output=json"
            response = await http_client.get(crt_url, timeout=15.0)
            
            if response.status_code == 200:
                crt_data = response.json()
                
                for cert in crt_data[:100]:  # Limit to 100 certificates
                    if 'name_value' in cert:
                        names = cert['name_value'].split('\n')
                        
                        for name in names:
                            name = name.strip().lower()
                            
                            # Only add valid subdomains
                            if (name and 
                                target in name and 
                                name not in seen_hosts and 
                                name != target and
                                not name.startswith('*')):  # Skip wildcards
                                
                                seen_hosts.add(name)
                                
                                # Determine node type
                                node_type = "subdomain" if name.endswith(f".{target}") else "host"
                                
                                results.append(DiscoveryResult(
                                    src_value=target,
                                    src_kind="domain",
                                    dst_value=name,
                                    dst_kind=node_type,
                                    relationship="has_subdomain" if node_type == "subdomain" else "has_certificate",
                                    confidence=0.95,
                                    evidence={
                                        "source": "crt.sh",
                                        "issuer": cert.get('issuer_name', '')[:100]
                                    },
                                    source_module=self.MODULE_ID
                                ))
                                
                                # Limit total results
                                if len(seen_hosts) >= 50:
                                    break
                    
                    if len(seen_hosts) >= 50:
                        break
        
        except Exception as e:
            # Log error but don't fail
            pass
        
        return results
