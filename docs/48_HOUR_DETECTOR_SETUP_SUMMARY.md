# 48-Hour High Conviction Token Detector Setup

## 📋 Overview

Successfully created a 48-hour version of the high conviction token detector that runs scans every 30 minutes for a total of 96 scan cycles over 48 hours (2 scans per hour).

## 🎯 Key Configuration

- **Duration**: 48 hours
- **Scan Interval**: 30 minutes
- **Total Cycles**: 96 scans
- **Frequency**: 2 scans per hour
- **Analysis**: Full comprehensive analysis on every cycle

## 📁 Files Created

### 1. `run_48hour_30min_detector.py`
- Main Python script for 48-hour detection
- Based on the proven 6-hour detector architecture
- Includes all advanced analysis features:
  - Pure scoring system analysis
  - Pipeline performance monitoring
  - Cost analysis and optimization
  - Token quality analysis
  - System health monitoring
  - Data accuracy validation

### 2. `run_48hour_detector.sh`
- Shell script for easy execution
- Handles virtual environment activation
- Provides comprehensive logging
- Includes dependency checking
- Timestamps all output

## 🚀 How to Run

### Option 1: Using the Shell Script (Recommended)
```bash
./run_48hour_detector.sh
```

### Option 2: Direct Python Execution
```bash
# Activate virtual environment first
source venv/bin/activate  # or source venv_new/bin/activate

# Run the detector
python run_48hour_30min_detector.py
```

## 📊 What You'll Get

### During Execution
- **Real-time Progress**: Live updates every 30 minutes
- **Cycle Summaries**: Detailed breakdown of each scan cycle
- **Token Discovery**: Individual tokens found with scores and platforms
- **API Usage Stats**: Real-time API call tracking across all platforms
- **Performance Metrics**: Pipeline efficiency and bottleneck analysis
- **Cost Tracking**: Running cost analysis and optimization recommendations

### Enhanced Analysis Per Cycle
Each of the 96 cycles includes:
1. **Token Breakdown**: Individual tokens discovered with full details
2. **Scoring Analysis**: Pure numerical scoring without categories
3. **Pipeline Performance**: Detailed timing and bottleneck analysis
4. **Cost Analysis**: Running costs and optimization recommendations
5. **Token Quality**: Score distribution and platform effectiveness
6. **System Health**: Error rates and recovery metrics
7. **Data Accuracy**: Validation and consistency checks

### Final Comprehensive Summary
At the end of 48 hours:
- **Complete Session Statistics**: All 96 cycles summarized
- **API Usage Breakdown**: Total calls per platform (Birdeye, DexScreener, RugCheck, Jupiter, Meteora)
- **Cost Analysis**: Total estimated costs and efficiency metrics
- **Token Discovery**: All high conviction tokens found over 48 hours
- **Performance Analysis**: Overall system performance and recommendations

## 🔧 Technical Features

### Robust Architecture
- **Error Handling**: Graceful handling of API failures and network issues
- **Data Validation**: Automatic detection and correction of data inconsistencies
- **Memory Management**: Optimized for long-running sessions
- **Logging**: Comprehensive logging to timestamped files

### Advanced Analytics
- **Cross-Platform Analysis**: Validates tokens across multiple DEX platforms
- **Smart Money Detection**: Tracks whale and institutional activity
- **Momentum Analysis**: Identifies tokens with strong price/volume momentum
- **Security Validation**: RugCheck integration for security analysis

### API Integration
- **Multi-Platform Support**: Birdeye, DexScreener, RugCheck, Jupiter, Meteora
- **Rate Limiting**: Intelligent rate limiting to avoid API restrictions
- **Cost Optimization**: Efficient API usage to minimize costs
- **Fallback Mechanisms**: Graceful degradation when APIs are unavailable

## 📈 Expected Performance

### Scan Statistics
- **96 total scan cycles** over 48 hours
- **~2,000-5,000 API calls** total (depending on token discovery)
- **10-50 high conviction tokens** discovered (market dependent)
- **Estimated cost**: $0.50-$2.00 total (varies by API usage)

### System Requirements
- **Memory**: ~100-200MB peak usage
- **CPU**: Low usage (mostly waiting between scans)
- **Network**: Stable internet connection required
- **Storage**: ~10-50MB for logs and results

## 🛡️ Safety Features

### Interruption Handling
- **Graceful Shutdown**: Ctrl+C safely stops the detector
- **Session Recovery**: Maintains session statistics even if interrupted
- **Data Preservation**: All discovered tokens and analysis saved

### Error Recovery
- **API Failure Recovery**: Continues operation even if some APIs fail
- **Network Resilience**: Handles temporary network outages
- **Data Validation**: Automatic correction of inconsistent data

## 📝 Logging and Output

### Console Output
- Real-time progress updates
- Detailed cycle summaries
- Enhanced analysis tables (requires `prettytable`)
- Color-coded status indicators

### Log Files
- Timestamped log files in `logs/` directory
- Complete session history preserved
- Both console output and detailed metrics logged

## 🎯 Use Cases

### Quantitative Trading
- **48-hour market scanning** for systematic token discovery
- **Cross-platform validation** for reduced false positives
- **Performance analytics** for strategy optimization

### Research and Analysis
- **Market trend analysis** over extended periods
- **Platform effectiveness comparison** across DEX ecosystems
- **Cost-benefit analysis** of different scanning strategies

### Production Deployment
- **Automated token discovery** for trading algorithms
- **Alert generation** for high conviction opportunities
- **Performance monitoring** for system optimization

## 🚨 Important Notes

1. **Long Running Process**: This is a 48-hour commitment - ensure stable environment
2. **API Costs**: Monitor API usage to stay within budget limits
3. **Network Stability**: Ensure reliable internet connection
4. **System Resources**: Monitor memory usage on resource-constrained systems
5. **Rate Limits**: Respects API rate limits but may hit daily quotas on high-activity days

## 🔄 Comparison with 6-Hour Version

| Feature | 6-Hour Version | 48-Hour Version |
|---------|---------------|-----------------|
| Duration | 6 hours | 48 hours |
| Scan Interval | 20 minutes | 30 minutes |
| Total Cycles | 18 | 96 |
| Scans per Hour | 3 | 2 |
| Expected Tokens | 5-20 | 40-200 |
| Estimated Cost | $0.10-$0.50 | $0.50-$2.00 |
| Use Case | Quick analysis | Extended monitoring |

## 🎉 Ready to Run!

The 48-hour detector is now ready for deployment. Simply execute:

```bash
./run_48hour_detector.sh
```

And let it run for the full 48 hours to get comprehensive market analysis and token discovery across all supported platforms. 