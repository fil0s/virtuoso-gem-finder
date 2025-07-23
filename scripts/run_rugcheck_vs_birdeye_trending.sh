#!/bin/bash

# RugCheck vs Birdeye Trending Comparison Runner
# This script compares trending tokens from both APIs to analyze quality and overlap

echo "🔥 RUGCHECK vs BIRDEYE TRENDING COMPARISON"
echo "==========================================="
echo ""
echo "This comparison will:"
echo "  • Fetch trending tokens from RugCheck /stats/trending (exactly 10 tokens)"
echo "  • Fetch trending tokens from Birdeye API (configurable limit)"
echo "  • Analyze overlap between the two sources"
echo "  • Compare token quality using RugCheck security analysis"
echo "  • Show which API provides better trending recommendations"
echo ""
echo "📊 Key Insights:"
echo "  • RugCheck: Fixed 10 tokens with inherent quality filtering"
echo "  • Birdeye: Larger selection based on volume/activity"
echo "  • Overlap: High-confidence tokens appearing in both sources"
echo "  • Quality: Safety rates and risk analysis for each source"
echo ""
echo "🔗 Reference: https://api.rugcheck.xyz/swagger/index.html#/"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $(basename $VIRTUAL_ENV)"
else
    echo "⚠️  Virtual environment not detected. Attempting to activate..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment not found. Please run 'python -m venv venv' first"
        exit 1
    fi
fi

echo ""
echo "🔧 Starting trending comparison analysis..."
echo "⏱️  This may take 1-2 minutes depending on API response times"
echo ""

# Run the comparison
python scripts/test_rugcheck_vs_birdeye_trending_comparison.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Comparison completed successfully!"
    echo ""
    echo "📊 KEY FINDINGS:"
    echo "  • Review the overlap rate between RugCheck and Birdeye trending"
    echo "  • Check the quality comparison (safety rates)"
    echo "  • Note which API provides better filtering"
    echo "  • See high-confidence tokens (appearing in both sources)"
    echo ""
    echo "🎯 IMPLEMENTATION STRATEGY:"
    echo "  • Use both APIs as complementary sources"
    echo "  • Prioritize tokens appearing in both (high confidence)"
    echo "  • Leverage RugCheck's quality filtering (10 curated tokens)"
    echo "  • Use Birdeye for broader market coverage"
    echo ""
    echo "💡 INTEGRATION BENEFITS:"
    echo "  • Fixed 10-token dataset from RugCheck = predictable processing"
    echo "  • Perfect for real-time polling and batch processing"
    echo "  • Quality over quantity approach reduces false positives"
    echo "  • Overlap validation provides highest confidence signals"
    echo ""
    echo "📁 Results saved in scripts/results/ directory"
else
    echo ""
    echo "❌ Comparison failed with exit code $?"
    echo "📋 Check the error output above for details"
    echo ""
    echo "🔧 Common issues:"
    echo "  • API rate limiting (wait and retry)"
    echo "  • Network connectivity issues"
    echo "  • Missing API credentials"
    echo "  • Configuration file issues"
fi

echo ""
echo "🔗 More info:"
echo "  • RugCheck API: https://api.rugcheck.xyz/swagger/index.html#/"
echo "  • Enhanced RugCheck features: api/rugcheck_connector.py"
echo "  • Integration guide: docs/RUGCHECK_INTEGRATION_GUIDE.md" 