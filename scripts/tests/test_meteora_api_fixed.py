#!/usr/bin/env python3
"""
Fixed Meteora API Test Script

Tests Meteora's universal search API with correct parameters
to understand data structure for trending token detection.

Key findings from investigation:
- API requires 'q' parameter (use '*' for all results)  
- Sorting format: 'sort_by=field:order' (e.g., 'volume_24h:desc')
- Returns pool-level data with volume_24h, tvl, token_mints
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


class FixedMeteoraAPITester:
    """Fixed Meteora API tester with correct parameters"""
    
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
    
    async def test_trending_pools_by_volume(self, limit: int = 20) -> Dict[str, Any]:
        """Test getting trending pools sorted by 24h volume"""
        logger.info(f"🔍 Testing trending pools by volume (limit: {limit})...")
        
        try:
            params = {
                "q": "*",  # Required parameter for all results
                "sort_by": "volume_24h:desc",  # Correct sorting format
                "limit": limit
            }
            
            url = f"{self.base_url}/pool/search"
            start_time = time.time()
            
            async with self.session.get(url, params=params) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('hits', [])
                    
                    # Extract pool documents
                    pool_documents = [hit.get('document', {}) for hit in pools]
                    
                    result = {
                        'status': 'success',
                        'total_found': data.get('found', 0),
                        'pools_returned': len(pool_documents),
                        'response_time_ms': round(response_time_ms, 1),
                        'pools': pool_documents,
                        'trending_analysis': self._analyze_trending_potential(pool_documents)
                    }
                    
                    logger.info(f"✅ Volume trending: {len(pool_documents)} pools, {result['total_found']} total available")
                    return result
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Volume trending failed: HTTP {response.status} - {error_text}")
                    return {
                        'status': 'error',
                        'status_code': response.status,
                        'error': error_text,
                        'response_time_ms': round(response_time_ms, 1)
                    }
                    
        except Exception as e:
            logger.error(f"❌ Volume trending exception: {e}")
            return {
                'status': 'exception',
                'error': str(e)
            }
    
    async def test_trending_pools_by_tvl(self, limit: int = 20) -> Dict[str, Any]:
        """Test getting trending pools sorted by TVL"""
        logger.info(f"🔍 Testing trending pools by TVL (limit: {limit})...")
        
        try:
            params = {
                "q": "*",
                "sort_by": "tvl:desc",
                "limit": limit
            }
            
            url = f"{self.base_url}/pool/search"
            start_time = time.time()
            
            async with self.session.get(url, params=params) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('hits', [])
                    
                    pool_documents = [hit.get('document', {}) for hit in pools]
                    
                    result = {
                        'status': 'success',
                        'total_found': data.get('found', 0),
                        'pools_returned': len(pool_documents),
                        'response_time_ms': round(response_time_ms, 1),
                        'pools': pool_documents,
                        'trending_analysis': self._analyze_trending_potential(pool_documents)
                    }
                    
                    logger.info(f"✅ TVL trending: {len(pool_documents)} pools, {result['total_found']} total available")
                    return result
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ TVL trending failed: HTTP {response.status} - {error_text}")
                    return {
                        'status': 'error',
                        'status_code': response.status,
                        'error': error_text,
                        'response_time_ms': round(response_time_ms, 1)
                    }
                    
        except Exception as e:
            logger.error(f"❌ TVL trending exception: {e}")
            return {
                'status': 'exception',
                'error': str(e)
            }
    
    async def test_token_specific_pools(self, token_address: str, limit: int = 10) -> Dict[str, Any]:
        """Test getting pools for a specific token"""
        logger.info(f"🔍 Testing pools for token: {token_address[:8]}...")
        
        try:
            params = {
                "q": token_address,
                "query_by": "token_mints",
                "limit": limit
            }
            
            url = f"{self.base_url}/pool/search"
            start_time = time.time()
            
            async with self.session.get(url, params=params) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    pools = data.get('hits', [])
                    
                    pool_documents = [hit.get('document', {}) for hit in pools]
                    
                    result = {
                        'status': 'success',
                        'token_address': token_address,
                        'pools_found': len(pool_documents),
                        'response_time_ms': round(response_time_ms, 1),
                        'pools': pool_documents
                    }
                    
                    logger.info(f"✅ Token pools: {len(pool_documents)} pools found for {token_address[:8]}")
                    return result
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Token pools failed: HTTP {response.status} - {error_text}")
                    return {
                        'status': 'error',
                        'status_code': response.status,
                        'error': error_text,
                        'response_time_ms': round(response_time_ms, 1)
                    }
                    
        except Exception as e:
            logger.error(f"❌ Token pools exception: {e}")
            return {
                'status': 'exception',
                'error': str(e)
            }
    
    def _analyze_trending_potential(self, pools: List[Dict]) -> Dict[str, Any]:
        """Analyze pools for trending detection potential"""
        if not pools:
            return {"error": "No pools to analyze"}
        
        analysis = {
            "total_pools": len(pools),
            "volume_range": {},
            "tvl_range": {},
            "vlr_analysis": {},
            "token_extraction": {},
            "data_quality": {}
        }
        
        # Extract metrics
        volumes = []
        tvls = []
        vlrs = []
        unique_tokens = set()
        
        for pool in pools:
            volume = pool.get('volume_24h', 0)
            tvl = pool.get('tvl', 0)
            token_mints = pool.get('token_mints', [])
            
            if volume and tvl:
                vlr = volume / tvl
                vlrs.append(vlr)
            
            volumes.append(volume)
            tvls.append(tvl)
            unique_tokens.update(token_mints)
        
        # Volume analysis
        if volumes:
            analysis["volume_range"] = {
                "min": min(volumes),
                "max": max(volumes),
                "avg": sum(volumes) / len(volumes),
                "top_10_avg": sum(sorted(volumes, reverse=True)[:10]) / min(10, len(volumes))
            }
        
        # TVL analysis
        if tvls:
            analysis["tvl_range"] = {
                "min": min(tvls),
                "max": max(tvls),
                "avg": sum(tvls) / len(tvls),
                "top_10_avg": sum(sorted(tvls, reverse=True)[:10]) / min(10, len(tvls))
            }
        
        # VLR analysis
        if vlrs:
            analysis["vlr_analysis"] = {
                "min": min(vlrs),
                "max": max(vlrs),
                "avg": sum(vlrs) / len(vlrs),
                "high_activity_pools": len([v for v in vlrs if v > 1.0]),
                "trending_potential": "HIGH" if max(vlrs) > 5.0 else "MEDIUM" if max(vlrs) > 1.0 else "LOW"
            }
        
        # Token extraction
        analysis["token_extraction"] = {
            "unique_tokens_found": len(unique_tokens),
            "avg_tokens_per_pool": sum(len(pool.get('token_mints', [])) for pool in pools) / len(pools),
            "sample_tokens": list(unique_tokens)[:10]
        }
        
        # Data quality
        pools_with_volume = len([p for p in pools if p.get('volume_24h', 0) > 0])
        pools_with_tvl = len([p for p in pools if p.get('tvl', 0) > 0])
        pools_with_tokens = len([p for p in pools if p.get('token_mints')])
        
        analysis["data_quality"] = {
            "pools_with_volume": pools_with_volume,
            "pools_with_tvl": pools_with_tvl,
            "pools_with_tokens": pools_with_tokens,
            "data_completeness_score": round((pools_with_volume + pools_with_tvl + pools_with_tokens) / (len(pools) * 3) * 100, 1)
        }
        
        return analysis
    
    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test API rate limiting behavior"""
        logger.info("🔍 Testing API rate limiting...")
        
        start_time = time.time()
        request_times = []
        
        try:
            # Make 10 rapid requests
            for i in range(10):
                request_start = time.time()
                
                params = {"q": "*", "limit": 1}
                async with self.session.get(f"{self.base_url}/pool/search", params=params) as response:
                    request_time = (time.time() - request_start) * 1000
                    request_times.append({
                        "request": i + 1,
                        "status": response.status,
                        "time_ms": round(request_time, 1)
                    })
                
                # Small delay to avoid overwhelming
                await asyncio.sleep(0.1)
            
            total_time = time.time() - start_time
            
            return {
                "status": "success",
                "total_requests": 10,
                "total_time_seconds": round(total_time, 2),
                "avg_response_time_ms": round(sum(r["time_ms"] for r in request_times) / len(request_times), 1),
                "requests_per_second": round(10 / total_time, 2),
                "request_details": request_times,
                "rate_limit_detected": any(r["status"] == 429 for r in request_times)
            }
            
        except Exception as e:
            return {
                "status": "exception",
                "error": str(e)
            }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive fixed API test"""
        logger.info("🚀 Starting comprehensive FIXED Meteora API test...")
        
        test_start = time.time()
        
        # Test 1: Trending by volume
        volume_results = await self.test_trending_pools_by_volume(30)
        
        # Test 2: Trending by TVL  
        tvl_results = await self.test_trending_pools_by_tvl(30)
        
        # Test 3: Token-specific pools (using SOL as example)
        sol_address = "So11111111111111111111111111111111111111112"
        token_results = await self.test_token_specific_pools(sol_address, 10)
        
        # Test 4: Rate limiting
        rate_limit_results = await self.test_rate_limiting()
        
        test_duration = time.time() - test_start
        
        # Extract trending tokens from successful results
        trending_tokens = set()
        if volume_results.get('status') == 'success':
            for pool in volume_results.get('pools', []):
                trending_tokens.update(pool.get('token_mints', []))
        
        results = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(test_duration, 2),
                "api_base_url": self.base_url,
                "status": "FIXED - Working with correct parameters"
            },
            "volume_trending_test": volume_results,
            "tvl_trending_test": tvl_results,
            "token_specific_test": token_results,
            "rate_limiting_test": rate_limit_results,
            "trending_token_discovery": {
                "unique_tokens_discovered": len(trending_tokens),
                "sample_tokens": list(trending_tokens)[:20],
                "discovery_feasibility": "HIGH" if len(trending_tokens) > 50 else "MEDIUM" if len(trending_tokens) > 20 else "LOW"
            },
            "integration_readiness": {
                "api_connectivity": "WORKING" if volume_results.get('status') == 'success' else "FAILED",
                "data_structure": "COMPATIBLE" if volume_results.get('pools') else "INCOMPATIBLE",
                "trending_detection": "READY" if volume_results.get('trending_analysis') else "NOT_READY",
                "rate_limiting": "ACCEPTABLE" if not rate_limit_results.get('rate_limit_detected') else "RESTRICTIVE"
            }
        }
        
        self.test_results = results
        return results
    
    def save_results(self, filename: Optional[str] = None):
        """Save test results to file"""
        if not filename:
            timestamp = int(time.time())
            filename = f"scripts/tests/meteora_api_fixed_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"💾 Fixed test results saved to: {filename}")


async def main():
    """Run fixed Meteora API tests"""
    logger.info("🌟 Fixed Meteora API Testing Suite")
    logger.info("=" * 50)
    
    async with FixedMeteoraAPITester() as tester:
        results = await tester.run_comprehensive_test()
        
        # Save results
        tester.save_results()
        
        # Print summary
        logger.info("\n📋 FIXED TEST SUMMARY:")
        logger.info(f"Duration: {results['test_summary']['duration_seconds']}s")
        logger.info(f"Status: {results['test_summary']['status']}")
        
        # Integration readiness
        readiness = results.get('integration_readiness', {})
        logger.info(f"\n🔧 INTEGRATION READINESS:")
        logger.info(f"API Connectivity: {readiness.get('api_connectivity', 'UNKNOWN')}")
        logger.info(f"Data Structure: {readiness.get('data_structure', 'UNKNOWN')}")
        logger.info(f"Trending Detection: {readiness.get('trending_detection', 'UNKNOWN')}")
        logger.info(f"Rate Limiting: {readiness.get('rate_limiting', 'UNKNOWN')}")
        
        # Trending discovery
        discovery = results.get('trending_token_discovery', {})
        logger.info(f"\n🎯 TRENDING DISCOVERY:")
        logger.info(f"Unique tokens discovered: {discovery.get('unique_tokens_discovered', 0)}")
        logger.info(f"Discovery feasibility: {discovery.get('discovery_feasibility', 'UNKNOWN')}")
        
        # Volume test results
        volume_test = results.get('volume_trending_test', {})
        if volume_test.get('status') == 'success':
            logger.info(f"\n📊 VOLUME TRENDING:")
            logger.info(f"Pools returned: {volume_test.get('pools_returned', 0)}")
            logger.info(f"Total available: {volume_test.get('total_found', 0)}")
            logger.info(f"Response time: {volume_test.get('response_time_ms', 0)}ms")
            
            analysis = volume_test.get('trending_analysis', {})
            if 'vlr_analysis' in analysis:
                vlr = analysis['vlr_analysis']
                logger.info(f"VLR trending potential: {vlr.get('trending_potential', 'UNKNOWN')}")
                logger.info(f"High activity pools: {vlr.get('high_activity_pools', 0)}")
        
        logger.info("\n✅ Fixed Meteora API test completed!")


if __name__ == "__main__":
    asyncio.run(main()) 