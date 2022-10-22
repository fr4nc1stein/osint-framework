import os, re
from base64 import b64encode
import requests
from terminaltables import SingleTable
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

    def _formatCheck(self,entry):
        if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", entry.lower()):
            return "MAC"
        else:
            return "SSID"

    def _print(self):
        title = "MAC: XX:XX:XX:XX"
        td_data = [
            ['2022-10-23','X, Y'],
            ['2022-10-22','X, Y'],
            ['2022-10-21','X, Y'],
        ]

        td_data = []
        header = ('Seen','Location')
        td_data.append(header)

        d = ('2022-10-23','X, Y')
        td_data.append(d)
        d = ('2022-10-22','X, Y')
        td_data.append(d)
        d = ('2022-10-21','X, Y')
        td_data.append(d)

        
        table = SingleTable(td_data,title)
        print("\n" + table.table)




    def run(self):
        self._print()
        return

        API_NAME = os.getenv('WIGLE_API_NAME')
        API_KEY = os.getenv('WIGLE_API_TOKEN')
        userToken = f"{API_NAME}:{API_KEY}"
        BasicAuth = b64encode(userToken.encode("utf-8"))
        BasicAuth = BasicAuth.decode("utf-8")

        wirelessIdentifier = self.config.option('WIRELESS_IDENTIFIER').value

        print("Searching...")
        url = self.WIGLE_URL + f"latrange1={self.PH['Lat1']}&latrange2={self.PH['Lat2']}&longrange1={self.PH['Lon1']}&longrange2={self.PH['Lon2']}&freenet=false&paynet=false&country=PH"
        
        if self._formatCheck(wirelessIdentifier) == "MAC":
            url += f"&netid={wirelessIdentifier}"
        elif self._formatCheck(wirelessIdentifier) == "SSID":
            url += f"&ssid={wirelessIdentifier}"

        # url = "https://api.wigle.net/api/v2/profile/user"
        r = requests.get(url, headers = { 'Authorization': 'Basic ' + BasicAuth, 'Accept': 'application/json'})
        print(r.json())

        self._print()