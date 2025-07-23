#!/usr/bin/env python3
"""
Check WSOL Pair Availability - Verify if trending tokens have WSOL pairs on major DEXs
"""

import asyncio
import sys
import os
import json
import aiohttp
from typing import Dict, List, Any, Set
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer, WSOL_ADDRESS

class WSolPairChecker:
    """Check WSOL pair availability across major DEXs"""
    
    def __init__(self):
        self.wsol_address = WSOL_ADDRESS
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_meteora_wsol_pair(self, token_address: str) -> Dict[str, Any]:
        """Check if token has WSOL pair on Meteora"""
        try:
            url = "https://app.meteora.ag/clmm-api/pair/all_by_groups"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('data', {}).get('groups', [])
                    
                    for group in pools:
                        pairs = group.get('pairs', [])
                        for pair in pairs:
                            token_x = pair.get('token_x_mint', '')
                            token_y = pair.get('token_y_mint', '')
                            
                            # Check if this pair has our token and WSOL
                            if ((token_x == token_address and token_y == self.wsol_address) or
                                (token_y == token_address and token_x == self.wsol_address)):
                                return {
                                    'available': True,
                                    'pair_name': pair.get('name', 'Unknown'),
                                    'liquidity_usd': pair.get('liquidity', 0),
                                    'volume_24h': pair.get('volume_24h', 0)
                                }
                    
                    return {'available': False}
                else:
                    return {'available': False, 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            return {'available': False, 'error': str(e)}

    async def check_orca_wsol_pair(self, token_address: str) -> Dict[str, Any]:
        """Check if token has WSOL pair on Orca"""
        try:
            url = "https://api.mainnet.orca.so/v1/whirlpool/list"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('whirlpools', [])
                    
                    for pool in pools:
                        token_a = pool.get('tokenA', {}).get('mint', '')
                        token_b = pool.get('tokenB', {}).get('mint', '')
                        
                        # Check if this pool has our token and WSOL
                        if ((token_a == token_address and token_b == self.wsol_address) or
                            (token_b == token_address and token_a == self.wsol_address)):
                            return {
                                'available': True,
                                'pool_address': pool.get('address', ''),
                                'liquidity_usd': pool.get('tvl', 0),
                                'volume_24h': pool.get('volume', {}).get('day', 0)
                            }
                    
                    return {'available': False}
                else:
                    return {'available': False, 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            return {'available': False, 'error': str(e)}

    async def check_raydium_wsol_pair(self, token_address: str) -> Dict[str, Any]:
        """Check if token has WSOL pair on Raydium"""
        try:
            url = "https://api.raydium.io/v2/main/pairs"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for pair_id, pair_data in data.items():
                        base_mint = pair_data.get('baseMint', '')
                        quote_mint = pair_data.get('quoteMint', '')
                        
                        # Check if this pair has our token and WSOL
                        if ((base_mint == token_address and quote_mint == self.wsol_address) or
                            (quote_mint == token_address and base_mint == self.wsol_address)):
                            return {
                                'available': True,
                                'pair_id': pair_id,
                                'pair_name': pair_data.get('name', 'Unknown'),
                                'liquidity_usd': pair_data.get('liquidity', 0),
                                'volume_24h': pair_data.get('volume24h', 0)
                            }
                    
                    return {'available': False}
                else:
                    return {'available': False, 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            return {'available': False, 'error': str(e)}

    async def check_jupiter_wsol_pair(self, token_address: str) -> Dict[str, Any]:
        """Check if token has WSOL pair routes on Jupiter"""
        try:
            # Check if Jupiter can route between this token and WSOL
            url = f"https://quote-api.jup.ag/v6/quote"
            params = {
                'inputMint': token_address,
                'outputMint': self.wsol_address,
                'amount': 1000000,  # 1 token (6 decimals)
                'onlyDirectRoutes': 'true'  # Only direct pairs
            }
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    routes = data.get('routePlan', [])
                    
                    if routes:
                        return {
                            'available': True,
                            'route_count': len(routes),
                            'price_impact': data.get('priceImpactPct', 0),
                            'out_amount': data.get('outAmount', 0)
                        }
                    else:
                        return {'available': False}
                else:
                    return {'available': False, 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            return {'available': False, 'error': str(e)}

    async def check_all_dexs(self, token_address: str, token_symbol: str = None) -> Dict[str, Any]:
        """Check WSOL pair availability across all DEXs"""
        
        # Check all DEXs concurrently
        tasks = [
            ('meteora', self.check_meteora_wsol_pair(token_address)),
            ('orca', self.check_orca_wsol_pair(token_address)),
            ('raydium', self.check_raydium_wsol_pair(token_address)),
            ('jupiter', self.check_jupiter_wsol_pair(token_address)),
        ]
        
        results = {}
        for dex_name, task in tasks:
            try:
                result = await task
                results[dex_name] = result
            except Exception as e:
                results[dex_name] = {'available': False, 'error': str(e)}
        
        # Count available DEXs
        available_dexs = [dex for dex, data in results.items() if data.get('available', False)]
        
        return {
            'token_address': token_address,
            'token_symbol': token_symbol,
            'dex_results': results,
            'available_on': available_dexs,
            'dex_count': len(available_dexs),
            'has_wsol_pairs': len(available_dexs) > 0
        }

async def main():
    """Main function to check WSOL pair availability for trending tokens"""
    print("🔍 Checking WSOL Pair Availability for Trending Tokens")
    print("=" * 70)
    
    start_time = time.time()
    
    # Get trending tokens from current analysis
    print("📡 Getting trending tokens from current analysis...")
    analyzer = CrossPlatformAnalyzer()
    
    try:
        results = await analyzer.run_analysis()
        correlations = results.get('correlations', {})
        all_tokens = correlations.get('all_tokens', {})
        
        print(f"📊 Found {len(all_tokens)} trending tokens to check")
        
        # Sample of tokens to check (to avoid overwhelming APIs)
        sample_size = min(20, len(all_tokens))
        token_sample = list(all_tokens.items())[:sample_size]
        
        print(f"🎯 Checking WSOL pair availability for {sample_size} tokens...")
        print()
        
        # Check WSOL pair availability
        async with WSolPairChecker() as checker:
            wsol_availability_results = []
            
            for i, (token_addr, token_info) in enumerate(token_sample, 1):
                token_symbol = token_info.get('symbol', 'Unknown')
                print(f"[{i:2d}/{sample_size}] Checking {token_symbol}...")
                
                result = await checker.check_all_dexs(token_addr, token_symbol)
                wsol_availability_results.append(result)
                
                # Brief delay to be respectful to APIs
                await asyncio.sleep(0.5)
        
        await analyzer.close()
        
    except Exception as e:
        print(f"❌ Error getting trending tokens: {e}")
        return
    
    end_time = time.time()
    
    # Analyze results
    print("\n" + "=" * 70)
    print("📊 WSOL PAIR AVAILABILITY ANALYSIS")
    print("=" * 70)
    
    tokens_with_wsol = [r for r in wsol_availability_results if r['has_wsol_pairs']]
    tokens_without_wsol = [r for r in wsol_availability_results if not r['has_wsol_pairs']]
    
    print(f"✅ Tokens WITH WSOL pairs: {len(tokens_with_wsol)}/{len(wsol_availability_results)} ({len(tokens_with_wsol)/len(wsol_availability_results)*100:.1f}%)")
    print(f"❌ Tokens WITHOUT WSOL pairs: {len(tokens_without_wsol)}/{len(wsol_availability_results)} ({len(tokens_without_wsol)/len(wsol_availability_results)*100:.1f}%)")
    
    # DEX availability breakdown
    dex_counts = {'meteora': 0, 'orca': 0, 'raydium': 0, 'jupiter': 0}
    for result in wsol_availability_results:
        for dex in result['available_on']:
            dex_counts[dex] += 1
    
    print(f"\n📊 WSOL PAIR AVAILABILITY BY DEX:")
    for dex, count in dex_counts.items():
        percentage = (count / len(wsol_availability_results) * 100)
        print(f"   • {dex.capitalize():<10}: {count:2d}/{len(wsol_availability_results)} tokens ({percentage:4.1f}%)")
    
    # Top tokens with WSOL pairs
    if tokens_with_wsol:
        print(f"\n🎯 TOP TOKENS WITH WSOL PAIRS:")
        sorted_tokens = sorted(tokens_with_wsol, key=lambda x: x['dex_count'], reverse=True)
        
        for i, token in enumerate(sorted_tokens[:10], 1):
            symbol = token['token_symbol']
            dex_count = token['dex_count']
            available_dexs = ', '.join(token['available_on'])
            print(f"   {i:2d}. {symbol:<15} | {dex_count} DEXs | Available on: {available_dexs}")
    
    # Tokens without WSOL pairs
    if tokens_without_wsol:
        print(f"\n❗ TOKENS WITHOUT WSOL PAIRS:")
        for i, token in enumerate(tokens_without_wsol[:5], 1):
            symbol = token['token_symbol']
            address = token['token_address'][:8]
            print(f"   {i:2d}. {symbol:<15} | {address}... | No WSOL pairs found")
    
    print(f"\n⏱️ Analysis completed in {end_time - start_time:.1f}s")
    
    # Save detailed results
    timestamp = int(time.time())
    results_file = f"wsol_pair_availability_{timestamp}.json"
    
    detailed_results = {
        'analysis_timestamp': timestamp,
        'analysis_duration_seconds': end_time - start_time,
        'tokens_analyzed': len(wsol_availability_results),
        'tokens_with_wsol_pairs': len(tokens_with_wsol),
        'tokens_without_wsol_pairs': len(tokens_without_wsol),
        'wsol_availability_percentage': len(tokens_with_wsol)/len(wsol_availability_results)*100,
        'dex_availability_counts': dex_counts,
        'detailed_results': wsol_availability_results
    }
    
    with open(results_file, 'w') as f:
        json.dump(detailed_results, f, indent=2, default=str)
    
    print(f"📁 Detailed results saved to: {results_file}")
    print("\n🎉 WSOL pair availability analysis completed!")

if __name__ == "__main__":
    asyncio.run(main()) 