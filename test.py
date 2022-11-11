import logging
import re,requests
requests.packages.urllib3.disable_warnings() 

logging.basicConfig(filename='module-error.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

targetIP = "file://outputs/ip-list-11-11-2022-18-31-35.csv"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
DEBUG = True

if targetIP[:7] != "file://":
    print("File input must have file:// in the beginning")

ipAddresses = []
for ip in open(targetIP[7:]):
    ipAddr = ip.strip()
    if "#" in ipAddr:
        continue

    if ipAddr == "":
        continue

    ipAddresses.append(ipAddr)

def main():
    ip = "20.43.181.113"
    domain = "doh.gov.ph"

    # title = venum(ip,domain,UA)
    # if not title is None:
    #     print(f"{ip} is working! {title}")

    # return

    ip_cnt = len(ipAddresses)
    plural_msg = "addresses" if ip_cnt > 1 else "address"
    print(f"Exploring on {ip_cnt} IP {plural_msg}")
    for ip in ipAddresses:
        title = venum(domain,ip,UA)
        if title is None:
            print(f"Failed on {ip}")
            continue
        print(f"{ip} | {title}")

def venum(d,ip,ua,https=False):
    ch = {
        "User-Agent": ua,
        "Host": d
    }

    pattern = re.compile("<title.*?>(.+?)</title>")
    scheme = "http://"

    try:
        if https:
            scheme = "https://"
        
        r = requests.get(f"{scheme}{ip}", headers=ch, verify=False)
        title = re.findall(pattern, r.text)
    except Exception as e:
        if not https:
            if DEBUG:
                print("Recursion!!!")
            venum(d,ip,ua,https=True)

        title = None
        logging.error("[venum] {}".format(e))
        
    return title

main()