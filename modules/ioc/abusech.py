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
    ABUSECH_API_KEY = os.getenv('ABUSECH_API_KEY')
    bazaar = Bazaar(ABUSECH_API_KEY)

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
        data = response.get("data", [])
        if not data:
            print("No data found for this hash.")
            return

        info = data[0]
        table_data = [
            ("File Name", info.get("file_name", "")),
            ("File Type", info.get("file_type", "")),
            ("File Size", info.get("file_size", "")),
            ("First Seen", info.get("first_seen", "")),
            ("Signature", info.get("signature", "")),
            ("SHA256", info.get("sha256_hash", "")),
            ("MD5", info.get("md5_hash", "")),
            ("Imphash", info.get("imphash", "")),
            ("Tags", ", ".join(info.get("tags", []))),
            ("ClamAV", ", ".join(info.get("intelligence", {}).get("clamav", []))),
            ("Downloads", info.get("intelligence", {}).get("downloads", "")),
            ("Uploads", info.get("intelligence", {}).get("uploads", "")),
            ("RedLine Verdict", info.get("vendor_intel", {}).get("ReversingLabs", {}).get("status", "")),
            ("RedLine Threat Name", info.get("vendor_intel", {}).get("ReversingLabs", {}).get("threat_name", "")),
            ("ANY.RUN Verdict", info.get("vendor_intel", {}).get("ANY.RUN", [{}])[0].get("verdict", "")),
            ("Triage Family", info.get("vendor_intel", {}).get("Triage", {}).get("malware_family", "")),
            ("Triage Score", info.get("vendor_intel", {}).get("Triage", {}).get("score", "")),
            ("Triage Link", info.get("vendor_intel", {}).get("Triage", {}).get("link", "")),
        ]

        table = SingleTable(table_data, "AbuseCH MalwareBazaar Summary")
        print("\n" + table.table)

        # Optionally, show related URLs
        print("\nRelated URLs:")
        for fi in info.get("file_information", []):
            print(f"- {fi.get('context', '')}: {fi.get('value', '')}")

        # Optionally, show YARA rules
        print("\nYARA Rules:")
        for rule in info.get("yara_rules", []):
            print(f"- {rule.get('rule_name', '')}: {rule.get('description', '')}")

