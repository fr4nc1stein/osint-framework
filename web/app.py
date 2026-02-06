#!/usr/bin/env python3
"""
OSIF Web Interface - Graph-based OSINT Visualization
Similar to Maltego/FlowSINT for visual intelligence gathering
"""
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
import sys

# Add parent directory to path to import OSINT modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Store investigation graphs in memory (in production, use Redis/Database)
investigations = {}

@app.route('/')
def index():
    """Main graph visualization interface"""
    return render_template('index.html')

@app.route('/api/investigate', methods=['POST'])
def investigate():
    """
    Main investigation endpoint - takes an entity and module, returns nodes and edges
    """
    data = request.json
    entity_type = data.get('entity_type')  # domain, ip, email, bitcoin, etc.
    entity_value = data.get('entity_value')
    module_name = data.get('module')
    investigation_id = data.get('investigation_id', str(uuid.uuid4()))
    
    try:
        result = run_osint_module(module_name, entity_value, entity_type)
        
        # Store in investigation
        if investigation_id not in investigations:
            investigations[investigation_id] = {
                'id': investigation_id,
                'created_at': datetime.now().isoformat(),
                'nodes': [],
                'edges': []
            }
        
        # Add results to graph
        nodes, edges = result['nodes'], result['edges']
        investigations[investigation_id]['nodes'].extend(nodes)
        investigations[investigation_id]['edges'].extend(edges)
        
        return jsonify({
            'success': True,
            'investigation_id': investigation_id,
            'nodes': nodes,
            'edges': edges
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/modules', methods=['GET'])
def get_modules():
    """Get available OSINT modules"""
    modules = {
        'domain': [
            {'id': 'email_hunter', 'name': 'Email Hunter', 'description': 'Find emails for domain'},
            {'id': 'sublister', 'name': 'Subdomain Lister', 'description': 'Find subdomains'},
            {'id': 'dns_records', 'name': 'DNS Records', 'description': 'Get DNS information'},
            {'id': 'dns_host', 'name': 'DNS Hosts', 'description': 'Find related hosts'},
            {'id': 'wappalyzer', 'name': 'Tech Stack', 'description': 'Identify technologies'},
            {'id': 'domain_history', 'name': 'Domain History', 'description': 'Historical DNS records'}
        ],
        'ip': [
            {'id': 'shodan', 'name': 'Shodan Lookup', 'description': 'Get IP information from Shodan'},
            {'id': 'ip_lookup', 'name': 'IP Geolocation', 'description': 'Geolocate IP address'}
        ],
        'email': [
            {'id': 'email_verify', 'name': 'Email Verification', 'description': 'Verify email existence'}
        ],
        'bitcoin': [
            {'id': 'bitcoin_balance', 'name': 'Bitcoin Balance', 'description': 'Check Bitcoin address'}
        ],
        'ethereum': [
            {'id': 'ethereum_balance', 'name': 'Ethereum Balance', 'description': 'Check ETH balance'},
            {'id': 'ethereum_ens', 'name': 'ENS Lookup', 'description': 'Lookup ENS name'}
        ],
        'hash': [
            {'id': 'virustotal', 'name': 'VirusTotal', 'description': 'Scan hash/URL'},
            {'id': 'abusech', 'name': 'Abuse.ch', 'description': 'Check malware hash'}
        ],
        'wifi': [
            {'id': 'geowifi', 'name': 'WiFi Geolocation', 'description': 'Locate WiFi SSID'}
        ],
        'phone': [
            {'id': 'phone_verify', 'name': 'Phone Verification', 'description': 'Check if temp number'}
        ]
    }
    return jsonify(modules)

@app.route('/api/investigation/<investigation_id>', methods=['GET'])
def get_investigation(investigation_id):
    """Get investigation graph data"""
    if investigation_id in investigations:
        return jsonify(investigations[investigation_id])
    return jsonify({'error': 'Investigation not found'}), 404

@app.route('/api/investigation/<investigation_id>', methods=['DELETE'])
def delete_investigation(investigation_id):
    """Delete investigation"""
    if investigation_id in investigations:
        del investigations[investigation_id]
        return jsonify({'success': True})
    return jsonify({'error': 'Investigation not found'}), 404

@app.route('/api/export/<investigation_id>', methods=['GET'])
def export_investigation(investigation_id):
    """Export investigation as JSON"""
    if investigation_id in investigations:
        return jsonify(investigations[investigation_id])
    return jsonify({'error': 'Investigation not found'}), 404


def run_osint_module(module_name, entity_value, entity_type):
    """
    Execute OSINT module and return graph data (nodes and edges)
    """
    nodes = []
    edges = []
    
    # Create source node
    source_node = {
        'id': f"{entity_type}_{entity_value}",
        'label': entity_value,
        'type': entity_type,
        'group': entity_type
    }
    nodes.append(source_node)
    
    # Execute module based on name
    if module_name == 'email_hunter':
        result = execute_email_hunter(entity_value)
        nodes.extend(result['nodes'])
        edges.extend(result['edges'])
    
    elif module_name == 'shodan':
        result = execute_shodan(entity_value)
        nodes.extend(result['nodes'])
        edges.extend(result['edges'])
    
    elif module_name == 'ip_lookup':
        result = execute_ip_lookup(entity_value)
        nodes.extend(result['nodes'])
        edges.extend(result['edges'])
    
    elif module_name == 'dns_records':
        result = execute_dns_records(entity_value)
        nodes.extend(result['nodes'])
        edges.extend(result['edges'])
    
    elif module_name == 'sublister':
        result = execute_sublister(entity_value)
        nodes.extend(result['nodes'])
        edges.extend(result['edges'])
    
    elif module_name == 'bitcoin_balance':
        result = execute_bitcoin(entity_value)
        nodes.extend(result['nodes'])
        edges.extend(result['edges'])
    
    elif module_name == 'wappalyzer':
        result = execute_wappalyzer(entity_value)
        nodes.extend(result['nodes'])
        edges.extend(result['edges'])
    
    # Add more modules as needed
    
    return {'nodes': nodes, 'edges': edges}


def execute_email_hunter(domain):
    """Execute email hunter module"""
    import requests
    nodes = []
    edges = []
    
    HUNTER_API_KEY = os.getenv('HUNTER_API_KEY')
    if not HUNTER_API_KEY:
        return {'nodes': [], 'edges': []}
    
    try:
        url = f'https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}'
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'data' in data and 'emails' in data['data']:
            for email in data['data']['emails'][:10]:  # Limit to 10 emails
                email_addr = email.get('value')
                if email_addr:
                    node = {
                        'id': f"email_{email_addr}",
                        'label': email_addr,
                        'type': 'email',
                        'group': 'email',
                        'details': {
                            'first_name': email.get('first_name'),
                            'last_name': email.get('last_name'),
                            'position': email.get('position')
                        }
                    }
                    nodes.append(node)
                    edges.append({
                        'from': f"domain_{domain}",
                        'to': f"email_{email_addr}",
                        'label': 'has_email'
                    })
    except Exception as e:
        print(f"Error in email_hunter: {e}")
    
    return {'nodes': nodes, 'edges': edges}


def execute_shodan(ip):
    """Execute Shodan module"""
    from shodan import Shodan
    nodes = []
    edges = []
    
    SHODAN_API = os.getenv('SHODAN_API_KEY')
    if not SHODAN_API:
        return {'nodes': [], 'edges': []}
    
    try:
        api = Shodan(SHODAN_API)
        host = api.host(ip)
        
        # Add org node
        if 'org' in host:
            org_node = {
                'id': f"org_{host['org']}",
                'label': host['org'],
                'type': 'organization',
                'group': 'organization'
            }
            nodes.append(org_node)
            edges.append({
                'from': f"ip_{ip}",
                'to': f"org_{host['org']}",
                'label': 'belongs_to'
            })
        
        # Add port nodes
        for port in host.get('ports', [])[:5]:
            port_node = {
                'id': f"port_{ip}_{port}",
                'label': f"Port {port}",
                'type': 'port',
                'group': 'port'
            }
            nodes.append(port_node)
            edges.append({
                'from': f"ip_{ip}",
                'to': f"port_{ip}_{port}",
                'label': 'open_port'
            })
        
        # Add hostnames
        for hostname in host.get('hostnames', [])[:3]:
            host_node = {
                'id': f"domain_{hostname}",
                'label': hostname,
                'type': 'domain',
                'group': 'domain'
            }
            nodes.append(host_node)
            edges.append({
                'from': f"ip_{ip}",
                'to': f"domain_{hostname}",
                'label': 'resolves_to'
            })
    
    except Exception as e:
        print(f"Error in shodan: {e}")
    
    return {'nodes': nodes, 'edges': edges}


def execute_ip_lookup(ip):
    """Execute IP lookup module"""
    import requests
    nodes = []
    edges = []
    
    try:
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == 'success':
            # Add location node
            city = data.get('city', 'Unknown')
            country = data.get('country', 'Unknown')
            location_node = {
                'id': f"location_{city}_{country}",
                'label': f"{city}, {country}",
                'type': 'location',
                'group': 'location',
                'details': {
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'region': data.get('regionName')
                }
            }
            nodes.append(location_node)
            edges.append({
                'from': f"ip_{ip}",
                'to': f"location_{city}_{country}",
                'label': 'located_in'
            })
            
            # Add ISP node
            if 'isp' in data:
                isp_node = {
                    'id': f"isp_{data['isp']}",
                    'label': data['isp'],
                    'type': 'isp',
                    'group': 'organization'
                }
                nodes.append(isp_node)
                edges.append({
                    'from': f"ip_{ip}",
                    'to': f"isp_{data['isp']}",
                    'label': 'isp'
                })
    
    except Exception as e:
        print(f"Error in ip_lookup: {e}")
    
    return {'nodes': nodes, 'edges': edges}


def execute_dns_records(domain):
    """Execute DNS records lookup"""
    import requests
    nodes = []
    edges = []
    
    try:
        response = requests.get(f"https://api.hackertarget.com/dnslookup/?q={domain}", timeout=10)
        lines = response.text.strip().split('\n')
        
        for line in lines[:10]:
            if 'has address' in line or 'has IPv6' in line:
                parts = line.split()
                if len(parts) >= 4:
                    ip = parts[-1]
                    ip_node = {
                        'id': f"ip_{ip}",
                        'label': ip,
                        'type': 'ip',
                        'group': 'ip'
                    }
                    nodes.append(ip_node)
                    edges.append({
                        'from': f"domain_{domain}",
                        'to': f"ip_{ip}",
                        'label': 'resolves_to'
                    })
    
    except Exception as e:
        print(f"Error in dns_records: {e}")
    
    return {'nodes': nodes, 'edges': edges}


def execute_sublister(domain):
    """Execute subdomain lister"""
    nodes = []
    edges = []
    
    try:
        import sublist3r
        subdomains = sublist3r.main(domain, 40, savefile=None, ports=None, 
                                    silent=True, verbose=False, 
                                    enable_bruteforce=False, engines=None)
        
        for subdomain in (subdomains or [])[:15]:  # Limit to 15
            sub_node = {
                'id': f"domain_{subdomain}",
                'label': subdomain,
                'type': 'subdomain',
                'group': 'domain'
            }
            nodes.append(sub_node)
            edges.append({
                'from': f"domain_{domain}",
                'to': f"domain_{subdomain}",
                'label': 'has_subdomain'
            })
    
    except Exception as e:
        print(f"Error in sublister: {e}")
    
    return {'nodes': nodes, 'edges': edges}


def execute_bitcoin(address):
    """Execute Bitcoin balance lookup"""
    import requests
    nodes = []
    edges = []
    
    try:
        url = f"https://blockchain.info/rawaddr/{address}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Add balance node
        balance = data.get('final_balance', 0) / 100000000
        balance_node = {
            'id': f"balance_{address}",
            'label': f"{balance} BTC",
            'type': 'balance',
            'group': 'financial',
            'details': {
                'tx_count': data.get('n_tx'),
                'total_received': data.get('total_received', 0) / 100000000,
                'total_sent': data.get('total_sent', 0) / 100000000
            }
        }
        nodes.append(balance_node)
        edges.append({
            'from': f"bitcoin_{address}",
            'to': f"balance_{address}",
            'label': 'has_balance'
        })
    
    except Exception as e:
        print(f"Error in bitcoin: {e}")
    
    return {'nodes': nodes, 'edges': edges}


def execute_wappalyzer(url):
    """Execute Wappalyzer tech detection"""
    from Wappalyzer import Wappalyzer, WebPage
    nodes = []
    edges = []
    
    try:
        wappalyzer = Wappalyzer.latest()
        webpage = WebPage.new_from_url(url)
        results = wappalyzer.analyze(webpage)
        
        for tech in list(results)[:10]:
            tech_node = {
                'id': f"tech_{tech}",
                'label': tech,
                'type': 'technology',
                'group': 'technology'
            }
            nodes.append(tech_node)
            edges.append({
                'from': f"domain_{url}",
                'to': f"tech_{tech}",
                'label': 'uses'
            })
    
    except Exception as e:
        print(f"Error in wappalyzer: {e}")
    
    return {'nodes': nodes, 'edges': edges}


if __name__ == '__main__':
    port = int(os.getenv('WEB_PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
