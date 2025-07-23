#!/usr/bin/env python3
"""
Whale Discovery Script

Demonstrates how to use Birdeye API to discover and validate whale wallets.
Shows practical curl commands and implements automated whale discovery.
"""

import asyncio
import os
import sys
import json
import subprocess
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.whale_discovery_service import WhaleDiscoveryService
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager

def show_curl_examples():
    """Show practical curl commands for whale discovery"""
    print("🔍 PRACTICAL CURL COMMANDS FOR WHALE DISCOVERY")
    print("=" * 70)
    
    api_key = "YOUR_API_KEY_HERE"
    
    print("\n1️⃣ GET TOP TRADERS FOR A TOKEN:")
    print("-" * 40)
    curl_cmd1 = f'''curl -X GET "https://public-api.birdeye.so/defi/v2/tokens/top_traders?address=So11111111111111111111111111111111111111112" \\
  -H "x-chain: solana" \\
  -H "X-API-KEY: {api_key}"'''
    print(curl_cmd1)
    
    print("\n2️⃣ GET TOKEN HOLDERS:")
    print("-" * 40)
    curl_cmd2 = f'''curl -X GET "https://public-api.birdeye.so/defi/token_holder?address=So11111111111111111111111111111111111111112" \\
  -H "x-chain: solana" \\
  -H "X-API-KEY: {api_key}"'''
    print(curl_cmd2)
    
    print("\n3️⃣ GET TOP GAINING TRADERS:")
    print("-" * 40)
    curl_cmd3 = f'''curl -X GET "https://public-api.birdeye.so/defi/v2/trader_gainers_losers?type=gainers&offset=0&limit=10" \\
  -H "x-chain: solana" \\
  -H "X-API-KEY: {api_key}"'''
    print(curl_cmd3)
    
    print("\n4️⃣ GET WALLET PORTFOLIO:")
    print("-" * 40)
    curl_cmd4 = f'''curl -X GET "https://public-api.birdeye.so/defi/wallet_portfolio?wallet=WALLET_ADDRESS" \\
  -H "x-chain: solana" \\
  -H "X-API-KEY: {api_key}"'''
    print(curl_cmd4)
    
    print("\n5️⃣ GET HIGH-VOLUME TOKENS FOR ANALYSIS:")
    print("-" * 40)
    curl_cmd5 = f'''curl -X GET "https://public-api.birdeye.so/defi/v3/token/list?sort_by=volume_24h_usd&sort_type=desc&min_liquidity=1000000&limit=20" \\
  -H "x-chain: solana" \\
  -H "X-API-KEY: {api_key}"'''
    print(curl_cmd5)
    
    print("\n6️⃣ GET ALL-TIME TRADES FOR MULTIPLE TOKENS:")
    print("-" * 40)
    curl_cmd6 = f'''curl -X POST "https://public-api.birdeye.so/defi/v3/all-time/trades/multiple" \\
  -H "x-chain: solana" \\
  -H "X-API-KEY: {api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{"time_frame": "24h", "list_address": "So11111111111111111111111111111111111111112,mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So"}}'
'''
    print(curl_cmd6)

def execute_sample_curl(api_key: str, endpoint_type: str = "top_traders") -> Dict[str, Any]:
    """Execute a sample curl command to demonstrate API usage"""
    
    if endpoint_type == "top_traders":
        # Get top traders for wrapped SOL
        cmd = [
            "curl", "-X", "GET",
            "https://public-api.birdeye.so/defi/v2/tokens/top_traders?address=So11111111111111111111111111111111111111112",
            "-H", "x-chain: solana",
            "-H", f"X-API-KEY: {api_key}",
            "-s"  # Silent mode
        ]
    elif endpoint_type == "gainers":
        # Get top gaining traders
        cmd = [
            "curl", "-X", "GET", 
            "https://public-api.birdeye.so/defi/v2/trader_gainers_losers?type=gainers&offset=0&limit=10",
            "-H", "x-chain: solana",
            "-H", f"X-API-KEY: {api_key}",
            "-s"
        ]
    else:
        return {"error": "Unknown endpoint type"}
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": f"Curl failed: {result.stderr}"}
    except Exception as e:
        return {"error": f"Execution failed: {e}"}

async def demo_whale_discovery():
    """Demonstrate automated whale discovery using the service"""
    print("\n🐋 AUTOMATED WHALE DISCOVERY DEMONSTRATION")
    print("=" * 70)
    
    # Initialize configuration and API
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    birdeye_config = config.get('BIRDEYE_API', {})
    birdeye_api = BirdeyeAPI(config=birdeye_config)
    
    # Initialize whale discovery service
    discovery_service = WhaleDiscoveryService(birdeye_api)
    
    print("🔍 Starting whale discovery process...")
    print("This will analyze top tokens and identify high-quality whale wallets")
    
    try:
        # Discover new whales (limit to 10 for demo)
        new_whales = await discovery_service.discover_new_whales(max_discoveries=10)
        
        if new_whales:
            print(f"\n✅ Successfully discovered {len(new_whales)} new whale wallets:")
            print("-" * 60)
            
            for i, whale in enumerate(new_whales, 1):
                print(f"{i}. Whale {whale.address[:8]}...{whale.address[-4:]}")
                print(f"   💰 Tier: {whale.tier} | Avg Position: ${whale.avg_position:,.0f}")
                print(f"   📈 Success Rate: {whale.success_rate:.1%} | Confidence: {whale.confidence_score:.1%}")
                print(f"   🎯 Known For: {whale.known_for}")
                print(f"   📊 Tokens Traded: {whale.tokens_traded} | Total PnL: ${whale.total_pnl:,.0f}")
                print()
            
            # Show updated whale database stats
            stats = discovery_service.get_discovery_stats()
            print("📊 WHALE DATABASE STATISTICS:")
            print(f"   Total Whales: {stats['total_whales']}")
            print(f"   Tier 1 (Mega): {stats['tier_distribution'][1]}")
            print(f"   Tier 2 (Large): {stats['tier_distribution'][2]}")  
            print(f"   Tier 3 (Medium): {stats['tier_distribution'][3]}")
            print(f"   Avg Success Rate: {stats['avg_success_rate']:.1%}")
            print(f"   Avg Confidence: {stats['avg_confidence_score']:.1%}")
            print(f"   Database File: {stats['database_file']}")
            
            # Update whale activity analyzer with new whales
            print("\n🔄 Updating whale activity analyzer with discoveries...")
            analyzer_format = discovery_service.get_whale_database_for_analyzer()
            print(f"✅ Updated analyzer with {len(analyzer_format)} whale profiles")
            
        else:
            print("❌ No new whales discovered. This could be due to:")
            print("   - API rate limits or errors")
            print("   - Strict validation criteria") 
            print("   - All quality whales already discovered")
            
    except Exception as e:
        print(f"❌ Error during whale discovery: {e}")
        print("💡 Try checking your API key and rate limits")

