"""IP Geolocation Module"""
from typing import List, ClassVar
import httpx

from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module
from app.schemas.module import DiscoveryResult


@register_module
class IPGeolocationModule(BaseOSINTModule):
    """Geolocate IP address using ip-api.com (free, no key required)"""
    
    MODULE_ID: ClassVar[str] = "ip_geolocation"
    DISPLAY_NAME: ClassVar[str] = "IP Geolocation"
    DESCRIPTION: ClassVar[str] = "Get geographic location and ISP information for an IP"
    CATEGORY: ClassVar[str] = "ip"
    ACCEPTS: ClassVar[List[str]] = ["ip"]
    REQUIRES_API_KEY: ClassVar[bool] = False
    
    async def execute(
        self,
        target: str,
        kind: str,
        *,
        http_client: httpx.AsyncClient,
        config: dict
    ) -> List[DiscoveryResult]:
        """Execute IP geolocation"""
        results = []
        
        try:
            url = f"http://ip-api.com/json/{target}"
            response = await http_client.get(url, timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    # Add location node
                    if data.get('country'):
                        city = data.get('city', 'Unknown')
                        country = data.get('country')
                        location = f"{city}, {country}"
                        
                        results.append(DiscoveryResult(
                            src_value=target,
                            src_kind="ip",
                            dst_value=location,
                            dst_kind="location",
                            relationship="located_in",
                            confidence=0.85,
                            evidence={
                                "city": city,
                                "country": country,
                                "region": data.get('regionName'),
                                "lat": data.get('lat'),
                                "lon": data.get('lon'),
                                "timezone": data.get('timezone'),
                                "source": "ip-api.com"
                            },
                            source_module=self.MODULE_ID
                        ))
                    
                    # Add ISP node
                    if data.get('isp'):
                        results.append(DiscoveryResult(
                            src_value=target,
                            src_kind="ip",
                            dst_value=data['isp'],
                            dst_kind="isp",
                            relationship="provided_by",
                            confidence=0.9,
                            evidence={
                                "isp": data['isp'],
                                "org": data.get('org'),
                                "as": data.get('as'),
                                "source": "ip-api.com"
                            },
                            source_module=self.MODULE_ID
                        ))
        
        except Exception as e:
            pass
        
        return results
