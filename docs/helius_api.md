# Helius API Documentation

## Overview

This document outlines the Helius API integration in the Virtuoso Gem Finder. Helius is a Solana RPC provider that offers enhanced data features, including detailed token information, holder metrics, transaction history, and on-chain analytics.

## API Implementation

The API is implemented in `api/helius_connector.py` and provides the following core functionality:

- Token metadata retrieval
- Token holder counts and historical tracking
- Transaction count analysis
- Wallet behavior classification

## API Keys and Environment Variables

The Helius API requires an API key, which is managed through environment variables:

```
HELIUS_API_KEY_LEGROOT=your_legroot_api_key_here
HELIUS_API_KEY_GEMNOON=your_gemnoon_api_key_here
```

These keys can be set in a `.env` file at the project root, which will be loaded automatically by the `utils/env_loader.py` module.

> **Important**: Some endpoints may return 401 Unauthorized or 404 Not Found errors if your API key doesn't have the required permissions or if the endpoints have been updated. Check the [Helius API documentation](https://docs.helius.xyz/) for the latest endpoints and required permissions.

## API Methods

### Token Metadata

```python
def get_token_metadata(mint_address: str) -> Optional[Dict]
```

Retrieves detailed metadata for a token, including name, symbol, decimals, and possibly supply information.

### Token Holders

```python
def get_token_holders(mint_address: str, limit: int = 100) -> Optional[List[Dict]]
```

Gets a list of token holders with their balances, up to the specified limit.

### Holder Count

```python
def get_current_holder_count(token_mint: str) -> Optional[int]
```

Gets the current number of holders for a token.

### Historical Holder Counts

```python
def get_historical_holder_counts(token_mint: str, days: int = 30) -> Optional[List[Dict[str, Any]]]
```

Retrieves historical holder count data over a period of days (currently a placeholder implementation).

### Transaction Count

```python
def get_transaction_count_for_token(token_mint: str, days: int = 1) -> Optional[int]
```

Gets the number of transactions involving a specific token over a period of days.

### Transaction History

```python
def get_transaction_history(address: str, type: str = "TOKEN", limit: int = 100) -> Optional[List[Dict]]
```

Retrieves detailed transaction history for an address, with optional type filtering.

### Wallet Type Analysis

```python
def get_wallet_type(address: str) -> Optional[str]
```

Analyzes a wallet's behavior and categorizes it (e.g., trader, holder, inactive).

## Response Data Structures

### Token Metadata

```typescript
interface TokenMetadata {
  mint: string;          // Token mint address
  decimals: number;      // Token decimals
  supply: string;        // Total supply in smallest units
  symbol: string;        // Token symbol
  name: string;          // Token name
  iconURL?: string;      // Optional icon URL
  offChainData?: {       // Additional data from external sources
    holderCount?: number; // Optional holder count if available
    website?: string;    // Official website
    twitter?: string;    // Twitter handle
    // Other metadata fields may be present
  }
}
```

### Token Holder

```typescript
interface TokenHolder {
  account: string;       // Account address holding tokens
  amount: string;        // Token amount in smallest units
  delegatedAmount?: string; // Delegated amount if applicable
  delegatedTo?: string;  // Delegation recipient if applicable
}
```

### Transaction

```typescript
interface Transaction {
  signature: string;     // Transaction signature
  timestamp: number;     // Unix timestamp
  type: string;          // Transaction type (e.g. "TOKEN", "NFT", "SOL")
  fee: number;           // Transaction fee in lamports
  status: string;        // Transaction status
  actions: any[];        // Array of actions in the transaction
  tokenTransfers: any[]; // Token transfers involved in transaction
  nativeTransfers: any[]; // Native SOL transfers
  accountData: any[];    // Account data changes
  events: any[];         // Events emitted by the transaction
}
```

### Historical Holder Count

```typescript
interface HistoricalHolderCount {
  timestamp: number;     // Unix timestamp
  holderCount: number;   // Number of holders at that timestamp
}
```

## Usage Examples

### Loading Environment and Initializing API

```python
from utils.env_loader import load_environment, get_helius_api_key
from api.helius_connector import HeliusAPI

# Load environment variables from .env file
load_environment()

# Get the API key from environment
api_key = get_helius_api_key("LEGROOT")

# Initialize the API with the key
helius_api = HeliusAPI(api_key)
```

### Getting Token Metadata

```python
# WSOL mint address
wsol_mint = "So11111111111111111111111111111111111111112"

# Get token metadata
token_metadata = helius_api.get_token_metadata(wsol_mint)

if token_metadata:
    print(f"Symbol: {token_metadata.get('symbol')}")
    print(f"Name: {token_metadata.get('name')}")
    print(f"Decimals: {token_metadata.get('decimals')}")
```

### Getting Holder Count

```python
# Get current holder count
holder_count = helius_api.get_current_holder_count(wsol_mint)

if holder_count is not None:
    print(f"Current holder count: {holder_count}")
```

### Getting Transaction Count

```python
# Get transaction count for the last day
tx_count = helius_api.get_transaction_count_for_token(wsol_mint, days=1)

if tx_count is not None:
    print(f"Transaction count in the last 24 hours: {tx_count}")
```

### Analyzing Wallet Type

```python
# Analyze a wallet's behavior
wallet_address = "9pRJmsCWnWQ2krUAe1xBGdqVKYsHFEkvGHBCQTJCg2b3"
wallet_type = helius_api.get_wallet_type(wallet_address)

if wallet_type:
    print(f"Wallet classification: {wallet_type}")
```

## API Endpoints

The implementation uses the following Helius API endpoints:

1. `/tokens` - Fetches token metadata
2. `/token-accounts` - Gets token holder information
3. `/addresses/{address}/transactions` - Retrieves transaction history
4. `/token-metrics` - Gets token-related metrics

## Error Handling

The implementation includes robust error handling:

- Retry mechanism for failed requests using tenacity
- Detailed error logging
- Fallback return values (None, empty lists) when operations fail
- Optional parameters with sensible defaults

## Notes on Implementation

- Some methods like `get_historical_holder_counts` are currently placeholders that provide mock data
- Token holder count may be obtained from metadata or calculated using RPC calls if not available in metadata
- Wallet type analysis is simplified and would benefit from more sophisticated algorithms in production
- API keys can be rotated by updating the environment variables
- If you're experiencing 401 or 404 errors, ensure your API key is valid and has the necessary permissions 