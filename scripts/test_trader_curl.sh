#!/bin/bash

# Birdeye API Trader Discovery Testing Script
# Tests all major trader-related endpoints for finding top performers

echo "🔍 BIRDEYE API TRADER DISCOVERY TESTING"
echo "========================================"

# Check if API key is available
if [ -z "$BIRDEYE_API_KEY" ]; then
    echo "⚠️  Warning: BIRDEYE_API_KEY not set. Some endpoints may be limited."
    echo "   Set it with: export BIRDEYE_API_KEY='your_api_key'"
fi

# Base URL and headers
BASE_URL="https://public-api.birdeye.so"
HEADERS="-H 'Accept: application/json'"

if [ ! -z "$BIRDEYE_API_KEY" ]; then
    HEADERS="$HEADERS -H 'X-API-Key: $BIRDEYE_API_KEY'"
fi

echo ""
echo "🚀 Testing Trader Discovery Endpoints"
echo "======================================"

# 1. Top Gainers/Losers - Primary trader discovery endpoint
echo ""
echo "1️⃣  TESTING: Trader Gainers/Losers (24h)"
echo "Endpoint: /trader/gainers-losers"
echo "Command:"
echo "curl -X GET '$BASE_URL/trader/gainers-losers?time_frame=24h&sort_type=desc&sort_by=pnl&limit=10' $HEADERS"
echo ""
echo "Response:"
eval "curl -X GET '$BASE_URL/trader/gainers-losers?time_frame=24h&sort_type=desc&sort_by=pnl&limit=10' $HEADERS" | jq '.' 2>/dev/null || echo "❌ Failed to fetch gainers/losers"

echo ""
echo "2️⃣  TESTING: Trader Gainers/Losers (7d)"
echo "Endpoint: /trader/gainers-losers"
echo "Command:"
echo "curl -X GET '$BASE_URL/trader/gainers-losers?time_frame=7d&sort_type=desc&sort_by=pnl&limit=10' $HEADERS"
echo ""
echo "Response:"
eval "curl -X GET '$BASE_URL/trader/gainers-losers?time_frame=7d&sort_type=desc&sort_by=pnl&limit=10' $HEADERS" | jq '.' 2>/dev/null || echo "❌ Failed to fetch 7d gainers/losers"

# 2. Top Traders for Specific Tokens
echo ""
echo "3️⃣  TESTING: Top Traders for SOL Token"
echo "Endpoint: /defi/v2/tokens/top_traders"
echo "Command:"
SOL_ADDRESS="So11111111111111111111111111111111111111112"
echo "curl -X GET '$BASE_URL/defi/v2/tokens/top_traders?address=$SOL_ADDRESS&time_frame=24h&sort_by=volume&limit=10' $HEADERS"
echo ""
echo "Response:"
eval "curl -X GET '$BASE_URL/defi/v2/tokens/top_traders?address=$SOL_ADDRESS&time_frame=24h&sort_by=volume&sort_type=desc&limit=10' $HEADERS" | jq '.' 2>/dev/null || echo "❌ Failed to fetch SOL top traders"

# 3. Get trending tokens to find more active traders
echo ""
echo "4️⃣  TESTING: Trending Tokens (for trader discovery)"
echo "Endpoint: /defi/tokenlist"
echo "Command:"
echo "curl -X GET '$BASE_URL/defi/tokenlist?sort_by=v24hUSD&sort_type=desc&limit=5' $HEADERS"
echo ""
echo "Response:"
eval "curl -X GET '$BASE_URL/defi/tokenlist?sort_by=v24hUSD&sort_type=desc&limit=5' $HEADERS" | jq '.data.tokens[] | {address: .address, symbol: .symbol, volume24h: .v24hUSD}' 2>/dev/null || echo "❌ Failed to fetch trending tokens"

# 4. Wallet Portfolio Analysis (for trader evaluation)
echo ""
echo "5️⃣  TESTING: Wallet Portfolio Analysis"
echo "Endpoint: /wallet/portfolio"
echo "Note: Using a known whale wallet for demonstration"
WHALE_WALLET="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
echo "Command:"
echo "curl -X GET '$BASE_URL/wallet/portfolio?wallet=$WHALE_WALLET' $HEADERS"
echo ""
echo "Response:"
eval "curl -X GET '$BASE_URL/wallet/portfolio?wallet=$WHALE_WALLET' $HEADERS" | jq '{totalValueUsd: .data.totalValueUsd, items: .data.items | length}' 2>/dev/null || echo "❌ Failed to fetch wallet portfolio"

# 5. Wallet Transaction History (for performance analysis)
echo ""
echo "6️⃣  TESTING: Wallet Transaction History"
echo "Endpoint: /wallet/transaction-history"
echo "Command:"
echo "curl -X GET '$BASE_URL/wallet/transaction-history?wallet=$WHALE_WALLET&limit=5' $HEADERS"
echo ""
echo "Response:"
eval "curl -X GET '$BASE_URL/wallet/transaction-history?wallet=$WHALE_WALLET&limit=5' $HEADERS" | jq '.data.items | length' 2>/dev/null || echo "❌ Failed to fetch transaction history"

