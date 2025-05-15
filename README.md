# Virtuoso Gem Finder 🚀

## Overview

Virtuoso Gem Finder is a sophisticated cryptocurrency token scanner specifically designed for the Solana blockchain. It automatically identifies potential "gem" tokens based on configurable criteria such as liquidity, market cap, holder count, and other metrics.

## Features

- 🔍 Real-time token scanning on Solana
- ⛓️ Direct Solana RPC integration for on-chain data
- 📊 Configurable scoring system for gem identification
- 🐋 RugCheck API integration for security analysis
- 🐋 Enhanced whale wallet tracking with on-chain verification
- 💾 Persistent storage of discovered tokens
- 📱 Telegram notifications for discovered gems
- 📈 Performance metrics and monitoring
- 🔄 Hot-reloading configuration
- 🪵 Comprehensive logging system
- 💎 Risk-based token filtering using customizable Dexscreener criteria
- 🚀 Jupiter API integration for real-time pricing and token verification
- 🔥 Helius API integration for enhanced transaction and wallet analysis
- 📈 Advanced trend analysis for volume and transaction patterns
- 🔍 Early detection of tokens with positive momentum

## Prerequisites

- Python 3.8+
- SQLite3
- Active Telegram Bot Token
- DexScreener API access
- RugCheck API key
- Solana RPC endpoint (public or private)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/virtuoso-gem-finder.git
cd virtuoso-gem-finder
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `credentials.json` file in the config directory:
```json
{
    "telegram_bot_token": "YOUR_BOT_TOKEN",
    "telegram_chat_id": "YOUR_CHAT_ID",
    "solana_rpc_url": "YOUR_PRIVATE_RPC_URL",  // Optional: defaults to public endpoint
    "rugcheck_api_key": "YOUR_RUGCHECK_API_KEY",
    "helius_api_key": "YOUR_FREE_HELIUS_API_KEY"
}
```

2. Configure settings in `config/config.yaml`:
```yaml
whale_tracking:
  suspicious_patterns:
    new_wallet_threshold: 86400  # 24 hours in seconds
    high_frequency_threshold: 100  # transactions per 24h
    contract_interaction_check: true
  analysis:
    min_wallet_age: 86400
    max_tx_frequency: 100
    verification_requirements:
      - minimum_balance
      - transaction_history
      - contract_status
  alerts:
    notify_on_suspicious: true
    tracking_interval: 3600
    movement_threshold: 0.02
```

## Enhanced Scoring System

The gem finder uses a sophisticated scoring system that evaluates tokens based on multiple criteria:

### Core Metrics (65% of total score)
- **Liquidity** (20%): Logarithmic scaling of liquidity depth with dynamic thresholds
- **Market Cap** (15%): Project size evaluation with growth potential analysis
- **Holders** (15%): Community strength and organic growth patterns
- **Volume** (15%): Trading activity relative to market cap and liquidity

### Distribution & Security Metrics (28% of total score)
- **Holder Distribution** (10%): Advanced Gini coefficient analysis
- **Supply Distribution** (10%): Whale concentration and token distribution patterns
- **Security** (8%): Smart contract analysis and risk assessment

### Technical Metrics (7% of total score)
- **Price Stability** (4%): Volatility and market manipulation detection
- **Age** (3%): Time-based maturity analysis

### Trend Analysis Metrics (NEW)
- **Volume Trends**: Analyzing volume patterns across 1h, 6h, and 24h timeframes
- **Volume Acceleration**: Detecting rapidly increasing trading activity
- **Transaction Trends**: Monitoring growth in transaction counts over time
- **Momentum Detection**: Identifying tokens with positive and increasing momentum

### Scoring Components

Each metric is evaluated using sophisticated algorithms:

1. **Liquidity Score**
   - Dynamic logarithmic scaling for fair comparison
   - Adaptive minimum and maximum thresholds
   - Real-time liquidity depth analysis

