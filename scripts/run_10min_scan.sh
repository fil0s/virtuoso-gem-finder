#!/bin/bash

# 10-Minute Interval Token Scanner with RugCheck Security Filtering
# This script runs continuous token discovery and analysis every 10 minutes
# with integrated RugCheck security filtering to avoid risky tokens

echo "🛡️ 10-MINUTE TOKEN SCANNER WITH RUGCHECK SECURITY"
echo "=================================================="

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

# Check if config file exists
if [ ! -f "config/config.yaml" ]; then
    echo "📋 Config file not found, creating from template..."
    cp config/config.example.yaml config/config.yaml
    echo "✅ Created config/config.yaml - using default settings"
fi

# Create necessary directories
mkdir -p logs data debug

echo "✅ Environment checks passed"
echo ""

# Display configuration
echo "📊 SCAN CONFIGURATION"
echo "===================="
echo "   • Scan Interval: 10 minutes"
echo "   • Security Filtering: RugCheck API enabled"
echo "   • Token Discovery: All strategies active"
echo "   • Risk Management: Conservative approach"
echo "   • Logging: Structured logs in logs/ directory"
echo ""

# Set environment variables for 10-minute scanning
export SCAN_INTERVAL_MINUTES=10
export ENHANCED_TIMEFRAMES=true

# Display security features
echo "🛡️ SECURITY FEATURES ACTIVE"
echo "============================"
echo "   • RugCheck API integration for token security analysis"
echo "   • Automatic filtering of honeypots and rug pulls"
echo "   • Risk level classification (SAFE/LOW/MEDIUM/HIGH/CRITICAL)"
echo "   • Deal-breaker detection (blacklist functions, proxy contracts)"
echo "   • Conservative approach: Unknown risk = Filtered out"
echo ""

# Display what will be filtered out
echo "🚫 TOKENS AUTOMATICALLY FILTERED OUT"
echo "====================================="
echo "   • Honeypots (can buy but not sell)"
echo "   • Proxy contracts (implementation can change)"
echo "   • Blacklist/whitelist functions"
echo "   • Ownership not renounced"
echo "   • Pausable contracts"
echo "   • High-risk or critical security issues"
echo "   • Tokens with safety scores < 50"
echo ""

# Ask for confirmation
echo "🚀 READY TO START SCANNING"
echo "=========================="
echo "This will run continuous token discovery every 10 minutes with:"
echo "   ✅ RugCheck security filtering"
echo "   ✅ Enhanced timeframe analysis"
echo "   ✅ Structured logging"
echo "   ✅ Telegram alerts (if configured)"
echo ""

read -p "Start 10-minute scanning? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Scan cancelled by user"
    exit 0
fi

echo ""
echo "🚀 Starting 10-minute token scanner..."
echo "======================================"

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down scanner..."
    echo "📊 Scan session complete"
    echo "📋 Check logs/ directory for detailed results"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the monitor with 10-minute intervals
echo "⏰ Scanner will run every 10 minutes until stopped (Ctrl+C to stop)"
echo "🛡️ All tokens will be security-filtered through RugCheck API"
echo "📊 Results will be logged to logs/ directory"
echo ""

# Run the monitor in continuous mode
python monitor.py run --enhanced-timeframes true

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Scanner completed successfully"
else
    echo ""
    echo "❌ Scanner exited with error code $?"
    echo "📋 Check logs for error details"
fi

echo ""
echo "📊 SCAN SESSION SUMMARY"
echo "======================"
echo "   • Scan interval: 10 minutes"
echo "   • Security filtering: RugCheck enabled"
echo "   • Logs location: logs/ directory"
echo "   • Data location: data/ directory"
echo ""
echo "🔗 RugCheck API: https://api.rugcheck.xyz/swagger/index.html"
echo "📋 For detailed analysis, check the structured logs" 