// OSIF Graph Visualization
let network = null;
let nodes = new vis.DataSet([]);
let edges = new vis.DataSet([]);
let selectedNode = null;

// Node colors by type
const nodeColors = {
    domain: '#2980b9',        // Blue - Main domain
    subdomain: '#3498db',     // Light Blue - Subdomains
    host: '#9b59b6',          // Purple - Hosts
    ip: '#e74c3c',            // Red - IP Addresses
    email: '#f39c12',         // Orange - Emails
    error: '#c0392b',         // Dark Red - Errors/API Limits
    port: '#8e44ad',          // Dark Purple - Ports
    location: '#1abc9c',      // Teal - Locations
    isp: '#34495e',           // Dark Gray - ISP
    organization: '#16a085',  // Dark Teal - Organizations
    technology: '#27ae60',    // Green - Technologies
    bitcoin: '#f1c40f',       // Gold - Bitcoin
    ethereum: '#9b59b6',      // Purple - Ethereum
    balance: '#d35400',       // Orange-Red - Balance
    hostname: '#5dade2',      // Sky Blue - Hostnames
    phone: '#c0392b',         // Dark Red - Phone
    hash: '#7f8c8d',          // Gray - Hashes
    default: '#95a5a6'        // Light Gray - Default
};

// Initialize the network
function initNetwork() {
    try {
        console.log('Initializing OSIF Graph...');
        
        const container = document.getElementById('mynetwork');
        if (!container) {
            console.error('Graph container #mynetwork not found!');
            return;
        }
        
        const data = {
            nodes: nodes,
            edges: edges
        };
        
        const options = {
            nodes: {
                shape: 'dot',
                size: 20,
                font: {
                    size: 14,
                    color: '#2c3e50'
                },
                borderWidth: 2,
                shadow: true
            },
            edges: {
                width: 2,
                color: {
                    color: '#95a5a6',
                    highlight: '#2c3e50'
                },
                arrows: {
                    to: {enabled: true, scaleFactor: 0.5}
                },
                font: {
                    size: 11,
                    align: 'middle'
                },
                smooth: {
                    type: 'continuous'
                }
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -8000,
                    centralGravity: 0.3,
                    springLength: 150,
                    springConstant: 0.04
                },
                stabilization: {
                    iterations: 150
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                navigationButtons: true,
                keyboard: true
            }
        };
        
        network = new vis.Network(container, data, options);
        console.log('Graph network initialized successfully');
        
        // Event listeners
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                selectNode(nodeId);
            }
        });
        
        network.on('doubleClick', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                expandNode(nodeId);
            }
        });
        
        updateStats();
        console.log('Graph initialization complete');
    } catch (error) {
        console.error('Error initializing graph:', error);
    }
}

// Add node to graph
function addNode(id, label, type, data = {}) {
    if (!nodes.get(id)) {
        nodes.add({
            id: id,
            label: label,
            color: {
                background: nodeColors[type] || nodeColors.default,
                border: darkenColor(nodeColors[type] || nodeColors.default),
                highlight: {
                    background: lightenColor(nodeColors[type] || nodeColors.default),
                    border: nodeColors[type] || nodeColors.default
                }
            },
            type: type,
            data: data,
            title: `${type}: ${label}` // Tooltip
        });
        updateStats();
    }
}

// Add edge to graph
function addEdge(from, to, label) {
    const edgeId = `${from}-${to}-${label}`;
    if (!edges.get(edgeId)) {
        edges.add({
            id: edgeId,
            from: from,
            to: to,
            label: label,
            title: label
        });
        updateStats();
    }
}