2. **Holder Distribution Score**
   - Advanced Gini coefficient calculation
   - Whale wallet tracking
   - Concentration risk assessment
   - Organic growth pattern verification

3. **Security Score**
   - Contract verification status
   - Honeypot detection
   - Buy/sell tax analysis
   - Risk factor identification
   - Mint authority verification
   - Upgradeable contract detection
   - Suspicious transfer pattern analysis

4. **Price Stability Score**
   - Advanced volatility measurement
   - Market manipulation detection
   - Historical price pattern analysis
   - Volume correlation studies

5. **Trend Analysis Score**
   - Hourly volume growth patterns
   - Volume acceleration calculation
   - Transaction count trend analysis
   - Multi-timeframe comparisons (1h, 6h, 24h)
   - Detection of recently increasing activity

## Trend Analysis System

The gem finder now includes an advanced trend analysis system to detect tokens showing positive momentum and increasing interest:

### Key Trend Analysis Features

- **Multi-timeframe Volume Analysis**: Compares average hourly volume across 1h, 1-6h, and 6-24h periods
- **Volume Acceleration Calculation**: Measures percentage increase in hourly volume
- **Transaction Count Trend Detection**: Identifies patterns of increasing transaction activity
- **Trend Categorization**: Classifies tokens into trend categories:
  - "Strongly Increasing": Rapid acceleration across all timeframes
  - "Increasing": Steady growth in recent periods
  - "Recently Increasing": New emerging momentum
  - "Stable": Consistent but not growing activity
  - "Decreasing": Declining interest

### Trend Visualization

Telegram alerts now include trend indicators:
- 🔥🔥 Strongly increasing trends
- 🔥 Increasing trends
- 📈 Recently increasing trends
- ➡️ Stable trends
- 📉 Decreasing trends

### Trend Filtering

The system can now filter potential gems based on trend criteria:
- Minimum volume trend score
- Minimum volume acceleration percentage
- Minimum transaction trend score

## On-Chain Data Integration

The gem finder now includes direct Solana blockchain integration:

- Token Supply Verification
- Holder Account Analysis
- Program ID Verification
- Mint Authority Status
- Token Metadata
- Transaction Monitoring

### RPC Methods Used

- `getTokenSupply`: Fetch accurate token supply
- `getTokenAccountsByOwner`: Analyze holder distributions
- `getProgramAccounts`: Verify token programs
- `getAccountInfo`: Check token metadata

## Enhanced Token Analysis

Token metrics now include additional on-chain data:
- Total token supply from blockchain
- Token decimals
- Mint authority status
- Program ID verification
- Top holder analysis with direct chain data

## Enhanced Whale Tracking

The gem finder now includes sophisticated whale wallet tracking with on-chain verification:

### Whale Analysis Features
- On-chain wallet verification
- Transaction pattern analysis
- Suspicious behavior detection
- Historical movement tracking
- Wallet age verification
- Real-time monitoring
- Suspicious activity alerts

### Whale Tracking Components

1. **Wallet Verification**
   - Age verification (minimum 24h old)
   - Transaction history analysis
   - Contract interaction patterns
   - Activity frequency monitoring
   - Legitimacy scoring

2. **Suspicious Pattern Detection**
   - New wallet identification (< 24h old)
   - Abnormal transaction frequency (>100 tx/24h)
   - Contract interaction analysis
   - Coordinated movement detection
   - Risk factor assessment

3. **Data Storage**
   - Whale wallet profiles
   - Historical holdings
   - Transaction patterns
   - Verification status
   - Activity metrics
   - Suspicious behavior flags

### Whale Metrics

The system tracks various whale-related metrics:
- Wallet age and creation time
- Transaction frequency and patterns
- Holding percentages and changes
- Contract interactions
- Historical movement patterns
- Verification status
- Risk assessment scores

## Configuration

