#!/bin/bash

# Trending Tokens vs RugCheck Analysis Runner
# This script runs a real-world test using trending tokens from Birdeye

echo "🔥 TRENDING TOKENS vs RUGCHECK ANALYSIS"
echo "========================================"
echo ""
echo "This analysis will:"
echo "  • Fetch the top trending tokens from Birdeye API"
echo "  • Run comprehensive RugCheck security analysis"
echo "  • Show what tokens would be filtered out"
echo "  • Calculate potential API call savings"
echo "  • Demonstrate real-world filtering effectiveness"
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
echo "🔧 Starting trending tokens analysis..."
echo "⏱️  This may take 1-2 minutes depending on token count and API response times"
echo ""

# Run the analysis
python scripts/test_trending_tokens_rugcheck_analysis.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Analysis completed successfully!"
    echo ""
    echo "📊 KEY INSIGHTS:"
    echo "  • Review the security risk breakdown"
    echo "  • Check the API call savings percentage"
    echo "  • See which trending tokens were filtered as risky"
    echo "  • Note the quality-based routing recommendations"
    echo ""
    echo "🎯 IMPLEMENTATION BENEFITS:"
    echo "  • Avoid expensive analysis on risky tokens"
    echo "  • Focus resources on high-quality opportunities"
    echo "  • Reduce false positives in your trading strategies"
    echo "  • Optimize API costs significantly"
    echo ""
    echo "📁 Results saved in scripts/results/ directory"
else
    echo ""
    echo "❌ Analysis failed with exit code $?"
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
echo "  • RugCheck API: https://api.rugcheck.xyz/swagger/index.html"
echo "  • Enhanced features: api/rugcheck_connector.py"
echo "  • Integration guide: docs/RUGCHECK_INTEGRATION_GUIDE.md" 