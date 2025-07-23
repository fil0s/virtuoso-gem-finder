#!/usr/bin/env python3
"""
Birdeye API Batch Size Optimization Script

Tests different batch sizes to find the optimal balance between
efficiency and reliability for the /defi/multi_price endpoint.
"""

import asyncio
import time
import statistics
from pathlib import Path
import sys

# Add project root to path
sys.path.append('.')

from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager

class BatchSizeOptimizer:
    def __init__(self):
        import logging
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        
        self.config = ConfigManager()
        self.logger = logging.getLogger(__name__)
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService()
        
        # Get Birdeye config section
        birdeye_config = self.config.get_section('BIRDEYE_API')
        
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
        self.test_results = {}
        
        # Test token addresses (using real Solana token addresses)
        self.test_tokens = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
            "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",  # POPCAT
            "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",   # JUP
            "5z3EQy7CKLKyeKCLJTM1LwHuGfKKrfAhU8RmPXvHpump",   # Test token
            "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk",   # Test token
            "J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr",   # Test token
            "JB2wezZLdzWfnaCfHxLg193RS3Rh51ThiXxEDWQDpump",   # Test token
            "9hjZ8UTNrNWt3YUTHVpvzdQjNbp64NbKSDsbLqKR6BZc",   # Test token
            "HaP8r3ksG76PhQLTqR8FYBeNiQpejcFbQmiHbg787Ut1",   # Test token
            "3B5wuUrMEi5yATD7on46hKfej3pfmd7t1RKgrsN3pump",   # Test token
            "D3MpL13nkZyjojPWQzVGDf8h3DFnVwWGWP4chqqDpump",   # Test token
            "72Sp7QibTt8vWoHzvJQ6QA1Pp6UuNjCtRDBdioVSpump",   # Test token
        ]
    
    async def test_batch_size(self, batch_size: int, num_tests: int = 3) -> dict:
        """Test a specific batch size multiple times"""
        print(f"\n🧪 Testing batch size: {batch_size} tokens")
        
        results = {
            'batch_size': batch_size,
            'response_times': [],
            'success_count': 0,
            'total_tests': num_tests,
            'errors': []
        }
        
        for test_num in range(num_tests):
            # Create batch from test tokens
            if batch_size <= len(self.test_tokens):
                test_batch = self.test_tokens[:batch_size]
            else:
                # Repeat tokens if we need more than available
                test_batch = (self.test_tokens * ((batch_size // len(self.test_tokens)) + 1))[:batch_size]
            
            try:
                start_time = time.time()
                response = await self.birdeye_api.get_multi_price(test_batch)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                if response and isinstance(response, dict):
                    results['response_times'].append(response_time)
                    results['success_count'] += 1
                    print(f"  ✅ Test {test_num + 1}: {response_time:.0f}ms - {len(response)} tokens returned")
                else:
                    results['errors'].append(f"Test {test_num + 1}: No data returned")
                    print(f"  ❌ Test {test_num + 1}: No data returned")
                
                # Add delay between tests to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                results['errors'].append(f"Test {test_num + 1}: {str(e)}")
                print(f"  ❌ Test {test_num + 1}: Error - {e}")
                await asyncio.sleep(2)  # Longer delay after error
        
        # Calculate statistics
        if results['response_times']:
            results['avg_response_time'] = statistics.mean(results['response_times'])
            results['min_response_time'] = min(results['response_times'])
            results['max_response_time'] = max(results['response_times'])
            results['success_rate'] = (results['success_count'] / results['total_tests']) * 100
        else:
            results['avg_response_time'] = 0
            results['min_response_time'] = 0
            results['max_response_time'] = 0
            results['success_rate'] = 0
        
        return results
    
    async def run_optimization_test(self):
        """Run comprehensive batch size optimization"""
        print("🚀 BIRDEYE API BATCH SIZE OPTIMIZATION")
        print("=" * 60)
        print(f"Testing endpoint: /defi/multi_price")
        print(f"API limit: 100 tokens per request")
        print(f"Current setting: 15 tokens")
        print("=" * 60)
        
        # Test different batch sizes
        batch_sizes_to_test = [15, 20, 25, 30, 35, 40, 50, 60, 75, 100]
        
        for batch_size in batch_sizes_to_test:
            try:
                result = await self.test_batch_size(batch_size)
                self.test_results[batch_size] = result
                
                # Print summary
                if result['success_rate'] > 0:
                    print(f"  📊 Success Rate: {result['success_rate']:.1f}%")
                    print(f"  ⏱️  Avg Response: {result['avg_response_time']:.0f}ms")
                    print(f"  📈 Range: {result['min_response_time']:.0f}-{result['max_response_time']:.0f}ms")
                else:
                    print(f"  ❌ All tests failed")
                
                # Stop testing if success rate drops below 80%
                if result['success_rate'] < 80:
                    print(f"  ⚠️ Success rate too low ({result['success_rate']:.1f}%), stopping tests")
                    break
                    
            except Exception as e:
                print(f"  ❌ Failed to test batch size {batch_size}: {e}")
                break
        
        # Analyze results and provide recommendations
        self.analyze_results()
    
    def analyze_results(self):
        """Analyze test results and provide optimization recommendations"""
        print("\n" + "=" * 60)
        print("📊 OPTIMIZATION ANALYSIS")
        print("=" * 60)
        
        if not self.test_results:
            print("❌ No test results to analyze")
            return
        
        # Find optimal batch size
        successful_tests = {k: v for k, v in self.test_results.items() if v['success_rate'] >= 95}
        
        if successful_tests:
            # Find the largest batch size with 95%+ success rate
            optimal_batch_size = max(successful_tests.keys())
            optimal_result = successful_tests[optimal_batch_size]
            
            print(f"\n🎯 RECOMMENDED OPTIMAL BATCH SIZE: {optimal_batch_size} tokens")
            print(f"   Success Rate: {optimal_result['success_rate']:.1f}%")
            print(f"   Avg Response Time: {optimal_result['avg_response_time']:.0f}ms")
            print(f"   Efficiency Gain: {(optimal_batch_size / 15 - 1) * 100:.1f}% vs current 15 tokens")
            
            # Calculate efficiency metrics
            current_efficiency = 15  # tokens per request
            optimal_efficiency = optimal_batch_size
            improvement = (optimal_efficiency / current_efficiency - 1) * 100
            
            print(f"\n💡 EFFICIENCY IMPROVEMENTS:")
            print(f"   Current: 15 tokens/request")
            print(f"   Optimal: {optimal_batch_size} tokens/request")
            print(f"   Improvement: {improvement:.1f}% more efficient")
            print(f"   API calls reduced by: {(1 - current_efficiency/optimal_efficiency) * 100:.1f}%")
            
        else:
            print("⚠️ No batch sizes achieved 95%+ success rate")
            # Find best performing size
            best_size = max(self.test_results.keys(), 
                          key=lambda k: self.test_results[k]['success_rate'])
            best_result = self.test_results[best_size]
            print(f"Best performing: {best_size} tokens ({best_result['success_rate']:.1f}% success)")
        
        # Print detailed results table
        print(f"\n📋 DETAILED RESULTS:")
        print(f"{'Batch Size':<12} {'Success Rate':<13} {'Avg Time':<10} {'Min Time':<10} {'Max Time':<10} {'Status'}")
        print("-" * 70)
        
        for batch_size, result in sorted(self.test_results.items()):
            status = "✅ Excellent" if result['success_rate'] >= 95 else \
                    "🟡 Good" if result['success_rate'] >= 90 else \
                    "🟠 Fair" if result['success_rate'] >= 80 else "❌ Poor"
            
            print(f"{batch_size:<12} {result['success_rate']:.1f}%{'':<8} "
                  f"{result['avg_response_time']:.0f}ms{'':<6} "
                  f"{result['min_response_time']:.0f}ms{'':<6} "
                  f"{result['max_response_time']:.0f}ms{'':<6} "
                  f"{status}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if hasattr(self.birdeye_api, 'close'):
            await self.birdeye_api.close()

async def main():
    optimizer = BatchSizeOptimizer()
    try:
        await optimizer.run_optimization_test()
    finally:
        await optimizer.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 