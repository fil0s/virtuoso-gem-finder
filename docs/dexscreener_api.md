# DexScreener API Documentation

## Overview

This document outlines the data structures and responses from the DexScreener API as implemented in the Virtuoso Gem Finder. The DexScreener API is used to fetch information about trading pairs and tokens on various blockchains, with our implementation focusing on Solana.

## API Implementation

The API is implemented in `services/dexscreener_api.py` and includes several methods:

- `get_solana_pairs()`: Fetches a list of Solana trading pairs
- `get_pair_details(pair_address)`: Gets detailed information about a specific trading pair
- `get_token_info(token_addresses)`: Retrieves information about specific tokens

## Rate Limiting

The implementation includes a token bucket-based rate limiting system:

- Default rate limit: 300 requests per minute
- Automatic backoff and retry mechanism with exponential wait times
- Retry limit: 3 attempts per request

## Response Data Structures

### Solana Trading Pairs (`get_solana_pairs()`)

Returns a list of trading pairs for Solana tokens.

```typescript
interface SolanaPair {
  chainId: string;            // Blockchain identifier (e.g., "solana")
  dexId: string;              // DEX identifier (e.g., "raydium", "orca")
  pairAddress: string;        // Unique identifier for the trading pair
  baseToken: {
    address: string;          // Token contract address
    name: string;             // Token name
    symbol: string;           // Token symbol
  };
  quoteToken: {
    address: string;          // Token contract address
    name: string;             // Token name
    symbol: string;           // Token symbol
  };
  priceUsd: string;           // Current price in USD
  priceNative: string;        // Price in native blockchain currency
  liquidity: {
    usd: number;              // Liquidity in USD
    base: number;             // Liquidity in base token
    quote: number;            // Liquidity in quote token
  };
  volume: {
    h24: number;              // 24-hour volume in USD
  };
  priceChange: {
    h1: number;               // 1-hour price change percentage
    h24: number;              // 24-hour price change percentage
    h7d: number;              // 7-day price change percentage
  };
  txns: {
    h1: {                     // 1-hour transactions
      buys: number;
      sells: number;
    },
    h24: {                    // 24-hour transactions
      buys: number;
      sells: number;
    }
  };
  fdv: number;                // Fully Diluted Valuation
  pairCreatedAt: number;      // Unix timestamp of pair creation
}
```

### Pair Details (`get_pair_details(pair_address)`)

Returns detailed information about a specific trading pair.

```typescript
interface PairDetails {
  chainId: string;            // Blockchain identifier
  dexId: string;              // DEX identifier
  pairAddress: string;        // Unique identifier for the trading pair
  baseToken: {
    address: string;          // Token contract address
    name: string;             // Token name
    symbol: string;           // Token symbol
  };
  quoteToken: {
    address: string;          // Token contract address
    name: string;             // Token name
    symbol: string;           // Token symbol
  };
  priceUsd: string;           // Current price in USD
  priceNative: string;        // Price in native blockchain currency
  liquidity: {
    usd: number;              // Liquidity in USD
    base: number;             // Base token liquidity
    quote: number;            // Quote token liquidity
  };
  volume: {
    h1: number;               // 1-hour volume in USD
    h6: number;               // 6-hour volume in USD
    h24: number;              // 24-hour volume in USD
  };
  priceChange: {
    h1: number;               // 1-hour price change percentage
    h6: number;               // 6-hour price change percentage
    h24: number;              // 24-hour price change percentage
    h7d: number;              // 7-day price change percentage
  };
  txns: {
    h1: {                     // 1-hour transactions
      buys: number;
      sells: number;
    },
    h6: {                     // 6-hour transactions
      buys: number;
      sells: number;
    },
    h24: {                    // 24-hour transactions
      buys: number;
      sells: number;
    }
  };
  fdv: number;                // Fully Diluted Valuation
  pairCreatedAt: number;      // Unix timestamp of pair creation
}
```

### Token Information (`get_token_info(token_addresses)`)

Returns information about specific tokens, including pairs they're traded in.

```typescript
interface TokenInfo {
  chainId: string;            // Blockchain identifier
  dexId: string;              // DEX identifier
  pairAddress: string;        // Pair address where token is traded
  baseToken: {
    address: string;          // Token contract address
    name: string;             // Token name
    symbol: string;           // Token symbol
  };
  quoteToken: {
    address: string;          // Token contract address
    name: string;             // Token name
    symbol: string;           // Token symbol
  };
  priceUsd: string;           // Current price in USD
  liquidity: {
    usd: number;              // Liquidity in USD
  };
  volume: {
    h24: number;              // 24-hour volume in USD
  };
  txns: {
    h24: {                    // 24-hour transactions
      buys: number;
      sells: number;
    }
  };
}
```

## Usage Examples

### Fetching Solana Pairs

```python
from services.dexscreener_api import DexScreenerAPI

dex_api = DexScreenerAPI()
pairs = dex_api.get_solana_pairs()

# Example: Print pair information
for pair in pairs[:3]:
    print(f"Pair: {pair.get('baseToken', {}).get('symbol')}/{pair.get('quoteToken', {}).get('symbol')}")
    print(f"Price: ${pair.get('priceUsd')}")
    print(f"Liquidity: ${pair.get('liquidity', {}).get('usd')}")
```

### Getting Pair Details

```python
pair_address = "9ndJDvDYQyBDx7KBH3hvp47oCUafAdUEb8xP1ERehmVx"
pair_details = dex_api.get_pair_details(pair_address)

if pair_details:
    print(f"Token: {pair_details.get('baseToken', {}).get('symbol')}")
    print(f"Price: ${pair_details.get('priceUsd')}")
    print(f"24h Change: {pair_details.get('priceChange', {}).get('h24')}%")
    print(f"24h Volume: ${pair_details.get('volume', {}).get('h24')}")
```

### Retrieving Token Information

```python
token_addresses = ["fESbUKjuMY6jzDH9VP8cy4p3pu2q5W2rK2XghVfNseP"]
tokens_info = dex_api.get_token_info(token_addresses)

for token_info in tokens_info:
    print(f"Token: {token_info.get('baseToken', {}).get('symbol')}")
    print(f"DEX: {token_info.get('dexId')}")
    print(f"Price: ${token_info.get('priceUsd')}")
```

## API Endpoints

The implementation uses the following DexScreener API endpoints:

1. `/search?q=solana` - Fetches Solana trading pairs
2. `/pairs/solana/{pair_address}` - Gets details for a specific pair
3. `/tokens/{addresses}` - Retrieves information about specific tokens

## Error Handling

The implementation includes robust error handling:

- Retry mechanism for failed requests
- Timeout handling (10-second timeout for all requests)
- Error logging with detailed error messages
- Fallback return values if API calls fail

## Notes on Solana Addresses

A valid Solana address:
- Is typically 32-44 characters long
- Contains only Base58 characters (`123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz`)
- Many DexScreener pairs may not return valid Solana addresses as their `pairAddress` fields
- Token addresses are more likely to be valid Solana addresses 