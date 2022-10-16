# OSIF 
Opensource Intelligence Framework is an open-source framework dedicated to OSINT. For the ease of use, the interface has a layout that looks like Metasploit.

It consists of various modules that aid osint operations:
1. Attack Surface
2. Blockchain
3. Email
4. Host Enumeration
5. IoC
6. Social Media
7. Web Enumeration

# Documentation
Full documentation found at https://osif.laet4x.com/

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
3. ./osif

If not started, follow this instruction below:
```
docker build --no-cache  --tag osif .
docker run -ti osif bash
./osif
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
1. Virustotal API https://www.virustotal.com/
2. CENSYS API https://accounts.censys.io/ (under development)
3. ABUSECH https://bazaar.abuse.ch/ (not required)
4. SHODAN API https://account.shodan.io/
5. HUNTER API https://hunter.io/api-keys
```
VT_API=""
CENSYS_APPID=""
CENSYS_SECRET=""
ABUSECH_API_KEY = ""
SHODAN_API_KEY = ""
HUNTER_API_KEY = ""
```



```
─$ ./osif


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
laet4x
cadeath