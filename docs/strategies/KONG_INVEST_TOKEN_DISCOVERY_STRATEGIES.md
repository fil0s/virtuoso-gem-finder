# Token Discovery Strategies - Kong Invest & Current Implementation

> **Reference**: [Kong Invest Token Discovery Guide](https://konginvest.ai/learn/token-discovery)

## Overview

This document consolidates token discovery strategies from Kong Invest's methodology with our current implementation approaches. Token discovery is the systematic process of identifying promising early-stage cryptocurrency tokens before they gain widespread recognition, combining on-chain analytics, trading patterns, and risk assessment.

---

## Kong Invest Token Discovery Strategies

Based on Kong Invest's systematic approach to token discovery, they implement five core strategies:

### 1. Volume Momentum Strategy

**Purpose**: Identify tokens with significant trading activity growth that may indicate emerging trends or market interest.

**Kong Invest Implementation**:
- **Sort By**: `volume_24h_change_percent` (descending)
- **API Parameters**:
  ```yaml
  sort_by: volume_24h_change_percent
  sort_type: desc
  min_liquidity: 100000
  min_volume_24h_usd: 50000
  min_holder: 500
  limit: 20
  ```

**Implementation Strategy**:
- Run daily at 00:00 UTC
- Track tokens appearing in top 20 for 3+ consecutive days
- Research fundamentals before portfolio consideration
- Prioritize tokens with consistent volume growth across multiple timeframes (24h, 8h, 4h)

**Risk Management**:
- Exclude tokens with suspicious volume patterns (sudden spikes followed by drops)
- Verify volume is distributed across multiple DEXs/pools
- Check holder concentration metrics

### 2. Recent Listings with Traction

**Purpose**: Discover newly listed tokens that are gaining significant market attention and liquidity.

**Kong Invest Implementation**:
- **Sort By**: `recent_listing_time` (descending)
- **API Parameters**:
  ```yaml
  sort_by: recent_listing_time
  sort_type: desc
  min_liquidity: 200000
  min_trade_24h_count: 500
  min_holder: 300
  limit: 30
  ```

**Implementation Strategy**:
- Run twice weekly (Monday and Thursday at 12:00 UTC)
- Monitor new listings that maintain or grow liquidity for 7+ days
- Compare trade count trends to identify sustained interest
- Prioritize tokens showing organic growth patterns rather than artificial pumps

**Risk Management**:
- Implement stricter position size limits for newer tokens
- Require minimum 7-day history before significant allocation
- Verify team and project information thoroughly

### 3. Price Momentum with Volume Confirmation

**Purpose**: Find tokens with strong price performance backed by increasing trading volume.

**Kong Invest Implementation**:
- **Sort By**: `price_change_24h_percent` (descending)
- **API Parameters**:
  ```yaml
  sort_by: price_change_24h_percent
  sort_type: desc
  min_volume_24h_usd: 100000
  min_volume_24h_change_percent: 20
  min_liquidity: 300000
  min_trade_24h_count: 700
  limit: 25
  ```

**Implementation Strategy**:
- Run daily after major market sessions (08:00 UTC and 20:00 UTC)
- Look for tokens appearing consistently across multiple timeframes
- Compare 4h, 3h, and 24h price changes to identify sustainable momentum
- Prioritize tokens where volume growth exceeds or matches price growth

**Risk Management**:
- Avoid chasing tokens already up significantly (>50% in 24h)
- Verify price action against broader market trends
- Check for unusual wallet activity or wash trading

### 4. Liquidity Growth Detector

**Purpose**: Find tokens that are rapidly gaining liquidity, which often precedes major price movements.

**Kong Invest Implementation**:
- **Sort By**: `liquidity` (descending)
- **API Parameters**:
  ```yaml
  sort_by: liquidity
  sort_type: desc
  min_market_cap: 1000000
  max_market_cap: 100000000
  min_holder: 1000
  min_volume_24h_usd: 200000
  limit: 50
  ```

**Implementation Strategy**:
- Run weekly on Friday at 16:00 UTC and track changes in rankings
- Identify tokens moving up the liquidity rankings rapidly
- Calculate liquidity-to-market-cap ratios to find undervalued tokens
- Prioritize tokens with growing holder counts and increasing trade frequency

**Risk Management**:
- Verify liquidity is distributed across multiple pools
- Check for single-wallet liquidity provision
- Monitor liquidity stability over 7-day period

### 5. High Trading Activity Filter

**Purpose**: Discover tokens with unusually high trading activity relative to their market cap.

**Kong Invest Implementation**:
- **Sort By**: `trade_24h_count` (descending)
- **API Parameters**:
  ```yaml
  sort_by: trade_24h_count
  sort_type: desc
  min_liquidity: 150000
  min_volume_24h_usd: 75000
  min_holder: 400
  limit: 30
  ```

**Implementation Strategy**:
- Run daily at 04:00 UTC
- Calculate ratio of trade count to market cap to find unusually active tokens
- Look for tokens with consistently high trading activity across multiple days
- Prioritize tokens where trading activity is growing week-over-week

**Risk Management**:
- Verify trade count distribution (should be spread across time periods)
- Check for bot activity or wash trading patterns
- Compare with historical activity levels

---

## Kong Invest vs Current Implementation Comparison

| Strategy | Kong Invest Focus | Our Implementation | Key Differences |
|----------|-------------------|-------------------|-----------------|
| **Volume Momentum** | `volume_24h_change_percent` sorting | `volume_24h_usd` sorting | Kong focuses on volume growth rate, we focus on absolute volume |
| **Recent Listings** | Higher liquidity thresholds ($200K) | Lower liquidity thresholds ($75K) | Kong is more conservative with new listings |
| **Price Momentum** | Volume change confirmation (20%+) | Static volume thresholds | Kong requires volume growth confirmation |
| **Liquidity Growth** | Market cap range filtering | No market cap limits | Kong targets specific market cap ranges |
| **High Activity** | Daily execution | Our strategy varies | Kong runs more frequently |

---

## Kong Invest Scheduling Strategy

Kong Invest implements a sophisticated scheduling approach:

- **Daily Strategies**: Volume Momentum (00:00 UTC), Price Momentum (08:00 & 20:00 UTC), High Trading Activity (04:00 UTC)
- **Weekly Strategies**: Liquidity Growth (Friday 16:00 UTC)
- **Bi-Weekly Strategies**: Recent Listings (Monday & Thursday 12:00 UTC)

This creates comprehensive market coverage while avoiding over-scanning and API cost optimization.

---

## Current Implementation Strategies

Based on our existing system, we have implemented the following comprehensive token discovery strategies:

### 1. Volume Momentum Strategy

**Purpose**: Identify tokens experiencing significant trading activity growth patterns.

**Implementation Details**:
- **Sort By**: Volume 24h USD (descending)
- **Key Filters**:
  - Minimum liquidity: $50,000
  - Minimum 24h volume: $30,000  
  - Minimum holder count: 100
  - Maximum price change: 200% (avoid extreme pumps)

**Risk Management**:
- Tracks volume consistency over time
- Flags suspicious volume spikes (>3x normal)
- Monitors holder distribution quality

```yaml
api_parameters:
  sort_by: "volume_24h_usd"
  sort_type: "desc"
  min_liquidity: 50000
  min_volume_24h_usd: 30000
  min_holder: 100
  max_price_change_24h_percent: 200
  limit: 20
```

### 2. Recent Listings with Traction Strategy

**Purpose**: Catch newly listed tokens that are gaining immediate organic traction.

**Implementation Details**:
- **Sort By**: Recent listing time (descending)
- **Key Filters**:
  - Minimum liquidity: $75,000
  - Minimum 24h volume: $25,000
  - Minimum holder count: 50
  - Maximum age: 7 days

**Risk Management**:
- Emphasizes organic growth over artificial pumps
- Requires minimum holder diversity
- Validates liquidity sustainability

```yaml
api_parameters:
  sort_by: "recent_listing_time"
  sort_type: "desc"
  min_liquidity: 75000
  min_volume_24h_usd: 25000
  min_holder: 50
  max_age_days: 7
  limit: 25
```

### 3. Price Momentum with Volume Confirmation Strategy

**Purpose**: Find tokens with strong price performance backed by legitimate volume.

**Implementation Details**:
- **Sort By**: Price change 24h percentage (descending)
- **Key Filters**:
  - Minimum liquidity: $100,000
  - Minimum 24h volume: $40,000
  - Minimum holder count: 200
  - Price change range: 10-150%

**Risk Management**:
- Volume-to-price-change correlation analysis
- Prevents selection of extreme pump scenarios
- Requires established holder base

```yaml
api_parameters:
  sort_by: "price_change_24h_percent"
  sort_type: "desc"
  min_liquidity: 100000
  min_volume_24h_usd: 40000
  min_holder: 200
  min_price_change_24h_percent: 10
  max_price_change_24h_percent: 150
  limit: 15
```

### 4. Liquidity Growth Strategy

**Purpose**: Detect tokens experiencing rapid but sustainable liquidity growth.

**Implementation Details**:
- **Sort By**: Liquidity (descending)
- **Key Filters**:
  - Minimum liquidity: $200,000
  - Minimum 24h volume: $50,000
  - Minimum holder count: 300
  - Minimum market cap: $500,000

**Risk Management**:
- Liquidity-to-volume ratio analysis
- Multi-DEX liquidity distribution checks
- Sustainable growth pattern verification

```yaml
api_parameters:
  sort_by: "liquidity"
  sort_type: "desc"
  min_liquidity: 200000
  min_volume_24h_usd: 50000
  min_holder: 300
  min_market_cap: 500000
  limit: 20
```

### 5. High Trading Activity Strategy

**Purpose**: Identify tokens with high trading activity relative to their market cap.

**Implementation Details**:
- **Sort By**: Trade count 24h (descending)
- **Key Filters**:
  - Minimum liquidity: $80,000
  - Minimum trade count: 500/24h
  - Minimum holder count: 150
  - Maximum market cap: $50M

**Risk Management**:
- Trade count to holder ratio analysis
- Bot trading pattern detection
- Organic activity verification

```yaml
api_parameters:
  sort_by: "trade_24h_count"
  sort_type: "desc"
  min_liquidity: 80000
  min_trade_24h_count: 500
  min_holder: 150
  max_market_cap: 50000000
  limit: 30
```

---

## Advanced Discovery Strategies (Proposed)

### 6. Smart Money Accumulation Strategy

**Purpose**: Track tokens being accumulated by historically profitable wallets.

**Key Features**:
- Monitor top holder changes over time
- Cross-reference with whale discovery service
- Track accumulation patterns by profitable addresses
- Verify wallet profitability history

**Implementation**:
```yaml
api_parameters:
  sort_by: "holder"
  sort_type: "desc"
  min_liquidity: 100000
  min_volume_24h_usd: 50000
  min_holder: 300
  limit: 30
```

### 7. Organic Growth Pattern Strategy

**Purpose**: Identify tokens with growth patterns matching successful memecoin launches.

**Key Features**:
- Steady holder growth (10-30% daily)
- Consistent volume without artificial spikes
- Price appreciation with healthy retracements
- Growing social metrics

**Implementation**:
```yaml
api_parameters:
  sort_by: "price_change_7d_percent"
  sort_type: "desc"
  min_liquidity: 150000
  min_volume_24h_usd: 75000
  min_holder: 500
  max_price_change_24h_percent: 30
  limit: 25
```

### 8. Whale Rotation Strategy

**Purpose**: Track tokens where whales from successful projects are rotating profits.

**Key Features**:
- Monitor whale wallet movements
- Track profit rotation patterns
- Identify cross-token investment flows
- Analyze timing of whale entries

**Implementation**:
```yaml
api_parameters:
  sort_by: "volume_24h_usd"
  sort_type: "desc"
  min_liquidity: 200000
  min_holder: 400
  min_market_cap: 500000
  max_market_cap: 50000000
  limit: 20
```

---

## Multi-Factor Scoring System

Our system employs a comprehensive **Gem Score** calculation that combines multiple factors:

### Core Factors (Current Implementation)

| Factor | Weight | Data Source | Scoring Logic |
|--------|--------|-------------|---------------|
| **Liquidity** | 25% | `/defi/token_overview` | `log10(liquidity+1)/6 * 100` |
| **Age** | 15% | `/defi/token_creation_info` | `2-24h: 100pts, 0.5-2h: 50pts` |
| **Concentration** | 20% | `/defi/v3/token/holder` | `(1 - Gini) * 100` |
| **Price Change** | 20% | `/defi/historical_price_unix` | `0-200%: 100pts, >200%: 50pts` |
| **Volume** | 10% | `/defi/token_overview` | `log10(volume+1)/6 * 100` |
| **Momentum** | 10% | OHLCV data | `15min momentum analysis` |

### Advanced Bonuses

- **Trending Bonus**: +10 points if token appears in trending list
- **New Listing Bonus**: +10 points for newly listed tokens
- **Smart Money Bonus**: +20 points (proportional to smart money involvement)
- **Clustering Bonus**: +5 points per whale (minimum 2 whales)
- **Volatility Bonus**: +10 points if healthy volatility >5%
- **Momentum Bonus**: +10 points if 15min momentum >10%

### Security Penalties

- **Scam Flag**: -30 points
- **Risk Flag**: -10 points

---

## Risk Management Framework

### Base Quality Filters

All strategies implement these fundamental filters:

1. **Minimum Liquidity**: $20,000+ (varies by strategy)
2. **Minimum Market Cap**: $30,000+
3. **Minimum Holder Count**: 50+ (varies by strategy)
4. **Recent Trading Activity**: Within 2 hours
5. **Volume Thresholds**: Strategy-specific minimums

### Advanced Risk Controls

1. **RugCheck Integration**: Automated security screening
2. **Holder Concentration Analysis**: Gini coefficient calculation
3. **Volume Manipulation Detection**: Suspicious pattern identification
4. **Multi-DEX Verification**: Liquidity distribution analysis
5. **Smart Money Validation**: Whale wallet verification

### Progressive Filtering Pipeline

1. **Initial Discovery**: Multiple sorting strategies
2. **Quality Filtering**: Basic metrics validation
3. **Security Screening**: RugCheck analysis
4. **Deep Analysis**: Multi-factor scoring
5. **Risk Assessment**: Final quality gates

---

## Implementation Architecture

### Batch Processing Optimization

- **API Efficiency**: Intelligent batching and caching
- **Rate Limiting**: Sophisticated rate management
- **Concurrent Processing**: Parallel strategy execution
- **Progressive Analysis**: Early elimination of low-potential tokens

### Temporal Adaptivity

- **Market Hours Adjustment**: Dynamic criteria based on trading sessions
- **Weekend Relaxation**: Adjusted thresholds for off-peak periods
- **Historical Context**: Time-based pattern recognition

### Performance Monitoring

- **Strategy Performance Tracking**: Individual strategy effectiveness
- **API Cost Management**: Birdeye API usage optimization
- **Alert Generation**: Automated opportunity notifications
- **Backtesting Framework**: Historical validation capabilities

---

## Data Sources & API Integration

### Primary Data Sources

1. **Birdeye API Endpoints**:
   - `/defi/v3/token/list` - Core token discovery
   - `/defi/token_trending` - Trending token identification
   - `/defi/v3/token/holder` - Holder analysis
   - `/defi/v2/tokens/top_traders` - Smart money tracking
   - `/defi/v2/tokens/new_listing` - New listing detection

2. **RugCheck API**: Security and risk assessment

3. **Social Media APIs** (Planned):
   - Telegram community metrics
   - Twitter engagement analysis
   - Discord activity tracking

### Data Processing Pipeline

1. **Real-time Collection**: Continuous market monitoring
2. **Batch Processing**: Efficient API utilization
3. **Quality Assessment**: Multi-stage filtering
4. **Storage & Caching**: Optimized data management
5. **Alert Generation**: Automated opportunity identification

---

## Future Enhancements

### Planned Improvements

1. **Machine Learning Integration**: Adaptive scoring weights
2. **Social Media Analysis**: Community sentiment tracking
3. **Cross-Chain Discovery**: Multi-blockchain support
4. **Advanced Pattern Recognition**: Historical success pattern matching
5. **Real-time Alerts**: Sub-minute opportunity detection

### Integration Opportunities

1. **Trading Bot Integration**: Automated position taking
2. **Portfolio Management**: Risk-adjusted allocation
3. **Performance Analytics**: Strategy effectiveness measurement
4. **Community Features**: Shared discovery insights

---

## Usage Guidelines

### Best Practices

1. **Diversification**: Use multiple strategies simultaneously
2. **Risk Management**: Never exceed position size limits
3. **Continuous Monitoring**: Regular strategy performance review
4. **Security First**: Always verify RugCheck results
5. **Historical Validation**: Backtest before live deployment

### Common Pitfalls

1. **Over-optimization**: Avoid curve-fitting to historical data
2. **Ignoring Risk Signals**: Don't override security warnings
3. **FOMO Trading**: Stick to systematic approach
4. **Insufficient Diversification**: Avoid concentration risk

---

## Conclusion

Effective token discovery requires a systematic, multi-faceted approach that combines quantitative analysis, risk management, and continuous adaptation. By implementing these strategies with proper risk controls and performance monitoring, traders can gain a significant edge in identifying high-potential opportunities before they gain widespread recognition.

The integration of Kong Invest's methodologies with our current implementation creates a robust framework for early-stage token identification while maintaining strict risk management standards.

---

*To complete this document with Kong Invest's specific strategies, please provide the actual content from https://konginvest.ai/learn/token-discovery* 