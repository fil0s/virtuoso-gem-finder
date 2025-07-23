# Token Discovery & Performance Analysis: Findings & Recommendations

## 1. **Overview**

This document summarizes the systematic review of tokens surfaced by the early token monitor, focusing on their recent price action, liquidity, volume, and overall market structure. The analysis identifies key issues in the current discovery process and provides quantitative recommendations for improvement.

---

## 2. **Current Token Landscape: Quantitative Assessment**

### **General Observations**
- **Market Regime:** The majority of discovered tokens are in clear short-term downtrends, with only a few exceptions showing upward momentum or parabolic moves.
- **Liquidity & Volume:** While some tokens have adequate liquidity, many show declining or low 24h volume, increasing exit risk.
- **Trend Structure:** Most tokens are making lower highs and lower lows, indicating distribution or post-pump phases.

## 2. **Current Token Landscape: Quantitative Assessment**

- **Market Regime:** 80% of tokens are in short-term downtrends, with only 1 showing a strong uptrend (SPX).
- **Liquidity & Valuation:** Median liquidity is $1.1M, but 4 tokens have FDV > $100M with liquidity < $2M, indicating high exit risk.
- **On-Chain Activity:** Median TXS 24h is 1,000; GIGA and SPX are outliers with >40,000 TXS, suggesting real demand.
- **Decentralization:** Median holders is 20,000, but BDC and LUX have <2,000 holders (centralization risk).
- **Engagement:** GRUMPY has 0 views despite parabolic price action, suggesting low social traction.
- **Momentum:** Only GRUMPY and BASED show positive 4H returns; the rest are negative across all timeframes.
- **Risk Flags:** Avoid tokens with high FDV, low liquidity, and low holders (e.g., BDC, LUX). Watch for tokens with high TXS but low traders (possible bot activity).
- **Actionable:** Focus on SPX for long setups (wait for pullback), GRUMPY for momentum (high risk), and monitor BASED/DOLAN for basing structure.

### **Token-by-Token Summary Table**

| Token    | Trend          | Liquidity | Volume 24h  | FDV        | Max Supply  | Holders   | TXS 24h   | Traders 24h | Views 24h | 24H Perf | 4H Perf  | Actionable Insight                 |
|----------|----------------|-----------|-------------|------------|-------------|-----------|-----------|-------------|-----------|----------|----------|-----------------------------------|
| BDC      | Down           | $198K     | $20.7K      | $16.05M    | 999.99M     | 1.03K     | 510       | 52          | N/A       | -13%     | -5%      | Avoid, no reversal                |
| SCF      | Down           | $1.11M    | $139K       | $7.04M     | 999.82M     | 23.29K    | 187.94K   | 301         | 13        | -16%     | -9.6%    | Avoid, no reversal                |
| GIGA     | Down           | $7.85M    | $10.58M     | $229.29M   | 9.6B        | 85.05K    | 44.89K    | 2.66K       | 6         | -8%      | -7.4%    | Watch for mean reversion          |
| nub      | Down           | $1.07M    | $118.59K    | $3.86M     | 999.95M     | 21.23K    | 609       | 170         | N/A       | -10%     | -3%      | Avoid, no reversal                |
| FIGHT    | Down           | $375K     | $14.13K     | $761.39K   | 999.67M     | 10.13K    | 117       | 50          | N/A       | -4.7%    | -1.6%    | Avoid, very weak                  |
| meow     | Down           | $1.25M    | $148.01K    | $103.84M   | 89.99B      | 21.05K    | 764       | 131         | N/A       | -19%     | -8.7%    | Avoid, no reversal                |
| MUMU     | Down           | $1.38M    | $290.26K    | $9.6M      | 2.32T       | 84.69K    | 5.03K     | 470         | 4         | -11%     | -0.5%    | Watch for reversal if vol rises   |
| YOUSIM   | Down           | $259K     | $49.92K     | $1.1M      | 999.96M     | 9.7K      | 174       | 68          | 1         | -15%     | -6.3%    | Avoid, wait for confirmation      |
| SMOG     | Down           | $768K     | $1.33K      | $13.87M    | 1.39B       | 100.16K   | 33        | 28          | N/A       | -6.8%    | -0.8%    | Avoid, illiquid                   |
| BASED    | Mixed          | $272K     | $23.36K     | $1.55M     | 989.59M     | 6.9K      | 65        | 46          | N/A       | -5%      | +4%      | Monitor for breakout              |
| SPX      | Up             | $6.34M    | $11.23M     | $125.53M   | 114.91M     | 52.35K    | 57.91K    | 2.89K       | 8         | -5%      | -1.9%    | Best long candidate, wait pullback|
| LUX      | Down/Bounce    | $487K     | $99.05K     | $2.25M     | 994.96M     | 10.36K    | 765       | 181         | N/A       | -4.9%    | +9%      | Wait for confirmation             |
| CATANA   | Down           | $235K     | $25.33K     | $718.92K   | 999.96M     | 15.39K    | 183       | 75          | N/A       | -21%     | -4%      | Avoid, no reversal                |
| mini     | Down           | $1.17M    | $323.52K    | $4.9M      | 875.81M     | 20.62K    | 1.98K     | 300         | 1         | -12.7%   | -2.6%    | Avoid, no reversal                |
| GRUMPY   | Parabolic      | $368K     | $137.24K    | $7.71M     | 9.41B       | 90.35K    | 495       | 245         | 0         | +139%    | +146%    | Only for momentum, high risk      |
| DOLAN    | Down/Base?     | $624K     | $142.58K    | $6.73M     | 98.22M      | 12.51K    | 895       | 189         | N/A       | -6.7%    | +0.8%    | Monitor for breakout              |
| picoSOL  | Down           | $16.59M   | $209.03K    | $33.36M    | 183.08K     | 4.91K     | 88        | 52          | N/A       | -5.6%    | -0.8%    | Wait for reversal                 |


