from sploitkit import Module, Config, Option, Command
import requests
from terminaltables import SingleTable

class dnsHost(Module):
    # Command.set_style("module")
    """ This module find DNS Host information
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
        request = requests.get("https://api.hackertarget.com/hostsearch/?q=" + domain)
        res = request.text
        print("\n", res)
        