// Investigate Domain
async function investigateDomain() {
    const domain = document.getElementById('domain-input').value.trim();
    if (!domain) {
        alert('Please enter a domain');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/investigate/domain', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({domain: domain})
        });
        
        const data = await response.json();
        
        console.log('Domain investigation response:', data);
        
        if (data.status === 'success') {
            // Main domain node is already added by backend
            await refreshGraph();
            const msg = `Domain ${domain} investigated! Found ${data.total_nodes || 0} total nodes, ${data.total_edges || 0} edges`;
            showNotification(msg, 'success');
            console.log(msg);
        } else {
            showNotification('Investigation failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Investigate IP
async function investigateIP() {
    const ip = document.getElementById('ip-input').value.trim();
    if (!ip) {
        alert('Please enter an IP address');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/investigate/ip', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ip: ip})
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            refreshGraph();
            showNotification(`IP ${ip} investigated successfully!`, 'success');
        } else {
            showNotification('Investigation failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Investigate Email
async function investigateEmail() {
    const email = document.getElementById('email-input').value.trim();
    if (!email) {
        alert('Please enter an email address');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/investigate/email', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: email})
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            refreshGraph();
            showNotification(`Email ${email} investigated successfully!`, 'success');
        } else {
            showNotification('Investigation failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Investigate Bitcoin
async function investigateBitcoin() {
    const address = document.getElementById('bitcoin-input').value.trim();
    if (!address) {
        alert('Please enter a Bitcoin address');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/investigate/bitcoin', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({address: address})
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            refreshGraph();
            showNotification(`Bitcoin address investigated! Balance: ${data.balance} BTC`, 'success');
        } else {
            showNotification('Investigation failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Refresh graph from server
async function refreshGraph() {
    try {
        const response = await fetch('/api/graph');
        const data = await response.json();
        
        console.log('Refreshing graph with data:', data);
        console.log('Nodes:', data.nodes.length, 'Edges:', data.edges.length);
        
        // Clear and reload
        nodes.clear();
        edges.clear();
        
        // Add nodes
        data.nodes.forEach(node => {
            console.log('Adding node:', node.id, node.label, node.type);
            addNode(node.id, node.label, node.type, node.data);
        });
        
        // Add edges
        data.edges.forEach(edge => {
            console.log('Adding edge:', edge.from, '->', edge.to, '(' + edge.relationship + ')');
            addEdge(edge.from, edge.to, edge.relationship);
        });
        
        updateStats();
        
        if (network) {
            network.fit();
        }
        
        console.log('Graph refreshed. Vis.js nodes:', nodes.length, 'edges:', edges.length);
    } catch (error) {
        console.error('Error refreshing graph:', error);
    }
}

// Select and show node details
async function selectNode(nodeId) {
    selectedNode = nodeId;
    
    try {
        const response = await fetch(`/api/node/${nodeId}`);
        const data = await response.json();
        
        if (data.node) {
            displayNodeDetails(data.node, data.edges_from, data.edges_to);
        }
    } catch (error) {
        console.error('Error fetching node details:', error);
    }
}

// Display node details
function displayNodeDetails(node, edgesFrom, edgesTo) {
    const detailsDiv = document.getElementById('node-details');
    document.getElementById('selected-label').textContent = node.label;
    
    let html = `
        <span class="node-type-badge">${node.type.toUpperCase()}</span>
        <div class="detail-item">
            <div class="detail-label">Label</div>
            <div class="detail-value">${node.label}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">ID</div>
            <div class="detail-value" style="font-size: 0.8rem;">${node.id}</div>
        </div>
    `;
    
    // Display data fields
    if (node.data && Object.keys(node.data).length > 0) {
        for (const [key, value] of Object.entries(node.data)) {
            if (value !== null && value !== undefined && value !== '') {
                html += `
                    <div class="detail-item">
                        <div class="detail-label">${key.replace(/_/g, ' ').toUpperCase()}</div>
                        <div class="detail-value">${JSON.stringify(value)}</div>
                    </div>
                `;
            }
        }
    }
    
    // Connections
    html += `<h3 style="margin-top: 1rem;">🔗 Connections</h3>`;
    html += `<p><strong>Outgoing:</strong> ${edgesFrom.length}</p>`;
    html += `<p><strong>Incoming:</strong> ${edgesTo.length}</p>`;
    
    detailsDiv.innerHTML = html;
}

// Expand node (investigate further)
function expandNode(nodeId) {
    const node = nodes.get(nodeId);
    if (!node) return;
    
    // Auto-fill the appropriate input based on node type
    switch(node.type) {
        case 'domain':
        case 'subdomain':
            document.getElementById('domain-input').value = node.label;
            break;
        case 'ip':
            document.getElementById('ip-input').value = node.label;
            break;
        case 'email':
            document.getElementById('email-input').value = node.label;
            break;
        case 'bitcoin':
            document.getElementById('bitcoin-input').value = node.data.address || node.label;
            break;
    }
    
    showNotification(`Double-click detected! Input filled with: ${node.label}`, 'info');
}

// Clear graph
async function clearGraph() {
    if (confirm('Are you sure you want to clear the entire graph?')) {
        try {
            await fetch('/api/graph/clear', {method: 'POST'});
            nodes.clear();
            edges.clear();
            document.getElementById('node-details').innerHTML = '<p class="placeholder">Click on a node to see details</p>';
            document.getElementById('selected-label').textContent = 'None';
            updateStats();
            showNotification('Graph cleared', 'success');
        } catch (error) {
            showNotification('Error clearing graph: ' + error.message, 'error');
        }
    }
}

// Export graph
async function exportGraph() {
    try {
        const response = await fetch('/api/export/graph');
        const data = await response.json();
        
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `osif-graph-${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showNotification('Graph exported successfully!', 'success');
    } catch (error) {
        showNotification('Error exporting graph: ' + error.message, 'error');
    }
}

// Fit view
function fitView() {
    if (network) {
        network.fit({animation: true});
    }
}

// Update statistics
function updateStats() {
    document.getElementById('node-count').textContent = nodes.length;
    document.getElementById('edge-count').textContent = edges.length;
}

// Show/hide loading
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple console log for now - can be enhanced with toast notifications
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // You can add a toast library like toastr.js for better notifications
    if (type === 'error') {
        alert(`Error: ${message}`);
    }
}

// Color utilities
function darkenColor(color) {
    // Simple darken by reducing RGB values
    return color;
}

function lightenColor(color) {
    // Simple lighten by increasing RGB values
    return color;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== OSIF Graph Starting ===');
    console.log('DOM Content Loaded');
    
    // Check if vis.js is loaded
    if (typeof vis === 'undefined') {
        console.error('ERROR: vis.js library not loaded! Check your internet connection.');
        alert('Error: Graph library not loaded. Please refresh the page.');
        return;
    }
    
    console.log('vis.js library detected');
    
    initNetwork();
    console.log('OSIF Graph initialized successfully');
    
    // Add keyboard shortcuts
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const activeElement = document.activeElement;
            if (activeElement.id === 'domain-input') investigateDomain();
            else if (activeElement.id === 'ip-input') investigateIP();
            else if (activeElement.id === 'email-input') investigateEmail();
            else if (activeElement.id === 'bitcoin-input') investigateBitcoin();
        }
    });
    
    console.log('Event listeners registered');
});
