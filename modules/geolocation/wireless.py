import os
import requests
from sploitkit import Module, Config, Option

class SearchTempMobile(Module):
    """ This module searches the location of the given MAC Address.
    wigle.net
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
        ): str("PH"),
    })

    API_NAME = self.config.option('WIGLE_API_NAME').value
    API_KEY = self.config.option('WIGLE_API_TOKEN').value
    
    def run(self):
        r = requests.get("")
    