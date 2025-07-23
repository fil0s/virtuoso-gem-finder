# 🎯 Platform Discovery Breakdown & Logic

## Overview
This document outlines the comprehensive token discovery system that analyzes tokens across **8 different platforms** to identify high-potential trading opportunities through cross-platform validation.

## 🏆 Top Multi-Platform Tokens (Sample Results)

| Rank | Symbol | Platforms | Total Score | Platform Names |
|------|--------|-----------|-------------|----------------|
| 1 | GOR | 4 | 22.18 | Birdeye-Stars, Meteora-Vol, Meteora-Vol, Meteora-Vol |
| 2 | WBTC | 4 | 14.16 | Birdeye-Trend, Birdeye-Stars, Meteora-Vol, Meteora-Vol |
| 3 | USELESS | 4 | 11.94 | Birdeye-Trend, Birdeye-Stars, Meteora-Vol, Meteora-Vol |
| 4 | JitoSOL | 4 | 10.17 | Birdeye-Stars, Meteora-Vol, Meteora-Vol, Jupiter-Quote |
| 5 | USDT | 3 | 16.4 | Birdeye-Stars, Meteora-Vol, Jupiter-Quote |

---

## 📊 Platform Categories & Discovery Logic

### 🚀 **1. DexScreener Platforms** (4 Different Endpoints)

#### **DexScreener-Boost** (`dexscreener_boosted`)
- **API Endpoint**: `/latest/dex/tokens/boosted`
- **Discovery Logic**: Fetches tokens with **paid promotional boosts**
- **Purpose**: Identifies tokens with marketing investment (indicates serious projects)
- **Symbol Extraction**: `baseToken.symbol` from pair data
- **Scoring Criteria**: Boost amount, volume, liquidity

#### **DexScreener-Top** (`dexscreener_top`)
- **API Endpoint**: `/latest/dex/tokens/boosted` + volume sorting
- **Discovery Logic**: Top **volume-ranked boosted tokens**
- **Purpose**: High-volume tokens with promotional backing
- **Symbol Extraction**: `baseToken.symbol` from pair data
- **Scoring Criteria**: 24h volume + boost metrics

#### **DexScreener-Prof** (`dexscreener_profiles`)
- **API Endpoint**: `/latest/dex/tokens/profiles`
- **Discovery Logic**: Tokens with **verified profiles** and social media presence
- **Purpose**: Tokens with established community/branding
- **Symbol Extraction**: `baseToken.symbol` from profile data
- **Scoring Criteria**: Profile completeness, social metrics

#### **DexScreener-Narr** (`dexscreener_narratives`)
- **API Endpoint**: `/latest/dex/search?q={narrative}`
- **Discovery Logic**: **Narrative-based search** for trending themes
- **Tracked Narratives**: ["AI", "agent", "pump", "meme", "dog", "cat", "pepe", "gaming", "DeFi"]
- **Purpose**: Captures tokens riding trending narratives
- **Symbol Extraction**: `baseToken.symbol` from search results
- **Scoring Criteria**: Search relevance + volume metrics

---

### 🔍 **2. RugCheck Platform**

#### **RugCheck** (`rugcheck_trending`)
- **API Endpoint**: `https://api.rugcheck.xyz/v1/tokens/{chain}/trending`
- **Discovery Logic**: **Community-voted trending tokens** with safety analysis
- **Purpose**: Community-validated tokens with safety scores
- **Symbol Extraction**: `symbol` field from RugCheck data
- **Scoring Criteria**: 
  - Vote count (up/down votes)
  - Sentiment score
  - Safety analysis results
  - Community engagement

---

### 🐦 **3. Birdeye Platforms** (2 Different Endpoints)

