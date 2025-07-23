#!/usr/bin/env python3
"""
Debug Rate-Limited Connector
Investigate why the rate-limited connector is getting different results
"""

import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConnectorDebugger:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_different_endpoints(self, token_address: str):
        """Test different Jupiter endpoints to see which one works"""
        
        endpoints = [
            "https://quote-api.jup.ag/v6/quote",  # Original endpoint (what worked)
            "https://lite-api.jup.ag/v6/quote",   # Free tier endpoint (what we're using now)
            "https://api.jup.ag/v6/quote"         # Paid tier endpoint
        ]
        
        params = {
            "inputMint": token_address,
            "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "amount": "1000000",
            "slippageBps": "50"
        }
        
        logger.info(f"🔍 Testing different endpoints for {token_address[:8]}...")
        
        results = {}
        
        for endpoint in endpoints:
            logger.info(f"   Testing: {endpoint}")
            
            try:
                async with self.session.get(endpoint, params=params) as response:
                    result = {
                        "endpoint": endpoint,
                        "status_code": response.status,
                        "success": response.status == 200,
                        "response_text": await response.text()
                    }
                    
                    if response.status == 200:
                        try:
                            data = json.loads(result["response_text"])
                            result["has_data"] = True
                            result["out_amount"] = data.get("outAmount")
                            result["price_impact"] = data.get("priceImpactPct")
                            logger.info(f"   ✅ Success: outAmount={data.get('outAmount')}")
                        except:
                            result["has_data"] = False
                            logger.info(f"   ✅ Success but invalid JSON")
                    else:
                        result["has_data"] = False
                        logger.warning(f"   ❌ Failed: {response.status} - {result['response_text'][:100]}")
                    
                    results[endpoint] = result
                    
            except Exception as e:
                logger.error(f"   ❌ Error: {e}")
                results[endpoint] = {
                    "endpoint": endpoint,
                    "success": False,
                    "error": str(e)
                }
            
            # Add delay between tests
            await asyncio.sleep(2)
        
        return results

    async def test_token_in_lists(self, token_address: str):
        """Check if token is in different Jupiter token lists"""
        
        token_lists = [
            "https://token.jup.ag/all",          # Main token list
            "https://token.jup.ag/strict",       # Strict list
            "https://cache.jup.ag/tokens"        # Cache endpoint
        ]
        
        logger.info(f"🔍 Checking token lists for {token_address[:8]}...")
        
        results = {}
        
        for list_url in token_lists:
            logger.info(f"   Checking: {list_url}")
            
            try:
                async with self.session.get(list_url) as response:
                    if response.status == 200:
                        tokens_data = await response.json()
                        
                        # Search for our token
                        found = False
                        token_info = None
                        
                        if isinstance(tokens_data, list):
                            for token in tokens_data:
                                if token.get("address") == token_address:
                                    found = True
                                    token_info = token
                                    break
                        elif isinstance(tokens_data, dict) and "tokens" in tokens_data:
                            for token in tokens_data["tokens"]:
                                if token.get("address") == token_address:
                                    found = True
                                    token_info = token
                                    break
                        
                        results[list_url] = {
                            "success": True,
                            "found": found,
                            "token_info": token_info,
                            "total_tokens": len(tokens_data) if isinstance(tokens_data, list) else len(tokens_data.get("tokens", []))
                        }
                        
                        if found:
                            logger.info(f"   ✅ Found: {token_info.get('symbol', 'Unknown')}")
                        else:
                            logger.info(f"   ❌ Not found in {len(tokens_data) if isinstance(tokens_data, list) else len(tokens_data.get('tokens', []))} tokens")
                    
                    else:
                        error_text = await response.text()
                        results[list_url] = {
                            "success": False,
                            "status_code": response.status,
                            "error": error_text[:200]
                        }
                        logger.warning(f"   ❌ Failed: {response.status}")
                        
            except Exception as e:
                logger.error(f"   ❌ Error: {e}")
                results[list_url] = {
                    "success": False,
                    "error": str(e)
                }
            
            # Add delay between tests
            await asyncio.sleep(1)
        
        return results

    async def comprehensive_debug(self, token_name: str, token_address: str):
        """Run comprehensive debugging for a token"""
        
        logger.info(f"\n🔍 Comprehensive Debug for {token_name} ({token_address})")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Test endpoints
        endpoint_results = await self.test_different_endpoints(token_address)
        
        # Test token lists
        token_list_results = await self.test_token_in_lists(token_address)
        
        duration = time.time() - start_time
        
        debug_results = {
            "token_name": token_name,
            "token_address": token_address,
            "debug_timestamp": datetime.now().isoformat(),
            "debug_duration_seconds": round(duration, 2),
            "endpoint_tests": endpoint_results,
            "token_list_tests": token_list_results,
            "summary": self._generate_debug_summary(endpoint_results, token_list_results)
        }
        
        return debug_results

    def _generate_debug_summary(self, endpoint_results: dict, token_list_results: dict) -> dict:
        """Generate debug summary"""
        
        working_endpoints = [ep for ep, result in endpoint_results.items() if result.get("success", False)]
        token_found_in = [list_url for list_url, result in token_list_results.items() if result.get("found", False)]
        
        return {
            "working_endpoints": working_endpoints,
            "failed_endpoints": [ep for ep in endpoint_results.keys() if ep not in working_endpoints],
            "token_found_in_lists": len(token_found_in),
            "token_lists_checked": len(token_list_results),
            "main_issue": self._identify_main_issue(endpoint_results, token_list_results)
        }

    def _identify_main_issue(self, endpoint_results: dict, token_list_results: dict) -> str:
        """Identify the main issue causing failures"""
        
        # Check if any endpoint works
        any_endpoint_works = any(result.get("success", False) for result in endpoint_results.values())
        
        # Check if token is found in any list
        token_found = any(result.get("found", False) for result in token_list_results.values())
        
        if not token_found:
            return "Token not found in any Jupiter token lists"
        elif not any_endpoint_works:
            return "All quote endpoints failing"
        elif endpoint_results.get("https://quote-api.jup.ag/v6/quote", {}).get("success", False) and not endpoint_results.get("https://lite-api.jup.ag/v6/quote", {}).get("success", False):
            return "Original endpoint works but lite-api endpoint fails"
        else:
            return "Unknown issue"

