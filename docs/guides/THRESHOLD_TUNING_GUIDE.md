# Smart Money Whale Strategy Threshold Tuning Guide

## 🎯 Overview

The **Threshold Tuning System** is a comprehensive tool designed to optimize the Smart Money Whale Strategy by systematically testing different threshold configurations in descending order of strictness. This helps find the optimal balance between selectivity (quality) and opportunity discovery (quantity).

## 🚀 Quick Start

### Run Threshold Tuning
```bash
# Make sure you're in the project directory and have API key set
export BIRDEYE_API_KEY=your_api_key_here

# Run the tuning system
./run_threshold_tuning.sh
```

### Choose Your Mode
- **Option 1**: Comprehensive Analysis (tests all 5 levels)
- **Option 2**: Stop on First Success (stops when tokens are found)

## 📊 Threshold Levels Explained

The system tests **5 threshold levels** in descending order of strictness:

### Level 1: Maximum Selectivity 🔒
- **Purpose**: Ultra-strict criteria for highest conviction plays only
- **Use Case**: When you want only the absolute best opportunities
- **Expected Results**: Very few tokens, but extremely high quality

**Key Thresholds**:
- `min_whale_count`: 2
- `min_whale_volume`: 500,000
- `whale_confidence_threshold`: 0.6
- `min_smart_traders`: 3
- `smart_money_skill_threshold`: 0.65
- `min_confluence_score`: 0.8

### Level 2: High Selectivity 🎯
- **Purpose**: Slightly relaxed criteria for quality opportunities
- **Relaxation**: ~20% reduction in strictness
- **Use Case**: Balanced approach with high standards

**Key Changes**:
- `min_whale_volume`: 400,000 (↓20%)
- `min_smart_traders`: 2 (↓1)
- `whale_confidence_threshold`: 0.54 (↓10%)
- `min_confluence_score`: 0.68 (↓15%)

### Level 3: Medium Selectivity ⚖️
- **Purpose**: Balanced criteria for broader opportunity capture
- **Relaxation**: ~40% reduction in strictness
- **Use Case**: Good balance between quality and quantity

**Key Changes**:
- `min_whale_count`: 1 (↓1)
- `min_whale_volume`: 300,000 (↓40%)
- `whale_confidence_threshold`: 0.48 (↓20%)
- `min_confluence_score`: 0.56 (↓30%)

### Level 4: Low Selectivity 📈
- **Purpose**: Relaxed criteria for maximum opportunity discovery
- **Relaxation**: ~60% reduction in strictness
- **Use Case**: When market conditions are tough or you want broader coverage

**Key Changes**:
- `min_whale_volume`: 200,000 (↓60%)
- `min_smart_traders`: 1 (minimum viable)
- `smart_money_skill_threshold`: 0.455 (↓30%)
- `min_confluence_score`: 0.48 (↓40%)

### Level 5: Minimum Viable 🌊
- **Purpose**: Most relaxed criteria for comprehensive market scanning
- **Relaxation**: ~80% reduction in strictness
- **Use Case**: Market research, finding emerging opportunities

**Key Changes**:
- `min_whale_volume`: 100,000 (↓80%)
- `whale_confidence_threshold`: 0.36 (↓40%)
- `smart_money_confidence_threshold`: 0.42 (↓40%)
- `min_confluence_score`: 0.40 (↓50%)

## 📈 Smart Scaling Logic

Different parameter types scale at different rates:

### 🔢 Count-Based Parameters
- **Examples**: `min_whale_count`, `min_smart_traders`, `min_whale_diversity`
- **Scaling**: Decrease in integer steps (3→2→1)
- **Logic**: Minimum viable counts for meaningful analysis

### 📊 Confidence/Ratio Parameters  
- **Examples**: `whale_confidence_threshold`, `smart_money_skill_threshold`
- **Scaling**: Proportional decrease (0.7 → 0.63 → 0.56)
- **Logic**: Gradual relaxation of quality standards

### 💰 Volume Parameters
- **Examples**: `min_whale_volume`
- **Scaling**: Aggressive decrease (500k → 400k → 300k → 200k → 100k)
- **Logic**: Volume thresholds often the biggest barrier

### 🎚️ Multipliers
- **Examples**: `confluence_bonus_multiplier`
- **Scaling**: Conservative decrease (1.5 → 1.425 → 1.35)
- **Logic**: Preserve scoring balance

## 📊 Analysis & Results

### Performance Metrics Tracked
- **Execution Time**: How long each level takes
- **API Calls**: Number of API requests made
- **Tokens Found**: Count of discovered opportunities
- **Quality Score**: Calculated quality rating (0-100)

### Quality Analysis
- **Whale Metrics**: Total whales, average whales per token
- **Smart Money Metrics**: Total smart traders, skill distribution
- **Risk Assessment**: Distribution of risk levels
- **Conviction Analysis**: Distribution of conviction levels