#### **Birdeye-Trend** (`birdeye_trending`)
- **API Endpoint**: `/defi/tokens/trending` or `/defi/v2/tokens/trending`
- **Discovery Logic**: **High-volume trending tokens** with price momentum
- **Purpose**: Tokens with significant trading activity
- **Symbol Extraction**: `symbol` field from Birdeye data
- **Scoring Metrics**:
  - 24h volume (USD)
  - Price change percentage
  - Liquidity depth
  - Market capitalization
  - Last trade timestamp

#### **Birdeye-Stars** (`birdeye_emerging_stars`)
- **API Endpoint**: `/defi/v3/token/list` with specific filters
- **Discovery Logic**: **Emerging tokens** with growth potential
- **Filters Applied**:
  - Minimum liquidity threshold
  - Minimum volume requirements
  - Minimum holder count
  - Minimum trade frequency
- **Purpose**: Early-stage tokens showing promise
- **Symbol Extraction**: `symbol` field from Birdeye data
- **Scoring Criteria**: Growth metrics + fundamental filters

---

### 🪐 **4. Jupiter Platform**

#### **Jupiter-Quote** (`jupiter_trending_quotes`)
- **API Endpoint**: `/quote` endpoint for individual tokens
- **Discovery Logic**: **Liquidity analysis** via quote requests
- **Analysis Performed**:
  - Route complexity assessment
  - Price impact calculation
  - Liquidity depth analysis
  - Tradability verification
- **Purpose**: Confirms actual tradability and liquidity
- **Symbol Extraction**: **None available** (only addresses) → Shows "Unknown"
- **Scoring Criteria**:
  - Liquidity score (1-10)
  - Activity score (1-10)
  - Route complexity (lower = better)
  - Price impact (lower = better)

---

### 🌊 **5. Meteora Platform**

#### **Meteora-Vol** (`meteora_trending_pools`)
- **API Endpoint**: `/pool/search?sort_by=volume_24h:desc`
- **Discovery Logic**: **High-volume AMM pools** sorted by 24h volume
- **Analysis Performed**:
  - Volume-to-Liquidity Ratio (VLR) calculation
  - Pool performance metrics
  - Fee generation analysis
- **Purpose**: Captures tokens with active AMM trading
- **Symbol Extraction**: **Pool name parsing** (e.g., "GOR-SOL" → "GOR")
- **Scoring Criteria**:
  - 24h volume
  - Total Value Locked (TVL)
  - Volume-to-Liquidity Ratio (VLR)
  - Fee generation (24h)

---

## 🎯 Cross-Platform Scoring Methodology

### **Scoring Algorithm**
1. **Individual Platform Scores**: Each platform assigns scores based on their specific metrics
2. **Score Aggregation**: Platform-specific scores are summed for total score
3. **Cross-Platform Bonus**: Tokens appearing on multiple platforms get validation bonus
4. **Quality Weighting**: Higher-quality platforms (Birdeye, Jupiter) carry more weight

### **Platform Score Ranges**
- **Meteora**: 0-10 (based on VLR, capped at 10)
- **Jupiter**: 0-10 (liquidity + activity scores)
- **Birdeye**: Variable (based on volume, price change, market metrics)
- **DexScreener**: Variable (based on boost amount, volume, narrative relevance)
- **RugCheck**: 0-10 (based on community votes and sentiment)

### **Multi-Platform Validation Benefits**
- **4+ Platforms**: Highest confidence (22+ total score possible)
- **3 Platforms**: High confidence (15+ total score typical)
- **2 Platforms**: Medium confidence (8-15 total score)
- **1 Platform**: Lower confidence (requires manual review)

---

## 🔍 Symbol Extraction Logic

### **Platform-Specific Symbol Sources**
| Platform | Symbol Source | Extraction Method |
|----------|---------------|-------------------|
| **Meteora** | Pool name | Parse "TOKEN-SOL" → "TOKEN" |
| **Jupiter** | None | Shows "Unknown" (address only) |
| **Birdeye** | API field | Direct `symbol` field |
| **DexScreener** | Pair data | `baseToken.symbol` |
| **RugCheck** | API field | Direct `symbol` field |

