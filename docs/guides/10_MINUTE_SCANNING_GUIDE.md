# 10-Minute Token Scanning Guide

## Overview

This guide covers the implementation of automated 10-minute interval token scanning with integrated RugCheck security filtering. The system provides multiple ways to run continuous token discovery and analysis, from simple interactive scripts to advanced daemon processes and systemd services.

## 🛡️ Key Features

### Security-First Approach
- **RugCheck Integration**: Every discovered token is analyzed for security risks
- **Automatic Filtering**: Risky tokens (honeypots, rug pulls, etc.) are filtered out
- **Risk Classification**: Tokens are classified into safety levels (SAFE/LOW/MEDIUM/HIGH/CRITICAL)
- **Conservative Defaults**: Unknown risk = Filtered out

### Flexible Scanning Options
- **Interactive Scanning**: User-friendly script with confirmation prompts
- **Daemon Mode**: Background process with full process management
- **Systemd Service**: System-level service with automatic restart
- **Advanced Scheduler**: Multiple scan profiles with different strategies

### Intelligent Resource Management
- **Rate Limiting**: Respectful API usage with built-in delays
- **Caching**: 10-minute result caching to avoid duplicate analysis
- **Batch Processing**: Efficient token analysis in batches
- **Error Recovery**: Graceful handling of API failures

## 📊 Scanning Methods

### Method 1: Interactive 10-Minute Scanner

**Best for**: Manual testing, development, short-term monitoring

```bash
./run_10min_scan.sh
```

**Features**:
- User confirmation before starting
- Real-time progress display
- Detailed security filtering information
- Easy to stop with Ctrl+C

**Output Example**:
```
🛡️ 10-MINUTE TOKEN SCANNER WITH RUGCHECK SECURITY
==================================================
✅ Environment checks passed

📊 SCAN CONFIGURATION
====================
   • Scan Interval: 10 minutes
   • Security Filtering: RugCheck API enabled
   • Token Discovery: All strategies active
   • Risk Management: Conservative approach

🛡️ SECURITY FEATURES ACTIVE
============================
   • RugCheck API integration for token security analysis
   • Automatic filtering of honeypots and rug pulls
   • Risk level classification (SAFE/LOW/MEDIUM/HIGH/CRITICAL)

Start 10-minute scanning? (y/N): y
```

### Method 2: Daemon Process Manager

**Best for**: Background operation, server deployment, production use

```bash
# Start daemon
./run_10min_scan_daemon.sh start

# Check status
./run_10min_scan_daemon.sh status

# View logs
./run_10min_scan_daemon.sh logs

# Follow logs in real-time
./run_10min_scan_daemon.sh logs -f

# Stop daemon
./run_10min_scan_daemon.sh stop

# Restart daemon
./run_10min_scan_daemon.sh restart
```

**Features**:
- Background daemon operation
- Process management (start/stop/restart/status)
- Automatic restart on failure
- Log file management
- PID file tracking

### Method 3: Systemd Service (Linux)

**Best for**: Production servers, automatic startup, system integration

```bash
# Install as system service (requires sudo)
sudo ./run_10min_scan_daemon.sh install-service

# Start service
sudo systemctl start token-scanner

# Enable auto-start on boot
sudo systemctl enable token-scanner

# Check status
sudo systemctl status token-scanner

# View logs
sudo journalctl -u token-scanner -f

# Stop service
sudo systemctl stop token-scanner
```

**Features**:
- System-level integration
- Automatic startup on boot
- Systemd logging integration
- Service dependency management
- Automatic restart on failure

### Method 4: Advanced Scheduled Scanner

**Best for**: Custom scan profiles, advanced configuration, multiple strategies

```bash
# Run with standard profile (10 minutes)
python scripts/scheduled_scanner.py --profile standard

# Run with aggressive profile (5 minutes)
python scripts/scheduled_scanner.py --profile aggressive

# Run with conservative profile (15 minutes)
python scripts/scheduled_scanner.py --profile conservative

# Run single scan and exit
python scripts/scheduled_scanner.py --profile standard --single-scan
```

