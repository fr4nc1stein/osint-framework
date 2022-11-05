import os,json,requests

from datetime import datetime
from sploitkit import Module, Config, Option
from terminaltables import SingleTable

class DomainHistory(Module):
    """ This module fetch passive data containing historical records on a target domain.
    Author:  cadeath
    Version: 1.1
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

        # self._tmp(json.dumps(d)) # For debug only
        
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

        # Extracting Data        
        filename = self._extract_init("org,first,last,ip")
        f = open(filename,"a")
        for rec in d["records"]:
            for rv in rec["values"]:
                orgs = ','.join(rec['organizations'])
                orgs = self._quote_space(orgs)
                f.writelines(f"{orgs},{rec['first_seen']},{rec['last_seen']},{rv['ip']}\n")
        f.close()
        print("Filename",filename)
    
    def _extract_init(self,headers):
        now = datetime.now()

        date_time = now.strftime("%m-%d-%Y-%H-%M-%S")
        filename = f"outputs/file-{date_time}.csv"

        with open(f"{filename}","w") as f:
            f.writelines(headers + "\n")

        return filename

    def _quote_space(self,str):
        if " " in str:
            return f"\"{str}\""

        return str
    
    def _tmp(self,result):
        now = datetime.now()

        date_time = now.strftime("%m-%d-%Y-%H-%M-%S")
        filename = f"file-{date_time}"

        f = open(f"tmp/{filename}","w")
        f.writelines(result)
        f.close()

        return filename