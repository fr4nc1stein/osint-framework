"""WHOIS Domain Lookup Module"""
import httpx
from typing import List
from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class WhoisLookupModule(BaseOSINTModule):
    """Look up WHOIS information for a domain"""
    
    MODULE_ID = "whois_lookup"
    DISPLAY_NAME = "WHOIS Lookup"
    DESCRIPTION = "Retrieve domain registration and ownership information"
    CATEGORY = "domain"
    ACCEPTS = ["domain"]
    REQUIRES_KEY = False
    
    async def execute(
        self,
        target: str,
        kind: str,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute WHOIS lookup using whoisxmlapi.com free tier"""
        
        discoveries = []
        
        try:
            # Use whoisxmlapi.com free API (limited)
            url = f"https://www.whoisxmlapi.com/whoisserver/WhoisService"
            params = {
                "domainName": target,
                "outputFormat": "JSON"
            }
            
            response = await http_client.get(url, params=params, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                whois_record = data.get("WhoisRecord", {})
                
                # Extract registrar
                registrar_name = whois_record.get("registrarName")
                if registrar_name:
                    discoveries.append(DiscoveryResult(
                        src_value=target,
                        src_kind="domain",
                        dst_value=registrar_name,
                        dst_kind="organization",
                        relationship="REGISTERED_WITH",
                        confidence=0.95,
                        evidence={
                            "source": "whois",
                            "registrar": registrar_name
                        },
                        source_module=self.MODULE_ID
                    ))
                
                # Extract name servers
                name_servers = whois_record.get("nameServers", {}).get("hostNames", [])
                for ns in name_servers[:5]:  # Limit to 5
                    discoveries.append(DiscoveryResult(
                        src_value=target,
                        src_kind="domain",
                        dst_value=ns.lower(),
                        dst_kind="nameserver",
                        relationship="USES_NAMESERVER",
                        confidence=0.98,
                        evidence={
                            "source": "whois"
                        },
                        source_module=self.MODULE_ID
                    ))
                
                # Extract registrant organization
                registrant = whois_record.get("registrant", {})
                org = registrant.get("organization")
                if org:
                    discoveries.append(DiscoveryResult(
                        src_value=target,
                        src_kind="domain",
                        dst_value=org,
                        dst_kind="organization",
                        relationship="OWNED_BY",
                        confidence=0.85,
                        evidence={
                            "source": "whois",
                            "registrant": org
                        },
                        source_module=self.MODULE_ID
                    ))
        
        except Exception as e:
            print(f"WHOIS lookup error for {target}: {e}")
        
        return discoveries
