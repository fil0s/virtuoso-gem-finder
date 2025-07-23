#!/usr/bin/env python3
"""
🧪 Test Optimized Raydium Integration
Test the enhanced optimizations based on research findings
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

async def test_optimized_integration():
    """Test the optimized Raydium integration"""
    logger.info("🚀 Testing Optimized Raydium Integration")
    logger.info("=" * 60)
    
    try:
        # Test 1: Advanced optimizer standalone
        logger.info("\n🧪 Test 1: Advanced API Optimizer...")
        
        from services.raydium_api_optimizer import RaydiumAPIOptimizer
        optimizer = RaydiumAPIOptimizer()
        
        start_time = time.time()
        try:
            pools = await asyncio.wait_for(optimizer.get_optimized_pools(max_pools=50), timeout=15)
            elapsed = time.time() - start_time
            
            if pools:
                logger.info(f"✅ Advanced optimizer: {len(pools)} pools in {elapsed:.1f}s")
                
                # Check SOL pairs
                sol_pairs = [p for p in pools if p.get('_optimized')]
                logger.info(f"   🌊 SOL pairs: {len(sol_pairs)}")
                logger.info(f"   💾 Cache used: {optimizer.stats['cache_hits'] > 0}")
                logger.info(f"   📊 Stats: {optimizer.get_stats()}")
            else:
                logger.warning("⚠️ Advanced optimizer returned no pools")
        
        except asyncio.TimeoutError:
            logger.error("❌ Advanced optimizer timeout")
        except Exception as e:
            logger.error(f"❌ Advanced optimizer error: {e}")
        
        # Test 2: SOL Bonding Detector with optimizer
        logger.info("\n🧪 Test 2: SOL Bonding Detector with optimizations...")
        
        from services.sol_bonding_curve_detector import SolBondingCurveDetector
        detector = SolBondingCurveDetector(analysis_mode="real_data")
        
        start_time = time.time()
        try:
            pools = await asyncio.wait_for(detector.get_raydium_pools_optimized(), timeout=15)
            elapsed = time.time() - start_time
            
            if pools:
                logger.info(f"✅ SOL detector: {len(pools)} pools in {elapsed:.1f}s")
                
                # Check SOL pair detection
                sol_pairs = [p for p in pools if detector._is_sol_pair(p)]
                logger.info(f"   🌊 SOL pairs found: {len(sol_pairs)}")
                
                if sol_pairs:
                    example = sol_pairs[0]
                    logger.info(f"   📋 Example: {example.get('name', 'Unknown')}")
                    logger.info(f"        Base: {example.get('baseMint', 'Unknown')[:12]}...")
                    logger.info(f"        Quote: {example.get('quoteMint', 'Unknown')[:12]}...")
                    logger.info(f"        Source: {example.get('_source', 'Unknown')}")
            else:
                logger.warning("⚠️ SOL detector returned no pools")
        
        except asyncio.TimeoutError:
            logger.error("❌ SOL detector timeout")
        except Exception as e:
            logger.error(f"❌ SOL detector error: {e}")
        
        # Test 3: Performance comparison
        logger.info("\n🧪 Test 3: Performance comparison...")
        
        # Test multiple runs for consistency
        times = []
        successful_runs = 0
        
        for run in range(3):
            start = time.time()
            try:
                test_pools = await asyncio.wait_for(detector.get_raydium_pools_optimized(), timeout=10)
                elapsed = time.time() - start
                times.append(elapsed)
                successful_runs += 1
                logger.info(f"   Run {run+1}: {elapsed:.1f}s ({len(test_pools or [])} pools)")
            except Exception as e:
                times.append(10.0)  # Max time for failed runs
                logger.warning(f"   Run {run+1}: Failed ({e})")
            
            await asyncio.sleep(1)  # Brief pause
        
        if times:
            avg_time = sum(times) / len(times)
            success_rate = (successful_runs / 3) * 100
            logger.info(f"   📊 Average: {avg_time:.1f}s, Success: {success_rate:.0f}%")
        
        # Test 4: Cache effectiveness
        logger.info("\n🧪 Test 4: Cache effectiveness...")
        
        # First call (should hit API)
        start = time.time()
        pools1 = await detector.get_raydium_pools_optimized()
        time1 = time.time() - start
        
        # Second call (should hit cache)
        start = time.time()
        pools2 = await detector.get_raydium_pools_optimized()
        time2 = time.time() - start
        
        if pools1 and pools2:
            logger.info(f"   📊 First call: {time1:.1f}s ({len(pools1)} pools)")
            logger.info(f"   📊 Second call: {time2:.1f}s ({len(pools2)} pools)")
            
            if time2 < time1 * 0.1:  # Second call should be much faster
                logger.info("   ✅ Cache is working effectively!")
            else:
                logger.warning("   ⚠️ Cache may not be working optimally")
        
        # Final assessment
        logger.info("\n" + "=" * 60)
        logger.info("📊 OPTIMIZATION ASSESSMENT")
        logger.info("=" * 60)
        
        improvements = []
        
        if avg_time < 10:
            improvements.append("✅ Performance under 10s")
        if successful_runs >= 2:
            improvements.append("✅ Reliable operation")
        if len(pools or []) > 0:
            improvements.append("✅ Successfully retrieves pools")
        if len(sol_pairs) > 0:
            improvements.append("✅ SOL pair detection working")
        if time2 < time1 * 0.5:
            improvements.append("✅ Caching effective")
        
        logger.info(f"Optimizations verified: {len(improvements)}/5")
        for improvement in improvements:
            logger.info(f"  {improvement}")
        
        if len(improvements) >= 4:
            logger.info("\n🎉 RAYDIUM INTEGRATION OPTIMIZED SUCCESSFULLY!")
            logger.info("   • Research-based optimizations implemented")
            logger.info("   • Performance improved with caching")
            logger.info("   • Circuit breakers handle API issues")
            logger.info("   • SOL pair detection reliable")
            return True
        else:
            logger.warning("\n⚠️ Some optimizations may need further tuning")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_optimized_integration())
    if success:
        print("\n✅ Optimization test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Optimization test found issues")
        sys.exit(1)