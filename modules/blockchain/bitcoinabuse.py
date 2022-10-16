import requests
import json
import os
from requests_oauthlib import OAuth1
from sploitkit import Module, Config, Option, Command
from dotenv import load_dotenv
from terminaltables import SingleTable
from pygments import highlight, lexers, formatters

class bitcoinAbuse(Module):
    """ This module find bitcoin addres use by ransomware or fraudsters
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    API = os.getenv('BITCOINABUSE_API_KEY')
    config = Config({
        Option(
            'ADDRESS',
            "Provide your target address",
            True,
        ): str("1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s"),
    })
     
    def run(self):
        TABLE_DATA = []
        TABLE_RECENT = []
        address = self.config.option('ADDRESS').value
        url = "https://www.bitcoinabuse.com/api/reports/check?address=" + address + "&api_token=" + self.API
        response=requests.get(url)
        r = json.loads(response.content)
        
        infos = ("ADDRESS", r['address'])
        TABLE_DATA.append(infos)

        infos = ("COUNT", r['count'])
        TABLE_DATA.append(infos)

        infos = ("FIRST SEEN", r['first_seen'])
        TABLE_DATA.append(infos)

        infos = ("LAST SEEN", r['last_seen'])
        TABLE_DATA.append(infos)

        table = SingleTable(TABLE_DATA, "BITCOIN ABUSE")
        print("\n"+table.table)  

        recent = r['recent']
        print("\n""RECENT REPORT ON ADDRESS: '%s'...." % (address))
        raw_json = json.dumps(
            recent,
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


    
  