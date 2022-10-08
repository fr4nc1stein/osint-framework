from http.client import responses
from sploitkit import *
import os
import requests
from dotenv import load_dotenv
from pygments import highlight, lexers, formatters
import json

class fullhuntSearch(Module):
    """ This module find Host Information using Shodan
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    FULLHUNT_API = os.getenv('FULLHUNT_API_KEY')

    config = Config({
        Option(
            'DOMAIN',
            "Provide your target Domain",
            True,
        ): str("laet4x.com"),
    })    

    def run(self):
        domain = self.config.option('DOMAIN').value
        print("\n"" Analyzing '%s'..." % (domain))
        # Lookup an IP
        url = "https://fullhunt.io/api/v1/domain/"+domain+"/details"
        response=requests.get(url, headers={"X-API-KEY": self.FULLHUNT_API})
        r = json.loads(response.content)
        raw_json = json.dumps(
            r,
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

