import os
from base64 import b64encode
import requests
from sploitkit import Module, Config, Option

class GeoWireless(Module):
    """ This module searches the location of the given MAC Address.
    https://wigle.net
    Author:  cadeath
    Version: 1.0
    """
    config = Config({
        Option(
            "WIRELESS_IDENTIFIER",
            "This could be MAC Address or SSID",
            True
        ): str("XX:XX:XX:XX:XX:XX|SSID"),
        Option(
            "COUNTRY",
            "Country where to lookup",
            False,
        ): str("PH")
    })

    PH = {
        "Lat1":"19.2855",
        "Lat2":"5.0405",
        "Lon1":"115.8137",
        "Lon2":"126.9333"
    }
    
    WIGLE_URL = "https://api.wigle.net/api/v2/network/search?onlymine=false&"

    def run(self):
        API_NAME = os.getenv('WIGLE_API_NAME')
        API_KEY = os.getenv('WIGLE_API_TOKEN')
        userToken = f"{API_NAME}:{API_KEY}"
        BasicAuth = b64encode(userToken.encode("utf-8"))
        BasicAuth = BasicAuth.decode("utf-8")

        print("Searching...")
        url = self.WIGLE_URL + f"latrange1={self.PH['Lat1']}&latrange2={self.PH['Lat2']}&longrange1={self.PH['Lon1']}&longrange2={self.PH['Lon2']}&freenet=false&paynet=false&country=PH"
        
        # url = "https://api.wigle.net/api/v2/profile/user"
        r = requests.get(url, headers = { 'Authorization': 'Basic ' + BasicAuth, 'Accept': 'application/json'})
        print(r.json())