# High Conviction Token Detector Guide

## Overview

The High Conviction Token Detector is an advanced system that combines cross-platform analysis with detailed Birdeye analysis to identify high-conviction trading opportunities. It runs every 15 minutes and only alerts on new high-conviction tokens to avoid spam.

## 🎯 Key Features

- **Cross-Platform Analysis**: Initial filtering using DexScreener, RugCheck, and Birdeye
- **Cost-Optimized**: Uses free APIs for initial filtering, detailed Birdeye analysis only for high-conviction candidates
- **Detailed Analysis**: Comprehensive whale, holder, volume, price, and community analysis
- **Smart Alerting**: Only alerts on new tokens, prevents duplicate notifications
- **Telegram Integration**: Rich, detailed alerts with actionable trading information
- **Daemon Mode**: Runs continuously in the background with 15-minute intervals

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   High Conviction Detection Flow                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Cross-Platform Analysis (Cost-Effective Filtering)          │
│    ├── DexScreener: Boosted tokens (free)                      │
│    ├── RugCheck: Trending tokens (free)                        │
│    └── Birdeye: Basic trending data (low cost)                 │
│                                                                 │
│ 2. High-Conviction Filtering                                   │
│    ├── Score threshold: >= 6.0 from cross-platform            │
│    ├── Multi-platform validation                               │
│    └── Remove already alerted tokens                           │
│                                                                 │
│ 3. Detailed Birdeye Analysis (Only for Candidates)            │
│    ├── Token Overview: Price, volume, market cap               │
│    ├── Whale Analysis: Holder concentration, smart money       │
│    ├── Volume/Price Analysis: Trends, momentum, volatility     │
│    ├── Community Analysis: Social presence, boosting           │
│    ├── Security Analysis: Scam/risk flags, authorities         │
│    └── Trading Activity: Transaction patterns, unique traders  │
│                                                                 │
│ 4. Final Scoring & Alerting                                    │
│    ├── Combined score calculation                              │
│    ├── Threshold check: >= 7.0 for alerts                     │
│    └── Detailed Telegram alert with all analysis              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Configuration Setup

```bash
# Copy example configuration
cp config/config.example.yaml config/config.yaml

# Edit configuration (set thresholds, enable Telegram)
nano config/config.yaml
```

### 2. Environment Variables

```bash
# Required for Birdeye analysis
export BIRDEYE_API_KEY="your_birdeye_api_key"

# Required for Telegram alerts
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 3. Test Single Run

```bash
# Test the detector with a single cycle
./run_high_conviction_detector_daemon.sh test
```

### 4. Start Daemon

```bash
# Start continuous detection (15-minute intervals)
./run_high_conviction_detector_daemon.sh start

# Check status
./run_high_conviction_detector_daemon.sh status

# View logs
./run_high_conviction_detector_daemon.sh logs -f
```

## 📊 Configuration Options

### High Conviction Thresholds

```yaml
ANALYSIS:
  alert_score_threshold: 7.0    # Final score threshold for alerts
  
  # Cross-platform minimum score (set in detector)
  # min_cross_platform_score: 6.0
```

### Telegram Settings

```yaml
TELEGRAM:
  enabled: true                 # Enable Telegram alerts
  alert_format: "detailed"      # Use detailed format
  max_alerts_per_hour: 10       # Rate limit alerts
```

### Birdeye API Settings

```yaml
BIRDEYE_API:
  api_key: "${BIRDEYE_API_KEY}"
  rate_limit_requests_per_second: 10
  request_timeout_seconds: 20
