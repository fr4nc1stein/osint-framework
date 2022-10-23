import os
import json
import requests
from base64 import b64encode
from terminaltables import SingleTable
from sploitkit import Module, Config, Option
from pygments import highlight, lexers, formatters

class GeoBluetooth(Module):
    """ This module searches the information like BSSID, Location, and Encryption of the given SSID.
    https://wigle.net
    Author:  cadeath
    Version: 1.0
    """

    config = Config({
        Option(
            "BLUETOOTH_BSSID",
            "Enter the Bluetooth Device BSSID",
            True
        ): str("XX:XX:XX:XX")
    })
    
    def run(self):
        API_NAME = os.getenv('WIGLE_API_NAME')
        API_KEY = os.getenv('WIGLE_API_TOKEN')
        userToken = f"{API_NAME}:{API_KEY}"
        BasicAuth = b64encode(userToken.encode("utf-8"))
        BasicAuth = BasicAuth.decode("utf-8")
        authHeaders = { 'Authorization': 'Basic ' + BasicAuth, 'Accept': 'application/json'}

        blueTooth = self.config.option('BLUETOOTH_BSSID').value

        print ("Searching...")

        btURL = "https://api.wigle.net/api/v2/bluetooth/detail?netid=" + blueTooth
        r = requests.get(btURL,headers=authHeaders)
        rep = r.json()

        # print(self._debug(rep))

        btInfo = []
        btLocation = []

        # Header Init
        th = ('Key', 'Value')
        btInfo.append(th)

        th = ('Seen','Coordinates','Accuracy')
        btLocation.append(th)
        
        if len(rep['results']) < 1:
            print ("Result not found.")

        for el in rep["results"]:
            td = ('Name',el['name'])
            btInfo.append(td)

            td = ('LastUpdate',el['lastupdt'])
            btInfo.append(td)

            td = ('Coordinates',f"{el['trilat']} , {el['trilong']}")
            btInfo.append(td)
            
            td = ('Location',f"{el['road']} {el['city']}, {el['country']}")
            btInfo.append(td)

            for loc in el["locationData"]:
                td = (loc['lastupdt'],f"{loc['latitude']} , {loc['longitude']} Alt: {loc['alt']}ft",loc['accuracy'])
                btLocation.append(td)

        title = f"BSSID: {blueTooth}"
        info = SingleTable(btInfo,title)

        title = "Location Information"
        location = SingleTable(btLocation,title)


        print("\n" + info.table)
        print("\n" + location.table)

    def _debug(self,jsr):
        raw_json = json.dumps(
            jsr,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')
        )
        colorful = highlight(
            raw_json,
            lexer=lexers.JsonLexer(),
            formatter=formatters.TerminalFormatter(),
        )
        print(colorful)