echo ""
echo "🔬 ADVANCED TRADER DISCOVERY WORKFLOW"
echo "====================================="

echo ""
echo "7️⃣  WORKFLOW: Find Top Traders from High-Volume Token"
echo ""

# Get a high-volume token
echo "Step 1: Get top volume token..."
TOP_TOKEN=$(eval "curl -s -X GET '$BASE_URL/defi/tokenlist?sort_by=v24hUSD&sort_type=desc&limit=1' $HEADERS" | jq -r '.data.tokens[0].address' 2>/dev/null)

if [ "$TOP_TOKEN" != "null" ] && [ ! -z "$TOP_TOKEN" ]; then
    echo "Found top token: $TOP_TOKEN"
    
    echo ""
    echo "Step 2: Get top traders for this token..."
    echo "Command:"
    echo "curl -X GET '$BASE_URL/defi/v2/tokens/top_traders?address=$TOP_TOKEN&time_frame=24h&sort_by=volume&limit=5' $HEADERS"
    echo ""
    echo "Response:"
    eval "curl -X GET '$BASE_URL/defi/v2/tokens/top_traders?address=$TOP_TOKEN&time_frame=24h&sort_by=volume&sort_type=desc&limit=5' $HEADERS" | jq '.data.items[] | {owner: .owner, volume: .volume, trades: .trade}' 2>/dev/null || echo "❌ Failed to fetch token traders"
else
    echo "❌ Could not fetch top token for workflow"
fi

echo ""
echo "📊 PERFORMANCE ANALYSIS WORKFLOW"
echo "================================"

echo ""
echo "8️⃣  WORKFLOW: Analyze Specific Trader Performance"
echo ""

# Get a trader from gainers
echo "Step 1: Get top gainer trader..."
TOP_TRADER=$(eval "curl -s -X GET '$BASE_URL/trader/gainers-losers?time_frame=24h&sort_type=desc&sort_by=pnl&limit=1' $HEADERS" | jq -r '.data.gainers[0].wallet' 2>/dev/null)

if [ "$TOP_TRADER" != "null" ] && [ ! -z "$TOP_TRADER" ]; then
    echo "Found top trader: $TOP_TRADER"
    
    echo ""
    echo "Step 2: Analyze trader portfolio..."
    echo "Command:"
    echo "curl -X GET '$BASE_URL/wallet/portfolio?wallet=$TOP_TRADER' $HEADERS"
    echo ""
    echo "Response:"
    eval "curl -X GET '$BASE_URL/wallet/portfolio?wallet=$TOP_TRADER' $HEADERS" | jq '{
             totalValue: .data.totalValueUsd,
             tokenCount: (.data.items | length),
             topHoldings: .data.items[0:3] | map({symbol: .symbol, value: .valueUsd})
         }' 2>/dev/null || echo "❌ Failed to analyze trader portfolio"
else
    echo "❌ Could not fetch top trader for analysis"
fi

echo ""
echo "💡 TRADER DISCOVERY SUMMARY"
echo "==========================="
echo ""
echo "✅ Key Endpoints for Finding Best Traders:"
echo "   1. /trader/gainers-losers - Primary discovery (24h, 7d performance)"
echo "   2. /defi/v2/tokens/top_traders - Token-specific top traders"
echo "   3. /defi/tokenlist - Find high-volume tokens for trader mining"
echo "   4. /wallet/portfolio - Analyze trader holdings and value"
echo "   5. /wallet/transaction-history - Detailed trade analysis"
echo ""
echo "🎯 Recommended Workflow:"
echo "   1. Use /trader/gainers-losers for 24h and 7d top performers"
echo "   2. Cross-reference with /defi/v2/tokens/top_traders from high-volume tokens"
echo "   3. Analyze each trader with /wallet/portfolio"
echo "   4. Calculate performance metrics from transaction history"
echo "   5. Rank by PnL, ROI, win rate, and risk-adjusted returns"
echo ""
echo "🔧 Usage Examples:"
echo "   # Find 24h top gainers"
echo "   python scripts/discover_top_traders.py --timeframe 24h --max-traders 20"
echo ""
echo "   # Find 7d top performers"
echo "   python scripts/discover_top_traders.py --timeframe 7d --max-traders 20"
echo ""
echo "   # Compare 24h vs 7d consistency"
echo "   python scripts/discover_top_traders.py --compare"
echo ""
echo "   # Analyze specific trader"
echo "   python scripts/discover_top_traders.py --analyze-trader 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
echo ""
echo "📁 Data Storage: Check data/trader_performance/ for cached results"
echo ""
echo "✅ Trader discovery testing completed!" 