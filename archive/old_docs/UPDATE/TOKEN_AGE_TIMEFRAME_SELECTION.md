# Token-Age Aware Timeframe Selection

## Overview

This document outlines the implementation of token-age aware timeframe selection in the Early Token Monitor system. This enhancement is designed to address the frequent issue of missing OHLCV data for newer tokens, enabling more effective trend analysis across tokens of all ages.

## Problem Statement

During testing with live data, we observed that many tokens, especially newer ones, lack sufficient OHLCV data for the standard timeframes (1h, 4h, 1d). This made trend analysis impossible for many promising early-stage tokens, defeating the primary purpose of the monitoring system.

## Solution: Age-Aware Timeframe Selection

The implemented solution dynamically selects appropriate timeframes based on the token's age:

### Age Categories and Timeframes

| Age Category | Token Age | Timeframes Used | Lookback Period |
|--------------|-----------|-----------------|-----------------|
| **new** | < 24h | 1m, 5m, 15m | 1-2 days |
| **recent** | 1-3 days | 15m, 1h, 4h | 2-5 days |
| **developing** | 3-7 days | 1h, 4h, 1d | 3-7 days |
| **established** | > 7 days | 1h, 4h, 1d | 7 days |

### Age Detection Process

1. For each token, the system attempts to determine its creation date by:
   - First checking the token security data for a `createdTime` field
   - If not found, checking token creation info endpoint
   - Defaulting to "established" category if creation time cannot be determined

2. Based on the token's age, appropriate timeframes are selected for trend analysis

3. The scoring weights for different timeframes are adjusted based on age category to ensure fair comparison

### Scoring Adjustments

For newer tokens, the scoring thresholds are slightly relaxed to account for the inherently noisier shorter-timeframe data:

| Age Category | Score Adjustment | Consensus Requirement |
|--------------|------------------|----------------------|
| **new** | 70% of standard | 80% of standard |
| **recent** | 80% of standard | 90% of standard |
| **developing** | 90% of standard | Standard |
| **established** | Standard | Standard |

Additionally, small confidence penalties are applied to newer token scores (10% for "new", 5% for "recent") to prevent overconfidence in volatile short-term patterns.

## Implementation Details

The implementation includes:

1. **Enhanced TrendConfirmationAnalyzer**:
   - Added token age detection method
   - Added age-based timeframe mapping
   - Modified OHLCV data fetching with age-appropriate lookback periods
   - Adjusted minimum required candles based on timeframe
   - Added age-specific scoring weights and thresholds

2. **Integration with BirdeyeAPI**:
   - The trend analyzer now accepts a Birdeye API instance to access token creation data
   - EarlyTokenDetector properly initializes the analyzer with the API instance

3. **Development Mode Support**:
   - Added test_mode parameter to apply more lenient criteria during development
   - Created run_monitor_dev_mode.sh script to run with DEV_MODE=true

4. **Testing Tools**:
   - Added scripts/test_token_age_detection.py to verify the age detection mechanism

## Usage

### Running in Development Mode

Development mode relaxes the trend confirmation criteria and enables better visibility into the age-based selection:

```bash
# Set API key if needed
export BIRDEYE_API_KEY=your_api_key

# Run with development mode
./run_monitor_dev_mode.sh
```

### Testing Token Age Detection

To verify the token age detection mechanism:

```bash
# Set API key if needed
export BIRDEYE_API_KEY=your_api_key

# Run the test script
./scripts/test_token_age_detection.py
```

The test results will be saved in the `data/token_age_tests/` directory.

## Benefits

This enhancement provides several key benefits:

1. **Increased Coverage**: The system can now effectively analyze newer tokens that would previously be excluded
2. **Age-Appropriate Analysis**: Each token is analyzed using timeframes appropriate for its maturity level
3. **Fairer Comparison**: Scoring adjustments ensure newer tokens aren't unfairly penalized
4. **More Robust Detection**: By adapting to token characteristics, the system provides more reliable signals

## Limitations

Some limitations to be aware of:

1. **API Dependency**: Creation time detection requires API calls, adding potential failure points
2. **Short-Term Volatility**: Analysis of very new tokens using short timeframes is inherently more susceptible to noise
3. **Default Fallback**: If age cannot be determined, the system defaults to treating tokens as established

## Conclusion

The token-age aware timeframe selection significantly improves the Early Token Monitor's ability to analyze tokens across all age ranges, addressing a key limitation identified during testing with live data. By dynamically adapting to each token's maturity level, the system can provide more accurate and comprehensive trend analysis for early token discovery. 