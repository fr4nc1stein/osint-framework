from sploitkit import *
import requests
import json
from terminaltables import SingleTable

class dns(Module):
    """ This module find DNS information
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'DOMAIN',
            "Provide your target Domain",
            True,
        ): str("google.com"),
    })    

    def run(self):
        domain = self.config.option('DOMAIN').value
        print("\n"" Analyzing '%s'..." % (domain))
        request = requests.get("https://api.hackertarget.com/dnslookup/?q=" + domain)
        res = request.text
        print("\n", res)
        

