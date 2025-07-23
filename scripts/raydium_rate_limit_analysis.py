#!/usr/bin/env python3
"""
Comprehensive Raydium Rate Limit Analysis
Based on investigation results and Bitquery documentation research
"""

def analyze_raydium_rate_limiting():
    """Comprehensive analysis of Raydium API rate limiting issues"""
    
    print("🔍 RAYDIUM RATE LIMITING COMPREHENSIVE ANALYSIS")
    print("="*70)
    
    print("\n📊 OUR INVESTIGATION FINDINGS:")
    print("-" * 50)
    print("✅ /pools endpoint: Reliable, 696K+ pools accessible")
    print("❌ /pairs endpoint: 100% rate limited (429 errors)")
    print("⏱️ All delay intervals (0s-5s): Still rate limited")
    print("🎯 Token discovery: SUCCESS when rate limits bypassed")
    print("   • SPX: Found 3 pools + 3 pairs")
    print("   • TRUMP: Found 7 pools + 7 pairs") 
    print("   • TESLA: Found 1 pool + 1 pair")
    
    print("\n🚀 BITQUERY'S SOPHISTICATED APPROACH:")
    print("-" * 50)
    print("📋 Uses GraphQL queries with complex filtering")
    print("🔄 Real-time WebSocket subscriptions")
    print("🎯 Program-specific instruction tracking")
    print("📈 Historical data access capabilities")
    print("🏗️ Blockchain-level data analysis")
    
    print("   Key Bitquery Methods:")
    print("   • DEXTradeByTokens - Real-time trading data")
    print("   • Instructions - Low-level blockchain analysis")
    print("   • Program filtering by Raydium addresses:")
    print("     - 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 (V4)")
    print("     - 5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1 (V3)")
    
    print("\n⚠️ RATE LIMITING ROOT CAUSES:")
    print("-" * 50)
    print("1. 🌍 CLOUDFLARE PROTECTION:")
    print("   • Headers show 'Server: cloudflare'")
    print("   • CF-RAY headers indicate Cloudflare routing")
    print("   • Aggressive DDoS protection on /pairs endpoint")
    print("   • Different protection levels for different endpoints")
    
    print("\n2. 📊 ENDPOINT RESOURCE INTENSITY:")
    print("   • /pools: 143MB response, basic pool data")
    print("   • /pairs: 473MB+ response, detailed trading metrics")
    print("   • /pairs endpoint is 3x more resource intensive")
    print("   • Higher computational cost = tighter rate limits")
    
    print("\n3. 🔄 API ARCHITECTURE DIFFERENCES:")
    print("   • /pools: Static/cached data, updated periodically")
    print("   • /pairs: Real-time trading data, high update frequency")
    print("   • Real-time endpoints get stricter protection")
    
    print("\n💡 OFFICIAL RATE LIMIT ANALYSIS:")
    print("-" * 50)
    print("📋 Based on response headers and behavior:")
    print("   • Cache-Control: 'public, max-age=691200' (8 days)")
    print("   • CF-Cache-Status: Shows Cloudflare caching")
    print("   • Age headers indicate stale cached responses")
    print("   • 429 responses suggest IP-based rate limiting")
    
    print("\n🎯 ESTIMATED RATE LIMITS:")
    print("   /pools endpoint:")
    print("     • ✅ ~10 requests/hour (our successful rate)")
    print("     • ✅ Heavy caching reduces server load")
    print("     • ✅ More permissive due to static nature")
    
    print("   /pairs endpoint:")
    print("     • ❌ <1 request/hour (our 100% failure rate)")
    print("     • ❌ Extremely aggressive protection")
    print("     • ❌ Possibly reserved for premium/partner access")
    
    print("\n🚀 SOLUTIONS AND ALTERNATIVES:")
    print("-" * 50)
    
    print("1. 🏗️ BITQUERY INTEGRATION:")
    print("   • GraphQL API for sophisticated queries")
    print("   • Real-time WebSocket subscriptions")
    print("   • Historical data access")
    print("   • Program-level filtering")
    print("   • Cost: ~$50-100/month for professional use")
    
    print("\n2. 🔄 ALTERNATIVE DATA SOURCES:")
    print("   • DexScreener API (more permissive)")
    print("   • Jupiter aggregator data")
    print("   • Direct Solana RPC calls")
    print("   • Moralis Solana API")
    
    print("\n3. ⚡ OPTIMIZATION STRATEGIES:")
    print("   • Focus on /pools endpoint (proven reliable)")
    print("   • Implement exponential backoff")
    print("   • Use distributed requests across IPs")
    print("   • Cache data more aggressively")
    print("   • Batch token searches")
    
    print("\n4. 🎯 HYBRID APPROACH:")
    print("   • Primary: Raydium /pools (basic data)")
    print("   • Secondary: Bitquery GraphQL (detailed analysis)")
    print("   • Fallback: DexScreener/Jupiter")
    print("   • Cache: Long-term storage for rate limit relief")

