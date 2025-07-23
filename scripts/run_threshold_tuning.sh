#!/bin/bash

# Smart Money Whale Strategy Threshold Tuning Runner
# This script runs comprehensive threshold tuning to find optimal whale criteria

echo "🎯 SMART MONEY WHALE THRESHOLD TUNING SYSTEM"
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

echo ""
echo "🔧 CONFIGURATION OPTIONS:"
echo "========================="
echo "1. Comprehensive Analysis (Test all 5 levels)"
echo "2. Stop on First Success (Stop when tokens found)"
echo ""
read -p "Select option (1 or 2): " option

case $option in
    1)
        echo "📊 Running comprehensive analysis of all threshold levels..."
        STOP_ON_SUCCESS="false"
        ;;
    2)
        echo "🎯 Running until first successful level found..."
        STOP_ON_SUCCESS="true"
        ;;
    *)
        echo "❌ Invalid option. Defaulting to comprehensive analysis."
        STOP_ON_SUCCESS="false"
        ;;
esac

echo ""
echo "🚀 STARTING THRESHOLD TUNING..."
echo "================================"
echo "📊 Testing 5 threshold levels:"
echo "   Level 1: Maximum Selectivity (Ultra-strict)"
echo "   Level 2: High Selectivity (20% relaxed)"
echo "   Level 3: Medium Selectivity (40% relaxed)"
echo "   Level 4: Low Selectivity (60% relaxed)"
echo "   Level 5: Minimum Viable (80% relaxed)"
echo ""
echo "⏱️  This may take several minutes..."
echo "🌐 Will make API calls to analyze whale activity"
echo "💾 Results will be saved to scripts/results/"
echo ""

# Run the threshold tuning script
if [[ "$STOP_ON_SUCCESS" == "true" ]]; then
    echo "🛑 Stop on first success: ENABLED"
else
    echo "📊 Comprehensive analysis: ENABLED"
fi

echo ""
echo "▶️  Executing threshold tuning..."
echo ""

# Use the virtual environment's Python explicitly
venv/bin/python scripts/tune_smart_money_whale_thresholds.py

exit_code=$?

echo ""
echo "======================================="
if [ $exit_code -eq 0 ]; then
    echo "✅ THRESHOLD TUNING COMPLETED SUCCESSFULLY!"
    echo ""
    echo "📁 Check scripts/results/ for:"
    echo "   • threshold_tuning_results_*.json (comprehensive analysis)"
    echo "   • optimal_whale_config_*.json (optimal configuration)"
    echo ""
    echo "💡 NEXT STEPS:"
    echo "   1. Review the results files"
    echo "   2. Apply optimal configuration to production"
    echo "   3. Test with the recommended thresholds"
else
    echo "❌ THRESHOLD TUNING FAILED (exit code: $exit_code)"
    echo ""
    echo "🔍 TROUBLESHOOTING:"
    echo "   • Check API key is valid"
    echo "   • Verify internet connection"
    echo "   • Check logs for specific errors"
    echo "   • Ensure all dependencies are installed"
fi

echo "=======================================" 