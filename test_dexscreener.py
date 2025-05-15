#!/usr/bin/env python3
"""
Test script for DexScreener API
"""

import sys
import json
from services.dexscreener_api import DexScreenerAPI

def print_json(data):
    """Print JSON data in a readable format"""
    print(json.dumps(data, indent=2))

def is_valid_solana_address(address):
    """Check if an address looks like a valid Solana address"""
    # Basic check - most Solana addresses are base58-encoded and ~32-44 chars
    if not address:
        return False
    
    # Check if it's a valid length for a Solana address
    if len(address) < 32 or len(address) > 44:
        return False
        
    # Check if it contains only base58 characters
    allowed_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    return all(c in allowed_chars for c in address)

def test_dexscreener_api():
    """Test the DexScreener API implementation"""
    print("Initializing DexScreener API...")
    dex_api = DexScreenerAPI()
    
    print("\n--- Testing get_solana_pairs() ---")
    print("Fetching Solana pairs...")
    pairs = dex_api.get_solana_pairs()
    print(f"Fetched {len(pairs)} pairs")
    
    if pairs:
        # Print the first 3 pairs
        print("\nSample pairs (first 3):")
        for i, pair in enumerate(pairs[:3]):
            print(f"\nPair {i+1}:")
            print(f"Pair Address: {pair.get('pairAddress')}")
            print(f"Base Token: {pair.get('baseToken', {}).get('symbol')}")
            print(f"Quote Token: {pair.get('quoteToken', {}).get('symbol')}")
            print(f"Price USD: ${pair.get('priceUsd', 'N/A')}")
            print(f"Liquidity USD: ${pair.get('liquidity', {}).get('usd', 'N/A')}")
        
        # Find a valid Solana pair address for testing
        valid_pair_address = None
        for pair in pairs:
            pair_address = pair.get('pairAddress')
            if is_valid_solana_address(pair_address):
                valid_pair_address = pair_address
                break
                
        if valid_pair_address:
            print(f"\n--- Testing get_pair_details() for {valid_pair_address} ---")
            pair_details = dex_api.get_pair_details(valid_pair_address)
            if pair_details:
                print("Pair details:")
                print(f"Pair Created At: {pair_details.get('pairCreatedAt', 'N/A')}")
                print(f"Price: ${pair_details.get('priceUsd', 'N/A')}")
                print(f"Price Change 24h: {pair_details.get('priceChange', {}).get('h24', 'N/A')}%")
                print(f"Volume 24h: ${pair_details.get('volume', {}).get('h24', 'N/A')}")
            else:
                print("Failed to fetch pair details")
        else:
            print("\nNo valid Solana pair address found for testing get_pair_details()")
        
        # Find valid token addresses for testing
        valid_token_addresses = []
        for pair in pairs:
            base_token_address = pair.get('baseToken', {}).get('address')
            if is_valid_solana_address(base_token_address) and base_token_address not in valid_token_addresses:
                valid_token_addresses.append(base_token_address)
                if len(valid_token_addresses) >= 3:
                    break
        
        if valid_token_addresses:
            print(f"\n--- Testing get_token_info() for {len(valid_token_addresses)} valid Solana addresses ---")
            print(f"Token addresses: {valid_token_addresses}")
            tokens_info = dex_api.get_token_info(valid_token_addresses)
            print(f"Fetched info for {len(tokens_info)} tokens")
            
            if tokens_info:
                print("\nSample token info (first one):")
                token = tokens_info[0]
                print(f"Token: {token.get('baseToken', {}).get('symbol')}")
                print(f"DEX: {token.get('dexId')}")
                print(f"Pair Address: {token.get('pairAddress')}")
        else:
            print("\nNo valid Solana token addresses found for testing get_token_info()")
    else:
        print("No pairs returned from the API")

if __name__ == "__main__":
    try:
        test_dexscreener_api()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 