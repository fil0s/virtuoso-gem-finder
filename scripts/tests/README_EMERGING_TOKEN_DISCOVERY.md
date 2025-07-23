# 🚀 Emerging Token Discovery System

## Overview

The Emerging Token Discovery System is an advanced pipeline that identifies new and promising tokens through cross-platform analysis of Meteora and Jupiter, specifically designed to catch tokens in their early growth phases before they become widely recognized.

## 🎯 Key Features

### **Multi-Stage Discovery Pipeline**
1. **Meteora New Pool Detection** - Identifies tokens in newly created high-activity pools
2. **Jupiter Early Liquidity Analysis** - Finds tokens establishing tradability 
3. **Cross-Platform Validation** - Validates discoveries across both platforms
4. **Risk-Adjusted Scoring** - Specialized scoring for emerging vs established tokens
5. **Comprehensive Risk Assessment** - Multi-factor risk analysis

### **Advanced Filtering Criteria**

#### **Meteora Emerging Filters:**
```python
{
    'min_volume_24h': 10000,        # Lower threshold for emerging
    'max_pool_age_hours': 168,      # Max 1 week old
    'min_vlr': 2.0,                 # Volume-to-Liquidity Ratio
    'max_tvl': 500000,              # Focus on smaller pools
    'min_trade_count': 50,          # Some activity required
    'min_growth_rate': 1.5          # 150% volume growth
}
```

#### **Jupiter Emerging Filters:**
```python
{
    'min_liquidity_score': 3,       # Lower threshold
    'max_price_impact': 0.1,        # 10% max slippage
    'max_route_complexity': 6,      # Reasonable routing
    'min_quote_success_rate': 0.8,  # 80% quote success
    'max_token_age_days': 30        # Focus on recent tokens
}
```

## 🔍 Discovery Methods

### **1. Meteora New Pool Discovery**
- **Target**: Tokens in newly created pools with high activity relative to size
- **Key Metric**: Volume-to-Liquidity Ratio (VLR) > 2.0
- **Focus**: Small pools ($10K-$500K TVL) with surprising volume
- **Scoring**: Based on VLR, volume growth, and pool age

### **2. Jupiter Early Liquidity Establishment**
- **Target**: Recently added tokens showing tradability
- **Key Metric**: Successful routing with reasonable slippage
- **Focus**: Tokens with improving liquidity metrics
- **Scoring**: Based on liquidity score, price impact, and route complexity

### **3. Cross-Platform Validation**
- **Target**: Tokens appearing on both platforms
- **Confidence**: HIGHEST (validated across systems)
- **Bonus**: +5 points for cross-platform presence
- **Risk**: Reduced due to multi-platform validation

## 📊 Scoring System

### **Emerging Token Scoring (0-15 scale)**

#### **Meteora Scoring:**
```python
VLR Score:
- VLR > 20: +8 points
- VLR > 10: +6 points  
- VLR > 5:  +4 points
- VLR > 2:  +2 points

Volume Score:
- > $500K: +4 points
- > $100K: +3 points
- > $50K:  +2 points
- > $10K:  +1 point

Small Pool Bonus:
- TVL < $50K + Volume > $50K: +3 points
- TVL < $100K + Volume > $100K: +2 points
```

#### **Jupiter Scoring:**
```python
Liquidity Score: 0-10 (from quote analysis)
Activity Score: 0-10 (from routing success)

Price Impact Bonus:
- < 2%: +3 points
- < 5%: +2 points
- < 10%: +1 point

Route Complexity Bonus:
- ≤ 2 hops: +2 points
- ≤ 4 hops: +1 point
```

## ⚖️ Risk Assessment

### **Risk Categories**
- **LOW**: Cross-platform validated, good metrics
- **MEDIUM**: Single platform or moderate risk indicators  
- **HIGH**: New tokens, high volatility indicators

### **Risk Factors Analyzed**
1. **Liquidity Risk**: Pool/token liquidity depth
2. **Volume Risk**: Abnormal volume patterns (manipulation indicators)
3. **Age Risk**: Very new tokens carry higher risk
4. **Slippage Risk**: High price impact on trades
5. **Routing Risk**: Complex routing paths

## 🎯 Usage Examples

### **Basic Discovery**
```python
from emerging_token_discovery_system import EmergingTokenDiscoverySystem

# Initialize system
discovery = EmergingTokenDiscoverySystem()

# Run discovery
results = await discovery.run_emerging_token_discovery()

# Access results
cross_platform_tokens = results['emerging_tokens']['cross_platform']
meteora_only = results['emerging_tokens']['meteora_only']
jupiter_only = results['emerging_tokens']['jupiter_only']
```

