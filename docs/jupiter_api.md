# Jupiter API Documentation

## Overview

This document outlines the Jupiter API integration in the Virtuoso Gem Finder. Jupiter is a key liquidity aggregator on Solana, providing access to token price data, swap quotes, and trading functionality. The implementation leverages the jupiter-python-sdk to access this data.

## API Implementation

The API is implemented in `api/jupiter_connector.py` and provides the following core functionality:

- Token price data in USD
- Token lists with metadata
- Swap quotes between token pairs
- Route maps for token trading pairs
- Historical price and volume data (placeholder implementation)

## Constants

```python
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC mint address
WSOL_MINT = "So11111111111111111111111111111111111111112"  # Wrapped SOL mint address
```

## API Methods

### Token List

```python
async def get_token_list() -> List[Dict]
```

Returns a comprehensive list of tokens supported by Jupiter, including their metadata.

### Token Price in USD

```python
async def get_token_price_usd(token_mint: str) -> Optional[float]
```

Gets the current price of a token in USD by querying against USDC.

### Swap Quote

```python
async def get_quote(input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50) -> Optional[Dict]
```

Retrieves a quote for swapping between two tokens, providing accurate price data and liquidity information.

### Indexed Route Map

```python
async def get_indexed_route_map() -> Optional[Dict]
```

Returns a map of which tokens can be swapped with each other, useful for understanding the available trading pairs.

### Swap Pairs

```python
async def get_swap_pairs(base_mint: str) -> Optional[List[Dict]]
```

Gets all tokens that can be traded with a specific token.

### Historical Prices (Placeholder)

```python
async def get_historical_prices(token_mint: str, timeframe: str, limit: int) -> Optional[List[Dict[str, Any]]]
```

Placeholder method for retrieving historical price data at specified intervals.

### Historical Volume (Placeholder)

```python
async def get_historical_volume(token_mint: str, timeframe: str, limit: int) -> Optional[List[Dict[str, Any]]]
```

Placeholder method for retrieving historical volume data at specified intervals.

## Response Data Structures

### Token List

```typescript
interface Token {
  address: string;         // Token mint address
  chainId: number;         // Chain ID (e.g., 101 for Solana mainnet)
  decimals: number;        // Number of decimal places
  name: string;            // Token name
  symbol: string;          // Token symbol
  logoURI?: string;        // Optional logo URL
  tags?: string[];         // Optional tags for categorization
  extensions?: {
    coingeckoId?: string;  // CoinGecko ID if available
    website?: string;      // Official website
    // Other extension fields may be present
  }
}
```

### Price Data

```typescript
interface PriceData {
  [tokenMint: string]: {
    id: string;            // Token mint address
    mintSymbol: string;    // Token symbol
    vsToken: string;       // Quote token mint address
    vsTokenSymbol: string; // Quote token symbol
    price: number;         // Price in quote token
  }
}
```

### Swap Quote

```typescript
interface SwapQuote {
  inputMint: string;       // Input token mint address
  outputMint: string;      // Output token mint address
  inAmount: string;        // Input amount in smallest units
  outAmount: string;       // Output amount in smallest units
  otherAmountThreshold: string; // Minimum output with slippage
  swapMode: string;        // Jupiter swap mode
  slippageBps: number;     // Slippage tolerance in basis points
  priceImpactPct: number;  // Price impact percentage
  routePlan: Route[];      // Array of routes to execute
  contextSlot: number;     // Current slot context
  timeTaken: number;       // Time taken to compute quote
}

interface Route {
  srcMint: string;     // Source token mint
  dstMint: string;     // Destination token mint
  marketInfos: any[];  // Market information for this leg
}
```

### Route Map

```typescript
interface RouteMap {
  [tokenMint: string]: string[];  // Maps token mint to array of tradeable token mints
}
```

### Swap Pairs

```typescript
interface SwapPair {
  id: string;           // Token mint address
  mintSymbol: string;   // Token symbol
  decimals: number;     // Token decimals
  vsToken: string;      // Quote token mint address
  vsTokenSymbol: string;// Quote token symbol
  price: number;        // Current price
}
```

### Historical Price Data (Placeholder)

```typescript
interface HistoricalPrice {
  timestamp: number;    // Unix timestamp
  price: number;        // Price at that timestamp
}
```

### Historical Volume Data (Placeholder)

```typescript
interface HistoricalVolume {
  timestamp: number;    // Unix timestamp
  volume: number;       // Volume traded at that timestamp
}
```

## Usage Examples

### Fetching Token List

```python
from api.jupiter_connector import JupiterAPI

# Initialize with a Solana RPC endpoint
jupiter_api = JupiterAPI("https://api.mainnet-beta.solana.com")

# Get the token list
tokens = await jupiter_api.get_token_list()
print(f"Retrieved {len(tokens)} tokens")

# Example: Find a specific token by symbol
sol_token = next((t for t in tokens if t.get('symbol') == 'SOL'), None)
if sol_token:
    print(f"SOL mint address: {sol_token.get('address')}")
```

### Getting Token Price

```python
from api.jupiter_connector import JupiterAPI, WSOL_MINT

jupiter_api = JupiterAPI("https://api.mainnet-beta.solana.com")

# Get SOL price in USD
sol_price = await jupiter_api.get_token_price_usd(WSOL_MINT)
print(f"SOL Price: ${sol_price}")
```

### Fetching a Swap Quote

```python
from api.jupiter_connector import JupiterAPI, WSOL_MINT, USDC_MINT

jupiter_api = JupiterAPI("https://api.mainnet-beta.solana.com")

# Get a quote for swapping 0.1 SOL to USDC
quote = await jupiter_api.get_quote(
    input_mint=WSOL_MINT,
    output_mint=USDC_MINT,
    amount=100000000  # 0.1 SOL in lamports
)

if quote:
    print(f"0.1 SOL = {int(quote.get('outAmount')) / 1000000} USDC")
    print(f"Price Impact: {quote.get('priceImpactPct')}%")
```

## Notes on Implementation

- The JupiterAPI class requires a valid Solana RPC endpoint.
- No private key is needed as we only use read-only operations.
- Historical price and volume methods are currently placeholders and return mocked data for testing.
- For production use, these methods should be implemented using actual data sources such as Jupiter's Strict API or external price oracles.
- Remember to close the connection with `await jupiter_api.close()` when done to prevent resource leaks.

## Dependencies

- `jupiter_python_sdk`: The official Jupiter Python SDK
- `solana.rpc.async_api`: For Solana RPC communication
- `solders.pubkey`: For handling Solana public keys

## Error Handling

The implementation includes robust error handling with:

- Try/catch blocks around API calls
- Detailed error logging
- Fallback return values (empty lists, None) when operations fail
- All methods properly documented with return types that include `Optional` to indicate possible failure 