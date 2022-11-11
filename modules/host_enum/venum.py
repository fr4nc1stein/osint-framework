import logging
import re,requests
from sploitkit import Module, Config, Option

DEBUG = False
requests.packages.urllib3.disable_warnings() 
logging.basicConfig(filename='module-error.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class Venum(Module):
    """ This module will check if the IP hosted a domain that is using a virtualhost
    Author:  cadeath
    Version: 1.0
    """

    config = Config({
        Option(
            "DOMAIN",
            "Provide the domain you are looking in the virtualhost",
            True,
        ): str("laet4x.com"),
        Option(
            "IP",
            "Provide a IP for a specific target",
            False,
        ): str("xx.xx.xx.xx"),
        Option(
            "IP_FILE",
            "Provide file used to checked vhost",
            False,
        ): str("file://output/vhost_ips.txt"),
        Option(
            "USERAGENT",
            "Provide your desire User-Agent",
            False,
        ): str("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"),
    })
    
    def run(self):
        VHOST = self.config.option('DOMAIN').value
        UA = self.config.option('USERAGENT').value
        targetIP = self.config.option('IP').value
        ipFile = self.config.option('IP_FILE').value

        if targetIP == "xx.xx.xx.xx" or targetIP is None:
            targetIP = ipFile
            if targetIP[:7] != "file://":
                print("File input must have file:// in the beginning")
                return None

            ipAddresses = []
            for ip in open(targetIP[7:]):
                ipAddr = ip.strip()
                if "#" in ipAddr:
                    continue

                if ipAddr == "":
                    continue

                ipAddresses.append(ipAddr)

            ip_cnt = len(ipAddresses)
            plural_msg = "addresses" if ip_cnt > 1 else "address"
            print(f"Exploring on {ip_cnt} IP {plural_msg}")
            for ip in ipAddresses:
                title = self._venum(VHOST,ip,UA)
                if title is None:
                    print(f"Failed on {ip}")
                    continue
                print(f"{ip} | {title}")

            return

        title = self._venum(VHOST,targetIP,UA)
        if title is None:
            print(f"Failed on {targetIP}")
            return

        print(f"{targetIP} | {title}")

    def _venum(self,d,ip,ua,https=False):
        ch = {
            "User-Agent": ua,
            "Host": d
        }

        pattern = re.compile("<title.*?>(.+?)</title>")
        scheme = "http://"

        try:
            if https:
                scheme = "https://"
            
            # deepcode ignore SSLVerificationBypass: I know that
            r = requests.get(f"{scheme}{ip}", headers=ch, verify=False)
            title = re.findall(pattern, r.text)
        except Exception as e:
            if not https:
                if DEBUG:
                    print("Recursion!!!")
                self._venum(d,ip,ua,https=True)

            title = None
            logging.error("[venum] {}".format(e))
            
        return title