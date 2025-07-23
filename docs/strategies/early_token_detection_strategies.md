# Early Token Detection Strategies with Birdeye Analytics

> **Purpose:**
> This document outlines quantitative, systematic strategies for catching promising tokens early using Birdeye API analytics. Each strategy is explained with theory, data requirements, and practical implementation steps. The final section describes how to combine these signals into an automated alerting/trading system.

---

## Table of Contents
1. [Overview](#overview)
2. [Data Sources & Example Fields](#data-sources--example-fields)
3. [Gem Score Calculation (Current Implementation)](#gem-score-calculation-current-implementation)
4. [New Birdeye Endpoints & Their Role](#new-birdeye-endpoints--their-role)
5. [Strategy 1: Early Holder Accumulation (Smart Money Tracking)](#strategy-1-early-holder-accumulation-smart-money-tracking)
6. [Strategy 2: Liquidity and Volume Surge Detection](#strategy-2-liquidity-and-volume-surge-detection)
7. [Strategy 3: New Listing and First Trade Analysis](#strategy-3-new-listing-and-first-trade-analysis)
8. [Strategy 4: Wallet Clustering and Social Proof](#strategy-4-wallet-clustering-and-social-proof)
9. [Strategy 5: Price Action and Volatility Breakouts](#strategy-5-price-action-and-volatility-breakouts)
10. [Strategy 6: On-Chain Social/Community Signals](#strategy-6-on-chain-socialcommunity-signals)
11. [Strategy 7: Wallet Flow Analytics & On-Chain Event Triggers](#strategy-7-wallet-flow-analytics--on-chain-event-triggers)
12. [Combining Signals for an Alerting/Trading System](#combining-signals-for-an-alertingtrading-system)
13. [Risk Management & Cautions](#risk-management--cautions)
14. [Operationalizing & Tuning the Pipeline](#operationalizing--tuning-the-pipeline)
15. [NEW: Adaptive, Quant-Driven, API-Efficient Monitoring Loop](#new-adaptive-quant-driven-api-efficient-monitoring-loop)
16. [References](#references)

---

## Overview

Catching tokens early—before they experience major price moves or become widely known—requires a blend of on-chain analytics, wallet behavior tracking, and market microstructure awareness. Birdeye's API suite provides real-time and historical data to systematically identify such opportunities.

---

## Data Sources & Example Fields

**Key Birdeye Endpoints:**
- `/defi/token_trending` — Trending tokens by volume/liquidity
- `/defi/token_security` — Security risk/scam flags for tokens
- `/defi/v3/token/list` — Full token list with sort/filter options. Current core filters:
    - `min_liquidity`
    - `min_volume_1h_usd`
    - `min_volume_24h_usd`
    - `min_holder`
    - `min_trade_24h_count`
    - `sort_by: 'recent_listing_time'` (descending)
- `/defi/v3/token/holder` — Top holders and concentration
- `/defi/token_creation_info` — Token creation time and creator
- `/defi/token_overview` — Token stats (liquidity, volume, price, etc.)
- `/defi/historical_price_unix` — Historical price at a given timestamp
- `/defi/v2/tokens/top_traders` — **Top active wallets for a token** *(NEW: used for clustering, smart money overlap, and behavioral scoring)*
- `/defi/v2/tokens/new_listing` — **Newly listed tokens** *(NEW: used for new listing bonus and discovery)*
- `/v1/wallet/token_list` — **Wallet portfolio holdings** *(NEW: available for advanced wallet clustering, not yet scored)*
- `/trader/gainers-losers` — **Top traders by PnL, volume, trade count** *(NEW: used to build smart money list for overlap bonus)*

**Example Data Fields:**
- Token: `address`, `symbol`, `name`, `liquidity`, `v24hUSD`, `recent_listing_time`, `marketcap`, `price`, `holder`, `totalSupply`
- Wallet: `owner`, `volume`, `trade`, `token holdings` (list of tokens, balances, USD value)
- Trade: `txHash`, `timestamp`, `amount`, `price`, `buyer/seller`

---

## Gem Score Calculation (Current Implementation)

The **gem score** is a composite, weighted metric designed to quantify the attractiveness and quality of a newly discovered token. It is calculated as a weighted sum of several quantitative and behavioral factors, each normalized to a 0–100 scale, and then combined using configurable weights.

### **Scoring Formula (Production Logic)**

```python
# Pseudocode for the current gem score calculation
score = 0
# Liquidity (log scaling, reduced penalty for new tokens)
if listing_age_hours is not None and listing_age_hours < 6:
    liquidity_penalty = -3 if liquidity < 5000 else 0  # Reduced penalty for new tokens
else:
    liquidity_penalty = -10 if liquidity < 5000 else 0
liquidity_score = np.log10(liquidity + 1) / 6 * 100 if liquidity > 0 else 0
score += weights['liquidity'] * liquidity_score + liquidity_penalty
# Age (bonus for very new tokens, no penalty for being too new)
age_score = 0
if age_hours is not None:
    if 2 <= age_hours <= 24:
        age_score = 100
    elif 0.5 <= age_hours < 2:
        age_score = 50
    elif age_hours > 24:
        age_score = 25
    elif age_hours < 0.5:
        age_score = 75  # Small bonus for being extremely new
score += weights['age'] * age_score
# Concentration (Gini penalty)
concentration_score = max(0, 100 - top1) * (1 - gini_concentration)
score += weights['concentration'] * concentration_score
# Price Change
score += weights['price_change'] * price_score
# Volume (log scaling)
volume_score = np.log10(volume_24h + 1) / 6 * 100 if volume_24h > 0 else 0
score += weights['volume'] * volume_score
# Momentum (advanced analytics)
score += weights['momentum'] * momentum_score
# Behavioral
score += weights['behavioral'] * behavioral_score
# Security penalty
if is_scam:
    score -= 30
elif is_risky:
    score -= 10
# Advanced analytics bonuses
if address in trending_tokens:
    score += 10  # Trending bonus
if address in new_listing_addresses:
    score += 10  # New listing bonus
if smart_money_share > 0.2:
    score += min(20, smart_money_share * 100)  # Smart money bonus (proportional)
if recent_whale_buys >= 2:
    score += 5 * recent_whale_buys  # Clustering bonus
if volatility > 0.05:
    score += 10  # Volatility bonus
if momentum > 0.10:
    score += 10  # Momentum bonus
elif momentum > 0.05:
    score += 5
score = min(max(score, 0), 100)
```

### **Factor Details (Production Logic)**

| Factor           | Birdeye Data Source         | Normalization/Logic                                  | Notes                                  |
|------------------|----------------------------|------------------------------------------------------|----------------------------------------|
| Liquidity        | `/defi/token_overview`     | log10(liquidity+1)/6 * 100, reduced penalty for <6h  | Log scaling, reduced penalty for new   |
| Age              | `/defi/token_creation_info` | 2–24h: 100, 0.5–2h: 50, >24h: 25, <0.5h: 75         | Favors new, small bonus for <0.5h      |
| Concentration    | `/defi/v3/token/holder`    | Gini coefficient, penalizes centralization           | More decentralized = higher score      |
| Price Change     | `/defi/historical_price_unix` | 0–200%: 100, 200–1000%: 50, -50–0%: 50              | Favors healthy appreciation            |
| Volume           | `/defi/token_overview`     | log10(volume_24h+1)/6 * 100                          | Log scaling                            |
| Momentum         | `/defi/token_overview`, OHLCV | Advanced: 1m/5m window, % change, bonus for >10%    | Short-term price action, robust        |
| Behavioral       | `/defi/token_overview`     | Churn, tx/wallet, buy/sell ratio                    | Penalizes suspicious activity          |
| Security Penalty | `/defi/token_security`     | -30 if scam, -10 if risky                           | Hard penalty for flagged tokens        |
| Trending Bonus   | `/defi/token_trending`     | +10 if token is trending                            | Bonus for trending tokens              |
| New Listing Bonus| `/defi/v2/tokens/new_listing` | +10 if token is newly listed                        | Bonus for new listings                 |
| Smart Money Bonus| `/trader/gainers-losers`, `/defi/v2/tokens/top_traders` | + up to 20, proportional to share     | Smart money overlap, proportional      |
| Clustering Bonus | `/defi/v2/tokens/top_traders` | +5 per whale (min 2 whales)                        | Wallet clustering                      |
| Volatility Bonus | OHLCV endpoints            | +10 if 1h stddev >5%                                | Healthy volatility                     |
| Momentum Bonus   | OHLCV endpoints            | +10 if 15m momentum >10%, +5 if >5%                 | Short-term momentum                    |

- **All weights and thresholds are configurable via config.**
- **ML/dynamic weighting is not yet implemented.**

### **Rationale and Best Practices (Production)**
- **Do not over-penalize new tokens:** Reduced liquidity penalty and age score bonus ensure high-upside early opportunities are not missed due to natural early-stage characteristics.
- **Advanced analytics:** Trending, new listing, smart money, clustering, volatility, and momentum bonuses are integrated for a robust, multi-factor approach.
- **Backtesting and tuning:** Regularly backtest and tune weights/thresholds to optimize for your risk appetite and market regime.
- **Configurable and extensible:** All logic is configurable and can be extended as new data sources or strategies become available.
- **References to production code:** See `services/early_token_detection.py` for implementation and `config/` for weights/thresholds.

### **References**
- [Birdeye Top Traders API](https://docs.birdeye.so/reference/get-defi-v2-tokens-top_traders)
- [Birdeye Token Trending API](https://docs.birdeye.so/reference/get-defi-token-trending)
- [Birdeye Wallet Portfolio API](https://docs.birdeye.so/reference/get-v1-wallet-token_list)
- [Birdeye New Listing API](https://docs.birdeye.so/reference/get-defi-v2-tokens-new_listing)
- [Birdeye API Documentation](https://docs.birdeye.so/)
- [Production scoring logic and adaptive monitoring](../services/early_token_detection.py)
- [Configuration and weights](../config/)

---

> **For further implementation help or code templates, contact the quant/dev team.**

### **Gini Coefficient for Concentration**
- The Gini coefficient is calculated on the holder percentage list to measure decentralization.
- Formula:
  ```python
  def gini(array):
      array = np.array(array)
      if np.amin(array) < 0:
          array -= np.amin(array)
      array += 1e-8
      array = np.sort(array)
      index = np.arange(1, array.shape[0] + 1)
      n = array.shape[0]
      return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))
  ```
- The concentration score is scaled by (1 - Gini), so more decentralized tokens are rewarded.

### **Security, Trending, and New Endpoint Integration**
- `/defi/token_security` is called for each token. If `is_scam` is `True`, the score is penalized by -30. If `is_risky` is `True`, penalized by -10.
- `/defi/token_trending` is called once per scan. If a token is in the trending list, it receives a +10 bonus.
- `/defi/v2/tokens/new_listing` is called to supplement discovery and for a +10 bonus if the token is newly listed.
- `/defi/v2/tokens/top_traders` is called for each token to:
    - Count unique top traders (clustering bonus)
    - Check overlap with smart money wallets (from `/trader/gainers-losers`) for a +10 bonus if >20% overlap
- `/trader/gainers-losers` is called to build the smart money wallet list (top PnL, volume, or trade count wallets).
- `/v1/wallet/token_list` is available for advanced wallet clustering and portfolio analysis (not yet scored, but available for future features).

### **Log Scaling**
- Both liquidity and volume use log scaling to prevent large tokens from dominating the score and to give small but growing tokens a fair chance.

---

## New Birdeye Endpoints & Their Role

**Recently Integrated Endpoints:**
- `/defi/v2/tokens/top_traders`: Used to identify top active wallets for a token. Enables wallet clustering, smart money overlap, and behavioral scoring.
- `/defi/v2/tokens/new_listing`: Used to supplement token discovery and to add a new listing bonus (+10) to the gem score.
- `/v1/wallet/token_list`: Used for wallet portfolio analysis and advanced clustering (future feature).
- `/trader/gainers-losers`: Used to build a list of "smart money" wallets (top PnL, volume, or trade count) for overlap analysis and bonus scoring.

**How They Impact Detection:**
- **Smart Money Overlap:** If >20% of a token's top traders are in the smart money list, the token gets a +10 bonus.
- **Clustering Bonus:** If a token has more than 5 unique top traders, it gets a +5 bonus.
- **New Listing Bonus:** If a token is in the new listings endpoint, it gets a +10 bonus.
- **Portfolio Analysis:** The wallet portfolio endpoint is available for future features such as advanced wallet clustering and social proof.

**Summary Table of All Factors and Birdeye Data Sources:**

| Factor                | Birdeye Endpoint(s)                        | Scoring Logic/Bonus                |
|-----------------------|--------------------------------------------|------------------------------------|
| Liquidity             | `/defi/token_overview`                     | Log scaling                        |
| Age                   | `/defi/token_creation_info`                | Age buckets                        |
| Concentration         | `/defi/v3/token/holder`                    | Gini coefficient                   |
| Price Change          | `/defi/historical_price_unix`              | Price change buckets               |
| Volume                | `/defi/token_overview`                     | Log scaling                        |
| Momentum              | `/defi/token_overview`                     | Acceleration                       |
| Behavioral            | `/defi/token_overview`                     | Churn, tx/wallet, buy/sell ratio   |
| Security Penalty      | `/defi/token_security`                     | -30/-10 for scam/risky             |
| Trending Bonus        | `/defi/token_trending`                     | +10 if trending                    |
| New Listing Bonus     | `/defi/v2/tokens/new_listing`              | +10 if newly listed                |
| Smart Money Bonus     | `/trader/gainers-losers`, `/defi/v2/tokens/top_traders` | +10 if >20% overlap                |
| Clustering Bonus      | `/defi/v2/tokens/top_traders`              | +5 if >5 unique top traders        |
| Portfolio Analysis    | `/v1/wallet/token_list`                    | (future: advanced clustering)      |

---

## Strategy 1: Early Holder Accumulation (Smart Money Tracking)

**Theory:**
- "Smart money" wallets (profitable, early adopters) often accumulate new tokens before major price moves.
- Tracking their activity can provide early signals of promising tokens.

**Data Needed:**
- `/trader/gainers-losers` to identify profitable wallets
- `/defi/v2/tokens/top_traders` to see which wallets are accumulating new tokens
- `/v1/wallet/token_list` to monitor wallet holdings

**Implementation Steps:**
1. Build a list of "smart money" wallets (e.g., top PnL or volume from `/trader/gainers-losers`).
2. For each new or trending token, check if these wallets are accumulating positions (via `/defi/v2/tokens/top_traders`).
3. If multiple smart wallets accumulate a new token within a short window, flag it for further analysis or alert.

**Practical Note:**
- See `test_discover_and_analyze_new_tokens` for how top holders and wallet flows are now tracked and snapshotted for each token.

---

## Strategy 2: Liquidity and Volume Surge Detection

**Theory:**
- Sudden increases in liquidity and volume often precede price discovery and broader adoption.

**Data Needed:**
- `/defi/v3/token/list` with appropriate filters (see above) and sorting by `recent_listing_time`.
- Python-side filtering for token age (e.g., must be at least `MIN_TOKEN_AGE_MINUTES` old AND listed within the last 24 hours).

**Implementation Steps:**
1. Query Birdeye `/defi/v3/token/list` sorting by `recent_listing_time` (desc) and filtering by `min_liquidity`, `min_volume_1h_usd`, `min_volume_24h_usd`, `min_holder`, `min_trade_24h_count`.
2. In Python, further filter the returned tokens to ensure they meet `MIN_TOKEN_AGE_MINUTES` and were listed within the last 24 hours.
3. Monitor these tokens for significant surges in their existing liquidity/volume or if they newly meet higher thresholds.
4. Flag tokens that exhibit these characteristics.

**Practical Note:**
- The codebase uses server-side filtering (as described in step 1) and client-side Python age filtering (step 2) to create a candidate list. Momentum analytics (volume/tx acceleration) are then applied to this list.

---

## Strategy 3: New Listing and First Trade Analysis

**Theory:**
- Tokens that attract immediate, aggressive trading interest are more likely to experience momentum.

**Data Needed:**
- `/defi/v3/token/list` (sorted by `recent_listing_time` and filtered as above) to identify new tokens.
- `/defi/txs/token/seek_by_time` (or equivalent trade history endpoint) for first trades.

**Implementation Steps:**
1. Utilize the primary `/defi/v3/token/list` query (sorted by newness and filtered for activity/liquidity) to get candidate tokens.
2. Apply the Python-side age filter (min age and max 24-hour window).
3. For tokens passing these filters, analyze their early trade history (first N trades) for large buys or clustering by active wallets.
4. Flag tokens with strong early trade activity.

**Practical Note:**
- The pipeline can be extended to fetch and analyze first trades for new listings as a future enhancement.

---

## Strategy 4: Wallet Clustering and Social Proof

**Theory:**
- Distributed early accumulation (many unique wallets) is a stronger signal than single-wallet activity.

**Data Needed:**
- `/defi/v2/tokens/top_traders` for unique wallet count

**Implementation Steps:**
1. For each new token, count unique active wallets accumulating in the first 24h.
2. Set a threshold (e.g., >10 unique wallets with >$X in holdings).
3. Flag tokens with broad early adoption.

**Practical Note:**
- The codebase computes wallet churn and unique wallet counts for behavioral analytics and risk scoring.

---

## Strategy 5: Price Action and Volatility Breakouts

**Theory:**
- Price breakouts with volume and wallet support are strong signals of trend initiation.

**Data Needed:**
- `/defi/historical_price_unix` and OHLCV endpoints for price/volatility
- `/defi/v2/tokens/top_traders` for wallet support

**Implementation Steps:**
1. Compute price volatility and detect breakouts above initial listing price.
2. Confirm with increasing volume and wallet participation.
3. Flag tokens meeting all criteria.

**Practical Note:**
- The pipeline generates price charts and computes price change/volatility for each token, integrating this into the scoring and alerting system.

---

## Strategy 6: On-Chain Social/Community Signals

**Theory:**
- Tokens with both on-chain and off-chain (social) momentum are more likely to sustain early moves.

**Data Needed:**
- On-chain: All above endpoints
- Off-chain: Twitter, Telegram, Discord, etc. (via scraping or APIs)

**Implementation Steps:**
1. Track token mentions and community growth off-chain.
2. Correlate social spikes with on-chain wallet accumulation and volume surges.
3. Flag tokens with both types of momentum.

**Practical Note:**
- The current codebase is ready to integrate off-chain signals for future hybrid analytics.

---

## Strategy 7: Wallet Flow Analytics & On-Chain Event Triggers

**Theory:**
- Real-time wallet flow and on-chain event monitoring can detect manipulation, bot-driven pumps, or organic accumulation before price moves.

**Data Needed:**
- `/defi/v3/token/holder` for top holders and concentration
- `/defi/token_overview` for supply, volume, and trade data
- `/defi/token_creation_info` for age
- `/defi/historical_price_unix` for price history

**Implementation Steps:**
1. For each token, snapshot top holders and compare to previous run (see `temp/analyze_wallet_cache/`).
2. Compute wallet churn (new wallets in top holders), large inflows/outflows (change in holdings), and concentration shifts.
3. Detect on-chain event triggers: sudden whale inflow/outflow, high churn, or bot-like activity (high tx per wallet).
4. Integrate these analytics into the scoring and risk flagging system.

**Practical Note:**
- The codebase implements these utilities and integrates them into the main detection and alerting pipeline.

---

## Combining Signals for an Alerting/Trading System

**Theory:**
- Combining multiple independent signals increases robustness and reduces false positives.

**Implementation Steps:**
1. Implement each strategy as a separate signal generator.
2. For each new token, score or flag based on how many signals are triggered.
3. Set an alert or execute a trade when a token meets a minimum number of signals (e.g., 3 out of 5).
4. Optionally, weight signals by historical predictive power.

**Practical Note:**
- The codebase uses a configurable, weighted scoring system (see `SCORING_WEIGHTS` in `test_birdeye_api.py`).
- Alerts are sent via Telegram with detailed context, risk explanations, and price charts.

---

## Risk Management & Cautions
- **Rug Pull/Scam Detection:** Always check for contract audits, blacklists, and abnormal holder distributions.
- **Liquidity Traps:** Avoid tokens with low or rapidly withdrawn liquidity, even if wallet activity is high.
- **Slippage and Gas:** Factor in transaction costs and slippage, especially for new or illiquid tokens.
- **Backtest:** Always backtest strategies on historical data before live deployment.
- **Bot/Manipulation Detection:** Use wallet churn, tx per wallet, and large inflow/outflow analytics to flag suspicious activity.

---

## Operationalizing & Tuning the Pipeline

**Configurable Weights & Thresholds:**
- All scoring metrics (liquidity, age, concentration, price change, volume, momentum, behavioral) are configurable via environment variables or a config dict.
- Tune these weights based on your risk appetite and backtesting results.

**Alerting & Monitoring:**
- Alerts are sent to Telegram with:
  - Token details, price, liquidity, volume, holders
  - Risk flags and explanations
  - Price chart (24h)
  - Links to Birdeye, DexScreener, Solscan
  - Wallet flow analytics (churn, inflow/outflow)

**Productionization:**
- Run the pipeline on a schedule (e.g., every 5-10 minutes) for real-time detection.
- Store snapshots and analytics for backtesting and continuous improvement.
- Integrate off-chain/social signals for even higher conviction.

### NEW: Adaptive, Quant-Driven, API-Efficient Monitoring Loop

**Purpose:**  
To maximize detection quality while minimizing API usage and rate limit risk, the pipeline now uses an adaptive, event-driven polling loop with state caching and change detection.

---

#### Key Features

- **Token State Caching:**  
  The system maintains a cache of last-seen state for each token (holders, volume, liquidity, etc.).
  Only tokens with significant state changes (e.g., new holders, volume/liquidity surges) are re-analyzed in each cycle.

- **Adaptive Polling Interval:**  
  The polling interval dynamically adjusts based on observed market activity:
    - **More frequent (5 min):** When new tokens or significant changes are detected.
    - **Less frequent (up to 30 min):** When the market is quiet or no changes are detected for several cycles.
  On API errors or rate limits, the interval increases (backoff) to avoid further issues.

- **API Call Throttling & Deduplication:**  
  Expensive analytics (e.g., whale wallet analysis) are only performed for tokens with changed state.
  Whale wallet analytics are cached with a TTL to avoid redundant calls.

- **Change Detection:**  
  The system compares the current state of each token to its cached state.
  Only tokens with meaningful changes are flagged for full analysis and alerting.

- **Continuous, Robust Monitoring:**  
  The main loop runs continuously until interrupted, providing real-time detection with minimal wasted computation or API usage.

---

#### Quantitative Rationale

- **Event-driven polling** ensures that API calls are made only when there is a high probability of actionable information, reducing noise and cost.
- **Adaptive intervals** allow the system to respond quickly to bursts of activity (e.g., new launches, volume spikes) while conserving resources during quiet periods.
- **State caching and deduplication** prevent redundant analysis and focus computational effort on the most promising opportunities.
- **Backoff on errors** ensures system stability and compliance with API rate limits.

---

#### Implementation Summary

- See `TokenStateCache` in `services/early_token_detection.py` for the in-memory state tracking logic.
- The main loop (`main_loop()`) dynamically adjusts its sleep interval and only analyzes tokens with changed state.
- Whale wallet and behavioral analytics are throttled and cached.
- All logic is fully asynchronous and production-ready.

---

#### Best Practices

- **Batch API requests** where possible to further reduce latency and rate limit risk.
- **Persist the token state cache** to disk or a database for even greater efficiency and resilience (future enhancement).
- **Monitor and tune** the adaptive interval parameters based on real-world usage and backtesting results.

---

#### Sample Pseudocode

```python
while True:
    tokens = discover_new_tokens()
    changed_tokens = [t for t in tokens if state_changed(t)]
    for token in changed_tokens:
        analyze_token(token)
    adjust_interval_based_on_activity()
    sleep(interval)
```

---

#### References

- See `services/early_token_detection.py` for the latest implementation.
- For further enhancements, consider persistent caching and distributed event-driven architectures.

**This adaptive, quant-driven approach is now live in the codebase and is recommended for all production deployments.**

---

## References
- [Birdeye Top Traders API](https://docs.birdeye.so/reference/get-defi-v2-tokens-top_traders)
- [Birdeye Token Trending API](https://docs.birdeye.so/reference/get-defi-token-trending)
- [Birdeye Wallet Portfolio API](https://docs.birdeye.so/reference/get-v1-wallet-token_list)
- [Birdeye New Listing API](https://docs.birdeye.so/reference/get-defi-v2-tokens-new_listing)
- [Birdeye API Documentation](https://docs.birdeye.so/)
- [Wallet Flow Analytics Utilities & Alerting Enhancements](../scripts/test_birdeye_api.py)

---

> **For further implementation help or code templates, contact the quant/dev team.**

**Short-Term Volatility & Momentum Scoring (1m & 5m Windows)**

- For each token, fetch both 1-minute and 5-minute OHLCV candles (base=token, quote=USDC).
- Compute volatility as the coefficient of variation (std/mean) of the last 5 closes for each window.
- Compute momentum as the % change from first to last close in each window.
- Score both volatility and momentum for each window:
  - Volatility: 100 (optimal) for 0.01–0.10, 60 for 0.10–0.20, 30 for 0.20–0.40, 0 otherwise.
  - Momentum: 100 for >5%, 60 for >2%, 30 for >0%, 0 otherwise.
- **Average the 1m and 5m scores** for final volatility and momentum scores, for robustness against noise.
- Integrate these averaged scores into the gem score (momentum and behavioral factors).

**Rationale:**
- Combining 1m and 5m windows smooths out noise and captures both micro and short-term price action.
- Penalizes both illiquid and manipulated launches, rewards healthy price discovery.

**Thresholds:**
- Volatility optimal: 0.01–0.10 (healthy), penalize outside this range.
- Momentum optimal: >5% up in window, moderate for 2–5%, mild for 0–2%.

**Integration:**
- Both scores are averaged and included in the overall scoring logic, as part of "momentum" and "behavioral" weights.

**Best Practices:**
- Always check for data availability and handle missing data gracefully.
- Batch requests where possible to reduce rate limits and latency.
- Combine price with other early signals (liquidity, volume, holders, smart money) for robust scoring.

**This approach is now implemented in the codebase.**

> **For further implementation help or code templates, contact the quant/dev team.** 