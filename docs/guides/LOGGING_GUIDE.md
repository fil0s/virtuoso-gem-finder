# Virtuoso Gem Hunter - Logging Guide

## 🚀 Overview

The Virtuoso Gem Hunter uses a sophisticated logging system that separates operational logging from user interface output, providing both detailed file logs for analysis and clean console output for monitoring.

## 📁 Log File Structure

```
logs/
├── virtuoso_gem_hunter.log      # Main log file (10MB, rotated)
├── virtuoso_gem_hunter.log.1    # Backup log file
├── virtuoso_gem_hunter.log.2    # Older backup
└── ...                         # Up to 10 backup files
```

## 🎛️ Log Levels Configuration

### Environment Variables

Configure logging behavior via environment variables in your `.env` file:

```bash
# Console output verbosity (what you see on screen)
CONSOLE_LOG_LEVEL=INFO          # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# File log verbosity (what gets saved to file)
FILE_LOG_LEVEL=DEBUG            # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Early detection service specific logging
EARLY_DETECTION_LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Custom log file location (optional)
LOG_FILE=logs/virtuoso_gem_hunter.log
```

### Recommended Settings

**Production Environment:**
```bash
CONSOLE_LOG_LEVEL=INFO
FILE_LOG_LEVEL=INFO
EARLY_DETECTION_LOG_LEVEL=INFO
```

**Development/Debug Environment:**
```bash
CONSOLE_LOG_LEVEL=DEBUG
FILE_LOG_LEVEL=DEBUG
EARLY_DETECTION_LOG_LEVEL=DEBUG
```

**Quiet Operation:**
```bash
CONSOLE_LOG_LEVEL=WARNING
FILE_LOG_LEVEL=INFO
EARLY_DETECTION_LOG_LEVEL=INFO
```

## 📊 Log Format

### Console Output (Clean UI)
```
2025-05-23 10:15:31 [INFO] VirtuosoGemHunter - Starting token detection scan #1
2025-05-23 10:15:45 [INFO] EarlyTokenDetector - Discovered 47 tokens with 1 API call
2025-05-23 10:16:02 [WARNING] TelegramAlerter - Failed to send alert: Network timeout
```

### File Output (Detailed)
```
2025-05-23 10:15:31,511 [INFO] [VirtuosoGemHunter.start] [/] [] - Starting token detection scan #1
2025-05-23 10:15:45,203 [DEBUG] [EarlyTokenDetector._efficient_discovery] [DOGE/7xKX...89Py] [discovery] - Token passed initial filters
2025-05-23 10:16:02,847 [ERROR] [TelegramAlerter._send_message_to_telegram] [/] [alert] - Failed to send message: Connection timeout
```

## 🎯 Logging Best Practices

### Operational vs UI Output

**✅ DO:** Use logging for operational events
```python
self.logger.info(f"Scan #{scan_count} completed in {elapsed_time:.2f} seconds")
self.logger.error(f"API call failed: {error_message}")
self.logger.debug(f"Processing token {token_address}")
```

**✅ DO:** Use print() for user interface output
```python
print(f"🚀 Starting Virtuoso Gem Hunter...")
print(f"Found {len(tokens)} promising tokens")
print(f"Next scan in: {interval} minutes")
```

### Log Levels Usage

| Level | Usage | Example |
|-------|-------|---------|
| **DEBUG** | Detailed diagnostic info | `self.logger.debug(f"Cache hit for {token_address}")` |
| **INFO** | General operational info | `self.logger.info("Scan completed successfully")` |
| **WARNING** | Unexpected but recoverable | `self.logger.warning("API rate limit approaching")` |
| **ERROR** | Error conditions | `self.logger.error("Failed to fetch token data", exc_info=True)` |
| **CRITICAL** | Serious errors | `self.logger.critical("System shutdown required")` |

### Context Fields

The logging system supports context fields for better tracking:

```python
# These fields are automatically added when available
# [token_symbol/token_address] [event_type]
self.logger.info("Token analysis completed", extra={
    'token': 'DOGE',
    'address': '7xKX...89Py',
    'event': 'analysis_complete'
})
```

## 🔧 Logger Setup in Code

### Basic Setup
```python
from services.logger_setup import LoggerSetup

# Initialize logger
logger_setup = LoggerSetup('ComponentName')
logger = logger_setup.logger

# Use the logger
logger.info("Component initialized")
logger.error("Error occurred", exc_info=True)
```

### Advanced Setup
```python
from services.logger_setup import LoggerSetup

# Custom log file and level
logger_setup = LoggerSetup(
    name='CustomComponent',
    log_file='logs/custom.log',
    log_level='DEBUG'
)
logger = logger_setup.logger
```

## 📈 Log Analysis

### Viewing Logs

**Real-time monitoring:**
```bash
# Follow the main log file
tail -f logs/virtuoso_gem_hunter.log

# Filter for specific component
tail -f logs/virtuoso_gem_hunter.log | grep "EarlyTokenDetector"

# Filter by log level
tail -f logs/virtuoso_gem_hunter.log | grep "\[ERROR\]"
```

**Log file rotation:**
- Files are automatically rotated when they reach 10MB
- Up to 10 backup files are kept
- Oldest files are automatically deleted

### Key Log Events to Monitor

**Successful Operations:**
```bash
grep "Scan.*completed" logs/virtuoso_gem_hunter.log
grep "API Call Reduction" logs/virtuoso_gem_hunter.log
```

**Errors and Warnings:**
```bash
grep -E "\[(ERROR|WARNING)\]" logs/virtuoso_gem_hunter.log
grep "Failed" logs/virtuoso_gem_hunter.log
```

**Performance Metrics:**
```bash
grep "OPTIMIZATION PERFORMANCE SUMMARY" logs/virtuoso_gem_hunter.log -A 20
grep "Total API calls" logs/virtuoso_gem_hunter.log
```

## 🛠️ Troubleshooting

### Common Issues

**No log file created:**
```bash
# Check if logs directory exists
ls -la logs/

# Verify permissions
chmod 755 logs/

# Test logger setup
python3 -c "from services.logger_setup import LoggerSetup; LoggerSetup('Test').logger.info('Test')"
```

**Log level too verbose:**
```bash
# Reduce verbosity in .env
CONSOLE_LOG_LEVEL=WARNING
FILE_LOG_LEVEL=INFO
```

**Log files too large:**
```bash
# Check current log file sizes
du -h logs/

# Logs are automatically rotated at 10MB
# Adjust rotation settings in LoggerSetup if needed
```

## 🎛️ Integration with Monitoring

The logging system integrates seamlessly with external monitoring tools:

**Logstash/ELK Stack:**
- Structured JSON logging available
- Easy parsing of log fields

**Grafana/Prometheus:**
- Log metrics can be extracted
- Performance monitoring integration

**Alerts:**
- Error log patterns can trigger alerts
- Performance degradation detection

## 🔄 Log Lifecycle

1. **Creation:** Logs created in `logs/` directory
2. **Rotation:** Files rotated at 10MB
3. **Retention:** 10 backup files kept
4. **Cleanup:** Oldest files automatically removed

This ensures your system never runs out of disk space while maintaining comprehensive logging history.

---

**💡 Pro Tip:** Use `CONSOLE_LOG_LEVEL=WARNING` for production and `FILE_LOG_LEVEL=DEBUG` to keep console clean while maintaining detailed file logs for troubleshooting. 