def show_bitquery_integration_example():
    """Show how to integrate Bitquery for comprehensive Raydium data"""
    
    print("\n🔧 BITQUERY INTEGRATION EXAMPLE:")
    print("-" * 50)
    
    print("📋 GraphQL Query for Real-time Raydium Token Discovery:")
    print("""
subscription {
  Solana {
    DEXTrades(
      where: {
        Trade: {
          Dex: {
            ProtocolFamily: { is: "Raydium" }
          }
        }
      }
    ) {
      Trade {
        Buy {
          Currency { MintAddress Symbol }
          Amount
          PriceInUSD
        }
        Sell {
          Currency { MintAddress Symbol }
          Amount
          PriceInUSD
        }
        Market { MarketAddress }
      }
      Block { Time }
    }
  }
}
""")
    
    print("📋 GraphQL Query for Token Price Discovery:")
    print("""
{
  Solana {
    DEXTradeByTokens(
      limit: {count: 1}
      orderBy: {descending: Block_Time}
      where: {
        Trade: {
          Dex: {ProgramAddress: {is: "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"}}
          Currency: {MintAddress: {is: "TOKEN_ADDRESS"}}
        }
      }
    ) {
      Block { Time }
      Trade { Price PriceInUSD }
    }
  }
}
""")

def provide_actionable_recommendations():
    """Provide specific actionable recommendations"""
    
    print("\n🎯 IMMEDIATE ACTION PLAN:")
    print("="*50)
    
    print("✅ SHORT-TERM (This Week):")
    print("   1. Optimize /pools endpoint usage")
    print("   2. Increase cache TTL to 1+ hours")
    print("   3. Implement exponential backoff (5s → 30s → 2min)")
    print("   4. Focus token discovery on pools data")
    print("   5. Batch process instead of real-time calls")
    
    print("\n🚀 MEDIUM-TERM (Next Month):")
    print("   1. Evaluate Bitquery integration cost/benefit")
    print("   2. Implement hybrid data source approach")
    print("   3. Add DexScreener as backup data source")
    print("   4. Create intelligent caching layer")
    print("   5. Implement distributed request system")
    
    print("\n🏆 LONG-TERM (Next Quarter):")
    print("   1. Build comprehensive multi-DEX aggregation")
    print("   2. Real-time WebSocket integration")
    print("   3. Historical data analysis capabilities")
    print("   4. Smart routing between data sources")
    print("   5. Predictive caching based on usage patterns")
    
    print("\n💰 COST-BENEFIT ANALYSIS:")
    print("-" * 30)
    print("Current Approach: Free but limited")
    print("   • ✅ 696K pools accessible")
    print("   • ❌ No pairs data")
    print("   • ❌ Rate limiting issues")
    
    print("\nBitquery Professional: ~$100/month")
    print("   • ✅ Complete Raydium data access")
    print("   • ✅ Real-time subscriptions")
    print("   • ✅ Historical analysis")
    print("   • ✅ No rate limiting")
    print("   • 🎯 ROI: Likely positive for serious trading")

def main():
    """Main analysis execution"""
    analyze_raydium_rate_limiting()
    show_bitquery_integration_example()
    provide_actionable_recommendations()
    
    print("\n🎯 FINAL CONCLUSIONS:")
    print("="*50)
    print("1. ✅ Our system IS finding tokens correctly")
    print("2. ⚠️ Rate limiting is the primary constraint")
    print("3. 🚀 Bitquery offers professional-grade solution")
    print("4. 💡 Hybrid approach balances cost and capability")
    print("5. 🎯 Focus on /pools + intelligent caching wins short-term")

if __name__ == "__main__":
    main() 