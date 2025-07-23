#!/bin/bash

# Whale Discovery Curl Test Script
# Test various Birdeye API endpoints for whale discovery

# Configuration
API_KEY="${BIRDEYE_API_KEY}"
BASE_URL="https://public-api.birdeye.so"
CHAIN="solana"

# Test tokens (Wrapped SOL, Bonk, etc.)
WSOL="So11111111111111111111111111111111111111112"
MSOL="mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So"
BONK="DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"

echo "🐋 WHALE DISCOVERY CURL TESTING SCRIPT"
echo "======================================"

if [ -z "$API_KEY" ]; then
    echo "❌ Error: BIRDEYE_API_KEY environment variable not set"
    echo "Please set your API key: export BIRDEYE_API_KEY=your_key_here"
    exit 1
fi

echo "✅ API Key found: ${API_KEY:0:8}..."
echo ""

# Test 1: Get Top Traders for Wrapped SOL
echo "1️⃣ Testing Top Traders endpoint..."
echo "GET ${BASE_URL}/defi/v2/tokens/top_traders"
echo ""

curl -X GET "${BASE_URL}/defi/v2/tokens/top_traders?address=${WSOL}" \
  -H "x-chain: ${CHAIN}" \
  -H "X-API-KEY: ${API_KEY}" \
  -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
  -s | jq '.' 2>/dev/null || echo "Response received (jq not available for formatting)"

echo -e "\n" && sleep 2

# Test 2: Get Token Holders
echo "2️⃣ Testing Token Holders endpoint..."
echo "GET ${BASE_URL}/defi/token_holder"
echo ""

curl -X GET "${BASE_URL}/defi/token_holder?address=${WSOL}" \
  -H "x-chain: ${CHAIN}" \
  -H "X-API-KEY: ${API_KEY}" \
  -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
  -s | jq '.data.items[:3]' 2>/dev/null || echo "Response received (showing top 3 holders)"

echo -e "\n" && sleep 2

# Test 3: Get Top Gaining Traders
echo "3️⃣ Testing Trader Gainers endpoint..."
echo "GET ${BASE_URL}/defi/v2/trader_gainers_losers"
echo ""

curl -X GET "${BASE_URL}/defi/v2/trader_gainers_losers?type=gainers&offset=0&limit=5" \
  -H "x-chain: ${CHAIN}" \
  -H "X-API-KEY: ${API_KEY}" \
  -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
  -s | jq '.data[:3]' 2>/dev/null || echo "Response received (showing top 3 gainers)"

echo -e "\n" && sleep 2

# Test 4: Get High-Volume Tokens
echo "4️⃣ Testing Token List endpoint for whale analysis..."
echo "GET ${BASE_URL}/defi/v3/token/list"
echo ""

curl -X GET "${BASE_URL}/defi/v3/token/list?sort_by=volume_24h_usd&sort_type=desc&min_liquidity=1000000&limit=5" \
  -H "x-chain: ${CHAIN}" \
  -H "X-API-KEY: ${API_KEY}" \
  -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
  -s | jq '.data.tokens[:3] | .[] | {symbol, volume_24h: .volume.h24, liquidity}' 2>/dev/null || echo "Response received (showing top volume tokens)"

echo -e "\n" && sleep 2

# Test 5: Example Wallet Portfolio Analysis
echo "5️⃣ Testing Wallet Portfolio endpoint..."
echo "GET ${BASE_URL}/defi/wallet_portfolio"
echo "Note: This will likely fail without a real wallet address"
echo ""

EXAMPLE_WALLET="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
curl -X GET "${BASE_URL}/defi/wallet_portfolio?wallet=${EXAMPLE_WALLET}" \
  -H "x-chain: ${CHAIN}" \
  -H "X-API-KEY: ${API_KEY}" \
  -w "\n\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
  -s | jq '.data | {totalValueUsd, realizedPnl, unrealizedPnl}' 2>/dev/null || echo "Response received (wallet portfolio data)"

echo -e "\n"

echo "🎯 WHALE DISCOVERY STRATEGY:"
echo "=========================="
echo "1. Use token/list to find high-volume tokens"
echo "2. Get top_traders for each high-volume token"
echo "3. Get token_holder for large position holders"
echo "4. Use trader_gainers_losers for performance data"
echo "5. Validate each wallet with wallet_portfolio"
echo "6. Filter by success rate, position size, and activity"
echo ""

echo "✅ Curl testing complete!"
echo "Run the Python script for automated whale discovery:"
echo "python scripts/discover_whales.py" 