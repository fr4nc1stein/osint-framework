from sploitkit import *
import requests

class dnsRecords(Module):
    """ This module find DNS information
    Author:  laet4x
    Version: 1.0
    """
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
        request = requests.get("https://api.hackertarget.com/dnslookup/?q=" + domain)
        res = request.text
        print("\n", res)


        

