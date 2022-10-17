import os
import jellyfish
from sploitkit import Module, Config, Option, Command

class SearchTempMobile(Module):
    """ This module validates if the mobile number used for receiving SMS is a temporary number. 
    This numbers are often used for temporary registration in sites but is not act 
    as legit mobile number.
    Author:  cadeath
    Version: 1.0.2
    """
    config = Config({
        Option(
            "MOBILE",
            "Enter your 11 digit mobile number",
            True,
        ): str("+63xxxxxxxxx"),
        Option(
            "DB_UPDATE",
            "Force to update the database (not yet working)",
            True,
            bool,
        ): "False",
    })

    list_number = "/db/mobile.txt"
    
    def _fetch(self):
        # print("Fetching DB...")
        pass
    
    def run(self):
        if self.config.option("DB_UPDATE").value:
            self._fetch()

        DB_TMP = os.getcwd() + self.list_number        
        
        search_number = str(self.config.option("MOBILE").value)
        numbers = open(DB_TMP)
        for num in numbers:
            # Skip comment line
            if "#" in num:
                continue
            # Skip newline
            if num == "":
                continue

            res = jellyfish.jaro_distance(num, search_number)            
            if res > 0.86:
                print(f"!!! {search_number} is a temporary number!!!")
                return

        print(f"{search_number} seems legit to me...")
                