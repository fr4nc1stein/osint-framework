"""AbuseIPDB Reputation Check Module"""
from typing import List, ClassVar
import os
import httpx

from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class AbuseIPDBModule(BaseOSINTModule):
    """Check IP reputation using AbuseIPDB"""
    
    MODULE_ID: ClassVar[str] = "abuseipdb"
    DISPLAY_NAME: ClassVar[str] = "AbuseIPDB Reputation"
    DESCRIPTION: ClassVar[str] = "Check IP address reputation and abuse reports"
    CATEGORY: ClassVar[str] = "ip"
    ACCEPTS: ClassVar[List[str]] = ["ip"]
    REQUIRES_API_KEY: ClassVar[bool] = True
    API_KEY_ENV_VAR: ClassVar[str] = "ABUSEIPDB_API_KEY"
    PROVIDER_ID: ClassVar[str] = "abuseipdb"
    
    async def execute(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute AbuseIPDB check"""
        results = []
        
        api_key = config.get('api_key') or os.getenv('ABUSEIPDB_API_KEY')
        if not api_key:
            return results
        
        try:
            url = 'https://api.abuseipdb.com/api/v2/check'
            headers = {
                'Accept': 'application/json',
                'Key': api_key
            }
            params = {
                'ipAddress': target,
                'maxAgeInDays': 90,
                'verbose': False
            }
            
            response = await http_client.get(url, headers=headers, params=params, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                abuse_score = data.get('abuseConfidenceScore', 0)
                
                # Only create threat node if abuse score is significant
                if abuse_score > 25:
                    threat_level = "High Risk" if abuse_score >= 75 else "Medium Risk"
                    
                    results.append(DiscoveryResult(
                        src_value=target,
                        src_kind="ip",
                        dst_value=f"{threat_level} ({abuse_score}%)",
                        dst_kind="threat",
                        relationship="has_reputation",
                        confidence=abuse_score / 100.0,
                        evidence={
                            "abuse_score": abuse_score,
                            "total_reports": data.get('totalReports', 0),
                            "is_whitelisted": data.get('isWhitelisted', False),
                            "usage_type": data.get('usageType', 'Unknown'),
                            "threat_level": threat_level,
                            "source": "abuseipdb"
                        },
                        source_module=self.MODULE_ID
                    ))
        
        except Exception as e:
            pass
        
        return results
