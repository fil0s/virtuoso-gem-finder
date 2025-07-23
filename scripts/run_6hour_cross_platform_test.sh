#!/bin/bash

# 6-Hour Cross-Platform Token Analyzer Test Runner
# =================================================

set -e  # Exit on error

echo "🚀 Starting 6-Hour Cross-Platform Token Analyzer Test"
echo "====================================================="

# Check if we're in the right directory
if [ ! -f "scripts/cross_platform_token_analyzer.py" ]; then
    echo "❌ Error: cross_platform_token_analyzer.py not found in scripts/"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "📦 Checking dependencies..."
python -c "import aiohttp, asyncio, requests" 2>/dev/null || {
    echo "❌ Missing dependencies. Installing..."
    pip install aiohttp requests
}

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p scripts/results

# Check configuration
if [ ! -f "config/config.yaml" ]; then
    echo "❌ Error: config/config.yaml not found"
    echo "Please ensure your configuration file exists"
    exit 1
fi

# Display test parameters
echo ""
echo "⚙️  Test Configuration:"
echo "   Duration: 6 hours"
echo "   Analysis interval: 15 minutes"
echo "   Expected runs: ~24"
echo "   Platforms: DexScreener, RugCheck, Birdeye"
echo ""

# Confirm start
read -p "🤔 Ready to start 6-hour test? This will run continuously. (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Test cancelled"
    exit 0
fi

echo ""
echo "🎯 Starting test... (Press Ctrl+C to stop early)"
echo "📝 Logs will be saved to logs/ directory"
echo "📊 Results will be saved to scripts/results/ directory"
echo ""

# Change to scripts directory and run the test
cd scripts
python run_6hour_cross_platform_test.py

echo ""
echo "✅ Test completed or stopped"
echo "📁 Check logs/ and scripts/results/ for detailed output" 