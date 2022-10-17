from http.client import responses
from sploitkit import *
import os
import requests
from dotenv import load_dotenv
from pygments import highlight, lexers, formatters
import json
from terminaltables import SingleTable


class hunterEmail(Module):
    """ This module find Host Information using Shodan
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    HUNTER_API_KEY = os.getenv('HUNTER_API_KEY')

    config = Config({
        Option(
            'DOMAIN',
            "Provide your target Domain",
            True,
        ): str("laet4x.com"),
    })    

    def run(self):
        TABLE_DATA = []
        domain = self.config.option('DOMAIN').value
        print("\n""Analyzing '%s'..." % (domain))
        # Lookup an IP
        company_details = None
        url = f'https://api.hunter.io/v2/domain-search?domain={domain}&api_key={self.HUNTER_API_KEY}'
        response = requests.get(url)
        json_response = response.json()
     
        emails_list = json_response['data']['emails']

        if emails_list:
            print("\nExtracted Emails:: ")
            info = ("Email", "First Name", "Last Name", "Position", "Phone", "Linkedin", "Twitter")
            TABLE_DATA.append(info)
            for email in emails_list:
                infos = (email['value'], email['first_name'], email['last_name'],  email['position'], email['phone_number'], email['linkedin'], email['twitter'])
                TABLE_DATA.append(infos)

        table = SingleTable(TABLE_DATA, domain)

        print("\n"+table.table)    

        #debugging 
        # raw_json = json.dumps(
        #     json_response,
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

