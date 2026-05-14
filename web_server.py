#!/usr/bin/env python3
"""
OSIF Web Server - Graph-based OSINT Visualization
Maltego-style interface for OSINT data visualization and exploration
"""
import os
import json
import warnings
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import threading
import webbrowser
from datetime import datetime

# Suppress warnings from third-party libraries
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Note: We use direct API calls instead of importing module classes
# to avoid import path issues with hyphenated directory names

load_dotenv()

app = Flask(__name__)
CORS(app)

# Graph storage (in-memory for now, can be moved to database)
graph_data = {
    "nodes": [],
    "edges": []
}

# Node ID counter
node_counter = {"count": 0}

def get_next_id():
    """Generate unique node ID"""
    node_counter["count"] += 1
    return node_counter["count"]

def add_node(node_id, label, node_type, data=None):
    """Add node to graph"""
    node = {
        "id": node_id,
        "label": label,
        "type": node_type,
        "data": data or {},
        "timestamp": datetime.now().isoformat()
    }
    # Check if node already exists
    existing = next((n for n in graph_data["nodes"] if n["id"] == node_id), None)
    if not existing:
        graph_data["nodes"].append(node)
    return node

def add_edge(from_id, to_id, relationship, data=None):
    """Add edge between nodes"""
    edge = {
        "from": from_id,
        "to": to_id,
        "relationship": relationship,
        "data": data or {},
        "timestamp": datetime.now().isoformat()
    }
    # Check if edge already exists
    existing = next((e for e in graph_data["edges"] 
                    if e["from"] == from_id and e["to"] == to_id and e["relationship"] == relationship), None)
    if not existing:
        graph_data["edges"].append(edge)
    return edge

@app.route('/')
def index():
    """Main graph visualization page"""
    return render_template('index.html')

@app.route('/api/graph', methods=['GET'])
def get_graph():
    """Get current graph data"""
    return jsonify(graph_data)

@app.route('/api/graph/clear', methods=['POST'])
def clear_graph():
    """Clear all graph data"""
    graph_data["nodes"].clear()
    graph_data["edges"].clear()
    node_counter["count"] = 0
    return jsonify({"status": "success", "message": "Graph cleared"})

