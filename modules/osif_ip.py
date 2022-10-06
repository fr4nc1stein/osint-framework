from sploitkit import *
import requests
import json
from terminaltables import SingleTable

class osifIp(Module):
    """ This module find leaked info using ihavebeenpwnd
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'IP',
            "Provide your target IP",
            True,
        ): str("122.53.219.50"),
    })    

    def run(self):
        dataList = []
        ip = self.config.option('IP').value

        print("\n"" Locating '%s'..." % (ip))

        TABLE_DATA = []

        url = "http://ip-api.com/json/"
        data = requests.get(url+ip).content.decode('utf-8')
        values = json.loads(data)

        status = values['status']

        if status != "success":
            print(warning+" Adresse IP invalide.")

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
            infos = ("Maps", "https://www.google.fr/maps?q="+localisation)
            TABLE_DATA.append(infos)

            table = SingleTable(TABLE_DATA, ip)
            print("\n"+table.table)

