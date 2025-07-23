#!/usr/bin/env python3
"""
Combined Meteora + Jupiter API Test Script

Tests both Meteora and Jupiter APIs together to understand their combined
potential for short-term trending token detection.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Import our individual testers
from test_meteora_api import MeteoraAPITester
from test_jupiter_api import JupiterAPITester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CombinedTrendingAPITester:
    """Combined tester for Meteora + Jupiter APIs"""
    
    def __init__(self):
        self.test_results = {}
        self.meteora_tester = None
        self.jupiter_tester = None
        
    async def __aenter__(self):
        self.meteora_tester = await MeteoraAPITester().__aenter__()
        self.jupiter_tester = await JupiterAPITester().__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.meteora_tester:
            await self.meteora_tester.__aexit__(exc_type, exc_val, exc_tb)
        if self.jupiter_tester:
            await self.jupiter_tester.__aexit__(exc_type, exc_val, exc_tb)
    
    async def test_data_overlap_analysis(self) -> Dict[str, Any]:
        """Analyze overlap and complementarity between Meteora and Jupiter data"""
        logger.info("🔄 Testing data overlap between Meteora and Jupiter...")
        
        analysis = {
            "data_overlap": {},
            "complementary_strengths": {},
            "trending_detection_potential": {},
            "combined_metrics": {}
        }
        
        # Get sample data from both APIs
        try:
            # Get Meteora pool data
            meteora_url = f"{self.meteora_tester.base_url}/pool/search"
            meteora_params = {"sort_by": "volume_24h:desc", "limit": 10}
            
            async with self.meteora_tester.session.get(meteora_url, params=meteora_params) as response:
                if response.status == 200:
                    meteora_data = await response.json()
                    meteora_pools = meteora_data.get('pools', meteora_data if isinstance(meteora_data, list) else [])
                    
                    analysis["meteora_sample"] = {
                        "pools_found": len(meteora_pools),
                        "sample_pool": meteora_pools[0] if meteora_pools else None,
                        "available_fields": list(meteora_pools[0].keys()) if meteora_pools else []
                    }
        except Exception as e:
            analysis["meteora_sample"] = {"error": str(e)}
        
        # Get Jupiter token data
        try:
            jupiter_url = f"{self.jupiter_tester.base_urls['price']}/tokens"
            
            async with self.jupiter_tester.session.get(jupiter_url) as response:
                if response.status == 200:
                    jupiter_data = await response.json()
                    
                    analysis["jupiter_sample"] = {
                        "tokens_found": len(jupiter_data) if isinstance(jupiter_data, list) else "unknown",
                        "sample_token": jupiter_data[0] if isinstance(jupiter_data, list) and jupiter_data else None,
                        "available_fields": list(jupiter_data[0].keys()) if isinstance(jupiter_data, list) and jupiter_data else []
                    }
        except Exception as e:
            analysis["jupiter_sample"] = {"error": str(e)}
        
        # Analyze complementarity
        meteora_fields = analysis.get("meteora_sample", {}).get("available_fields", [])
        jupiter_fields = analysis.get("jupiter_sample", {}).get("available_fields", [])
        
        analysis["data_overlap"] = {
            "meteora_unique_fields": [f for f in meteora_fields if f not in jupiter_fields],
            "jupiter_unique_fields": [f for f in jupiter_fields if f not in meteora_fields],
            "common_fields": [f for f in meteora_fields if f in jupiter_fields],
            "total_combined_fields": len(set(meteora_fields + jupiter_fields))
        }
        
        return analysis
    
    async def run_comprehensive_combined_test(self) -> Dict[str, Any]:
        """Run comprehensive combined test of both APIs"""
        logger.info("🚀 Starting comprehensive Meteora + Jupiter combined test...")
        
        test_start = time.time()
        
        # Run individual API tests
        logger.info("📊 Running individual API tests...")
        meteora_results = await self.meteora_tester.run_comprehensive_test()
        jupiter_results = await self.jupiter_tester.run_comprehensive_test()
        
        # Run combined analysis tests
        logger.info("🔄 Running combined analysis tests...")
        overlap_analysis = await self.test_data_overlap_analysis()
        
        test_duration = time.time() - test_start
        
        # Compile comprehensive results
        results = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_duration_seconds": round(test_duration, 2)
            },
            "individual_results": {
                "meteora": meteora_results,
                "jupiter": jupiter_results
            },
            "combined_analysis": {
                "data_overlap": overlap_analysis
            }
        }
        
        self.test_results = results
        return results
    
    def save_results(self, filename: Optional[str] = None):
        """Save combined test results to file"""
        if not filename:
            timestamp = int(time.time())
            filename = f"scripts/tests/meteora_jupiter_combined_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"💾 Combined test results saved to: {filename}")


async def main():
    """Run combined Meteora + Jupiter API tests"""
    logger.info("🌟 Meteora + Jupiter Combined API Testing Suite")
    logger.info("=" * 60)
    
    async with CombinedTrendingAPITester() as tester:
        results = await tester.run_comprehensive_combined_test()
        
        # Save results
        tester.save_results()
        
        # Print summary
        logger.info("\n📋 COMPREHENSIVE TEST SUMMARY:")
        logger.info("=" * 50)
        
        summary = results['test_summary']
        logger.info(f"Total Duration: {summary['total_duration_seconds']}s")
        
        logger.info("\n✅ Combined Meteora + Jupiter API test completed!")


if __name__ == "__main__":
    asyncio.run(main()) 