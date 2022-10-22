from email import header
import os, re
import requests, json
from datetime import date
from base64 import b64encode
from terminaltables import SingleTable
from sploitkit import Module, Config, Option
from dateutil.relativedelta import relativedelta
from pygments import highlight, lexers, formatters


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

    def run(self):
        API_NAME = os.getenv('WIGLE_API_NAME')
        API_KEY = os.getenv('WIGLE_API_TOKEN')
        userToken = f"{API_NAME}:{API_KEY}"
        BasicAuth = b64encode(userToken.encode("utf-8"))
        BasicAuth = BasicAuth.decode("utf-8")

        wirelessIdentifier = self.config.option('WIRELESS_IDENTIFIER').value

        print("Searching...")

        wifi_url, entryType = self._requestWifi(wirelessIdentifier)
        r = requests.get(wifi_url, headers = { 'Authorization': 'Basic ' + BasicAuth, 'Accept': 'application/json'})
        self._debug(r.json())

        tableData = []
        rep = r.json()

        title = f"{entryType}: {wirelessIdentifier}"
        th = ('Seen','Location','Coordinates')
        tableData.append(th)

        if rep["resultCount"] == 0:
            print("No entries found.")
            return

        for el in rep["results"]:
            tableData.append((el["lastupdt"],f"{el['road']} {el['city']} {el['region']}",f"{el['trilat']} , {el['trilong']}"))

        self._print(title,tableData)

    def _formatCheck(self,entry):
        if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", entry.lower()):
            return "MAC"
        else:
            return "SSID"

    def _print(self,title,data):        
        table = SingleTable(data,title)
        print("\n" + table.table)

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

    def _last6Mon(self):
        six_months = date.today() + relativedelta(months=+6)
        ret = six_months.strftime("%Y%m%d") + "000000"
        return ret

    def _requestWifi(self,id):
        url = "https://api.wigle.net/api/v2/network/search?onlymine=false&"
        url += url + f"latrange1={self.PH['Lat1']}&latrange2={self.PH['Lat2']}&longrange1={self.PH['Lon1']}&longrange2={self.PH['Lon2']}"
        url += f"&lastupdt={self._last6Mon()}&freenet=false&paynet=false&country=PH"
        
        entryType = self._formatCheck(id)
        if entryType == "MAC":
            url += f"&netid={id}"
        elif entryType == "SSID":
            url += f"&ssid={id}"

        return url, entryType