### **Symbol Priority Logic**
1. If token appears on multiple platforms, use first non-"Unknown" symbol found
2. Birdeye symbols generally most reliable
3. DexScreener symbols good for new/promoted tokens
4. Meteora symbols extracted from pool names
5. Jupiter provides no symbol data (liquidity analysis only)

---

## 📈 Platform Performance Insights

### **API Success Rates** (Sample Session)
- **DexScreener**: 12 calls, 100% success
- **RugCheck**: 1 call, 100% success  
- **Birdeye**: 33 calls, varies (authentication dependent)
- **Jupiter**: 15 calls, 100% success
- **Meteora**: 1 call, 100% success

### **Token Discovery Volume**
- **Jupiter Token List**: 287,863 total tokens (reference only)
- **Jupiter Quote Analysis**: 14 trending tokens
- **Meteora Pools**: 39 trending tokens
- **DexScreener Combined**: 88+ tokens across endpoints
- **Birdeye Combined**: Variable (authentication dependent)
- **RugCheck**: 10 trending tokens

---

## 🎯 Strategic Advantages

### **Why Cross-Platform Analysis Works**
1. **Validation**: Multiple sources confirm token legitimacy
2. **Diversification**: Different discovery methods catch different opportunities
3. **Quality Filtering**: Cross-platform presence indicates higher quality
4. **Risk Reduction**: Community validation + technical analysis
5. **Trend Identification**: Narrative tracking + volume analysis

### **Use Cases**
- **High-Conviction Trading**: 4+ platform tokens for safest bets
- **Emerging Opportunities**: 2-3 platform tokens for growth potential  
- **Narrative Plays**: DexScreener narrative discoveries
- **Liquidity Confirmation**: Jupiter quote analysis for execution
- **Community Sentiment**: RugCheck validation for social proof

---

## 🔧 Technical Implementation

### **Data Collection Flow**
1. **Parallel API Calls**: All platforms queried simultaneously
2. **Data Normalization**: Standardize token data across platforms
3. **Address Deduplication**: Merge tokens found on multiple platforms
4. **Score Calculation**: Apply platform-specific scoring algorithms
5. **Cross-Platform Analysis**: Identify overlaps and calculate combined scores
6. **Symbol Resolution**: Apply symbol extraction logic with fallbacks

### **Exclusion Filters**
- **Stablecoins**: USDC, USDT, DAI, BUSD, etc.
- **Wrapped Tokens**: WETH, WBTC, wSOL, etc.
- **Infrastructure Tokens**: Platform-specific utility tokens
- **Total Excluded**: 136+ addresses to focus on trading opportunities

---

## 📊 Output Format

### **Token Ranking Table**
```
| Rank | Symbol | Platforms | Address | Total Score | Platform Names |
|------|--------|-----------|---------|-------------|----------------|
| 1    | GOR    | 4         | 71Jvq... | 22.18      | Birdeye-Stars, Meteora-Vol, Meteora-Vol, Meteora-Vol |
```

### **Platform Statistics**
- Total platforms active
- Tokens per platform
- Cross-platform distribution
- API performance metrics
- Discovery insights and recommendations

---

## 🚀 Future Enhancements

### **Planned Improvements**
1. **Enhanced Symbol Resolution**: Jupiter token list integration for better symbols
2. **Real-time Scoring**: Dynamic score updates based on price movements  
3. **Social Sentiment**: Twitter/Telegram integration for social signals
4. **Technical Analysis**: Chart pattern recognition integration
5. **Portfolio Tracking**: Position monitoring for discovered tokens

### **Additional Platforms**
- **Pump.fun**: Meme token discovery
- **Raydium**: DEX-specific trending analysis
- **Magic Eden**: NFT-related token discovery
- **Solscan**: On-chain activity analysis

---

*Last Updated: June 2025*
*System Version: Jupiter + Meteora Integration v2.0* 