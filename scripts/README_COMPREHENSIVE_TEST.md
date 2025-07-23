# Comprehensive System Test Suite

This directory contains a unified test suite that validates the entire Virtuoso Gem Hunter system across four critical areas:

## 🎯 Test Categories

### 1. **End-to-End System Test** (`e2e`)
Tests the complete token discovery pipeline from start to finish:
- ✅ Token discovery strategy execution
- ✅ Strategy coordination and data sharing
- ✅ Data persistence and caching
- ✅ Complete workflow integration

### 2. **API Integration Test** (`api`)
Validates all external API connections:
- 🔌 Birdeye API endpoints (token data, security, prices)
- 🛡️ RugCheck API integration
- 📱 Telegram API (if configured)
- 🌐 Solana RPC connectivity

### 3. **Performance Benchmark Test** (`performance`)
Tests system efficiency and resource usage:
- ⚡ Rate limiting performance
- 💾 Memory usage patterns
- 🔄 Concurrent operations handling
- 📊 Resource optimization

### 4. **Production Readiness Test** (`production`)
Validates system readiness for live trading:
- ⚙️ Configuration validation
- 🛡️ Error handling capabilities
- 📏 Resource limit compliance
- 🔒 Security measures

## 🚀 Quick Start

### Run All Tests
```bash
# Simple run - all tests
./scripts/run_comprehensive_test.sh

# All tests with verbose output
./scripts/run_comprehensive_test.sh -v

# All tests with results saved to file
./scripts/run_comprehensive_test.sh -o test_results.json
```

### Run Specific Test Categories
```bash
# API integration tests only
./scripts/run_comprehensive_test.sh -t api

# End-to-end tests with verbose output
./scripts/run_comprehensive_test.sh -t e2e -v

# Performance tests with results saved
./scripts/run_comprehensive_test.sh -t performance -o perf_results.json

# Production readiness check
./scripts/run_comprehensive_test.sh -t production
```

### Python Direct Usage
```bash
# All tests
python3 scripts/comprehensive_system_test.py

# Specific test type with verbose output
python3 scripts/comprehensive_system_test.py --test-type api --verbose

# Save results to JSON
python3 scripts/comprehensive_system_test.py --test-type all --output results.json
```

## 📋 Test Results

### Status Codes
- **PASS** ✅ - Test completed successfully
- **FAIL** ❌ - Test failed (critical issue)
- **WARNING** ⚠️ - Test passed with concerns
- **SKIP** ⏭️ - Test was skipped (e.g., service not configured)

### Example Output
```
🎯 COMPREHENSIVE SYSTEM TEST RESULTS
================================================================================
Total Tests: 15
✅ Passed: 12
❌ Failed: 1
⚠️  Warnings: 2
⏭️  Skipped: 0
📊 Success Rate: 80.0%
⏱️  Duration: 45.3s
================================================================================
🎯 RECOMMENDATIONS:
  ❌ 1 critical tests failed - investigate immediately
  ⚠️ 2 tests have warnings - review for optimization
  🔌 API integration issues detected - check API keys and network connectivity
================================================================================
```

## 🔧 Configuration Requirements

### Required Configuration Sections
- `BIRDEYE_API` - Birdeye API configuration
- `RPC` - Solana RPC endpoint configuration  
- `DATABASE` - Database configuration

### Optional Configuration Sections
- `TELEGRAM` - Telegram notifications (set `enabled: true`)
- `RUGCHECK_API` - RugCheck integration
- `WHALE_TRACKING` - Whale tracking features

### Environment Variables
Ensure these environment variables are set:
```bash
BIRDEYE_API_KEY=your_birdeye_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token  # if using Telegram
TELEGRAM_CHAT_ID=your_telegram_chat_id      # if using Telegram
```

## 📊 Detailed Test Descriptions

### API Integration Tests

#### Birdeye API Integration
- Tests core endpoints: `token_overview`, `token_list`, `token_security`, `price_data`
- Validates response structure and success status
- Checks error handling for invalid requests

#### RugCheck API Integration
- Tests token security analysis functionality
- Validates response format and data quality

#### Telegram API Integration
- Tests bot connectivity (if enabled)
- Validates configuration completeness

