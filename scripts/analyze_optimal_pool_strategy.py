#!/usr/bin/env python3
"""
Analyze optimal pool selection strategy for early gem detection
Tests different approaches to find the best pools for analysis
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.raydium_connector import RaydiumConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_pool_strategies():
    """Analyze different pool selection strategies for early gem detection"""
    print("🔍 Analyzing Optimal Pool Selection Strategies")
    print("=" * 60)
    
    async with RaydiumConnector() as connector:
        
        # Strategy 1: Current approach - High volume pools
        print("\n📊 Strategy 1: High Volume Pools (Current)")
        high_volume_endpoint = '/pools/info/list?poolType=all&poolSortField=volume24h&sortType=desc&page=1&pageSize=10'
        high_volume_data = await connector._make_tracked_request(high_volume_endpoint, use_v2_fallback=False)
        
        if high_volume_data and high_volume_data.get('success'):
            pools = high_volume_data['data']['data']
            print(f"   ✅ Found {len(pools)} high-volume pools")
            
            # Analyze characteristics
            avg_tvl = sum(p.get('tvl', 0) for p in pools) / len(pools)
            avg_volume = sum(p.get('day', {}).get('volume', 0) for p in pools) / len(pools)
            wsol_count = sum(1 for p in pools if 
                           (isinstance(p.get('mintA'), dict) and p['mintA'].get('address') == 'So11111111111111111111111111111111111111112') or
                           (isinstance(p.get('mintB'), dict) and p['mintB'].get('address') == 'So11111111111111111111111111111111111111112'))
            
            print(f"   📈 Average TVL: ${avg_tvl:,.2f}")
            print(f"   📊 Average Volume: ${avg_volume:,.2f}")
            print(f"   🌊 WSOL pairs: {wsol_count}/{len(pools)} ({wsol_count/len(pools)*100:.1f}%)")
            
            # Check for potential early gems (low TVL but decent volume)
            early_gems = [p for p in pools if p.get('tvl', 0) < 50000 and p.get('day', {}).get('volume', 0) > 1000]
            print(f"   💎 Potential early gems (TVL < $50k, Volume > $1k): {len(early_gems)}")
        
        # Strategy 2: Low liquidity but active pools  
        print("\n🔬 Strategy 2: Low Liquidity + High Volume (Potential Early Gems)")
        low_liq_endpoint = '/pools/info/list?poolType=all&poolSortField=liquidity&sortType=asc&page=1&pageSize=50'
        low_liq_data = await connector._make_tracked_request(low_liq_endpoint, use_v2_fallback=False)
        
        if low_liq_data and low_liq_data.get('success'):
            pools = low_liq_data['data']['data']
            
            # Filter for pools with some volume activity
            active_low_liq = [p for p in pools if p.get('day', {}).get('volume', 0) > 100]
            print(f"   ✅ Found {len(active_low_liq)} low-liquidity but active pools")
            
            if active_low_liq:
                avg_tvl = sum(p.get('tvl', 0) for p in active_low_liq) / len(active_low_liq)
                avg_volume = sum(p.get('day', {}).get('volume', 0) for p in active_low_liq) / len(active_low_liq)
                wsol_count = sum(1 for p in active_low_liq if 
                               (isinstance(p.get('mintA'), dict) and p['mintA'].get('address') == 'So11111111111111111111111111111111111111112') or
                               (isinstance(p.get('mintB'), dict) and p['mintB'].get('address') == 'So11111111111111111111111111111111111111112'))
                
                print(f"   📈 Average TVL: ${avg_tvl:,.2f}")
                print(f"   📊 Average Volume: ${avg_volume:,.2f}")
                print(f"   🌊 WSOL pairs: {wsol_count}/{len(active_low_liq)} ({wsol_count/len(active_low_liq)*100:.1f}%)")
        
        # Strategy 3: Multi-page volume scanning for emerging gems
        print("\n🚀 Strategy 3: Multi-Page Volume Scanning (Emerging Gems)")
        emerging_gems = []
        
        # Scan pages 5-15 of volume-sorted data (skip the giants, find rising stars)
        for page in range(5, 11):  # Pages 5-10
            page_endpoint = f'/pools/info/list?poolType=all&poolSortField=volume24h&sortType=desc&page={page}&pageSize=20'
            page_data = await connector._make_tracked_request(page_endpoint, use_v2_fallback=False)
            
            if page_data and page_data.get('success'):
                pools = page_data['data']['data']
                
                # Find pools with good volume/TVL ratio (high activity relative to size)
                for pool in pools:
                    tvl = pool.get('tvl', 0)
                    volume = pool.get('day', {}).get('volume', 0)
                    
                    # Criteria for emerging gems:
                    # - TVL between $5k-$500k (not too small, not too big)
                    # - Volume > TVL * 0.1 (at least 10% daily turnover)
                    # - Must be WSOL paired
                    is_wsol = ((isinstance(pool.get('mintA'), dict) and pool['mintA'].get('address') == 'So11111111111111111111111111111111111111112') or
                              (isinstance(pool.get('mintB'), dict) and pool['mintB'].get('address') == 'So11111111111111111111111111111111111111112'))
                    
                    if (5000 <= tvl <= 500000 and 
                        volume > tvl * 0.1 and 
                        is_wsol):
                        
                        emerging_gems.append({
                            'tvl': tvl,
                            'volume': volume,
                            'volume_tvl_ratio': volume / tvl if tvl > 0 else 0,
                            'page': page,
                            'pool': pool
                        })
        
        emerging_gems.sort(key=lambda x: x['volume_tvl_ratio'], reverse=True)
        print(f"   ✅ Found {len(emerging_gems)} emerging gem candidates")
        
        if emerging_gems:
            print("   🏆 Top 3 emerging gems by volume/TVL ratio:")
            for i, gem in enumerate(emerging_gems[:3]):
                mint_a_symbol = gem['pool'].get('mintA', {}).get('symbol', 'Unknown')
                mint_b_symbol = gem['pool'].get('mintB', {}).get('symbol', 'Unknown')
                print(f"      {i+1}. {mint_a_symbol}/{mint_b_symbol} - TVL: ${gem['tvl']:,.0f}, Volume: ${gem['volume']:,.0f}, Ratio: {gem['volume_tvl_ratio']:.2f}")
        
        # Strategy 4: Combined optimal approach
        print("\n🎯 Strategy 4: Optimal Combined Approach")
        print("   Recommended strategy for early gem detection:")
        print("   1. 📊 Scan pages 3-8 of volume-sorted pools (skip giants, catch rising stars)")  
        print("   2. 🔍 Filter for TVL $1k-$100k (early stage but with some liquidity)")
        print("   3. ⚡ Require volume/TVL ratio > 0.2 (20% daily turnover = high activity)")
        print("   4. 🌊 WSOL-paired only (easier to trade)")
        print("   5. 🚫 Exclude major tokens (stablecoins, etc.)")
        print("   6. 🔄 Refresh every 5-10 minutes for new discoveries")

async def main():
    await analyze_pool_strategies()

if __name__ == "__main__":
    asyncio.run(main())