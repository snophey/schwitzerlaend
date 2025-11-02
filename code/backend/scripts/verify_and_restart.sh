#!/bin/bash

echo "=================================================="
echo "  Server Restart Verification Script"
echo "=================================================="
echo ""

# Check if server is running
echo "1. Checking if server is running on port 8000..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✓ Server is running"
    
    echo ""
    echo "2. Checking if history router is loaded..."
    if curl -s http://localhost:8000/history/health | grep -q "ok"; then
        echo "   ✓ History router IS loaded!"
        echo ""
        echo "   Server is up to date. You can run the tests:"
        echo "   python scripts/test_history_workflow.py"
    else
        echo "   ✗ History router is NOT loaded!"
        echo ""
        echo "   ⚠️  THE SERVER NEEDS TO BE RESTARTED ⚠️"
        echo ""
        echo "   Steps to restart:"
        echo "   1. Go to the terminal running the server"
        echo "   2. Press Ctrl+C to stop it"
        echo "   3. Run: python main.py"
        echo "   4. Then run this script again to verify"
    fi
else
    echo "   ✗ Server is NOT running!"
    echo ""
    echo "   Please start the server:"
    echo "   python main.py"
fi

echo ""
echo "=================================================="
