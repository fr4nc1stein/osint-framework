from sploitkit import *
from dotenv import load_dotenv
from terminaltables import SingleTable
import os
import requests

class AbuseIPDBCheck(Module):
    """ Check IP reputation using AbuseIPDB
    Author:  laet4x
    Version: 1.0
    """
    load_dotenv()
    ABUSEIPDB_API_KEY = os.getenv('ABUSEIPDB_API_KEY')

    config = Config({
        Option(
            'IP',
            "IP address to check",
            True,
        ): str("8.8.8.8"),
        Option(
            'MAX_AGE',
            "Maximum age in days to check (default: 90)",
            False,
        ): int(90),
    })    

    def run(self):
        if not self.ABUSEIPDB_API_KEY:
            self.logger.error("AbuseIPDB API key not configured in .env file")
            return

        ip = self.config.option('IP').value
        max_age = self.config.option('MAX_AGE').value

        url = 'https://api.abuseipdb.com/api/v2/check'
        
        headers = {
            'Accept': 'application/json',
            'Key': self.ABUSEIPDB_API_KEY
        }
        
        params = {
            'ipAddress': ip,
            'maxAgeInDays': max_age,
            'verbose': True
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if 'data' not in result:
                self.logger.error("Invalid response from AbuseIPDB")
                return

            data = result['data']
            
            # Main information table
            table_data = [
                ("IP Address", data.get("ipAddress", "")),
                ("Abuse Confidence Score", f"{data.get('abuseConfidenceScore', 0)}%"),
                ("Usage Type", data.get("usageType", "Unknown")),
                ("ISP", data.get("isp", "Unknown")),
                ("Domain", data.get("domain", "N/A")),
                ("Country", f"{data.get('countryName', 'Unknown')} ({data.get('countryCode', '')})"),
                ("Is Public", "Yes" if data.get("isPublic") else "No"),
                ("Is Whitelisted", "Yes" if data.get("isWhitelisted") else "No"),
                ("Total Reports", str(data.get("totalReports", 0))),
                ("Distinct Users", str(data.get("numDistinctUsers", 0))),
                ("Last Reported", data.get("lastReportedAt", "Never")),
            ]

            table = SingleTable(table_data, f"AbuseIPDB Report for {ip}")
            print("\n" + table.table)

            # Abuse score interpretation
            score = data.get('abuseConfidenceScore', 0)
            print("\n[Threat Assessment]")
            if score == 0:
                print("✅ Clean - No abuse reports found")
            elif score < 25:
                print("⚠️  Low Risk - Few abuse reports")
            elif score < 75:
                print("🔶 Medium Risk - Multiple abuse reports")
            else:
                print("🔴 High Risk - Significant abuse activity")

            # Show recent reports if available
            if 'reports' in data and data['reports']:
                print("\n[Recent Abuse Reports]")
                print("-" * 80)
                for idx, report in enumerate(data['reports'][:5], 1):
                    print(f"\nReport #{idx}:")
                    print(f"  Date: {report.get('reportedAt', 'Unknown')}")
                    print(f"  Categories: {', '.join(map(str, report.get('categories', [])))}")
                    print(f"  Comment: {report.get('comment', 'No comment')[:100]}")
                
                if len(data['reports']) > 5:
                    print(f"\n... and {len(data['reports']) - 5} more reports")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error querying AbuseIPDB: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
