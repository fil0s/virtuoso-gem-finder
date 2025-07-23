#!/usr/bin/env python3
"""
Test and analyze underutilized endpoints from RugCheck and DexScreener APIs.

This script explores additional data sources that could enhance our token analysis process.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

class UnderutilizedEndpointTester:
    """Test underutilized API endpoints for enhanced data extraction"""
    
    def __init__(self):
        self.rugcheck_base = "https://api.rugcheck.xyz/v1"
        self.dexscreener_base = "https://api.dexscreener.com"
        self.results = {}
        
    async def test_rugcheck_endpoints(self) -> Dict[str, Any]:
        """Test RugCheck endpoints that we don't fully utilize"""
        print("\n🛡️ Testing RugCheck Underutilized Endpoints...")
        
        endpoints_to_test = {
            "trending_tokens": "/stats/trending",
            "detailed_token_report": "/tokens/{token_address}/report"
        }
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Test trending tokens
            try:
                url = f"{self.rugcheck_base}{endpoints_to_test['trending_tokens']}"
                async with session.get(url) as response:
                    if response.status == 200:
                        trending_data = await response.json()
                        results["trending_tokens"] = {
                            "status": "success",
                            "count": len(trending_data),
                            "sample_data": trending_data[:3] if trending_data else [],
                            "data_structure": self._analyze_structure(trending_data[0] if trending_data else {})
                        }
                        
                        # Test detailed report with first trending token
                        if trending_data:
                            first_token = trending_data[0]["mint"]
                            report_url = f"{self.rugcheck_base}/tokens/{first_token}/report"
                            
                            async with session.get(report_url) as report_response:
                                if report_response.status == 200:
                                    report_data = await report_response.json()
                                    results["detailed_token_report"] = {
                                        "status": "success",
                                        "token_tested": first_token,
                                        "available_sections": list(report_data.keys()),
                                        "risk_analysis": {
                                            "risks_count": len(report_data.get("risks", [])),
                                            "sample_risks": report_data.get("risks", [])[:2]
                                        },
                                        "holder_analysis": {
                                            "top_holders_count": len(report_data.get("topHolders", [])),
                                            "sample_holder": report_data.get("topHolders", [{}])[0] if report_data.get("topHolders") else {}
                                        },
                                        "token_metadata": {
                                            "creator": report_data.get("creator"),
                                            "supply": report_data.get("token", {}).get("supply"),
                                            "decimals": report_data.get("token", {}).get("decimals")
                                        }
                                    }
                                else:
                                    results["detailed_token_report"] = {"status": "failed", "code": report_response.status}
                    else:
                        results["trending_tokens"] = {"status": "failed", "code": response.status}
                        
            except Exception as e:
                results["trending_tokens"] = {"status": "error", "error": str(e)}
                
        return results
    
    async def test_dexscreener_endpoints(self) -> Dict[str, Any]:
        """Test DexScreener endpoints that we don't fully utilize"""
        print("\n📊 Testing DexScreener Underutilized Endpoints...")
        
        endpoints_to_test = {
            "token_profiles": "/token-profiles/latest/v1",
            "token_boosts_latest": "/token-boosts/latest/v1", 
            "token_boosts_top": "/token-boosts/top/v1",
            "search_narratives": "/latest/dex/search?q={query}",
            "batch_token_data": "/tokens/v1/{chain}/{addresses}",
            "marketing_orders": "/orders/v1/{chain}/{token_address}"
        }
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Test token profiles
            try:
                url = f"{self.dexscreener_base}{endpoints_to_test['token_profiles']}"
                async with session.get(url) as response:
                    if response.status == 200:
                        profiles_data = await response.json()
                        results["token_profiles"] = {
                            "status": "success",
                            "count": len(profiles_data),
                            "sample_profile": profiles_data[0] if profiles_data else {},
                            "social_links_available": bool(profiles_data[0].get("links") if profiles_data else False),
                            "metadata_richness": {
                                "has_description": bool(profiles_data[0].get("description") if profiles_data else False),
                                "has_images": bool(profiles_data[0].get("icon") and profiles_data[0].get("header") if profiles_data else False),
                                "has_social_links": len(profiles_data[0].get("links", []) if profiles_data else [])
                            }
                        }
                        
                        # Test marketing orders for first token
                        if profiles_data:
                            first_token = profiles_data[0]
                            chain_id = first_token["chainId"]
                            token_address = first_token["tokenAddress"]
                            orders_url = f"{self.dexscreener_base}/orders/v1/{chain_id}/{token_address}"
                            
                            async with session.get(orders_url) as orders_response:
                                if orders_response.status == 200:
                                    orders_data = await orders_response.json()
                                    results["marketing_orders"] = {
                                        "status": "success",
                                        "token_tested": token_address,
                                        "orders_count": len(orders_data),
                                        "sample_order": orders_data[0] if orders_data else {},
                                        "marketing_investment_tracking": {
                                            "payment_timestamps": [order.get("paymentTimestamp") for order in orders_data],
                                            "order_types": list(set([order.get("type") for order in orders_data])),
                                            "order_statuses": list(set([order.get("status") for order in orders_data]))
                                        }
                                    }
                                else:
                                    results["marketing_orders"] = {"status": "failed", "code": orders_response.status}
                    else:
                        results["token_profiles"] = {"status": "failed", "code": response.status}
                        
            except Exception as e:
                results["token_profiles"] = {"status": "error", "error": str(e)}
            
            # Test token boosts
            for boost_type in ["latest", "top"]:
                try:
                    url = f"{self.dexscreener_base}/token-boosts/{boost_type}/v1"
                    async with session.get(url) as response:
                        if response.status == 200:
                            boosts_data = await response.json()
                            results[f"token_boosts_{boost_type}"] = {
                                "status": "success",
                                "count": len(boosts_data),
                                "sample_boost": boosts_data[0] if boosts_data else {},
                                "promotion_tracking": {
                                    "total_amounts": [boost.get("totalAmount", 0) for boost in boosts_data[:5]],
                                    "avg_promotion_amount": sum([boost.get("totalAmount", 0) for boost in boosts_data[:10]]) / min(10, len(boosts_data)) if boosts_data else 0,
                                    "has_descriptions": sum([1 for boost in boosts_data if boost.get("description")]) if boosts_data else 0
                                }
                            }
                        else:
                            results[f"token_boosts_{boost_type}"] = {"status": "failed", "code": response.status}
                except Exception as e:
                    results[f"token_boosts_{boost_type}"] = {"status": "error", "error": str(e)}
            
            # Test narrative search
            test_narratives = ["AI", "agent", "pump", "meme", "gaming"]
            narrative_results = {}
            
            for narrative in test_narratives:
                try:
                    url = f"{self.dexscreener_base}/latest/dex/search?q={narrative}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            search_data = await response.json()
                            pairs = search_data.get("pairs", [])
                            narrative_results[narrative] = {
                                "results_count": len(pairs),
                                "sample_result": pairs[0] if pairs else {},
                                "chain_distribution": self._analyze_chain_distribution(pairs),
                                "volume_range": self._analyze_volume_range(pairs)
                            }
                        else:
                            narrative_results[narrative] = {"status": "failed", "code": response.status}
                except Exception as e:
                    narrative_results[narrative] = {"status": "error", "error": str(e)}
                    
                # Rate limiting
                await asyncio.sleep(0.2)
            
            results["narrative_search"] = narrative_results
            
            # Test batch token data
            try:
                # Use some tokens from profiles for batch testing
                if "token_profiles" in results and results["token_profiles"]["status"] == "success":
                    sample_profiles = await self._get_sample_profiles(session)
                    if sample_profiles:
                        # Group by chain for batch requests
                        chains = {}
                        for profile in sample_profiles[:6]:  # Limit to 6 tokens
                            chain = profile["chainId"]
                            if chain not in chains:
                                chains[chain] = []
                            chains[chain].append(profile["tokenAddress"])
                        
                        batch_results = {}
                        for chain, addresses in chains.items():
                            if len(addresses) > 0:
                                batch_url = f"{self.dexscreener_base}/tokens/v1/{chain}/{','.join(addresses[:3])}"  # Max 3 per batch
                                async with session.get(batch_url) as response:
                                    if response.status == 200:
                                        batch_data = await response.json()
                                        batch_results[chain] = {
                                            "status": "success",
                                            "tokens_requested": len(addresses[:3]),
                                            "tokens_returned": len(batch_data),
                                            "sample_token_data": batch_data[0] if batch_data else {},
                                            "data_richness": self._analyze_token_data_richness(batch_data[0] if batch_data else {})
                                        }
                                    else:
                                        batch_results[chain] = {"status": "failed", "code": response.status}
                                        
                                await asyncio.sleep(0.3)  # Rate limiting
                        
                        results["batch_token_data"] = batch_results
            except Exception as e:
                results["batch_token_data"] = {"status": "error", "error": str(e)}
                
        return results
    
    async def _get_sample_profiles(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Get sample token profiles for testing"""
        try:
            url = f"{self.dexscreener_base}/token-profiles/latest/v1"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        except:
            pass
        return []
    
    def _analyze_structure(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Analyze the structure of API response data"""
        structure = {}
        for key, value in data.items():
            if isinstance(value, dict):
                structure[key] = "object"
            elif isinstance(value, list):
                structure[key] = f"array[{len(value)}]"
            elif isinstance(value, str):
                structure[key] = "string"
            elif isinstance(value, (int, float)):
                structure[key] = "number"
            elif isinstance(value, bool):
                structure[key] = "boolean"
            else:
                structure[key] = "unknown"
        return structure
    
    def _analyze_chain_distribution(self, pairs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of chains in search results"""
        chains = {}
        for pair in pairs:
            chain = pair.get("chainId", "unknown")
            chains[chain] = chains.get(chain, 0) + 1
        return chains
    
    def _analyze_volume_range(self, pairs: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze volume ranges in search results"""
        volumes = []
        for pair in pairs:
            vol_24h = pair.get("volume", {}).get("h24", 0)
            if vol_24h and vol_24h > 0:
                volumes.append(vol_24h)
        
        if volumes:
            return {
                "min": min(volumes),
                "max": max(volumes),
                "avg": sum(volumes) / len(volumes),
                "count": len(volumes)
            }
        return {"min": 0, "max": 0, "avg": 0, "count": 0}
    
    def _analyze_token_data_richness(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze richness of token data from batch endpoint"""
        return {
            "has_price_data": bool(token_data.get("priceUsd")),
            "has_volume_data": bool(token_data.get("volume")),
            "has_transaction_data": bool(token_data.get("txns")),
            "has_market_cap": bool(token_data.get("marketCap")),
            "has_social_info": bool(token_data.get("info", {}).get("socials")),
            "has_price_changes": bool(token_data.get("priceChange")),
            "pair_created_timestamp": token_data.get("pairCreatedAt"),
            "available_timeframes": list(token_data.get("volume", {}).keys()) if token_data.get("volume") else []
        }
    
    async def generate_enhancement_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations for enhancing our analysis process"""
        print("\n💡 Generating Enhancement Recommendations...")
        
        rugcheck_results = await self.test_rugcheck_endpoints()
        dexscreener_results = await self.test_dexscreener_endpoints()
        
        recommendations = {
            "high_priority_enhancements": [],
            "medium_priority_enhancements": [],
            "data_quality_improvements": [],
            "new_analysis_capabilities": []
        }
        
        # Analyze RugCheck opportunities
        if rugcheck_results.get("detailed_token_report", {}).get("status") == "success":
            recommendations["high_priority_enhancements"].append({
                "source": "RugCheck",
                "enhancement": "Detailed Risk Analysis Integration",
                "description": "Extract granular risk scores, holder concentration analysis, and creator history",
                "value": "Enhanced security filtering and risk scoring",
                "implementation": "Add detailed report analysis to token evaluation pipeline"
            })
        
        # Analyze DexScreener opportunities
        if dexscreener_results.get("marketing_orders", {}).get("status") == "success":
            recommendations["high_priority_enhancements"].append({
                "source": "DexScreener",
                "enhancement": "Marketing Investment Tracking",
                "description": "Track promotional spending and marketing timeline for tokens",
                "value": "Identify heavily promoted tokens and marketing patterns",
                "implementation": "Add marketing order analysis to token discovery strategies"
            })
        
        if dexscreener_results.get("token_boosts_top", {}).get("status") == "success":
            recommendations["medium_priority_enhancements"].append({
                "source": "DexScreener", 
                "enhancement": "Promotion Level Analysis",
                "description": "Analyze promotion amounts and boost patterns",
                "value": "Identify tokens with significant promotional backing",
                "implementation": "Integrate boost data into token scoring algorithms"
            })
        
        if dexscreener_results.get("narrative_search", {}).get("AI", {}).get("results_count", 0) > 0:
            recommendations["new_analysis_capabilities"].append({
                "source": "DexScreener",
                "enhancement": "Narrative-Based Discovery",
                "description": "Discover tokens based on trending narratives (AI, gaming, etc.)",
                "value": "Early detection of narrative-driven token movements",
                "implementation": "Add narrative search to discovery strategies"
            })
        
        # Data quality improvements
        if dexscreener_results.get("batch_token_data"):
            recommendations["data_quality_improvements"].append({
                "enhancement": "Batch Data Optimization",
                "description": "Use batch endpoints to reduce API calls and get richer data",
                "value": "Improved efficiency and more comprehensive token data",
                "implementation": "Replace individual token calls with batch requests where possible"
            })
        
        return {
            "test_results": {
                "rugcheck": rugcheck_results,
                "dexscreener": dexscreener_results
            },
            "recommendations": recommendations,
            "summary": {
                "total_working_endpoints": self._count_working_endpoints(rugcheck_results, dexscreener_results),
                "enhancement_opportunities": len(recommendations["high_priority_enhancements"]) + len(recommendations["medium_priority_enhancements"]),
                "new_capabilities": len(recommendations["new_analysis_capabilities"])
            }
        }
    
    def _count_working_endpoints(self, rugcheck_results: Dict[str, Any], dexscreener_results: Dict[str, Any]) -> int:
        """Count successfully tested endpoints"""
        count = 0
        for result in rugcheck_results.values():
            if isinstance(result, dict) and result.get("status") == "success":
                count += 1
        for result in dexscreener_results.values():
            if isinstance(result, dict) and result.get("status") == "success":
                count += 1
            elif isinstance(result, dict) and any(v.get("status") == "success" for v in result.values() if isinstance(v, dict)):
                count += 1
        return count
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of underutilized endpoints"""
        print("🚀 Testing Underutilized API Endpoints for Enhanced Analysis")
        print("=" * 60)
        
        start_time = time.time()
        
        # Generate recommendations
        analysis_results = await self.generate_enhancement_recommendations()
        
        # Save results
        timestamp = int(time.time())
        filename = f"scripts/results/underutilized_endpoints_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        # Print summary
        print(f"\n📊 Analysis Complete!")
        print(f"⏱️  Duration: {time.time() - start_time:.2f} seconds")
        print(f"✅ Working Endpoints: {analysis_results['summary']['total_working_endpoints']}")
        print(f"🎯 Enhancement Opportunities: {analysis_results['summary']['enhancement_opportunities']}")
        print(f"🆕 New Capabilities: {analysis_results['summary']['new_capabilities']}")
        print(f"💾 Results saved to: {filename}")
        
        # Print key recommendations
        print("\n🔥 Top Enhancement Opportunities:")
        for i, rec in enumerate(analysis_results["recommendations"]["high_priority_enhancements"][:3], 1):
            print(f"{i}. {rec['enhancement']} ({rec['source']})")
            print(f"   → {rec['description']}")
            print(f"   💰 Value: {rec['value']}")
            print()

if __name__ == "__main__":
    tester = UnderutilizedEndpointTester()
    asyncio.run(tester.run_comprehensive_test())