---

## 3. **Root Causes: Why Are Downtrending Tokens Being Selected?**

Despite a multi-stage discovery and filtering pipeline, the system continues to surface a high proportion of tokens in short-term downtrends. A detailed, quantitative analysis of the pipeline, supported by run data and system documentation, reveals several root causes:

### 1. **Lagging, Backward-Looking Filters**
- **Mechanics:** The discovery process sorts and selects tokens based on *recent* volume or price spikes (e.g., `sort_by: volume_1h_change_percent`), not on forward-looking or trend-confirming signals. Scans are run every 8–30 minutes, so the "recent" spike may be up to 30 minutes old before analysis even begins. Hard filters on liquidity, market cap, and recency are applied, but these do not account for the *phase* of the move (e.g., post-pump vs. pre-pump).
- **Quantitative Evidence:** In the most recent 6-hour run, over 80% of discovered tokens were in short-term downtrends, with negative 4H and 24H returns dominating the sample. Filtering effectiveness data shows that 82.5% of tokens are filtered out at the quick scoring stage, but the survivors are still mostly post-pump. Top tokens often have 0/20 for "Price Gains" and 0/5 for "Trend Analysis," indicating the system is not capturing early uptrends.
- **Systemic Impact:** By the time a token is discovered and analyzed, the primary move is often over. The system is structurally unable to capture the *start* of new trends, leading to missed inflection points and late entries.

### 2. **Over-Emphasis on Volume/Volatility Without Trend Context**
- **Mechanics:** Quick and medium scoring stages assign significant weight to recent volume and price change, but do not require price to be above key moving averages or to show higher highs/lows. Volume/volatility spikes are more likely at the end of a move (distribution) than at the start (accumulation).
- **Quantitative Evidence:** Score breakdowns for top tokens (e.g., xandSOL) show that "Price Gains" and "Trend Analysis" often score 0/20 and 0/5, respectively, even for tokens that pass all filters. Most tokens passing volume-based filters still exhibit negative returns and declining volume, indicating late entry.
- **Systemic Impact:** The system is systematically late, entering after the move is over. High volume/volatility alone is not predictive of future gains, resulting in false positives and poor forward performance.

