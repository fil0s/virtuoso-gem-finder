#!/usr/bin/env python3
"""
Test All DEX WSOL Filtering - Comprehensive verification of WSOL filtering across all DEX connectors
"""

import asyncio
import sys
import os
import json
import time
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.cross_platform_token_analyzer import (
    MeteoraConnector, 
    WSOL_ADDRESS, 
    WSOL_ONLY_MODE,
    CrossPlatformAnalyzer
)

async def test_meteora_wsol_filtering():
    """Test MeteoraConnector WSOL filtering"""
    print("🌊 Testing Meteora WSOL Filtering")
    print("-" * 50)
    
    connector = MeteoraConnector()
    
    try:
        print(f"📡 Calling MeteoraConnector.get_volume_trending_pools()...")
        tokens = await connector.get_volume_trending_pools(limit=10)
        
        print(f"📊 Found {len(tokens)} tokens from Meteora")
        
        wsol_tokens = [t for t in tokens if t.get('is_wsol_pair', False)]
        non_wsol_tokens = [t for t in tokens if not t.get('is_wsol_pair', False)]
        
        print(f"✅ WSOL-paired tokens: {len(wsol_tokens)}")
        print(f"❌ Non-WSOL tokens: {len(non_wsol_tokens)}")
        
        if wsol_tokens:
            print("\n🎯 WSOL-paired tokens found:")
            for i, token in enumerate(wsol_tokens[:5], 1):
                symbol = token.get('symbol', 'Unknown')
                pool_name = token.get('pool_name', 'Unknown')
                address = token.get('address', 'Unknown')
                print(f"   {i}. {symbol:<12} | Pool: {pool_name:<20} | {address[:8]}...")
        
        return {
            'platform': 'meteora',
            'total_tokens': len(tokens),
            'wsol_tokens': len(wsol_tokens),
            'non_wsol_tokens': len(non_wsol_tokens),
            'wsol_percentage': (len(wsol_tokens) / len(tokens) * 100) if tokens else 0,
            'sample_wsol_tokens': wsol_tokens[:3]
        }
        
    except Exception as e:
        print(f"❌ Error testing Meteora: {e}")
        return {
            'platform': 'meteora',
            'error': str(e),
            'total_tokens': 0,
            'wsol_tokens': 0
        }
    finally:
        await connector.close()

async def test_orca_wsol_filtering():
    """Test Orca connector WSOL filtering via CrossPlatformAnalyzer"""
    print("\n🐋 Testing Orca WSOL Filtering")
    print("-" * 50)
    
    analyzer = CrossPlatformAnalyzer()
    
    try:
        # Get raw platform data to check Orca specifically
        print(f"📡 Collecting Orca data via CrossPlatformAnalyzer...")
        platform_data = await analyzer.collect_all_data()
        
        # Check for Orca-specific keys
        orca_keys = [key for key in platform_data.keys() if 'orca' in key.lower()]
        print(f"📊 Found Orca data sources: {orca_keys}")
        
        total_orca_tokens = 0
        wsol_orca_tokens = 0
        sample_tokens = []
        
        for key in orca_keys:
            tokens = platform_data.get(key, [])
            total_orca_tokens += len(tokens)
            
            wsol_tokens_in_source = [t for t in tokens if t.get('is_wsol_pair', False)]
            wsol_orca_tokens += len(wsol_tokens_in_source)
            
            if wsol_tokens_in_source:
                sample_tokens.extend(wsol_tokens_in_source[:2])
                
            print(f"   📈 {key}: {len(tokens)} total, {len(wsol_tokens_in_source)} WSOL-paired")
        
        print(f"✅ Total Orca WSOL-paired tokens: {wsol_orca_tokens}")
        print(f"📊 Total Orca tokens: {total_orca_tokens}")
        
        if sample_tokens:
            print("\n🎯 Sample Orca WSOL-paired tokens:")
            for i, token in enumerate(sample_tokens[:3], 1):
                symbol = token.get('symbol', 'Unknown')
                address = token.get('address', 'Unknown')
                source = token.get('discovery_source', 'Unknown')
                print(f"   {i}. {symbol:<12} | Source: {source:<25} | {address[:8]}...")
        
        return {
            'platform': 'orca',
            'total_tokens': total_orca_tokens,
            'wsol_tokens': wsol_orca_tokens,
            'wsol_percentage': (wsol_orca_tokens / total_orca_tokens * 100) if total_orca_tokens else 0,
            'data_sources': orca_keys,
            'sample_wsol_tokens': sample_tokens[:3]
        }
        
    except Exception as e:
        print(f"❌ Error testing Orca: {e}")
        return {
            'platform': 'orca',
            'error': str(e),
            'total_tokens': 0,
            'wsol_tokens': 0
        }
    finally:
        await analyzer.close()

