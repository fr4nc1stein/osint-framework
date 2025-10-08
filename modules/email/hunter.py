from http.client import responses
from sploitkit import *
import os
import requests
from dotenv import load_dotenv
from pygments import highlight, lexers, formatters
import json
from terminaltables import SingleTable
from tomba.client import Client
from tomba.services.domain import Domain


class hunterEmail(Module):
    """ This module finds email addresses using Hunter.io and Tomba
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    HUNTER_API_KEY = os.getenv('HUNTER_API_KEY')
    TOMBA_API_KEY = os.getenv('TOMBA_API_KEY')
    TOMBA_SECRET_KEY = os.getenv('TOMBA_SECRET_KEY')

    config = Config({
        Option(
            'DOMAIN',
            "Provide your target Domain",
            True,
        ): str("laet4x.com"),
        Option(
            'SERVICE',
            "Choose email search service (hunter, tomba, both)",
            False,
        ): str("both"),
        Option(
            'LIMIT',
            "Number of results to return for Tomba (max 100)",
            False,
        ): str("10"),
    })

    def run(self):
        domain = self.config.option('DOMAIN').value
        service = self.config.option('SERVICE').value.lower()
        limit = int(self.config.option('LIMIT').value)

        print(f"\nAnalyzing '{domain}'...")

        if service in ['hunter', 'both']:
            self.search_hunter(domain)

        if service in ['tomba', 'both']:
            self.search_tomba(domain, limit)

    def search_hunter(self, domain):
        """Search emails using Hunter.io"""
        print(f"\n🔍 Searching with Hunter.io...")

        if not self.HUNTER_API_KEY:
            print(
                "Hunter.io API key not found. Please set HUNTER_API_KEY in your .env file")
            return

        TABLE_DATA = []
        try:
            url = f'https://api.hunter.io/v2/domain-search?domain={domain}&api_key={self.HUNTER_API_KEY}'
            response = requests.get(url)
            json_response = response.json()

            if 'data' in json_response and 'emails' in json_response['data']:
                emails_list = json_response['data']['emails']

                if emails_list:
                    print(f"✅ Hunter.io found {len(emails_list)} emails:")
                    info = ("Email", "First Name", "Last Name",
                            "Position", "Phone", "LinkedIn", "Twitter")
                    TABLE_DATA.append(info)
                    for email in emails_list:
                        infos = (
                            email.get('value', 'N/A'),
                            email.get('first_name', 'N/A'),
                            email.get('last_name', 'N/A'),
                            email.get('position', 'N/A'),
                            email.get('phone_number', 'N/A'),
                            email.get('linkedin', 'N/A'),
                            email.get('twitter', 'N/A')
                        )
                        TABLE_DATA.append(infos)

                    table = SingleTable(
                        TABLE_DATA, f"Hunter.io Results for {domain}")
                    print("\n" + table.table)
                else:
                    print("No emails found with Hunter.io")
            else:
                print("No data returned from Hunter.io")

        except Exception as e:
            print(f"Error with Hunter.io: {str(e)}")

    def search_tomba(self, domain, limit):
        """Search emails using Tomba"""
        print(f"\n🔍 Searching with Tomba...")

        if not self.TOMBA_API_KEY or not self.TOMBA_SECRET_KEY:
            print("Tomba API credentials not found. Please set TOMBA_API_KEY and TOMBA_SECRET_KEY in your .env file")
            return

        TABLE_DATA = []
        try:
            # Initialize Tomba client
            client = Client()
            client.set_key(self.TOMBA_API_KEY)
            client.set_secret(self.TOMBA_SECRET_KEY)
            domain_service = Domain(client)
            # Search for emails in the domain
            result = domain_service.domain_search(domain=domain, limit=limit)

            if result and 'data' in result and 'emails' in result['data']:
                emails_list = result['data']['emails']

                if emails_list:
                    print(f"✅ Tomba found {len(emails_list)} emails:")

                    # Table headers
                    headers = ("Email", "First Name", "Last Name",
                               "Position", "Department", "Type", "Sources")
                    TABLE_DATA.append(headers)

                    for email_data in emails_list:
                        email = email_data.get('email', 'N/A')
                        first_name = email_data.get('first_name', 'N/A')
                        last_name = email_data.get('last_name', 'N/A')
                        position = email_data.get('position', 'N/A')
                        department = email_data.get('department', 'N/A')
                        email_type = email_data.get('type', 'N/A')
                        sources = len(email_data.get('sources', []))

                        row = (email, first_name, last_name, position,
                               department, email_type, str(sources))
                        TABLE_DATA.append(row)

                    # Display results in table
                    table = SingleTable(
                        TABLE_DATA, f"Tomba Results for {domain}")
                    print("\n" + table.table)

                    # Display additional domain information if available
                    if 'meta' in result['data']:
                        meta = result['data']['meta']
                        print(f"\n📊 Domain Statistics:")
                        if 'total' in meta:
                            print(f"   • Total emails found: {meta['total']}")
                        if 'department' in meta:
                            print(
                                f"   • Department distribution: {meta['department']}")
                        if 'seniority' in meta:
                            print(
                                f"   • Seniority distribution: {meta['seniority']}")

                else:
                    print("No emails found with Tomba")

            else:
                print("No results returned from Tomba")

        except Exception as e:
            print(f"Error with Tomba: {str(e)}")

        # debugging
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