async def analyze_specific_wallet(wallet_address: str):
    """Analyze a specific wallet to see if it qualifies as a whale"""
    print(f"\n🔍 ANALYZING SPECIFIC WALLET: {wallet_address}")
    print("=" * 70)
    
    # Initialize API
    config_manager = ConfigManager()
    config = config_manager.get_config()
    birdeye_config = config.get('BIRDEYE_API', {})
    birdeye_api = BirdeyeAPI(config=birdeye_config)
    
    discovery_service = WhaleDiscoveryService(birdeye_api)
    
    try:
        # Validate and profile the wallet
        whale_profile = await discovery_service._validate_and_profile_whale(wallet_address)
        
        if whale_profile:
            print("✅ WALLET ANALYSIS RESULTS:")
            print(f"   🏷️  Name: {whale_profile.name}")
            print(f"   💰 Tier: {whale_profile.tier}")
            print(f"   💵 Average Position: ${whale_profile.avg_position:,.0f}")
            print(f"   📈 Success Rate: {whale_profile.success_rate:.1%}")
            print(f"   🎯 Known For: {whale_profile.known_for}")
            print(f"   💸 Total PnL: ${whale_profile.total_pnl:,.0f}")
            print(f"   🪙 Tokens Traded: {whale_profile.tokens_traded}")
            print(f"   📊 Confidence Score: {whale_profile.confidence_score:.1%}")
            
            # Check if meets criteria
            meets_criteria = discovery_service._meets_validation_criteria(whale_profile)
            print(f"\n🎯 MEETS WHALE CRITERIA: {'✅ YES' if meets_criteria else '❌ NO'}")
            
            if not meets_criteria:
                criteria = discovery_service.validation_criteria
                print("   Requirements not met:")
                if whale_profile.success_rate < criteria['min_success_rate']:
                    print(f"   - Success rate too low: {whale_profile.success_rate:.1%} < {criteria['min_success_rate']:.1%}")
                if whale_profile.total_pnl < criteria['min_total_pnl']:
                    print(f"   - Total PnL too low: ${whale_profile.total_pnl:,.0f} < ${criteria['min_total_pnl']:,.0f}")
                if whale_profile.tokens_traded < criteria['min_tokens_traded']:
                    print(f"   - Not enough tokens traded: {whale_profile.tokens_traded} < {criteria['min_tokens_traded']}")
                if whale_profile.avg_position < criteria['min_avg_position']:
                    print(f"   - Average position too small: ${whale_profile.avg_position:,.0f} < ${criteria['min_avg_position']:,.0f}")
                if whale_profile.confidence_score < criteria['min_confidence_score']:
                    print(f"   - Confidence too low: {whale_profile.confidence_score:.1%} < {criteria['min_confidence_score']:.1%}")
        else:
            print("❌ Failed to analyze wallet (likely API error or invalid address)")
            
    except Exception as e:
        print(f"❌ Error analyzing wallet: {e}")

def main():
    """Main function to demonstrate whale discovery capabilities"""
    print("🐋 WHALE DISCOVERY SYSTEM")
    print("Automated whale wallet discovery using Birdeye API")
    print("=" * 70)
    
    # Show curl examples
    show_curl_examples()
    
    # Get API key from environment or config
    config_manager = ConfigManager()
    config = config_manager.get_config()
    api_key = config.get('BIRDEYE_API', {}).get('api_key')
    
    if not api_key:
        print("\n❌ No Birdeye API key found!")
        print("Please set your API key in the configuration or environment.")
        return
    
    print(f"\n📡 Testing API connection with curl...")
    
    # Test API with curl
    result = execute_sample_curl(api_key, "gainers")
    if "error" not in result:
        print("✅ API connection successful!")
        if 'data' in result and result['data']:
            print(f"📊 Found {len(result['data'])} top gaining traders")
            
            # Show first few traders
            for i, trader in enumerate(result['data'][:3], 1):
                address = trader.get('address', 'Unknown')
                pnl = trader.get('total_pnl', 0)
                win_rate = trader.get('win_rate', 0)
                print(f"   {i}. {address[:8]}... | PnL: ${pnl:,.0f} | Win Rate: {win_rate:.1%}")
    else:
        print(f"❌ API test failed: {result['error']}")
        return
    
    # Run automated discovery
    print("\n" + "="*70)
    asyncio.run(demo_whale_discovery())
    
    # Example: Analyze a specific wallet (you can replace with any wallet address)
    # example_wallet = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Example address
    # asyncio.run(analyze_specific_wallet(example_wallet))

if __name__ == "__main__":
    main() 