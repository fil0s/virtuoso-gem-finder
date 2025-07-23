# 🚀 3-Hour Detector with Dashboard - Command Guide (9 Cycles)

## 📊 Dashboard Features

The dashboard provides real-time insights into your gem detection sessions:

- **Session Overview**: Runtime, progress, total tokens analyzed
- **Performance Metrics**: Average cycle times, discovery rates, efficiency
- **Top Tokens**: Best scoring tokens discovered across all cycles
- **Platform Performance**: Which platforms are finding the most tokens
- **API Efficiency**: Batch processing stats and cost savings
- **Recent Activity**: Last few cycles with key metrics

## 🔧 Basic Commands

### Standard Run (No Dashboard)
```bash
source venv_new/bin/activate && python run_3hour_detector.py
```

### With Debug Output
```bash
source venv_new/bin/activate && python run_3hour_detector.py --debug
```

## 📊 Dashboard Commands

### Compact Dashboard (Recommended)
```bash
source venv_new/bin/activate && python run_3hour_detector.py --compact-dashboard
```
- Shows key metrics in a condensed format
- Updates after each cycle
- Perfect for monitoring progress

### Full Dashboard (Detailed)
```bash
source venv_new/bin/activate && python run_3hour_detector.py --dashboard
```
- Complete dashboard with all sections
- Clears screen for real-time updates
- Shows comprehensive insights

### Dashboard + Debug Mode
```bash
source venv_new/bin/activate && python run_3hour_detector.py --compact-dashboard --debug
```
- Combines dashboard with verbose logging
- Best for troubleshooting while monitoring

## 🌌 Futuristic Dashboard Commands (NEW!)

### Futuristic Full Dashboard
```bash
source venv_new/bin/activate && python run_3hour_detector.py --futuristic-dashboard
```
- Modern dark-mode interface with cosmic theme
- Glassmorphism effects and neon colors
- Complete dashboard with all sections
- Futuristic progress bars and visualizations

### Futuristic Compact Dashboard (Recommended)
```bash
source venv_new/bin/activate && python run_3hour_detector.py --futuristic-compact
```
- Sleek condensed format with neon styling
- Perfect for monitoring with style
- Modern glassmorphism design
- Animated progress indicators

### Futuristic + Debug Mode
```bash
source venv_new/bin/activate && python run_3hour_detector.py --futuristic-compact --debug
```
- Combines futuristic styling with verbose logging
- Best for troubleshooting with visual appeal

## 🎯 Dashboard Sections Explained

### 📊 Session Overview
- **Runtime**: How long the session has been running
- **Progress**: Completion percentage with visual progress bar
- **Total Analyzed**: Cumulative tokens processed
- **High Conviction**: Tokens meeting quality threshold
- **Alerts Sent**: Telegram notifications sent
- **API Calls Saved**: Efficiency gains from batching

### ⚡ Performance Metrics
- **Avg Tokens/Cycle**: Average discovery rate
- **Avg Cycle Time**: How long each scan takes
- **Avg Batch Efficiency**: API optimization percentage
- **Discovery Rate**: High conviction tokens as % of total

### 🏆 Top Tokens
- **Best 5 tokens** discovered across all cycles
- **Score, Symbol, Source** for each token
- **Cycle number** when found

### 🌐 Platform Performance
- **Token counts** by platform (Pump.fun, Raydium, etc.)
- **Average tokens per cycle** for each platform
- **Active cycles** count

### 📊 Recent Activity
- **Last 3 cycles** with key metrics
- **Timestamp, tokens analyzed, high conviction count**
- **Cycle duration** for performance monitoring

### 🚀 API Efficiency
- **Batch efficiency percentage**
- **Total API calls** vs **batch calls**
- **Cost savings estimate** in USD
- **Calls saved** through optimization

## 📁 Data Export

Dashboard automatically saves session data to JSON files:
- **File**: `dashboard_session_YYYYMMDD_HHMMSS.json`
- **Contains**: All cycle data, tokens found, performance metrics
- **Use**: Analysis, reporting, historical comparison

## 🔄 Real-time Updates

### Compact Dashboard Updates
- Shows after each cycle completion
- Key metrics in 4-5 lines
- Progress bar visualization
- Best token highlight

### Full Dashboard Updates
- Complete screen refresh
- All sections updated
- Comprehensive insights
- Visual progress tracking

## 💡 Pro Tips

1. **Start with Compact Dashboard** for first-time users
2. **Use Debug Mode** only when troubleshooting
3. **Monitor API Efficiency** to see batching benefits
4. **Check Recent Activity** for pattern recognition
5. **Review Top Tokens** for quality assessment

## 📈 Performance Monitoring

The dashboard tracks several key performance indicators:

- **Tokens/Second**: Processing efficiency
- **API Calls/Hour**: Resource usage
- **Batch Efficiency**: Optimization effectiveness
- **Discovery Rate**: Quality of token finding
- **Platform Distribution**: Source diversification

## 🎯 Example Dashboard Output

```
============================================================
🚀 DASHBOARD - Cycle 3/9 (33.3%)
============================================================
⏰ Runtime: 1.0h | 🔍 Analyzed: 425 | 🎯 High Conviction: 8 | 📱 Alerts: 3
📈 |██████████░░░░░░░░░░░░░░░░░░░░| 33.3%
🏆 Best Token: SUPERGEM (92.3 pts)
🚀 API Efficiency: 67.5% | 💰 Saved: ~1,240 calls
============================================================
```

## 🚨 Important Notes

- Dashboard requires successful detector initialization
- Session data is automatically saved on completion
- Progress bars show real-time completion status
- All metrics are cumulative across the entire session
- Dashboard works alongside all existing features (alerts, logging, etc.)

## 🔧 Troubleshooting

If dashboard doesn't appear:
1. Check that `dashboard_utils.py` exists
2. Verify Python can import dashboard modules
3. Check for any import errors in logs
4. Try running without dashboard first to isolate issues

The dashboard enhances monitoring without affecting core detection functionality!