```

## 🔍 Analysis Components

### 1. Cross-Platform Analysis

**Data Sources:**
- **DexScreener**: Latest and top boosted tokens
- **RugCheck**: Trending tokens with community votes
- **Birdeye**: High-volume trending tokens

**Scoring Factors:**
- Multi-platform presence (bonus for appearing on multiple platforms)
- Boost consumption rate and effectiveness
- Community sentiment and voting
- Volume and liquidity metrics

### 2. Detailed Birdeye Analysis

#### Token Overview Data
- Real-time price and market cap
- 24h volume and liquidity
- Price changes (5m, 1h, 24h)
- Holder count and transaction metrics

#### Whale & Holder Analysis
- Total holder count
- Whale concentration (>1% holdings)
- Top 10 holder concentration
- Smart money wallet detection
- Top trader activity

#### Volume & Price Analysis
- Volume trend analysis (increasing/stable/decreasing)
- Price momentum (bullish/neutral/bearish)
- Volatility scoring
- Recent volume spikes
- Transaction volume validation

#### Community & Boost Analysis
- Social media presence (website, Twitter, Telegram)
- Community strength scoring
- Boost status and marketing activity
- Social engagement metrics

#### Security Analysis
- Scam and risk flag detection
- Mint and freeze authority status
- Security score calculation
- Risk factor identification

#### Trading Activity Analysis
- Recent transaction patterns
- Buy/sell ratio analysis
- Unique trader count
- Average trade size
- Trading frequency assessment

### 3. Final Scoring Algorithm

```python
final_score = cross_platform_score + adjustments

# Positive adjustments (max +5.5):
# - Volume trend increasing: +0.5
# - Recent volume spike: +0.5
# - Bullish price momentum: +1.0
# - Healthy whale concentration (10-40%): +0.5
# - Smart money detected: +1.0
# - Strong community: +1.0
# - High trading activity: +1.0

# Negative adjustments (max -3.0):
# - Flagged as scam: -3.0
# - Flagged as risky: -1.5
# - Low security score: -1.0
```

## 📱 Telegram Alert Format

### Alert Sections

1. **Header**: Score-based styling with token info
2. **Core Metrics**: Price, market cap, liquidity, volume, holders
3. **Cross-Platform Analysis**: Platform presence and validation
4. **Whale Analysis**: Concentration metrics and smart money
5. **Volume/Price Analysis**: Trends and momentum
6. **Community Analysis**: Social presence and strength
7. **Security Analysis**: Risk factors and flags
8. **Trading Activity**: Recent patterns and metrics
9. **Quick Actions**: Trading links and token address

### Sample Alert

```
🚀🔥 VIRTUOSO GEM DETECTED 🚀🔥
HIGH POTENTIAL
Token: Example Token (EXAMPLE)
Score: 8.2/10

💎 CORE METRICS
💰 Price: $0.001234
📊 Market Cap: $1,234,567
🌊 Liquidity: $456,789
📈 24h Volume: $234,567
👥 Holders: 1,234

🌐 CROSS-PLATFORM VALIDATION
✅ Platforms: DexScreener, RugCheck, Birdeye
📊 Cross-Platform Score: 7.5/10
🚀 Boost Status: Active (High consumption)

🐋 WHALE ANALYSIS
👥 Total Holders: 1,234
📊 Whale Concentration: 25% (Healthy)
🎯 Smart Money: Detected
⭐ Top Traders: 8 active

📈 VOLUME & PRICE ANALYSIS
📈 Volume Trend: Increasing
🚀 Price Momentum: Bullish
⚡ Recent Spike: Yes
🎯 Volatility: Moderate

🌐 COMMUNITY & SOCIAL
✅ Social Score: 7/10
🟢 Community: Strong
📱 Channels: Website, Twitter, Telegram

🔒 SECURITY STATUS
✅ Clean - No major security flags
⚠️ Risk Factors: None detected

🔗 QUICK ACTIONS
📊 View Chart | 📈 Dexscreener | 🚀 Trade Now
```

## 🛠️ Daemon Management

### Commands

```bash
# Start the daemon
./run_high_conviction_detector_daemon.sh start

# Stop the daemon
./run_high_conviction_detector_daemon.sh stop

# Restart the daemon
./run_high_conviction_detector_daemon.sh restart