### Best Performer Categories
- **Best Quality**: Highest quality score
- **Most Efficient**: Best tokens per API call ratio
- **Fastest**: Shortest execution time

## 🎯 Optimization Insights

### Threshold Effectiveness Analysis
The system analyzes which thresholds are most restrictive:

```
📊 MAXIMUM: 0.0% success rate, 0.0 avg tokens when successful
📊 HIGH: 100.0% success rate, 5.0 avg tokens when successful  
📊 MEDIUM: 100.0% success rate, 12.0 avg tokens when successful
📊 LOW: 100.0% success rate, 25.0 avg tokens when successful
```

### Recommendations Generated
- **Optimal Level**: Which threshold level performs best
- **Expected Performance**: Tokens per scan, quality score, execution time
- **Tuning Insights**: Specific recommendations for production use

## 💾 Output Files

### Comprehensive Results
**File**: `scripts/results/threshold_tuning_results_[timestamp].json`

Contains:
- Complete results for all tested levels
- Performance metrics and comparisons
- Best performer analysis
- Comprehensive recommendations

### Optimal Configuration
**File**: `scripts/results/optimal_whale_config_[timestamp].json`

Contains:
- Ready-to-use optimal criteria
- Risk management settings
- Expected performance metrics
- Configuration metadata

## 🛠️ Using Results in Production

### 1. Review Results
```bash
# Check the results files
ls scripts/results/threshold_tuning_results_*.json
ls scripts/results/optimal_whale_config_*.json
```

### 2. Apply Optimal Configuration
```python
import json

# Load optimal configuration
with open('scripts/results/optimal_whale_config_[timestamp].json', 'r') as f:
    optimal_config = json.load(f)

# Apply to strategy
strategy = SmartMoneyWhaleStrategy()
strategy.criteria.update(optimal_config['criteria'])
strategy.risk_management.update(optimal_config['risk_management'])
```

### 3. Validate Performance
```bash
# Test with the optimal configuration
./run_smart_money_whale_debug.sh
```

## 🔧 Advanced Configuration

### Custom Threshold Levels
You can modify the threshold levels in `scripts/tune_smart_money_whale_thresholds.py`:

```python
def _define_threshold_levels(self) -> List[ThresholdLevel]:
    # Customize base criteria
    base_criteria = {
        "min_whale_count": 2,  # Your custom value
        "min_whale_volume": 500000,  # Your custom value
        # ... other parameters
    }
```

### Stop Conditions
- **Comprehensive Mode**: Tests all levels regardless of results
- **Stop on Success Mode**: Stops at first successful level
- **Custom Logic**: Modify the stopping conditions in the code

## 📈 Market Condition Adaptation

### Bull Market
- **Recommended**: Level 1-2 (High selectivity)
- **Reason**: Many opportunities available, can be selective

### Bear Market  
- **Recommended**: Level 3-4 (Medium-Low selectivity)
- **Reason**: Fewer opportunities, need broader criteria

### Sideways Market
- **Recommended**: Level 2-3 (High-Medium selectivity)
- **Reason**: Balanced approach for mixed conditions

## 🚨 Troubleshooting

### No Tokens Found at Any Level
**Possible Causes**:
- API issues or rate limiting
- Market conditions (very low activity)
- Base token filtering too strict
- Whale/smart money services not functioning

**Solutions**:
1. Check API connectivity and key
2. Verify whale and smart money services
3. Test during high-activity market periods
4. Review base token filtering criteria

### Quality Scores Too Low
**Possible Causes**:
- Market conditions affecting token quality
- Scoring algorithm needs adjustment
- Thresholds not aligned with current market

**Solutions**:
1. Adjust quality scoring weights
2. Review risk and conviction assessments
3. Consider market-specific threshold sets

### Performance Issues
**Possible Causes**:
- Too many API calls
- Network latency
- Inefficient threshold combinations

**Solutions**:
1. Optimize API call patterns
2. Use caching more effectively
3. Consider parallel processing

## 🎯 Best Practices

### 1. Regular Tuning
- Run threshold tuning weekly during volatile periods
- Monthly tuning during stable periods
- After major market events or changes

### 2. A/B Testing
- Test different threshold configurations
- Compare performance over time
- Use backtesting when possible

### 3. Market Context
- Consider current market conditions
- Adjust based on trading volume patterns
- Account for seasonal effects

### 4. Documentation
- Document which configurations work best when
- Track performance over time
- Share insights with team

## 📚 Related Documentation

- [Smart Money Whale Strategy Guide](SMART_MONEY_WHALE_STRATEGY_GUIDE.md)
- [API Endpoints Reference](BIRDEYE_API_ENDPOINTS_REFERENCE.md)
- [Strategy Testing Guide](STRATEGY_TESTING_GUIDE.md)
- [Production Deployment Guide](PRODUCTION_INSIGHTS_FROM_LIVE_TESTING.md)

---

**Next Steps**: Run the threshold tuning system and analyze the results to find your optimal configuration! 🚀 