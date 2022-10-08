from tabnanny import verbose
from sploitkit import *
import sublist3r

class sublister(Module):
    """ This module find WHOIS Information
    Author:  laet4x
    Version: 1.0
    """
    config = Config({
        Option(
            'DOMAIN',
            "Provide your target Domain",
            True,
        ): str("google.com"),
        Option(
            'NO_THREADS',
            "No of Threads",
            True,
        ): str("40"),
        Option(
            'SAVEFILE',
            "Save the output into text file",
            True,
        ): str("subdomains.txt"),
         Option(
            'VERBOSE',
            "display the found subdomains in real time.",
            True,
        ): bool("True"),
    })    

    def run(self):
        domain = self.config.option('DOMAIN').value
        no_threads = self.config.option('NO_THREADS').value
        save_file = domain + "_" +self.config.option('SAVEFILE').value
        verbose = self.config.option('VERBOSE').value
        print("\n"" Analyzing '%s'..." % (domain))
        subdomains = sublist3r.main(domain, no_threads, save_file, ports= None, silent=False, verbose= verbose, enable_bruteforce= False, engines=None)
        # print(subdomains)
      
        

