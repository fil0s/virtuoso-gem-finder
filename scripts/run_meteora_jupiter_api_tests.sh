#!/bin/bash

# Meteora + Jupiter API Testing Suite
# Tests both APIs to understand their potential for trending token detection

echo "🌟 Starting Meteora + Jupiter API Testing Suite"
echo "=================================================="

# Change to the project directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv_new" ]; then
    echo "📦 Activating virtual environment..."
    source venv_new/bin/activate
elif [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️ No virtual environment found. Using system Python."
fi

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python -c "import aiohttp, asyncio" 2>/dev/null || {
    echo "❌ Missing required packages. Installing..."
    pip install aiohttp asyncio
}

echo ""
echo "🚀 Running individual API tests..."
echo "=================================="

# Test Meteora API first
echo ""
echo "🔍 Testing Meteora API..."
python scripts/tests/test_meteora_api.py

# Test Jupiter API
echo ""
echo "🪐 Testing Jupiter API..."
python scripts/tests/test_jupiter_api.py

# Test combined analysis
echo ""
echo "🔄 Testing Combined Analysis..."
python scripts/tests/test_meteora_jupiter_combined.py

echo ""
echo "✅ All API tests completed!"
echo ""
echo "📊 Results saved to scripts/tests/ directory"
echo "Check the generated JSON files for detailed analysis"

# List the generated result files
echo ""
echo "📁 Generated test result files:"
ls -la scripts/tests/*_test_results_*.json 2>/dev/null | tail -5 || echo "No result files found yet"

echo ""
echo "🎯 Next steps:"
echo "1. Review the JSON result files for API data structure analysis"
echo "2. Check feasibility scores for trending detection implementation"
echo "3. Implement the trending detection system based on findings" 