The whale tracking system is highly configurable through `config.yaml`:

```yaml
whale_tracking:
  suspicious_patterns:
    new_wallet_threshold: 86400  # 24 hours in seconds
    high_frequency_threshold: 100  # transactions per 24h
    contract_interaction_check: true
  analysis:
    min_wallet_age: 86400
    max_tx_frequency: 100
    verification_requirements:
      - minimum_balance
      - transaction_history
      - contract_status
  alerts:
    notify_on_suspicious: true
    tracking_interval: 3600
    movement_threshold: 0.02
```

## Enhanced Whale & Smart Money Tracking

The gem finder now includes sophisticated whale and smart money tracking with advanced pattern detection:

### Smart Money Analysis Features
- Developer wallet identification
- 7-day and 30-day performance metrics
- Win rate analysis
- Trading pattern detection
- Sell timing analysis
- Price impact tracking

### Smart Money Detection Components

1. **Developer Wallet Analysis**
   - Contract creation involvement
   - Admin function usage patterns
   - Early token distribution tracking
   - Developer selling activity monitoring

2. **Trading Pattern Detection**
   - Win rate calculation
   - Sell timing near price tops
   - Price impact after trades
   - Performance tracking (7d/30d)
   - Suspicious pattern identification

3. **Red Flag Detection**
   - Unrealistic win rates
   - Coordinated selling patterns
   - Price manipulation indicators
   - Immediate post-sell dumps
   - Local top selling patterns

### Smart Money Metrics

The system tracks various smart money related metrics:
- Trading success rates
- Average profit per trade
- Sell timing accuracy
- Price impact scores
- Developer wallet

## Advanced Wallet Analysis

The gem finder now includes sophisticated wallet analysis:

### Smart Money Clustering
- Identifies groups of wallets known historically for profitable early token purchases
- Clusters wallets based on behavioral patterns using machine learning
- Tracks wallet performance metrics including win rates and profit multiples
- Improves predictive confidence by identifying smart money interest in tokens

### Enhanced Wallet Profiling
- Classifies wallets as whales, smart money, or retail investors
- Tracks wallet activity, balance, and transaction patterns
- Provides richer context for holder analysis
- Identifies suspicious wallet behaviors
- Calculates behavioral scores for each wallet type

### Behavioral Scoring System
- Evaluates developer responsiveness, transparency and community engagement
- Introduces weighted scoring for early vs trailing signals
- Analyzes developer wallet behavior and project history
- Detects suspicious patterns in transaction growth
- Identifies potential risk factors in token metrics

### Early Signal Weighting
- Applies higher weights to early signals like transaction growth and new wallet engagement
- Reduces emphasis on trailing metrics like total volume and market cap
- Provides better detection of emerging gems
- Enables more nuanced scoring for new tokens

## Database Schema Updates

### Whale Holdings Table
```sql
CREATE TABLE whale_holdings (
    token_address TEXT,
    whale_address TEXT,
    holding_percentage REAL,
    last_updated INTEGER,
    transaction_count INTEGER,
    wallet_age INTEGER,
    is_contract BOOLEAN,
    verified BOOLEAN,
    PRIMARY KEY (token_address, whale_address)
)
```

## Dexscreener-based Gem Filters

Virtuoso Gem Finder now incorporates a flexible filtering system based on popular Dexscreener criteria to help identify potential gems across different risk profiles. This allows for a more nuanced approach to token discovery, catering to various investment strategies.

The filters are categorized into four distinct risk profiles:

1.  **High Risk**
    *   **Max Market Cap:** \$500k
    *   **Max Pair Age:** 48h
    *   **24h TXs min:** 1000
    *   **24h Volume min:** \$1M
    *   **1h change:** +10-20%
    *   **6h change:** 0%
    *   **24h change:** 0%

