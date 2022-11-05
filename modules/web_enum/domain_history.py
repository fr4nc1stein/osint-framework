import os,json,requests

from sploitkit import Module, Config, Option, Command
from terminaltables import SingleTable

class DomainHistory(Module):
    """ This module fetch passive data containing historical records on a target domain.
    Author:  cadeath
    Version: 1.0
    """

    config = Config({
        Option(
            "DOMAIN",
            "Provide any domain",
            True,
        ): str("laet4x.com"),
    })
    
    API_URL = "https://api.securitytrails.com/v1/history/"

    def run(self):
        apiKey = os.getenv('SECURITY_TRAIL_API')
        targetDomain = self.config.option('DOMAIN').value

        apiHeader = { "apikey": apiKey }
        r = requests.get(self.API_URL + targetDomain + "/dns/a", headers=apiHeader)
        d = r.json()
        
        tblOutput = []
        th = ('First Seen','Organization','Last Seen','IP')
        tblOutput.append(th)

        for rec in d["records"]:

            ips = []
            for rv in rec['values']:
                ips.append(rv['ip'])
            
            td = (rec['first_seen'],','.join(rec['organizations']),rec['last_seen'],', '.join(ips))
            tblOutput.append(td)

        table = SingleTable(tblOutput,"Historical Data")
        print("\n" + table.table)
        