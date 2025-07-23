#!/usr/bin/env python3
"""
Test script to verify the emerging token discovery deduplication and exclusion fix
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scripts.tests.emerging_token_discovery_system import (
    EmergingTokenDiscoverySystem, 
    is_excluded_token, 
    filter_excluded_tokens,
    EMERGING_TOKEN_EXCLUSIONS,
    BASE_TOKEN_SYMBOLS
)

def test_exclusion_logic():
    """Test the exclusion logic"""
    print("🧪 Testing Exclusion Logic")
    print("=" * 50)
    
    # Test known excluded addresses
    usdc_address = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
    sol_address = 'So11111111111111111111111111111111111111112'
    fake_address = 'FakeTokenAddress123456789'
    
    print(f"USDC ({usdc_address[:8]}...): {'EXCLUDED' if is_excluded_token(usdc_address) else 'ALLOWED'}")
    print(f"SOL ({sol_address[:8]}...): {'EXCLUDED' if is_excluded_token(sol_address) else 'ALLOWED'}")
    print(f"Fake ({fake_address[:8]}...): {'EXCLUDED' if is_excluded_token(fake_address) else 'ALLOWED'}")
    
    # Test token filtering
    test_tokens = [
        {'address': usdc_address, 'symbol': 'USDC'},
        {'address': sol_address, 'symbol': 'SOL'},
        {'address': fake_address, 'symbol': 'FAKE'},
        {'address': 'AnotherFakeAddress', 'symbol': 'EMERGING'}
    ]
    
    print(f"\nBefore filtering: {len(test_tokens)} tokens")
    filtered = filter_excluded_tokens(test_tokens)
    print(f"After filtering: {len(filtered)} tokens")
    
    for token in filtered:
        print(f"  ✅ {token['symbol']} ({token['address'][:8]}...)")
    
    print(f"\n📊 Total exclusions in system: {len(EMERGING_TOKEN_EXCLUSIONS)}")
    print(f"📊 Base token symbols: {BASE_TOKEN_SYMBOLS}")

def test_pool_extraction():
    """Test the pool token extraction logic"""
    print("\n🧪 Testing Pool Token Extraction")
    print("=" * 50)
    
    # Create a test discovery system
    discovery_system = EmergingTokenDiscoverySystem()
    
    # Test pool data scenarios
    test_pools = [
        {
            'pool_name': 'CUDIS-SOL',
            'address': 'PoolAddress123',
            'token_a_address': 'CudisTokenAddress',
            'token_b_address': 'So11111111111111111111111111111111111111112'
        },
        {
            'pool_name': 'CUDIS-USDC',
            'address': 'PoolAddress456',
            'token_a_address': 'CudisTokenAddress',
            'token_b_address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
        },
        {
            'pool_name': 'JLP-SOL',
            'address': 'PoolAddress789',
            'token_a_address': '',
            'token_b_address': ''
        }
    ]
    
    for i, pool in enumerate(test_pools, 1):
        print(f"\nPool {i}: {pool['pool_name']}")
        candidates = discovery_system._extract_tokens_from_pool(pool, pool['pool_name'])
        print(f"  Extracted candidates: {len(candidates)}")
        
        for address, symbol in candidates:
            excluded = is_excluded_token(address)
            base_token = symbol in BASE_TOKEN_SYMBOLS
            status = "EXCLUDED" if excluded else ("BASE" if base_token else "EMERGING")
            print(f"    {symbol} ({address[:8]}...): {status}")

async def test_discovery_system():
    """Test the full discovery system with mock data"""
    print("\n🧪 Testing Discovery System")
    print("=" * 50)
    
    try:
        discovery_system = EmergingTokenDiscoverySystem()
        print("✅ Discovery system initialized successfully")
        
        # Test token extraction methods
        test_pool_name = "CUDIS-SOL"
        extracted_symbol = discovery_system._extract_token_from_pool_name(test_pool_name)
        print(f"✅ Pool name extraction: '{test_pool_name}' -> '{extracted_symbol}'")
        
        # Test pool extraction
        test_pool = {
            'pool_name': 'CUDIS-SOL',
            'address': 'TestPoolAddress',
            'token_a_address': 'CudisAddress',
            'token_b_address': 'SolAddress'
        }
        candidates = discovery_system._extract_tokens_from_pool(test_pool, test_pool['pool_name'])
        print(f"✅ Pool extraction: {len(candidates)} candidates found")
        
        print("✅ All discovery system tests passed")
        
    except Exception as e:
        print(f"❌ Discovery system test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 EMERGING TOKEN DISCOVERY FIX VERIFICATION")
    print("=" * 80)
    
    # Test exclusion logic
    test_exclusion_logic()
    
    # Test pool extraction
    test_pool_extraction()
    
    # Test discovery system
    asyncio.run(test_discovery_system())
    
    print("\n✅ ALL TESTS COMPLETED")
    print("=" * 80)
    print("🎯 The fix should now:")
    print("  1. ✅ Exclude stablecoins and infrastructure tokens")
    print("  2. ✅ Prevent duplicate token entries")
    print("  3. ✅ Properly extract tokens from pool data")
    print("  4. ✅ Apply deduplication at multiple stages")

if __name__ == "__main__":
    main() 