2.  **Medium Risk**
    *   **Max Market Cap:** \$1M-\$5M
    *   **Min Pair Age:** 72h
    *   **24h TXs min:** 1500
    *   **24h Volume min:** \$1.5M
    *   **1h change:** +40%
    *   **6h change:** 0%
    *   **24h change:** 0%

3.  **Low Risk**
    *   **Max Market Cap:** \$5M-\$10M
    *   **Min Pair Age:** 100h
    *   **24h TXs min:** 2000
    *   **24h Volume min:** \$3M
    *   **1h change:** +20%
    *   **6h change:** +10-20%
    *   **24h change:** +10-30%

4.  **Minimum Risk**
    *   **Max Market Cap:** \$20M+
    *   **Min Pair Age:** 200h
    *   **24h TXs min:** 3000
    *   **24h Volume min:** \$5M
    *   **1h change:** +10%
    *   **6h change:** 0%
    *   **24h change:** +10%

These filters are applied to incoming token data, and tokens can be matched against one or more of these profiles. The specific parameters (e.g., market capitalization, pair age, transaction volume, price percentage changes over 1h, 6h, and 24h) are defined internally based on the criteria shown in the user-provided image and can be adapted as needed within the `solgem.py` script.

This feature complements the existing scoring system by providing an initial layer of categorization based on common trading patterns and risk assessment. The "Three more factors to check using other tools" (Artificial inflation of TXs, volumes and holders amount; Smart wallets accumulation; Insider/Dev trading wallets) mentioned in the source image are intended to be addressed by other functionalities within Virtuoso Gem Finder or require manual analysis.

## Jupiter API Integration

Virtuoso Gem Finder now includes direct integration with Jupiter, Solana's leading liquidity aggregator and DEX network, to enhance token data accuracy and reliability:

### Key Jupiter Integration Features

- **Real-time Token Pricing**: Get the most up-to-date token prices from Jupiter's extensive liquidity pools, providing a more accurate current price than DexScreener alone
- **Token Verification**: Validate tokens against Jupiter's token list to quickly identify legitimate projects
- **Enhanced Price Change Calculations**: Combine Jupiter's current prices with historical data to calculate more accurate price changes over different time periods
- **Price Discrepancy Detection**: Automatically identify and flag significant price differences between data sources, which can indicate potential market issues or manipulation
- **Fallback Mechanisms**: Access Jupiter data when DexScreener API is unavailable or rate-limited

### How Jupiter Integration Improves Gem Finding

1. **More Accurate Filtering**:
   - Real-time prices from Jupiter improve the accuracy of price change filters
   - Fresh price data helps identify very recent price movements that might not yet be reflected in DexScreener's data
   - Catch gems in the earliest stages of price movement

2. **Enhanced Security**:
   - Token verification through Jupiter's token lists adds an additional layer of legitimacy checking
   - Tokens not listed in Jupiter's database receive an automatic risk factor flag

3. **Data Reliability**:
   - Cross-verification between multiple data sources improves overall data quality
   - Reduced reliance on any single data provider improves system resilience
   - Price discrepancy detection helps identify potentially manipulated markets

### Technical Implementation

The Jupiter integration uses the `jupiter-python-sdk` package to:
- Fetch token lists and store them for efficient verification
- Query real-time prices against USDC for accurate valuation
- Calculate updated price changes using current Jupiter prices and historical data
- Update token risk assessments with additional verification information

This integration makes the gem-finding process more robust and accurate, particularly for identifying early-stage opportunities with very recent price movements.

## Helius API Integration

Virtuoso Gem Finder now integrates with Helius API to provide enhanced transaction data and wallet analysis capabilities:

### Key Helius Integration Features

- **Enhanced Transaction Data**: Access detailed, enriched transaction metadata that provides deeper insights into token activity
- **Advanced Wallet Analysis**: Identify bot wallets, smart money, and suspicious trading patterns with comprehensive behavioral analysis
- **Token Metadata Enhancement**: Get additional creator and metadata information for tokens
- **NFT Event Tracking**: Monitor NFT-related events for relevant tokens
- **Suspicious Activity Detection**: Identify automated trading, wash trading, and potential bot wallets

