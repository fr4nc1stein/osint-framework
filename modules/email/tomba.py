from sploitkit import *
import os
import json
from dotenv import load_dotenv
from terminaltables import SingleTable
from tomba.client import Client
from tomba.services.domain import Domain
from tomba.services.verifier import Verifier
from tomba.services.finder import Finder


class TombaEmail(Module):
    """ This module finds email addresses using Tomba Email Finder
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    TOMBA_API_KEY = os.getenv('TOMBA_API_KEY')
    TOMBA_SECRET_KEY = os.getenv('TOMBA_SECRET_KEY')

    config = Config({
        Option(
            'DOMAIN',
            "Provide your target Domain",
            True,
        ): str("laet4x.com"),
        Option(
            'LIMIT',
            "Number of results to return (max 100)",
            False,
        ): str("10"),
    })

    def run(self):
        TABLE_DATA = []
        domain = self.config.option('DOMAIN').value
        limit = int(self.config.option('LIMIT').value)

        print(f"\nSearching for emails in domain '{domain}' using Tomba...")

        if not self.TOMBA_API_KEY or not self.TOMBA_SECRET_KEY:
            print(
                "Error: TOMBA_API_KEY and TOMBA_SECRET_KEY environment variables are required!")
            print("Please set them in your .env file")
            return

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
                    print(f"\n✅ Found {len(emails_list)} emails:")

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
                        print(
                            f"   • Total emails found: {meta.get('total', 'N/A')}")
                        print(
                            f"   • Department distribution: {meta.get('department', 'N/A')}")
                        print(
                            f"   • Seniority distribution: {meta.get('seniority', 'N/A')}")

                else:
                    print(f"No emails found for domain '{domain}'")

            else:
                print(f"No results returned for domain '{domain}'")

        except Exception as e:
            print(f"Error occurred while searching: {str(e)}")
            print("Please check your API credentials and domain name")


class TombaEmailVerifier(Module):
    """ This module verifies email addresses using Tomba Email Verifier
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    TOMBA_API_KEY = os.getenv('TOMBA_API_KEY')
    TOMBA_SECRET_KEY = os.getenv('TOMBA_SECRET_KEY')

    config = Config({
        Option(
            'EMAIL',
            "Email address to verify",
            True,
        ): str("info@tomba.io"),
    })

    def run(self):
        email = self.config.option('EMAIL').value

        print(f"\nVerifying email '{email}' using Tomba...")

        if not self.TOMBA_API_KEY or not self.TOMBA_SECRET_KEY:
            print(
                "Error: TOMBA_API_KEY and TOMBA_SECRET_KEY environment variables are required!")
            print("Please set them in your .env file")
            return

        try:
            # Initialize Tomba client
            client = Client()
            client.set_key(self.TOMBA_API_KEY)
            client.set_secret(self.TOMBA_SECRET_KEY)

            verifier_service = Verifier(client)
            # Verify the email
            result = verifier_service.email_verifier(email=email)

            if result and 'data' in result:
                data = result['data']
                email_data = data.get("email", {})

                print(f"\n Email Verification Results for: {email}")
                print(f"   • Status: {email_data.get('status', 'Unknown')}")
                print(f"   • Result: {email_data.get('result', 'Unknown')}")
                print(f"   • Score: {email_data.get('score', 'N/A')}")
                print(f"   • Email: {email_data.get('email', 'N/A')}")
                print(f"   • Regexp: {email_data.get('regex', 'N/A')}")
                print(f"   • Gibberish: {email_data.get('gibberish', 'N/A')}")
                print(
                    f"   • Disposable: {email_data.get('disposable', 'N/A')}")
                print(f"   • Webmail: {email_data.get('webmail', 'N/A')}")
                print(
                    f"   • MX Records: {email_data.get('mx', 'N/A')}")
                print(
                    f"   • SMTP Server: {email_data.get('smtp_server', 'N/A')}")
                print(
                    f"   • SMTP Check: {email_data.get('smtp_check', 'N/A')}")
                print(
                    f"   • Accept All: {email_data.get('accept_all', 'N/A')}")
                print(f"   • Block: {email_data.get('block', 'N/A')}")

                # Display sources if available
                if 'sources' in data and data['sources']:
                    print(f"   • Sources: {len(data['sources'])} found")

            else:
                print(f"No verification results returned for '{email}'")

        except Exception as e:
            print(f"Error occurred while verifying: {str(e)}")
            print("Please check your API credentials and email address")


class TombaEmailFinder(Module):
    """ This module finds email addresses for specific people using Tomba
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    TOMBA_API_KEY = os.getenv('TOMBA_API_KEY')
    TOMBA_SECRET_KEY = os.getenv('TOMBA_SECRET_KEY')

    config = Config({
        Option(
            'DOMAIN',
            "Target domain",
            True,
        ): str("laet4x.com"),
        Option(
            'FIRST_NAME',
            "First name of the person",
            True,
        ): str("John"),
        Option(
            'LAST_NAME',
            "Last name of the person",
            True,
        ): str("Doe"),
    })

    def run(self):
        domain = self.config.option('DOMAIN').value
        first_name = self.config.option('FIRST_NAME').value
        last_name = self.config.option('LAST_NAME').value

        print(
            f"\nFinding email for '{first_name} {last_name}' at '{domain}' using Tomba...")

        if not self.TOMBA_API_KEY or not self.TOMBA_SECRET_KEY:
            print(
                "Error: TOMBA_API_KEY and TOMBA_SECRET_KEY environment variables are required!")
            print("Please set them in your .env file")
            return

        try:
            # Initialize Tomba client
            client = Client()
            client.set_key(self.TOMBA_API_KEY)
            client.set_secret(self.TOMBA_SECRET_KEY)
            finder_service = Finder(client)

            # Find email for the person
            result = finder_service.email_finder(
                domain=domain,
                first_name=first_name,
                last_name=last_name
            )

            if result and 'data' in result:
                data = result['data']

                print(f"\n🎯 Email Finder Results:")
                print(f"   • Email: {data.get('email', 'Not found')}")
                print(f"   • Score: {data.get('score', 'N/A')}")
                print(f"   • First Name: {data.get('first_name', 'N/A')}")
                print(f"   • Last Name: {data.get('last_name', 'N/A')}")
                print(f"   • Full Name: {data.get('full_name', 'N/A')}")
                print(f"   • Position: {data.get('position', 'N/A')}")
                print(f"   • Country: {data.get('country', 'N/A')}")
                print(f"   • Company: {data.get('company', 'N/A')}")

                if 'sources' in data and data['sources']:
                    print(f"   • Sources: {len(data['sources'])} found")

            else:
                print(
                    f"No email found for '{first_name} {last_name}' at '{domain}'")

        except Exception as e:
            print(f"Error occurred while finding email: {str(e)}")
            print("Please check your API credentials and input parameters")
