#!/bin/bash

echo "🚀 Starting Comprehensive Strategy Comparison V4 with API Optimization Analysis"
echo "=============================================================================="
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
echo "🔍 Starting comprehensive strategy analysis..."
echo ""

# Run the comprehensive strategy comparison
python scripts/comprehensive_strategy_comparison_v4.py

echo ""
echo "📊 Analysis complete! Check scripts/results/ for detailed reports."
echo "🔧 New API optimization insights included in the analysis!" 