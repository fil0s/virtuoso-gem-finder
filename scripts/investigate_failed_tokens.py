#!/usr/bin/env python3
"""
Failed Token Investigation Script
Comprehensive analysis of $michi, BILLY, and INF tokens that failed in Jupiter testing
"""

import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FailedTokenInvestigator:
    def __init__(self):
        self.session = None
        self.results = {}
        
        # Failed tokens from the test
        self.failed_tokens = {
            "$michi": "5mbK36SZ7J19An8jFochhQS4of8g6BwUjbeCSxBSoWdp",
            "BILLY": "3B5wuUrMEi5yATD7on46hKfej3pfmd7t1RKgrsN3pump", 
            "INF": "5oVNBeEEQvYi1cX3ir8Dx5n1P7pdxydbGF2X4TxVusJm"
        }
        
        # API endpoints to test
        self.endpoints = {
            "jupiter_quote": "https://quote-api.jup.ag/v6/quote",
            "jupiter_tokens": "https://token.jup.ag/all",
            "dexscreener": "https://api.dexscreener.com/latest/dex/tokens/",
            "rugcheck": "https://api.rugcheck.xyz/v1/tokens/",
            "birdeye": "https://public-api.birdeye.so/defi/token_overview"
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_jupiter_quote_detailed(self, token_address: str) -> Dict[str, Any]:
        """Test Jupiter quote API with detailed error analysis"""
        logger.info(f"🔍 Testing Jupiter Quote API for {token_address[:8]}...")
        
        results = {
            "token_in_jupiter_list": False,
            "quote_attempts": [],
            "error_analysis": {},
            "token_metadata": None
        }
        
        # First check if token is in Jupiter's token list
        try:
            async with self.session.get(self.endpoints["jupiter_tokens"]) as response:
                if response.status == 200:
                    tokens_data = await response.json()
                    for token in tokens_data:
                        if token.get("address") == token_address:
                            results["token_in_jupiter_list"] = True
                            results["token_metadata"] = token
                            logger.info(f"✅ Token found in Jupiter list: {token.get('symbol', 'Unknown')}")
                            break
                    
                    if not results["token_in_jupiter_list"]:
                        logger.warning(f"❌ Token {token_address[:8]} NOT found in Jupiter token list")
        except Exception as e:
            logger.error(f"❌ Error checking Jupiter token list: {e}")
            results["error_analysis"]["token_list_error"] = str(e)

        # Test different quote scenarios
        quote_scenarios = [
            {"inputMint": token_address, "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "amount": "1000000"},  # to USDC
            {"inputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "outputMint": token_address, "amount": "1000000"},  # from USDC
            {"inputMint": token_address, "outputMint": "So11111111111111111111111111111111111111112", "amount": "1000000"},  # to SOL
            {"inputMint": "So11111111111111111111111111111111111111112", "outputMint": token_address, "amount": "1000000"},  # from SOL
        ]
        
        for i, params in enumerate(quote_scenarios):
            try:
                await asyncio.sleep(0.5)  # Rate limiting
                async with self.session.get(self.endpoints["jupiter_quote"], params=params) as response:
                    scenario_result = {
                        "scenario": f"Scenario {i+1}",
                        "params": params,
                        "status_code": response.status,
                        "success": False,
                        "response_data": None,
                        "error": None
                    }
                    
                    if response.status == 200:
                        data = await response.json()
                        scenario_result["success"] = True
                        scenario_result["response_data"] = data
                        logger.info(f"✅ Quote scenario {i+1} successful")
                    else:
                        error_text = await response.text()
                        scenario_result["error"] = error_text
                        logger.warning(f"❌ Quote scenario {i+1} failed: {response.status} - {error_text}")
                    
                    results["quote_attempts"].append(scenario_result)
                    
            except Exception as e:
                logger.error(f"❌ Error in quote scenario {i+1}: {e}")
                results["quote_attempts"].append({
                    "scenario": f"Scenario {i+1}",
                    "params": params,
                    "success": False,
                    "error": str(e)
                })
        
        return results

    async def test_dexscreener_api(self, token_address: str) -> Dict[str, Any]:
        """Test DexScreener API for token data"""
        logger.info(f"🔍 Testing DexScreener API for {token_address[:8]}...")
        
        try:
            url = f"{self.endpoints['dexscreener']}{token_address}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ DexScreener data found: {len(data.get('pairs', []))} pairs")
                    return {
                        "success": True,
                        "status_code": response.status,
                        "data": data,
                        "pairs_count": len(data.get('pairs', [])),
                        "has_financial_data": bool(data.get('pairs'))
                    }
                else:
                    error_text = await response.text()
                    logger.warning(f"❌ DexScreener failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": error_text
                    }
        except Exception as e:
            logger.error(f"❌ DexScreener API error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_rugcheck_api(self, token_address: str) -> Dict[str, Any]:
        """Test RugCheck API for token validation"""
        logger.info(f"🔍 Testing RugCheck API for {token_address[:8]}...")
        
        try:
            url = f"{self.endpoints['rugcheck']}{token_address}/report"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ RugCheck data found")
                    return {
                        "success": True,
                        "status_code": response.status,
                        "data": data,
                        "has_validation": True
                    }
                else:
                    error_text = await response.text()
                    logger.warning(f"❌ RugCheck failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": error_text
                    }
        except Exception as e:
            logger.error(f"❌ RugCheck API error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_birdeye_api(self, token_address: str) -> Dict[str, Any]:
        """Test BirdEye API for token data"""
        logger.info(f"🔍 Testing BirdEye API for {token_address[:8]}...")
        
        try:
            params = {
                "address": token_address,
                "x-chain": "solana"
            }
            async with self.session.get(self.endpoints['birdeye'], params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ BirdEye data found")
                    return {
                        "success": True,
                        "status_code": response.status,
                        "data": data,
                        "has_financial_data": bool(data.get('data'))
                    }
                else:
                    error_text = await response.text()
                    logger.warning(f"❌ BirdEye failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": error_text
                    }
        except Exception as e:
            logger.error(f"❌ BirdEye API error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def comprehensive_token_analysis(self, token_name: str, token_address: str) -> Dict[str, Any]:
        """Run comprehensive analysis on a single token"""
        logger.info(f"\n🔍 Starting comprehensive analysis for {token_name} ({token_address[:8]}...)")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Run all API tests
        jupiter_results = await self.test_jupiter_quote_detailed(token_address)
        dexscreener_results = await self.test_dexscreener_api(token_address)
        rugcheck_results = await self.test_rugcheck_api(token_address)
        birdeye_results = await self.test_birdeye_api(token_address)
        
        analysis_duration = time.time() - start_time
        
        # Compile comprehensive results
        comprehensive_results = {
            "token_name": token_name,
            "token_address": token_address,
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_duration_seconds": round(analysis_duration, 2),
            "jupiter_analysis": jupiter_results,
            "dexscreener_analysis": dexscreener_results,
            "rugcheck_analysis": rugcheck_results,
            "birdeye_analysis": birdeye_results,
            "summary": self._generate_token_summary(jupiter_results, dexscreener_results, rugcheck_results, birdeye_results)
        }
        
        logger.info(f"📊 Analysis complete for {token_name} in {analysis_duration:.2f}s")
        return comprehensive_results

    def _generate_token_summary(self, jupiter: Dict, dexscreener: Dict, rugcheck: Dict, birdeye: Dict) -> Dict[str, Any]:
        """Generate summary analysis of token across all platforms"""
        return {
            "data_availability": {
                "jupiter_token_list": jupiter.get("token_in_jupiter_list", False),
                "jupiter_quotable": any(attempt.get("success", False) for attempt in jupiter.get("quote_attempts", [])),
                "dexscreener_available": dexscreener.get("success", False),
                "rugcheck_available": rugcheck.get("success", False),
                "birdeye_available": birdeye.get("success", False)
            },
            "platform_count": sum([
                dexscreener.get("success", False),
                rugcheck.get("success", False),
                birdeye.get("success", False),
                jupiter.get("token_in_jupiter_list", False)
            ]),
            "has_financial_data": any([
                dexscreener.get("has_financial_data", False),
                birdeye.get("has_financial_data", False)
            ]),
            "potential_issues": self._identify_potential_issues(jupiter, dexscreener, rugcheck, birdeye)
        }

    def _identify_potential_issues(self, jupiter: Dict, dexscreener: Dict, rugcheck: Dict, birdeye: Dict) -> List[str]:
        """Identify potential issues with the token"""
        issues = []
        
        if not jupiter.get("token_in_jupiter_list", False):
            issues.append("Not in Jupiter's official token list")
        
        if not any(attempt.get("success", False) for attempt in jupiter.get("quote_attempts", [])):
            issues.append("No successful Jupiter quotes (no liquidity/routing)")
        
        if not dexscreener.get("success", False):
            issues.append("No DexScreener data (not trading on major DEXs)")
        
        if not rugcheck.get("success", False):
            issues.append("No RugCheck validation data")
        
        if not birdeye.get("success", False):
            issues.append("No BirdEye market data")
        
        return issues

    async def run_investigation(self):
        """Run comprehensive investigation of all failed tokens"""
        logger.info("🚀 Starting Failed Token Investigation")
        logger.info("=" * 80)
        logger.info(f"Investigating {len(self.failed_tokens)} failed tokens:")
        for name, address in self.failed_tokens.items():
            logger.info(f"  - {name}: {address}")
        logger.info("=" * 80)
        
        investigation_start = time.time()
        
        # Analyze each token
        for token_name, token_address in self.failed_tokens.items():
            try:
                token_results = await self.comprehensive_token_analysis(token_name, token_address)
                self.results[token_name] = token_results
                
                # Brief summary for each token
                summary = token_results["summary"]
                logger.info(f"\n📋 Summary for {token_name}:")
                logger.info(f"   Platforms with data: {summary['platform_count']}/4")
                logger.info(f"   Has financial data: {summary['has_financial_data']}")
                logger.info(f"   Jupiter quotable: {summary['data_availability']['jupiter_quotable']}")
                if summary['potential_issues']:
                    logger.info(f"   Issues: {', '.join(summary['potential_issues'])}")
                
            except Exception as e:
                logger.error(f"❌ Error analyzing {token_name}: {e}")
                self.results[token_name] = {
                    "error": str(e),
                    "token_address": token_address
                }
        
        total_duration = time.time() - investigation_start
        
        # Save results
        results_file = f"scripts/tests/failed_token_investigation_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "investigation_results": self.results,
                "investigation_summary": self._generate_investigation_summary(),
                "investigation_timestamp": datetime.now().isoformat(),
                "total_duration_seconds": round(total_duration, 2)
            }, f, indent=2)
        
        logger.info(f"\n📊 Investigation Complete!")
        logger.info(f"Duration: {total_duration:.2f} seconds")
        logger.info(f"Results saved to: {results_file}")
        
        # Print final summary
        self._print_final_summary()

    def _generate_investigation_summary(self) -> Dict[str, Any]:
        """Generate overall investigation summary"""
        summary = {
            "tokens_analyzed": len(self.results),
            "successful_analyses": 0,
            "failed_analyses": 0,
            "platform_availability": {
                "jupiter": 0,
                "dexscreener": 0,
                "rugcheck": 0,
                "birdeye": 0
            },
            "common_issues": []
        }
        
        all_issues = []
        for token_name, results in self.results.items():
            if "error" not in results:
                summary["successful_analyses"] += 1
                token_summary = results.get("summary", {})
                availability = token_summary.get("data_availability", {})
                
                if availability.get("jupiter_token_list", False):
                    summary["platform_availability"]["jupiter"] += 1
                if availability.get("dexscreener_available", False):
                    summary["platform_availability"]["dexscreener"] += 1
                if availability.get("rugcheck_available", False):
                    summary["platform_availability"]["rugcheck"] += 1
                if availability.get("birdeye_available", False):
                    summary["platform_availability"]["birdeye"] += 1
                
                all_issues.extend(token_summary.get("potential_issues", []))
            else:
                summary["failed_analyses"] += 1
        
        # Find common issues
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        summary["common_issues"] = [
            {"issue": issue, "count": count}
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return summary

    def _print_final_summary(self):
        """Print comprehensive final summary"""
        logger.info("\n" + "=" * 80)
        logger.info("🎯 FINAL INVESTIGATION SUMMARY")
        logger.info("=" * 80)
        
        for token_name, results in self.results.items():
            if "error" not in results:
                summary = results["summary"]
                logger.info(f"\n🔍 {token_name} ({results['token_address'][:8]}...):")
                logger.info(f"   Platform Count: {summary['platform_count']}/4")
                logger.info(f"   Jupiter Listed: {'✅' if summary['data_availability']['jupiter_token_list'] else '❌'}")
                logger.info(f"   Jupiter Quotable: {'✅' if summary['data_availability']['jupiter_quotable'] else '❌'}")
                logger.info(f"   DexScreener: {'✅' if summary['data_availability']['dexscreener_available'] else '❌'}")
                logger.info(f"   RugCheck: {'✅' if summary['data_availability']['rugcheck_available'] else '❌'}")
                logger.info(f"   BirdEye: {'✅' if summary['data_availability']['birdeye_available'] else '❌'}")
                logger.info(f"   Has Financial Data: {'✅' if summary['has_financial_data'] else '❌'}")
                
                if summary['potential_issues']:
                    logger.info(f"   Issues:")
                    for issue in summary['potential_issues']:
                        logger.info(f"     - {issue}")
            else:
                logger.info(f"\n❌ {token_name}: Analysis failed - {results['error']}")

async def main():
    """Main investigation function"""
    async with FailedTokenInvestigator() as investigator:
        await investigator.run_investigation()

if __name__ == "__main__":
    asyncio.run(main()) 