# Token Data Structure Reference

**Comprehensive Documentation of All Data Fields Collected for Each Token**

*Generated from system analysis and API testing*

---

## 📊 **Overview**

This document provides a complete reference of all data fields collected and processed for each token in the Early Token Monitor system. Data is collected from multiple sources including Birdeye API, on-chain analysis, and derived calculations.

---

## 🔍 **Primary Token Data Structure**

### **Core Token Information**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `token_name` | string | Birdeye API | Full token name | "Bonk" |
| `token_symbol` | string | Birdeye API | Token symbol/ticker | "BONK" |
| `token_address` | string | Birdeye API | Contract address | "85VBFQZC9TZkfaptBWjvUw7YbZjy52A6mjtPGjstQAmQ" |
| `token_thumbnail` | string | Birdeye API | Logo/image URL | "https://..." |
| `decimals` | number | Birdeye API | Token decimal places | 6 |
| `link` | string | Generated | Birdeye token page URL | "https://birdeye.so/token/..." |

### **Pricing & Market Data**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `price_now` | number | Birdeye API | Current USD price | 0.00004177 |
| `price_24h_ago` | number | Birdeye API | Price 24 hours ago | 0.00004058 |
| `priceChange24h` | number | Birdeye API | 24h price change % | 2.45 |
| `priceChange4h` | number | Birdeye API | 4h price change % | -1.23 |
| `priceChange1h` | number | Birdeye API | 1h price change % | 0.56 |
| `market_cap` | number | Birdeye API | Market capitalization USD | 98765432.10 |
| `fdv` | number | Birdeye API | Fully diluted valuation | 125834567.89 |

### **Liquidity & Volume Metrics**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `liquidity` | number | Birdeye API | Total liquidity in USD | 125834567.89 |
| `volume_24h` | number | Birdeye API | 24-hour trading volume | 2345678.90 |
| `volume_4h` | number | Birdeye API | 4-hour trading volume | 892345.67 |
| `volume_1h` | number | Birdeye API | 1-hour trading volume | 234567.12 |
| `volume_change_24h` | number | Calculated | 24h volume change % | 15.32 |

### **Supply Information**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `supply.total` | number | Birdeye API | Total token supply | 92666666666666665 |
| `supply.circulating` | number | Birdeye API | Circulating supply | 92666666666666665 |
| `supply.max` | number | Birdeye API | Maximum supply | 999999999999999 |

### **Holder & Community Data**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `holder_count` | number | Birdeye API | Total number of holders | 654321 |
| `top_holders` | array | Birdeye API | List of top holders with percentages | [{"owner": "...", "percentage": 0.849}] |
| `unique_trader_count` | number | Birdeye API | 24h unique traders | 2890 |

### **Security & Risk Assessment**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `is_scam` | boolean | Birdeye API | Scam detection flag | false |
| `is_risky` | boolean | Birdeye API | Risk level assessment | false |
| `security_info` | object | Birdeye API | Detailed security data | {...} |
| `concentration_analysis` | object | Calculated | Holder concentration metrics | {...} |
| `position_sizing_recommendation` | string | Calculated | Risk-based position sizing | "Conservative" |

---

## 📈 **Trading & Technical Analysis Data**

### **OHLCV Data (Multiple Timeframes)**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `ohlcv_1m` | array | Birdeye API | 1-minute candlestick data | [{"open": 0.041, "high": 0.042, ...}] |
| `ohlcv_5m` | array | Calculated | 5-minute aggregated data | [...] |
| `ohlcv_15m` | array | Calculated | 15-minute aggregated data | [...] |
| `ohlcv_1h` | array | Calculated | 1-hour aggregated data | [...] |

### **Trading Activity**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `recent_trades` | array | Birdeye API | Last 50 trades | [{"side": "buy", "amount": 1000, ...}] |
| `trade_metrics` | object | Birdeye API | Trading statistics | {"trend_dynamics_score": 0.75, ...} |
| `large_trades_24h` | number | Calculated | Number of trades >$10K | 15 |
| `buy_sell_ratio` | number | Calculated | 24h buy/sell ratio | 1.35 |

---

## 🐋 **Whale & Smart Money Analysis**

