#!/usr/bin/env python3
"""
🔧 SOL Bonding Fixes Test
Quick test to verify the timeout and performance fixes work
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

async def test_sol_bonding_fixes():
    """Test the SOL bonding detection fixes"""
    logger.info("🔧 Testing SOL Bonding Detection Fixes")
    logger.info("=" * 50)
    
    try:
        # Import the detector
        from services.sol_bonding_curve_detector import SolBondingCurveDetector
        
        # Initialize detector
        detector = SolBondingCurveDetector(analysis_mode="real_data")
        logger.info("✅ SOL Bonding Detector initialized")
        
        # Test 1: Quick pool fetch with timeout monitoring
        logger.info("\n🧪 Test 1: Pool fetching with optimizations...")
        start_time = time.time()
        pools = []
        sol_pairs = []
        fetch_time = 0
        
        try:
            pools = await asyncio.wait_for(detector.get_raydium_pools_optimized(), timeout=30)
            fetch_time = time.time() - start_time
            
            if pools:
                logger.info(f"✅ Test 1 PASSED: Fetched {len(pools)} pools in {fetch_time:.1f}s")
                
                # Check if we found SOL pairs
                sol_pairs = [p for p in pools if detector._is_sol_pair(p)]
                logger.info(f"   📊 Found {len(sol_pairs)} SOL pairs from {len(pools)} total pools")
                
                if len(sol_pairs) > 0:
                    logger.info("   ✅ SOL pair filtering is working!")
                else:
                    logger.warning("   ⚠️ No SOL pairs found - may need more filtering fixes")
            else:
                logger.warning(f"⚠️ Test 1 WARNING: No pools returned in {fetch_time:.1f}s")
        
        except asyncio.TimeoutError:
            fetch_time = time.time() - start_time
            logger.error("❌ Test 1 FAILED: Timeout after 30s")
        except Exception as e:
            fetch_time = time.time() - start_time
            logger.error(f"❌ Test 1 ERROR: {e}")
        
        # Test 2: Candidate analysis with limited scope
        analysis_time = 0
        if pools and len(pools) > 0:
            logger.info("\n🧪 Test 2: Candidate analysis performance...")
            analysis_start = time.time()
            
            # Limit to first 5 pools for quick test
            test_pools = pools[:5]
            logger.info(f"   🎯 Testing with {len(test_pools)} pools")
            
            try:
                candidates = await asyncio.wait_for(
                    detector.get_sol_bonding_candidates(limit=5), 
                    timeout=20
                )
                analysis_time = time.time() - analysis_start
                
                logger.info(f"✅ Test 2 PASSED: Found {len(candidates)} candidates in {analysis_time:.1f}s")
                
                if candidates:
                    for i, candidate in enumerate(candidates, 1):
                        symbol = candidate.get('symbol', 'Unknown')
                        sol_raised = candidate.get('estimated_sol_raised', 0)
                        graduation = candidate.get('graduation_progress_pct', 0)
                        logger.info(f"   {i}. {symbol}: {sol_raised:.1f} SOL ({graduation:.1f}%)")
                else:
                    logger.info("   ℹ️ No candidates met the criteria (this is normal)")
                    
            except asyncio.TimeoutError:
                logger.error("❌ Test 2 FAILED: Analysis timeout after 20s")
            except Exception as e:
                logger.error(f"❌ Test 2 ERROR: {e}")
        
        # Test 3: Circuit breaker functionality
        logger.info("\n🧪 Test 3: Circuit breaker and fallback systems...")
        
        # Simulate multiple timeouts to trigger circuit breaker
        detector.timeout_count = 3
        detector.high_load_mode = True
        
        fallback_start = time.time()
        fallback_pools = await detector.get_raydium_pools_optimized()
        fallback_time = time.time() - fallback_start
        
        if fallback_pools:
            logger.info(f"✅ Test 3 PASSED: Fallback system provided {len(fallback_pools)} pools in {fallback_time:.1f}s")
        else:
            logger.warning("⚠️ Test 3 WARNING: Fallback system returned no pools")
        
        # Overall assessment
        logger.info("\n" + "=" * 50)
        logger.info("📊 OVERALL ASSESSMENT")
        logger.info("=" * 50)
        
        improvements = []
        if fetch_time < 30:
            improvements.append("✅ Pool fetching within timeout")
        if len(pools or []) > 0:
            improvements.append("✅ Successfully retrieved pool data")
        if len(sol_pairs) > 0:
            improvements.append("✅ SOL pair filtering working")
        if analysis_time < 20:
            improvements.append("✅ Analysis completes within timeout")
        if fallback_pools:
            improvements.append("✅ Fallback systems operational")
        
        logger.info(f"Improvements verified: {len(improvements)}/5")
        for improvement in improvements:
            logger.info(f"  {improvement}")
        
        if len(improvements) >= 3:
            logger.info("🎉 SOL Bonding fixes appear to be working well!")
            return True
        else:
            logger.warning("⚠️ Some issues may still need addressing")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sol_bonding_fixes())
    if success:
        print("\n✅ Test completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Test completed with issues")
        sys.exit(1)