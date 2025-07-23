# Position Tracking System Guide

## Overview

The Position Tracking System is a comprehensive solution that allows users to track their token positions and receive intelligent exit alerts when market conditions suggest it's time to take profit. It seamlessly integrates with the existing high conviction token detector to provide a complete trading workflow.

## 🎯 Key Features

### Position Management
- **Track Positions**: Monitor token positions with entry price, size, and targets
- **Real-time P&L**: Continuous profit/loss calculation and tracking
- **Custom Targets**: Set profit targets and stop losses per position
- **Hold Time Tracking**: Monitor how long positions have been held
- **Portfolio Overview**: View all positions and total portfolio performance

### Exit Signal Detection
- **Multi-factor Analysis**: 5-factor scoring system for exit signals
- **Risk Assessment**: Intelligent risk level determination
- **Time-based Modifiers**: Adjustments based on hold time
- **Confidence Scoring**: Signal strength and confidence levels
- **Actionable Recommendations**: Clear HOLD/REDUCE/EXIT guidance

### Telegram Integration
- **Bot Commands**: Full command interface for position management
- **Real-time Alerts**: Instant notifications when exit conditions are met
- **Interactive Buttons**: Easy position tracking from token alerts
- **Status Reports**: Portfolio summaries and position details

## 🚀 Quick Start

### 1. Configuration

Add position tracking configuration to your `config/config.yaml`:

```yaml
position_tracking:
  enabled: true
  min_score_for_tracking: 7.0
  auto_suggest_tracking: true
  
position_monitoring:
  check_interval_minutes: 15
  max_concurrent_analysis: 5
  enable_auto_close: false
  
telegram:
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
```

### 2. Start Position Monitor

```bash
# Start the position monitoring daemon
./run_position_monitor_daemon.sh start

# Check daemon status
./run_position_monitor_daemon.sh status

# View logs
./run_position_monitor_daemon.sh logs
```

### 3. Track Your First Position

When you receive a high conviction token alert, use the provided command:

```
/track 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU 0.004178 1000 25 10
```

This tracks the token with:
- **Address**: `7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU`
- **Entry Price**: `$0.004178`
- **Position Size**: `$1000`
- **Profit Target**: `25%`
- **Stop Loss**: `10%`

## 📱 Telegram Commands

### Position Management

#### `/track <address> <price> [size] [profit%] [stop%]`
Start tracking a new position.

**Examples:**
```
/track 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU 0.004178
/track 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU 0.004178 1000
/track 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU 0.004178 1000 25 10
```

**Parameters:**
- `address`: Token contract address (required)
- `price`: Entry price in USD (required)
- `size`: Position size in USD (optional, default: 100)
- `profit%`: Profit target percentage (optional, default: 50)
- `stop%`: Stop loss percentage (optional, default: 20)

#### `/positions`
View all your active positions with current P&L.

**Example Output:**
```
📊 Your Active Positions (3 positions)

🎯 BONK - $BONK
💰 Entry: $0.000012 → Current: $0.000015 (+25.0%)
💎 Size: $1,000 → Value: $1,250 → P&L: +$250
⏱️ Hold Time: 2h 15m
🎯 Targets: 50% profit, 20% stop

🎯 PEPE - $PEPE  
💰 Entry: $0.000008 → Current: $0.000007 (-12.5%)
💎 Size: $500 → Value: $437.50 → P&L: -$62.50
⏱️ Hold Time: 45m
🎯 Targets: 30% profit, 15% stop

📈 Portfolio Total: +$187.50 (+12.5%)
```

#### `/untrack <symbol>`
Stop tracking a position (close it).

**Examples:**
```
/untrack BONK
/untrack PEPE
```

#### `/set_targets <symbol> <profit%> <stop%>`
Update profit and stop loss targets for a position.

**Examples:**
```
/set_targets BONK 40 15
/set_targets PEPE 25 10
```

### Configuration Commands

#### `/preferences`
View and configure your position tracking preferences.

**Example Output:**
```
⚙️ Your Position Tracking Preferences

🎯 Exit Signal Sensitivity: Medium (60)
⏰ Max Hold Time: 48 hours
💰 Default Profit Target: 50%
🛑 Default Stop Loss: 20%
📢 Alert Frequency: Every 30 minutes
🤖 Auto-close on Exit Signal: Disabled

Use /set_sensitivity, /set_hold_time, etc. to modify
```

