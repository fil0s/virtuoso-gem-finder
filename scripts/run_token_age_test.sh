#!/bin/bash

# Script to test token age detection and timeframe selection
# This script is part of the token-age aware timeframe selection enhancement

echo "Running token age detection and timeframe selection test..."
echo "---------------------------------------------------------"

# Export environment variables for development mode
export DEV_MODE=true
export DEBUG_LEVEL=INFO
export CACHE_ENABLED=true
export CACHE_TTL=300

# Run the test script
python scripts/tests/test_token_age_detection.py

# Check the exit status
if [ $? -eq 0 ]; then
    echo "Test completed successfully."
else
    echo "Test failed with exit code $?"
fi 