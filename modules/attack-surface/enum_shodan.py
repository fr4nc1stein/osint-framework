from distutils.log import info
from sploitkit import *
import os
from dotenv import load_dotenv
from shodan import Shodan
from pygments import highlight, lexers, formatters
import json
from terminaltables import SingleTable

class shodanSearch(Module):
    """ This module find Host Information using Shodan
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    SHODAN_API = os.getenv('SHODAN_API_KEY')
    if not SHODAN_API:
        raise ValueError("SHODAN_API_KEY not found in environment. Please set it in your .env file.")
    API = Shodan(SHODAN_API)

    config = Config({
        Option(
            'HOST_IP',
            "Provide your target IP",
            True,
        ): str("136.158.41.95"),
    })    

    def run(self):
        TABLE_DATA = []
        host = self.config.option('HOST_IP').value
        print("\n""Analyzing '%s'..." % (host))
        # Lookup an IP
        ipinfo = self.API.host(host)

        #host
        infos = ("HOST", host)
        TABLE_DATA.append(infos)

        #asn
        infos = ("ASN", ipinfo['asn'])
        TABLE_DATA.append(infos)
        
        #domain
        hostnames =  ipinfo['hostnames']
        newStringHostnames = ','.join(str(x) for x in hostnames)
        infos = ("HOSTNAME", newStringHostnames)
        TABLE_DATA.append(infos)

        #ORG
        infos = ("ORG", ipinfo['org'])
        TABLE_DATA.append(infos)

         #ISP
        infos = ("ISP", ipinfo['isp'])
        TABLE_DATA.append(infos)

        #ports
        ports =  ipinfo['ports']
        newStringPorts = ','.join(str(x) for x in ports)
        infos = ("PORTS", newStringPorts)
        TABLE_DATA.append(infos)

        if "vulns" in ipinfo:
            vulns =  ipinfo['vulns'][0:5]
            newStringVulns = ','.join(str(x) for x in vulns)
            infos = ("VULNERABILITIES", newStringVulns + " and more...")
            TABLE_DATA.append(infos)

        #modules/service
        modules = []
        for data in ipinfo['data']:
            infos = (data['_shodan']['module'])
            modules.append(infos)
        services = ','.join(modules)
        infos = ("SERVICES", services)
        TABLE_DATA.append(infos)    
      
        # raw_json = json.dumps(
        #     ipinfo,
        #     sort_keys=True,
        #     indent=4,
        #     separators=(',', ': ')
        # )
        # colorful = highlight(
        #     raw_json,
        #     lexer=lexers.JsonLexer(),
        #     formatter=formatters.TerminalFormatter(),
        # )
        # print(colorful)

        table = SingleTable(TABLE_DATA, "SHODAN")
        print("\n"+table.table)