#### RPC Integration
- Tests Solana RPC endpoint connectivity
- Validates configuration parameters

### End-to-End Tests

#### Token Discovery Pipeline
- Executes complete strategy scheduler workflow
- Tests multi-strategy coordination
- Validates token discovery and filtering

#### Strategy Coordination
- Tests strategy status reporting
- Validates active strategy management

#### Data Persistence
- Tests cache functionality (set/get/delete)
- Validates data integrity

### Performance Tests

#### Rate Limiting Performance
- Tests rate limiter behavior under load
- Measures calls per second compliance

#### Memory Usage
- Monitors memory allocation and cleanup
- Tests garbage collection effectiveness

#### Concurrent Operations
- Tests parallel cache operations
- Validates thread safety

### Production Readiness Tests

#### Configuration Validation
- Checks all required configuration sections
- Validates API key presence

#### Error Handling
- Tests graceful error handling
- Validates exception management

#### Resource Limits
- Monitors CPU and memory usage
- Validates resource consumption limits

#### Security Measures
- Checks sensitive data protection
- Validates security configurations

## 🐛 Troubleshooting

### Common Issues

#### API Key Issues
```
❌ API integration issues detected - check API keys and network connectivity
```
**Solution**: Verify your API keys are correctly set in environment variables

#### Configuration Missing
```
❌ Configuration validation failed - missing required sections
```
**Solution**: Check your `config/config.yaml` file has all required sections

#### Network Connectivity
```
❌ API tests failing with timeout errors
```
**Solution**: Check your internet connection and firewall settings

#### Memory Issues
```
⚠️ Performance issues detected - consider optimization
```
**Solution**: Monitor system resources and optimize memory usage

### Debug Mode
Run with verbose output to get detailed information:
```bash
./scripts/run_comprehensive_test.sh -v -t api
```

### Selective Testing
If some tests are failing, run them individually:
```bash
# Test just API integration
./scripts/run_comprehensive_test.sh -t api -v

# Test just performance
./scripts/run_comprehensive_test.sh -t performance -v
```

## 📈 Continuous Integration

### CI/CD Integration
Add to your CI pipeline:
```yaml
# GitHub Actions example
- name: Run Comprehensive Tests
  run: |
    ./scripts/run_comprehensive_test.sh -o ci_results.json
    
- name: Upload Test Results
  uses: actions/upload-artifact@v2
  with:
    name: test-results
    path: ci_results.json
```

### Pre-deployment Checks
Before deploying to production:
```bash
# Full production readiness check
./scripts/run_comprehensive_test.sh -t production -v

# Complete system validation
./scripts/run_comprehensive_test.sh -t all -o pre_deploy_results.json
```

## 🎯 Best Practices

1. **Run tests regularly** - Include in your development workflow
2. **Monitor performance** - Track performance test results over time
3. **Fix failures immediately** - Don't ignore failed tests
4. **Review warnings** - Address warnings before they become failures
5. **Save results** - Keep test results for trend analysis
6. **Test before deployment** - Always run production readiness tests

## 📝 Test Result Schema

The JSON output follows this schema:
```json
{
  "test_summary": {
    "total_tests": 15,
    "passed_tests": 12,
    "failed_tests": 1,
    "warning_tests": 2,
    "skipped_tests": 0,
    "success_rate": 0.8,
    "total_duration_seconds": 45.3
  },
  "results_by_type": {
    "api": { "total": 4, "passed": 3, "failed": 1, "warnings": 0, "skipped": 0 },
    "e2e": { "total": 3, "passed": 3, "failed": 0, "warnings": 0, "skipped": 0 },
    "performance": { "total": 3, "passed": 2, "failed": 0, "warnings": 1, "skipped": 0 },
    "production": { "total": 4, "passed": 4, "failed": 0, "warnings": 0, "skipped": 0 }
  },
  "detailed_results": [...],
  "system_metrics": {...},
  "recommendations": [...],
  "timestamp": "2024-01-15T10:30:00",
  "test_environment": {...}
}
```

This comprehensive test suite ensures your Virtuoso Gem Hunter system is robust, performant, and ready for production trading operations. 