### **Whale Activity**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `whale_analysis` | object | Calculated | Whale activity summary | {...} |
| `net_whale_flow` | number | Calculated | Net whale inflow/outflow | 125000 |
| `large_buy_count` | number | Calculated | Large buy trades count | 8 |
| `whale_confidence` | string | Calculated | Whale activity confidence | "HIGH" |

### **Smart Money Tracking**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `has_smart_money` | boolean | Calculated | Smart money activity detected | true |
| `smart_money_activity` | object | Birdeye API | Smart money metrics | {...} |
| `top_traders` | array | Birdeye API | Top trader wallets | [{"wallet": "...", "volume": 50000}] |

---

## 🎯 **Scoring & Analysis Results**

### **Core Scores**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `token_score` | number | Calculated | Final composite score (0-100) | 82.0 |
| `score` | number | Calculated | Alias for token_score | 82.0 |

### **Component Scores**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `liquidity_score` | number | Calculated | Liquidity quality score | 85 |
| `volume_score` | number | Calculated | Trading volume score | 78 |
| `trend_score` | number | Calculated | Trend analysis score | 65 |
| `momentum_score` | number | Calculated | Price momentum score | 72 |
| `security_score` | number | Calculated | Security assessment score | 90 |
| `whale_score` | number | Calculated | Whale activity score | 80 |

### **Time-based Analysis**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `short_timeframe_analysis` | object | Calculated | 1-4h technical analysis | {...} |
| `medium_timeframe_analysis` | object | Calculated | 4-24h technical analysis | {...} |
| `long_timeframe_analysis` | object | Calculated | 1-7d technical analysis | {...} |

---

## ⏰ **Temporal & Meta Data**

### **Timestamps**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `creation_time` | number | Birdeye API | Token creation timestamp | 1642765432 |
| `analyzed_at` | number | System | Analysis timestamp | 1748359050 |
| `last_updated` | number | System | Last data update | 1748359050 |

### **Age Calculations**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `age_hours` | number | Calculated | Token age in hours | 24.5 |
| `age_days` | number | Calculated | Token age in days | 1.02 |
| `is_new_listing` | boolean | Calculated | New listing flag (<24h) | true |

---

## 📱 **Social & Community Data**

### **Social Media Presence**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `extensions.website` | string | Birdeye API | Official website | "https://..." |
| `extensions.twitter` | string | Birdeye API | Twitter/X handle | "https://twitter.com/..." |
| `extensions.telegram` | string | Birdeye API | Telegram group | "https://t.me/..." |
| `extensions.discord` | string | Birdeye API | Discord server | "https://discord.gg/..." |

### **Community Metrics**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `social_score` | number | Calculated | Social media activity score | 65 |
| `community_strength` | string | Calculated | Community assessment | "MODERATE" |

---

## 🔍 **Discovery & Strategy Data**

### **Discovery Metadata**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `discovery_source` | string | System | How token was discovered | "volume_surge" |
| `discovery_time` | number | System | When token was first found | 1748359000 |
| `scan_id` | string | System | Unique scan identifier | "scan_1748359000_001" |

### **Strategy Classification**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `strategic_coordination` | object | Calculated | Strategy-based analysis | {...} |
| `strategy_match` | array | Calculated | Matching strategies | ["volume_momentum", "new_listing"] |
| `priority_level` | string | Calculated | Discovery priority | "HIGH" |

---

## 📊 **Data Quality & Freshness**

### **Data Completeness**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `data_freshness` | object | System | Data source freshness | {...} |
| `data_quality` | string | System | Overall data quality | "complete" |
| `missing_fields` | array | System | List of missing data fields | [] |

### **API Response Metadata**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `api_response_time` | number | System | API response time (ms) | 3899 |
| `cache_status` | string | System | Cache hit/miss status | "fresh" |
| `error_count` | number | System | Number of API errors | 0 |

---

## 🚀 **Performance Tracking**

### **Forward Returns (Post-Discovery)**

| Field | Type | Source | Description | Example |
|-------|------|--------|-------------|---------|
| `return_1h` | number | Calculated | 1h return after discovery | 2.5 |
| `return_4h` | number | Calculated | 4h return after discovery | -1.2 |
| `return_24h` | number | Calculated | 24h return after discovery | 8.7 |
| `max_gain` | number | Calculated | Maximum gain achieved | 15.2 |
| `max_drawdown` | number | Calculated | Maximum drawdown | -3.8 |

