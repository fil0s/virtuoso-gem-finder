#!/bin/bash

# Comprehensive API Comparison Test Runner
# Tests all available APIs against specific tokens from user's analysis

echo "🚀 Starting Comprehensive API Comparison Test"
echo "============================================="
echo ""
echo "This test will compare all available APIs:"
echo "• BirdEye API"
echo "• RugCheck API" 
echo "• Jupiter API"
echo "• Orca API"
echo "• Raydium API"
echo "• DexScreener API"
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
    echo "⚠️ No virtual environment found. Running with system Python."
fi

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python3 -c "import tabulate" 2>/dev/null || {
    echo "📦 Installing tabulate package..."
    pip install tabulate
}

# Create results directory if it doesn't exist
mkdir -p scripts/results

# Run the comprehensive API comparison test
echo ""
echo "🔬 Running API comparison test..."
echo "This may take a few minutes as we test all APIs against all tokens..."
echo ""

python3 scripts/comprehensive_api_comparison_test.py

# Check if test completed successfully
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ API comparison test completed successfully!"
    echo ""
    echo "📋 Results saved to scripts/results/"
    echo "📊 Check the generated files for detailed analysis and recommendations"
    echo ""
    echo "🔍 Latest results files:"
    ls -la scripts/results/ | grep "comprehensive_api_comparison" | tail -2
else
    echo ""
    echo "❌ API comparison test failed!"
    echo "Check the logs above for error details."
    exit 1
fi 