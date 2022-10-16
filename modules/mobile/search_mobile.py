import requests
from sploitkit import Module, Config, Option, Command

class SearchMobile(Module):
    """ This module with validate if the mobile number is temporary.
    Author:  cadeath
    Version: 1.0
    """
    config = Config({
        Option(
            'Mobile',
            "Enter your 11 digit mobile number",
            True,
        ): str("+639xxxxxxxxx"),
        Option(
            'Update_DB',
            "Force to update the database",
            False,
        ): bool("False"),
    })
    
    def _fetch(self):
        print("Fetching DB...")
    
    def run(self):
        if self.config.option("Update_DB").value:
            self._fetch()
        
        print("Not Found")
