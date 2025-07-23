#!/usr/bin/env python3
"""
Test enhanced pool selection strategy showing early gem detection capabilities
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.raydium_connector import RaydiumConnector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_pool_selection():
    """Test the enhanced pool selection strategy"""
    print("🚀 Testing Enhanced Pool Selection Strategy")
    print("=" * 60)
    
    async with RaydiumConnector() as connector:
        # Get WSOL pairs using enhanced strategy
        print("\n🔍 Getting WSOL pairs with enhanced early gem detection...")
        wsol_pairs = await connector.get_wsol_trending_pairs(limit=20)
        
        if wsol_pairs:
            print(f"✅ Retrieved {len(wsol_pairs)} WSOL pairs")
            
            # Separate early gems from regular pairs
            early_gems = [pair for pair in wsol_pairs if pair.get('is_early_gem_candidate', False)]
            regular_pairs = [pair for pair in wsol_pairs if not pair.get('is_early_gem_candidate', False)]
            
            print(f"\n💎 Early Gem Candidates: {len(early_gems)}")
            print(f"📊 Regular Pairs: {len(regular_pairs)}")
            
            # Show top early gems
            if early_gems:
                print(f"\n🏆 Top 10 Early Gem Candidates (sorted by volume/TVL ratio):")
                print(f"{'#':<3} {'Symbol':<12} {'TVL':<12} {'Volume':<15} {'Ratio':<8} {'Score'}")
                print("-" * 65)
                
                for i, gem in enumerate(early_gems[:10]):
                    symbol = gem.get('symbol', 'Unknown')[:11]
                    tvl = gem.get('tvl', 0)
                    volume = gem.get('volume_24h', 0)
                    ratio = gem.get('volume_tvl_ratio', 0)
                    score = gem.get('early_gem_score', 0)
                    
                    print(f"{i+1:<3} {symbol:<12} ${tvl:<11,.0f} ${volume:<14,.0f} {ratio:<7.1f} {score:.1f}")
            
            # Show comparison with regular high-volume pairs
            if regular_pairs:
                print(f"\n📈 Top 5 Regular High-Volume Pairs:")
                print(f"{'#':<3} {'Symbol':<12} {'TVL':<15} {'Volume':<15} {'Type'}")
                print("-" * 65)
                
                for i, pair in enumerate(regular_pairs[:5]):
                    symbol = pair.get('symbol', 'Unknown')[:11]
                    tvl = pair.get('tvl', 0)
                    volume = pair.get('volume_24h', 0)
                    pair_type = "Established" if tvl > 500000 else "Mid-tier"
                    
                    print(f"{i+1:<3} {symbol:<12} ${tvl:<14,.0f} ${volume:<14,.0f} {pair_type}")
            
            # Analysis summary
            print(f"\n📊 Analysis Summary:")
            if early_gems:
                avg_early_tvl = sum(g.get('tvl', 0) for g in early_gems) / len(early_gems)
                avg_early_volume = sum(g.get('volume_24h', 0) for g in early_gems) / len(early_gems)
                avg_early_ratio = sum(g.get('volume_tvl_ratio', 0) for g in early_gems) / len(early_gems)
                
                print(f"   💎 Early Gems - Avg TVL: ${avg_early_tvl:,.0f}, Avg Volume: ${avg_early_volume:,.0f}, Avg Ratio: {avg_early_ratio:.1f}")
            
            if regular_pairs:
                avg_regular_tvl = sum(p.get('tvl', 0) for p in regular_pairs) / len(regular_pairs)
                avg_regular_volume = sum(p.get('volume_24h', 0) for p in regular_pairs) / len(regular_pairs)
                
                print(f"   📊 Regular Pairs - Avg TVL: ${avg_regular_tvl:,.0f}, Avg Volume: ${avg_regular_volume:,.0f}")
            
            print(f"\n🎯 Strategy Benefits:")
            print(f"   ✅ Prioritizes high-activity, low-cap tokens (early gems)")
            print(f"   ✅ Scans mid-tier volume pages (pages 3-12) to avoid giants")
            print(f"   ✅ Uses volume/TVL ratio to identify momentum")
            print(f"   ✅ Filters for $1k-$500k TVL range (tradeable but early)")
            print(f"   ✅ WSOL-paired only for easier trading")
            
        else:
            print("❌ No WSOL pairs retrieved")

if __name__ == "__main__":
    asyncio.run(test_enhanced_pool_selection())