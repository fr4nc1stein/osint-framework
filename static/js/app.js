// Global variables
let network = null;
let nodes = new vis.DataSet([]);
let edges = new vis.DataSet([]);

// Node type colors and icons
const nodeStyles = {
    domain: { color: '#3498db', icon: '\uf0ac', shape: 'dot', size: 25 },
    email: { color: '#e74c3c', icon: '\uf0e0', shape: 'dot', size: 20 },
    ip: { color: '#2ecc71', icon: '\uf233', shape: 'dot', size: 20 },
    subdomain: { color: '#9b59b6', icon: '\uf0ac', shape: 'dot', size: 18 },
    technology: { color: '#f39c12', icon: '\uf013', shape: 'dot', size: 18 },
    location: { color: '#1abc9c', icon: '\uf3c5', shape: 'dot', size: 20 },
    isp: { color: '#34495e', icon: '\uf1eb', shape: 'dot', size: 20 },
    port: { color: '#e67e22', icon: '\uf0c1', shape: 'dot', size: 15 },
    hostname: { color: '#95a5a6', icon: '\uf233', shape: 'dot', size: 18 },
    bitcoin: { color: '#f39c12', icon: '\uf15a', shape: 'dot', size: 22 }
};

// Initialize network
function initNetwork() {
    const container = document.getElementById('network');
    const data = { nodes: nodes, edges: edges };
    
    const options = {
        nodes: {
            font: {
                color: '#e0e0e0',
                size: 14,
                face: 'Segoe UI'
            },
            borderWidth: 2,
            borderWidthSelected: 3,
            shadow: {
                enabled: true,
                color: 'rgba(0,0,0,0.5)',
                size: 10,
                x: 0,
                y: 0
            }
        },
        edges: {
            color: {
                color: '#667eea',
                highlight: '#764ba2',
                hover: '#764ba2'
            },
            width: 2,
            smooth: {
                type: 'continuous',
                roundness: 0.5
            },
            arrows: {
                to: {
                    enabled: true,
                    scaleFactor: 0.5
                }
            },
            font: {
                color: '#8b9dc3',
                size: 11,
                align: 'middle'
            }
        },
        physics: {
            enabled: true,
            barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.3,
                springLength: 150,
                springConstant: 0.04,
                damping: 0.09,
                avoidOverlap: 0.1
            },
            stabilization: {
                iterations: 200,
                updateInterval: 25
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 100,
            hideEdgesOnDrag: true,
            multiselect: true
        }
    };
    
    network = new vis.Network(container, data, options);
    
    // Event listeners
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            showNodeDetails(params.nodes[0]);
        }
    });
    
    network.on('doubleClick', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = nodes.get(nodeId);
            expandNode(node);
        }
    });
    
    // Load existing graph
    loadGraph();
}

// Show loading overlay
function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
    updateStatus('Investigating...', 'warning');
}

// Hide loading overlay
function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
    updateStatus('Ready', 'success');
}

// Update status
function updateStatus(message, type = 'info') {
    const statusElement = document.getElementById('status');
    const icon = statusElement.querySelector('i');
    
    statusElement.innerHTML = `<i class="fas fa-circle"></i> ${message}`;
    
    const colors = {
        success: '#2ecc71',
        warning: '#f39c12',
        error: '#e74c3c',
        info: '#3498db'
    };
    
    icon.style.color = colors[type] || colors.info;
}

// Add nodes to graph
function addNodes(newNodes) {
    newNodes.forEach(node => {
        if (!nodes.get(node.id)) {
            const style = nodeStyles[node.type] || nodeStyles.domain;
            nodes.add({
                id: node.id,
                label: node.label,
                title: `${node.type}: ${node.label}`,
                color: style.color,
                size: style.size,
                shape: style.shape,
                type: node.type
            });
        }
    });
    updateStats();
}

