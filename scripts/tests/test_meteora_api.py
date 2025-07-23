#!/usr/bin/env python3
"""
Meteora API Test Script

Tests Meteora's universal search API to understand data structure
and evaluate suitability for short-term trending token detection.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeteoraAPITester:
    """Test and analyze Meteora API endpoints"""
    
    def __init__(self):
        self.base_url = "https://universal-search-api.meteora.ag"
        self.session = None
        self.test_results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_pool_search_endpoint(self) -> Dict[str, Any]:
        """Test the main pool search endpoint with various parameters"""
        logger.info("🔍 Testing Meteora Pool Search API...")
        
        test_queries = [
            # Basic volume-sorted query
            {
                "name": "high_volume_pools",
                "params": {
                    "sort_by": "volume_24h:desc",
                    "limit": 20
                }
            },
            # TVL-sorted query
            {
                "name": "high_tvl_pools", 
                "params": {
                    "sort_by": "tvl:desc",
                    "limit": 20
                }
            },
            # Search by specific tokens
            {
                "name": "sol_pools",
                "params": {
                    "query_by": "token_mints",
                    "q": "So11111111111111111111111111111111111111112",  # SOL
                    "limit": 10
                }
            },
            # Search by pool name
            {
                "name": "pool_name_search",
                "params": {
                    "query_by": "pool_name",
                    "q": "SOL",
                    "limit": 10
                }
            }
        ]
        
        results = {}
        
        for query in test_queries:
            try:
                logger.info(f"Testing query: {query['name']}")
                
                url = f"{self.base_url}/pool/search"
                async with self.session.get(url, params=query['params']) as response:
                    if response.status == 200:
                        data = await response.json()
                        results[query['name']] = {
                            'status': 'success',
                            'data': data,
                            'pool_count': len(data.get('pools', [])) if isinstance(data, dict) else len(data) if isinstance(data, list) else 0,
                            'response_time_ms': response.headers.get('X-Response-Time', 'unknown')
                        }
                        logger.info(f"✅ {query['name']}: {results[query['name']]['pool_count']} pools found")
                    else:
                        error_text = await response.text()
                        results[query['name']] = {
                            'status': 'error',
                            'status_code': response.status,
                            'error': error_text
                        }
                        logger.error(f"❌ {query['name']}: HTTP {response.status} - {error_text}")
                        
            except Exception as e:
                results[query['name']] = {
                    'status': 'exception',
                    'error': str(e)
                }
                logger.error(f"❌ {query['name']}: Exception - {e}")
                
            # Rate limiting
            await asyncio.sleep(0.5)
            
        return results
    
    async def analyze_pool_data_structure(self, pool_data: List[Dict]) -> Dict[str, Any]:
        """Analyze the structure of pool data for trending detection"""
        logger.info("📊 Analyzing pool data structure...")
        
        if not pool_data:
            return {"error": "No pool data to analyze"}
            
        analysis = {
            "total_pools": len(pool_data),
            "sample_pool": pool_data[0] if pool_data else None,
            "available_fields": set(),
            "volume_metrics": {},
            "tvl_metrics": {},
            "liquidity_metrics": {},
            "timestamp_fields": [],
            "token_fields": []
        }
        
        # Analyze field availability across all pools
        for pool in pool_data:
            if isinstance(pool, dict):
                analysis["available_fields"].update(pool.keys())
                
                # Check for volume-related fields
                for field in pool.keys():
                    if 'volume' in field.lower():
                        if field not in analysis["volume_metrics"]:
                            analysis["volume_metrics"][field] = []
                        value = pool.get(field)
                        if isinstance(value, (int, float)):
                            analysis["volume_metrics"][field].append(value)
                    
                    # Check for TVL-related fields
                    if 'tvl' in field.lower():
                        if field not in analysis["tvl_metrics"]:
                            analysis["tvl_metrics"][field] = []
                        value = pool.get(field)
                        if isinstance(value, (int, float)):
                            analysis["tvl_metrics"][field].append(value)
                    
                    # Check for liquidity-related fields
                    if 'liquidity' in field.lower():
                        if field not in analysis["liquidity_metrics"]:
                            analysis["liquidity_metrics"][field] = []
                        value = pool.get(field)
                        if isinstance(value, (int, float)):
                            analysis["liquidity_metrics"][field].append(value)
                    
                    # Check for timestamp fields
                    if any(time_word in field.lower() for time_word in ['time', 'timestamp', 'created', 'updated']):
                        analysis["timestamp_fields"].append(field)
                    
                    # Check for token-related fields
                    if any(token_word in field.lower() for token_word in ['token', 'mint', 'address']):
                        analysis["token_fields"].append(field)
        
        # Convert sets to lists for JSON serialization
        analysis["available_fields"] = list(analysis["available_fields"])
        analysis["timestamp_fields"] = list(set(analysis["timestamp_fields"]))
        analysis["token_fields"] = list(set(analysis["token_fields"]))
        
        # Calculate statistics for numeric fields
        for metric_type in ["volume_metrics", "tvl_metrics", "liquidity_metrics"]:
            for field, values in analysis[metric_type].items():
                if values:
                    analysis[metric_type][field] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "sample_values": values[:5]  # First 5 values as examples
                    }
        
        return analysis
    
    async def test_trending_detection_feasibility(self) -> Dict[str, Any]:
        """Test if Meteora API can support trending detection requirements"""
        logger.info("🎯 Testing trending detection feasibility...")
        
        # Get high volume pools
        url = f"{self.base_url}/pool/search"
        params = {"sort_by": "volume_24h:desc", "limit": 50}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return {"error": f"API request failed: {response.status}"}
                
                data = await response.json()
                pools = data.get('pools', data if isinstance(data, list) else [])
                
                if not pools:
                    return {"error": "No pools returned from API"}
                
                # Analyze for trending detection requirements
                analysis = {
                    "api_response_time": response.headers.get('X-Response-Time', 'unknown'),
                    "total_pools_available": len(pools),
                    "trending_detection_requirements": {
                        "minute_level_polling": "unknown",  # Need to test polling frequency
                        "volume_delta_calculation": False,
                        "tvl_delta_calculation": False,
                        "vlr_calculation": False,
                        "historical_snapshots": False
                    },
                    "sample_pools": []
                }
                
                # Analyze top 10 pools for data quality
                for i, pool in enumerate(pools[:10]):
                    pool_analysis = {
                        "rank": i + 1,
                        "pool_data": pool,
                        "has_volume_24h": 'volume_24h' in pool or any('volume' in k for k in pool.keys()),
                        "has_tvl": 'tvl' in pool or any('tvl' in k for k in pool.keys()),
                        "has_liquidity": 'liquidity' in pool or any('liquidity' in k for k in pool.keys()),
                        "has_tokens": any('token' in k or 'mint' in k for k in pool.keys()),
                        "volume_value": pool.get('volume_24h', 'N/A'),
                        "tvl_value": pool.get('tvl', 'N/A')
                    }
                    analysis["sample_pools"].append(pool_analysis)
                
                # Check if we can calculate VLR (Volume-to-Liquidity Ratio)
                vlr_possible = any(
                    pool.get('volume_24h') and pool.get('liquidity') 
                    for pool in pools[:10]
                )
                analysis["trending_detection_requirements"]["vlr_calculation"] = vlr_possible
                
                # Check if volume data is available
                volume_available = any(
                    'volume' in str(pool.keys()).lower()
                    for pool in pools[:10]
                )
                analysis["trending_detection_requirements"]["volume_delta_calculation"] = volume_available
                
                # Check if TVL data is available
                tvl_available = any(
                    'tvl' in str(pool.keys()).lower()
                    for pool in pools[:10]
                )
                analysis["trending_detection_requirements"]["tvl_delta_calculation"] = tvl_available
                
                return analysis
                
        except Exception as e:
            return {"error": f"Exception during feasibility test: {e}"}
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of Meteora API"""
        logger.info("🚀 Starting comprehensive Meteora API test...")
        
        test_start = time.time()
        
        # Test 1: Pool search endpoints
        pool_search_results = await self.test_pool_search_endpoint()
        
        # Test 2: Analyze data structure
        data_analysis = {}
        if pool_search_results.get('high_volume_pools', {}).get('status') == 'success':
            pools_data = pool_search_results['high_volume_pools']['data']
            if isinstance(pools_data, dict) and 'pools' in pools_data:
                pools_list = pools_data['pools']
            elif isinstance(pools_data, list):
                pools_list = pools_data
            else:
                pools_list = []
            
            if pools_list:
                data_analysis = await self.analyze_pool_data_structure(pools_list)
        
        # Test 3: Trending detection feasibility
        trending_feasibility = await self.test_trending_detection_feasibility()
        
        test_duration = time.time() - test_start
        
        results = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(test_duration, 2),
                "api_base_url": self.base_url
            },
            "pool_search_tests": pool_search_results,
            "data_structure_analysis": data_analysis,
            "trending_detection_feasibility": trending_feasibility
        }
        
        self.test_results = results
        return results
    
    def save_results(self, filename: Optional[str] = None):
        """Save test results to file"""
        if not filename:
            timestamp = int(time.time())
            filename = f"scripts/tests/meteora_api_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"💾 Test results saved to: {filename}")


