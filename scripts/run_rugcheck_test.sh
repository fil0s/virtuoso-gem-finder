#!/bin/bash

# RugCheck Integration Test Runner
# This script runs the RugCheck integration tests to verify security filtering works correctly

echo "🛡️ RugCheck Integration Test Runner"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup_environment.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if environment file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your API keys."
    echo "   You can copy from config/env.template"
    exit 1
fi

# Check for required API key
if ! grep -q "BIRDEYE_API_KEY=" .env || grep -q "BIRDEYE_API_KEY=$" .env; then
    echo "❌ BIRDEYE_API_KEY not found or empty in .env file"
    echo "   Please add your Birdeye API key to the .env file"
    exit 1
fi

echo "✅ Environment checks passed"
echo ""

# Run the RugCheck integration test
echo "🚀 Running RugCheck Integration Tests..."
echo "========================================"

python scripts/test_rugcheck_integration.py

# Check if test was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ RugCheck integration tests completed successfully!"
    echo ""
    echo "🛡️ Security filtering is now active in your token discovery strategies."
    echo "   This will help filter out potentially risky tokens like:"
    echo "   • Honeypots"
    echo "   • Proxy contracts"
    echo "   • Tokens with ownership issues"
    echo "   • Blacklist/whitelist functions"
    echo "   • High-risk or critical issues"
    echo ""
    echo "📊 The system will now:"
    echo "   • Analyze token security during discovery"
    echo "   • Filter out unhealthy tokens automatically"
    echo "   • Add security scores to discovered tokens"
    echo "   • Log security analysis results"
else
    echo ""
    echo "❌ RugCheck integration tests failed!"
    echo "   Please check the error messages above and resolve any issues."
    exit 1
fi

echo ""
echo "🔗 RugCheck API documentation: https://api.rugcheck.xyz/swagger/index.html"
echo "📋 Test results are logged in the logs/ directory" 