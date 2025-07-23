#!/usr/bin/env python3
"""
🔍 Raydium API Endpoints Verification
Comprehensive test to verify all Raydium APIs are working and returning expected data
"""

import asyncio
import aiohttp
import time
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RaydiumAPITester:
    def __init__(self):
        # Current endpoints from the detector
        self.endpoints = {
            'raydium_pools': 'https://api.raydium.io/pools',
            'raydium_pairs': 'https://api.raydium.io/v2/main/pairs',
            'raydium_pairs_alt': 'https://api.raydium.io/pairs',
            'raydium_token_info': 'https://api.raydium.io/v2/sdk/token/raydium.mainnet.json',
            'raydium_farm_info': 'https://api.raydium.io/v2/sdk/farm/mainnet.json',
            'raydium_pools_full': 'https://api.raydium.io/v2/sdk/liquidity/mainnet.json',
        }
        
        # Alternative endpoints to test
        self.alternative_endpoints = {
            'raydium_api_v1': 'https://api.raydium.io/v1/main/pairs',
            'raydium_api_info': 'https://api.raydium.io/info',
            'raydium_stats': 'https://api.raydium.io/stats',
            'raydium_pools_v2': 'https://api.raydium.io/v2/pools',
        }
        
        self.SOL_MINT = 'So11111111111111111111111111111111111111112'
        self.test_results = []

    async def test_endpoint_detailed(self, name: str, url: str, timeout: int = 30) -> Dict:
        """Test endpoint with detailed analysis"""
        logger.info(f"🔍 Testing {name}...")
        logger.info(f"   URL: {url}")
        
        start_time = time.time()
        result = {
            'name': name,
            'url': url,
            'status': 'unknown',
            'test_timestamp': datetime.now().isoformat(),
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    request_time = time.time() - start_time
                    
                    result.update({
                        'status_code': response.status,
                        'request_time_seconds': round(request_time, 2),
                        'headers': dict(response.headers),
                        'content_type': response.headers.get('content-type', 'unknown')
                    })
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            total_time = time.time() - start_time
                            
                            # Analyze the data structure
                            data_analysis = self._analyze_data_structure(data)
                            
                            result.update({
                                'status': 'success',
                                'total_time_seconds': round(total_time, 2),
                                'data_size_bytes': len(str(data)),
                                'data_analysis': data_analysis
                            })
                            
                            # Test SOL pair filtering on this data
                            sol_pairs = self._find_sol_pairs(data)
                            result['sol_pairs_found'] = len(sol_pairs)
                            result['sol_pair_examples'] = sol_pairs[:3]  # First 3 examples
                            
                            logger.info(f"   ✅ SUCCESS: {response.status} in {total_time:.2f}s")
                            logger.info(f"   📊 Data: {len(str(data)):,} bytes, {data_analysis['record_count']} records")
                            logger.info(f"   🌊 SOL pairs: {len(sol_pairs)} found")
                            
                        except json.JSONDecodeError as e:
                            result.update({
                                'status': 'json_error',
                                'error': f'JSON decode error: {str(e)}',
                                'content_preview': str(await response.text())[:200]
                            })
                            logger.error(f"   ❌ JSON ERROR: {e}")
                        except Exception as e:
                            result.update({
                                'status': 'processing_error',
                                'error': f'Data processing error: {str(e)}'
                            })
                            logger.error(f"   ❌ PROCESSING ERROR: {e}")
                    else:
                        result.update({
                            'status': 'http_error',
                            'error': f'HTTP {response.status}',
                            'response_text': await response.text() if response.status != 404 else 'Not Found'
                        })
                        logger.warning(f"   ❌ HTTP {response.status}")
                        
        except asyncio.TimeoutError:
            result.update({
                'status': 'timeout',
                'error': f'Timeout after {timeout} seconds',
                'request_time_seconds': timeout
            })
            logger.error(f"   ⏰ TIMEOUT after {timeout}s")
        except Exception as e:
            result.update({
                'status': 'connection_error',
                'error': str(e),
                'request_time_seconds': round(time.time() - start_time, 2)
            })
            logger.error(f"   ❌ CONNECTION ERROR: {e}")
        
        return result

    def _analyze_data_structure(self, data: Any) -> Dict:
        """Analyze the structure of returned data"""
        analysis = {
            'data_type': type(data).__name__,
            'record_count': 0,
            'sample_keys': [],
            'nested_structure': False
        }
        
        if isinstance(data, list):
            analysis['record_count'] = len(data)
            if data:
                first_item = data[0]
                if isinstance(first_item, dict):
                    analysis['sample_keys'] = list(first_item.keys())[:10]
                    analysis['nested_structure'] = any(isinstance(v, (dict, list)) for v in first_item.values())
        elif isinstance(data, dict):
            analysis['record_count'] = 1
            analysis['sample_keys'] = list(data.keys())[:10]
            analysis['nested_structure'] = any(isinstance(v, (dict, list)) for v in data.values())
        
        return analysis

    def _find_sol_pairs(self, data: Any) -> List[Dict]:
        """Find SOL pairs in the data using various field patterns"""
        sol_pairs = []
        
        try:
            # Handle different data structures
            items_to_check = []
            if isinstance(data, list):
                items_to_check = data
            elif isinstance(data, dict):
                # Check if it's a nested structure
                for key, value in data.items():
                    if isinstance(value, list):
                        items_to_check.extend(value)
                    elif isinstance(value, dict):
                        items_to_check.append(value)
                if not items_to_check:
                    items_to_check = [data]
            
            # Check each item for SOL pairs
            for item in items_to_check[:1000]:  # Limit to first 1000 items for performance
                if not isinstance(item, dict):
                    continue
                
                # Try multiple field patterns
                base_mints = [
                    item.get('baseMint'),
                    item.get('base_mint'),
                    item.get('baseToken', {}).get('mint') if isinstance(item.get('baseToken'), dict) else None,
                    item.get('baseToken', {}).get('address') if isinstance(item.get('baseToken'), dict) else None,
                    item.get('token0', {}).get('address') if isinstance(item.get('token0'), dict) else None,
                ]
                
                quote_mints = [
                    item.get('quoteMint'),
                    item.get('quote_mint'),
                    item.get('quoteToken', {}).get('mint') if isinstance(item.get('quoteToken'), dict) else None,
                    item.get('quoteToken', {}).get('address') if isinstance(item.get('quoteToken'), dict) else None,
                    item.get('token1', {}).get('address') if isinstance(item.get('token1'), dict) else None,
                ]
                
                # Check if any combination indicates SOL pair
                all_mints = [m for m in base_mints + quote_mints if m]
                if self.SOL_MINT in all_mints:
                    sol_pairs.append({
                        'pool_id': item.get('id') or item.get('pool_id') or item.get('ammId', 'unknown'),
                        'base_mint': next((m for m in base_mints if m), 'unknown'),
                        'quote_mint': next((m for m in quote_mints if m), 'unknown'),
                        'sample_keys': list(item.keys())[:5],
                    })
                
                # Limit results
                if len(sol_pairs) >= 10:
                    break
        
        except Exception as e:
            logger.debug(f"Error finding SOL pairs: {e}")
        
        return sol_pairs

    async def test_all_endpoints(self):
        """Test all endpoints comprehensively"""
        logger.info("🚀 Starting Raydium API Endpoints Verification")
        logger.info("=" * 70)
        
        # Test main endpoints
        logger.info("\n📡 TESTING MAIN ENDPOINTS:")
        logger.info("-" * 50)
        
        for name, url in self.endpoints.items():
            result = await self.test_endpoint_detailed(name, url)
            self.test_results.append(result)
            
            # Add delay between requests to be respectful
            await asyncio.sleep(1)
        
        # Test alternative endpoints
        logger.info("\n🔄 TESTING ALTERNATIVE ENDPOINTS:")
        logger.info("-" * 50)
        
        for name, url in self.alternative_endpoints.items():
            result = await self.test_endpoint_detailed(name, url)
            self.test_results.append(result)
            
            # Add delay between requests
            await asyncio.sleep(1)

    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 COMPREHENSIVE RAYDIUM API TEST REPORT")
        logger.info("=" * 70)
        
        # Categorize results
        working_endpoints = [r for r in self.test_results if r['status'] == 'success']
        timeout_endpoints = [r for r in self.test_results if r['status'] == 'timeout']
        error_endpoints = [r for r in self.test_results if r['status'] in ['http_error', 'connection_error', 'json_error']]
        
        logger.info(f"\n📈 SUMMARY STATISTICS:")
        logger.info(f"  • Total endpoints tested: {len(self.test_results)}")
        logger.info(f"  • ✅ Working endpoints: {len(working_endpoints)}")
        logger.info(f"  • ⏰ Timeout endpoints: {len(timeout_endpoints)}")
        logger.info(f"  • ❌ Error endpoints: {len(error_endpoints)}")
        logger.info(f"  • 📊 Success rate: {len(working_endpoints)/len(self.test_results)*100:.1f}%")
        
        # Working endpoints details
        if working_endpoints:
            logger.info(f"\n✅ WORKING ENDPOINTS ({len(working_endpoints)}):")
            for result in working_endpoints:
                sol_pairs = result.get('sol_pairs_found', 0)
                speed = result.get('total_time_seconds', 0)
                size_mb = result.get('data_size_bytes', 0) / 1024 / 1024
                records = result.get('data_analysis', {}).get('record_count', 0)
                
                logger.info(f"  🌟 {result['name']}")
                logger.info(f"     ⏱️  {speed:.1f}s | 📊 {records:,} records | 💾 {size_mb:.1f}MB | 🌊 {sol_pairs} SOL pairs")
                
                # Show sample keys for debugging
                sample_keys = result.get('data_analysis', {}).get('sample_keys', [])
                if sample_keys:
                    logger.info(f"     🔑 Sample keys: {sample_keys[:5]}")
        
        # Problem endpoints
        if timeout_endpoints:
            logger.info(f"\n⏰ TIMEOUT ENDPOINTS ({len(timeout_endpoints)}):")
            for result in timeout_endpoints:
                logger.info(f"  • {result['name']}: {result.get('error', 'Unknown timeout')}")
        
        if error_endpoints:
            logger.info(f"\n❌ ERROR ENDPOINTS ({len(error_endpoints)}):")
            for result in error_endpoints:
                logger.info(f"  • {result['name']}: {result.get('error', 'Unknown error')}")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        
        # Find best endpoint for SOL pairs
        best_sol_endpoint = None
        best_sol_count = 0
        for result in working_endpoints:
            sol_count = result.get('sol_pairs_found', 0)
            if sol_count > best_sol_count:
                best_sol_count = sol_count
                best_sol_endpoint = result
        
        if best_sol_endpoint:
            logger.info(f"  🏆 Best for SOL pairs: {best_sol_endpoint['name']} ({best_sol_count} pairs)")
            logger.info(f"     URL: {best_sol_endpoint['url']}")
        
        # Find fastest endpoint
        fastest_endpoint = None
        fastest_time = float('inf')
        for result in working_endpoints:
            time_taken = result.get('total_time_seconds', float('inf'))
            if time_taken < fastest_time:
                fastest_time = time_taken
                fastest_endpoint = result
        
        if fastest_endpoint:
            logger.info(f"  ⚡ Fastest endpoint: {fastest_endpoint['name']} ({fastest_time:.1f}s)")
            logger.info(f"     URL: {fastest_endpoint['url']}")
        
        # Check if current primary endpoint is working
        primary_result = next((r for r in self.test_results if r['name'] == 'raydium_pools'), None)
        if primary_result:
            if primary_result['status'] == 'success':
                logger.info(f"  ✅ Current primary endpoint (raydium_pools) is WORKING")
            else:
                logger.info(f"  ⚠️  Current primary endpoint (raydium_pools) has issues: {primary_result.get('error', 'Unknown')}")
                
                # Recommend alternative
                if best_sol_endpoint and best_sol_endpoint['name'] != 'raydium_pools':
                    logger.info(f"  🔄 RECOMMEND SWITCHING to: {best_sol_endpoint['name']}")
        
        return {
            'working_endpoints': working_endpoints,
            'timeout_endpoints': timeout_endpoints,
            'error_endpoints': error_endpoints,
            'best_sol_endpoint': best_sol_endpoint,
            'fastest_endpoint': fastest_endpoint,
            'primary_endpoint_status': primary_result
        }

    def save_detailed_report(self, filename: str = None):
        """Save detailed JSON report"""
        if not filename:
            filename = f"raydium_api_test_report_{int(time.time())}.json"
        
        report_data = {
            'test_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_endpoints_tested': len(self.test_results),
                'test_duration_seconds': sum(r.get('total_time_seconds', 0) for r in self.test_results)
            },
            'endpoints_tested': self.endpoints,
            'alternative_endpoints_tested': self.alternative_endpoints,
            'detailed_results': self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\n💾 Detailed report saved to: {filename}")
        return filename

async def main():
    """Main test function"""
    tester = RaydiumAPITester()
    
    # Run comprehensive tests
    await tester.test_all_endpoints()
    
    # Generate summary
    summary = tester.generate_summary_report()
    
    # Save detailed report
    report_file = tester.save_detailed_report()
    
    # Final assessment
    working_count = len(summary['working_endpoints'])
    total_count = len(tester.test_results)
    
    if working_count > 0:
        logger.info(f"\n🎉 SUCCESS: {working_count}/{total_count} endpoints are working!")
        if summary['primary_endpoint_status'] and summary['primary_endpoint_status']['status'] == 'success':
            logger.info("✅ Current primary endpoint is functional - no changes needed")
        else:
            logger.info("⚠️  Current primary endpoint has issues - consider switching")
        return True
    else:
        logger.error(f"\n💥 CRITICAL: No endpoints are working! Need to find alternative APIs.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✅ API verification completed successfully")
        exit(0)
    else:
        print("\n❌ API verification found critical issues")
        exit(1)