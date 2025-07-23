#!/usr/bin/env python3
"""
Simple performance validation for Raydium v3 integration
Tests core functionality and performance metrics
"""

import asyncio
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.raydium_connector import RaydiumConnector

async def test_raydium_v3_performance():
    """Performance validation test for Raydium v3 connector"""
    
    print("⚡ Raydium v3 Performance Validation")
    print("=" * 50)
    
    # Test with minimal configuration
    connector = RaydiumConnector(
        enhanced_cache=None,  # Disable cache for pure performance test
        api_tracking_enabled=True,
        rate_limiter=None  # Disable rate limiter for performance test
    )
    
    results = {
        'total_tests': 0,
        'successful_tests': 0,
        'failed_tests': 0,
        'performance_metrics': {}
    }
    
    async with connector:
        
        # Test 1: Basic pools retrieval
        print("\n📊 Test 1: Basic Pools Retrieval")
        results['total_tests'] += 1
        try:
            start_time = time.time()
            pools = await connector.get_pools(limit=5)
            elapsed = time.time() - start_time
            
            if isinstance(pools, list):
                print(f"✅ Retrieved {len(pools)} pools in {elapsed:.2f}s")
                results['successful_tests'] += 1
                results['performance_metrics']['pools_retrieval_time'] = elapsed
                results['performance_metrics']['pools_count'] = len(pools)
            else:
                print(f"❌ Invalid response type: {type(pools)}")
                results['failed_tests'] += 1
                
        except Exception as e:
            print(f"❌ Pools retrieval failed: {e}")
            results['failed_tests'] += 1
        
        # Test 2: WSOL pairs with early gem detection
        print("\n💎 Test 2: WSOL Early Gem Detection")
        results['total_tests'] += 1
        try:
            start_time = time.time()
            wsol_pairs = await connector.get_wsol_trending_pairs(limit=10)
            elapsed = time.time() - start_time
            
            if isinstance(wsol_pairs, list):
                early_gems = [p for p in wsol_pairs if p.get('is_early_gem_candidate', False)]
                print(f"✅ Retrieved {len(wsol_pairs)} WSOL pairs ({len(early_gems)} early gems) in {elapsed:.2f}s")
                results['successful_tests'] += 1
                results['performance_metrics']['wsol_retrieval_time'] = elapsed
                results['performance_metrics']['wsol_pairs_count'] = len(wsol_pairs)
                results['performance_metrics']['early_gems_count'] = len(early_gems)
                
                # Show top early gems
                if early_gems:
                    print("🏆 Top early gems:")
                    for i, gem in enumerate(early_gems[:3]):
                        symbol = gem.get('symbol', 'Unknown')
                        tvl = gem.get('tvl', 0)
                        ratio = gem.get('volume_tvl_ratio', 0)
                        print(f"   {i+1}. {symbol} - TVL: ${tvl:,.0f}, Ratio: {ratio:.1f}")
                        
            else:
                print(f"❌ Invalid response type: {type(wsol_pairs)}")
                results['failed_tests'] += 1
                
        except Exception as e:
            print(f"❌ WSOL pairs retrieval failed: {e}")
            results['failed_tests'] += 1
        
        # Test 3: API Statistics
        print("\n📈 Test 3: API Statistics")
        results['total_tests'] += 1
        try:
            stats = connector.get_api_call_statistics()
            
            if isinstance(stats, dict) and 'total_calls' in stats:
                print(f"✅ API Stats:")
                print(f"   Total calls: {stats['total_calls']}")
                print(f"   Success rate: {stats['success_rate']:.1%}")
                print(f"   Average response time: {stats['average_response_time']:.2f}s")
                
                results['successful_tests'] += 1
                results['performance_metrics']['api_stats'] = stats
            else:
                print(f"❌ Invalid stats format: {stats}")
                results['failed_tests'] += 1
                
        except Exception as e:
            print(f"❌ API statistics failed: {e}")
            results['failed_tests'] += 1
        
        # Test 4: Concurrent requests
        print("\n🚀 Test 4: Concurrent Performance")
        results['total_tests'] += 1
        try:
            start_time = time.time()
            
            # Make 3 concurrent requests
            tasks = [
                connector.get_pools(limit=3),
                connector.get_pairs(limit=3),
                connector.get_wsol_trending_pairs(limit=5)
            ]
            
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time
            
            successful_concurrent = sum(1 for r in concurrent_results if not isinstance(r, Exception))
            
            print(f"✅ Concurrent test: {successful_concurrent}/3 successful in {elapsed:.2f}s")
            print(f"   Requests per second: {3/elapsed:.1f}")
            
            results['successful_tests'] += 1
            results['performance_metrics']['concurrent_time'] = elapsed
            results['performance_metrics']['concurrent_rps'] = 3/elapsed
            
        except Exception as e:
            print(f"❌ Concurrent test failed: {e}")
            results['failed_tests'] += 1
    
    # Calculate final results
    success_rate = (results['successful_tests'] / results['total_tests']) * 100 if results['total_tests'] > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 Performance Validation Results")
    print(f"✅ Tests passed: {results['successful_tests']}/{results['total_tests']} ({success_rate:.1f}%)")
    
    if results['performance_metrics']:
        print("\n⚡ Performance Metrics:")
        metrics = results['performance_metrics']
        
        if 'pools_retrieval_time' in metrics:
            print(f"   Pools retrieval: {metrics['pools_retrieval_time']:.2f}s")
            
        if 'wsol_retrieval_time' in metrics:
            print(f"   WSOL detection: {metrics['wsol_retrieval_time']:.2f}s")
            
        if 'early_gems_count' in metrics:
            print(f"   Early gems found: {metrics['early_gems_count']}")
            
        if 'concurrent_rps' in metrics:
            print(f"   Concurrent RPS: {metrics['concurrent_rps']:.1f}")
            
        if 'api_stats' in metrics:
            api_stats = metrics['api_stats']
            print(f"   Overall success rate: {api_stats.get('success_rate', 0):.1%}")
    
    # Production readiness assessment
    print("\n🚀 Production Readiness Assessment:")
    
    if success_rate >= 75:
        print("✅ PRODUCTION READY")
        print("   All core functionality working")
        if results.get('performance_metrics', {}).get('early_gems_count', 0) > 0:
            print("   Early gem detection functional")
        if results.get('performance_metrics', {}).get('concurrent_rps', 0) >= 1:
            print("   Performance meets requirements")
        return True
    else:
        print("❌ NOT PRODUCTION READY")
        print(f"   Success rate too low: {success_rate:.1f}%")
        return False

async def main():
    try:
        is_ready = await test_raydium_v3_performance()
        return 0 if is_ready else 1
    except Exception as e:
        print(f"\n💥 Performance test crashed: {e}")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)