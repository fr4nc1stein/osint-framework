from sploitkit import *
from dotenv import load_dotenv
import os
from terminaltables import SingleTable
from censys.search import CensysHosts
import json
import socket

class censys(Module):
    load_dotenv()
    """ This module load Censys
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'HOST',
            "Provide your target HOST",
            True,
        ): str("hackerone.com"),
    })    

    def run(self):
        censys_appid = os.getenv('CENSYS_APPID')
        censys_secret = os.getenv('CENSYS_SECRET')
        host = self.config.option('HOST').value
        try:
            socket.inet_aton(host)
            print('Valid IP Address')
        except socket.error:
            print("Invalid Host Converting to IP")
            host = socket.gethostbyname(host)
        
        print("\n"" Analyzing '%s'..." % (host))
        h = CensysHosts(censys_appid,censys_secret)
        x = h.view(host)
        print(json.dumps(
            x,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')
        ))
        

