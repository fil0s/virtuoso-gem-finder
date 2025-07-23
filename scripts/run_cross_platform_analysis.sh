#!/bin/bash

echo "🚀 Running Cross-Platform Token Analysis..."
echo "================================================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the analysis
python scripts/cross_platform_token_analyzer.py

echo ""
echo "✅ Analysis complete!" 