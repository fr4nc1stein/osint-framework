from sploitkit import *
from dotenv import load_dotenv
from terminaltables import SingleTable
import os
import vt

class osifVirusTotal(Module):
    """ This module scan HASH or URL using VT
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'URL',
            "Provide your target IP",
            True,
        ): str("server.dotomater.club"),
    })    

    def run(self):
        TABLE_DATA = []
        load_dotenv()
        VT_API = os.getenv('VT_API')
        url = self.config.option('URL').value

        client = vt.Client(VT_API)
        url_id = vt.url_id(url)
        url_vt = client.get_object("/urls/{}", url_id)
        print("\n"" Analyzing '%s'..." % (url))
        
        infos = ("URL", url)
        TABLE_DATA.append(infos)
        
        infos = ("HARMLESS", url_vt.last_analysis_stats['harmless'])
        TABLE_DATA.append(infos)
        
        infos = ("MALICIOUS",  url_vt.last_analysis_stats['malicious'])
        TABLE_DATA.append(infos)
            
        infos = ("SUSPICIOUS",  url_vt.last_analysis_stats['suspicious'])
        TABLE_DATA.append(infos)

        infos = ("UNDETECTED",  url_vt.last_analysis_stats['undetected'])
        TABLE_DATA.append(infos)

        table = SingleTable(TABLE_DATA, url)
        print("\n"+table.table)
