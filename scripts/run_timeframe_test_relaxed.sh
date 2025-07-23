#!/bin/bash
# Run the virtuoso gem hunter with RELAXED FILTERS to test enhanced timeframe selection
# This script bypasses strict time-based filtering to ensure tokens reach analysis phase

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "${BLUE}${BOLD}     TIMEFRAME SELECTION TEST - RELAXED FILTERS MODE                 ${NC}"
echo -e "${BLUE}${BOLD}======================================================================${NC}"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables from .env file...${NC}"
    source .env
fi

# Check environment variables
if [ -z "$BIRDEYE_API_KEY" ]; then
    echo -e "${RED}Error: BIRDEYE_API_KEY environment variable is required${NC}"
    echo -e "${YELLOW}Please run: export BIRDEYE_API_KEY=your_api_key${NC}"
    echo -e "${YELLOW}Or create a .env file with BIRDEYE_API_KEY=your_api_key${NC}"
    exit 1
fi

# Create necessary directories
mkdir -p logs/monitoring_runs
mkdir -p data/discovery_results
mkdir -p temp/app_cache
mkdir -p debug/token_analysis

# Set development mode with RELAXED FILTERS for timeframe testing
export DEV_MODE=true
export DEBUG_LEVEL=INFO
export CACHE_ENABLED=true
export CACHE_TTL=300
export LOG_TO_FILE=true
export LOG_TOKEN_AGE=true
export ENHANCED_TIMEFRAMES=true
export MAX_PARALLEL_REQUESTS=5
export SAVE_DISCOVERED_TOKENS=true

# RELAXED FILTER OVERRIDES - Allow more tokens through to analysis
export FORCE_RELAXED_FILTERS=true
export MIN_LIQUIDITY_OVERRIDE=1000      # Very low liquidity requirement
export MIN_MARKET_CAP_OVERRIDE=1000     # Very low market cap requirement  
export MIN_MOMENTUM_SCORE_OVERRIDE=10   # Very low momentum requirement
export BYPASS_TIME_SCHEDULING=true      # Bypass time-based strict filtering
export FORCE_ANALYSIS_MODE=true         # Force tokens into analysis phase

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/monitoring_runs/timeframe_test_relaxed_$TIMESTAMP.log"

echo -e "${GREEN}${BOLD}Starting RELAXED FILTER timeframe test...${NC}"
echo -e "${YELLOW}⚠️ RELAXED FILTERS: Allowing more tokens through to analysis${NC}"
echo -e "${YELLOW}⚠️ Enhanced timeframe selection enabled${NC}"
echo -e "${YELLOW}⚠️ Bypassing strict time-based filtering${NC}"
echo -e "${GREEN}Logging to: $LOG_FILE${NC}"
echo

# Ask for runtime duration
read -p "Enter runtime duration in hours (e.g., 0.25 for 15 minutes): " RUNTIME_HOURS

# Default to 15 minutes if not specified
RUNTIME_HOURS=${RUNTIME_HOURS:-0.25}

echo -e "${GREEN}Starting relaxed filter test for ${RUNTIME_HOURS} hours...${NC}"

# Run the monitor with relaxed filters and enhanced timeframes
python monitor.py debug --runtime-hours $RUNTIME_HOURS --enhanced-timeframes true | tee "$LOG_FILE"

# Generate a summary report
echo -e "\n${BLUE}${BOLD}Generating timeframe selection analysis report...${NC}"
python scripts/analysis/timeframe_selection_report.py --log-file "$LOG_FILE" --output "debug/token_analysis/timeframe_report_relaxed_$TIMESTAMP.json"

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate
fi

echo -e "\n${GREEN}${BOLD}Relaxed filter timeframe test completed!${NC}"
echo -e "${GREEN}Log file: $LOG_FILE${NC}"
echo -e "${GREEN}Report: debug/token_analysis/timeframe_report_relaxed_$TIMESTAMP.json${NC}"

# Display quick summary if jq is available
if command -v jq &> /dev/null && [ -f "debug/token_analysis/timeframe_report_relaxed_$TIMESTAMP.json" ]; then
    echo -e "\n${BLUE}${BOLD}Quick Summary:${NC}"
    echo "--------------------------------"
    jq -r '.overall_stats | "Total tokens: \(.total_tokens), Success rate: \(.overall_success_rate)%"' "debug/token_analysis/timeframe_report_relaxed_$TIMESTAMP.json"
    
    echo -e "\n${BLUE}Top timeframes by success rate:${NC}"
    jq -r '.timeframe_stats | to_entries | sort_by(.value.success_rate) | reverse | .[:5][] | "\(.key): \(.value.success_rate)% (\(.value.success_count)/\(.value.total))"' "debug/token_analysis/timeframe_report_relaxed_$TIMESTAMP.json" 2>/dev/null || echo "No timeframe data available"
fi 