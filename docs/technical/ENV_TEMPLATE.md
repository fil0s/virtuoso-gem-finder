# Environment Configuration Template

Copy the content below to create your `.env` file in the project root directory.

```bash
# ====================================================================================
# EARLY TOKEN MONITOR ENVIRONMENT CONFIGURATION TEMPLATE
# ====================================================================================
# Copy this file to .env and fill in your actual values
# DO NOT commit the .env file to version control

# ====================================================================================
# CORE API CREDENTIALS
# ====================================================================================

# Birdeye API Configuration (Primary API for token data)
BIRDEYE_API_KEY=your_birdeye_api_key_here

# Helius API Configuration (Solana RPC and additional data)
HELIUS_API_KEY=your_helius_api_key_here

# ====================================================================================
# TELEGRAM ALERT CONFIGURATION
# ====================================================================================

# Telegram Bot Configuration (Required for alerts)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# ====================================================================================
# SOLANA NETWORK CONFIGURATION
# ====================================================================================

# Solana RPC Endpoint (can use default or custom)
SOLANA_RPC_ENDPOINT=https://api.mainnet-beta.solana.com

# Whale Tracking RPC URL (if using Helius)
WHALE_TRACKING_RPC_URL=https://mainnet.helius-rpc.com/?api-key=your_helius_api_key_here

# ====================================================================================
# EARLY TOKEN DETECTION SETTINGS (Optional - Override config.yaml)
# ====================================================================================

# Scan Configuration
# EARLY_DETECTION_SCAN_INTERVAL=20    # Minutes between scans
# EARLY_DETECTION_MAX_TOKENS=30       # Max tokens to analyze per scan
# EARLY_DETECTION_MIN_SCORE=70        # Minimum score threshold for alerts

# ====================================================================================
# EXTERNAL API SETTINGS
# ====================================================================================

# Jupiter API Settings
JUPITER_TIMEOUT_SECONDS=10

# DexScreener API Settings
DEXSCREENER_RATE_LIMIT=300

# ====================================================================================
# DATABASE CONFIGURATION (Optional)
# ====================================================================================

# Database settings (if using external database)
# DB_NAME=early_token_monitor
# DB_USER=your_db_user
# DB_PASSWORD=your_db_password
# DB_HOST=localhost
# DB_PORT=5432

# ====================================================================================
# CACHING CONFIGURATION (Optional)
# ====================================================================================

# Redis URL for advanced caching (if enabled)
# CACHING_REDIS_URL=redis://localhost:6379/0

# ====================================================================================
# LOGGING CONFIGURATION (Optional)
# ====================================================================================

# Logging settings (override config.yaml)
# LOG_LEVEL=INFO
# LOG_FILE=logs/monitor.log

# ====================================================================================
# LEGACY/BACKUP CREDENTIALS
# ====================================================================================

# Legacy Helius API Keys (for backward compatibility)
# HELIUS_API_KEY_LEGROOT=your_legroot_api_key_here
# HELIUS_API_KEY_GEMNOON=your_gemnoon_api_key_here
```

## Setup Instructions

### 1. Birdeye API Setup
- Sign up at [Birdeye Documentation](https://docs.birdeye.so/)
- Get your API key from the dashboard
- Replace `your_birdeye_api_key_here` with your actual key

### 2. Telegram Bot Setup
- **Create a bot**: Message [@BotFather](https://t.me/BotFather) on Telegram
- Send `/newbot` and follow instructions
- Copy the bot token to `TELEGRAM_BOT_TOKEN`
- **Get your chat ID**: Message [@userinfobot](https://t.me/userinfobot) or check your chat
- Replace `your_telegram_chat_id_here` with your chat ID

### 3. Helius Setup (Optional)
- Sign up at [Helius](https://helius.xyz/)
- Get your API key for enhanced Solana data
- Replace `your_helius_api_key_here` with your actual key

### 4. Testing Your Setup
```bash
# Run the monitor
python3 monitor.py

# Check that:
# - APIs connect successfully
# - Telegram alerts work (if enabled)
# - Configuration loads properly
```

### 5. Environment Variables Priority

The system uses this priority order for configuration:
1. Environment variables (`.env` file)
2. Configuration file (`config/config.yaml`)
3. Default values

### 6. Security Notes

- **Never commit your `.env` file** to version control
- Keep your API keys secure and private
- Regularly rotate your API keys for security
- Use environment-specific configurations for different deployments

### 7. Required vs Optional Variables

**Required for basic functionality:**
- `BIRDEYE_API_KEY`

**Required for Telegram alerts:**
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

**Optional (have defaults):**
- All other variables can use system defaults 