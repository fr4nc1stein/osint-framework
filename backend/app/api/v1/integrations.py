"""Integrations Catalog API — reads env vars for configured status"""
import os
from fastapi import APIRouter

router = APIRouter()

INTEGRATIONS_CATALOG = [
    {"id": "shodan",      "name": "Shodan",            "env_var": "SHODAN_API_KEY",      "description": "Port scanning & banner grabbing",         "category": "recon"},
    {"id": "virustotal",  "name": "VirusTotal",        "env_var": "VIRUSTOTAL_API_KEY",  "description": "File & URL reputation scoring",           "category": "threat"},
    {"id": "abuseipdb",   "name": "AbuseIPDB",         "env_var": "ABUSEIPDB_API_KEY",   "description": "IP reputation & abuse reports",           "category": "threat"},
    {"id": "tomba",       "name": "Tomba.io",          "env_var": "TOMBA_API_KEY",       "description": "Email discovery & verification",          "category": "email"},
    {"id": "hibp",        "name": "Have I Been Pwned", "env_var": "HIBP_API_KEY",        "description": "Data breach checking",                    "category": "breach"},
    {"id": "hunter",      "name": "Hunter.io",         "env_var": "HUNTER_API_KEY",      "description": "Email finder & verification",             "category": "email"},
    {"id": "ipinfo",      "name": "IPinfo",            "env_var": "IPINFO_TOKEN",        "description": "IP geolocation & ASN data",               "category": "recon"},
    {"id": "alienvault",  "name": "AlienVault OTX",   "env_var": "ALIENVAULT_API_KEY",  "description": "Open threat intelligence platform",       "category": "threat"},
    {"id": "censys",      "name": "Censys",            "env_var": "CENSYS_API_KEY",      "description": "Internet-wide scanning & certificates",   "category": "recon"},
    {"id": "urlscan",     "name": "URLScan.io",        "env_var": "URLSCAN_API_KEY",     "description": "URL & domain sandbox scanning",           "category": "threat"},
]


@router.get("")
async def list_integrations():
    """Return integration catalog with configured status"""
    return [
        {
            **integration,
            "is_configured": bool(os.getenv(integration["env_var"])),
        }
        for integration in INTEGRATIONS_CATALOG
    ]
