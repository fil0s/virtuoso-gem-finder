#!/usr/bin/env python3
"""
🔍 SOL Bonding Performance Investigation
Test script to isolate and profile the SOL bonding detection bottleneck
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SOLBondingPerformanceTester:
    def __init__(self):
        self.endpoints = {
            'jupiter_quote': 'https://quote-api.jup.ag/v6/quote',
            'raydium_pools': 'https://api.raydium.io/pools',
            'raydium_pairs': 'https://api.raydium.io/v2/main/pairs',
            'raydium_pools_full': 'https://api.raydium.io/v2/sdk/liquidity/mainnet.json',
        }
        self.SOL_MINT = 'So11111111111111111111111111111111111111112'

    async def test_endpoint_performance(self, url: str, timeout: int = 30, name: str = "Endpoint") -> Dict:
        """Test individual endpoint performance"""
        logger.info(f"🔍 Testing {name}...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(url) as response:
                    request_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        total_time = time.time() - start_time
                        
                        # Calculate size information
                        data_size = len(str(data)) if data else 0
                        record_count = len(data) if isinstance(data, list) else 1
                        
                        result = {
                            'name': name,
                            'url': url,
                            'status': 'success',
                            'request_time_ms': request_time * 1000,
                            'total_time_ms': total_time * 1000,
                            'status_code': response.status,
                            'data_size_bytes': data_size,
                            'record_count': record_count
                        }
                        
                        logger.info(f"✅ {name}: {total_time:.2f}s, {record_count} records, {data_size:,} bytes")
                        return result
                    else:
                        result = {
                            'name': name,
                            'url': url,
                            'status': 'failed',
                            'request_time_ms': (time.time() - start_time) * 1000,
                            'status_code': response.status,
                            'error': f'HTTP {response.status}'
                        }
                        logger.warning(f"❌ {name}: HTTP {response.status}")
                        return result
                        
        except asyncio.TimeoutError:
            result = {
                'name': name,
                'url': url,
                'status': 'timeout',
                'timeout_seconds': timeout,
                'error': f'Timeout after {timeout}s'
            }
            logger.error(f"⏰ {name}: Timeout after {timeout}s")
            return result
        except Exception as e:
            result = {
                'name': name,
                'url': url,
                'status': 'error',
                'request_time_ms': (time.time() - start_time) * 1000,
                'error': str(e)
            }
            logger.error(f"❌ {name}: {e}")
            return result

    def filter_sol_pairs(self, data: List[Dict]) -> List[Dict]:
        """Filter for SOL pairs from pool data"""
        sol_pairs = []
        
        for item in data:
            # Check different possible structures
            base_mint = item.get('baseMint') or item.get('base_mint') or item.get('token0', {}).get('address', '')
            quote_mint = item.get('quoteMint') or item.get('quote_mint') or item.get('token1', {}).get('address', '')
            
            if base_mint == self.SOL_MINT or quote_mint == self.SOL_MINT:
                sol_pairs.append(item)
                
        return sol_pairs

    async def test_data_processing_performance(self, data: List[Dict], name: str) -> Dict:
        """Test the performance of processing retrieved data"""
        logger.info(f"🔄 Processing {name} data...")
        start_time = time.time()
        
        try:
            # Filter for SOL pairs
            sol_pairs = self.filter_sol_pairs(data)
            processing_time = time.time() - start_time
            
            result = {
                'name': f"{name} Processing",
                'status': 'success',
                'processing_time_ms': processing_time * 1000,
                'total_records': len(data),
                'sol_pairs_found': len(sol_pairs),
                'filter_rate_percent': (len(sol_pairs) / len(data)) * 100 if data else 0
            }
            
            logger.info(f"✅ {name} Processing: {processing_time:.2f}s, {len(sol_pairs)}/{len(data)} SOL pairs")
            return result
            
        except Exception as e:
            result = {
                'name': f"{name} Processing",
                'status': 'error',
                'processing_time_ms': (time.time() - start_time) * 1000,
                'error': str(e)
            }
            logger.error(f"❌ {name} Processing: {e}")
            return result

    async def run_comprehensive_test(self):
        """Run comprehensive performance test"""
        logger.info("🚀 Starting SOL Bonding Performance Investigation")
        logger.info("=" * 60)
        
        results = []
        
        # Test 1: Jupiter Quote API (for SOL price)
        jupiter_url = f"{self.endpoints['jupiter_quote']}?inputMint={self.SOL_MINT}&outputMint=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v&amount=1000000&slippageBps=50"
        jupiter_result = await self.test_endpoint_performance(jupiter_url, 10, "Jupiter SOL Price")
        results.append(jupiter_result)
        
        # Test 2: Raydium Pools API (primary)
        pools_result = await self.test_endpoint_performance(self.endpoints['raydium_pools'], 30, "Raydium Pools")
        results.append(pools_result)
        
        if pools_result['status'] == 'success':
            # Get the actual data to test processing
            async with aiohttp.ClientSession() as session:
                async with session.get(self.endpoints['raydium_pools']) as response:
                    if response.status == 200:
                        pools_data = await response.json()
                        if pools_data:
                            processing_result = await self.test_data_processing_performance(pools_data, "Raydium Pools")
                            results.append(processing_result)
        
        # Test 3: Raydium Pairs API (secondary)
        pairs_result = await self.test_endpoint_performance(self.endpoints['raydium_pairs'], 30, "Raydium Pairs")
        results.append(pairs_result)
        
        if pairs_result['status'] == 'success':
            # Get the actual data to test processing
            async with aiohttp.ClientSession() as session:
                async with session.get(self.endpoints['raydium_pairs']) as response:
                    if response.status == 200:
                        pairs_data = await response.json()
                        if pairs_data:
                            processing_result = await self.test_data_processing_performance(pairs_data, "Raydium Pairs")
                            results.append(processing_result)
        
        # Test 4: Full Liquidity JSON (fallback - most likely to be slow)
        full_result = await self.test_endpoint_performance(self.endpoints['raydium_pools_full'], 45, "Raydium Full Liquidity")
        results.append(full_result)
        
        # Test 5: Concurrent requests simulation
        logger.info("🔄 Testing concurrent request performance...")
        concurrent_start = time.time()
        
        concurrent_tasks = [
            self.test_endpoint_performance(jupiter_url, 10, f"Jupiter Concurrent {i+1}")
            for i in range(5)
        ]
        
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        concurrent_time = time.time() - concurrent_start
        
        concurrent_result = {
            'name': 'Concurrent Requests Test',
            'status': 'completed',
            'total_time_ms': concurrent_time * 1000,
            'concurrent_requests': 5,
            'successful_requests': sum(1 for r in concurrent_results if isinstance(r, dict) and r.get('status') == 'success'),
            'average_time_ms': concurrent_time * 1000 / 5
        }
        results.append(concurrent_result)
        
        logger.info(f"✅ Concurrent Test: {concurrent_time:.2f}s for 5 requests")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 PERFORMANCE ANALYSIS SUMMARY")
        logger.info("=" * 60)
        
        for result in results:
            status_icon = "✅" if result['status'] == 'success' else "❌" if result['status'] == 'error' else "⏰"
            name = result['name']
            
            if 'total_time_ms' in result:
                time_info = f"{result['total_time_ms']:.0f}ms"
            elif 'request_time_ms' in result:
                time_info = f"{result['request_time_ms']:.0f}ms"
            elif 'processing_time_ms' in result:
                time_info = f"{result['processing_time_ms']:.0f}ms"
            else:
                time_info = "N/A"
            
            extra_info = ""
            if 'record_count' in result:
                extra_info = f" ({result['record_count']} records)"
            elif 'sol_pairs_found' in result:
                extra_info = f" ({result['sol_pairs_found']} SOL pairs)"
            elif 'concurrent_requests' in result:
                extra_info = f" ({result['successful_requests']}/{result['concurrent_requests']} success)"
            
            logger.info(f"{status_icon} {name}: {time_info}{extra_info}")
            
            if 'error' in result:
                logger.info(f"   Error: {result['error']}")
        
        # Identify bottlenecks
        logger.info("\n🔍 BOTTLENECK ANALYSIS:")
        
        slow_endpoints = [r for r in results if r.get('total_time_ms', 0) > 10000 or r.get('request_time_ms', 0) > 10000]
        if slow_endpoints:
            logger.info("⚠️ Slow endpoints (>10s):")
            for endpoint in slow_endpoints:
                time_ms = endpoint.get('total_time_ms') or endpoint.get('request_time_ms', 0)
                logger.info(f"   • {endpoint['name']}: {time_ms:.0f}ms")
        
        timeout_endpoints = [r for r in results if r['status'] == 'timeout']
        if timeout_endpoints:
            logger.info("⏰ Timeout endpoints:")
            for endpoint in timeout_endpoints:
                logger.info(f"   • {endpoint['name']}: {endpoint.get('timeout_seconds', 'N/A')}s timeout")
        
        failed_endpoints = [r for r in results if r['status'] == 'error']
        if failed_endpoints:
            logger.info("❌ Failed endpoints:")
            for endpoint in failed_endpoints:
                logger.info(f"   • {endpoint['name']}: {endpoint.get('error', 'Unknown error')}")
        
        return results

async def main():
    """Main test function"""
    tester = SOLBondingPerformanceTester()
    results = await tester.run_comprehensive_test()
    
    # Save results for further analysis
    import json
    with open('sol_bonding_performance_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n💾 Results saved to sol_bonding_performance_results.json")

if __name__ == "__main__":
    asyncio.run(main())