# OSIF 
This CLI framework is based on sploitkit and is an attempt to gather OSINT Tools. For the ease of use, the interface has a layout that looks like Metasploit.

# Installation

```
git clone https://github.com/fr4nc1stein/osint-framework osif
cd osif
pip3 install -r requirements.txt
```

# Configuration

Create .env
1. Virustotal API
2. CENSYS API
```
VT_API=""
CENSYS_APPID=""
CENSYS_SECRET=""
```

# Sample framework usage:

```
─$ python3 main.py 

                                                   _|_|      _|_|_|  _|_|_|  _|_|_|_|
                                                  _|    _|  _|          _|    _|      
                                                  _|    _|    _|_|      _|    _|_|_|  
                                                  _|    _|        _|    _|    _|
                                                    _|_|    _|_|_|    _|_|_|  _|




                                                      #######   #####   ###  #######                                                       
                                                      #     #  #     #   #   #
                                                      #     #  #         #   #
                                                      #     #   #####    #   #####
                                                      #     #        #   #   #
                                                      #     #  #     #   #   #
                                                      #######   #####   ###  #

                                                            >> OSINT Framework
                                                                >> @laet4x


        -=[ 3 uncategorized ]=-

[!] There are some issues ; use 'show issues' to see more details
osif > show modules                                                                                                                        

Uncategorized modules
=====================

   Name              Path  Enabled  Description
   ----              ----  -------  -----------
   osif_ip           .     Y        This module find IP information
   osif_twitter      .     Y        This module find twitter account
   osif_virus_total  .     Y        This module scan HASH or URL using VT

osif > use osif_virus_total                                                                                                                
osif (osif_virus_total) > show options                                                                                                     

Module options
==============

   Name  Value                  Required  Description
   ----  -----                  --------  -----------
   URL   server.dotomater.club  Y         Provide your target IP 

osif (osif_virus_total) > run                                                                                                              

 Analyzing 'server.dotomater.club'...

┌server.dotomater.club───────────────┐
│ URL        │ server.dotomater.club │
├────────────┼───────────────────────┤
│ HARMLESS   │ 62                    │
│ MALICIOUS  │ 17                    │
│ SUSPICIOUS │ 0                     │
│ UNDETECTED │ 9                     │
└────────────┴───────────────────────┘
osif (osif_virus_total) > 

```