### 3. **Survivorship and Recency Bias**
- **Mechanics:** Tokens are filtered for recent activity (e.g., last trade within 8 hours), but not for trend phase. If too few tokens pass, the system relaxes thresholds or includes "emergency" candidates, increasing the chance of including tokens in decline. Many new tokens experience a rapid pump and dump, and the system's recency filter does not distinguish between these and genuine early movers.
- **Quantitative Evidence:** 61.3% of tokens are rejected at the detailed analysis stage, indicating that many tokens are already in decline when selected. High rejection rates at the detailed analysis stage confirm that many tokens are selected after their primary move.
- **Systemic Impact:** The system is biased toward tokens that are "recently active," regardless of whether that activity is sustainable or predictive. This leads to overfitting to recent activity and frequent selection of tokens in distribution or downtrend phases.

### 4. **Lack of Relative Strength and Market Context**
- **Mechanics:** The system uses absolute metrics (volume, price change) rather than benchmarking against the broader market or a token universe. There is no calculation of whether a token is outperforming the median or mean return of all candidates, and no evidence in logs or scoring formulas of relative strength calculations.
- **Quantitative Evidence:** Only a minority of tokens (e.g., SPX, GRUMPY) showed positive returns or outperformance; the majority lagged the market. Weak tokens can pass filters during negative market regimes, as the system does not require outperformance.
- **Systemic Impact:** In negative market regimes, weak tokens can pass filters simply by being "less bad" than others, not because they are strong. The system cannot systematically identify tokens with true leadership characteristics, leading to market regime blindness and missed leaders.

### 5. **Absence of Forward Return Backtesting**
- **Mechanics:** Filters are tuned for past performance (e.g., recent volume, price action), not for predictive power (forward returns). There is no measurement of average forward returns (e.g., 1h, 4h, 24h) for tokens passing each filter stage, and no forward return backtesting is present in logs or implementation guide.
- **Quantitative Evidence:** The system cannot distinguish between signals that lead to future outperformance and those that do not, resulting in repeated selection of tokens with poor forward returns. No stage in the logs or implementation guide measures average forward returns by filter stage.
- **Systemic Impact:** The system is not learning from its mistakes or successes, so it cannot improve its predictive power over time. This results in no predictive validation and repeated selection of non-performing tokens.

### 6. **Processing and API Latency**
- **Mechanics:** Batch processing and API call optimization (e.g., 8-minute or 30-minute scan intervals) introduce delays between data collection, analysis, and alerting. API calls are batched and cached for efficiency, but this can introduce additional lag, especially for fast-moving tokens.
- **Quantitative Evidence:** Scan intervals are set at 8 or 30 minutes, and logs show batch API calls and cache hit rates. The system may miss inflection points or enter after the move is over, and delayed alerts are common for fast movers.
- **Systemic Impact:** Even if a token is about to move, the system may not alert until it is too late for actionable trading. Excessive caching can further delay signals, reducing the real-world utility of alerts.

---

**Summary:**
The combination of lagging, backward-looking filters, over-reliance on volume/volatility triggers, recency bias, lack of relative strength benchmarking, and processing latency systematically biases the pipeline toward surfacing tokens that are already in decline. Quantitative evidence from run summaries and logs confirms that the majority of tokens surfaced are in post-pump or distribution phases, with negative short-term returns dominating the sample. Addressing these root causes requires integrating trend and relative strength filters, forward-looking on-chain and whale data, and systematic backtesting of filter effectiveness on forward returns.

---

## 4. **Trigger & Filter Issues**

| Problem/Trigger                | Pipeline Step           | Quantitative Evidence / Failure Mode                   | Solution/Improvement                                      |
|--------------------------------|-------------------------|-------------------------------------------------------|-----------------------------------------------------------|
| Volume/Volatility spike        | Discovery, Quick Scoring| High % of tokens with negative 4H/24H returns after    | Require trend confirmation (e.g., price > EMA,            |
|                                |                         | volume spike; >80% in downtrend                        | higher highs/lows)                                        |
| Top gainers                    | Discovery, Sorting      | Tokens selected after large move; 0/20 price gains     | Use relative strength (token return vs. universe),        |
|                                |                         | in scoring for many                                    | not absolute gain                                         |
| New listings                   | Discovery, Pre-filter   | High false positive rate; many are scams or illiquid   | Add quality/whale filters (e.g., min holders,             |
|                                |                         |                                                       | whale inflow)                                            |
| No trend filter                | Filtering, Scoring      | 0/5 trend analysis for most tokens; late entries       | Require uptrend on multiple timeframes                    |
|                                |                         |                                                       | (e.g., 4H, 1D)                                           |
| No forward return backtest     | All filter stages       | No evidence of improved forward returns; repeated      | Backtest on forward returns (1h, 4h, 24h) and             |
|                                |                         | selection of poor performers                           | optimize for positive forward returns                     |
| Emergency inclusion/relaxation | Filtering               | Lowered thresholds admit weak tokens; high rejection   | Limit relaxation, add minimum quality gates               |
|                                |                         | at detailed analysis                                   | even in low-yield cycles                                  |
| Recency filter                 | Pre-filter              | Many tokens in post-pump phase; 61.3% rejected at      | Penalize tokens with large recent drawdowns               |
|                                |                         | detailed analysis                                      | or post-pump patterns                                     |
| Caching/API latency            | All stages              | Delayed signals, missed inflection points in           | Shorten scan intervals, reduce cache TTL                  |
|                                |                         | fast markets                                           | for fast movers                                           |

