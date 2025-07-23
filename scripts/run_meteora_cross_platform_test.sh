#!/bin/bash

# Meteora Cross-Platform Integration Test Runner
# Tests integration of Meteora API with existing cross-platform analysis

echo "🚀 Starting Meteora Cross-Platform Integration Test..."
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup_environment.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if required environment variables are set
if [ -z "$BIRDEYE_API_KEY" ]; then
    echo "⚠️  Warning: BIRDEYE_API_KEY not set. Some features may not work."
fi

# Create tests directory if it doesn't exist
mkdir -p scripts/tests

# Run the test
echo "🔧 Running Meteora cross-platform integration test..."
python scripts/tests/test_meteora_cross_platform_integration.py

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Test completed successfully!"
    echo "📁 Check scripts/tests/ for detailed results"
else
    echo ""
    echo "❌ Test failed. Check the output above for details."
    exit 1
fi

echo "=================================================="
echo "🎯 Meteora Cross-Platform Test Complete" 