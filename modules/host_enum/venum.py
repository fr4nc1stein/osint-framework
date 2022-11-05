import os,requests
from sploitkit import Module, Config, Option, Model

class Venum(Module):
    """ This module will check if the IP hosted a domain that is using a virtualhost
    Author:  cadeath
    Version: 1.0
    """

    config = Config({
        Option(
            "DOMAIN",
            "Provide the domain you are looking in the virtualhost",
            True,
        ): str("laet4x.com"),
        Option(
            "IP",
            "Provide a IP for a specific target",
            False,
        ): str("xx.xx.xx.xx"),
        Option(
            "IP_FILE",
            "Provide file used to checked vhost",
            False,
        ): str("file://output/vhost_ips.txt"),
        Option(
            "USERAGENT",
            "Provide your desire User-Agent",
            False,
        ): str("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"),
    })
    
    def run(self):
        UA = self.config.option('USERAGENT').value
        targetIP = self.config.option('IP').value
        ipFile = self.config.option('IP_FILE').value

        target = targetIP    
        if targetIP == "xx.xx.xx.xx":
            target = ipFile            
            if not os.path.exists(ipFile):
                print("Missing input")
                return 

        print("Searching...")
        if targetIP[:7] == "file://":
            pass