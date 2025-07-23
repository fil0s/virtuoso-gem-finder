#!/bin/bash
# Run the early token monitor in development mode with live data
# This script is focused on testing the enhanced timeframe selection with real-time token discovery

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "${BLUE}${BOLD}     EARLY TOKEN MONITOR - LIVE DATA WITH ENHANCED TIMEFRAMES        ${NC}"
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

# Set development mode with specific settings for better debug info
export DEV_MODE=true
export DEBUG_LEVEL=INFO
export CACHE_ENABLED=true
export CACHE_TTL=300
export LOG_TO_FILE=true
export LOG_TOKEN_AGE=true
export ENHANCED_TIMEFRAMES=true
export MAX_PARALLEL_REQUESTS=5
export SAVE_DISCOVERED_TOKENS=true

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/monitoring_runs/live_timeframe_test_$TIMESTAMP.log"

echo -e "${GREEN}${BOLD}Starting monitor with LIVE DATA and ENHANCED TIMEFRAMES...${NC}"
echo -e "${YELLOW}⚠️ DEV_MODE=true: Using relaxed trend confirmation criteria${NC}"
echo -e "${YELLOW}⚠️ Age-aware timeframe selection is enabled with full granularity${NC}"
echo -e "${YELLOW}⚠️ Enhanced logging of token age and timeframe selection${NC}"
echo -e "${GREEN}Logging to: $LOG_FILE${NC}"
echo

# Ask for runtime duration
read -p "Enter runtime duration in hours (e.g., 0.5 for 30 minutes): " RUNTIME_HOURS

# Default to 1 hour if not specified
RUNTIME_HOURS=${RUNTIME_HOURS:-1}

echo -e "${GREEN}Starting monitor for ${RUNTIME_HOURS} hours...${NC}"

# Run the monitor with development mode flags
python monitor.py run --runtime-hours $RUNTIME_HOURS --discovery-source all --enhanced-timeframes true | tee "$LOG_FILE"

# Generate a summary report
echo -e "\n${BLUE}${BOLD}Generating test summary report...${NC}"
python scripts/analysis/timeframe_selection_report.py --log-file "$LOG_FILE" --output "debug/token_analysis/timeframe_report_$TIMESTAMP.json"

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate
fi

echo -e "\n${GREEN}${BOLD}Test completed! Check the logs and report for details.${NC}"
echo -e "${GREEN}Log file: $LOG_FILE${NC}"
echo -e "${GREEN}Report: debug/token_analysis/timeframe_report_$TIMESTAMP.json${NC}"

echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "${BLUE}${BOLD}     VIRTUOSO GEM HUNTER - LIVE DATA WITH ENHANCED TIMEFRAMES        ${NC}"
echo -e "${BLUE}${BOLD}======================================================================${NC}" 