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
```
VT_API=""
CENSYS_APPID=""
CENSYS_SECRET=""
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




                                           ....                ...             .....     .      .....                                      
                                                    .x~X88888Hx.        .x888888hx    :   .d88888Neu. 'L  .H8888888x.  '`+                 
                                                   H8X 888888888h.     d88888888888hxx    F""""*8888888F :888888888888x.  !                
                                                  8888:`*888888888:   8" ... `"*8888%`   *      `"*88*"  8~    `"*88888888"                
                                                   88888:        `%8  !  "   ` .xnxx.      -....    ue=:. !      .  `f""""                 
                                                . `88888          ?> X X   .H8888888%:           :88N  `  ~:...-` :8L <)88:                
                                                `. ?888%           X X 'hn8888888*"   >          9888L       .   :888:>X88!                
                                                  ~*??.            > X: `*88888%`     !   uzu.   `8888L   :~"88x 48888X ^`                 
                                                  .x88888h.        <  '8h.. ``     ..x8> ,""888i   ?8888  <  :888k'88888X                  
                                                 :"""8888888x..  .x    `88888888888888f  4  9888L   %888>   d8888f '88888X                 
                                                `    `*888888888"      '%8888888888*"   '  '8888   '88%   :8888!    ?8888>                 
                                                        ""***""           ^"****""`          "*8Nu.z*"    X888!      8888~                 
                                                                                                           '888       X88f                 
                                                                                                            '%8:     .8*"                  
                                                                                                                ^----~"`                   
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

osif dns(dns_records) > set DOMAIN laet4x.com                                                                                              
[+] DOMAIN => laet4x.com
osif dns(dns_records) > run                                                                                                                

 Analyzing 'laet4x.com'...

 A : 172.67.188.86
A : 104.21.48.231
AAAA : 2606:4700:3030::6815:30e7
AAAA : 2606:4700:3033::ac43:bc56
MX : 10 eforward1.registrar-servers.com.
MX : 10 eforward2.registrar-servers.com.
MX : 10 eforward3.registrar-servers.com.
MX : 15 eforward4.registrar-servers.com.
MX : 20 eforward5.registrar-servers.com.
NS : drew.ns.cloudflare.com.
NS : zelda.ns.cloudflare.com.
SOA : drew.ns.cloudflare.com. dns.cloudflare.com. 2289666711 10000 2400 604800 3600
osif dns(dns_records) >  

```
## If you love OSIF you can buy me a coffee to support this project :)
 <a href="https://www.buymeacoffee.com/laet4x" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>


# Author
Al Francis 
