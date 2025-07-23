# Enhanced Structured Logging Guide

## Overview

The Enhanced Structured Logging system provides comprehensive debugging and performance tracking for the Virtuoso Gem Hunter. Built on top of `structlog`, it offers stage-based context tracking, API call monitoring, and detailed performance metrics.

## Key Features

### 🔍 **Stage-Based Context Tracking**
- Track progression through all 5 detection stages
- Automatic timing and performance measurement
- Error tracking by stage
- Nested context support for complex operations

### 📡 **API Call Monitoring**
- Individual and batch API call tracking
- Response time measurement and analysis
- API call type classification
- Rate limiting and error monitoring

### 📊 **Performance Metrics**
- Real-time performance tracking
- Cache hit/miss statistics
- Token processing efficiency
- Comprehensive performance summaries

### 🆔 **Contextual Debugging** 
- Unique scan IDs for tracing full detection cycles
- Nested operation contexts
- Token processing flow visibility
- Full request/response correlation

## Quick Start

### Basic Usage

```python
from utils.enhanced_structured_logger import create_enhanced_logger, DetectionStage, APICallType

# Create logger
logger = create_enhanced_logger("MyComponent")

# Start a scan context
scan_id = logger.new_scan_context(
    strategy="early_gem_detection",
    timeframe="4_stages"
)

# Use stage contexts
with logger.stage_context(DetectionStage.STAGE_0_DISCOVERY, tokens_expected=1000):
    # Your stage logic here
    logger.info("Stage processing", tokens_discovered=856)

# Track API calls
with logger.api_call_context(APICallType.BATCH_METADATA, "birdeye/multi_metadata", token_count=50):
    # Your API call here
    result = await api_call()

# Log performance summary
logger.log_performance_summary()
```

## Detailed Usage

### 1. Logger Initialization

```python
logger = create_enhanced_logger(
    name="EarlyGemDetector",
    log_level="INFO",  # DEBUG, INFO, WARNING, ERROR
    enable_performance_tracking=True,
    enable_api_tracking=True, 
    enable_context_tracking=True
)
```

### 2. Scan Context Management

```python
# Start new scan
scan_id = logger.new_scan_context(
    strategy="comprehensive_scan",
    timeframe="hourly"
)

# The scan_id will be automatically included in all subsequent logs
logger.info("Starting detection cycle", target_tokens=500)
```

### 3. Stage Context Tracking

```python
# Track each detection stage
stages = [
    DetectionStage.STAGE_0_DISCOVERY,
    DetectionStage.STAGE_1_BASIC_FILTER,
    DetectionStage.STAGE_2_BATCH_ENRICHMENT,
    DetectionStage.STAGE_3_DETAILED_ANALYSIS,
    DetectionStage.STAGE_4_FINAL_SCORING
]

for stage in stages:
    with logger.stage_context(stage, expected_duration_ms=5000):
        # Stage processing logic
        await process_stage()
        
        # Log stage-specific information
        logger.info(f"Completed {stage.value}", 
                   tokens_processed=len(results),
                   success_rate=calculate_success_rate())
```

### 4. API Call Tracking

```python
# Track different types of API calls
api_calls = [
    (APICallType.TOKEN_DISCOVERY, "birdeye/defi/tokenlist"),
    (APICallType.BATCH_METADATA, "birdeye/defi/multi_metadata"),
    (APICallType.BATCH_PRICE, "birdeye/defi/multi_price"),
    (APICallType.INDIVIDUAL_METADATA, "birdeye/defi/metadata"),
    (APICallType.VALIDATION, "internal/validator")
]

for call_type, endpoint in api_calls:
    with logger.api_call_context(call_type, endpoint, token_count=batch_size):
        try:
            result = await make_api_call(endpoint)
            logger.debug("API success", response_size=len(result))
        except Exception as e:
            logger.error("API failed", error=str(e))
```

### 5. Token Processing Logging

```python
# Log token processing statistics
logger.log_token_processing(
    stage=DetectionStage.STAGE_1_BASIC_FILTER,
    tokens_input=1000,
    tokens_output=650,
    tokens_filtered=350,
    filter_reasons={
        "invalid_format": 100,
        "excluded_tokens": 50,
        "duplicates": 75,
        "low_volume": 125
    },
    processing_time_ms=1200
)
```

### 6. Validation Logging

```python
# Log validation results
validation_report = {
    "total_input": 500,
    "valid_count": 450,
    "filtered_count": 50,
    "validation_time_ms": 25.5,
    "api_calls_saved": 50
}

logger.log_validation_stats(
    validation_report,
    validator_version="enhanced_v1.0"
)
```

### 7. Cache Operation Logging

```python
# Track cache operations
logger.log_cache_operation(
    operation="get",
    cache_key="token_metadata_So111...",
    hit=True,
    ttl=300,
    cache_size_mb=15.2
)
```

### 8. Alert Logging

```python
# Log gem detection alerts
logger.log_alert(
    alert_type="high_confidence_gem",
    token_address="7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",
    confidence_score=0.89,
    alert_data={
        "price_change_24h": 156.8,
        "volume_change_24h": 245.2,
        "market_cap": 1250000,
        "risk_score": 0.15
    },
    telegram_sent=True
)
```

### 9. Performance Summary

```python
# Generate comprehensive performance summary
logger.log_performance_summary(
    total_gems_found=12,
    detection_complete=True,
    scan_duration_override=None  # Auto-calculated
)
```

## Log Output Format

All logs are output in structured JSON format for easy parsing and analysis:

```json
{
  "timestamp": "2025-01-22T10:30:45.123456Z",
  "level": "info",
  "event": "stage_start",
  "logger": "EarlyGemDetector",
  "scan_id": "scan_abc12345",
  "strategy": "early_gem_detection", 
  "timeframe": "4_stages",
  "stage": "stage_1_basic_filter",
  "stage_id": "stage_1_basic_filter_xyz789",
  "stage_start": "2025-01-22T10:30:45.123456Z",
  "tokens_input": 1000,
  "expected_duration_ms": 5000
}
```

## Integration with Existing Code

### Early Gem Detector Integration

The system integrates seamlessly with the existing early gem detector:

```python
# In early_gem_detector.py
from utils.enhanced_structured_logger import create_enhanced_logger, DetectionStage

class EarlyGemDetector:
    def __init__(self, config):
        # Initialize enhanced logger
        self.enhanced_logger = create_enhanced_logger("EarlyGemDetector")
        
        # Start scan context
        scan_id = self.enhanced_logger.new_scan_context(
            strategy=config.get('strategy_name', 'early_gem_detection'),
            timeframe=config.get('timeframe', '4_stages')
        )
        
    async def detect_early_gems(self):
        # Stage 0: Discovery
        with self.enhanced_logger.stage_context(DetectionStage.STAGE_0_DISCOVERY):
            token_addresses = await self.discover_tokens()
            
        # Stage 1: Basic Filter
        with self.enhanced_logger.stage_context(DetectionStage.STAGE_1_BASIC_FILTER):
            filtered_tokens = await self.basic_filter(token_addresses)
            
        # Continue for other stages...
        
        # Final summary
        self.enhanced_logger.log_performance_summary(
            total_gems_found=len(final_gems)
        )
        
        return final_gems
```

## Performance Monitoring

### Key Metrics Tracked

- **Stage Performance**: Duration and success rate for each detection stage
- **API Efficiency**: Call counts, response times, and error rates  
- **Cache Performance**: Hit/miss ratios and cache effectiveness
- **Token Processing**: Processing rates and filter effectiveness
- **Validation Stats**: Validation success rates and API calls saved

### Performance Thresholds

Configure alerting thresholds in `config/enhanced_logging.yaml`:

```yaml
thresholds:
  max_stage_duration_seconds: 30
  max_api_call_duration_seconds: 5  
  min_cache_hit_rate_percent: 80
  max_errors_per_scan: 5
```

## Log Analysis

### Parsing Logs

Since logs are in JSON format, they can be easily parsed and analyzed:

```python
import json

# Read and parse log file
with open('logs/gem_detection.log') as f:
    for line in f:
        log_entry = json.loads(line)
        
        # Extract specific information
        if log_entry.get('event') == 'performance_summary':
            print(f"Scan {log_entry['scan_id']} took {log_entry['total_scan_duration_ms']}ms")
            print(f"API calls: {log_entry['total_api_calls']}")
            print(f"Cache hit rate: {log_entry['cache_hit_rate']}%")
```

### Common Log Queries

**Find slow API calls:**
```bash
grep '"event":"api_complete"' logs/gem_detection.log | jq 'select(.duration_ms > 1000)'
```

**Get performance summaries:**
```bash
grep '"event":"performance_summary"' logs/gem_detection.log | jq '.{scan_id, total_scan_duration_ms, total_api_calls, cache_hit_rate}'
```

**Track token processing efficiency:**
```bash
grep '"event":"token_processing"' logs/gem_detection.log | jq '.{stage, tokens_input, tokens_output, processing_efficiency}'
```

## Troubleshooting

### Common Issues

1. **Missing structlog dependency**
   ```bash
   pip install structlog
   ```

2. **Log level too high**
   - Set log level to "DEBUG" for maximum detail
   - Use "INFO" for production

3. **Performance impact**
   - Disable tracking features if needed:
     ```python
     logger = create_enhanced_logger(
         enable_performance_tracking=False,
         enable_api_tracking=False
     )
     ```

### Debug Mode

Enable debug logging for maximum visibility:

```python
logger = create_enhanced_logger(
    log_level="DEBUG",
    enable_performance_tracking=True,
    enable_api_tracking=True,
    enable_context_tracking=True
)
```

## Best Practices

1. **Use scan contexts**: Always start with a scan context for full traceability
2. **Stage contexts**: Wrap each logical stage in a stage context
3. **API call contexts**: Track all external API calls
4. **Error handling**: Log errors with full context
5. **Performance summaries**: Generate summaries at the end of operations
6. **Consistent naming**: Use consistent field names across logs
7. **Structured data**: Include relevant structured data in log entries

## Testing

Run the comprehensive test suite:

```bash
python scripts/test_enhanced_structured_logging.py
```

This will demonstrate all logging features and output structured JSON logs showing the system in action.

## Integration Script

Apply the enhanced logging to your existing system:

```bash
python scripts/integrate_enhanced_logging.py
```

This script will:
- Create backups of existing files
- Patch the early gem detector with enhanced logging
- Update batch API managers
- Create configuration files
- Provide integration summary

## Configuration

Customize logging behavior via `config/enhanced_logging.yaml`:

```yaml
logging_config:
  log_level: "INFO"
  performance_tracking: true
  api_tracking: true
  context_tracking: true
  output_format: "json"
  
  thresholds:
    max_stage_duration_seconds: 30
    max_api_call_duration_seconds: 5
    min_cache_hit_rate_percent: 80
```

## Support

For issues or questions:
1. Check the test script output for examples
2. Review log output format and fields
3. Verify configuration settings
4. Check for missing dependencies

The enhanced structured logging system provides comprehensive visibility into your gem detection process, enabling better debugging, performance optimization, and monitoring.