### **Risk-Filtered Results**
```python
# Get only high-confidence emerging tokens
risk_filtered = results['emerging_tokens']['risk_filtered']

# Filter by confidence level
high_confidence = [t for t in risk_filtered if t.get('confidence_level') == 'HIGH']
```

## 📈 Expected Output

### **Sample Results Structure**
```json
{
  "discovery_summary": {
    "timestamp": "2025-06-23T10:30:00",
    "duration_seconds": 45.2,
    "status": "SUCCESS"
  },
  "discovery_results": {
    "meteora_emerging_count": 12,
    "jupiter_emerging_count": 8,
    "cross_platform_count": 3,
    "risk_filtered_count": 7
  },
  "emerging_tokens": {
    "cross_platform": [...],
    "meteora_only": [...],
    "jupiter_only": [...],
    "risk_filtered": [...]
  }
}
```

### **Sample Token Data**
```json
{
  "address": "TokenAddress123...",
  "symbol": "NEWTOKEN",
  "platforms": ["meteora_emerging", "jupiter_emerging"],
  "platform_count": 2,
  "total_score": 18.5,
  "confidence_level": "HIGH",
  "risk_assessment": {
    "overall_risk": "MEDIUM",
    "liquidity_risk": "LOW",
    "volume_risk": "MEDIUM"
  },
  "meteora_data": {
    "vlr": 12.3,
    "volume_24h": 150000,
    "tvl": 12200
  },
  "jupiter_data": {
    "liquidity_score": 7,
    "price_impact": 0.045,
    "route_complexity": 3
  }
}
```

## 🚨 Risk Warnings

### **Important Considerations**
1. **High Risk**: All emerging tokens carry significant risk
2. **Position Sizing**: Never exceed 5% portfolio allocation per token
3. **Monitoring**: Requires active monitoring and quick decision making
4. **Liquidity**: May have poor liquidity and high slippage
5. **Volatility**: Expect high price volatility

### **Best Practices**
- **Start Small**: Test with minimal position sizes
- **Cross-Platform Priority**: Focus on tokens validated across platforms
- **Risk Management**: Set strict stop-losses
- **Diversification**: Don't concentrate in emerging tokens
- **Time Horizon**: Short to medium-term holds typically

## 🔧 Configuration

### **Customizing Discovery Parameters**
```python
custom_config = {
    'meteora_filters': {
        'min_volume_24h': 20000,     # Increase minimum volume
        'min_vlr': 5.0,              # Require higher VLR
        'max_tvl': 200000            # Focus on smaller pools
    },
    'jupiter_filters': {
        'min_liquidity_score': 5,    # Require better liquidity
        'max_price_impact': 0.05     # Lower slippage tolerance
    }
}

discovery = EmergingTokenDiscoverySystem(config=custom_config)
```

## 📊 Performance Metrics

### **Typical Discovery Rates**
- **Meteora Emerging**: 10-20 tokens per scan
- **Jupiter Emerging**: 5-15 tokens per scan  
- **Cross-Platform**: 2-8 tokens per scan
- **High Confidence**: 3-10 tokens per scan

### **Execution Performance**
- **Duration**: 30-60 seconds typical
- **API Calls**: 50-100 calls per scan
- **Success Rate**: 85-95% API success rate

## 🚀 Running the System

### **Simple Test**
```bash
cd scripts/tests
python test_emerging_token_discovery.py
```

### **Full Integration**
```bash
cd scripts/tests  
python enhanced_jupiter_meteora_with_emerging_discovery.py
```

### **Standalone Discovery**
```bash
cd scripts/tests
python emerging_token_discovery_system.py
```

## 📁 Output Files

Results are automatically saved to:
- `emerging_token_discovery_results_{timestamp}.json`
- `enhanced_comprehensive_analysis_{timestamp}.json`

## 🔮 Future Enhancements

### **Planned Features**
1. **Historical Performance Tracking** - Track discovery success rates
2. **Machine Learning Scoring** - AI-enhanced scoring models
3. **Social Sentiment Integration** - Twitter/Telegram signal analysis
4. **Real-time Monitoring** - Continuous discovery daemon
5. **Portfolio Integration** - Direct trading interface

### **Additional Data Sources**
- **Pump.fun** integration for meme token discovery
- **Raydium** DEX-specific analysis
- **On-chain metrics** from Solscan/SolanaFM
- **Social signals** from crypto Twitter

---

*Last Updated: June 2025*  
*System Version: Emerging Token Discovery v1.0* 