#!/bin/bash

# OSIF Web Server Startup Script
# This script starts the OSIF web interface with graph visualization

echo "========================================"
echo "  OSIF Web Interface"
echo "  Graph-based OSINT Visualization"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ -d "venv" ] || [ -d ".venv" ]; then
    echo "✓ Virtual environment detected"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    echo "✓ Virtual environment activated"
else
    echo "⚠ No virtual environment found"
    echo "  Consider creating one: python3 -m venv venv"
    echo ""
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠ Warning: .env file not found"
    echo "  Some features may not work without API keys"
    echo "  Run './osif' first to set up your API keys"
    echo ""
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ Flask not installed. Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting web server..."
echo "→ URL: http://localhost:5000"
echo "→ Press Ctrl+C to stop"
echo ""

# Start the web server
python3 web_server.py