**Available Profiles**:

| Profile | Interval | Strategies | Risk Tolerance | Description |
|---------|----------|------------|----------------|-------------|
| **aggressive** | 5 min | All 5 strategies | Medium | High-frequency scanning |
| **standard** | 10 min | 3 main strategies | Low | Balanced approach |
| **conservative** | 15 min | 2 safe strategies | Low | Strict filtering |
| **discovery** | 30 min | New token focus | Medium | Discovery-oriented |
| **monitoring** | 60 min | Established tokens | Low | Long-term monitoring |

## 🔧 Configuration

### Environment Variables

Set these in your `.env` file:

```bash
# Required
BIRDEYE_API_KEY=your_birdeye_api_key_here

# Optional - Override scan interval
SCAN_INTERVAL_MINUTES=10

# Optional - Enable enhanced timeframes
ENHANCED_TIMEFRAMES=true

# Optional - Telegram alerts
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### Scan Interval Customization

The system supports multiple ways to set scan intervals:

1. **Environment Variable** (highest priority):
   ```bash
   export SCAN_INTERVAL_MINUTES=10
   ```

2. **Config File** (`config/config.yaml`):
   ```yaml
   TOKEN_DISCOVERY:
     scan_interval_minutes: 10
   ```

3. **Script Parameters**: Built into each scanning method

### RugCheck Configuration

RugCheck filtering is enabled by default with these settings:

```python
# Risk thresholds (customizable in code)
risk_thresholds = {
    "min_safe_score": 80.0,      # Scores ≥80 are safe
    "min_low_risk_score": 60.0,  # Scores ≥60 are low risk  
    "min_medium_risk_score": 40.0, # Scores ≥40 are medium risk
}

# Tokens automatically filtered out:
critical_issues = [
    "honeypot",
    "proxy_contract", 
    "ownership_not_renounced",
    "pausable_contract",
    "blacklist_function",
    "whitelist_function"
]
```

## 📊 Monitoring and Logs

### Log Locations

- **Interactive Scanner**: Console output + `logs/` directory
- **Daemon Mode**: `logs/scanner_daemon.log`
- **Systemd Service**: `journalctl -u token-scanner`
- **Advanced Scanner**: `logs/` directory with structured logging

### Log Format

All scanners use structured logging for easy analysis:

```json
{
  "event": "scan_complete",
  "scan_id": "scan_1640995200",
  "profile": "standard",
  "duration_seconds": 45.2,
  "total_discovered": 25,
  "total_filtered": 18,
  "tokens_removed": 7,
  "timestamp": 1640995200
}
```

### Key Metrics to Monitor

- **Scan Duration**: How long each scan takes
- **Discovery Rate**: Tokens found per scan
- **Filtering Rate**: Percentage of tokens filtered out
- **API Call Efficiency**: Calls per token analyzed
- **Error Rate**: Failed scans or API calls

## 🚀 Getting Started

### Quick Start (10-Minute Interactive Scanning)

1. **Setup Environment**:
   ```bash
   # Run setup if not done already
   ./setup_environment.sh
   
   # Ensure .env file has your API key
   echo "BIRDEYE_API_KEY=your_key_here" >> .env
   ```

2. **Test RugCheck Integration**:
   ```bash
   ./run_rugcheck_test.sh
   ```

3. **Start 10-Minute Scanning**:
   ```bash
   ./run_10min_scan.sh
   ```

### Production Deployment (Daemon Mode)

1. **Test in Foreground**:
   ```bash
   ./run_10min_scan.sh
   # Let it run for a few cycles, then Ctrl+C
   ```

2. **Start as Daemon**:
   ```bash
   ./run_10min_scan_daemon.sh start
   ```

3. **Monitor Operation**:
   ```bash
   # Check status
   ./run_10min_scan_daemon.sh status
   
   # Follow logs
   ./run_10min_scan_daemon.sh logs -f
   ```

4. **Install as System Service** (Linux):
   ```bash
   sudo ./run_10min_scan_daemon.sh install-service
   sudo systemctl start token-scanner
   sudo systemctl enable token-scanner
   ```

## 📈 Expected Performance

### Scan Timing
- **Scan Duration**: 30-60 seconds per cycle
- **RugCheck Analysis**: ~600ms per token (with rate limiting)
- **Total Cycle Time**: ~2-5 minutes depending on tokens found

### Filtering Effectiveness
Based on testing with various market conditions:

- **Volume-based strategies**: 20-40% of tokens filtered out
- **New listings**: 50-70% of tokens filtered out  
- **Trending tokens**: 10-30% of tokens filtered out
- **Overall average**: ~30-50% filtering rate

### Resource Usage
- **Memory**: ~100-200MB during operation
- **CPU**: Low usage, spikes during analysis
- **Network**: Respectful API usage with rate limiting
- **Storage**: Log files grow ~10-50MB per day

## 🛠️ Troubleshooting

### Common Issues

**Scanner Won't Start**
```bash
# Check environment
./run_10min_scan.sh
# Look for error messages about missing API keys or dependencies
```

**High Filtering Rate (>80%)**
- Market conditions may be particularly risky
- Consider adjusting risk thresholds in code
- Check RugCheck API status

**Low Discovery Rate (<5 tokens per scan)**
- Market may be quiet
- Check Birdeye API limits and status
- Verify strategy configurations

**Daemon Process Dies**
```bash
# Check logs for errors
./run_10min_scan_daemon.sh logs