@app.route('/api/investigate/domain', methods=['POST'])
def investigate_domain():
    """Investigate a domain - find emails, subdomains, DNS records, etc."""
    data = request.json
    domain = data.get('domain')
    
    if not domain:
        return jsonify({"error": "Domain is required"}), 400
    
    # Create domain node
    domain_id = f"domain_{domain}"
    add_node(domain_id, domain, "domain", {"value": domain})
    
    results = {"nodes": [], "edges": []}
    
    try:
        # 1. Find emails using Tomba
        if os.getenv('TOMBA_API_KEY') and os.getenv('TOMBA_SECRET_KEY'):
            try:
                from tomba.client import Client
                from tomba.services.domain import Domain
                
                client = Client()
                client.set_key(os.getenv('TOMBA_API_KEY'))
                client.set_secret(os.getenv('TOMBA_SECRET_KEY'))
                domain_service = Domain(client)
                
                result = domain_service.domain_search(domain=domain, limit=10)
                
                if result and 'data' in result and 'emails' in result['data']:
                    for email_data in result['data']['emails'][:10]:  # Limit to 10
                        email = email_data.get('email')
                        if email:
                            email_id = f"email_{email}"
                            add_node(email_id, email, "email", {
                                "email": email,
                                "first_name": email_data.get('first_name'),
                                "last_name": email_data.get('last_name'),
                                "position": email_data.get('position'),
                                "department": email_data.get('department'),
                                "type": email_data.get('type')
                            })
                            add_edge(domain_id, email_id, "has_email")
                            results["nodes"].append({"id": email_id, "label": email, "type": "email"})
            except Exception as e:
                pass  # Silently skip email search errors
        
        # 2. Get DNS records using dnspython (no API needed)
        try:
            import dns.resolver
            
            # Query A records (IPv4)
            try:
                answers = dns.resolver.resolve(domain, 'A', lifetime=5)
                for rdata in list(answers)[:5]:  # Limit to 5 IPs
                    ip = str(rdata)
                    ip_id = f"ip_{ip}"
                    add_node(ip_id, ip, "ip", {"ip": ip, "record_type": "A"})
                    add_edge(domain_id, ip_id, "resolves_to")
                    results["nodes"].append({"id": ip_id, "label": ip, "type": "ip"})
            except:
                pass
            
            # Query MX records (Mail servers)
            try:
                mx_answers = dns.resolver.resolve(domain, 'MX', lifetime=5)
                for rdata in list(mx_answers)[:3]:  # Limit to 3 MX
                    mx_host = str(rdata.exchange).rstrip('.')
                    mx_id = f"host_{mx_host}"
                    add_node(mx_id, mx_host, "host", {"hostname": mx_host, "record_type": "MX", "priority": rdata.preference})
                    add_edge(domain_id, mx_id, "mail_server")
                    results["nodes"].append({"id": mx_id, "label": f"{mx_host} (MX)", "type": "host"})
            except:
                pass
        except Exception as e:
            pass  # Silently skip DNS lookup errors
        
        # 3. Get subdomains/hosts from Certificate Transparency (crt.sh - unlimited, free)
        try:
            import requests
            import dns.resolver
            crt_url = f"https://crt.sh/?q=%.{domain}&output=json"
            crt_response = requests.get(crt_url, timeout=10)
            
            if crt_response.status_code == 200:
                crt_data = crt_response.json()
                seen_hosts = set()
                
                for cert in crt_data[:50]:  # Limit to 50 certificates
                    # Extract from name_value (can be multiline)
                    if 'name_value' in cert:
                        names = cert['name_value'].split('\n')
                        for name in names:
                            name = name.strip().lower()
                            # Only add valid subdomains/hosts
                            if name and domain in name and name not in seen_hosts and name != domain:
                                seen_hosts.add(name)
                                
                                # Determine if subdomain or host
                                node_type = "subdomain" if name.endswith(f".{domain}") else "host"
                                host_id = f"{node_type}_{name}"
                                
                                add_node(host_id, name, node_type, {
                                    "hostname": name,
                                    "source": "crt.sh",
                                    "issuer": cert.get('issuer_name', '')[:50]
                                })
                                add_edge(domain_id, host_id, "has_certificate")
                                results["nodes"].append({"id": host_id, "label": name, "type": node_type})
                                
                                # 3rd LEVEL: Get IPs for each subdomain/host (limit to first 5 subdomains)
                                if len(seen_hosts) <= 5:
                                    try:
                                        subdomain_answers = dns.resolver.resolve(name, 'A', lifetime=3)
                                        for rdata in list(subdomain_answers)[:2]:  # Limit to 2 IPs per subdomain
                                            subdomain_ip = str(rdata)
                                            subdomain_ip_id = f"ip_{subdomain_ip}"
                                            
                                            # Add IP node if not exists
                                            if not any(n["id"] == subdomain_ip_id for n in graph_data["nodes"]):
                                                add_node(subdomain_ip_id, subdomain_ip, "ip", {
                                                    "ip": subdomain_ip,
                                                    "parent_subdomain": name
                                                })
                                                results["nodes"].append({"id": subdomain_ip_id, "label": subdomain_ip, "type": "ip"})
                                            
                                            # Create edge from subdomain to IP
                                            add_edge(host_id, subdomain_ip_id, "resolves_to")
                                    except:
                                        pass  # Skip DNS errors for subdomains
                                
                                if len(seen_hosts) >= 15:  # Limit to 15 unique hosts
                                    break
                    
                    if len(seen_hosts) >= 15:
                        break
        except Exception as e:
            pass  # Silently skip host search errors
        
        results["status"] = "success"
        results["domain"] = domain
        results["total_nodes"] = len(graph_data["nodes"])
        results["total_edges"] = len(graph_data["edges"])
        
        print(f"[DEBUG] Investigation complete: {len(results['nodes'])} new nodes discovered")
        print(f"[DEBUG] Total graph size: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify(results)

@app.route('/api/investigate/ip', methods=['POST'])
def investigate_ip():
    """Investigate an IP address"""
    data = request.json
    ip = data.get('ip')
    
    if not ip:
        return jsonify({"error": "IP address is required"}), 400
    
    ip_id = f"ip_{ip}"
    add_node(ip_id, ip, "ip", {"ip": ip})
    
    results = {"nodes": [], "edges": []}
    
    try:
        # 1. Get IP info
        import requests
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            ip_data = response.json()
            
            # Update node with data
            node = next((n for n in graph_data["nodes"] if n["id"] == ip_id), None)
            if node:
                node["data"].update(ip_data)
            
            # Add location node
            if ip_data.get('country'):
                location = f"{ip_data.get('city', 'Unknown')}, {ip_data.get('country')}"
                loc_id = f"location_{location.replace(' ', '_')}"
                add_node(loc_id, location, "location", {
                    "city": ip_data.get('city'),
                    "country": ip_data.get('country'),
                    "lat": ip_data.get('lat'),
                    "lon": ip_data.get('lon')
                })
                add_edge(ip_id, loc_id, "located_in")
                results["nodes"].append({"id": loc_id, "label": location, "type": "location"})
            
            # Add ISP node
            if ip_data.get('isp'):
                isp = ip_data.get('isp')
                isp_id = f"isp_{isp.replace(' ', '_')}"
                add_node(isp_id, isp, "isp", {"isp": isp, "org": ip_data.get('org')})
                add_edge(ip_id, isp_id, "provided_by")
                results["nodes"].append({"id": isp_id, "label": isp, "type": "isp"})
        
        # 2. AbuseIPDB reputation check (if available)
        if os.getenv('ABUSEIPDB_API_KEY'):
            try:
                import requests
                abuseipdb_url = 'https://api.abuseipdb.com/api/v2/check'
                abuseipdb_headers = {
                    'Accept': 'application/json',
                    'Key': os.getenv('ABUSEIPDB_API_KEY')
                }
                abuseipdb_params = {
                    'ipAddress': ip,
                    'maxAgeInDays': 90,
                    'verbose': False
                }
                
                abuseipdb_response = requests.get(abuseipdb_url, headers=abuseipdb_headers, 
                                                  params=abuseipdb_params, timeout=10)
                
                if abuseipdb_response.status_code == 200:
                    abuseipdb_data = abuseipdb_response.json().get('data', {})
                    
                    # Update IP node with reputation data
                    node = next((n for n in graph_data["nodes"] if n["id"] == ip_id), None)
                    if node:
                        node["data"]["abuseipdb"] = {
                            "abuse_score": abuseipdb_data.get('abuseConfidenceScore', 0),
                            "total_reports": abuseipdb_data.get('totalReports', 0),
                            "is_whitelisted": abuseipdb_data.get('isWhitelisted', False),
                            "usage_type": abuseipdb_data.get('usageType', 'Unknown')
                        }
                    
                    # Add threat node if abuse score is significant
                    abuse_score = abuseipdb_data.get('abuseConfidenceScore', 0)
                    if abuse_score > 25:
                        threat_level = "High Risk" if abuse_score >= 75 else "Medium Risk"
                        threat_id = f"threat_{ip}"
                        add_node(threat_id, f"{threat_level} ({abuse_score}%)", "threat", {
                            "abuse_score": abuse_score,
                            "total_reports": abuseipdb_data.get('totalReports', 0),
                            "threat_level": threat_level
                        })
                        add_edge(ip_id, threat_id, "has_reputation")
                        results["nodes"].append({"id": threat_id, "label": f"{threat_level}", "type": "threat"})
                        
            except Exception as e:
                pass  # Silently skip AbuseIPDB errors
        
        # 3. Shodan lookup (if available)
        if os.getenv('SHODAN_API_KEY'):
            try:
                from shodan import Shodan
                api = Shodan(os.getenv('SHODAN_API_KEY'))
                shodan_data = api.host(ip)
                
                # Add port nodes
                for port in shodan_data.get('ports', [])[:5]:
                    port_id = f"port_{ip}_{port}"
                    add_node(port_id, f"Port {port}", "port", {"port": port})
                    add_edge(ip_id, port_id, "has_open_port")
                    results["nodes"].append({"id": port_id, "label": f"Port {port}", "type": "port"})
                
                # Add hostname nodes
                for hostname in shodan_data.get('hostnames', [])[:3]:
                    host_id = f"hostname_{hostname}"
                    add_node(host_id, hostname, "hostname", {"hostname": hostname})
                    add_edge(ip_id, host_id, "has_hostname")
                    results["nodes"].append({"id": host_id, "label": hostname, "type": "hostname"})
                    
            except Exception as e:
                pass  # Silently skip Shodan errors
        
        results["status"] = "success"
        results["ip"] = ip
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify(results)

@app.route('/api/investigate/email', methods=['POST'])
def investigate_email():
    """Investigate an email address"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    email_id = f"email_{email}"
    add_node(email_id, email, "email", {"email": email})
    
    results = {"nodes": [], "edges": []}
    
    try:
        # Extract domain from email
        domain = email.split('@')[1] if '@' in email else None
        
        if domain:
            domain_id = f"domain_{domain}"
            add_node(domain_id, domain, "domain", {"domain": domain})
            add_edge(email_id, domain_id, "belongs_to")
            results["nodes"].append({"id": domain_id, "label": domain, "type": "domain"})
        
        results["status"] = "success"
        results["email"] = email
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify(results)

@app.route('/api/investigate/bitcoin', methods=['POST'])
def investigate_bitcoin():
    """Investigate a Bitcoin address"""
    data = request.json
    address = data.get('address')
    
    if not address:
        return jsonify({"error": "Bitcoin address is required"}), 400
    
    btc_id = f"bitcoin_{address}"
    add_node(btc_id, address[:16] + "...", "bitcoin", {"address": address})
    
    results = {"nodes": [], "edges": []}
    
    try:
        import requests
        url = f"https://blockchain.info/rawaddr/{address}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            btc_data = response.json()
            
            # Update node with balance info
            node = next((n for n in graph_data["nodes"] if n["id"] == btc_id), None)
            if node:
                node["data"].update({
                    "balance": btc_data.get('final_balance', 0) / 100000000,
                    "total_received": btc_data.get('total_received', 0) / 100000000,
                    "total_sent": btc_data.get('total_sent', 0) / 100000000,
                    "n_tx": btc_data.get('n_tx', 0)
                })
            
            results["status"] = "success"
            results["address"] = address
            results["balance"] = btc_data.get('final_balance', 0) / 100000000
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify(results)

@app.route('/api/node/<node_id>', methods=['GET'])
def get_node_details(node_id):
    """Get detailed information about a node"""
    node = next((n for n in graph_data["nodes"] if n["id"] == node_id), None)
    
    if not node:
        return jsonify({"error": "Node not found"}), 404
    
    # Get connected edges
    edges_from = [e for e in graph_data["edges"] if e["from"] == node_id]
    edges_to = [e for e in graph_data["edges"] if e["to"] == node_id]
    
    return jsonify({
        "node": node,
        "edges_from": edges_from,
        "edges_to": edges_to
    })

@app.route('/api/export/graph', methods=['GET'])
def export_graph():
    """Export graph data as JSON"""
    return jsonify({
        "graph": graph_data,
        "exported_at": datetime.now().isoformat(),
        "node_count": len(graph_data["nodes"]),
        "edge_count": len(graph_data["edges"])
    })

def open_browser(port):
    """Open browser after short delay"""
    import time
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{port}')

if __name__ == '__main__':
    import argparse
    import socket
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='OSIF Web Server - Graph Visualization')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on (default: 5001)')
    args = parser.parse_args()
    
    port = args.port
    
    print("=" * 60)
    print("🌐 OSIF Web Server - Graph Visualization")
    print("=" * 60)
    print(f"Starting server at http://localhost:{port}")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Open browser in background
    threading.Thread(target=lambda: open_browser(port), daemon=True).start()
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ Port {port} is already in use!")
            print(f"💡 Try running with a different port: python3 web_server.py --port {port + 1}")
        else:
            raise
