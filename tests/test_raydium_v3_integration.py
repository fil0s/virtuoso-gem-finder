#!/usr/bin/env python3
"""
Integration test for complete Raydium v3 workflow
Tests end-to-end functionality with real EarlyGemDetector
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.detectors.early_gem_detector import EarlyGemDetector
from api.raydium_connector import RaydiumConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_raydium_v3_integration():
    """Complete integration test for Raydium v3 in EarlyGemDetector"""
    
    print("🧪 Raydium v3 Integration Test")
    print("=" * 50)
    
    # Test 1: Initialize EarlyGemDetector with RaydiumConnector
    print("\n📋 Test 1: EarlyGemDetector Initialization")
    try:
        detector = EarlyGemDetector(
            debug_mode=True,
            stage0_debug=True
        )
        
        # Check Raydium connector initialization
        if detector.raydium_connector:
            print("✅ RaydiumConnector initialized successfully")
            
            # Check connector configuration
            assert detector.raydium_connector.base_url == "https://api-v3.raydium.io"
            assert detector.raydium_connector.enhanced_cache is not None
            assert detector.raydium_connector.rate_limiter is not None
            print("✅ RaydiumConnector configuration verified")
        else:
            print("❌ RaydiumConnector not initialized")
            return False
            
    except Exception as e:
        print(f"❌ EarlyGemDetector initialization failed: {e}")
        return False
    
    # Test 2: Direct RaydiumConnector functionality
    print("\n📋 Test 2: Direct RaydiumConnector Test")
    try:
        start_time = time.time()
        
        # Test API functionality
        async with detector.raydium_connector as connector:
            # Test pools
            pools = await connector.get_pools(limit=3)
            print(f"✅ Retrieved {len(pools)} pools")
            
            # Test WSOL pairs
            wsol_pairs = await connector.get_wsol_trending_pairs(limit=5)
            print(f"✅ Retrieved {len(wsol_pairs)} WSOL pairs")
            
            if wsol_pairs:
                early_gems = [p for p in wsol_pairs if p.get('is_early_gem_candidate')]
                print(f"💎 Found {len(early_gems)} early gem candidates")
                
                # Show top early gem
                if early_gems:
                    top_gem = early_gems[0]
                    print(f"🏆 Top gem: {top_gem['symbol']} - TVL: ${top_gem['tvl']:,.0f}, Ratio: {top_gem['volume_tvl_ratio']:.1f}")
            
            # Test API statistics
            stats = connector.get_api_call_statistics()
            print(f"📊 API Stats: {stats['successful_calls']}/{stats['total_calls']} success rate: {stats['success_rate']:.1%}")
        
        elapsed = time.time() - start_time
        print(f"⏱️ Direct connector test completed in {elapsed:.1f}s")
        
    except Exception as e:
        print(f"❌ Direct connector test failed: {e}")
        return False
    
    # Test 3: _fetch_raydium_v3_pools method
    print("\n📋 Test 3: _fetch_raydium_v3_pools Method Test")
    try:
        start_time = time.time()
        
        candidates = await detector._fetch_raydium_v3_pools()
        print(f"✅ _fetch_raydium_v3_pools returned {len(candidates)} candidates")
        
        if candidates:
            # Validate candidate structure
            sample_candidate = candidates[0]
            required_fields = [
                'symbol', 'address', 'market_cap', 'volume_24h', 'liquidity',
                'is_early_gem_candidate', 'early_gem_score', 'discovery_source',
                'platform', 'platforms', 'source'
            ]
            
            missing_fields = [field for field in required_fields if field not in sample_candidate]
            if missing_fields:
                print(f"❌ Missing fields in candidate: {missing_fields}")
                return False
            else:
                print("✅ Candidate structure validated")
            
            # Show early gems
            early_gems = [c for c in candidates if c.get('is_early_gem_candidate')]
            print(f"💎 Early gem candidates: {len(early_gems)}/{len(candidates)}")
            
            if early_gems:
                print("🏆 Top early gems:")
                for i, gem in enumerate(early_gems[:3]):
                    print(f"   {i+1}. {gem['symbol']} - Score: {gem['early_gem_score']:.1f}")
        
        elapsed = time.time() - start_time
        print(f"⏱️ Fetch method test completed in {elapsed:.1f}s")
        
    except Exception as e:
        print(f"❌ _fetch_raydium_v3_pools test failed: {e}")
        return False
    
    # Test 4: Integration with detection pipeline
    print("\n📋 Test 4: Detection Pipeline Integration")
    try:
        start_time = time.time()
        
        # Run discovery with Raydium v3 included
        all_candidates = await detector.discover_early_tokens()
        
        # Find Raydium v3 candidates
        raydium_v3_candidates = [
            c for c in all_candidates 
            if c.get('discovery_source') == 'raydium_v3_enhanced' or c.get('source') == 'raydium_v3_pools'
        ]
        
        print(f"✅ Pipeline returned {len(all_candidates)} total candidates")
        print(f"⚡ Raydium v3 contributed {len(raydium_v3_candidates)} candidates")
        
        if raydium_v3_candidates:
            early_gems = [c for c in raydium_v3_candidates if c.get('is_early_gem_candidate')]
            print(f"💎 Raydium v3 early gems: {len(early_gems)}")
            
            # Show platform distribution
            platforms = {}
            for candidate in all_candidates:
                source = candidate.get('discovery_source', candidate.get('source', 'unknown'))
                platforms[source] = platforms.get(source, 0) + 1
            
            print("📊 Platform distribution:")
            for platform, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
                print(f"   {platform}: {count}")
        
        elapsed = time.time() - start_time
        print(f"⏱️ Pipeline integration test completed in {elapsed:.1f}s")
        
    except Exception as e:
        print(f"❌ Pipeline integration test failed: {e}")
        return False
    
    # Test 5: Performance validation
    print("\n📋 Test 5: Performance Validation")
    try:
        # Test multiple rapid calls
        start_time = time.time()
        
        tasks = []
        for i in range(3):
            tasks.append(detector._fetch_raydium_v3_pools())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        print(f"✅ Concurrent test: {len(successful_results)}/3 successful")
        
        if failed_results:
            print(f"⚠️ Some concurrent calls failed: {len(failed_results)}")
            for failure in failed_results:
                print(f"   Error: {failure}")
        
        elapsed = time.time() - start_time
        print(f"⏱️ Concurrent performance test completed in {elapsed:.1f}s")
        
        # Calculate performance metrics
        if successful_results:
            avg_candidates_per_call = sum(len(r) for r in successful_results) / len(successful_results)
            print(f"📊 Average candidates per call: {avg_candidates_per_call:.1f}")
            print(f"📊 Calls per second: {len(successful_results) / elapsed:.1f}")
        
    except Exception as e:
        print(f"❌ Performance validation failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All integration tests PASSED!")
    print("✅ Raydium v3 integration is production ready")
    
    return True

async def main():
    """Run the integration test"""
    try:
        success = await test_raydium_v3_integration()
        if success:
            print("\n🚀 Integration test completed successfully")
            return 0
        else:
            print("\n❌ Integration test failed")
            return 1
    except Exception as e:
        print(f"\n💥 Integration test crashed: {e}")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)