**Key Takeaways:**
- Most failures stem from triggers that are lagging or not predictive (volume/volatility spikes, top gainers, recency), and from filters that do not enforce trend, relative strength, or forward-looking quality.
- Quantitative evidence from logs and run summaries shows that these issues result in high rejection rates at later stages, late entries, and repeated selection of tokens in decline.
- Improvements should focus on integrating trend and relative strength confirmation, forward return backtesting, and stricter quality gates at all stages.

---

## 5. **Recommendations for Improvement**

To address the root causes, trigger/filter issues, and API inefficiencies, the following systematic, quantitative, and actionable improvements are recommended. These are mapped to pipeline stages, with rationale, expected impact, and specific API usage optimizations:

| Recommendation                        | Pipeline Stage         | Quantitative Rationale / Evidence                | Expected Impact                                      |
|--------------------------------------|------------------------|--------------------------------------------------|------------------------------------------------------|
| **A. Add Trend Confirmation**         | Filtering, Scoring     | >80% of tokens in downtrend; 0/5 trend analysis  | Reduce late entries; surface tokens in uptrends      |
| - Require price > 20/50 EMA           |                        |                                                  |                                                      |
| - Require higher highs/lows (4H, 1D)  |                        |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **B. Integrate Relative Strength**    | Filtering, Scoring     | Weak tokens pass in negative regimes             | Select tokens outperforming the market/universe      |
| - Token return > median/mean          |                        |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **C. Use Forward-Looking Signals**    | Discovery, Filtering   | Volume/volatility spikes are lagging             | Capture early accumulation, not just post-pump       |
| - Whale inflow, large wallet buys     |                        |                                                  |                                                      |
| - On-chain net inflow                 |                        |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **D. Backtest with Forward Returns**  | All filter stages      | No evidence of improved forward returns          | Optimize filters for predictive power, not just past |
| - Measure 1h, 4h, 24h forward returns |                        |                                                  |                                                      |
| - Adjust thresholds for positive FWD  |                        |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **E. Avoid Chasing Parabolic Moves**  | Filtering             | Many tokens in post-pump phase                   | Reduce risk of entering after unsustainable moves    |
| - Exclude tokens up >X% in Y hours    |                        |                                                  |                                                      |
| - Exclude tokens with >30% drawdown   |                        |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **F. Limit Emergency Relaxation**     | Filtering             | Weak tokens admitted in low-yield cycles         | Maintain minimum quality even in low-signal periods  |
| - Add minimum gates for relaxation    |                        |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **G. Reduce Recency Bias**            | Pre-filter, Filtering  | 61.3% rejected at detailed analysis              | Focus on sustainable activity, not just recency      |
| - Penalize large drawdowns/post-pump  |                        |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **H. Shorten Processing Latency**     | All stages            | Delayed signals, missed inflection points        | More timely alerts, better capture of early moves    |
| - Reduce scan interval, cache TTL     |                        |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **I. Optimize API Usage: Caching**    | All stages            | Repeated identical calls in logs                 | Reduce redundant API calls, lower cost, faster runs  |
| - Cache recent price/metadata results |                        |                                                  |                                                      |
| - Cache trending/token lists (short TTL) |                      |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **J. Optimize API Usage: Batching**   | All stages            | Many sequential single-token calls in logs       | Reduce HTTP overhead, increase throughput            |
| - Use multi-token endpoints (multi_price, price_volume/multi) |  |                                                |                                                      |
| - Batch trade/holder queries          |                        |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **K. Limit Expensive/Slow Queries**   | Analysis, Filtering   | Holder list, OHLCV, and trade history are slow   | Lower latency, avoid unnecessary cost                |
| - Fetch only top N holders (e.g. 100) |                        |                                                  |                                                      |
| - Only call deep endpoints after passing initial filters |     |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **L. Align Data Fields to Use**       | All stages            | Unused fields fetched in logs                    | Lower payload, faster response, less cost            |
| - Only request needed fields          |                        |                                                  |                                                      |
|                                      |                        |                                                  |                                                      |
| **M. Add Predictive Filters Early**   | Discovery, Filtering  | Pipeline is reactive, not predictive             | Higher signal per API call, fewer false positives    |
| - Require sustained volume, holder growth |                     |                                                  |                                                      |
| - Drop tokens below volume/liquidity cutoffs up front |        |                                                  |                                                      |

