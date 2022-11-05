from sploitkit import *

class DomainHistory(Model):
    ip = IPAddressField(primary_key=True)
    org = TextField()