async def main():
    """Main debug function"""
    
    test_tokens = [
        ("$michi", "5mbK36SZ7J19An8jFochhQS4of8g6BwUjbeCSxBSoWdp"),
        ("BILLY", "3B5wuUrMEi5yATD7on46hKfej3pfmd7t1RKgrsN3pump"),
        ("USELESS", "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk")
    ]
    
    async with ConnectorDebugger() as debugger:
        logger.info("🚀 Starting Rate-Limited Connector Debug")
        logger.info("=" * 80)
        
        all_results = {}
        
        for token_name, token_address in test_tokens:
            try:
                debug_results = await debugger.comprehensive_debug(token_name, token_address)
                all_results[token_name] = debug_results
                
                # Print summary
                summary = debug_results["summary"]
                logger.info(f"\n📋 Debug Summary for {token_name}:")
                logger.info(f"   Working endpoints: {len(summary['working_endpoints'])}/3")
                logger.info(f"   Found in token lists: {summary['token_found_in_lists']}/{summary['token_lists_checked']}")
                logger.info(f"   Main issue: {summary['main_issue']}")
                
            except Exception as e:
                logger.error(f"❌ Error debugging {token_name}: {e}")
                all_results[token_name] = {"error": str(e)}
        
        # Save results
        results_file = f"scripts/tests/rate_limited_debug_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "debug_results": all_results,
                "debug_timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"\n💾 Debug results saved to: {results_file}")
        
        # Print final conclusions
        logger.info(f"\n🎯 CONCLUSIONS:")
        for token_name, results in all_results.items():
            if "error" not in results:
                summary = results["summary"]
                logger.info(f"   {token_name}: {summary['main_issue']}")

if __name__ == "__main__":
    asyncio.run(main()) 