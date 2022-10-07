#!/usr/bin/python3
import re
from sploitkit import *
from tinyscript.helpers import is_bool, ExpiringDict, Path
from tinyscript import *

class OsifConsole(FrameworkConsole):
    exclude = ["root/test", "root/help"]
    sources = {'banners': "banners"}
    
    def at_exit():
        subprocess.call("service network-manager restart", shell=True)
        if not args.dev:
            subprocess.call("reset", shell=True)

__all__ = ["OsifConsole"]
__script__ = "osif"
__doc__    = """
Osif launcher script.
"""
if __name__ == '__main__':
    parser.add_argument("-d", "--dev", action="store_true", help="enable development mode")
    initialize(exit_at_interrupt=False)
    c = OsifConsole(
        "OSIF",
        #TODO: configure your console settings
        banner_section_styles={'title': {'fgcolor': "lolcat"}},
        dev=args.dev,
        debug=args.verbose,
    )
    c.start()