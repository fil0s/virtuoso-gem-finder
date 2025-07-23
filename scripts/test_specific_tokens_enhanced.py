#!/usr/bin/env python3
"""
Test Enhanced Endpoint Integration with Specific Tokens

This script tests the enhanced endpoint integration using specific token addresses
to verify trending analysis, smart money detection, and holder distribution analysis.
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from services.trending_token_monitor import TrendingTokenMonitor
from services.smart_money_detector import SmartMoneyDetector
from services.holder_distribution_analyzer import HolderDistributionAnalyzer
from utils.env_loader import load_environment
import yaml

# Test token addresses
TEST_TOKENS = [
    "9b1BzC1af9gQBtegh5WcuFB6ARBYQk7PgURW1aogpump",
    "9civd7ktdbBtSUgkyduxQoHhBLtThf9xr1Kvj5dcpump", 
    "rCDpCrYepyYffZz7AQhBV1LMJvWo7mps8fWr4Bvpump",
    "69G8CpUVZAxbPMiEBrfCCCH445NwFxH6PzVL693Xpump",
    "4jXJcKQoojvFuA7MSzJLpgDvXyiACqLnMyh6ULEEnVhg",
    "8jFpBJoJwHkYLgNgequJJu6CMt3LkY3P6QndUupLpump"
]

async def test_enhanced_services():
    """Test the enhanced endpoint integration services with specific tokens."""
    
    print("🧪 Testing Enhanced Endpoint Integration with Specific Tokens")
    print("=" * 60)
    print(f"📅 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing {len(TEST_TOKENS)} specific tokens")
    print()
    
    # Load environment and config
    load_environment()
    
    config_file = 'config/config.enhanced.yaml'
    if not os.path.exists(config_file):
        config_file = 'config/config.yaml'
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize services
    from core.cache_manager import CacheManager
    from services.rate_limiter_service import RateLimiterService
    from services.logger_setup import LoggerSetup
    
    logger_setup = LoggerSetup('EnhancedTokenTest')
    logger = logger_setup.logger
    
    cache_manager = CacheManager()
    rate_limiter = RateLimiterService()
    
    birdeye_config = config.get('BIRDEYE_API', {})
    birdeye_config['api_key'] = os.environ.get('BIRDEYE_API_KEY')
    
    birdeye_api = BirdeyeAPI(
        config=birdeye_config,
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    # Initialize enhanced services
    trending_monitor = TrendingTokenMonitor(birdeye_api, logger)
    smart_money_detector = SmartMoneyDetector(birdeye_api, logger)
    holder_analyzer = HolderDistributionAnalyzer(birdeye_api, logger)
    
    results = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "tokens_tested": len(TEST_TOKENS),
            "config_used": config_file
        },
        "trending_analysis": {},
        "smart_money_analysis": {},
        "holder_distribution_analysis": {},
        "enhanced_scoring_results": {}
    }
    
    # Test 1: Trending Analysis
    print("📈 TEST 1: Trending Token Analysis")
    print("-" * 40)
    
    try:
        # Get general trending tokens first
        trending_tokens = await trending_monitor.get_trending_tokens(limit=50)
        print(f"✅ Found {len(trending_tokens)} trending tokens")
        
        # Check each test token for trending status
        for i, token_address in enumerate(TEST_TOKENS, 1):
            print(f"\n🔍 Analyzing token {i}/{len(TEST_TOKENS)}: {token_address[:8]}...")
            
            trending_status = await trending_monitor.check_token_trending_status(token_address)
            results["trending_analysis"][token_address] = trending_status
            
            if trending_status["is_trending"]:
                print(f"   🔥 TRENDING! Rank: {trending_status['trending_rank']}, Score: {trending_status['trending_score']:.3f}")
                print(f"   📊 Score Boost: {trending_status['score_boost']:.2f}x")
            else:
                print(f"   📊 Not trending (Score Boost: {trending_status['score_boost']:.2f}x)")
                
    except Exception as e:
        print(f"❌ Trending analysis failed: {e}")
        results["trending_analysis"]["error"] = str(e)
    
    print(f"\n⏳ Waiting 3 seconds before next test...")
    await asyncio.sleep(3)
    
    # Test 2: Smart Money Detection
    print("\n🧠 TEST 2: Smart Money Detection")
    print("-" * 40)
    
    try:
        for i, token_address in enumerate(TEST_TOKENS, 1):
            print(f"\n🔍 Analyzing traders for token {i}/{len(TEST_TOKENS)}: {token_address[:8]}...")
            
            trader_analysis = await smart_money_detector.analyze_token_traders(token_address, limit=20)
            results["smart_money_analysis"][token_address] = trader_analysis
            
            smart_traders_count = trader_analysis.get("smart_traders_count", 0)
            smart_money_level = trader_analysis.get("smart_money_level", "unknown")
            score_boost = trader_analysis.get("score_boost", 1.0)
            
            if smart_traders_count > 0:
                print(f"   💰 Smart Money Detected! Level: {smart_money_level}")
                print(f"   👥 Smart Traders: {smart_traders_count}")
                print(f"   📈 Score Boost: {score_boost:.2f}x")
            else:
                print(f"   📊 No smart money detected (Level: {smart_money_level})")
                
            # Small delay between tokens
            await asyncio.sleep(1)
                
    except Exception as e:
        print(f"❌ Smart money analysis failed: {e}")
        results["smart_money_analysis"]["error"] = str(e)
    
    print(f"\n⏳ Waiting 3 seconds before next test...")
    await asyncio.sleep(3)
    
    # Test 3: Holder Distribution Analysis
    print("\n👥 TEST 3: Holder Distribution Analysis")
    print("-" * 40)
    
    try:
        for i, token_address in enumerate(TEST_TOKENS, 1):
            print(f"\n🔍 Analyzing holders for token {i}/{len(TEST_TOKENS)}: {token_address[:8]}...")
            
            holder_analysis = await holder_analyzer.analyze_holder_distribution(token_address, limit=100)
            results["holder_distribution_analysis"][token_address] = holder_analysis
            
            risk_assessment = holder_analysis.get("risk_assessment", {})
            risk_level = risk_assessment.get("risk_level", "unknown")
            is_high_risk = risk_assessment.get("is_high_risk", True)
            score_multiplier = holder_analysis.get("score_adjustment", {}).get("score_multiplier", 1.0)
            total_holders = holder_analysis.get("total_holders", 0)
            
            if is_high_risk:
                print(f"   ⚠️ HIGH RISK! Level: {risk_level}")
                print(f"   📉 Score Penalty: {score_multiplier:.2f}x")
            else:
                print(f"   ✅ Acceptable Risk (Level: {risk_level})")
                print(f"   📈 Score Adjustment: {score_multiplier:.2f}x")
            
            print(f"   👥 Total Holders: {total_holders}")
            
            # Small delay between tokens
            await asyncio.sleep(1)
                
    except Exception as e:
        print(f"❌ Holder distribution analysis failed: {e}")
        results["holder_distribution_analysis"]["error"] = str(e)
    
    # Test 4: Enhanced Scoring Simulation
    print("\n🎯 TEST 4: Enhanced Scoring Simulation")
    print("-" * 40)
    
    for i, token_address in enumerate(TEST_TOKENS, 1):
        print(f"\n📊 Enhanced scoring for token {i}/{len(TEST_TOKENS)}: {token_address[:8]}...")
        
        # Simulate enhanced scoring using the analysis results
        base_score = 50.0  # Starting score
        enhanced_score = base_score
        enhancement_factors = []
        
        # Apply trending boost
        trending_data = results["trending_analysis"].get(token_address, {})
        if trending_data and not isinstance(trending_data, str):  # Not an error
            trending_boost = trending_data.get("score_boost", 1.0)
            if trending_boost > 1.0:
                enhanced_score *= trending_boost
                enhancement_factors.append(f"Trending: {trending_boost:.2f}x")
        
        # Apply smart money boost
        smart_money_data = results["smart_money_analysis"].get(token_address, {})
        if smart_money_data and not isinstance(smart_money_data, str):  # Not an error
            smart_money_boost = smart_money_data.get("score_boost", 1.0)
            if smart_money_boost > 1.0:
                enhanced_score *= smart_money_boost
                enhancement_factors.append(f"Smart Money: {smart_money_boost:.2f}x")
        
        # Apply holder distribution adjustment
        holder_data = results["holder_distribution_analysis"].get(token_address, {})
        if holder_data and not isinstance(holder_data, str):  # Not an error
            holder_adjustment = holder_data.get("score_adjustment", {}).get("score_multiplier", 1.0)
            enhanced_score *= holder_adjustment
            if holder_adjustment != 1.0:
                enhancement_factors.append(f"Holder Quality: {holder_adjustment:.2f}x")
        
        # Calculate total enhancement
        total_enhancement = enhanced_score / base_score if base_score > 0 else 1.0
        
        results["enhanced_scoring_results"][token_address] = {
            "base_score": base_score,
            "enhanced_score": round(enhanced_score, 2),
            "total_enhancement": round(total_enhancement, 3),
            "enhancement_factors": enhancement_factors
        }
        
        print(f"   📊 Base Score: {base_score}")
        print(f"   🚀 Enhanced Score: {enhanced_score:.2f}")
        print(f"   📈 Total Enhancement: {total_enhancement:.3f}x")
        if enhancement_factors:
            print(f"   🎯 Factors: {', '.join(enhancement_factors)}")
        else:
            print(f"   ➡️ No enhancements applied")
    
    # Save results
    results_dir = Path("scripts/results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"enhanced_tokens_test_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print(f"\n🎉 Enhanced Endpoint Integration Test Complete!")
    print("=" * 50)
    
    # Count successful analyses
    trending_success = sum(1 for v in results["trending_analysis"].values() if not isinstance(v, str))
    smart_money_success = sum(1 for v in results["smart_money_analysis"].values() if not isinstance(v, str))
    holder_success = sum(1 for v in results["holder_distribution_analysis"].values() if not isinstance(v, str))
    
    print(f"📈 Trending Analysis: {trending_success}/{len(TEST_TOKENS)} successful")
    print(f"🧠 Smart Money Analysis: {smart_money_success}/{len(TEST_TOKENS)} successful")
    print(f"👥 Holder Analysis: {holder_success}/{len(TEST_TOKENS)} successful")
    
    # Enhancement summary
    enhanced_tokens = [addr for addr, data in results["enhanced_scoring_results"].items() 
                      if data["total_enhancement"] > 1.0]
    
    print(f"🚀 Enhanced Tokens: {len(enhanced_tokens)}/{len(TEST_TOKENS)}")
    
    if enhanced_tokens:
        print(f"\n🎯 Top Enhanced Tokens:")
        sorted_tokens = sorted(
            [(addr, data["total_enhancement"]) for addr, data in results["enhanced_scoring_results"].items()],
            key=lambda x: x[1], reverse=True
        )
        
        for addr, enhancement in sorted_tokens[:3]:
            print(f"   {addr[:8]}... - {enhancement:.3f}x enhancement")
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_enhanced_services()) 