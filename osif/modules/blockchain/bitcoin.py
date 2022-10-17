import requests
import json
from requests_oauthlib import OAuth1
from sploitkit import Module, Config, Option, Command
from dotenv import load_dotenv
from terminaltables import SingleTable


class bitcoinBalance(Module):
    """ This module find bitcoin addres balance
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'ADDRESS',
            "Provide your target address",
            True,
        ): str("1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s"),
    })
     
    def run(self):
        TABLE_DATA = []
        address = self.config.option('ADDRESS').value
        url = "https://chain.api.btc.com/v3/address/"+ address
        response=requests.get(url)
        r = json.loads(response.content)
        data = r['data']
        infos = ("ADDRESS", address)
        TABLE_DATA.append(infos)
        count = 1
        for key in data:
            if key == 'received':
                data[key] = data[key] / 100000000
            if key == 'sent': 
                data[key] = data[key] / 100000000
            if key == 'balance': 
                data[key] = data[key] / 100000000    
            infos = (key, data[key])
            TABLE_DATA.append(infos)
            count +=1
        table = SingleTable(TABLE_DATA, "BALANCE")
        print("\n"+table.table)

class bitcoinBalance(Module):
    """ This module find bitcoin addres use by ransomware or fraudsters
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'ADDRESS',
            "Provide your target address",
            True,
        ): str("1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s"),
    })
     
    def run(self):
        TABLE_DATA = []
        address = self.config.option('ADDRESS').value
        url = "https://chain.api.btc.com/v3/address/"+ address
        response=requests.get(url)
        r = json.loads(response.content)
        data = r['data']
        infos = ("ADDRESS", address)
        TABLE_DATA.append(infos)
        count = 1
        for key in data:
            if key == 'received':
                data[key] = data[key] / 100000000
            if key == 'sent': 
                data[key] = data[key] / 100000000
            if key == 'balance': 
                data[key] = data[key] / 100000000    
            infos = (key, data[key])
            TABLE_DATA.append(infos)
            count +=1
        table = SingleTable(TABLE_DATA, "BALANCE")
        print("\n"+table.table)    


    
  