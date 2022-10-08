from sploitkit import Module, Config, Option, Command
import requests
from terminaltables import SingleTable
from Wappalyzer import Wappalyzer, WebPage

class wappalyzer(Module):
    # Command.set_style("module")
    """ This module find Web Application Technology Stack 
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'URL',
            "Provide your target RUL",
            True,
        ): str("https://laet4x.com"),
    })    

    def run(self):
        wappalyzer = Wappalyzer.latest()
        url = self.config.option('URL').value
        print("\n"" Analyzing '%s'..." % (url))
        webpage = WebPage.new_from_url(url)
        results = wappalyzer.analyze(webpage)
        print(results)
        

