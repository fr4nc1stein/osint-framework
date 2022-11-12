from dotenv import load_dotenv
import base64,os,json, requests, jellyfish
load_dotenv()

APPID = os.getenv("CENSYS_APPID")
SECRET = os.getenv("CENSYS_SECRET")

mAuth = f"{APPID}:{SECRET}"
auth = base64.b64encode(mAuth.encode("ascii"))
auth = auth.decode("ascii")

PAGES = 50
DOMAIN = "doh.gov.ph"

API_URL = f"https://search.censys.io/api/v2/hosts/search?q=service.service_name%3A%20HTTP%20and%20{DOMAIN}&per_page={PAGES}&virtual_hosts=EXCLUDE"

ch = {
    "accept": "application/json",
    "Authorization": "Basic " + auth
}

KNOWN_WAF = []

def main():
    init()
    # fetchData(API_URL,ch)
    parseData("tmp/censys.json")

def init():
    f = open("db/waf-org.txt")
    for org in f:
        if "#" in org:
            continue

        if org == "":
            continue

        KNOWN_WAF.append(org.strip())

    f.close()

def parseData(file):
    foundIP = []

    f = open(file)
    for jd in f:
        d = json.loads(jd)
        if d['code'] != 200:
            continue

        print(f"running test on {len(d['result']['hits'])} data")
        for hit in d['result']['hits']:
            ip = hit['ip']
            if not isWaf(ip):
                foundIP.append(ip)

    f.close()
    print(len(foundIP))

def isWaf(ip):
    url = "http://ip-api.com/json/"
    r = requests.get(url+ip,headers={"accept":"application/json"})
    w = r.json()

    for waf in KNOWN_WAF:
        print(w['isp'].lower())
        res = jellyfish.jaro_distance(waf.lower(), w['isp'].lower())
        if res > 0.8:
            return True

    return False

def fetchData(url,ch):
    print("fetching...")
    r = requests.get(url,headers=ch)
    
    if not os.path.exists("tmp"):
        os.mkdir("tmp")

    with open("tmp/censys.json","a") as f:
        f.writelines(r.text + "\n")
        f.close()

        d = r.json()
        if d['code'] != 200:
            print(d['status'])
            return 

        if d['result']['links']['next'] != "":
            next = d['result']['links']['next']
            fetchData(url + "&cursor=" + next,ch)

main()