# Restart daemon
./run_10min_scan_daemon.sh restart
```

### Debug Commands

```bash
# Test RugCheck connectivity
python -c "
import asyncio
from api.rugcheck_connector import RugCheckConnector
rugcheck = RugCheckConnector()
result = asyncio.run(rugcheck.analyze_token_security('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'))
print(f'Risk: {result.risk_level.value}, Healthy: {result.is_healthy}')
"

# Test single scan
python scripts/scheduled_scanner.py --profile standard --single-scan

# Check daemon status
./run_10min_scan_daemon.sh status
```

## 🔄 Customization

### Adjusting Scan Intervals

**For Interactive Scanner**:
Edit `run_10min_scan.sh` and change:
```bash
export SCAN_INTERVAL_MINUTES=15  # Change to desired interval
```

**For Daemon**:
Edit `run_10min_scan_daemon.sh` and change:
```bash
export SCAN_INTERVAL_MINUTES=15  # In start_daemon function
```

**For Advanced Scanner**:
Create custom profile or modify existing ones in `scripts/scheduled_scanner.py`

### Adding Custom Strategies

1. Create new strategy class in `core/token_discovery_strategies.py`
2. Add to strategy instances in scanner scripts
3. Configure in scan profiles

### Modifying Risk Thresholds

Edit `api/rugcheck_connector.py`:
```python
self.risk_thresholds = {
    "min_safe_score": 85.0,      # Increase for stricter filtering
    "min_low_risk_score": 65.0,  # Adjust as needed
    "min_medium_risk_score": 45.0,
}
```

## 📋 Best Practices

### For Development
- Use interactive scanner for testing
- Monitor logs closely during development
- Test RugCheck integration regularly

### For Production
- Use daemon mode or systemd service
- Set up log rotation
- Monitor system resources
- Have alerting for daemon failures

### For Risk Management
- Start with conservative profiles
- Monitor filtering rates
- Adjust risk thresholds based on market conditions
- Keep RugCheck integration enabled

## 🔗 Related Documentation

- [RugCheck Integration Guide](RUGCHECK_INTEGRATION_GUIDE.md)
- [API Endpoints Reference](api_endpoints_reference.md)
- [Token Discovery Strategies](../docs/token_discovery.md)
- [Project Structure](../PROJECT_STRUCTURE.md)

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review log files for error messages
3. Test individual components (RugCheck, Birdeye API)
4. Verify environment configuration

The 10-minute scanning system is designed to be robust and self-healing, with comprehensive error handling and automatic recovery mechanisms. 