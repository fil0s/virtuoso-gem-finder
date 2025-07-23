#!/bin/bash

# WSOL-Only Filtering Test Runner
# Runs both unit tests and live test for WSOL filtering functionality

echo "🪙 WSOL-Only Filtering Test Suite"
echo "================================="
echo

# Check if we're in the right directory
if [ ! -f "scripts/cross_platform_token_analyzer.py" ]; then
    echo "❌ Error: Must run from virtuoso_gem_hunter root directory"
    echo "💡 Current directory: $(pwd)"
    echo "💡 Expected file: scripts/cross_platform_token_analyzer.py"
    exit 1
fi

# Set up environment
echo "🔧 Setting up environment..."
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Function to run test with error handling
run_test() {
    local test_name="$1"
    local test_file="$2"
    
    echo
    echo "🚀 Running $test_name..."
    echo "----------------------------------------"
    
    if python3 "$test_file"; then
        echo "✅ $test_name completed successfully"
        return 0
    else
        echo "❌ $test_name failed"
        return 1
    fi
}

# Run unit tests
echo "📋 Step 1: Running Unit Tests..."
if run_test "WSOL Filtering Unit Tests" "test_wsol_only_filtering.py"; then
    UNIT_TESTS_PASSED=true
else
    UNIT_TESTS_PASSED=false
fi

# Run live test
echo
echo "📊 Step 2: Running Live Test..."
if run_test "WSOL Filtering Live Test" "run_wsol_filtering_test.py"; then
    LIVE_TEST_PASSED=true
else
    LIVE_TEST_PASSED=false
fi

# Summary
echo
echo "📈 WSOL FILTERING TEST SUMMARY"
echo "=============================="

if [ "$UNIT_TESTS_PASSED" = true ]; then
    echo "✅ Unit Tests: PASSED"
else
    echo "❌ Unit Tests: FAILED"
fi

if [ "$LIVE_TEST_PASSED" = true ]; then
    echo "✅ Live Test: PASSED"
else
    echo "❌ Live Test: FAILED"
fi

# Overall result
if [ "$UNIT_TESTS_PASSED" = true ] && [ "$LIVE_TEST_PASSED" = true ]; then
    echo
    echo "🎉 All WSOL filtering tests passed!"
    echo "🪙 WSOL-only filtering is working correctly"
    exit 0
else
    echo
    echo "⚠️ Some tests failed - please review the output above"
    exit 1
fi 