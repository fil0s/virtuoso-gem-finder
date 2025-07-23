# Quick Start Guide

Get the Virtuoso Gem Hunter running in under 5 minutes!

## 🚀 Prerequisites

- **Python 3.8+** installed
- **Birdeye API Key** ([Get one here](https://birdeye.so/api))
- (Optional) **Telegram Bot** for alerts

## ⚡ Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Run the automated setup script
./setup_environment.sh

# Edit your API keys
nano .env

# Start the monitor
./run_monitor.sh
```

### Option 2: Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp env.template .env
nano .env  # Edit with your API keys

# 3. Setup config file (optional)
cp config/config.example.yaml config/config.yaml

# 4. Run the monitor
./run_monitor.sh
```

**Required in .env:**
```bash
BIRDEYE_API_KEY=your_birdeye_api_key_here
```

**Optional for Telegram alerts:**
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

## 🎯 Expected Output

```
========================================
VIRTUOSO GEM HUNTER CONFIGURATION
========================================

--- OPTIMIZATION FEATURES ---
✓ Batch API processing (90% reduction in individual calls)
✓ Progressive analysis pipeline (3-stage filtering)
✓ Smart caching with TTL optimization
✓ Centralized data management
✓ Efficient discovery with strict filters

--- EXPECTED PERFORMANCE ---
API calls per scan: 50-150 (vs 700-1000+ in old system)
Expected reduction: 75-85%
Analysis quality: Maintained or improved

========================================
STARTING VIRTUOSO GEM HUNTER
========================================

==========================================
EARLY TOKEN DISCOVERY SCAN #1
==========================================
...
```

## 📊 Performance Metrics

After each scan, you'll see detailed metrics:

```
DETAILED API CALL BREAKDOWN - SCAN #1
--------------------------------------------------------------------------------

📊 API CALL SUMMARY:
   Discovery Calls:      1
   Batch Calls:          3
   Individual Calls:    15
   TOTAL API CALLS:     19

🏆 OPTIMIZATION GRADE: A+ (Excellent)
```

## 🔧 Quick Configuration

### Basic Settings (Optional)
```bash
# Scan every 30 minutes instead of 20
export EARLY_DETECTION_SCAN_INTERVAL=30

# Analyze maximum 50 tokens instead of 30
export EARLY_DETECTION_MAX_TOKENS=50

# Only alert on tokens with score > 80
export EARLY_DETECTION_MIN_SCORE=80
```

### Telegram Alerts Setup
```bash
# 1. Create Telegram Bot
# - Message @BotFather on Telegram
# - Send /newbot and follow instructions
# - Copy the bot token

# 2. Get your Chat ID
# - Message @userinfobot on Telegram
# - Copy your chat ID

# 3. Add to .env file
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# 4. Enable in config.yaml
nano config/config.yaml
# Set: TELEGRAM.enabled: true
```

## 🎛️ Advanced Configuration

For more advanced settings, edit the configuration:
```bash
nano config/config.yaml
# Customize filters, thresholds, and analysis parameters
```

## 🎛️ Logging Optimization (Optional)

The monitor includes advanced logging optimizations for better performance:

### **Quick Setup for Production**
```bash
# In your .env file, add:
LOGGING_MODE=production
LOGGING_ENABLE_ASYNC=true
LOGGING_ENABLE_JSON=true
LOGGING_ENABLE_COMPRESSION=true
```

### **Available Modes**
- `standard` - Basic logging (default)
- `optimized` - 60-80% faster with JSON + compression
- `production` - 95% faster with sampling + all optimizations
- `development` - Verbose logging for debugging
- `minimal` - Maximum performance, minimal logs

### **Test Performance**
```bash
# Run performance benchmark
python scripts/test_logging_performance.py
```

**Expected improvements:**
- 🚀 **60-80% faster** with async logging
- 💾 **90% smaller** log files with compression
- 📊 **Better monitoring** with JSON structured logs

---

## 📚 Next Steps

- Read the [Complete README](README.md) for full documentation
- Check the [API Optimization Guide](docs/api_optimization_guide.md)
- Customize filters in `config/config.yaml`
- Set up Telegram alerts for notifications

## 🔧 Alternative Run Methods

```bash
# Direct Python execution
python monitor.py

# With virtual environment
source venv/bin/activate
python monitor.py

# Background execution
nohup ./run_monitor.sh > monitor.log 2>&1 &
```

---

**🎉 You're now running an optimized token monitor with 75-85% fewer API calls!**

**💡 Pro Tip:** Use the automated setup script `./setup_environment.sh` for the smoothest installation experience. 