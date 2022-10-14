from unittest import result
from sploitkit import Module, Config, Option, Command
from dotenv import load_dotenv
import os
from terminaltables import SingleTable
import json
import requests
from pygments import highlight, lexers, formatters

class ethereumBalance(Module):
    """ This module find Wallet Balance with other tokens
    Author:  laet4x
    Version: 1.0
    """

    config = Config({
        Option(
            'ADDRESS',
            "Provide your target address",
            True,
        ): str("0xbFCC250e1d5603d144c7ce99834403B0452d2644"),
    })

     
    def run(self):
        TABLE_DATA = []
        TABLE_DATAS = []
        address = self.config.option('ADDRESS').value
        url = "https://api.ethplorer.io/getAddressInfo/"+ address + "?apiKey=freekey"
        response=requests.get(url)
        r = json.loads(response.content)
        infos = ("ADDRESS", r['address'])
        TABLE_DATA.append(infos)

        infos = ("BALANCE", r['ETH']['balance'])
        TABLE_DATA.append(infos)

        infos = ("COUNT TXS", r['countTxs'])
        TABLE_DATA.append(infos)

        result = r['tokens']
        infos = ("TOKEN", "BALANCE", "TOTAL IN", "TOTAL OUT")
        TABLE_DATAS.append(infos)
        count = 1
        for key in result:
            infos = (key['tokenInfo']['symbol'], key['balance'], key['totalIn'], key['totalOut'])
            TABLE_DATAS.append(infos)
            count +=1

        table = SingleTable(TABLE_DATA, "ETH")
        print("\n"+table.table)    

        table = SingleTable(TABLE_DATAS, "TOKEN")
        print("\n"+table.table)   

class ethereumNameIdentifier(Module):
    """ This module find ENS of Address
    Author:  laet4x
    Version: 1.0
    

    osif blockchain(ethereum_name_identifier) > run  

    The ENS of `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` is vitalik.eth.

    eosif blockchain(ethereum_name_identifier) >  
    """

    config = Config({
        Option(
            'ADDRESS',
            "Provide your target address or ENS",
            True,
        ): str("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"),
    })

    def run(self):
        TABLE_DATA = []
        address = self.config.option('ADDRESS').value
        url = "https://api.ensideas.com/ens/resolve/"+ address
        response=requests.get(url)
        r = json.loads(response.content)

        infos = ("ADDRESS", r['address'])
        TABLE_DATA.append(infos)

        infos = ("NAME", r['name'])
        TABLE_DATA.append(infos)

        infos = ("AVATAR", r['avatar'])
        TABLE_DATA.append(infos)

        table = SingleTable(TABLE_DATA, "ETH")
        print("\n"+table.table)   



