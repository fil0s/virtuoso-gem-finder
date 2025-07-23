#!/bin/bash

echo "🐛 Starting Comprehensive Strategy Comparison V4 - DEBUG MODE"
echo "=============================================================="
echo ""

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Load environment variables from .env file if it exists
if [[ -f ".env" ]]; then
    echo "📄 Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: .env file not found"
fi

# Set debug environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
export VERBOSE_LOGGING=true

echo "🐛 Debug environment variables set:"
echo "   DEBUG_MODE=true"
echo "   LOG_LEVEL=DEBUG" 
echo "   VERBOSE_LOGGING=true"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected. Activating..."
    source venv/bin/activate
fi

# Check for required environment variables
if [[ -z "$BIRDEYE_API_KEY" ]]; then
    echo "❌ Error: BIRDEYE_API_KEY environment variable not set"
    echo "   Please check your .env file or set manually: export BIRDEYE_API_KEY='your_key_here'"
    exit 1
fi

echo "✅ Environment checks passed"
echo "🔍 Starting comprehensive strategy analysis in DEBUG MODE..."
echo "📝 Debug logs will be more verbose and detailed"
echo ""

# Run with Python debug flags and verbose output
python -u -W all scripts/comprehensive_strategy_comparison_v4.py

echo ""
echo "📊 Debug analysis complete! Check logs/ directory for detailed debug logs."
echo "🔧 API optimization insights included with debug details!" 