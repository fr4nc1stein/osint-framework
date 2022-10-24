from sploitkit import *
from censys.search import CensysHosts
from dotenv import load_dotenv
import os
import json
import socket
from pygments import highlight, lexers, formatters

class censys(Module):
    """ This module load Censys
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    censys_appid = os.getenv('CENSYS_APPID')
    censys_secret = os.getenv('CENSYS_SECRET')   

    config = Config({
        Option(
            'HOST',
            "Provide your target HOST",
            True,
        ): str("hackerone.com"),
    })

    def prerun(self):
        if(self.censys_appid == "" or self.censys_secret == ""):
            print("Error: .env CENSYS_APPID or CENSYS_SECRET are empty")
            raise Exception("Fill in your key ID pair!")

    def run(self):
        censys_appid = self.censys_appid
        censys_secret = self.censys_secret
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
        raw_json = json.dumps(
            x,
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

