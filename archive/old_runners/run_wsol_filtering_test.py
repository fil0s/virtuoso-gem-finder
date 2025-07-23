#!/usr/bin/env python3
"""
Live WSOL-Only Filtering Test

Quick test to run the cross-platform analyzer with WSOL-only filtering
and see the actual results compared to all-pairs mode.
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer, WSOL_ADDRESS, WSOL_ONLY_MODE

async def run_wsol_filtering_test():
    """Run live test of WSOL-only filtering"""
    print("🪙 WSOL-Only Filtering Live Test")
    print("=" * 50)
    print(f"🎯 WSOL Address: {WSOL_ADDRESS}")
    print(f"⚙️ WSOL Only Mode: {WSOL_ONLY_MODE}")
    print(f"🕐 Starting test at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    analyzer = None
    try:
        # Initialize analyzer
        print("🚀 Initializing CrossPlatformAnalyzer...")
        analyzer = CrossPlatformAnalyzer()
        
        # Run analysis
        print("📊 Running cross-platform analysis...")
        start_time = time.time()
        results = await analyzer.run_analysis()
        execution_time = time.time() - start_time
        
        # Extract key metrics
        if 'error' in results:
            print(f"❌ Analysis failed: {results['error']}")
            return
        
        correlations = results.get('correlations', {})
        all_tokens = correlations.get('all_tokens', {})
        multi_platform_tokens = correlations.get('multi_platform_tokens', [])
        high_conviction_tokens = correlations.get('high_conviction_tokens', [])
        
        # Analyze WSOL-specific tokens by checking normalized data structure
        wsol_paired_tokens = []
        
        # Check normalized token data for is_wsol_pair flags in platform-specific data
        for token_addr, token_info in all_tokens.items():
            token_data = token_info.get('data', {})
            wsol_platforms = []
            
            # Check each platform's data for is_wsol_pair flag
            for platform in ['meteora', 'orca', 'raydium']:
                platform_data = token_data.get(platform, {})
                if platform_data.get('is_wsol_pair', False):
                    wsol_platforms.append(platform)
            
            if wsol_platforms:
                wsol_paired_tokens.append({
                    'address': token_addr,
                    'symbol': token_info.get('symbol', 'Unknown'),
                    'platforms': list(token_info.get('platforms', [])),
                    'wsol_platforms': wsol_platforms,
                    'score': token_info.get('score', 0)
                })
        
        # Sort by score
        wsol_paired_tokens.sort(key=lambda x: x['score'], reverse=True)
        
        # Display results
        print("\n📈 ANALYSIS RESULTS")
        print("-" * 30)
        print(f"⏱️  Execution time: {execution_time:.1f}s")
        print(f"🎯 Total unique tokens: {len(all_tokens)}")
        print(f"🪙 WSOL-paired tokens: {len(wsol_paired_tokens)}")
        print(f"✅ Multi-platform tokens: {len(multi_platform_tokens)}")
        print(f"💎 High-conviction tokens: {len(high_conviction_tokens)}")
        
        # Platform distribution
        platform_counts = correlations.get('platform_analysis', {}).get('distribution', {})
        print(f"\n📊 Platform Distribution:")
        for platform, count in sorted(platform_counts.items()):
            print(f"  • {platform}: {count} tokens")
        
        # Show top WSOL-paired tokens
        if wsol_paired_tokens:
            print(f"\n🪙 Top WSOL-Paired Tokens:")
            for i, token in enumerate(wsol_paired_tokens[:10], 1):
                symbol = token['symbol']
                score = token['score']
                platforms = ', '.join(token['wsol_platforms'])
                address = token['address'][:8] + "..."
                print(f"  {i:2d}. {symbol:12s} | Score: {score:5.1f} | {platforms:20s} | {address}")
        
        # Show high conviction tokens
        if high_conviction_tokens:
            print(f"\n💎 High-Conviction Tokens:")
            for i, token in enumerate(high_conviction_tokens[:5], 1):
                symbol = token.get('symbol', 'Unknown')
                score = token.get('score', 0)
                platforms = len(token.get('platforms', []))
                address = token.get('address', '')[:8] + "..."
                volume = token.get('volume_24h', 0)
                print(f"  {i}. {symbol:12s} | Score: {score:5.1f} | {platforms} platforms | ${volume:,.0f} vol | {address}")
        
        # API usage stats
        cache_stats = results.get('cache_statistics', {})
        print(f"\n📊 Performance Metrics:")
        print(f"  💰 Cache hit rate: {cache_stats.get('hit_rate_percent', 0):.1f}%")
        print(f"  💸 Estimated savings: ${cache_stats.get('estimated_cost_savings_usd', 0):.4f}")
        
        # Save results
        timestamp = int(time.time())
        output_file = f"wsol_filtering_live_test_{timestamp}.json"
        
        test_summary = {
            'timestamp': datetime.now().isoformat(),
            'wsol_address': WSOL_ADDRESS,
            'wsol_only_mode': WSOL_ONLY_MODE,
            'execution_time_seconds': execution_time,
            'total_tokens': len(all_tokens),
            'wsol_paired_tokens': len(wsol_paired_tokens),
            'multi_platform_tokens': len(multi_platform_tokens),
            'high_conviction_tokens': len(high_conviction_tokens),
            'platform_distribution': platform_counts,
            'top_wsol_tokens': wsol_paired_tokens[:10],
            'cache_statistics': cache_stats,
            'full_results': results
        }
        
        with open(output_file, 'w') as f:
            json.dump(test_summary, f, indent=2)
        
        print(f"\n📁 Full results saved to: {output_file}")
        
        # Key insights
        print(f"\n🔍 Key Insights:")
        wsol_ratio = (len(wsol_paired_tokens) / len(all_tokens) * 100) if all_tokens else 0
        print(f"  • {wsol_ratio:.1f}% of tokens have WSOL pairs")
        
        if WSOL_ONLY_MODE:
            print(f"  • WSOL-only filtering is ACTIVE - focusing on SOL-based liquidity")
        else:
            print(f"  • All-pairs mode - analyzing all token pairs")
        
        insights = results.get('insights', [])
        for insight in insights[:3]:
            print(f"  • {insight}")
        
        print("\n🎉 Live test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
    
    finally:
        if analyzer:
            await analyzer.close()

async def main():
    """Main execution"""
    await run_wsol_filtering_test()

if __name__ == "__main__":
    asyncio.run(main()) 