#### `/set_sensitivity <level>`
Set exit signal sensitivity (weak/medium/strong).

**Examples:**
```
/set_sensitivity weak      # 40+ signal strength
/set_sensitivity medium    # 60+ signal strength  
/set_sensitivity strong    # 80+ signal strength
```

#### `/set_hold_time <hours>`
Set maximum hold time for positions.

**Examples:**
```
/set_hold_time 24    # 24 hours
/set_hold_time 48    # 48 hours
/set_hold_time 72    # 72 hours
```

### Information Commands

#### `/help`
Show all available commands and usage examples.

#### `/status`
Show position tracking system status and statistics.

## 🔍 Exit Signal Analysis

The system uses a sophisticated 5-factor scoring system to determine when to exit positions:

### Scoring Factors

1. **Volume Degradation (25% weight)**
   - Analyzes 24h volume decline
   - >50% decline = 25 points
   - Indicates reduced market interest

2. **Price Momentum (25% weight)**  
   - Tracks price trend changes
   - Bullish→Bearish shift = 25 points
   - Shows momentum reversal

3. **Whale Activity (20% weight)**
   - Monitors smart money movements
   - Large holder selling = 20 points
   - Early warning of institutional exits

4. **Community Sentiment (15% weight)**
   - Social media activity analysis
   - Declining engagement = 15 points
   - Measures community confidence

5. **Technical Indicators (15% weight)**
   - RSI, support levels, patterns
   - Overbought + support break = 15 points
   - Traditional TA signals

### Time-based Modifiers

- **4+ hours held**: +5 points
- **24+ hours held**: +10 points
- **Approaching max hold time**: Additional scaling

### Signal Interpretation

| Score Range | Risk Level | Recommendation | Action |
|-------------|------------|----------------|---------|
| 0-39        | Low        | HOLD          | Continue holding |
| 40-59       | Weak       | MONITOR       | Watch closely |
| 60-79       | Moderate   | REDUCE        | Consider partial exit |
| 80-89       | Strong     | EXIT          | Exit recommended |
| 90-100      | Critical   | EXIT NOW      | Immediate exit |

### Example Exit Alert

```
🚨 EXIT SIGNAL DETECTED

🎯 Position: BONK ($BONK)
📊 Signal Strength: 75/100 (Strong)
🎯 Recommendation: REDUCE POSITION

📈 Analysis:
• Volume degradation: -60% (25 pts)
• Price momentum: Bearish shift (20 pts) 
• Whale activity: Large sells detected (15 pts)
• Community sentiment: Declining (10 pts)
• Technical: RSI overbought (5 pts)

💰 Current P&L: +$250 (+25%)
⏱️ Hold Time: 6 hours

🎯 Suggested Action:
Consider taking 50-75% profit while maintaining small position for potential recovery.
```

## 🛠️ System Architecture

### Core Components

1. **Position Tracker** (`services/position_tracker.py`)
   - SQLite database for persistence
   - CRUD operations for positions
   - User preference management
   - P&L calculations

2. **Exit Signal Detector** (`services/exit_signal_detector.py`)
   - Multi-factor analysis engine
   - Real-time token data fetching
   - Signal strength calculation
   - Risk assessment

3. **Telegram Bot Handler** (`services/telegram_bot_handler.py`)
   - Command processing
   - Interactive user interface
   - Alert formatting and sending
   - User state management

4. **Position Monitor** (`scripts/position_monitor.py`)
   - Background daemon process
   - Continuous position monitoring
   - Alert triggering
   - Performance tracking

### Integration Points

- **High Conviction Detector**: Automatic tracking suggestions
- **Birdeye API**: Real-time price and volume data
- **Telegram Alerter**: Existing alert infrastructure
- **Cache Manager**: Efficient data caching
- **Rate Limiter**: API usage optimization

## 🔧 Advanced Configuration

### Database Settings

```yaml
position_tracking:
  database_path: "data/positions.db"
  backup_interval_hours: 24
  cleanup_closed_positions_days: 30
```

### Exit Signal Tuning

```yaml
exit_signal_detection:
  volume_degradation_threshold: 0.5    # 50% decline
  price_momentum_window_hours: 4       # 4-hour window
  whale_activity_threshold: 100000     # $100k+ movements
  sentiment_decline_threshold: 0.3     # 30% decline
  technical_rsi_overbought: 70         # RSI > 70
```

### Alert Customization