// Load graph from server
async function loadGraph() {
    try {
        const response = await fetch('/api/graph');
        const data = await response.json();
        
        // Clear current data
        nodes.clear();
        edges.clear();
        
        // Add nodes
        data.nodes.forEach(node => {
            const style = nodeStyles[node.type] || nodeStyles.domain;
            nodes.add({
                id: node.id,
                label: node.label,
                title: `${node.type}: ${node.label}`,
                color: style.color,
                size: style.size,
                shape: style.shape,
                type: node.type,
                data: node.data
            });
        });
        
        // Add edges
        data.edges.forEach(edge => {
            edges.add({
                id: `${edge.from}_${edge.to}_${edge.relationship}`,
                from: edge.from,
                to: edge.to,
                label: edge.relationship.replace(/_/g, ' '),
                title: edge.relationship
            });
        });
        
        updateStats();
        
    } catch (error) {
        console.error('Error loading graph:', error);
        updateStatus('Error loading graph', 'error');
    }
}

// Investigate domain
async function investigateDomain() {
    const domain = document.getElementById('domainInput').value.trim();
    
    if (!domain) {
        alert('Please enter a domain');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/investigate/domain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
            updateStatus('Investigation failed', 'error');
        } else {
            await loadGraph();
            updateStatus(`Found ${data.nodes.length} related entities`, 'success');
            
            // Focus on the domain node
            if (network) {
                network.focus(`domain_${domain}`, {
                    scale: 1.0,
                    animation: true
                });
            }
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error investigating domain: ' + error.message);
        updateStatus('Investigation failed', 'error');
    } finally {
        hideLoading();
    }
}

// Investigate IP
async function investigateIP() {
    const ip = document.getElementById('ipInput').value.trim();
    
    if (!ip) {
        alert('Please enter an IP address');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/investigate/ip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
            updateStatus('Investigation failed', 'error');
        } else {
            await loadGraph();
            updateStatus(`Found ${data.nodes.length} related entities`, 'success');
            
            if (network) {
                network.focus(`ip_${ip}`, {
                    scale: 1.0,
                    animation: true
                });
            }
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error investigating IP: ' + error.message);
        updateStatus('Investigation failed', 'error');
    } finally {
        hideLoading();
    }
}

// Investigate email
async function investigateEmail() {
    const email = document.getElementById('emailInput').value.trim();
    
    if (!email) {
        alert('Please enter an email address');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/investigate/email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
            updateStatus('Investigation failed', 'error');
        } else {
            await loadGraph();
            updateStatus(`Found ${data.nodes.length} related entities`, 'success');
            
            if (network) {
                network.focus(`email_${email}`, {
                    scale: 1.0,
                    animation: true
                });
            }
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error investigating email: ' + error.message);
        updateStatus('Investigation failed', 'error');
    } finally {
        hideLoading();
    }
}

// Investigate Bitcoin
async function investigateBitcoin() {
    const address = document.getElementById('bitcoinInput').value.trim();
    
    if (!address) {
        alert('Please enter a Bitcoin address');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/investigate/bitcoin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
            updateStatus('Investigation failed', 'error');
        } else {
            await loadGraph();
            updateStatus(`Bitcoin balance: ${data.balance} BTC`, 'success');
            
            if (network) {
                network.focus(`bitcoin_${address}`, {
                    scale: 1.0,
                    animation: true
                });
            }
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error investigating Bitcoin address: ' + error.message);
        updateStatus('Investigation failed', 'error');
    } finally {
        hideLoading();
    }
}

