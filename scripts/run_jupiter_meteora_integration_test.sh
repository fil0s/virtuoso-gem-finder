#!/bin/bash

# Jupiter + Meteora Cross-Platform Integration Test Runner
# Tests integration of both Jupiter and Meteora APIs in the trending detection system

echo "🚀 Starting Jupiter + Meteora Cross-Platform Integration Test..."
echo "=================================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup_environment.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check for API keys (optional but recommended)
if [ -z "$JUPITER_API_KEY" ]; then
    echo "⚠️  Info: JUPITER_API_KEY not set. Using free tier limits."
    echo "   You can get an API key from: https://portal.jup.ag/onboard"
fi

if [ -z "$BIRDEYE_API_KEY" ]; then
    echo "⚠️  Info: BIRDEYE_API_KEY not set. Some cross-platform features may be limited."
fi

# Create tests directory if it doesn't exist
mkdir -p scripts/tests

echo ""
echo "🔧 Running Jupiter + Meteora integration test..."
echo "   This will test:"
echo "   ✅ Jupiter Token List API (287K+ tokens)"
echo "   ✅ Jupiter Quote API (liquidity analysis)" 
echo "   ✅ Meteora Pool Search API (volume/TVL trending)"
echo "   🔄 Cross-platform token correlation"
echo ""

# Run the test
python scripts/tests/test_jupiter_meteora_cross_platform_integration.py

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Integration test completed successfully!"
    echo ""
    echo "📊 Check the generated results file:"
    echo "   scripts/tests/jupiter_meteora_integration_results_*.json"
    echo ""
    echo "🎯 Key Integration Points:"
    echo "   • Jupiter provides 287K+ tokens for discovery"
    echo "   • Jupiter Quote API enables real-time liquidity analysis"
    echo "   • Meteora provides pool-level volume/TVL trending data"
    echo "   • Combined system detects cross-platform trending signals"
    echo ""
    echo "📈 Next Steps:"
    echo "   1. Review the integration results JSON file"
    echo "   2. Check API performance metrics"
    echo "   3. Analyze cross-platform token correlations"
    echo "   4. Consider deploying to production if feasibility is HIGH"
else
    echo ""
    echo "❌ Integration test failed. Check the logs above for details."
    echo ""
    echo "🔍 Common Issues:"
    echo "   • Network connectivity problems"
    echo "   • API rate limiting (try reducing sample sizes)"
    echo "   • Missing dependencies (run: pip install -r requirements.txt)"
    echo ""
    exit 1
fi

echo ""
echo "🏁 Jupiter + Meteora integration test runner completed." 