import requests
import json
from requests_oauthlib import OAuth1
from sploitkit import Module, Config, Option, Command
from dotenv import load_dotenv
from terminaltables import SingleTable


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
        url = f"https://blockchain.info/rawaddr/{address}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"API error: {response.status_code} - {response.text}")
            return
        r = response.json()
        # Example response:
        # {
        #   "hash160": "660d4ef3a743e3e696ad990364e555c271ad504b",
        #   "address": "1AJbsFZ64EpEfS5UAjAfcUG8pH8Jn3rn1F",
        #   "n_tx": 17,
        #   "n_unredeemed": 2,
        #   "total_received": 1031350000,
        #   "total_sent": 931250000,
        #   "final_balance": 100100000,
        #   "txs": [ ... ]
        # }
        infos = ("ADDRESS", r.get('address', 'N/A'))
        TABLE_DATA.append(infos)
        infos = ("TX COUNT", r.get('n_tx', 0))
        TABLE_DATA.append(infos)
        infos = ("UNREDEEMED TX", r.get('n_unredeemed', 0))
        TABLE_DATA.append(infos)
        infos = ("RECEIVED", r.get('total_received', 0) / 100000000)
        TABLE_DATA.append(infos)
        infos = ("SENT", r.get('total_sent', 0) / 100000000)
        TABLE_DATA.append(infos)
        infos = ("BALANCE", r.get('final_balance', 0) / 100000000)
        TABLE_DATA.append(infos)
        table = SingleTable(TABLE_DATA, "BITCOIN BALANCE")
        print("\n" + table.table)