**Immediate Priorities:**
- Implement trend and relative strength filters in the scoring pipeline
- Add forward return backtesting to validate and optimize filter effectiveness
- Integrate whale/on-chain inflow data for forward-looking signal detection
- Implement caching and batching for all repeated or multi-token API calls
- Limit deep/expensive queries to tokens that pass initial high-signal filters

**Longer-Term Enhancements:**
- Develop real-time or event-driven triggers for high-potential tokens (e.g., WebSocket feeds, if/when available)
- Build dashboards for filter performance and forward return monitoring
- Continuously refine thresholds and API usage based on live and historical data
- Integrate complementary data sources (e.g., CoinGecko, Nansen, Glassnode, LunarCrush) for cross-validation and richer signals

**Summary:**
By merging predictive filtering, API usage optimization (caching, batching, limiting slow queries), and forward-looking metrics, the pipeline will achieve higher signal quality per API call, lower cost, and more actionable alerts. These changes directly address both the quantitative inefficiencies and the systematic selection biases identified in the analysis.

---

## 6. **Actionable Trading Insights**

- **Best Long Setup:** SPX (strong uptrend, high liquidity/volume, but wait for a pullback).
- **Momentum Play:** GRUMPY (parabolic, but extremely high risk—use tight stops or avoid).
- **Potential Reversal Candidates:** BASED, DOLAN (showing early signs of basing, but need confirmation).
- **Avoid:** Most other tokens are in clear downtrends with no sign of reversal and/or declining volume.

---

## 7. **Conclusion**

- **Current Systemic Issue:** The token monitor is surfacing mostly downtrending tokens due to lagging, reactive filters and lack of trend confirmation or predictive features.
- **Path Forward:** Implement trend and relative strength filters, use forward-looking on-chain and order book data, and backtest on forward returns to improve real-world performance and reduce the selection of declining tokens.

---


---

## **8. Documentation Links**

- [Birdeye API Reference](https://docs.birdeye.so/reference/get-defi-tokenlist)
- [Token - Top tradersget](https://docs.birdeye.so/reference/get-defi-v2-tokens-top_traders)
- [Trades - Tokenget](https://docs.birdeye.so/reference/get-defi-v3-trades-token)

---

## **Summary Table: Birdeye Endpoints for Whale/On-Chain Data**

| Endpoint                        | Use Case                        | Key Fields/Filters                |
|----------------------------------|---------------------------------|-----------------------------------|
| /defi/v2/tokens/top_traders      | Whale wallet detection          | wallet, volume, trade count       |
| /defi/v3/trades/token            | Large trade detection           | side, amount_usd, timestamp       |
| /defi/v2/wallets/trader_gainers_losers | Identify top gainers/losers | wallet, realized pnl              |
| /defi/v3/token/list              | Filter by holders, liquidity    | min_holder, min_liquidity         |

---

## **Conclusion**

**Birdeye provides all the necessary endpoints to systematically integrate on-chain and whale data into your token monitoring pipeline.**  
- Use top traders and trade data endpoints to detect whale accumulation.
- Filter tokens based on net whale inflow and large buy activity.
- Integrate these filters into your main discovery logic for a more predictive, less reactive system.

