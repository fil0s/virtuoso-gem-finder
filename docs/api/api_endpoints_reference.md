# API Endpoints Reference

This document provides a comprehensive reference of all API endpoints used in the Early Token Monitor system. For each endpoint, we detail the specific query parameters and how the data is utilized within the application.

## Table of Contents

1. [Token Discovery Endpoints](#token-discovery-endpoints)
2. [Token Analysis Endpoints](#token-analysis-endpoints)
3. [Price & Market Data Endpoints](#price--market-data-endpoints)
4. [Wallet & Portfolio Endpoints](#wallet--portfolio-endpoints)
5. [Transaction Analysis Endpoints](#transaction-analysis-endpoints)

## Token Discovery Endpoints

### `/defi/v3/token/list`

Used for primary token discovery with various sorting strategies.

**Birdeye Documentation**: [Token - List (V3)](https://docs.birdeye.so/reference/get-defi-v3-token-list)

#### Query Parameters

| Parameter | Description | Example Values | Usage |
|-----------|-------------|----------------|-------|
| `chain` | Blockchain to query | `solana` | Always set to "solana" |
| `limit` | Maximum number of tokens to return | `100` | Typically set to min(100, max_tokens * 2) |
| `sort_by` | Field to sort results by | `volume_1h_change_percent`, `last_trade_unix_time`, `fdv`, `liquidity` | Changed for different discovery attempts |
| `sort_type` | Direction of sorting | `desc` | Always "desc" for discovery |

#### Response Fields Used

| Field | Description | Usage |
|-------|-------------|-------|
| `address` | Token contract address | Primary identifier, used in all subsequent API calls |
| `symbol` | Token symbol | Display and identification |
| `liquidity` | Current liquidity in USD | Quality filtering, minimum $20,000 base threshold |
| `market_cap` | Market capitalization | Quality filtering, minimum $30,000 base threshold |
| `holder` | Number of holders | Quality filtering, minimum 50 base threshold |
| `last_trade_unix_time` | Timestamp of most recent trade | Ensures active trading (max 2 hours old) |
| `recent_listing_time` | When token was first listed | Identifies new tokens for adjusted scoring |
| `volume_Xh_usd` | Volume over X hours (1h, 2h, 4h, 8h, 24h) | Multi-timeframe volume analysis |
| `volume_Xh_change_percent` | Volume change percentage | Volume momentum detection |
| `price_change_Xh_percent` | Price change percentage | Price momentum detection |
| `trade_Xh_count` | Number of trades in period | Trading activity assessment |

#### Implementation Details

- Used in methods: 
  - `efficient_discovery_with_strict_filters`
  - `_alternate_discovery`
  - `_fallback_v3_discovery_fdv_sort`
  - `_fallback_v3_discovery_liquidity_sort`
- Filter relaxation levels adjust thresholds by factor (L0: 100%, L1: 80%, L2: 65%)
- Progressive 5-attempt discovery pipeline with different sorting strategies

### `/defi/token_trending`

Used for trending token discovery.

**Birdeye Documentation**: [Token - Trending List](https://docs.birdeye.so/reference/get-defi-token-trending-list)

#### Query Parameters

| Parameter | Description | Example Values | Usage |
|-----------|-------------|----------------|-------|
| `limit` | Maximum number of tokens to return | `50` | Typically set to min(50, max_tokens) |

#### Response Fields Used

Same fields as `/defi/v3/token/list`

#### Implementation Details

- Used in methods:
  - `_trending_discovery`
  - `_trending_discovery_alternate`
- Relies on default API sorting for trending tokens
- Applied as third attempt in discovery pipeline when v3 attempts yield insufficient results

## Token Analysis Endpoints

### `/defi/token_overview`

Used to fetch comprehensive token overview data.

**Birdeye Documentation**: [Token - Overview](https://docs.birdeye.so/reference/get-defi-token-overview)

#### Query Parameters

| Parameter | Description | Example Values | Usage |
|-----------|-------------|----------------|-------|
| `token_address` | Token contract address | `So11111111111111111111111111111111111111112` | Required, identifies the token |

#### Response Fields Used

| Field | Description | Usage |
|-------|-------------|-------|
| `name` | Full token name | Token identification |
| `symbol` | Token symbol | Token identification |
| `decimals` | Token decimal places | Price calculation |
| `price` | Current token price | Price analysis |
| `fdv` | Fully diluted valuation | Token valuation metrics |
| `marketCap` | Market capitalization | Token size assessment |
| `supply` | Token supply information | Supply analysis |
| `volume` | Trading volume data | Activity assessment |
| `socials` | Social media links | Community analysis |
| `createdAt` | Creation timestamp | Token age assessment |

#### Implementation Details

- Used in methods:
  - `batch_token_overviews`
  - `_batch_overviews_ultra`
- Processed in smaller chunks to optimize API usage
- Concurrent fetching with semaphore (max 5 concurrent calls)
- 30-second timeout per request

### `/defi/token_security_check`

Used to fetch token security and risk analysis data.

**Birdeye Documentation**: [Token - Security](https://docs.birdeye.so/reference/get-defi-token-security)

#### Query Parameters

| Parameter | Description | Example Values | Usage |
|-----------|-------------|----------------|-------|
| `token_address` | Token contract address | `So11111111111111111111111111111111111111112` | Required, identifies the token |

#### Response Fields Used

| Field | Description | Usage |
|-------|-------------|-------|
| `is_scam` | Scam detection flag | Risk assessment |
| `is_risky` | Risk level assessment | Risk assessment |
| `security_score` | Overall security score | Risk quantification |
| `holder_distribution` | Distribution among holders | Concentration analysis |
| `top_holders` | List of largest holders | Whale detection |
| `mint_authority` | Mint authority information | Security assessment |
| `freeze_authority` | Freeze authority information | Security assessment |
| `creator_address` | Token creator address | Creator tracking |

#### Implementation Details

- Used in methods:
  - `batch_security_checks`
  - `_batch_security_ultra`
- Semaphore limiting concurrent calls (8 max)
- 30-second timeout per request
- 5-minute overall batch timeout

## Price & Market Data Endpoints

### `/defi/multi_price`

Used to fetch price data for multiple tokens in a single call.

**Birdeye Documentation**: [Price - Multiple](https://docs.birdeye.so/reference/post-defi-price-multiple)

#### Query Parameters

| Parameter | Description | Example Values | Usage |
|-----------|-------------|----------------|-------|
| `list_address` | Comma-separated token addresses | `addr1,addr2,addr3` | Required, identifies tokens |
| `include_liquidity` | Whether to include liquidity data | `true` | Set to true to get liquidity metrics |

#### Response Fields Used

| Field | Description | Usage |
|-------|-------------|-------|
| `price` | Current token price | Price analysis |
| `liquidity` | Token liquidity | Liquidity assessment |
| `priceChange` | Price change metrics | Momentum analysis |
| `volume` | Volume metrics | Activity assessment |
| `volumeChange` | Volume change percentages | Momentum analysis |

#### Implementation Details

- Used in methods:
  - `batch_multi_price`
  - `_batch_multi_price_ultra`
- Batch size limited to 50 addresses per request
- Fallback to individual calls if batch request fails

### `/defi/ohlcv`

Used to fetch historical price candles.

**Birdeye Documentation**: [OHLCV](https://docs.birdeye.so/reference/get-defi-ohlcv)

#### Query Parameters

| Parameter | Description | Example Values | Usage |
|-----------|-------------|----------------|-------|
| `address` | Token contract address | `So11111111111111111111111111111111111111112` | Required, identifies the token |
| `timeframe` | Candle timeframe | `1h`, `4h`, `1d` | Indicates analysis granularity |
| `time_from` | Start timestamp | `1643673600` | Set to current time minus period (e.g., 24h) |
| `time_to` | End timestamp | `1643760000` | Optional, defaults to current time |

#### Response Fields Used

| Field | Description | Usage |
|-------|-------------|-------|
| `time` | Candle timestamp | Time series analysis |
| `open` | Opening price | Price pattern analysis |
| `high` | Highest price | Volatility assessment |
| `low` | Lowest price | Support level analysis |
| `close` | Closing price | Trend analysis |
| `volume` | Trading volume | Volume analysis |

#### Implementation Details

- Used in methods:
  - `_ultra_batch_price_history`
  - `_fetch_batch_ohlcv_optimized`
- Focus on critical timeframes (1h, 4h, 1d)
- Optimized to fetch only most recent data (last 24 hours)

## Wallet & Portfolio Endpoints

### `/defi/wallet_portfolio`

Used to analyze whale and trader wallets.

**Birdeye Documentation**: [Wallet Portfolio](https://docs.birdeye.so/reference/get-defi-wallet-portfolio)

#### Query Parameters

| Parameter | Description | Example Values | Usage |
|-----------|-------------|----------------|-------|
| `wallet` | Wallet address | `HN7cABqLq...` | Required, identifies the wallet |
| `include_meta` | Include token metadata | `true` | Always true for complete data |
| `include_price` | Include price data | `true` | Always true for portfolio valuation |

#### Response Fields Used

| Field | Description | Usage |
|-------|-------------|-------|
| `totalValueUsd` | Portfolio total value | Whale/trader size assessment |
| `items` | List of token holdings | Portfolio composition analysis |
| `tokenAddress` | Address of held token | Token tracking |
| `balance` | Token balance | Position size analysis |
| `valueUsd` | USD value of position | Position importance |
| `priceUsd` | Token price | Valuation |
| `allocation` | Percentage of portfolio | Conviction assessment |

#### Implementation Details

- Used in methods:
  - `batch_whale_portfolios`
  - `batch_trader_analysis`
  - `fetch_whale_portfolio`
  - `fetch_trader_data`
- Processed in optimized batches (20 whales or 15 traders per batch)
- Semaphore limiting concurrent API calls
- Adaptive inter-batch delays based on success rates

## Transaction Analysis Endpoints

### `/defi/token_tx`

Used to analyze token transaction patterns.

**Birdeye Documentation**: [Trades - Token](https://docs.birdeye.so/reference/get-defi-trades-token)

#### Query Parameters

| Parameter | Description | Example Values | Usage |
|-----------|-------------|----------------|-------|
| `address` | Token contract address | `So11111111111111111111111111111111111111112` | Required, identifies the token |
| `limit` | Maximum transactions to fetch | `20` | Optimized to 20 (from 50) to save API quota |
| `tx_type` | Transaction type filter | `swap` | Set to "swap" to focus on trading activity |

#### Response Fields Used

| Field | Description | Usage |
|-------|-------------|-------|
| `blockTime` | Transaction timestamp | Temporal analysis |
| `volumeInUsd` | Transaction USD volume | Volume analysis |
| `side` | Buy or sell | Buy/sell ratio calculation |
| `buyer` | Buyer wallet | Buyer analysis |
| `seller` | Seller wallet | Seller analysis |
| `price` | Transaction price | Price impact analysis |

#### Implementation Details

- Used in methods:
  - `_ultra_batch_transactions`
  - `_fetch_batch_transactions_optimized`
- Limited to 20 transactions per token
- Semaphore limiting to 3 concurrent calls (conservative)
- Quick transaction pattern analysis calculating:
  - Total volume
  - Average transaction size
  - Buy/sell ratio
  - Transaction count
  - Momentum assessment (bullish/bearish)

### `/defi/v3/all-time/trades/multiple`

Used to analyze all-time trade data for multiple tokens.

**Birdeye Documentation**: [All Time Trades (Multiple)](https://docs.birdeye.so/reference/post-defi-v3-all-time-trades-multiple)

#### Query Parameters

| Parameter | Description | Example Values | Usage |
|-----------|-------------|----------------|-------|
| `time_frame` | Time interval | `24h`, `7d`, `alltime` | Set based on analysis timeframe |
| `list_address` | Comma-separated token addresses | `addr1,addr2,addr3` | Required, identifies tokens |

#### Response Fields Used

| Field | Description | Usage |
|-------|-------------|-------|
| `total_volume` | Total trading volume | Volume analysis |
| `total_volume_usd` | Total USD volume | USD volume analysis |
| `volume_buy_usd` | Buy volume in USD | Buy pressure assessment |
| `volume_sell_usd` | Sell volume in USD | Sell pressure assessment |
| `total_trade` | Total trade count | Activity assessment |
| `buy` | Buy trade count | Buy transaction counting |
| `sell` | Sell trade count | Sell transaction counting |

#### Implementation Details

- Used in methods:
  - `batch_trades_analysis`
  - `_ultra_batch_trades_analysis`
- Batch size limited to 20 tokens per request
- Comprehensive buy/sell pressure analysis

---

## API Usage Optimization

### Batching Strategies

- **Multi-price batching**: Up to 50 tokens per call
- **Progressive discovery pipeline**: 5 attempts with increasing filter relaxation
- **Ultra-batch workflows**: Complete token analysis with 90%+ API call reduction
- **Timeframe batching**: OHLCV data grouped by timeframe
- **Cross-service coordination**: Simultaneous fetching for tokens, whales, and traders

### Rate Limiting

- **Semaphore controls**: Limit concurrent API calls
- **Inter-batch delays**: Adaptive pauses between batches
- **Timeout management**: 30s per request, 5min per batch
- **Fallback mechanisms**: Alternative endpoints when primary fails

### Caching

- **TTL-based caching**: 5-minute cache for batch data
- **Recently analyzed tracking**: Avoid reprocessing tokens for 2 hours
- **Progressive filtering**: Eliminate unsuitable tokens early 

## API Reference Documentation

For complete API documentation, visit the [Birdeye API Reference](https://docs.birdeye.so/reference/get-defi-tokenlist). 