```yaml
position_alerts:
  min_signal_strength: 60              # Minimum alert threshold
  cooldown_minutes: 60                 # Time between similar alerts
  include_charts: true                 # Include price charts
  include_recommendations: true        # Include action suggestions
```

## 📊 Monitoring and Analytics

### Daemon Status

```bash
# Check if daemon is running
./run_position_monitor_daemon.sh status

# View recent activity
./run_position_monitor_daemon.sh logs

# Run test cycle
./run_position_monitor_daemon.sh test
```

### Performance Metrics

The system tracks:
- **Total positions tracked**
- **Active vs closed positions**
- **Average hold times**
- **Exit signal accuracy**
- **Alert response times**
- **API usage statistics**

### Database Queries

```sql
-- View all active positions
SELECT * FROM positions WHERE status = 'active';

-- Get user statistics
SELECT user_id, COUNT(*) as total_positions, 
       AVG(current_pnl_percentage) as avg_pnl
FROM positions 
WHERE status = 'active' 
GROUP BY user_id;

-- Recent alerts
SELECT * FROM position_alerts 
WHERE sent_at > datetime('now', '-24 hours')
ORDER BY sent_at DESC;
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Daemon Won't Start
```bash
# Check configuration
cat config/config.yaml | grep -A 10 telegram

# Check dependencies
python3 -c "from services.position_tracker import PositionTracker; print('OK')"

# Check logs
tail -f logs/position_monitor.log
```

#### 2. No Exit Alerts
```bash
# Verify positions are tracked
sqlite3 data/positions.db "SELECT COUNT(*) FROM positions WHERE status='active';"

# Check monitoring cycle
./run_position_monitor_daemon.sh test

# Verify API connectivity
python3 -c "from api.birdeye_connector import BirdeyeAPI; print('API OK')"
```

#### 3. Telegram Commands Not Working
```bash
# Verify bot token and chat ID
grep -E "(bot_token|chat_id)" config/config.yaml

# Test telegram connection
python3 -c "from services.telegram_alerter import TelegramAlerter; print('Telegram OK')"
```

### Log Analysis

Key log patterns to monitor:

```bash
# Successful monitoring cycles
grep "Monitoring cycle.*completed" logs/position_monitor.log

# Exit alerts sent
grep "Sent exit alert" logs/position_monitor.log

# API errors
grep "ERROR.*API" logs/position_monitor.log

# Position tracking activity
grep "Position.*tracked\|untracked" logs/position_monitor.log
```

## 🔄 Workflow Integration

### Complete Trading Workflow

1. **Detection**: High conviction detector finds promising token
2. **Alert**: Receive Telegram alert with token details
3. **Decision**: Evaluate token and decide to enter position
4. **Tracking**: Use `/track` command to start monitoring
5. **Monitoring**: System continuously analyzes exit conditions
6. **Alert**: Receive exit signal when conditions deteriorate
7. **Action**: Take profit or cut losses based on signal
8. **Closure**: Position automatically marked as closed

### Best Practices

1. **Set Realistic Targets**: Use 20-50% profit targets for most tokens
2. **Use Stop Losses**: Always set stop losses to limit downside
3. **Monitor Signals**: Pay attention to exit signal strength and confidence
4. **Take Partial Profits**: Consider reducing position size on strong signals
5. **Review Performance**: Regularly check position statistics and outcomes

## 📈 Future Enhancements

### Planned Features

- **Portfolio Analytics**: Detailed performance tracking and reporting
- **Risk Management**: Position sizing recommendations based on portfolio
- **Advanced Signals**: Additional technical and on-chain indicators
- **Mobile App**: Dedicated mobile interface for position management
- **Social Features**: Share positions and strategies with community
- **Backtesting**: Historical analysis of exit signal performance

### Integration Opportunities

- **DeFi Protocols**: Direct integration with DEX trading
- **Wallet Connections**: Automatic position detection from wallet activity
- **Price Alerts**: Additional price-based alert types
- **News Integration**: Sentiment analysis from news and social media
- **Portfolio Rebalancing**: Automated position management strategies

---

## 🆘 Support

For support with the position tracking system:

1. **Check Documentation**: Review this guide and other docs
2. **Check Logs**: Look at daemon and application logs
3. **Test Components**: Use test commands to isolate issues
4. **Community**: Ask questions in the project community
5. **Issues**: Report bugs and feature requests on GitHub

Remember: This system is designed to assist with trading decisions, not replace your judgment. Always do your own research and never invest more than you can afford to lose. 