from sploitkit import *
import requests
import json
from terminaltables import SingleTable

class iplookup(Module):
    """ This module find IP information
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'HOST_IP',
            "Provide your target IP",
            True,
        ): str("136.158.41.95"),
    })    

    def run(self):
        dataList = []
        ip = self.config.option('HOST_IP').value

        print("\n"" Locating '%s'..." % (ip))

        TABLE_DATA = []

        url = "http://ip-api.com/json/"
        data = requests.get(url+ip).content.decode('utf-8')
        values = json.loads(data)

        status = values['status']

        if status != "success":
            print(" Address IP invalid.")

        else:
            infos = ("IP", ip)
            TABLE_DATA.append(infos)
            infos = ("ISP", values['isp'])
            TABLE_DATA.append(infos)
            infos = ("Organisation", values['org'])
            TABLE_DATA.append(infos)
            infos = ("Pays", values['country'])
            TABLE_DATA.append(infos)
            infos = ("Region", values['regionName'])
            TABLE_DATA.append(infos)
            infos = ("Ville", values['city'])
            TABLE_DATA.append(infos)
            infos = ("Code Postal", values['zip'])
            TABLE_DATA.append(infos)
            localisation = str(values['lat'])+', '+str(values['lon'])
            infos = ("Localisation", localisation)
            TABLE_DATA.append(infos)
            infos = ("Maps", "https://www.google.com/maps?q="+localisation)
            TABLE_DATA.append(infos)

            table = SingleTable(TABLE_DATA, ip)
            print("\n"+table.table)