# Check status and recent logs
./run_high_conviction_detector_daemon.sh status

# View logs (add -f to follow)
./run_high_conviction_detector_daemon.sh logs
./run_high_conviction_detector_daemon.sh logs -f

# Test single run
./run_high_conviction_detector_daemon.sh test

# Install as system service
sudo ./run_high_conviction_detector_daemon.sh install-service
```

### Log Files

- **Daemon logs**: `logs/high_conviction_detector_daemon.log`
- **System service logs**: `logs/systemd_detector.log`

## 💰 Cost Optimization

### API Usage Strategy

1. **Free APIs First**: DexScreener and RugCheck for initial filtering
2. **Birdeye Basic**: Low-cost trending data for cross-platform validation
3. **Birdeye Detailed**: Only for high-conviction candidates (typically 1-5 per cycle)
4. **Batch Operations**: Multiple data points per API call when possible
5. **Smart Caching**: Appropriate TTL for different data types

### Expected Costs

**Per 15-minute cycle:**
- Cross-platform analysis: ~5-10 Birdeye CUs
- Detailed analysis (per candidate): ~50-100 Birdeye CUs
- Average total: ~100-500 CUs per cycle (depending on candidates found)

**Daily estimate**: ~10,000-50,000 Birdeye CUs (well within typical limits)

## 🔧 Troubleshooting

### Common Issues

#### No API Key Errors
```bash
# Check environment variables
echo $BIRDEYE_API_KEY
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# Set in shell profile
echo 'export BIRDEYE_API_KEY="your_key"' >> ~/.bashrc
source ~/.bashrc
```

#### Configuration Issues
```bash
# Verify configuration file exists
ls -la config/config.yaml

# Test configuration loading
python -c "from core.config_manager import ConfigManager; print(ConfigManager('config/config.yaml').get_config())"
```

#### Telegram Not Working
```bash
# Test Telegram bot
curl -X GET "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Test sending message
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
     -d "chat_id=$TELEGRAM_CHAT_ID" \
     -d "text=Test message"
```

#### Daemon Not Starting
```bash
# Check logs for errors
tail -n 50 logs/high_conviction_detector_daemon.log

# Test single run
./run_high_conviction_detector_daemon.sh test

# Check Python path and dependencies
source venv/bin/activate
python -c "import scripts.high_conviction_token_detector"
```

### Debug Mode

```bash
# Run with debug logging
export PYTHONPATH=$PWD:$PYTHONPATH
python scripts/high_conviction_token_detector.py --single-run --config config/config.yaml
```

## 📈 Performance Monitoring

### Key Metrics

- **Detection cycles per hour**: 4 (every 15 minutes)
- **Average candidates per cycle**: 2-5
- **Alert rate**: 0-2 alerts per hour (only high conviction)
- **API usage**: 10k-50k Birdeye CUs per day
- **Cache hit rate**: >80% for repeated data

### Monitoring Commands

```bash
# View real-time status
./run_high_conviction_detector_daemon.sh status

# Monitor logs
./run_high_conviction_detector_daemon.sh logs -f

# Check alerted tokens
cat data/alerted_tokens.json | jq '.'
```

## 🔒 Security Considerations

1. **API Keys**: Store in environment variables, never in code
2. **Rate Limiting**: Built-in rate limiting for all APIs
3. **Error Handling**: Graceful degradation on API failures
4. **Resource Management**: Proper cleanup of connections and resources
5. **Data Validation**: Input validation and sanitization

## 🎯 Best Practices

1. **Start with Test**: Always run a test cycle before starting daemon
2. **Monitor Logs**: Regularly check logs for errors or issues
3. **Adjust Thresholds**: Fine-tune scoring thresholds based on results
4. **Rate Limit Alerts**: Use max_alerts_per_hour to prevent spam
5. **Regular Maintenance**: Restart daemon weekly for optimal performance

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Test individual components
4. Verify API credentials and configuration 