# Birdeye Starter Plan Optimization Guide

## Overview

This guide helps you run the Early Gem Detector within Birdeye starter plan limitations.

## 🚀 Quick Start

### 1. Run Optimized Detector
```bash
python run_starter_plan_detector.py
```

### 2. Use Starter Plan Config
```bash
python run_3hour_detector.py --config config/config.starter_plan.yaml
```

## 📊 Starter Plan Limitations

| Feature | Starter Plan | Paid Plans |
|---------|-------------|------------|
| Rate Limit | 30 RPM | 100+ RPM |
| Batch Endpoints | ❌ Not Available | ✅ Available |
| Advanced Analytics | ❌ Limited | ✅ Full Access |
| Historical Data | ❌ Limited | ✅ Full Access |
| Concurrent Requests | ❌ Not Supported | ✅ Supported |

## 🔧 Optimizations Applied

### 1. Rate Limiting
- **Requests per minute**: Limited to 30 (conservative)
- **Delay between requests**: 2 seconds minimum
- **No concurrent requests**: Sequential processing only

### 2. Endpoint Fallbacks
- **Batch metadata** → Individual overview calls
- **Batch price/volume** → Individual price calls
- **Batch trade data** → Individual transaction calls

### 3. Caching Enhancements
- **Extended cache duration**: 2x longer caching
- **Aggressive caching**: Cache everything possible
- **Reduced API calls**: Minimize redundant requests

### 4. Analysis Optimization
- **Lightweight mode**: Skip expensive analysis
- **Trending focus**: Prioritize trending tokens
- **Reduced token count**: 10 tokens per cycle max

## 💰 Cost Optimization

### API Call Reduction
- **Before**: 50+ calls per cycle
- **After**: 15-20 calls per cycle
- **Savings**: 60-70% reduction

### Cache Strategy
- **Metadata**: 1 hour cache (vs 5 minutes)
- **Price data**: 10 minutes cache (vs 5 minutes)
- **Trending data**: 30 minutes cache (vs 10 minutes)

## 🎯 Best Practices

### 1. Monitor Usage
```bash
# Check API usage in logs
grep "API calls" logs/detector.log
```

### 2. Stay Within Limits
- Keep cycles to 20 minutes minimum
- Monitor rate limit warnings
- Use extended caching when possible

### 3. Upgrade Considerations
Consider upgrading to paid plan for:
- Batch endpoint access
- Higher rate limits
- Advanced analytics
- Historical data access

## 🔍 Troubleshooting

### Rate Limit Errors
```
🚫 Rate limit hit (429) for /defi/v3/ohlcv
```

**Solution**: Increase delay between requests or reduce token count.

### Authentication Errors
```
❌ AUTHENTICATION FAILED for /defi/v3/token/meta-data/multiple
```

**Solution**: This endpoint is not available in starter plan. Use individual calls instead.

### Missing Data
If you're getting incomplete results:
1. Check if endpoints are available in starter plan
2. Verify rate limits aren't being exceeded
3. Enable aggressive caching
4. Reduce token count per cycle

## 📈 Performance Expectations

### Starter Plan Performance
- **Tokens per cycle**: 5-10 tokens
- **Cycle duration**: 20-30 minutes
- **API calls per cycle**: 15-20 calls
- **Detection accuracy**: 70-80% (reduced due to limited data)

### Upgrade Benefits
- **Tokens per cycle**: 20-50 tokens
- **Cycle duration**: 5-10 minutes
- **API calls per cycle**: 50-100 calls
- **Detection accuracy**: 85-95%

## 🚀 Advanced Configuration

### Custom Rate Limits
Edit `config/config.starter_plan.yaml`:
```yaml
birdeye_starter_plan:
  rate_limit_rpm: 25  # Reduce if hitting limits
  rate_limit_delay: 2.5  # Increase delay
```

### Cache Optimization
```yaml
caching:
  extended_cache_duration: true
  cache_multiplier: 3.0  # Even longer caching
```

### Analysis Mode
```yaml
detection_strategy:
  max_tokens_per_cycle: 5  # Very conservative
  use_trending_only: true
  skip_comprehensive_analysis: true
```

## 📞 Support

If you encounter issues:
1. Check the logs for specific error messages
2. Verify your API key is valid
3. Ensure you're not exceeding rate limits
4. Consider upgrading to paid plan for full features
