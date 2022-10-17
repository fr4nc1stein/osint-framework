#!/usr/bin/env python
import re
import sys 
from sploitkit import *
from tinyscript.helpers import is_bool, ExpiringDict, Path
from tinyscript import *

class OsifConsole(FrameworkConsole):
    exclude = ["root/test", "root/helpe"]
    sources = {'banners': "banners"}
    
__all__ = ["OsifConsole"]
__script__ = "osif"
__doc__    = """
Osif launcher script.
"""

def main():
    parser.add_argument("-d", "--dev", action="store_true", help="enable development mode")
    initialize(exit_at_interrupt=False)
    
    #add traceback   
    sys.tracebacklimit=0

    #disable _pycachce_
    sys.dont_write_bytecode = True

    c = OsifConsole(
        "OSIF",
        #TODO: configure your console settings
        banner_section_styles={'title': {'fgcolor': "lolcat"}},
        dev=args.dev,
        debug=args.verbose,
    )
    c.start()
    
# if __name__ == "__main__": main()    