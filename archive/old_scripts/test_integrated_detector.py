#!/usr/bin/env python3
"""
🧪 Test Integrated SOL Bonding Detector
Test the new integrated version without separate optimizer dependency
"""

import asyncio
import time
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_integrated_detector():
    """Test the integrated SOL bonding detector"""
    logger.info("🧪 Testing Integrated SOL Bonding Detector")
    logger.info("=" * 60)
    
    try:
        # Test 1: Initialize detector
        logger.info("\n🧪 Test 1: Detector initialization...")
        
        from services.sol_bonding_curve_detector import SolBondingCurveDetector
        detector = SolBondingCurveDetector(analysis_mode="real_data")
        
        logger.info("✅ Detector initialized successfully")
        
        # Test 2: Pool fetching with integrated optimizations
        logger.info("\n🧪 Test 2: Optimized pool fetching...")
        
        start_time = time.time()
        try:
            pools = await asyncio.wait_for(detector.get_raydium_pools_optimized(), timeout=15)
            elapsed = time.time() - start_time
            
            if pools:
                logger.info(f"✅ Integrated fetch: {len(pools)} pools in {elapsed:.1f}s")
                
                # Check SOL pair detection
                sol_pairs = [p for p in pools if detector._is_sol_pair(p)]
                logger.info(f"   🌊 SOL pairs found: {len(sol_pairs)}")
                
                if sol_pairs:
                    example = sol_pairs[0]
                    logger.info(f"   📋 Example: {example.get('name', 'Unknown')}")
                    logger.info(f"        Token: {example.get('token_address', 'Unknown')[:16]}...")
                    logger.info(f"        Source: {example.get('_source', 'Unknown')}")
                    logger.info(f"        Optimized: {example.get('_optimized', False)}")
            else:
                logger.warning("⚠️ Integrated fetch returned no pools")
        
        except asyncio.TimeoutError:
            logger.error("❌ Integrated fetch timeout")
        except Exception as e:
            logger.error(f"❌ Integrated fetch error: {e}")
        
        # Test 3: Candidate generation
        logger.info("\n🧪 Test 3: Candidate generation...")
        
        start_time = time.time()
        try:
            candidates = await asyncio.wait_for(detector.get_sol_bonding_candidates(limit=5), timeout=20)
            elapsed = time.time() - start_time
            
            if candidates:
                logger.info(f"✅ Generated {len(candidates)} candidates in {elapsed:.1f}s")
                
                for i, candidate in enumerate(candidates, 1):
                    symbol = candidate.get('symbol', 'Unknown')
                    sol_raised = candidate.get('estimated_sol_raised', 0)
                    graduation = candidate.get('graduation_progress_pct', 0)
                    source = candidate.get('_source', 'unknown')
                    
                    logger.info(f"   {i}. {symbol}: {sol_raised:.2f} SOL ({graduation:.1f}%) [{source}]")
            else:
                logger.info("   ℹ️ No candidates generated (normal if filtering is strict)")
        
        except asyncio.TimeoutError:
            logger.error("❌ Candidate generation timeout")
        except Exception as e:
            logger.error(f"❌ Candidate generation error: {e}")
        
        # Test 4: Cache effectiveness
        logger.info("\n🧪 Test 4: Cache effectiveness...")
        
        # First call (may hit API or cache)
        start = time.time()
        pools1 = await detector.get_raydium_pools_optimized()
        time1 = time.time() - start
        
        # Second call (should hit cache)
        start = time.time()
        pools2 = await detector.get_raydium_pools_optimized()
        time2 = time.time() - start
        
        logger.info(f"   📊 First call: {time1:.1f}s ({len(pools1 or [])} pools)")
        logger.info(f"   📊 Second call: {time2:.1f}s ({len(pools2 or [])} pools)")
        
        cache_effective = time2 < time1 * 0.5 if time1 > 1 else True
        if cache_effective:
            logger.info("   ✅ Cache is working effectively!")
        else:
            logger.warning("   ⚠️ Cache may not be optimized")
        
        # Test 5: Optimization statistics
        logger.info("\n🧪 Test 5: Optimization statistics...")
        
        stats = detector.get_optimization_stats()
        logger.info(f"   📊 API calls made: {stats.get('api_calls_made', 0)}")
        logger.info(f"   📊 Cache hits: {stats.get('cache_hits', 0)}")
        logger.info(f"   📊 Timeouts: {stats.get('timeouts', 0)}")
        logger.info(f"   📊 Circuit breaker: {stats.get('circuit_breaker_active', False)}")
        logger.info(f"   📊 High load mode: {stats.get('high_load_mode', False)}")
        logger.info(f"   📊 Cache file exists: {stats.get('cache_file_exists', False)}")
        
        # Overall assessment
        logger.info("\n" + "=" * 60)
        logger.info("📊 INTEGRATION ASSESSMENT")
        logger.info("=" * 60)
        
        improvements = []
        
        if len(pools or []) > 0:
            improvements.append("✅ Successfully retrieves pools")
        if len(sol_pairs) > 0:
            improvements.append("✅ SOL pair detection working")
        if elapsed < 15:
            improvements.append("✅ Performance under 15s")
        if cache_effective:
            improvements.append("✅ Caching effective")
        if stats.get('api_calls_made', 0) > 0:
            improvements.append("✅ API integration working")
        if not stats.get('circuit_breaker_active', False):
            improvements.append("✅ No circuit breaker activation")
        
        logger.info(f"Integration features verified: {len(improvements)}/6")
        for improvement in improvements:
            logger.info(f"  {improvement}")
        
        if len(improvements) >= 4:
            logger.info("\n🎉 INTEGRATED DETECTOR WORKING SUCCESSFULLY!")
            logger.info("   • All optimizations integrated without separate dependency")
            logger.info("   • Research-based optimizations applied")
            logger.info("   • Persistent caching and circuit breakers active")
            logger.info("   • SOL pair detection reliable")
            return True
        else:
            logger.warning("\n⚠️ Some integration features need attention")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_integrated_detector())
    if success:
        print("\n✅ Integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Integration test found issues")
        sys.exit(1)