from sploitkit import *
import requests
import json

class osifLeaked(Module):
    """ This module find leaked info using ihavebeenpwnd
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'EMAIL',
            True,
        )
    })

    def run(self):
        dataList = []
        email = self.config.option('EMAIL').value
        try:
            req = requests.get("https://haveibeenpwned.com/api/v2/breachedaccount/"+email, headers={"Content-Type":"application/json", "Accept":"application/json", "User-Agent":"OSINF"})
            if req.status_code == 200:
                data = json.loads(req.text)
                for d in data:
                    name = d['Title']
                    domain = d['Domain']
                    date = d['BreachDate']
                    dataDic = {'Title':name, 'Domain':domain, 'Date':date}
                    dataList.append(dataDic)
                    
                    print(dataList)
        except:
            print("Error")