### How Helius Integration Improves Gem Finding

1. **Better Wallet Verification**:
   - Analyze transaction patterns to identify suspicious wallets
   - Calculate key metrics like transaction frequency and token diversity
   - Identify potential pump and dump participants
   - Flag wallet behaviors indicative of bots or coordinated groups

2. **Enhanced Token Analysis**:
   - Get creator information to better understand token provenance
   - Access additional metadata including off-chain links and resources
   - View detailed supply and distribution information
   - Enhance risk assessment with creator wallet behavior analysis

3. **Comprehensive Data Integration**:
   - Combine data from DexScreener, Jupiter, and Helius for a complete picture
   - Cross-validate information across multiple reputable sources
   - Fall back to alternative data sources when one is unavailable
   - Get the most accurate and up-to-date token information available

### Technical Implementation

The Helius integration supports:
- Asynchronous API calls for better performance
- Detailed transaction history analysis
- Comprehensive wallet behavior metrics
- Token metadata enrichment
- Intelligent fallback mechanisms

### Configuration

To use the Helius API integration, add your free Helius API key to the `credentials.json` file:

```json
{
    "telegram_bot_token": "YOUR_BOT_TOKEN",
    "telegram_chat_id": "YOUR_CHAT_ID",
    "helius_api_key": "YOUR_FREE_HELIUS_API_KEY"
}
```

The application will automatically detect and use Helius capabilities when an API key is provided.

## Usage

Run the script:
```bash
python solgem.py
```

### Debug Mode

To enable debug logging:
```python
gem_finder = VirtuosoGemFinder(BOT_TOKEN, CHAT_ID)
gem_finder.debug_mode = True
```

## Logging

Logs are stored in `virtuoso_gem_finder.log` with rotation enabled:
- Maximum file size: 5MB
- Backup count: 5 files
- Console output: INFO level and above
- File output: DEBUG level and above

View logs in real-time:
```bash
tail -f virtuoso_gem_finder.log
```

## Database

The script uses SQLite3 for data persistence with the following tables:
- `tokens`: Stores discovered token information
- `whale_holdings`: Tracks significant token holders

## API Rate Limiting

- Default rate limit: 300 requests per minute
- Token bucket algorithm for efficient rate limiting
- Automatic backoff and retry mechanism

## Metrics

The script tracks various performance metrics:
- API call success/failure rates
- Response times
- Memory usage
- Gems discovered
- Processing duration

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Dependencies

```
requests>=2.25.1
pydantic>=1.8.2
tenacity>=8.0.1
python-telegram-bot>=13.7
watchdog>=2.1.6
psutil>=5.8.0
cachetools>=4.2.2
base58>=2.1.0  # For statistical calculations
numpy>=1.21.0
scipy>=1.7.0   # For advanced metrics
```

## Project Structure

