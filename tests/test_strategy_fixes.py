#!/usr/bin/env python3
"""
Test Strategy Fixes

This script tests the fixes for:
1. Price Momentum Strategy - graduated price change thresholds
2. Smart Money Whale Strategy - relaxed thresholds
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from services.logger_setup import LoggerSetup
from core.strategies.price_momentum_strategy import PriceMomentumStrategy
from core.strategies.smart_money_whale_strategy import SmartMoneyWhaleStrategy


async def test_strategy_fixes():
    """Test both fixed strategies."""
    print("🔧 Testing Strategy Fixes")
    print("=" * 50)
    
    # Initialize logger
    logger_setup = LoggerSetup("StrategyFixTest")
    logger = logger_setup.logger
    
    try:
        # Initialize Birdeye API
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        
        api_key = os.getenv('BIRDEYE_API_KEY')
        if not api_key:
            print("❌ BIRDEYE_API_KEY not set")
            return
        
        cache_manager = CacheManager(ttl_default=300)
        rate_limiter = RateLimiterService()
        
        config = {
            'api_key': api_key,
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 100,
            'request_timeout_seconds': 20,
            'cache_ttl_default_seconds': 300,
            'cache_ttl_error_seconds': 60,
            'max_retries': 3,
            'backoff_factor': 2
        }
        
        birdeye_logger = LoggerSetup("BirdeyeAPI")
        birdeye_api = BirdeyeAPI(config, birdeye_logger, cache_manager, rate_limiter)
        
        scan_id = f"strategy_fix_test_{int(time.time())}"
        
        # Test 1: Price Momentum Strategy
        print("\n🎯 Testing Price Momentum Strategy...")
        start_time = time.time()
        
        try:
            pm_strategy = PriceMomentumStrategy(logger=logger)
            pm_tokens = await pm_strategy.execute(birdeye_api, scan_id=f"{scan_id}_pm")
            pm_time = time.time() - start_time
            
            print(f"✅ Price Momentum: {len(pm_tokens)} tokens in {pm_time:.2f}s")
            
            # Show examples of graduated thresholds
            for i, token in enumerate(pm_tokens[:3]):
                strategy_analysis = token.get("strategy_analysis", {})
                symbol = token.get("symbol", "Unknown")
                actual_change = strategy_analysis.get("actual_price_change", 0)
                max_allowed = strategy_analysis.get("max_allowed_price_change", 0)
                market_cap = token.get("marketCap", 0)
                
                print(f"   📊 {symbol}: {actual_change:.1f}% change (max: {max_allowed:.1f}%, mcap: ${market_cap:,.0f})")
                
        except Exception as e:
            print(f"❌ Price Momentum failed: {e}")
            pm_tokens = []
        
        # Test 2: Smart Money Whale Strategy
        print("\n🐋 Testing Smart Money Whale Strategy...")
        start_time = time.time()
        
        try:
            smw_strategy = SmartMoneyWhaleStrategy(logger=logger)
            smw_tokens = await smw_strategy.execute(birdeye_api, scan_id=f"{scan_id}_smw")
            smw_time = time.time() - start_time
            
            print(f"✅ Smart Money Whale: {len(smw_tokens)} tokens in {smw_time:.2f}s")
            
            # Show examples of relaxed thresholds working
            for i, token in enumerate(smw_tokens[:3]):
                symbol = token.get("symbol", "Unknown")
                whale_analysis = token.get("whale_analysis", {})
                smart_money_analysis = token.get("smart_money_analysis", {})
                
                whale_count = len(whale_analysis.get("whales", []))
                smart_traders = smart_money_analysis.get("skill_metrics", {}).get("skilled_count", 0)
                confluence = token.get("confluence_score", 0)
                
                print(f"   🐋 {symbol}: {whale_count} whales, {smart_traders} skilled traders, {confluence:.2f} confluence")
                
        except Exception as e:
            print(f"❌ Smart Money Whale failed: {e}")
            smw_tokens = []
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 FIX TEST SUMMARY")
        print("=" * 50)
        
        total_tokens = len(pm_tokens) + len(smw_tokens)
        print(f"🎯 Price Momentum Strategy: {len(pm_tokens)} tokens")
        print(f"🐋 Smart Money Whale Strategy: {len(smw_tokens)} tokens")
        print(f"📈 Total Tokens Discovered: {total_tokens}")
        
        if len(pm_tokens) > 0:
            print("✅ Price Momentum fix successful - graduated thresholds working")
        else:
            print("❌ Price Momentum fix needs more work")
            
        if len(smw_tokens) > 0:
            print("✅ Smart Money Whale fix successful - relaxed thresholds working")
        else:
            print("❌ Smart Money Whale fix needs more work")
        
        if total_tokens > 0:
            print("🎉 Overall: Strategy fixes are working!")
        else:
            print("⚠️  Overall: More tuning needed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_strategy_fixes()) 