async def test_raydium_wsol_filtering():
    """Test Raydium connector WSOL filtering via CrossPlatformAnalyzer"""
    print("\n⚡ Testing Raydium WSOL Filtering")
    print("-" * 50)
    
    analyzer = CrossPlatformAnalyzer()
    
    try:
        # Get raw platform data to check Raydium specifically  
        print(f"📡 Collecting Raydium data via CrossPlatformAnalyzer...")
        platform_data = await analyzer.collect_all_data()
        
        # Check for Raydium-specific keys
        raydium_keys = [key for key in platform_data.keys() if 'raydium' in key.lower()]
        print(f"📊 Found Raydium data sources: {raydium_keys}")
        
        total_raydium_tokens = 0
        wsol_raydium_tokens = 0
        sample_tokens = []
        
        for key in raydium_keys:
            tokens = platform_data.get(key, [])
            total_raydium_tokens += len(tokens)
            
            wsol_tokens_in_source = [t for t in tokens if t.get('is_wsol_pair', False)]
            wsol_raydium_tokens += len(wsol_tokens_in_source)
            
            if wsol_tokens_in_source:
                sample_tokens.extend(wsol_tokens_in_source[:2])
                
            print(f"   📈 {key}: {len(tokens)} total, {len(wsol_tokens_in_source)} WSOL-paired")
        
        print(f"✅ Total Raydium WSOL-paired tokens: {wsol_raydium_tokens}")
        print(f"📊 Total Raydium tokens: {total_raydium_tokens}")
        
        if sample_tokens:
            print("\n🎯 Sample Raydium WSOL-paired tokens:")
            for i, token in enumerate(sample_tokens[:3], 1):
                symbol = token.get('symbol', 'Unknown')
                address = token.get('address', 'Unknown')
                source = token.get('discovery_source', 'Unknown')
                print(f"   {i}. {symbol:<12} | Source: {source:<25} | {address[:8]}...")
        
        return {
            'platform': 'raydium',
            'total_tokens': total_raydium_tokens,
            'wsol_tokens': wsol_raydium_tokens,
            'wsol_percentage': (wsol_raydium_tokens / total_raydium_tokens * 100) if total_raydium_tokens else 0,
            'data_sources': raydium_keys,
            'sample_wsol_tokens': sample_tokens[:3]
        }
        
    except Exception as e:
        print(f"❌ Error testing Raydium: {e}")
        return {
            'platform': 'raydium',
            'error': str(e),
            'total_tokens': 0,
            'wsol_tokens': 0
        }
    finally:
        await analyzer.close()

async def test_integration_wsol_filtering():
    """Test integrated WSOL filtering across all platforms"""
    print("\n🔗 Testing Integrated WSOL Filtering")
    print("-" * 50)
    
    analyzer = CrossPlatformAnalyzer()
    
    try:
        print(f"📡 Running full cross-platform analysis...")
        results = await analyzer.run_analysis()
        
        correlations = results.get('correlations', {})
        all_tokens = correlations.get('all_tokens', {})
        
        print(f"📊 Total tokens in analysis: {len(all_tokens)}")
        
        # Count WSOL tokens by checking the data field
        wsol_tokens = []
        platform_wsol_counts = {}
        
        for token_addr, token_info in all_tokens.items():
            token_data = token_info.get('data', {})
            platforms = token_info.get('platforms', [])
            
            # Check each platform for WSOL pair flag
            for platform in platforms:
                if platform in token_data:
                    platform_data = token_data[platform]
                    if platform_data.get('is_wsol_pair', False):
                        wsol_tokens.append({
                            'address': token_addr,
                            'symbol': token_info.get('symbol', 'Unknown'),
                            'platform': platform,
                            'score': token_info.get('score', 0)
                        })
                        
                        # Count by platform
                        if platform not in platform_wsol_counts:
                            platform_wsol_counts[platform] = 0
                        platform_wsol_counts[platform] += 1
                        break  # Only count once per token
        
        print(f"✅ Total WSOL-paired tokens: {len(wsol_tokens)}")
        print(f"📈 WSOL percentage: {(len(wsol_tokens) / len(all_tokens) * 100):.1f}%")
        
        print("\n📊 WSOL tokens by platform:")
        for platform, count in platform_wsol_counts.items():
            print(f"   • {platform}: {count} tokens")
        
        if wsol_tokens:
            print("\n🎯 Top WSOL-paired tokens:")
            sorted_tokens = sorted(wsol_tokens, key=lambda x: x['score'], reverse=True)
            for i, token in enumerate(sorted_tokens[:5], 1):
                print(f"   {i}. {token['symbol']:<12} | Score: {token['score']:5.1f} | {token['platform']:<15} | {token['address'][:8]}...")
        
        return {
            'platform': 'integrated',
            'total_tokens': len(all_tokens),
            'wsol_tokens': len(wsol_tokens),
            'wsol_percentage': (len(wsol_tokens) / len(all_tokens) * 100) if all_tokens else 0,
            'platform_breakdown': platform_wsol_counts,
            'top_wsol_tokens': sorted(wsol_tokens, key=lambda x: x['score'], reverse=True)[:5]
        }
        
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        return {
            'platform': 'integrated',
            'error': str(e),
            'total_tokens': 0,
            'wsol_tokens': 0
        }
    finally:
        await analyzer.close()

