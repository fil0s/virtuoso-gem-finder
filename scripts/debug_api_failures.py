#!/usr/bin/env python3
"""
API Failure Diagnostic Script

Systematically investigates the API call failures and data analysis issues
identified in the enhanced_deep_analysis_strategy_comparison results.

Key Issues to Investigate:
1. API Call Failures (Recent Listings Strategy: 50% failure rate)
2. Holder Analysis Failures ("No holder items found")
3. Volatility Analysis Failures ("Insufficient price data points")
4. Strategy Execution Failures (Price Momentum, Liquidity Growth)
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from core.config_manager import ConfigManager
from utils.logger_setup import LoggerSetup

class APIFailureDiagnostic:
    """Comprehensive diagnostic tool for API failures and data analysis issues"""
    
    def __init__(self):
        logger_setup = LoggerSetup(__name__)
        self.logger = logger_setup.logger
        self.config_manager = ConfigManager()
        
        # Initialize core services
        self.cache_manager = CacheManager(ttl_default=300)
        self.rate_limiter = RateLimiterService()
        
        # Initialize BirdEye API
        birdeye_config = self.config_manager.get_section('BIRDEYE_API')
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
        
        # Test tokens for diagnostics
        self.test_tokens = [
            "9civd7ktdbBtSUgkyduxQoHhBLtThf9xr1Kvj5dcpump",
            "rCDpCrYepyYffZz7AQhBV1LMJvWo7mps8fWr4Bvpump",
            "4jXJcKQoojvFuA7MSzJLpgDvXyiACqLnMyh6ULEEnVhg",
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        ]
        
        self.diagnostic_results = {
            "test_timestamp": datetime.now().isoformat(),
            "api_connectivity": {},
            "endpoint_diagnostics": {},
            "holder_analysis_issues": {},
            "volatility_analysis_issues": {},
            "strategy_execution_issues": {},
            "recommendations": []
        }
    
    async def run_comprehensive_diagnostic(self) -> Dict[str, Any]:
        """Run complete diagnostic suite"""
        self.logger.info("🔍 Starting Comprehensive API Failure Diagnostic")
        self.logger.info("=" * 60)
        
        try:
            await self._test_api_connectivity()
            await self._diagnose_endpoint_failures()
            await self._investigate_holder_analysis_failures()
            await self._investigate_volatility_analysis_failures()
            await self._test_strategy_execution()
            self._generate_recommendations()
            await self._save_diagnostic_report()
            
            return self.diagnostic_results
            
        except Exception as e:
            self.logger.error(f"❌ Diagnostic failed: {e}")
            self.diagnostic_results["critical_error"] = str(e)
            return self.diagnostic_results
        finally:
            await self.birdeye_api.close()
    
    async def _test_api_connectivity(self):
        """Test basic API connectivity and authentication"""
        self.logger.info("🌐 Testing API Connectivity...")
        
        connectivity_results = {
            "api_key_configured": bool(self.birdeye_api.api_key),
            "base_url": self.birdeye_api.base_url,
            "endpoints_tested": {},
            "authentication_status": "unknown"
        }
        
        test_token = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
        
        try:
            overview = await self.birdeye_api.get_token_overview(test_token)
            if overview:
                connectivity_results["authentication_status"] = "success"
                connectivity_results["endpoints_tested"]["token_overview"] = "success"
                self.logger.info("✅ API connectivity confirmed")
            else:
                connectivity_results["authentication_status"] = "failed"
                connectivity_results["endpoints_tested"]["token_overview"] = "failed"
                self.logger.warning("⚠️ API connectivity issues detected")
        except Exception as e:
            connectivity_results["authentication_status"] = "error"
            connectivity_results["endpoints_tested"]["token_overview"] = f"error: {str(e)}"
            self.logger.error(f"❌ API connectivity failed: {e}")
        
        self.diagnostic_results["api_connectivity"] = connectivity_results
    
    async def _diagnose_endpoint_failures(self):
        """Diagnose specific endpoint failures"""
        self.logger.info("🔍 Diagnosing Endpoint Failures...")
        
        endpoint_results = {}
        
        endpoints_to_test = [
            ("get_token_overview", self.birdeye_api.get_token_overview),
            ("get_token_holders", lambda addr: self.birdeye_api.get_token_holders(addr, limit=50)),
            ("get_token_transactions", lambda addr: self.birdeye_api.get_token_transactions(addr, limit=20)),
            ("get_token_creation_info", self.birdeye_api.get_token_creation_info),
            ("get_token_security", self.birdeye_api.get_token_security),
        ]
        
        for endpoint_name, endpoint_func in endpoints_to_test:
            self.logger.info(f"  Testing {endpoint_name}...")
            endpoint_results[endpoint_name] = {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0,
                "error_details": [],
                "success_rate": 0.0
            }
            
            for token_address in self.test_tokens:
                try:
                    result = await endpoint_func(token_address)
                    endpoint_results[endpoint_name]["total_tests"] += 1
                    
                    if result is not None:
                        endpoint_results[endpoint_name]["successful_tests"] += 1
                        self.logger.debug(f"    ✅ {endpoint_name} success for {token_address[:8]}")
                    else:
                        endpoint_results[endpoint_name]["failed_tests"] += 1
                        endpoint_results[endpoint_name]["error_details"].append(
                            f"{token_address[:8]}: returned None"
                        )
                        
                except Exception as e:
                    endpoint_results[endpoint_name]["total_tests"] += 1
                    endpoint_results[endpoint_name]["failed_tests"] += 1
                    endpoint_results[endpoint_name]["error_details"].append(
                        f"{token_address[:8]}: {str(e)}"
                    )
                
                await asyncio.sleep(0.5)
            
            total = endpoint_results[endpoint_name]["total_tests"]
            successful = endpoint_results[endpoint_name]["successful_tests"]
            endpoint_results[endpoint_name]["success_rate"] = (successful / total * 100) if total > 0 else 0
            
            self.logger.info(f"    {endpoint_name}: {successful}/{total} success ({endpoint_results[endpoint_name]['success_rate']:.1f}%)")
        
        self.diagnostic_results["endpoint_diagnostics"] = endpoint_results
    
    async def _investigate_holder_analysis_failures(self):
        """Investigate holder analysis failures"""
        self.logger.info("👥 Investigating Holder Analysis Failures...")
        
        holder_issues = {
            "tokens_tested": [],
            "common_failure_patterns": []
        }
        
        for token_address in self.test_tokens:
            self.logger.info(f"  Analyzing holder data for {token_address[:8]}...")
            
            token_result = {
                "token_address": token_address,
                "holder_endpoint_result": None,
                "data_structure": "unknown",
                "items_found": 0,
                "total_holders": 0,
                "failure_reason": None
            }
            
            try:
                holder_data = await self.birdeye_api.get_token_holders(token_address, limit=100)
                token_result["holder_endpoint_result"] = "success" if holder_data else "null_response"
                
                if holder_data:
                    if isinstance(holder_data, dict):
                        token_result["data_structure"] = "dict"
                        
                        if "items" in holder_data:
                            items = holder_data["items"]
                            token_result["items_found"] = len(items) if isinstance(items, list) else 0
                            token_result["total_holders"] = holder_data.get("total", 0)
                            
                            if not items:
                                token_result["failure_reason"] = "empty_items_list"
                            elif not isinstance(items, list):
                                token_result["failure_reason"] = f"items_not_list_{type(items)}"
                        else:
                            token_result["failure_reason"] = "no_items_key"
                            token_result["available_keys"] = list(holder_data.keys())
                    else:
                        token_result["data_structure"] = f"unexpected_{type(holder_data)}"
                        token_result["failure_reason"] = "unexpected_data_type"
                else:
                    token_result["failure_reason"] = "null_response_from_api"
                
            except Exception as e:
                token_result["holder_endpoint_result"] = "exception"
                token_result["failure_reason"] = f"exception: {str(e)}"
            
            holder_issues["tokens_tested"].append(token_result)
            await asyncio.sleep(0.5)
        
        failure_reasons = [t["failure_reason"] for t in holder_issues["tokens_tested"] if t["failure_reason"]]
        holder_issues["common_failure_patterns"] = list(set(failure_reasons))
        
        total_tested = len(holder_issues["tokens_tested"])
        successful_holder_fetches = len([t for t in holder_issues["tokens_tested"] if t["items_found"] > 0])
        holder_issues["success_rate"] = (successful_holder_fetches / total_tested * 100) if total_tested > 0 else 0
        
        self.logger.info(f"    Holder Analysis Success Rate: {successful_holder_fetches}/{total_tested} ({holder_issues['success_rate']:.1f}%)")
        
        self.diagnostic_results["holder_analysis_issues"] = holder_issues
    
    async def _investigate_volatility_analysis_failures(self):
        """Investigate volatility analysis failures"""
        self.logger.info("📈 Investigating Volatility Analysis Failures...")
        
        volatility_issues = {
            "tokens_tested": []
        }
        
        for token_address in self.test_tokens:
            self.logger.info(f"  Analyzing price data for {token_address[:8]}...")
            
            token_result = {
                "token_address": token_address,
                "price_sources": {},
                "total_price_points": 0,
                "usable_price_points": 0,
                "failure_reason": None
            }
            
            try:
                # Test transactions source
                try:
                    transactions = await self.birdeye_api.get_token_transactions(token_address, limit=50, max_pages=2)
                    if transactions:
                        prices_from_txs = self._extract_prices_from_transactions(transactions)
                        token_result["price_sources"]["transactions"] = {
                            "total_transactions": len(transactions),
                            "price_points_extracted": len(prices_from_txs)
                        }
                        token_result["total_price_points"] += len(prices_from_txs)
                        token_result["usable_price_points"] += len([p for p in prices_from_txs if p > 0])
                    else:
                        token_result["price_sources"]["transactions"] = {"error": "no_transactions"}
                except Exception as e:
                    token_result["price_sources"]["transactions"] = {"error": str(e)}
                
                # Test OHLCV source
                try:
                    ohlcv_data = await self.birdeye_api.get_ohlcv_data(token_address, time_frame="1h", limit=24)
                    if ohlcv_data:
                        prices_from_ohlcv = [float(candle.get('c', 0)) for candle in ohlcv_data if candle.get('c')]
                        token_result["price_sources"]["ohlcv"] = {
                            "candles_available": len(ohlcv_data),
                            "price_points_extracted": len(prices_from_ohlcv)
                        }
                        token_result["total_price_points"] += len(prices_from_ohlcv)
                        token_result["usable_price_points"] += len([p for p in prices_from_ohlcv if p > 0])
                    else:
                        token_result["price_sources"]["ohlcv"] = {"error": "no_ohlcv_data"}
                except Exception as e:
                    token_result["price_sources"]["ohlcv"] = {"error": str(e)}
                
                # Determine failure reason
                if token_result["usable_price_points"] < 5:
                    token_result["failure_reason"] = f"insufficient_data_points_{token_result['usable_price_points']}_of_5_required"
                elif token_result["total_price_points"] == 0:
                    token_result["failure_reason"] = "no_price_data_from_any_source"
                else:
                    token_result["failure_reason"] = None
                
            except Exception as e:
                token_result["failure_reason"] = f"analysis_exception: {str(e)}"
            
            volatility_issues["tokens_tested"].append(token_result)
            await asyncio.sleep(0.5)
        
        total_tested = len(volatility_issues["tokens_tested"])
        successful_volatility = len([t for t in volatility_issues["tokens_tested"] if t["failure_reason"] is None])
        volatility_issues["success_rate"] = (successful_volatility / total_tested * 100) if total_tested > 0 else 0
        
        self.logger.info(f"    Volatility Analysis Success Rate: {successful_volatility}/{total_tested} ({volatility_issues['success_rate']:.1f}%)")
        
        self.diagnostic_results["volatility_analysis_issues"] = volatility_issues
    
    def _extract_prices_from_transactions(self, transactions: List[Dict]) -> List[float]:
        """Extract price data from transaction list"""
        prices = []
        
        for tx in transactions:
            try:
                if 'price' in tx and tx['price'] > 0:
                    prices.append(float(tx['price']))
                    continue
                
                if 'tokenPrice' in tx and tx['tokenPrice'] > 0:
                    prices.append(float(tx['tokenPrice']))
                    continue
                
                if 'from' in tx and isinstance(tx['from'], dict):
                    from_price = tx['from'].get('price', 0) or tx['from'].get('priceInUsd', 0)
                    if from_price > 0:
                        prices.append(float(from_price))
                        continue
                
                if 'to' in tx and isinstance(tx['to'], dict):
                    to_price = tx['to'].get('price', 0) or tx['to'].get('priceInUsd', 0)
                    if to_price > 0:
                        prices.append(float(to_price))
                        continue
                        
            except (ValueError, TypeError):
                continue
        
        return prices
    
    async def _test_strategy_execution(self):
        """Test strategy execution paths"""
        self.logger.info("🎯 Testing Strategy Execution Paths...")
        
        strategy_results = {
            "token_list_endpoint": {}
        }
        
        try:
            self.logger.info("  Testing token list endpoint...")
            
            token_list_params = [
                {"sort_by": "volume_24h_usd", "limit": 10, "min_liquidity": 100000},
                {"sort_by": "trade_24h_count", "limit": 10, "min_volume_24h_usd": 50000}
            ]
            
            for i, params in enumerate(token_list_params):
                try:
                    result = await self.birdeye_api.get_token_list(**params)
                    if result and result.get("success") and result.get("data", {}).get("tokens"):
                        tokens = result["data"]["tokens"]
                        strategy_results["token_list_endpoint"][f"test_{i+1}"] = {
                            "success": True,
                            "tokens_returned": len(tokens),
                            "params": params
                        }
                        self.logger.info(f"    ✅ Token list test {i+1}: {len(tokens)} tokens returned")
                    else:
                        strategy_results["token_list_endpoint"][f"test_{i+1}"] = {
                            "success": False,
                            "error": "no_tokens_returned",
                            "params": params
                        }
                        self.logger.warning(f"    ❌ Token list test {i+1}: no tokens returned")
                except Exception as e:
                    strategy_results["token_list_endpoint"][f"test_{i+1}"] = {
                        "success": False,
                        "error": str(e),
                        "params": params
                    }
                    self.logger.warning(f"    ❌ Token list test {i+1} failed: {e}")
                
                await asyncio.sleep(1)
        
        except Exception as e:
            strategy_results["token_list_endpoint"]["critical_error"] = str(e)
        
        self.diagnostic_results["strategy_execution_issues"] = strategy_results
    
    def _generate_recommendations(self):
        """Generate specific recommendations"""
        self.logger.info("💡 Generating Recommendations...")
        
        recommendations = []
        
        # API Connectivity
        connectivity = self.diagnostic_results.get("api_connectivity", {})
        if connectivity.get("authentication_status") != "success":
            recommendations.append({
                "priority": "CRITICAL",
                "category": "API_CONNECTIVITY",
                "issue": "API authentication failed",
                "recommendation": "Verify BIRDEYE_API_KEY environment variable is set correctly"
            })
        
        # Endpoint Failures
        endpoint_diag = self.diagnostic_results.get("endpoint_diagnostics", {})
        for endpoint, results in endpoint_diag.items():
            success_rate = results.get("success_rate", 0)
            if success_rate < 50:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "ENDPOINT_RELIABILITY",
                    "issue": f"{endpoint} has {success_rate:.1f}% success rate",
                    "recommendation": f"Implement retry logic and error handling for {endpoint}"
                })
        
        # Holder Analysis
        holder_issues = self.diagnostic_results.get("holder_analysis_issues", {})
        holder_success_rate = holder_issues.get("success_rate", 0)
        if holder_success_rate < 80:
            recommendations.append({
                "priority": "HIGH",
                "category": "HOLDER_ANALYSIS",
                "issue": f"Holder analysis has {holder_success_rate:.1f}% success rate",
                "recommendation": "Fix holder data parsing and add fallback data sources"
            })
        
        # Volatility Analysis
        volatility_issues = self.diagnostic_results.get("volatility_analysis_issues", {})
        volatility_success_rate = volatility_issues.get("success_rate", 0)
        if volatility_success_rate < 80:
            recommendations.append({
                "priority": "HIGH",
                "category": "VOLATILITY_ANALYSIS",
                "issue": f"Volatility analysis has {volatility_success_rate:.1f}% success rate",
                "recommendation": "Implement multiple price data sources and reduce minimum requirements"
            })
        
        self.diagnostic_results["recommendations"] = recommendations
        
        self.logger.info(f"  Generated {len(recommendations)} recommendations")
    
    async def _save_diagnostic_report(self):
        """Save diagnostic report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"api_failure_diagnostic_{timestamp}.json"
        filepath = f"scripts/results/{filename}"
        
        os.makedirs("scripts/results", exist_ok=True)
        
        api_stats = self.birdeye_api.get_api_call_statistics()
        self.diagnostic_results["api_call_statistics"] = api_stats
        
        with open(filepath, 'w') as f:
            json.dump(self.diagnostic_results, f, indent=2)
        
        self.logger.info(f"📄 Diagnostic report saved to: {filepath}")
        self._print_diagnostic_summary()
    
    def _print_diagnostic_summary(self):
        """Print diagnostic summary"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🔍 DIAGNOSTIC SUMMARY")
        self.logger.info("=" * 60)
        
        connectivity = self.diagnostic_results.get("api_connectivity", {})
        auth_status = connectivity.get("authentication_status", "unknown")
        self.logger.info(f"🌐 API Authentication: {auth_status.upper()}")
        
        self.logger.info("\n📡 Endpoint Success Rates:")
        endpoint_diag = self.diagnostic_results.get("endpoint_diagnostics", {})
        for endpoint, results in endpoint_diag.items():
            success_rate = results.get("success_rate", 0)
            status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
            self.logger.info(f"  {status} {endpoint}: {success_rate:.1f}%")
        
        self.logger.info("\n📊 Analysis Success Rates:")
        holder_rate = self.diagnostic_results.get("holder_analysis_issues", {}).get("success_rate", 0)
        volatility_rate = self.diagnostic_results.get("volatility_analysis_issues", {}).get("success_rate", 0)
        
        holder_status = "✅" if holder_rate >= 80 else "⚠️" if holder_rate >= 50 else "❌"
        volatility_status = "✅" if volatility_rate >= 80 else "⚠️" if volatility_rate >= 50 else "❌"
        
        self.logger.info(f"  {holder_status} Holder Analysis: {holder_rate:.1f}%")
        self.logger.info(f"  {volatility_status} Volatility Analysis: {volatility_rate:.1f}%")
        
        recommendations = self.diagnostic_results.get("recommendations", [])
        critical_count = len([r for r in recommendations if r.get("priority") == "CRITICAL"])
        high_count = len([r for r in recommendations if r.get("priority") == "HIGH"])
        
        self.logger.info(f"\n💡 Recommendations: {len(recommendations)} total")
        if critical_count > 0:
            self.logger.info(f"  🚨 CRITICAL: {critical_count}")
        if high_count > 0:
            self.logger.info(f"  ⚠️  HIGH: {high_count}")
        
        self.logger.info("=" * 60)

async def main():
    """Main diagnostic execution"""
    diagnostic = APIFailureDiagnostic()
    
    try:
        results = await diagnostic.run_comprehensive_diagnostic()
        
        recommendations = results.get("recommendations", [])
        critical_issues = len([r for r in recommendations if r.get("priority") == "CRITICAL"])
        
        if critical_issues > 0:
            print(f"\n🚨 CRITICAL ISSUES FOUND: {critical_issues}")
            print("Review the diagnostic report for immediate action items.")
            return 1
        else:
            print("\n✅ No critical issues detected.")
            return 0
            
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 