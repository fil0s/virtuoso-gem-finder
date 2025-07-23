#!/bin/bash

# Comprehensive System Test Runner
# This script provides easy access to run the comprehensive system test suite

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
VERBOSE=false
OUTPUT_FILE=""
PYTHON_CMD="python3"

# Function to print colored output
print_colored() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    echo "Comprehensive System Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --test-type TYPE    Type of tests to run (all|api|e2e|performance|production)"
    echo "                          Default: all"
    echo "  -v, --verbose          Enable verbose logging"
    echo "  -o, --output FILE      Save results to JSON file"
    echo "  -p, --python CMD       Python command to use (default: python3)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Run all tests"
    echo "  $0 -t api                       # Run only API integration tests"
    echo "  $0 -t e2e -v                    # Run end-to-end tests with verbose output"
    echo "  $0 -t all -o results.json       # Run all tests and save results"
    echo "  $0 -t performance -v -o perf.json  # Performance tests with results"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--test-type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -p|--python)
            PYTHON_CMD="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate test type
case $TEST_TYPE in
    all|api|e2e|performance|production)
        ;;
    *)
        print_colored $RED "Error: Invalid test type '$TEST_TYPE'"
        echo "Valid types: all, api, e2e, performance, production"
        exit 1
        ;;
esac

# Check if Python is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    print_colored $RED "Error: $PYTHON_CMD is not available"
    echo "Please install Python 3 or specify a different Python command with -p"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "scripts/comprehensive_system_test.py" ]; then
    print_colored $RED "Error: comprehensive_system_test.py not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Build command
CMD="$PYTHON_CMD scripts/comprehensive_system_test.py --test-type $TEST_TYPE"

if [ "$VERBOSE" = true ]; then
    CMD="$CMD --verbose"
fi

if [ -n "$OUTPUT_FILE" ]; then
    CMD="$CMD --output $OUTPUT_FILE"
fi

# Print test information
print_colored $BLUE "🚀 Starting Comprehensive System Test"
print_colored $BLUE "=================================="
echo "Test Type: $TEST_TYPE"
echo "Verbose: $VERBOSE"
echo "Python: $PYTHON_CMD"
if [ -n "$OUTPUT_FILE" ]; then
    echo "Output File: $OUTPUT_FILE"
fi
echo ""

# Run the test
print_colored $YELLOW "Executing: $CMD"
echo ""

# Execute the command and capture exit code
set +e  # Don't exit on error so we can handle it
$CMD
EXIT_CODE=$?
set -e

# Print results based on exit code
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    print_colored $GREEN "✅ All tests completed successfully!"
    if [ -n "$OUTPUT_FILE" ]; then
        print_colored $GREEN "📄 Results saved to: $OUTPUT_FILE"
    fi
else
    print_colored $RED "❌ Some tests failed (exit code: $EXIT_CODE)"
    if [ -n "$OUTPUT_FILE" ]; then
        print_colored $YELLOW "📄 Results saved to: $OUTPUT_FILE"
    fi
    echo ""
    print_colored $YELLOW "💡 Tips for troubleshooting:"
    echo "  • Check API keys in your configuration"
    echo "  • Ensure network connectivity"
    echo "  • Run with --verbose for detailed logs"
    echo "  • Check individual test types: api, e2e, performance, production"
fi

exit $EXIT_CODE 