async def main():
    """Run comprehensive WSOL filtering tests across all DEX connectors"""
    print("🔍 Comprehensive DEX WSOL Filtering Test")
    print("=" * 70)
    print(f"🎯 WSOL Address: {WSOL_ADDRESS}")
    print(f"⚙️ WSOL Only Mode: {WSOL_ONLY_MODE}")
    print()
    
    start_time = time.time()
    
    # Test each DEX individually
    meteora_results = await test_meteora_wsol_filtering()
    orca_results = await test_orca_wsol_filtering()
    raydium_results = await test_raydium_wsol_filtering()
    
    # Test integrated filtering
    integration_results = await test_integration_wsol_filtering()
    
    end_time = time.time()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)
    
    all_results = [meteora_results, orca_results, raydium_results, integration_results]
    
    for result in all_results:
        platform = result['platform'].upper()
        if 'error' in result:
            print(f"❌ {platform:<12}: ERROR - {result['error']}")
        else:
            total = result['total_tokens']
            wsol = result['wsol_tokens']
            pct = result.get('wsol_percentage', 0)
            print(f"✅ {platform:<12}: {wsol:3d}/{total:3d} tokens ({pct:4.1f}% WSOL-paired)")
    
    print(f"\n⏱️ Total test time: {end_time - start_time:.1f}s")
    
    # Detailed results
    print("\n🔍 DETAILED ANALYSIS:")
    
    if not meteora_results.get('error') and meteora_results['wsol_tokens'] > 0:
        print("✅ Meteora WSOL filtering: WORKING")
    else:
        print("❌ Meteora WSOL filtering: NOT WORKING")
    
    if not orca_results.get('error') and orca_results['wsol_tokens'] > 0:
        print("✅ Orca WSOL filtering: WORKING")
    else:
        print("⚠️ Orca WSOL filtering: NO WSOL PAIRS FOUND")
    
    if not raydium_results.get('error') and raydium_results['wsol_tokens'] > 0:
        print("✅ Raydium WSOL filtering: WORKING")
    else:
        print("⚠️ Raydium WSOL filtering: NO WSOL PAIRS FOUND")
    
    if not integration_results.get('error') and integration_results['wsol_tokens'] > 0:
        print("✅ Integrated WSOL filtering: WORKING")
    else:
        print("❌ Integrated WSOL filtering: NOT WORKING")
    
    # Save detailed results
    timestamp = int(time.time())
    results_file = f"dex_wsol_filtering_test_{timestamp}.json"
    
    detailed_results = {
        'test_timestamp': timestamp,
        'test_duration_seconds': end_time - start_time,
        'wsol_address': WSOL_ADDRESS,
        'wsol_only_mode': WSOL_ONLY_MODE,
        'meteora_results': meteora_results,
        'orca_results': orca_results,
        'raydium_results': raydium_results,
        'integration_results': integration_results
    }
    
    with open(results_file, 'w') as f:
        json.dump(detailed_results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    print("\n🎉 DEX WSOL filtering test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 