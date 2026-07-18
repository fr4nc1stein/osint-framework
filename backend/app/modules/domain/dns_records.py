"""DNS Records Lookup Module"""
from typing import List, ClassVar
import dns.resolver
import httpx

from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class DNSRecordsModule(BaseOSINTModule):
    """Resolve DNS records (A, AAAA, MX, TXT) for a domain"""
    
    MODULE_ID: ClassVar[str] = "dns_records"
    DISPLAY_NAME: ClassVar[str] = "DNS Records Lookup"
    DESCRIPTION: ClassVar[str] = "Resolve A, AAAA, MX, TXT, NS records for a domain"
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
        """Execute DNS lookup"""
        results = []
        
        # A records (IPv4)
        try:
            answers = dns.resolver.resolve(target, 'A', lifetime=5)
            for rdata in list(answers)[:10]:  # Limit to 10
                results.append(DiscoveryResult(
                    src_value=target,
                    src_kind="domain",
                    dst_value=str(rdata),
                    dst_kind="ip",
                    relationship="resolves_to",
                    confidence=1.0,
                    evidence={"record_type": "A"},
                    source_module=self.MODULE_ID
                ))
        except Exception:
            pass  # DNS lookup can fail, continue
        
        # AAAA records (IPv6)
        try:
            answers = dns.resolver.resolve(target, 'AAAA', lifetime=5)
            for rdata in list(answers)[:5]:
                results.append(DiscoveryResult(
                    src_value=target,
                    src_kind="domain",
                    dst_value=str(rdata),
                    dst_kind="ip",
                    relationship="resolves_to",
                    confidence=1.0,
                    evidence={"record_type": "AAAA"},
                    source_module=self.MODULE_ID
                ))
        except Exception:
            pass
        
        # MX records (Mail servers)
        try:
            mx_answers = dns.resolver.resolve(target, 'MX', lifetime=5)
            for rdata in list(mx_answers)[:5]:
                mx_host = str(rdata.exchange).rstrip('.')
                results.append(DiscoveryResult(
                    src_value=target,
                    src_kind="domain",
                    dst_value=mx_host,
                    dst_kind="host",
                    relationship="mail_server",
                    confidence=1.0,
                    evidence={"record_type": "MX", "priority": rdata.preference},
                    source_module=self.MODULE_ID
                ))
        except Exception:
            pass
        
        # NS records (Name servers)
        try:
            ns_answers = dns.resolver.resolve(target, 'NS', lifetime=5)
            for rdata in list(ns_answers)[:5]:
                ns_host = str(rdata).rstrip('.')
                results.append(DiscoveryResult(
                    src_value=target,
                    src_kind="domain",
                    dst_value=ns_host,
                    dst_kind="host",
                    relationship="name_server",
                    confidence=1.0,
                    evidence={"record_type": "NS"},
                    source_module=self.MODULE_ID
                ))
        except Exception:
            pass
        
        return results
