import ipaddress
import os,json,requests

from datetime import datetime
from sploitkit import Module, Config, Option
from terminaltables import SingleTable

DEBUG = True

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
        Option(
            "TO_FILE",
            "Extract result to file at output folder. Except Proxy IPs",
            False,
            bool,
        ): "False",
    })
    
    API_URL = "https://api.securitytrails.com/v1/history/"

    def run(self):
        apiKey = os.getenv('SECURITY_TRAIL_API')
        targetDomain = self.config.option('DOMAIN').value
        tobeExtracted = self.config.option('TO_FILE').value

        if DEBUG:
            print("[?] apiKey",apiKey)
            print("[?] targetDomain",targetDomain)
            print("[?] tobeExtracted",tobeExtracted)

        apiHeader = { "apikey": apiKey }
        r = requests.get(self.API_URL + targetDomain + "/dns/a", headers=apiHeader)
        d = r.json()

        if DEBUG:
            print("Request received...")

        if not "records" in d:
            print("Please check your Securitytrail API.")
            print(d)
            return

        if DEBUG:
            self._tmp(json.dumps(d))
        
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

        if tobeExtracted:
            WAF_IPS = []
            blockIPs = open("db/waf-ips.txt")
            for waf in blockIPs:
                # Skip comment line
                if "#" in waf:
                    continue

                WAF_IPS.append(waf)
            blockIPs.close()

            filename = self._extract_init("#ip",fname="ip-list")
            f = open(filename,"a")
            for rec in d["records"]:
                for rv in rec["values"]:
                    for excludeIP in WAF_IPS:
                        result = ipaddress.ip_address(rv['ip']) in ipaddress.ip_network(excludeIP.strip())
                        if not result:
                            f.writelines(rv['ip'] + "\n")

            f.close()
            print("Result at",filename)


            
    
    def _extract_init(self,headers,fname="file"):
        if not os.path.exists("outputs/"):
            os.makedirs("outputs/")

        now = datetime.now()

        date_time = now.strftime("%m-%d-%Y-%H-%M-%S")
        filename = f"outputs/{fname}-{date_time}.csv"

        with open(f"{filename}","w") as f:
            f.writelines(headers + "\n")

        return filename

    def _quote_space(self,str):
        if " " in str:
            return f"\"{str}\""

        return str
    
    def _tmp(self,result):
        if not os.path.exists("tmp/"):
            os.makedirs("tmp/")

        now = datetime.now()

        date_time = now.strftime("%m-%d-%Y-%H-%M-%S")
        filename = f"file-{date_time}.txt"

        f = open(f"tmp/{filename}","w")
        f.writelines(result)
        f.close()

        return filename