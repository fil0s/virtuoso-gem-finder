#!/bin/bash

#  Token Monitor Startup Script

echo "========================================"
echo "    OPTIMIZED TOKEN MONITOR STARTUP"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if [ ! -f ".requirements_installed" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
    touch .requirements_installed
    echo "Requirements installed successfully"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "Please copy env.template to .env and configure your API keys:"
    echo "  cp env.template .env"
    echo "  # Then edit .env with your settings"
    exit 1
fi

# Check if config file exists
if [ ! -f "config/config.yaml" ]; then
    echo "📋 Config file not found, creating from template..."
    cp config/config.example.yaml config/config.yaml
    echo "✅ Created config/config.yaml - please review and customize settings"
fi

# Create necessary directories
mkdir -p logs data debug

# Check API key
if [ -z "$BIRDEYE_API_KEY" ]; then
    echo "⚠️  WARNING: BIRDEYE_API_KEY not set in environment"
    echo "Please set your Birdeye API key in .env file"
fi

echo "========================================"
echo "🚀 Starting  Token Monitor..."
echo "========================================"

# Check for command line arguments
if [ "$#" -gt 0 ]; then
    echo "🔧 Running with arguments: $@"
    python monitor.py "$@"
else
    echo "💡 TIP: You can now use these modes:"
    echo "   --mode discover-traders     (Run trader discovery only)"
    echo "   --mode analyze-trader --trader-address <ADDRESS>"
    echo "   --mode compare-timeframes   (Compare 24h vs 7d traders)"
    echo "   --discovery-now            (Run discovery then start monitoring)"
    echo ""
    
# Run the monitor with proper error handling
python monitor.py
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Monitor exited normally"
else
    echo "❌ Monitor exited with error code $?"
fi

echo "========================================"
echo "    MONITOR SHUTDOWN COMPLETE"
echo "========================================" 