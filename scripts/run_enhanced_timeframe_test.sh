#!/bin/bash

# Script to test the enhanced timeframe selection functionality
# with various token age categories

# Text formatting
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}Running enhanced timeframe selection test...${RESET}"
echo "---------------------------------------------------------"

# Load environment variables if .env file exists
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables from .env file...${RESET}"
    source .env
else
    echo -e "${YELLOW}No .env file found. Make sure environment variables are set.${RESET}"
fi

# Check if API key is set
if [ -z "$BIRDEYE_API_KEY" ]; then
    echo -e "${YELLOW}Warning: BIRDEYE_API_KEY environment variable is not set.${RESET}"
    echo "The script might still work with rate limiting if your Birdeye API allows unauthenticated requests."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting."
        exit 1
    fi
fi

# Export environment variables for development mode
export DEV_MODE=true
export DEBUG_LEVEL=INFO
export CACHE_ENABLED=true
export CACHE_TTL=300
export MAX_PARALLEL_REQUESTS=5

# Ensure directories exist
mkdir -p debug/token_analysis
mkdir -p temp/app_cache
mkdir -p logs/monitoring_runs

# Make test script executable
chmod +x scripts/tests/test_enhanced_timeframes.py

echo -e "${BOLD}Starting test...${RESET}"
echo "This will test timeframe selection across all age categories."
echo "Results will be saved to debug/token_analysis/enhanced_timeframe_test_results.json"
echo

# Run the test script
python scripts/tests/test_enhanced_timeframes.py

# Check the exit status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Test completed successfully.${RESET}"
    echo "Results saved to debug/token_analysis/enhanced_timeframe_test_results.json"
    
    # Check if jq is installed for pretty formatting
    if command -v jq &> /dev/null; then
        echo -e "${BOLD}Summary of results:${RESET}"
        echo "--------------------------------"
        jq -r 'to_entries[] | "\(.key): Age \(.value.age_days | tostring | .[0:5]) days, Category: \(.value.age_category)"' debug/token_analysis/enhanced_timeframe_test_results.json
    fi
else
    echo -e "${RED}Test failed with exit code $?.${RESET}"
    echo "Check the logs for more information."
fi

echo -e "${BOLD}${BLUE}Done.${RESET}" 