---

## 📋 **Complete Example Token Object**

```json
{
  "token_name": "Bonk",
  "token_symbol": "BONK",
  "token_address": "85VBFQZC9TZkfaptBWjvUw7YbZjy52A6mjtPGjstQAmQ",
  "token_thumbnail": "https://img.fotofolio.xyz/?url=https%3A%2F%2Farweave.net%2FhQiPZOsRZXGXBJd_82PhVdlM_hACsT_q6wqwf5cSY7I",
  "link": "https://birdeye.so/token/85VBFQZC9TZkfaptBWjvUw7YbZjy52A6mjtPGjstQAmQ",
  "token_score": 82.0,
  "score": 82.0,
  "price_now": 0.00004177,
  "price_24h_ago": 0.00004058,
  "priceChange24h": 2.45,
  "priceChange4h": -1.23,
  "priceChange1h": 0.56,
  "liquidity": 125834567.89,
  "volume_24h": 2345678.90,
  "volume_4h": 892345.67,
  "volume_1h": 234567.12,
  "market_cap": 98765432.10,
  "fdv": 125834567.89,
  "is_scam": false,
  "is_risky": false,
  "security_info": {
    "security_score": 90,
    "risk_factors": []
  },
  "concentration_analysis": {
    "top_1_percent": 15.2,
    "top_5_percent": 35.8,
    "top_10_percent": 52.1,
    "concentration_risk": "MODERATE"
  },
  "position_sizing_recommendation": "Conservative",
  "holder_count": 654321,
  "top_holders": [
    {
      "owner": "3XLkRVg69AgwKAbnSjJpm3PB4QgVeXFEjiXfw5shWMBT",
      "percentage": 0.849,
      "amount": "785966502744984"
    }
  ],
  "unique_trader_count": 2890,
  "has_smart_money": true,
  "creation_time": 1642765432,
  "analyzed_at": 1748359050,
  "age_hours": 24.5,
  "short_timeframe_analysis": {
    "trend": "UPWARD",
    "momentum": "POSITIVE",
    "support_level": 0.000040,
    "resistance_level": 0.000045
  },
  "whale_analysis": {
    "net_flow": 125000,
    "large_trades": 8,
    "confidence": "HIGH"
  },
  "strategic_coordination": {
    "primary_strategy": "volume_momentum",
    "secondary_strategies": ["new_listing", "whale_accumulation"],
    "confidence": 85
  },
  "discovery_source": "volume_surge",
  "discovery_time": 1748359000,
  "scan_id": "scan_1748359000_001",
  "data_freshness": {
    "overview": "fresh",
    "price_data": "fresh",
    "trading_data": "fresh",
    "holders": "fresh",
    "security_data": "fresh"
  },
  "data_quality": "complete"
}
```

---

## 🔧 **Data Sources Summary**

| Data Source | Endpoint/Method | Update Frequency | Fields Provided |
|-------------|-----------------|------------------|-----------------|
| **Birdeye API - Overview** | `/defi/token_overview` | Real-time | Price, volume, liquidity, market cap, basic info |
| **Birdeye API - Holders** | `/defi/v3/token/holder` | ~5 minutes | Holder count, top holders, concentration |
| **Birdeye API - Security** | `/defi/token_security_check` | ~30 minutes | Security flags, risk assessment |
| **Birdeye API - Trades** | `/defi/v3/trades/token` | Real-time | Recent trades, trading patterns |
| **Birdeye API - OHLCV** | `/defi/ohlcv` | Real-time | Candlestick data, technical analysis |
| **System Calculations** | Internal | Real-time | Scores, analysis, derived metrics |
| **Cache System** | Internal | Variable | Optimized data delivery |

---

## 📝 **Usage Notes**

- **Data Freshness**: Most price and volume data is real-time or near real-time
- **Cache Strategy**: Data is cached with appropriate TTL to optimize API usage
- **Error Handling**: Missing or failed data is gracefully handled with defaults
- **Performance**: Data fetching is optimized with concurrent requests and batching
- **Validation**: All data goes through multiple validation layers before scoring 