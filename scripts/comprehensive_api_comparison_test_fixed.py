#!/usr/bin/env python3
"""
FIXED Comprehensive API Comparison Test

Tests all available APIs against specific tokens using the CORRECT method names.
Fixed issues identified in the original test:

1. BirdEye: Use get_token_overview() and get_multi_price() instead of non-existent methods
2. Jupiter: Use get_batch_prices() and get_comprehensive_token_analysis() 
3. Orca: Use get_token_pools() with proper session initialization
4. Raydium: Use get_token_pairs() instead of get_token_pools()
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
import os
import sys
import logging
from tabulate import tabulate

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all API connectors
from api.birdeye_connector import BirdeyeAPI
from api.rugcheck_connector import RugCheckConnector
from api.enhanced_jupiter_connector import EnhancedJupiterConnector
from api.orca_connector import OrcaConnector
from api.raydium_connector import RaydiumConnector
from core.config_manager import ConfigManager, get_config_manager
from services.logger_setup import LoggerSetup
from services.enhanced_cache_manager import EnhancedPositionCacheManager
from services.rate_limiter_service import RateLimiterService
from core.cache_manager import CacheManager

class DexScreenerConnector:
    """DexScreener API connector for comparison testing"""
    
    def __init__(self):
        self.base_url = "https://api.dexscreener.com"
        self.api_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_response_time_ms": 0,
            "endpoints_used": set(),
        }
        
    async def get_token_data(self, token_address: str) -> Optional[Dict]:
        """Get token data from DexScreener"""
        start_time = time.time()
        self.api_stats["total_calls"] += 1
        
        try:
            async with aiohttp.ClientSession() as session:
                endpoint = f"/latest/dex/tokens/{token_address}"
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    self.api_stats["total_response_time_ms"] += response_time_ms
                    
                    if response.status == 200:
                        self.api_stats["successful_calls"] += 1
                        data = await response.json()
                        return data
                    else:
                        self.api_stats["failed_calls"] += 1
                        return None
                        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.api_stats["total_response_time_ms"] += response_time_ms
            self.api_stats["failed_calls"] += 1
            logging.error(f"DexScreener API error for {token_address}: {e}")
            return None

class FixedAPIComparison:
    """Fixed API comparison test runner with correct method names"""
    
    def __init__(self):
        # Test tokens from user's table
        self.test_tokens = {
            "USELESS": "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk",
            "TRUMP": "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN", 
            "aura": "DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2",
            "GOR": "71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4Bhqd9iL6bEFELvg",
            "SPX": "J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr",
            "MUMU": "5LafQUrVco6o7KMz42eqVEJ9LW31StPyGjeeu5sKoMtA",
            "$michi": "5mbK36SZ7J19An8jFochhQS4of8g6BwUjbeCSxBSoWdp",
            "BILLY": "3B5wuUrMEi5yATD7on46hKfej3pfmd7t1RKgrsN3pump",
            "INF": "5oVNBeEEQvYi1cX3ir8Dx5n1P7pdxydbGF2X4TxVusJm"
        }
        
        # Initialize results storage
        self.results = {
            "test_start_time": datetime.now().isoformat(),
            "api_results": {},
            "performance_metrics": {},
            "data_coverage": {},
            "comparison_summary": {},
            "fixes_applied": [
                "Fixed BirdEye method names: get_token_overview(), get_multi_price()",
                "Fixed Jupiter method names: get_batch_prices(), get_comprehensive_token_analysis()",
                "Fixed Raydium method names: get_token_pairs() instead of get_token_pools()",
                "Fixed Orca session initialization and error handling",
                "Added proper async session management"
            ]
        }
        
        # Setup logging
        self.logger_setup = LoggerSetup(__name__, log_level="INFO")
        self.logger = self.logger_setup.logger
        
        # Initialize config
        self.config_manager = get_config_manager()
        self.config = self.config_manager.get_config()
        
        # Initialize API connectors
        self.apis = {}
        
        # Initialize cache manager and rate limiter for BirdEye API
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService()
        
    async def initialize_apis(self):
        """Initialize all API connectors with proper error handling"""
        try:
            # BirdEye API
            birdeye_config = self.config.get("BIRDEYE_API", {})
            self.apis["birdeye"] = BirdeyeAPI(
                config=birdeye_config,
                logger=self.logger,
                cache_manager=self.cache_manager,
                rate_limiter=self.rate_limiter
            )
            
            # RugCheck API
            self.apis["rugcheck"] = RugCheckConnector()
            
            # Jupiter API
            self.apis["jupiter"] = EnhancedJupiterConnector()
            
            # Orca API - with proper session initialization
            self.apis["orca"] = OrcaConnector()
            await self.apis["orca"].__aenter__()  # Initialize session
            
            # Raydium API - with proper session initialization  
            self.apis["raydium"] = RaydiumConnector()
            await self.apis["raydium"].__aenter__()  # Initialize session
            
            # DexScreener API
            self.apis["dexscreener"] = DexScreenerConnector()
            
            self.logger.info(f"✅ Initialized {len(self.apis)} API connectors with fixes applied")
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing APIs: {e}")
            raise
    
    async def test_birdeye_api(self, token_address: str, symbol: str) -> Dict[str, Any]:
        """Test BirdEye API using CORRECT method names"""
        start_time = time.time()
        result = {
            "api_name": "BirdEye",
            "token_address": token_address,
            "symbol": symbol,
            "success": False,
            "response_time_ms": 0,
            "data_points": 0,
            "data_quality": "unknown",
            "error": None,
            "raw_data": None,
            "methods_used": ["get_token_overview", "get_multi_price"]
        }
        
        try:
            # Use CORRECT BirdEye methods
            token_overview = await self.apis["birdeye"].get_token_overview(token_address)
            price_data = await self.apis["birdeye"].get_multi_price([token_address])
            
            response_time = (time.time() - start_time) * 1000
            result["response_time_ms"] = response_time
            
            if token_overview or price_data:
                result["success"] = True
                result["raw_data"] = {
                    "overview": token_overview,
                    "price": price_data
                }
                
                # Count data points
                data_points = 0
                if token_overview:
                    data_points += len([k for k, v in token_overview.items() if v is not None])
                if price_data:
                    data_points += len([k for k, v in price_data.items() if v is not None])
                    
                result["data_points"] = data_points
                result["data_quality"] = "excellent" if data_points > 15 else "good" if data_points > 8 else "basic"
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000
            
        return result
    
    async def test_rugcheck_api(self, token_address: str, symbol: str) -> Dict[str, Any]:
        """Test RugCheck API"""
        start_time = time.time()
        result = {
            "api_name": "RugCheck",
            "token_address": token_address,
            "symbol": symbol,
            "success": False,
            "response_time_ms": 0,
            "data_points": 0,
            "data_quality": "unknown",
            "error": None,
            "raw_data": None,
            "methods_used": ["get_token_report"]
        }
        
        try:
            token_data = await self.apis["rugcheck"].get_token_report(token_address)
            
            response_time = (time.time() - start_time) * 1000
            result["response_time_ms"] = response_time
            
            if token_data:
                result["success"] = True
                result["raw_data"] = token_data
                
                # Count data points
                data_points = len([k for k, v in token_data.items() if v is not None])
                result["data_points"] = data_points
                result["data_quality"] = "excellent" if data_points > 15 else "good" if data_points > 8 else "basic"
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000
            
        return result
    
    async def test_jupiter_api(self, token_address: str, symbol: str) -> Dict[str, Any]:
        """Test Jupiter API using CORRECT method names"""
        start_time = time.time()
        result = {
            "api_name": "Jupiter",
            "token_address": token_address,
            "symbol": symbol,
            "success": False,
            "response_time_ms": 0,
            "data_points": 0,
            "data_quality": "unknown",
            "error": None,
            "raw_data": None,
            "methods_used": ["get_batch_prices", "get_comprehensive_token_analysis"]
        }
        
        try:
            # Use CORRECT Jupiter methods
            price_data = await self.apis["jupiter"].get_batch_prices([token_address])
            analysis_data = await self.apis["jupiter"].get_comprehensive_token_analysis([token_address])
            
            response_time = (time.time() - start_time) * 1000
            result["response_time_ms"] = response_time
            
            if price_data or analysis_data:
                result["success"] = True
                result["raw_data"] = {
                    "prices": price_data,
                    "analysis": analysis_data
                }
                
                # Count data points
                data_points = 0
                if price_data:
                    data_points += len(price_data) * 5  # Estimate based on price data structure
                if analysis_data:
                    data_points += len(analysis_data) * 10  # Estimate based on analysis data
                    
                result["data_points"] = data_points
                result["data_quality"] = "excellent" if data_points > 20 else "good" if data_points > 10 else "basic"
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000
            
        return result
    
    async def test_orca_api(self, token_address: str, symbol: str) -> Dict[str, Any]:
        """Test Orca API with proper session handling"""
        start_time = time.time()
        result = {
            "api_name": "Orca",
            "token_address": token_address,
            "symbol": symbol,
            "success": False,
            "response_time_ms": 0,
            "data_points": 0,
            "data_quality": "unknown",
            "error": None,
            "raw_data": None,
            "methods_used": ["get_token_pools", "get_pool_analytics"]
        }
        
        try:
            # Use CORRECT Orca methods with proper error handling
            pool_data = await self.apis["orca"].get_token_pools(token_address)
            analytics_data = await self.apis["orca"].get_pool_analytics(token_address)
            
            response_time = (time.time() - start_time) * 1000
            result["response_time_ms"] = response_time
            
            if pool_data or analytics_data:
                result["success"] = True
                result["raw_data"] = {
                    "pools": pool_data,
                    "analytics": analytics_data
                }
                
                # Count data points
                data_points = 0
                if pool_data:
                    data_points += len(pool_data) * 8  # Estimate based on pool data structure
                if analytics_data:
                    data_points += len([k for k, v in analytics_data.items() if v is not None])
                    
                result["data_points"] = data_points
                result["data_quality"] = "excellent" if data_points > 15 else "good" if data_points > 5 else "basic"
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000
            
        return result
    
    async def test_raydium_api(self, token_address: str, symbol: str) -> Dict[str, Any]:
        """Test Raydium API using CORRECT method names"""
        start_time = time.time()
        result = {
            "api_name": "Raydium",
            "token_address": token_address,
            "symbol": symbol,
            "success": False,
            "response_time_ms": 0,
            "data_points": 0,
            "data_quality": "unknown",
            "error": None,
            "raw_data": None,
            "methods_used": ["get_token_pairs", "get_pool_stats"]
        }
        
        try:
            # Use CORRECT Raydium methods
            pairs_data = await self.apis["raydium"].get_token_pairs(token_address)
            stats_data = await self.apis["raydium"].get_pool_stats(token_address)
            
            response_time = (time.time() - start_time) * 1000
            result["response_time_ms"] = response_time
            
            if pairs_data or stats_data:
                result["success"] = True
                result["raw_data"] = {
                    "pairs": pairs_data,
                    "stats": stats_data
                }
                
                # Count data points
                data_points = 0
                if pairs_data:
                    data_points += len(pairs_data) * 10  # Estimate based on pairs data
                if stats_data:
                    data_points += len([k for k, v in stats_data.items() if v is not None])
                    
                result["data_points"] = data_points
                result["data_quality"] = "excellent" if data_points > 20 else "good" if data_points > 10 else "basic"
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000
            
        return result
    
    async def test_dexscreener_api(self, token_address: str, symbol: str) -> Dict[str, Any]:
        """Test DexScreener API"""
        start_time = time.time()
        result = {
            "api_name": "DexScreener",
            "token_address": token_address,
            "symbol": symbol,
            "success": False,
            "response_time_ms": 0,
            "data_points": 0,
            "data_quality": "unknown",
            "error": None,
            "raw_data": None,
            "methods_used": ["get_token_data"]
        }
        
        try:
            token_data = await self.apis["dexscreener"].get_token_data(token_address)
            
            response_time = (time.time() - start_time) * 1000
            result["response_time_ms"] = response_time
            
            if token_data:
                result["success"] = True
                result["raw_data"] = token_data
                
                # Count data points
                pairs = token_data.get("pairs", [])
                data_points = len(pairs) * 10  # Estimate based on pairs data
                result["data_points"] = data_points
                result["data_quality"] = "excellent" if data_points > 50 else "good" if data_points > 20 else "basic"
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time_ms"] = (time.time() - start_time) * 1000
            
        return result
    
    async def test_all_apis_for_token(self, symbol: str, token_address: str) -> Dict[str, Any]:
        """Test all APIs for a single token using FIXED methods"""
        self.logger.info(f"🔍 Testing all APIs for {symbol} ({token_address}) with FIXED methods")
        
        # Test all APIs concurrently
        tasks = [
            self.test_birdeye_api(token_address, symbol),
            self.test_rugcheck_api(token_address, symbol),
            self.test_jupiter_api(token_address, symbol),
            self.test_orca_api(token_address, symbol),
            self.test_raydium_api(token_address, symbol),
            self.test_dexscreener_api(token_address, symbol)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        token_results = {}
        for result in results:
            if isinstance(result, dict):
                api_name = result["api_name"]
                token_results[api_name] = result
                
                # Log result with methods used
                status = "✅" if result["success"] else "❌"
                methods = ", ".join(result.get("methods_used", []))
                self.logger.info(f"  {status} {api_name}: {result['response_time_ms']:.1f}ms, {result['data_points']} data points, methods: {methods}")
                if result.get("error"):
                    self.logger.warning(f"    Error: {result['error']}")
            else:
                self.logger.error(f"  ❌ Exception in API test: {result}")
        
        return token_results
    
    async def run_comprehensive_test(self):
        """Run comprehensive API test with all fixes applied"""
        self.logger.info("🚀 Starting FIXED Comprehensive API Comparison Test")
        self.logger.info(f"Testing {len(self.test_tokens)} tokens across {len(self.apis)} APIs with correct method names")
        
        # Initialize APIs
        await self.initialize_apis()
        
        # Test each token
        for symbol, token_address in self.test_tokens.items():
            try:
                token_results = await self.test_all_apis_for_token(symbol, token_address)
                self.results["api_results"][symbol] = token_results
                
                # Add small delay between tokens to be respectful to APIs
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"❌ Error testing {symbol}: {e}")
                self.results["api_results"][symbol] = {"error": str(e)}
        
        # Clean up API connections
        await self.cleanup_apis()
        
        # Generate analysis
        self.analyze_results()
        
        # Save results
        self.save_results()
        
        # Display summary
        self.display_summary()
    
    async def cleanup_apis(self):
        """Properly close API connections"""
        try:
            if "orca" in self.apis:
                await self.apis["orca"].__aexit__(None, None, None)
            if "raydium" in self.apis:
                await self.apis["raydium"].__aexit__(None, None, None)
        except Exception as e:
            self.logger.warning(f"Error during API cleanup: {e}")
    
    def analyze_results(self):
        """Analyze test results and generate insights"""
        self.logger.info("📊 Analyzing FIXED test results...")
        
        # Performance metrics
        api_performance = defaultdict(lambda: {
            "total_calls": 0,
            "successful_calls": 0,
            "total_response_time": 0,
            "total_data_points": 0,
            "success_rate": 0,
            "avg_response_time": 0,
            "avg_data_points": 0,
            "methods_used": set()
        })
        
        # Data coverage
        token_coverage = defaultdict(lambda: {
            "apis_with_data": [],
            "apis_without_data": [],
            "best_api": None,
            "total_data_points": 0
        })
        
        # Process results
        for symbol, token_results in self.results["api_results"].items():
            if isinstance(token_results, dict) and "error" not in token_results:
                best_api = None
                best_data_points = 0
                
                for api_name, api_result in token_results.items():
                    # Update API performance
                    perf = api_performance[api_name]
                    perf["total_calls"] += 1
                    
                    # Track methods used
                    if "methods_used" in api_result:
                        perf["methods_used"].update(api_result["methods_used"])
                    
                    if api_result["success"]:
                        perf["successful_calls"] += 1
                        perf["total_response_time"] += api_result["response_time_ms"]
                        perf["total_data_points"] += api_result["data_points"]
                        
                        # Track coverage
                        token_coverage[symbol]["apis_with_data"].append(api_name)
                        token_coverage[symbol]["total_data_points"] += api_result["data_points"]
                        
                        # Find best API for this token
                        if api_result["data_points"] > best_data_points:
                            best_data_points = api_result["data_points"]
                            best_api = api_name
                    else:
                        token_coverage[symbol]["apis_without_data"].append(api_name)
                
                token_coverage[symbol]["best_api"] = best_api
        
        # Calculate final metrics
        for api_name, perf in api_performance.items():
            if perf["total_calls"] > 0:
                perf["success_rate"] = (perf["successful_calls"] / perf["total_calls"]) * 100
                
            if perf["successful_calls"] > 0:
                perf["avg_response_time"] = perf["total_response_time"] / perf["successful_calls"]
                perf["avg_data_points"] = perf["total_data_points"] / perf["successful_calls"]
            
            # Convert set to list for JSON serialization
            perf["methods_used"] = list(perf["methods_used"])
        
        self.results["performance_metrics"] = dict(api_performance)
        self.results["data_coverage"] = dict(token_coverage)
        
        # Generate comparison summary
        successful_apis = [api for api, perf in api_performance.items() if perf["success_rate"] > 0]
        
        if successful_apis:
            self.results["comparison_summary"] = {
                "best_overall_api": max(successful_apis, 
                                      key=lambda x: api_performance[x]["success_rate"] * api_performance[x]["avg_data_points"]),
                "fastest_api": min(successful_apis, 
                                 key=lambda x: api_performance[x]["avg_response_time"] if api_performance[x]["avg_response_time"] > 0 else float('inf')),
                "most_comprehensive_api": max(successful_apis, 
                                            key=lambda x: api_performance[x]["avg_data_points"]),
                "most_reliable_api": max(successful_apis, 
                                       key=lambda x: api_performance[x]["success_rate"])
            }
        else:
            self.results["comparison_summary"] = {
                "best_overall_api": "None",
                "fastest_api": "None", 
                "most_comprehensive_api": "None",
                "most_reliable_api": "None"
            }
    
    def display_summary(self):
        """Display comprehensive test summary with fixes"""
        print("\n" + "="*80)
        print("🏆 FIXED COMPREHENSIVE API COMPARISON TEST RESULTS")
        print("="*80)
        
        # Show fixes applied
        print("\n🔧 FIXES APPLIED:")
        for fix in self.results["fixes_applied"]:
            print(f"  • {fix}")
        
        # Performance Summary Table
        print("\n📊 API PERFORMANCE METRICS:")
        perf_data = []
        for api_name, metrics in self.results["performance_metrics"].items():
            methods_str = ", ".join(metrics["methods_used"][:2])  # Show first 2 methods
            if len(metrics["methods_used"]) > 2:
                methods_str += "..."
                
            perf_data.append([
                api_name,
                f"{metrics['success_rate']:.1f}%",
                f"{metrics['avg_response_time']:.1f}ms",
                f"{metrics['avg_data_points']:.1f}",
                metrics['successful_calls'],
                metrics['total_calls'],
                methods_str
            ])
        
        print(tabulate(perf_data, 
                      headers=["API", "Success Rate", "Avg Response", "Avg Data Points", "Successful", "Total Calls", "Methods Used"],
                      tablefmt="grid"))
        
        # Token Coverage Table
        print("\n🎯 TOKEN COVERAGE ANALYSIS:")
        coverage_data = []
        for symbol, coverage in self.results["data_coverage"].items():
            coverage_data.append([
                symbol,
                len(coverage["apis_with_data"]),
                len(coverage["apis_without_data"]),
                coverage["best_api"] or "None",
                coverage["total_data_points"],
                ", ".join(coverage["apis_with_data"])
            ])
        
        print(tabulate(coverage_data,
                      headers=["Token", "APIs w/ Data", "APIs w/o Data", "Best API", "Total Data Points", "Available APIs"],
                      tablefmt="grid"))
        
        # Summary Insights
        summary = self.results["comparison_summary"]
        print(f"\n🏅 KEY INSIGHTS (AFTER FIXES):")
        print(f"• Best Overall API: {summary['best_overall_api']}")
        print(f"• Fastest API: {summary['fastest_api']}")
        print(f"• Most Comprehensive API: {summary['most_comprehensive_api']}")
        print(f"• Most Reliable API: {summary['most_reliable_api']}")
        
        # Recommendations
        print(f"\n💡 UPDATED RECOMMENDATIONS:")
        if summary['fastest_api'] != "None":
            print(f"• For real-time trading: Use {summary['fastest_api']} (fastest response)")
            print(f"• For comprehensive analysis: Use {summary['most_comprehensive_api']} (most data)")
            print(f"• For reliability: Use {summary['most_reliable_api']} (highest success rate)")
            print(f"• For balanced approach: Use {summary['best_overall_api']} (best overall)")
        else:
            print("• All APIs failed - check configuration and method implementations")
    
    def save_results(self):
        """Save test results to file"""
        timestamp = int(time.time())
        filename = f"scripts/results/fixed_api_comparison_test_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.logger.info(f"💾 FIXED results saved to {filename}")
        
        # Also save a summary report
        summary_filename = f"scripts/results/fixed_api_comparison_summary_{timestamp}.txt"
        with open(summary_filename, 'w') as f:
            f.write("FIXED COMPREHENSIVE API COMPARISON TEST SUMMARY\n")
            f.write("="*55 + "\n\n")
            f.write(f"Test Date: {self.results['test_start_time']}\n")
            f.write(f"Tokens Tested: {len(self.test_tokens)}\n")
            f.write(f"APIs Tested: {len(self.apis)}\n\n")
            
            f.write("FIXES APPLIED:\n")
            f.write("-" * 15 + "\n")
            for fix in self.results["fixes_applied"]:
                f.write(f"  • {fix}\n")
            f.write("\n")
            
            # Write performance metrics
            f.write("API PERFORMANCE METRICS:\n")
            f.write("-" * 30 + "\n")
            for api_name, metrics in self.results["performance_metrics"].items():
                f.write(f"{api_name}:\n")
                f.write(f"  Success Rate: {metrics['success_rate']:.1f}%\n")
                f.write(f"  Avg Response Time: {metrics['avg_response_time']:.1f}ms\n")
                f.write(f"  Avg Data Points: {metrics['avg_data_points']:.1f}\n")
                f.write(f"  Methods Used: {', '.join(metrics['methods_used'])}\n\n")
            
            # Write recommendations
            summary = self.results["comparison_summary"]
            f.write("UPDATED RECOMMENDATIONS:\n")
            f.write("-" * 25 + "\n")
            f.write(f"Best Overall API: {summary['best_overall_api']}\n")
            f.write(f"Fastest API: {summary['fastest_api']}\n")
            f.write(f"Most Comprehensive API: {summary['most_comprehensive_api']}\n")
            f.write(f"Most Reliable API: {summary['most_reliable_api']}\n")
        
        self.logger.info(f"📋 FIXED summary saved to {summary_filename}")

async def main():
    """Main function to run the FIXED comprehensive API comparison test"""
    try:
        tester = FixedAPIComparison()
        await tester.run_comprehensive_test()
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())