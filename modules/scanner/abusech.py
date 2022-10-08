from sploitkit import *
from dotenv import load_dotenv
from terminaltables import SingleTable
import os
import json
from malwarebazaar.api import Bazaar
from pygments import highlight, lexers, formatters

class abusechScan(Module):
    """ This module scan HASH or URL using VT
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    ABUSECH_API_KEYVT_API = os.getenv('ABUSECH_API_KEY')
    bazaar = Bazaar(ABUSECH_API_KEYVT_API)

    config = Config({
        Option(
            'HASH',
            "Provide hash",
            True,
        ): str("f670080b1f42d1b70a37adda924976e6d7bd62bf77c35263aff97e7968291807"),
    })    

    def run(self):
        hash = self.config.option('HASH').value
        response = self.bazaar.query_hash(hash)
        raw_json = json.dumps(
            response,
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

