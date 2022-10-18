from sploitkit import *
import os
from dotenv import load_dotenv
from shodan import Shodan
from pygments import highlight, lexers, formatters
import json

class shodanSearch(Module):
    """ This module find Host Information using Shodan
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    SHODAN_API = os.getenv('SHODAN_API_KEY')
    API = Shodan(SHODAN_API)

    config = Config({
        Option(
            'HOST_IP',
            "Provide your target IP",
            True,
        ): str("136.158.41.95"),
    })    

    def run(self):
        host = self.config.option('HOST_IP').value
        print("\n""Analyzing '%s'..." % (host))
        # Lookup an IP
        ipinfo = self.API.host(host)
        raw_json = json.dumps(
            ipinfo,
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

