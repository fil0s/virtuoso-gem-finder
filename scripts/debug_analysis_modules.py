#!/usr/bin/env python3
"""
Analysis Module Debugging Script

Tests the specific analysis modules (holder analysis, volatility analysis) 
that are failing in the strategy comparison to identify exact parsing issues.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from core.config_manager import ConfigManager
from utils.logger_setup import LoggerSetup
from services.holder_distribution_analyzer import HolderDistributionAnalyzer
from services.price_volatility_analyzer import PriceVolatilityAnalyzer

class AnalysisModuleDebugger:
    """Debug specific analysis modules to find parsing issues"""
    
    def __init__(self):
        logger_setup = LoggerSetup(__name__)
        self.logger = logger_setup.logger
        self.config_manager = ConfigManager()
        
        # Initialize API infrastructure
        self.cache_manager = CacheManager(ttl_default=300)
        self.rate_limiter = RateLimiterService()
        
        birdeye_config = self.config_manager.get_section('BIRDEYE_API')
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
        
        # Initialize analysis modules
        self.holder_analyzer = HolderDistributionAnalyzer(
            birdeye_api=self.birdeye_api,
            logger=self.logger
        )
        
        self.volatility_analyzer = PriceVolatilityAnalyzer(
            birdeye_api=self.birdeye_api,
            logger=self.logger
        )
        
        # Test tokens from the failed analysis
        self.test_tokens = [
            "9civd7ktdbBtSUgkyduxQoHhBLtThf9xr1Kvj5dcpump",
            "rCDpCrYepyYffZz7AQhBV1LMJvWo7mps8fWr4Bvpump",
            "4jXJcKQoojvFuA7MSzJLpgDvXyiACqLnMyh6ULEEnVhg",
        ]
        
        self.debug_results = {
            "test_timestamp": datetime.now().isoformat(),
            "holder_analysis_debug": {},
            "volatility_analysis_debug": {},
            "raw_api_data_samples": {},
            "parsing_issues_found": [],
            "recommended_fixes": []
        }
    
    async def run_analysis_debugging(self) -> Dict[str, Any]:
        """Run comprehensive analysis module debugging"""
        self.logger.info("🔧 Starting Analysis Module Debugging")
        self.logger.info("=" * 60)
        
        try:
            await self._examine_raw_api_data()
            await self._debug_holder_analysis()
            await self._debug_volatility_analysis()
            self._identify_parsing_issues()
            self._generate_fix_recommendations()
            await self._save_debug_report()
            
            return self.debug_results
            
        except Exception as e:
            self.logger.error(f"❌ Analysis debugging failed: {e}")
            self.debug_results["critical_error"] = str(e)
            return self.debug_results
        finally:
            await self.birdeye_api.close()
    
    async def _examine_raw_api_data(self):
        """Examine raw API data structure"""
        self.logger.info("🔍 Examining Raw API Data Structure...")
        
        raw_data_samples = {}
        
        for token_address in self.test_tokens[:1]:
            self.logger.info(f"  📊 Testing token {token_address[:8]}...")
            
            token_samples = {}
            
            try:
                # Test holder data structure
                holder_data = await self.birdeye_api.get_token_holders(token_address, limit=10)
                if holder_data:
                    token_samples["holder_data"] = {
                        "type": str(type(holder_data)),
                        "keys": list(holder_data.keys()) if isinstance(holder_data, dict) else "not_dict",
                        "items_type": str(type(holder_data.get("items", "no_items"))) if isinstance(holder_data, dict) else "no_items",
                        "items_count": len(holder_data.get("items", [])) if isinstance(holder_data, dict) and holder_data.get("items") else 0,
                        "sample_item": holder_data.get("items", [{}])[0] if isinstance(holder_data, dict) and holder_data.get("items") else "no_sample",
                        "total_field": holder_data.get("total", "no_total") if isinstance(holder_data, dict) else "no_total"
                    }
                else:
                    token_samples["holder_data"] = {"error": "no_data_returned"}
                
                # Test transaction data structure
                transaction_data = await self.birdeye_api.get_token_transactions(token_address, limit=5)
                if transaction_data:
                    token_samples["transaction_data"] = {
                        "type": str(type(transaction_data)),
                        "count": len(transaction_data) if isinstance(transaction_data, list) else "not_list",
                        "sample_transaction": transaction_data[0] if isinstance(transaction_data, list) and transaction_data else "no_sample",
                        "price_fields_found": self._find_price_fields_in_transaction(transaction_data[0]) if isinstance(transaction_data, list) and transaction_data else "no_transaction"
                    }
                else:
                    token_samples["transaction_data"] = {"error": "no_data_returned"}
                
                raw_data_samples[token_address] = token_samples
                
            except Exception as e:
                raw_data_samples[token_address] = {"error": str(e)}
            
            await asyncio.sleep(1)
        
        self.debug_results["raw_api_data_samples"] = raw_data_samples
        self.logger.info(f"  ✅ Raw API data structure examined")
    
    def _find_price_fields_in_transaction(self, transaction: Dict) -> Dict[str, Any]:
        """Find all possible price fields in a transaction"""
        price_fields = {}
        
        # Check direct price fields
        for field in ['price', 'priceInUsd', 'tokenPrice', 'usdAmount']:
            if field in transaction:
                price_fields[field] = transaction[field]
        
        # Check nested price fields
        for side in ['from', 'to']:
            if side in transaction and isinstance(transaction[side], dict):
                for field in ['price', 'priceInUsd', 'tokenPrice', 'usdAmount']:
                    if field in transaction[side]:
                        price_fields[f"{side}.{field}"] = transaction[side][field]
        
        return price_fields
    
    async def _debug_holder_analysis(self):
        """Debug the holder analysis module step by step"""
        self.logger.info("👥 Debugging Holder Analysis Module...")
        
        holder_debug = {}
        
        for token_address in self.test_tokens:
            self.logger.info(f"  🔍 Testing holder analysis for {token_address[:8]}...")
            
            token_debug = {
                "token_address": token_address,
                "raw_api_success": False,
                "analysis_success": False,
                "errors": [],
                "data_flow": {}
            }
            
            try:
                # Test raw API call
                raw_holder_data = await self.birdeye_api.get_token_holders(token_address, limit=100)
                if raw_holder_data:
                    token_debug["raw_api_success"] = True
                    token_debug["data_flow"]["raw_data_structure"] = {
                        "type": str(type(raw_holder_data)),
                        "keys": list(raw_holder_data.keys()) if isinstance(raw_holder_data, dict) else "not_dict",
                        "items_count": len(raw_holder_data.get("items", [])) if isinstance(raw_holder_data, dict) else 0
                    }
                else:
                    token_debug["errors"].append("Raw API returned None")
                
                # Test analysis module
                analysis_result = await self.holder_analyzer.analyze_holder_distribution(token_address, limit=100)
                if analysis_result:
                    token_debug["analysis_success"] = True
                    token_debug["data_flow"]["analysis_result"] = {
                        "validation_passed": analysis_result.get("validation_passed", False),
                        "total_holders": analysis_result.get("total_holders", 0),
                        "risk_level": analysis_result.get("risk_assessment", {}).get("risk_level", "unknown"),
                        "errors_in_analysis": [k for k, v in analysis_result.items() if "error" in str(k).lower()]
                    }
                else:
                    token_debug["errors"].append("Analysis module returned None")
                
            except Exception as e:
                token_debug["errors"].append(f"Exception in holder analysis: {str(e)}")
                self.logger.error(f"    ❌ Holder analysis failed for {token_address[:8]}: {e}")
            
            holder_debug[token_address] = token_debug
            await asyncio.sleep(1)
        
        self.debug_results["holder_analysis_debug"] = holder_debug
        
        successful_raw = sum(1 for t in holder_debug.values() if t["raw_api_success"])
        successful_analysis = sum(1 for t in holder_debug.values() if t["analysis_success"])
        
        self.logger.info(f"  📊 Holder Analysis Summary:")
        self.logger.info(f"    Raw API Success: {successful_raw}/{len(self.test_tokens)}")
        self.logger.info(f"    Analysis Success: {successful_analysis}/{len(self.test_tokens)}")
    
    async def _debug_volatility_analysis(self):
        """Debug the volatility analysis module step by step"""
        self.logger.info("📈 Debugging Volatility Analysis Module...")
        
        volatility_debug = {}
        
        for token_address in self.test_tokens:
            self.logger.info(f"  🔍 Testing volatility analysis for {token_address[:8]}...")
            
            token_debug = {
                "token_address": token_address,
                "raw_api_success": False,
                "analysis_success": False,
                "errors": [],
                "data_flow": {}
            }
            
            try:
                # Test raw transaction API call
                raw_transactions = await self.birdeye_api.get_token_transactions(token_address, limit=50, max_pages=2)
                if raw_transactions:
                    token_debug["raw_api_success"] = True
                    
                    # Test price extraction manually
                    extracted_prices = []
                    for tx in raw_transactions[:10]:
                        price_fields = self._find_price_fields_in_transaction(tx)
                        if price_fields:
                            for field, value in price_fields.items():
                                if isinstance(value, (int, float)) and value > 0:
                                    extracted_prices.append(value)
                                    break
                    
                    token_debug["data_flow"]["raw_transaction_data"] = {
                        "total_transactions": len(raw_transactions),
                        "sample_price_fields": self._find_price_fields_in_transaction(raw_transactions[0]) if raw_transactions else {},
                        "manual_price_extraction": {
                            "prices_found": len(extracted_prices),
                            "sample_prices": extracted_prices[:5]
                        }
                    }
                else:
                    token_debug["errors"].append("Raw transaction API returned None")
                
                # Test analysis module
                analysis_result = await self.volatility_analyzer.analyze_price_volatility(token_address)
                if analysis_result:
                    token_debug["analysis_success"] = True
                    token_debug["data_flow"]["analysis_result"] = {
                        "price_data_available": analysis_result.get("price_data_available", False),
                        "price_points_analyzed": analysis_result.get("price_points_analyzed", 0),
                        "volatility_classification": analysis_result.get("volatility_metrics", {}).get("volatility_classification", "unknown"),
                        "errors_in_analysis": analysis_result.get("errors", [])
                    }
                else:
                    token_debug["errors"].append("Volatility analysis module returned None")
                
            except Exception as e:
                token_debug["errors"].append(f"Exception in volatility analysis: {str(e)}")
                self.logger.error(f"    ❌ Volatility analysis failed for {token_address[:8]}: {e}")
            
            volatility_debug[token_address] = token_debug
            await asyncio.sleep(1)
        
        self.debug_results["volatility_analysis_debug"] = volatility_debug
        
        successful_raw = sum(1 for t in volatility_debug.values() if t["raw_api_success"])
        successful_analysis = sum(1 for t in volatility_debug.values() if t["analysis_success"])
        
        self.logger.info(f"  📊 Volatility Analysis Summary:")
        self.logger.info(f"    Raw API Success: {successful_raw}/{len(self.test_tokens)}")
        self.logger.info(f"    Analysis Success: {successful_analysis}/{len(self.test_tokens)}")
    
    def _identify_parsing_issues(self):
        """Identify specific parsing issues from the debug data"""
        self.logger.info("🔍 Identifying Parsing Issues...")
        
        issues_found = []
        
        # Check holder analysis issues
        holder_debug = self.debug_results.get("holder_analysis_debug", {})
        for token, debug_data in holder_debug.items():
            if debug_data.get("raw_api_success") and not debug_data.get("analysis_success"):
                issues_found.append({
                    "module": "holder_analysis",
                    "token": token,
                    "issue": "Raw API works but analysis fails",
                    "details": debug_data.get("errors", [])
                })
        
        # Check volatility analysis issues
        volatility_debug = self.debug_results.get("volatility_analysis_debug", {})
        for token, debug_data in volatility_debug.items():
            if debug_data.get("raw_api_success") and not debug_data.get("analysis_success"):
                issues_found.append({
                    "module": "volatility_analysis",
                    "token": token,
                    "issue": "Raw API works but analysis fails",
                    "details": debug_data.get("errors", [])
                })
        
        self.debug_results["parsing_issues_found"] = issues_found
        self.logger.info(f"  🔍 Found {len(issues_found)} parsing issues")
    
    def _generate_fix_recommendations(self):
        """Generate specific fix recommendations"""
        self.logger.info("💡 Generating Fix Recommendations...")
        
        recommendations = []
        
        issues = self.debug_results.get("parsing_issues_found", [])
        
        holder_issues = [i for i in issues if i["module"] == "holder_analysis"]
        volatility_issues = [i for i in issues if i["module"] == "volatility_analysis"]
        
        if holder_issues:
            recommendations.append({
                "module": "holder_analysis",
                "priority": "HIGH",
                "issue_count": len(holder_issues),
                "recommendation": "Fix holder data parsing in HolderDistributionAnalyzer",
                "specific_fixes": [
                    "Check if analysis code expects 'data.items' instead of 'items'",
                    "Verify balance field parsing (balance vs ui_amount)",
                    "Add error handling for missing fields"
                ]
            })
        
        if volatility_issues:
            recommendations.append({
                "module": "volatility_analysis", 
                "priority": "HIGH",
                "issue_count": len(volatility_issues),
                "recommendation": "Fix price extraction in PriceVolatilityAnalyzer",
                "specific_fixes": [
                    "Update _extract_transaction_price() to handle current API response format",
                    "Add fallback price field extraction",
                    "Fix timeframe filtering in _fetch_price_data()"
                ]
            })
        
        self.debug_results["recommended_fixes"] = recommendations
        self.logger.info(f"  💡 Generated {len(recommendations)} fix recommendations")
    
    async def _save_debug_report(self):
        """Save debug report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_module_debug_{timestamp}.json"
        filepath = f"scripts/results/{filename}"
        
        os.makedirs("scripts/results", exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.debug_results, f, indent=2)
        
        self.logger.info(f"📄 Debug report saved to: {filepath}")
        self._print_debug_summary()
    
    def _print_debug_summary(self):
        """Print debug summary"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("🔧 ANALYSIS MODULE DEBUG SUMMARY")
        self.logger.info("=" * 60)
        
        # Issues found
        issues = self.debug_results.get("parsing_issues_found", [])
        self.logger.info(f"🔍 Issues Found: {len(issues)}")
        
        for issue in issues:
            self.logger.info(f"  ❌ {issue['module']}: {issue['issue']}")
        
        # Recommendations
        recommendations = self.debug_results.get("recommended_fixes", [])
        self.logger.info(f"💡 Fix Recommendations: {len(recommendations)}")
        
        for rec in recommendations:
            self.logger.info(f"  🛠️  {rec['module']}: {rec['recommendation']}")
        
        self.logger.info("=" * 60)

async def main():
    """Main debugging execution"""
    debugger = AnalysisModuleDebugger()
    
    try:
        results = await debugger.run_analysis_debugging()
        
        issues_count = len(results.get("parsing_issues_found", []))
        
        if issues_count > 0:
            print(f"\n🔍 ISSUES FOUND: {issues_count}")
            print("Review the debug report for specific fixes needed.")
            return 1
        else:
            print("\n✅ No parsing issues detected.")
            return 0
            
    except Exception as e:
        print(f"\n❌ Debug failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 