#!/bin/bash
# Run comprehensive E2E test for Phase 1 and Phase 2 with live data

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}        VIRTUOSO GEM HUNTER - PHASE 1 & 2 FULL IMPLEMENTATION TEST     ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Check environment variables
if [ -z "$BIRDEYE_API_KEY" ]; then
    echo -e "${RED}Error: BIRDEYE_API_KEY environment variable is required${NC}"
    echo -e "${YELLOW}Please run: export BIRDEYE_API_KEY=your_api_key${NC}"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p logs

# Set default token limit
TOKEN_LIMIT=5
SAVE_RESULTS=true

# Parse command line arguments
while getopts "l:n" opt; do
  case $opt in
    l) TOKEN_LIMIT=$OPTARG ;;
    n) SAVE_RESULTS=false ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
  esac
done

echo -e "${BLUE}Test Configuration:${NC}"
echo -e "  Token Limit: ${TOKEN_LIMIT}"
echo -e "  Save Results: ${SAVE_RESULTS}"
echo -e "  API Key: ${BIRDEYE_API_KEY:0:4}...${BIRDEYE_API_KEY: -4}"
echo -e "${BLUE}----------------------------------------------------------------------${NC}"

# Check if Python and required packages are installed
echo -e "${BLUE}Checking environment...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not in PATH${NC}"
    exit 1
fi

# Check if virtualenv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not detected${NC}"
    
    # Check if venv directory exists
    if [ -d "venv" ]; then
        echo -e "${BLUE}Found venv directory, activating...${NC}"
        source venv/bin/activate
    else
        echo -e "${YELLOW}Running with system Python. Consider using a virtual environment.${NC}"
    fi
else
    echo -e "${GREEN}Using virtual environment: $VIRTUAL_ENV${NC}"
fi

# Run preflight check for required packages
echo -e "${BLUE}Checking required packages...${NC}"
python3 -c "import asyncio, logging, json, time, datetime, random, pathlib" || {
    echo -e "${RED}Error: Basic Python packages are missing${NC}"
    exit 1
}

# Run the test with specified token limit
SAVE_FLAG=""
if [ "$SAVE_RESULTS" = false ]; then
    SAVE_FLAG="--no-save"
fi

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}                      STARTING TEST EXECUTION                         ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Run the test with stdout and stderr to terminal and log file
LOG_FILE="logs/full_test_$(date +%Y%m%d_%H%M%S).log"
python3 -m scripts.e2e_full_test -l $TOKEN_LIMIT $SAVE_FLAG 2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo -e "${BLUE}======================================================================${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}TEST COMPLETED SUCCESSFULLY${NC}"
else
    echo -e "${RED}TEST COMPLETED WITH ERRORS (Exit code: $EXIT_CODE)${NC}"
    echo -e "${YELLOW}Check the log file for details: $LOG_FILE${NC}"
fi
echo -e "${BLUE}======================================================================${NC}"

exit $EXIT_CODE 