async def main():
    """Run Meteora API tests"""
    logger.info("🌟 Meteora API Testing Suite")
    logger.info("=" * 50)
    
    async with MeteoraAPITester() as tester:
        results = await tester.run_comprehensive_test()
        
        # Save results
        tester.save_results()
        
        # Print summary
        logger.info("\n📋 TEST SUMMARY:")
        logger.info(f"Duration: {results['test_summary']['duration_seconds']}s")
        
        # Pool search results
        search_results = results.get('pool_search_tests', {})
        successful_queries = sum(1 for r in search_results.values() if r.get('status') == 'success')
        logger.info(f"Pool search queries: {successful_queries}/{len(search_results)} successful")
        
        # Data analysis
        data_analysis = results.get('data_structure_analysis', {})
        if 'total_pools' in data_analysis:
            logger.info(f"Pools analyzed: {data_analysis['total_pools']}")
            logger.info(f"Available fields: {len(data_analysis.get('available_fields', []))}")
            logger.info(f"Volume metrics: {len(data_analysis.get('volume_metrics', {}))}")
            logger.info(f"TVL metrics: {len(data_analysis.get('tvl_metrics', {}))}")
        
        # Trending feasibility
        trending = results.get('trending_detection_feasibility', {})
        if 'trending_detection_requirements' in trending:
            reqs = trending['trending_detection_requirements']
            logger.info(f"VLR calculation possible: {reqs.get('vlr_calculation', False)}")
            logger.info(f"Volume data available: {reqs.get('volume_delta_calculation', False)}")
            logger.info(f"TVL data available: {reqs.get('tvl_delta_calculation', False)}")
        
        logger.info("\n✅ Meteora API test completed!")


if __name__ == "__main__":
    asyncio.run(main()) 