```
virtuoso-gem-finder/
├── core/                  # Core application logic
│   ├── __init__.py
│   └── solgem.py          # Main application orchestrator (VirtuosoGemFinder class)
├── api/                   # API clients and connectors
│   ├── __init__.py
│   ├── jupiter_connector.py   # Jupiter API client
│   ├── helius_connector.py    # Helius API client
│   ├── solana_rpc_enhanced.py # Enhanced Solana RPC functionalities
│   └── pump_fun_scraper.py    # PumpFun data scraper
├── analysis/              # Analysis modules and scoring logic
│   ├── __init__.py
│   ├── enhanced_scoring.py    # Orchestrates advanced scoring modules
│   ├── momentum_analyzer.py   # On-chain momentum analysis
│   ├── smart_money_clustering.py # Smart money wallet clustering logic
│   ├── wallet_analyzer.py     # Individual wallet analysis logic
│   └── behavioral_scoring.py  # Behavioral pattern scoring for tokens/wallets
├── config/                # Configuration files
│   ├── __init__.py
│   ├── config.yaml        # Main configuration file
│   └── pump_fun_tokens.json # Token data for pump fun analysis
├── services/              # Modular services
│   ├── __init__.py
│   ├── logger_setup.py      # Centralized logging configuration
│   ├── config_handler.py    # Handles config file watching and reloading
│   ├── config_models.py     # Pydantic models for config.yaml validation
│   ├── service_interfaces.py # Protocol definitions for service abstractions
│   ├── dexscreener_api.py   # DexScreener API client
│   ├── solscan_api.py       # Solscan API client
│   ├── gem_scorer.py        # Base gem scoring logic (GemScorer class)
│   ├── whale_tracker.py     # Whale wallet tracking and analysis
│   ├── trend_analysis_service.py # Volume and transaction trend analysis
│   ├── filtering_service.py   # Token filtering logic
│   ├── token_enrichment_service.py # Comprehensive token data aggregation and enrichment
│   ├── database_manager.py  # SQLite database interactions
│   ├── telegram_alerter.py  # Telegram notification service
│   └── rug_check_api.py     # RugCheck API client
├── utils/                 # Utility functions and helpers
│   └── __init__.py
├── logs/                  # Log files directory
│   └── virtuoso_gem_finder.log # Main application log file
├── main.py                # Entry point script
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Project Architecture

The Virtuoso Gem Finder is designed with a modular architecture, centered around a main orchestrator (`VirtuosoGemFinder` in `solgem.py`) that coordinates various specialized services. This design promotes separation of concerns, testability, and maintainability.

### Core Components:

1.  **`VirtuosoGemFinder` (Orchestrator - `solgem.py`):**
    *   Initializes and manages the lifecycle of all services.
    *   Runs the main asynchronous scanning loop(s).
    *   Coordinates the flow of data between services (filtering, enrichment, scoring, alerting).
    *   Handles configuration loading (using Pydantic models from `config_models.py`) and signal processing for graceful shutdown.

2.  **Service Modules (`services/` directory):**
    *   **API Clients**: Individual modules for interacting with external APIs (`DexScreenerAPI`, `SolscanAPI`, `RugCheckAPI`, `JupiterAPI` from `jupiter_connector.py`, `HeliusAPI` from `helius_connector.py`). These are responsible for raw data fetching.
    *   **`FilteringService`**: Implements logic to initially filter token pairs based on criteria defined in `config.yaml` and `FILTERS_DATA` (e.g., liquidity, market cap, age, price changes). Uses `TrendAnalysisService` and `JupiterAPI` for more nuanced filtering.
    *   **`TrendAnalysisService`**: Analyzes volume and transaction trends from DexScreener data.
    *   **`TokenEnrichmentService`**: Gathers comprehensive data for a token from multiple sources (DexScreener, Solscan, Jupiter, Helius, RPC) and compiles it into a `TokenMetrics` object. This service acts as the primary data aggregator for a specific token after initial filtering.
    *   **`GemScorerService` (`gem_scorer.py`):** Calculates a base score for a token based on fundamental metrics defined in `TokenMetrics` and configured weights.
    *   **`EnhancedScoring` (`enhanced_scoring.py`):** Orchestrates advanced scoring modules:
        *   **`MomentumAnalyzer`**: Calculates on-chain momentum scores (price, volume, holders, etc.).
        *   **`WalletAnalyzer`**: Performs deep analysis of individual wallets.
        *   **`SmartMoneyClusterer`**: Identifies clusters of smart money wallets.
        *   **`BehavioralScorer`**: Scores tokens/wallets based on behavioral patterns.
        This service adjusts the base score from `GemScorer` based on its findings.
    *   **`WhaleTrackerService` (`whale_tracker.py`):** Tracks and analyzes significant whale wallets, incorporating data from `SmartMoneyAnalyzer`.
    *   **`DatabaseManager`**: Manages persistence of discovered gems and other relevant data to an SQLite database.
    *   **`TelegramAlerter`**: Formats and sends notifications for discovered gems via Telegram.
    *   **Utility Services**:
        *   `LoggerSetup`: Centralized logging configuration.
        *   `ConfigHandler` & `ConfigModels`: Manages YAML configuration loading, validation with Pydantic, and potential hot-reloading.
        *   `ServiceInterfaces`: Defines `Protocol` classes for dependency inversion and testability.

3.  **Solana Interaction:**
    *   `SolanaRPC` & `EnhancedSolanaRPC`: Provide low-level access to the Solana blockchain for fetching on-chain data like token supply, account info, etc.

### Design Principles:

*   **Modularity & Single Responsibility**: Each service aims to handle a specific aspect of the gem finding process.
*   **Dependency Injection**: Services are generally initialized by the `VirtuosoGemFinder` orchestrator, and dependencies (like other services or API clients) are passed in via constructors.
*   **Asynchronous Operations**: I/O-bound operations (API calls, database interactions where applicable) are handled asynchronously using `async/await` and `asyncio.to_thread` for wrapping synchronous library calls.
*   **Configuration Driven**: Behavior of services and the overall application is heavily driven by `config.yaml`.
*   **Abstraction for Testability**: `Protocol`s in `service_interfaces.py` allow for easier mocking and testing of individual components.

## Data Flow

The typical data flow for identifying and processing a potential gem is as follows:

1.  **Pair Discovery (`DexScreenerAPI` -> `VirtuosoGemFinder`):
    *   `VirtuosoGemFinder` periodically calls `DexScreenerAPI` (via `asyncio.to_thread`) to fetch new token pairs on Solana.

2.  **Initial Filtering (`VirtuosoGemFinder` -> `FilteringService`):
    *   For each new pair, `VirtuosoGemFinder` calls `FilteringService.is_potential_gem()`. 
    *   `FilteringService` uses basic pair data (liquidity, market cap, age) and may consult `TrendAnalysisService` (which uses `DexScreenerAPI`) and `JupiterAPI` (for real-time price changes) to decide if the pair warrants further analysis.

3.  **Comprehensive Data Enrichment (`VirtuosoGemFinder` -> `TokenEnrichmentService`):
    *   If a pair passes initial filtering, `VirtuosoGemFinder` calls `TokenEnrichmentService.analyze_token_comprehensively()`.
    *   `TokenEnrichmentService` fetches detailed data from multiple sources:
        *   `DexScreenerAPI`: Pair details, historical token data.
        *   `SolscanAPI` / `HeliusAPI`: Holder counts, token metadata.
        *   `JupiterAPI`: Real-time price, token verification.
        *   `HeliusAPI` / `EnhancedSolanaRPC`: On-chain metadata (supply, mint status, creators).
        *   `TrendAnalysisService`: Volume and transaction trends.
    *   It compiles all this information into a `TokenMetrics` object.

4.  **Base Scoring (`VirtuosoGemFinder` -> `GemScorerService`):
    *   The `TokenMetrics` object is passed to `GemScorerService.calculate_score()`.
    *   `GemScorerService` calculates a base score based on fundamental metrics and configured weights.

5.  **Enhanced Scoring (Optional) (`VirtuosoGemFinder` -> `EnhancedScoring`):
    *   If the base score meets a configured threshold (`min_base_score_for_trigger`) and `EnhancedScoring` is enabled:
        *   `VirtuosoGemFinder` calls `EnhancedScoring.enhance_token_analysis()` with the `TokenMetrics` and base score.
        *   `EnhancedScoring` orchestrates calls to its sub-modules:
            *   `MomentumAnalyzer` (uses `HeliusAPI`, `JupiterAPI`, `EnhancedSolanaRPC`).
            *   `WalletAnalyzer`, `SmartMoneyClusterer`, `BehavioralScorer` (use `HeliusAPI`, `JupiterAPI`, `EnhancedSolanaRPC`).
        *   `EnhancedScoring.calculate_enhanced_gem_score()` combines the base score with adjustments from the advanced analyses to produce a final score and detailed breakdown.

6.  **Gem Discovery Handling (`VirtuosoGemFinder` -> `DatabaseManager`, `TelegramAlerter`):
    *   If the final score (either base or enhanced) meets the `min_gem_score` threshold:
        *   `VirtuosoGemFinder` calls `DatabaseManager.save_token()` to persist the token and its score.
        *   `VirtuosoGemFinder` calls `TelegramAlerter.send_gem_alert()` to notify the user, providing the `TokenMetrics`, final score, score breakdown, and any enhanced analysis data.

7.  **Whale Tracking (`TokenEnrichmentService` -> `WhaleTrackerService` - *Note: Current implementation in `TokenEnrichmentService` uses LP shares for `whale_holdings`. True token whale tracking based on top holders would be a separate flow, likely initiated after token enrichment*):
    *   During token enrichment, `TokenEnrichmentService` might invoke `WhaleTrackerService` (which uses `SmartMoneyAnalyzer`) to analyze significant holders (currently LP data, ideally actual token holders from Solscan/Helius). The results can update `TokenMetrics.risk_factors`.

This flow is managed within `VirtuosoGemFinder`'s asynchronous scanning loops, allowing for concurrent processing of multiple pairs.

## Performance Considerations

### RPC Optimization
- Multiple RPC endpoints for redundancy
- Automatic failover between endpoints
- Configurable commitment levels
- Request batching for efficiency

### Rate Limiting
- DexScreener API: 300 requests per minute
- Solana RPC: Configurable based on endpoint
- Automatic backoff and retry mechanism

### Scoring System Optimization
- Caching of intermediate calculations
- Batch processing of historical data
- Efficient statistical computations
- Memory-optimized data structures

## Error Handling

The script includes comprehensive error handling:
- API request retries
- RPC connection management
- Database connection recovery
- Configuration validation
- Rate limit management
- Exception logging

## Monitoring

Real-time monitoring through:
- Telegram notifications
- Rotating log files
- Performance metrics
- Health checks

## Function Reference

### Core Classes

#### VirtuosoGemFinder
Main class that orchestrates the gem finding process.

- `__init__(telegram_bot_token, telegram_chat_id)`: Initializes the gem finder with Telegram credentials
- `scan_new_pairs()`: Main scanning loop that continuously monitors for new token pairs
- `_analyze_token(pair)`: Performs detailed analysis of a potential gem token
- `_handle_gem_discovery(metrics, score_data)`: Processes and notifies about discovered gems
- `_track_api_call(start_time, success)`: Tracks API performance metrics
- `_log_performance_metrics(operation, start_time)`: Logs detailed performance data
- `_setup_signal_handlers()`: Sets up graceful shutdown handlers
- `_setup_config_watcher()`: Implements hot-reloading of configuration
- `_analyze_volume_trend(pair_address)`: Analyzes volume trends across timeframes
- `_analyze_transaction_trend(pair)`: Analyzes transaction count trends

#### GemScorer
Handles the sophisticated scoring system for token evaluation.

- `calculate_score(metrics, historical_data)`: Calculates comprehensive gem score
- `_score_liquidity(liquidity)`: Evaluates liquidity with logarithmic scaling
- `_score_market_cap(mcap)`: Scores market cap with preference for smaller caps
- `_score_holders(holder_count)`: Analyzes holder count and distribution
- `_score_volume_trends(metrics)`: Evaluates volume trend patterns
- `_score_transaction_trends(metrics)`: Evaluates transaction trend patterns
