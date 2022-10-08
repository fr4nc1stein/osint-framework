# OSIF 
This CLI framework is based on sploitkit and is an attempt to gather OSINT Tools. For the ease of use, the interface has a layout that looks like Metasploit.

# Docker Installation (Recommended)

### Docker installation
Get [Docker](https://docs.docker.com/get-docker/)
for Windows, Linux and MacOS

### Where to get Docker Compose
### Windows and macOS
Docker Compose is included in
[Docker Desktop](https://www.docker.com/products/docker-desktop)
for Windows and macOS.

### Linux
You can download Docker Compose binaries from the
[release page](https://github.com/docker/compose/releases) on this repository.

### Run osif with docker and docker-compose
1. docker-compose up -d
2. docker exec -ti osif bash
3. python3 -B main.py

If not started, follow this instruction below:
```
docker build --no-cache  --tag osif .
docker run -ti osif bash
```



# Installation
Recommended on linux or kali
```
git clone https://github.com/fr4nc1stein/osint-framework osif
cd osif
pip3 install -r requirements.txt
```

# Configuration

Create .env
1. Virustotal API
2. CENSYS API
3. BLOCHAIN https://blockchainapi.com/#pricing
4. ABUSECH https://bazaar.abuse.ch/ (not required)
```
VT_API=""
CENSYS_APPID=""
CENSYS_SECRET=""
BLOCKCHAIN_API_KEY_ID = ""
BLOCKCHAIN_API_SECRET_KEY = ""
ABUSECH_API_KEY = ""
```



```
─$ python3 -B main.py 


                                                         ##     ####   #####   ######
                                                        #  #   #    #    #     #
                                                       #    #  #         #     #
                                                       #    #   ####     #     ####
                                                       #    #       #    #     #
                                                        #  #   #    #    #     #
                                                         ##     ####   #####   #

            
                                                             >> OSINT Framework                                                            
                                                                 >> @laet4x                                                                
                                                                                                                                           
 

        -=[ 1 api           ]=-
        -=[ 2 dns           ]=-
        -=[ 1 social        ]=-
        -=[ 1 subdomain     ]=-
        -=[ 1 uncategorized ]=-

[!] There are some issues ; use 'show issues' to see more details
osif > use dns/dns_records                                                                                                                 
osif dns(dns_records) > show options                                                                                                       

Module options
==============

   Name    Value       Required  Description                
   ----    -----       --------  -----------                
   DOMAIN  google.com  Y         Provide your target Domain 

osif dns(dns_records) > 
```
## If you love OSIF you can buy me a coffee to support this project :)
 <a href="https://www.buymeacoffee.com/laet4x" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>


# Author
Al Francis 
