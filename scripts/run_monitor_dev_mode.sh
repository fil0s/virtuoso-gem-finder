#!/bin/bash
# Run the monitor in development mode

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}        VIRTUOSO GEM HUNTER - DEVELOPMENT MODE                        ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Check environment variables
if [ -z "$BIRDEYE_API_KEY" ]; then
    echo -e "${RED}Error: BIRDEYE_API_KEY environment variable is required${NC}"
    echo -e "${YELLOW}Please run: export BIRDEYE_API_KEY=your_api_key${NC}"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p logs
mkdir -p logs/monitoring_runs

# Set development mode
export DEV_MODE=true

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/monitoring_runs/monitor_dev_run_$TIMESTAMP.log"

echo -e "${GREEN}Starting monitor in DEVELOPMENT MODE...${NC}"
echo -e "${YELLOW}⚠️ DEV_MODE=true: Using relaxed trend confirmation criteria${NC}"
echo -e "${YELLOW}⚠️ Age-aware timeframe selection is enabled${NC}"
echo -e "${GREEN}Logging to: $LOG_FILE${NC}"
echo

# Run the monitor with development mode flags
python monitor.py run --runtime-hours 0.5 | tee "$LOG_FILE"

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate
fi 