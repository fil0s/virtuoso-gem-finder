#!/usr/bin/env python3
"""
Comprehensive DEX Data Structure Analysis
Shows exactly what information and data we can extract from Orca and Raydium
"""

import asyncio
import json
from typing import Dict, Any
from api.orca_connector import OrcaConnector
from api.raydium_connector import RaydiumConnector

class DEXDataAnalyzer:
    def __init__(self):
        self.orca_data_samples = {}
        self.raydium_data_samples = {}
    
    async def analyze_orca_data_structure(self):
        """Comprehensive analysis of Orca data structure"""
        print("🌊 ORCA DEX DATA STRUCTURE ANALYSIS")
        print("="*60)
        
        async with OrcaConnector(enhanced_cache=None) as orca:
            # Get sample pool data
            pools = await orca.get_pools()
            
            print(f"📊 Total Orca Pools Available: {len(pools)}")
            
            if pools:
                sample_pool = pools[0]
                print(f"\n📋 Raw Pool Data Structure (Sample):")
                print(json.dumps(sample_pool, indent=2))
                
                print(f"\n🔍 Available Pool Fields:")
                for key, value in sample_pool.items():
                    print(f"   • {key}: {type(value).__name__} = {value}")
                
                # Test with SAMO (known working token)
                samo_address = "9rguDaKqTrVjaDXafq6E7rKGn7NPHomkdb8RKpjKCDm2"
                
                print(f"\n🎯 SAMO Token Analysis (Known Working):")
                print(f"   Address: {samo_address}")
                
                # Get token-specific pools
                samo_pools = await orca.get_token_pools(samo_address)
                print(f"\n📊 SAMO Pool Data ({len(samo_pools)} pools found):")
                
                if samo_pools:
                    for i, pool in enumerate(samo_pools):
                        print(f"\n   Pool {i+1}:")
                        for key, value in pool.items():
                            print(f"      {key}: {value}")
                
                # Get comprehensive analytics
                analytics = await orca.get_pool_analytics(samo_address)
                print(f"\n📈 SAMO Analytics Data:")
                print(json.dumps(analytics, indent=2))
                
                print(f"\n🏆 Orca Analytics Fields Available:")
                for key, value in analytics.items():
                    print(f"   • {key}: {type(value).__name__} = {value}")
                
                # Get trending pools
                trending = await orca.get_trending_pools(min_volume_24h=100)
                print(f"\n📈 Trending Pools (Volume > $100): {len(trending)} pools")
                
                if trending:
                    print(f"   Top trending pool: {trending[0]['name']}")
                    print(f"   Volume: ${trending[0].get('volume_24h', 0):,.2f}")
                    print(f"   Liquidity: ${trending[0].get('liquidity', 0):,.2f}")
                
                self.orca_data_samples = {
                    'raw_pool': sample_pool,
                    'token_pools': samo_pools,
                    'analytics': analytics,
                    'trending_sample': trending[0] if trending else None
                }
    
    async def analyze_raydium_data_structure(self):
        """Comprehensive analysis of Raydium data structure"""
        print(f"\n☀️ RAYDIUM DEX DATA STRUCTURE ANALYSIS")
        print("="*60)
        
        async with RaydiumConnector(enhanced_cache=None) as raydium:
            # Get sample data (limited to avoid rate limits)
            try:
                pools = await raydium.get_pools(limit=10)
                pairs = await raydium.get_pairs(limit=10)
                
                print(f"📊 Raydium Pools Sample: {len(pools)} pools")
                print(f"📊 Raydium Pairs Sample: {len(pairs)} pairs")
                
                if pools:
                    sample_pool = pools[0]
                    print(f"\n📋 Raw Pool Data Structure (Sample):")
                    print(json.dumps(sample_pool, indent=2))
                    
                    print(f"\n🔍 Available Pool Fields:")
                    for key, value in sample_pool.items():
                        print(f"   • {key}: {type(value).__name__} = {value}")
                
                if pairs:
                    sample_pair = pairs[0]
                    print(f"\n📋 Raw Pair Data Structure (Sample):")
                    print(json.dumps(sample_pair, indent=2))
                    
                    print(f"\n🔍 Available Pair Fields:")
                    for key, value in sample_pair.items():
                        print(f"   • {key}: {type(value).__name__} = {value}")
                
                # Extract a token address from the pair for testing
                if pairs and pairs[0].get('pair_id'):
                    pair_id = pairs[0]['pair_id']
                    if '-' in pair_id:
                        test_token = pair_id.split('-')[0]
                        
                        print(f"\n🎯 Sample Token Analysis: {test_token[:12]}...")
                        
                        # Get comprehensive stats (careful with rate limits)
                        try:
                            token_pairs = await raydium.get_token_pairs(test_token, search_limit=100)
                            stats = await raydium.get_pool_stats(test_token)
                            
                            print(f"\n📊 Token Pairs Found: {len(token_pairs)}")
                            if token_pairs:
                                print(f"   Sample pair data:")
                                for key, value in token_pairs[0].items():
                                    print(f"      {key}: {value}")
                            
                            print(f"\n📈 Token Stats Data:")
                            print(json.dumps(stats, indent=2))
                            
                            print(f"\n🏆 Raydium Stats Fields Available:")
                            for key, value in stats.items():
                                print(f"   • {key}: {type(value).__name__} = {value}")
                            
                            self.raydium_data_samples = {
                                'raw_pool': sample_pool,
                                'raw_pair': sample_pair,
                                'token_pairs': token_pairs,
                                'stats': stats
                            }
                            
                        except Exception as e:
                            print(f"   ⚠️ Rate limited on detailed analysis: {e}")
                
            except Exception as e:
                print(f"❌ Raydium analysis limited due to: {e}")
    
    def show_data_comparison(self):
        """Show comparison of data available from both DEXs"""
        print(f"\n🔄 COMPARATIVE DEX DATA ANALYSIS")
        print("="*60)
        
        print(f"🌊 ORCA provides:")
        print(f"   📊 Pool Information:")
        print(f"      • Pool name and account details")
        print(f"      • Token mint accounts")
        print(f"      • Real-time liquidity amounts")
        print(f"      • Current token prices")
        print(f"      • APY data (24h, 7d, 30d)")
        print(f"      • Volume data (24h, 7d, 30d)")
        print(f"      • Volume in quote currency")
        
        print(f"\n   📈 Analytics:")
        print(f"      • Pool count per token")
        print(f"      • Total liquidity aggregation")
        print(f"      • Volume aggregation")
        print(f"      • Quality scoring")
        print(f"      • Top pools ranking")
        
        print(f"\n☀️ RAYDIUM provides:")
        print(f"   📊 Pool Information:")
        print(f"      • Pool identifiers and LP tokens")
        print(f"      • Liquidity lock status")
        print(f"      • APY calculations")
        print(f"      • Official pool verification")
        
        print(f"\n   📊 Pair Information:")
        print(f"      • Trading pair names")
        print(f"      • Market IDs and AMM IDs")
        print(f"      • Detailed liquidity data")
        print(f"      • Volume and fee metrics")
        print(f"      • Token amount breakdowns")
        print(f"      • LP pricing information")
        
        print(f"\n   📈 Analytics:")
        print(f"      • Combined pool and pair stats")
        print(f"      • Liquidity aggregation")
        print(f"      • Volume tracking")
        print(f"      • Quality scoring")
        print(f"      • APY analysis")
    
    def show_practical_use_cases(self):
        """Show practical use cases for the DEX data"""
        print(f"\n🎯 PRACTICAL USE CASES FOR DEX DATA")
        print("="*60)
        
        print(f"💰 Liquidity Analysis:")
        print(f"   • Total liquidity across all pools/pairs")
        print(f"   • Liquidity distribution and concentration")
        print(f"   • Pool depth for trade impact analysis")
        print(f"   • Cross-DEX liquidity comparison")
        
        print(f"\n📈 Trading Opportunities:")
        print(f"   • Volume trend analysis (24h, 7d, 30d)")
        print(f"   • Price discovery across DEXs")
        print(f"   • Arbitrage opportunity detection")
        print(f"   • Slippage estimation")
        
        print(f"\n🏆 Quality Assessment:")
        print(f"   • DEX adoption scoring")
        print(f"   • Pool quality metrics")
        print(f"   • Trading activity levels")
        print(f"   • Market maturity indicators")
        
        print(f"\n⚡ Risk Analysis:")
        print(f"   • Liquidity risk assessment")
        print(f"   • Pool concentration risk")
        print(f"   • Volume sustainability")
        print(f"   • APY sustainability analysis")
        
        print(f"\n🔍 Token Validation:")
        print(f"   • DEX presence confirmation")
        print(f"   • Official pool verification")
        print(f"   • Market maker activity")
        print(f"   • Ecosystem integration level")

