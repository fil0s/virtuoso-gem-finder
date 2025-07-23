#!/bin/bash

# Smart Money Whale Strategy Debug Analysis Runner
# This script runs comprehensive debugging of the SmartMoneyWhaleStrategy

echo "🔍 SMART MONEY WHALE STRATEGY DEBUG ANALYSIS"
echo "=============================================="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  WARNING: Not in a virtual environment"
    echo "   Run: source venv/bin/activate"
    read -p "Continue anyway? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "❌ Exiting"
        exit 1
    fi
fi

# Check API key
if [[ -z "$BIRDEYE_API_KEY" ]]; then
    echo "❌ BIRDEYE_API_KEY environment variable not set"
    echo "   Please set it with: export BIRDEYE_API_KEY=your_key_here"
    exit 1
fi

# Create results directory if it doesn't exist
mkdir -p scripts/results

echo "🚀 Starting comprehensive debug analysis..."
echo "   This will track every step, API call, and decision"
echo "   Expected duration: 2-5 minutes"
echo "   Debug report will be saved to scripts/results/"
echo ""

# Run the debug script
venv/bin/python scripts/debug_smart_money_whale_strategy.py

exit_code=$?

echo ""
if [[ $exit_code -eq 0 ]]; then
    echo "✅ Debug analysis completed successfully!"
    echo "   📊 Check the detailed report in scripts/results/"
    echo "   🔍 Review logs for comprehensive step-by-step analysis"
else
    echo "❌ Debug analysis failed with exit code: $exit_code"
    echo "   Check the logs above for error details"
fi

echo ""
echo "🎯 NEXT STEPS:"
echo "   1. Review the JSON debug report for detailed metrics"
echo "   2. Check filtering ratios and API efficiency"
echo "   3. Analyze discovered tokens and their scores"
echo "   4. Optimize strategy parameters if needed"

exit $exit_code 