#!/bin/bash

# Orca and Raydium Integration Test Runner
echo "🚀 Starting Orca & Raydium Integration Test..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Set PYTHONPATH to include current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the comprehensive integration test
echo "🧪 Running comprehensive integration test..."
python3 scripts/test_orca_raydium_integration.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Integration test completed successfully!"
else
    echo "❌ Integration test encountered errors"
    exit 1
fi

echo "📊 Test complete. Check the results in scripts/results/ directory." 