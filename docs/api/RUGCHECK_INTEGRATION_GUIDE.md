# RugCheck Integration Guide

## Overview

The Early Token Monitor now integrates with the **RugCheck API** (https://api.rugcheck.xyz) to provide security analysis and filtering during the initial token discovery phase. This integration helps filter out potentially risky tokens such as honeypots, proxy contracts, and other security vulnerabilities before they enter the analysis pipeline.

## Features

### 🛡️ Security Analysis
- **Token Security Scoring**: Each token receives a safety score (0-100, higher is safer)
- **Risk Level Classification**: Tokens are classified into risk categories
- **Issue Detection**: Identifies critical security issues and warnings
- **Batch Processing**: Efficient analysis of multiple tokens with rate limiting

### 🚫 Automatic Filtering
- **Pre-Analysis Filtering**: Risky tokens are filtered out before expensive analysis
- **Customizable Risk Thresholds**: Configure what constitutes a "healthy" token
- **Deal-Breaker Detection**: Automatic rejection of tokens with critical issues

### 📊 Enhanced Token Data
- **Security Metadata**: Discovered tokens include security analysis results
- **Risk Indicators**: Clear visibility into token security status
- **Analysis Timestamps**: Track when security analysis was performed

## Risk Classification

### Risk Levels

| Risk Level | Description | Safety Score | Healthy for Trading |
|------------|-------------|--------------|-------------------|
| **SAFE** | High safety score, minimal issues | ≥80 | ✅ Yes |
| **LOW_RISK** | Good safety score, minor warnings | ≥60 | ✅ Yes |
| **MEDIUM_RISK** | Moderate risk, some concerns | ≥40 | ✅ Yes |
| **HIGH_RISK** | High risk, significant issues | <40 | ❌ No |
| **CRITICAL_RISK** | Critical issues detected | Any | ❌ No |
| **UNKNOWN** | Analysis failed or unavailable | N/A | ❌ No |

### Critical Issues (Auto-Reject)

The following issues automatically classify a token as unhealthy:

- **Honeypot** - Token can be bought but not sold
- **Proxy Contract** - Implementation can be changed by owner
- **Blacklist Function** - Can prevent specific addresses from trading
- **Ownership Not Renounced** - Owner retains control over contract
- **Pausable Contract** - Trading can be paused by owner

## Implementation Details

### API Integration

The RugCheck connector (`api/rugcheck_connector.py`) provides:

```python
class RugCheckConnector:
    async def analyze_token_security(token_address: str) -> RugCheckResult
    async def batch_analyze_tokens(token_addresses: List[str]) -> Dict[str, RugCheckResult]
    def filter_healthy_tokens(tokens: List[Dict], results: Dict) -> List[Dict]
```

### Strategy Integration

Token discovery strategies automatically include RugCheck filtering:

```python
# Base strategy with RugCheck enabled (default)
strategy = VolumeMomentumStrategy()

# Disable RugCheck filtering if needed
strategy = VolumeMomentumStrategy()
strategy.enable_rugcheck_filtering = False
```

### Result Structure

Tokens that pass security filtering include additional metadata:

```json
{
  "address": "token_address",
  "symbol": "TOKEN",
  "security_analysis": {
    "rugcheck_score": 85.5,
    "risk_level": "safe",
    "issues_count": 0,
    "warnings_count": 1,
    "analysis_timestamp": 1640995200
  }
}
```

## Configuration

### Risk Thresholds

Default risk assessment thresholds (can be customized):

```python
risk_thresholds = {
    "min_safe_score": 80.0,      # Scores ≥80 are safe
    "min_low_risk_score": 60.0,  # Scores ≥60 are low risk
    "min_medium_risk_score": 40.0, # Scores ≥40 are medium risk
}
```

### Rate Limiting

- **Request Interval**: 500ms between requests
- **Retry Logic**: Automatic retry on rate limiting (429 errors)
- **Batch Processing**: Sequential processing with delays

### Caching

- **Cache Duration**: 10 minutes per token analysis
- **Memory Cache**: Results cached in memory during operation
- **Cache Management**: Automatic cleanup and statistics

## Usage Examples

### Testing the Integration

Run the integration test to verify everything works:

```bash
./run_rugcheck_test.sh
```

### Manual Analysis

```python
from api.rugcheck_connector import RugCheckConnector

rugcheck = RugCheckConnector()

# Analyze single token
result = await rugcheck.analyze_token_security("token_address")
print(f"Risk Level: {result.risk_level.value}")
print(f"Healthy: {result.is_healthy}")

# Batch analysis
results = await rugcheck.batch_analyze_tokens(["addr1", "addr2"])
```

### Strategy Usage

```python
# Strategy with RugCheck enabled (default)
strategy = VolumeMomentumStrategy()
tokens = await strategy.execute(birdeye_api)

# All returned tokens have passed security checks
for token in tokens:
    security = token.get("security_analysis", {})
    print(f"Token: {token['symbol']}")
    print(f"Risk Level: {security.get('risk_level')}")
    print(f"Score: {security.get('rugcheck_score')}")
```

## Performance Impact

### API Call Efficiency

- **Batching**: Multiple tokens analyzed in sequence
- **Caching**: Avoids duplicate analysis within 10 minutes
- **Rate Limiting**: Respectful API usage (500ms intervals)

### Expected Filtering Rates

Based on testing with various token sets:

- **Volume-based strategies**: ~20-40% of tokens filtered out
- **New listings**: ~50-70% of tokens filtered out
- **Trending tokens**: ~10-30% of tokens filtered out

### Time Impact

- **Per Token**: ~600ms including rate limiting
- **Batch of 20**: ~12-15 seconds total
- **Caching**: Subsequent analyses are instant

## Monitoring and Logging

### Structured Logging

All RugCheck activities are logged with structured data:

```json
{
  "event": "rugcheck_analysis_complete",
  "token_address": "...",
  "risk_level": "safe",
  "score": 85.5,
  "is_healthy": true,
  "timestamp": 1640995200
}
```

### Log Events

- `rugcheck_api_call` - API request/response status
- `rugcheck_analysis_complete` - Token analysis finished
- `rugcheck_cache_hit` - Result served from cache
- `strategy_token_eval` - Strategy evaluation with security data

### Statistics

Track filtering effectiveness:

```python
# Get cache statistics
stats = rugcheck.get_cache_stats()

# Strategy comparison
tokens_with_rugcheck = await strategy_with_security.execute(api)
tokens_without_rugcheck = await strategy_without_security.execute(api)

filtered_count = len(tokens_without_rugcheck) - len(tokens_with_rugcheck)
print(f"Filtered out {filtered_count} risky tokens")
```

## Troubleshooting

### Common Issues

**API Rate Limiting**
- The connector handles rate limiting automatically
- Reduces request frequency if rate limited
- Logs warnings when rate limits are hit

**Analysis Failures**
- Tokens with failed analysis are marked as unhealthy (conservative approach)
- Network timeouts are handled gracefully
- Partial failures don't stop batch processing

**Missing Security Data**
- Tokens without security analysis are excluded by default
- Enable debug logging to see detailed failure reasons
- Cache misses are normal for new tokens

### Debug Commands

```bash
# Test RugCheck API connectivity
python -c "
import asyncio
from api.rugcheck_connector import RugCheckConnector
rugcheck = RugCheckConnector()
result = asyncio.run(rugcheck.analyze_token_security('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'))
print(result)
"

# Check strategy with debug logging
PYTHONPATH=. python scripts/test_rugcheck_integration.py
```

## Benefits

### Risk Reduction
- **Prevent Honeypot Losses**: Automatic detection of honeypot tokens
- **Avoid Rug Pulls**: Early warning system for risky contracts
- **Ownership Transparency**: Identify tokens with concerning ownership patterns

### Analysis Efficiency
- **Pre-Filtering**: Expensive analysis only on healthy tokens
- **Resource Conservation**: Reduce API calls on risky tokens
- **Focus on Quality**: Analysis pipeline focuses on legitimate opportunities

### Data Quality
- **Enhanced Metadata**: Security scores enrich token data
- **Risk Awareness**: Clear visibility into token security status
- **Audit Trail**: Complete record of security analysis decisions

## Integration Status

✅ **Implemented Features:**
- RugCheck API connector with full functionality
- Integration with all token discovery strategies
- Configurable risk thresholds and filtering
- Comprehensive test suite
- Structured logging and monitoring
- Batch processing with rate limiting
- Caching for performance optimization

🔄 **Future Enhancements:**
- Configuration via YAML files
- Custom risk scoring models
- Integration with additional security APIs
- Real-time security alerts
- Historical security trend analysis

## References

- **RugCheck API**: https://api.rugcheck.xyz/swagger/index.html
- **Integration Test**: `scripts/test_rugcheck_integration.py`
- **Connector Code**: `api/rugcheck_connector.py`
- **Strategy Integration**: `core/token_discovery_strategies.py` 