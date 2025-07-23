#!/bin/bash

# FIXED Comprehensive API Comparison Test Runner
# Tests all available APIs with CORRECT method names

echo "🔧 Starting FIXED Comprehensive API Comparison Test"
echo "=================================================="
echo ""
echo "FIXES APPLIED:"
echo "• BirdEye: Using get_token_overview() and get_multi_price()"
echo "• Jupiter: Using get_batch_prices() and get_comprehensive_token_analysis()"
echo "• Raydium: Using get_token_pairs() instead of get_token_pools()"
echo "• Orca: Fixed session initialization and error handling"
echo "• All APIs: Added proper async session management"
echo ""
echo "Testing tokens: USELESS, TRUMP, aura, GOR, SPX, MUMU, \$michi, BILLY, INF"
echo ""

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -d "venv_new" ]; then
    echo "📦 Activating virtual environment..."
    source venv_new/bin/activate
else
    echo "⚠️ No virtual environment found, continuing without activation"
fi

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python3 -c "import tabulate" 2>/dev/null || {
    echo "Installing required packages..."
    pip install tabulate
}

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the FIXED test
echo "🚀 Running FIXED API comparison test..."
echo "This will test all APIs with the correct method names and proper error handling"
echo ""

python3 scripts/comprehensive_api_comparison_test_fixed.py

echo ""
echo "✅ FIXED API comparison test completed!"
echo "Check the results directory for detailed analysis and recommendations." 