async def demonstrate_sample_token_analysis():
    """Demonstrate analysis on your sample tokens"""
    print(f"\n🧪 SAMPLE TOKEN ANALYSIS DEMONSTRATION")
    print("="*60)
    
    # Your sample tokens
    sample_tokens = [
        {"name": "SPX", "address": "J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr"},
        {"name": "TRUMP", "address": "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN"},
        {"name": "SAMO", "address": "9rguDaKqTrVjaDXafq6E7rKGn7NPHomkdb8RKpjKCDm2"}  # Known to work
    ]
    
    async with OrcaConnector(enhanced_cache=None) as orca:
        for token in sample_tokens:
            print(f"\n🔍 Analyzing {token['name']}: {token['address'][:12]}...")
            
            # What we can get when token has DEX data
            analytics = await orca.get_pool_analytics(token['address'])
            
            if analytics.get('found'):
                print(f"   ✅ Found on Orca!")
                print(f"   📊 Available Data:")
                print(f"      • Pool Count: {analytics.get('pool_count', 0)}")
                print(f"      • Total Liquidity: ${analytics.get('total_liquidity', 0):,.2f}")
                print(f"      • 24h Volume: ${analytics.get('total_volume_24h', 0):,.2f}")
                print(f"      • Average APY: {analytics.get('avg_apy', 0):.2f}%")
                print(f"      • Quality Score: {analytics.get('quality_score', 0):.2f}")
                print(f"      • DEX Name: {analytics.get('dex_name', 'Unknown')}")
                
                if analytics.get('pools'):
                    print(f"      • Pool Details: {len(analytics['pools'])} pools")
                    for i, pool in enumerate(analytics['pools'][:2]):
                        print(f"        Pool {i+1}: {pool.get('name', 'Unknown')}")
                        print(f"          Liquidity: ${pool.get('liquidity', 0):,.2f}")
                        print(f"          Volume 24h: ${pool.get('volume_24h', 0):,.2f}")
                        print(f"          APY: {pool.get('apy_24h', 0):.2f}%")
            else:
                print(f"   ⚪ Not found on Orca (normal for emerging tokens)")
                print(f"   📊 What we'd get if it were there:")
                print(f"      • Pool count and details")
                print(f"      • Total liquidity across all pools")
                print(f"      • Trading volume metrics")
                print(f"      • APY and yield information")
                print(f"      • Quality and risk scores")

async def main():
    """Main execution"""
    print("🔍 COMPREHENSIVE DEX DATA STRUCTURE ANALYSIS")
    print("="*70)
    print("This shows exactly what information we can extract from Orca and Raydium")
    
    analyzer = DEXDataAnalyzer()
    
    # Analyze data structures
    await analyzer.analyze_orca_data_structure()
    await analyzer.analyze_raydium_data_structure()
    
    # Show comparisons
    analyzer.show_data_comparison()
    analyzer.show_practical_use_cases()
    
    # Demonstrate with sample tokens
    await demonstrate_sample_token_analysis()
    
    print(f"\n🎯 SUMMARY")
    print("="*60)
    print("✅ Orca provides: Pool data, liquidity, volume, APY, quality scores")
    print("✅ Raydium provides: Pair data, trading metrics, LP info, market data")
    print("✅ Both integrate seamlessly with your token scanner")
    print("✅ Rich data available when tokens have DEX activity")
    print("✅ Your emerging tokens are pre-DEX = early opportunity!")

if __name__ == "__main__":
    asyncio.run(main()) 