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
        
        # 2. Get DNS records
        try:
            import requests
            dns_response = requests.get(f"https://api.hackertarget.com/dnslookup/?q={domain}", timeout=5)
            if dns_response.status_code == 200:
                dns_lines = dns_response.text.strip().split('\n')
                for line in dns_lines[:5]:  # Limit records
                    if 'has address' in line or 'mail is handled' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            ip = parts[-1].rstrip('.')
                            ip_id = f"ip_{ip}"
                            add_node(ip_id, ip, "ip", {"ip": ip})
                            add_edge(domain_id, ip_id, "resolves_to")
                            results["nodes"].append({"id": ip_id, "label": ip, "type": "ip"})
        except Exception as e:
            pass  # Silently skip DNS lookup errors
        
        # 3. Get subdomains
        try:
            import sublist3r
            import sys
            from io import StringIO
            
            # Capture stdout to suppress sublist3r output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # Exclude DNSdumpster as it's causing errors - use only working engines
            engines = ['baidu', 'yahoo', 'google', 'bing', 'ask', 'netcraft', 'virustotal', 'threatcrowd', 'ssl', 'passivedns']
            
            subdomains = sublist3r.main(domain, 20, None, ports=None, silent=True, verbose=False, enable_bruteforce=False, engines=engines)
            
            # Restore stdout
            sys.stdout = old_stdout
            
            if subdomains:
                for subdomain in subdomains[:10]:  # Limit to 10
                    sub_id = f"subdomain_{subdomain}"
                    add_node(sub_id, subdomain, "subdomain", {"subdomain": subdomain})
                    add_edge(domain_id, sub_id, "has_subdomain")
                    results["nodes"].append({"id": sub_id, "label": subdomain, "type": "subdomain"})
        except Exception as e:
            pass  # Silently skip subdomain enumeration errors
        
        # 4. Get DNS hosts using hackertarget hostsearch
        try:
            import requests
            host_response = requests.get(f"https://api.hackertarget.com/hostsearch/?q={domain}", timeout=5)
            if host_response.status_code == 200:
                host_lines = host_response.text.strip().split('\n')
                for line in host_lines[:15]:  # Limit to 15 hosts
                    if line and ',' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            hostname = parts[0].strip()
                            host_ip = parts[1].strip()
                            
                            # Add hostname node
                            if hostname and hostname != domain:
                                host_id = f"host_{hostname}"
                                add_node(host_id, hostname, "host", {"hostname": hostname, "ip": host_ip})
                                add_edge(domain_id, host_id, "has_host")
                                results["nodes"].append({"id": host_id, "label": hostname, "type": "host"})
                                
                                # Add IP node for the host
                                if host_ip:
                                    ip_id = f"ip_{host_ip}"
                                    # Check if IP node doesn't exist yet
                                    if not any(n["id"] == ip_id for n in graph_data["nodes"]):
                                        add_node(ip_id, host_ip, "ip", {"ip": host_ip})
                                        results["nodes"].append({"id": ip_id, "label": host_ip, "type": "ip"})
                                    add_edge(host_id, ip_id, "resolves_to")
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
        
        # 2. Shodan lookup (if available)
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

def open_browser():
    """Open browser after short delay"""
    import time
    time.sleep(1.5)
    webbrowser.open('http://localhost:5001')

if __name__ == '__main__':
    print("=" * 60)
    print("🌐 OSIF Web Server - Graph Visualization")
    print("=" * 60)
    print("Starting server at http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