// Show node details
async function showNodeDetails(nodeId) {
    try {
        const response = await fetch(`/api/node/${nodeId}`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Error:', data.error);
            return;
        }
        
        const node = data.node;
        const detailsPanel = document.getElementById('nodeDetails');
        const detailsContent = document.getElementById('detailsContent');
        
        let html = `
            <div class="detail-item">
                <strong>Type:</strong>
                <span>${node.type}</span>
            </div>
            <div class="detail-item">
                <strong>Label:</strong>
                <span>${node.label}</span>
            </div>
            <div class="detail-item">
                <strong>ID:</strong>
                <span style="font-size: 0.85em; word-break: break-all;">${node.id}</span>
            </div>
        `;
        
        // Add node data
        if (node.data && Object.keys(node.data).length > 0) {
            html += '<div class="detail-item"><strong>Additional Data:</strong></div>';
            for (const [key, value] of Object.entries(node.data)) {
                if (value && key !== 'timestamp') {
                    html += `
                        <div class="detail-item">
                            <strong>${key.replace(/_/g, ' ')}:</strong>
                            <span>${JSON.stringify(value, null, 2)}</span>
                        </div>
                    `;
                }
            }
        }
        
        // Add connection info
        const totalConnections = data.edges_from.length + data.edges_to.length;
        html += `
            <div class="detail-item">
                <strong>Connections:</strong>
                <span>${totalConnections}</span>
            </div>
        `;
        
        if (data.edges_from.length > 0) {
            html += '<div class="detail-item"><strong>Outgoing:</strong>';
            data.edges_from.forEach(edge => {
                html += `<div style="margin: 5px 0; padding-left: 10px;">→ ${edge.relationship}</div>`;
            });
            html += '</div>';
        }
        
        if (data.edges_to.length > 0) {
            html += '<div class="detail-item"><strong>Incoming:</strong>';
            data.edges_to.forEach(edge => {
                html += `<div style="margin: 5px 0; padding-left: 10px;">← ${edge.relationship}</div>`;
            });
            html += '</div>';
        }
        
        detailsContent.innerHTML = html;
        detailsPanel.style.display = 'block';
        
    } catch (error) {
        console.error('Error fetching node details:', error);
    }
}

// Close details panel
function closeDetails() {
    document.getElementById('nodeDetails').style.display = 'none';
}

// Expand node (double-click to investigate further)
function expandNode(node) {
    if (node.type === 'domain') {
        document.getElementById('domainInput').value = node.data.domain || node.label;
        investigateDomain();
    } else if (node.type === 'ip') {
        document.getElementById('ipInput').value = node.data.ip || node.label;
        investigateIP();
    } else if (node.type === 'email') {
        document.getElementById('emailInput').value = node.data.email || node.label;
        investigateEmail();
    }
}

// Clear graph
async function clearGraph() {
    if (!confirm('Are you sure you want to clear the entire graph?')) {
        return;
    }
    
    try {
        await fetch('/api/graph/clear', { method: 'POST' });
        nodes.clear();
        edges.clear();
        updateStats();
        updateStatus('Graph cleared', 'info');
        closeDetails();
    } catch (error) {
        console.error('Error clearing graph:', error);
        alert('Error clearing graph: ' + error.message);
    }
}

// Export graph
async function exportGraph() {
    try {
        const response = await fetch('/api/export/graph');
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `osif-graph-${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        updateStatus('Graph exported', 'success');
        
    } catch (error) {
        console.error('Error exporting graph:', error);
        alert('Error exporting graph: ' + error.message);
    }
}

// Fit network to view
function fitNetwork() {
    if (network) {
        network.fit({
            animation: {
                duration: 1000,
                easingFunction: 'easeInOutQuad'
            }
        });
    }
}

// Update stats
function updateStats() {
    document.getElementById('nodeCount').textContent = nodes.length;
    document.getElementById('edgeCount').textContent = edges.length;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initNetwork();
    
    // Add Enter key support for inputs
    document.getElementById('domainInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') investigateDomain();
    });
    
    document.getElementById('ipInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') investigateIP();
    });
    
    document.getElementById('emailInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') investigateEmail();
    });
    
    document.getElementById('bitcoinInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') investigateBitcoin();
    });
    
    updateStatus('Ready', 'success');
});
