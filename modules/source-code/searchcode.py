from http.client import responses
from sploitkit import *
import os
import requests
from dotenv import load_dotenv
import json
from prettytable import PrettyTable


class SearchCode(Module):
    """ This module find Host Information using Shodan
    Author:  laet4x
    Version: 1.0
    """

    config = Config({
        Option(
            'KEYWORD',
            "Provide your keyword",
            True,
        ): str("api_key="),
    })    

    def run(self):
        TABLE_DATA = []
        keyword = self.config.option('KEYWORD').value
        print("\n""Analyzing '%s'..." % (keyword))

        # endpoint URL
        endpoint = "https://searchcode.com/api/codesearch_I/?"

        # send the GET request to the API
        response = requests.get(endpoint + "q=" + keyword)

        # parse the JSON response
        data = json.loads(response.text)

        if data:
            print("\nExtracted Repositories:: ")

            # initialize the table
            table = PrettyTable()
            table.field_names = ["Repository", "Language", "Filename", "Location", "URL"]

            # parse the JSON data
            for result in data["results"]:
                # add the data to the table
                table.add_row([result["repo"], result["language"], result["filename"], result["location"], result["url"]])
                print(table)
                table.clear_rows()

