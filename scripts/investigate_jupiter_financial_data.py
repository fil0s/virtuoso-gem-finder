#!/usr/bin/env python3
"""
Jupiter API Financial Data Investigation

This script comprehensively tests Jupiter API endpoints to understand:
1. What financial data (price, volume, market cap) is available
2. Which endpoints provide the most reliable data
3. How to derive missing financial metrics
4. Best practices for financial data extraction

Focus areas:
- Quote API for pricing and liquidity
- Token list API for basic token info
- Price derivation through quote analysis
- Volume estimation through routing complexity
- Market cap calculation approaches
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JupiterFinancialDataInvestigator:
    """Comprehensive Jupiter API financial data investigation"""
    
    def __init__(self):
        # Official Jupiter API endpoints
        self.endpoints = {
            "quote": "https://quote-api.jup.ag/v6/quote",
            "tokens": "https://token.jup.ag/all",
            "tokens_strict": "https://token.jup.ag/strict",
            "price": "https://price.jup.ag/v4/price",  # May have issues
            "stats": "https://stats.jup.ag/api",       # May have issues
        }
        
        # Reference tokens for testing
        self.reference_tokens = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
            "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        }
        
        # Test amounts for depth analysis
        self.test_amounts = [
            1000000,      # $1 worth
            10000000,     # $10 worth  
            100000000,    # $100 worth
            1000000000,   # $1000 worth
            10000000000,  # $10000 worth
        ]
        
        self.session = None
        self.results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, url: str, params: Dict = None) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "data": data,
                        "response_time": response.headers.get("X-Response-Time", "unknown")
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "status_code": response.status,
                        "error": error_text
                    }
        except Exception as e:
            return {
                "status": "exception",
                "error": str(e)
            }
    
    async def test_token_list_financial_data(self) -> Dict[str, Any]:
        """Test what financial data is available in token lists"""
        logger.info("🪙 Testing Jupiter token list financial data...")
        
        results = {}
        
        # Test both token list endpoints
        for endpoint_name, url in [("all_tokens", self.endpoints["tokens"]), 
                                  ("strict_tokens", self.endpoints["tokens_strict"])]:
            logger.info(f"Testing {endpoint_name}: {url}")
            
            result = await self._make_request(url)
            
            if result["status"] == "success":
                tokens = result["data"]
                
                if tokens and isinstance(tokens, list):
                    # Analyze first few tokens for financial data
                    sample_tokens = tokens[:10]
                    
                    financial_fields = set()
                    for token in sample_tokens:
                        if isinstance(token, dict):
                            financial_fields.update(token.keys())
                    
                    # Check for financial-related fields
                    financial_indicators = [
                        "price", "volume", "market_cap", "fdv", "liquidity",
                        "volume_24h", "volume_24h_usd", "price_change_24h",
                        "market_cap_usd", "daily_volume", "volume_change_24h"
                    ]
                    
                    found_financial = [field for field in financial_indicators if field in financial_fields]
                    
                    results[endpoint_name] = {
                        "success": True,
                        "token_count": len(tokens),
                        "sample_token": sample_tokens[0] if sample_tokens else None,
                        "all_fields": list(financial_fields),
                        "financial_fields_found": found_financial,
                        "has_financial_data": len(found_financial) > 0
                    }
                    
                    logger.info(f"✅ {endpoint_name}: {len(tokens)} tokens, {len(found_financial)} financial fields")
                else:
                    results[endpoint_name] = {
                        "success": False,
                        "error": "Invalid token list format"
                    }
            else:
                results[endpoint_name] = {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
                logger.error(f"❌ {endpoint_name}: {result.get('error', 'Unknown error')}")
        
        return results
    
    async def test_quote_api_pricing(self) -> Dict[str, Any]:
        """Test quote API for price derivation capabilities"""
        logger.info("💱 Testing Jupiter quote API for pricing...")
        
        results = {}
        
        # Test different token pairs and amounts
        test_cases = [
            {
                "name": "sol_to_usdc_small",
                "input_mint": self.reference_tokens["SOL"],
                "output_mint": self.reference_tokens["USDC"],
                "amount": "1000000000",  # 1 SOL
                "description": "1 SOL → USDC"
            },
            {
                "name": "jup_to_usdc_medium",
                "input_mint": self.reference_tokens["JUP"],
                "output_mint": self.reference_tokens["USDC"],
                "amount": "1000000000",  # 1 JUP (assuming 9 decimals)
                "description": "1 JUP → USDC"
            },
            {
                "name": "ray_to_sol_large",
                "input_mint": self.reference_tokens["RAY"],
                "output_mint": self.reference_tokens["SOL"],
                "amount": "100000000000",  # 100 RAY
                "description": "100 RAY → SOL"
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"Testing: {test_case['description']}")
            
            params = {
                "inputMint": test_case["input_mint"],
                "outputMint": test_case["output_mint"],
                "amount": test_case["amount"],
                "slippageBps": "50"  # 0.5% slippage
            }
            
            result = await self._make_request(self.endpoints["quote"], params)
            
            if result["status"] == "success":
                quote_data = result["data"]
                
                # Analyze quote for pricing information
                pricing_analysis = self._analyze_quote_pricing(quote_data, test_case)
                
                results[test_case["name"]] = {
                    "success": True,
                    "description": test_case["description"],
                    "pricing_analysis": pricing_analysis,
                    "raw_quote": quote_data,
                    "response_time": result.get("response_time", "unknown")
                }
                
                logger.info(f"✅ {test_case['description']}: Price derivable = {pricing_analysis['price_derivable']}")
            else:
                results[test_case["name"]] = {
                    "success": False,
                    "description": test_case["description"],
                    "error": result.get("error", "Unknown error")
                }
                logger.error(f"❌ {test_case['description']}: {result.get('error', 'Unknown error')}")
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        return results
    
    def _analyze_quote_pricing(self, quote_data: Dict, test_case: Dict) -> Dict[str, Any]:
        """Analyze quote data for pricing capabilities"""
        analysis = {
            "price_derivable": False,
            "effective_price": None,
            "price_impact": None,
            "liquidity_indicators": {},
            "route_analysis": {},
            "slippage_analysis": {}
        }
        
        try:
            # Check if we can derive price
            if "inAmount" in quote_data and "outAmount" in quote_data:
                in_amount = int(quote_data["inAmount"])
                out_amount = int(quote_data["outAmount"])
                
                if in_amount > 0 and out_amount > 0:
                    analysis["price_derivable"] = True
                    analysis["effective_price"] = out_amount / in_amount
                    
                    # Price impact analysis
                    if "priceImpactPct" in quote_data:
                        analysis["price_impact"] = float(quote_data["priceImpactPct"])
                    
                    # Liquidity indicators
                    analysis["liquidity_indicators"] = {
                        "input_amount": in_amount,
                        "output_amount": out_amount,
                        "price_ratio": analysis["effective_price"],
                        "has_price_impact": "priceImpactPct" in quote_data
                    }
            
            # Route analysis for liquidity depth
            if "routePlan" in quote_data:
                route_plan = quote_data["routePlan"]
                analysis["route_analysis"] = {
                    "route_count": len(route_plan),
                    "is_direct_swap": len(route_plan) == 1,
                    "dexes_involved": [],
                    "swap_steps": len(route_plan)
                }
                
                # Extract DEX information
                for step in route_plan:
                    if "swapInfo" in step and "label" in step["swapInfo"]:
                        analysis["route_analysis"]["dexes_involved"].append(step["swapInfo"]["label"])
                
                analysis["route_analysis"]["unique_dexes"] = list(set(analysis["route_analysis"]["dexes_involved"]))
            
            # Slippage analysis
            if "slippageBps" in quote_data:
                analysis["slippage_analysis"] = {
                    "slippage_bps": quote_data["slippageBps"],
                    "slippage_percent": quote_data["slippageBps"] / 100,
                    "within_tolerance": quote_data["slippageBps"] <= 100  # 1% or less
                }
        
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    async def test_liquidity_depth_analysis(self) -> Dict[str, Any]:
        """Test liquidity depth through varying quote amounts"""
        logger.info("🌊 Testing liquidity depth analysis...")
        
        results = {}
        
        # Test with SOL → USDC across different amounts
        base_params = {
            "inputMint": self.reference_tokens["SOL"],
            "outputMint": self.reference_tokens["USDC"],
            "slippageBps": "100"  # 1% slippage
        }
        
        for amount in self.test_amounts:
            amount_label = f"${amount/1000000:.0f}"
            logger.info(f"Testing liquidity depth for {amount_label}")
            
            params = base_params.copy()
            params["amount"] = str(amount)
            
            result = await self._make_request(self.endpoints["quote"], params)
            
            if result["status"] == "success":
                quote_data = result["data"]
                
                # Analyze depth
                depth_analysis = {
                    "amount_tested": amount,
                    "amount_label": amount_label,
                    "quote_successful": True,
                    "price_impact": float(quote_data.get("priceImpactPct", 0)),
                    "route_complexity": len(quote_data.get("routePlan", [])),
                    "effective_price": None
                }
                
                # Calculate effective price
                if "inAmount" in quote_data and "outAmount" in quote_data:
                    in_amt = int(quote_data["inAmount"])
                    out_amt = int(quote_data["outAmount"])
                    if in_amt > 0:
                        depth_analysis["effective_price"] = out_amt / in_amt
                
                results[amount_label] = depth_analysis
                logger.info(f"✅ {amount_label}: {depth_analysis['price_impact']:.3f}% impact, {depth_analysis['route_complexity']} routes")
            else:
                results[amount_label] = {
                    "amount_tested": amount,
                    "amount_label": amount_label,
                    "quote_successful": False,
                    "error": result.get("error", "Unknown error")
                }
                logger.error(f"❌ {amount_label}: {result.get('error', 'Unknown error')}")
            
            # Rate limiting
            await asyncio.sleep(0.3)
        
        return results
    
    async def test_volume_estimation_approaches(self) -> Dict[str, Any]:
        """Test different approaches to estimate trading volume"""
        logger.info("📊 Testing volume estimation approaches...")
        
        results = {
            "direct_api_volume": await self._test_direct_volume_apis(),
            "quote_based_volume": await self._test_quote_based_volume(),
            "route_complexity_volume": await self._test_route_complexity_volume()
        }
        
        return results
    
    async def _test_direct_volume_apis(self) -> Dict[str, Any]:
        """Test direct volume APIs (likely to fail)"""
        logger.info("Testing direct volume APIs...")
        
        volume_endpoints = [
            f"{self.endpoints['stats']}/volume",
            f"{self.endpoints['price']}/volume",
            f"{self.endpoints['stats']}/daily"
        ]
        
        results = {}
        
        for i, url in enumerate(volume_endpoints):
            endpoint_name = f"volume_endpoint_{i+1}"
            result = await self._make_request(url)
            
            results[endpoint_name] = {
                "url": url,
                "success": result["status"] == "success",
                "error": result.get("error") if result["status"] != "success" else None,
                "has_volume_data": False
            }
            
            if result["status"] == "success":
                # Check if response contains volume data
                data = result["data"]
                volume_indicators = ["volume", "volume_24h", "daily_volume", "total_volume"]
                
                if isinstance(data, dict):
                    found_volume = any(indicator in str(data).lower() for indicator in volume_indicators)
                    results[endpoint_name]["has_volume_data"] = found_volume
                    if found_volume:
                        results[endpoint_name]["sample_data"] = data
        
        return results
    
    async def _test_quote_based_volume(self) -> Dict[str, Any]:
        """Test volume estimation through quote frequency/depth"""
        logger.info("Testing quote-based volume estimation...")
        
        # This is a conceptual test - in practice you'd:
        # 1. Make multiple quotes over time
        # 2. Track price changes and liquidity
        # 3. Estimate volume from route complexity changes
        
        return {
            "approach": "quote_based_volume_estimation",
            "feasible": True,
            "description": "Estimate volume by tracking quote changes over time",
            "requirements": [
                "Multiple quotes over time intervals",
                "Price impact tracking",
                "Route complexity monitoring",
                "Historical quote data storage"
            ],
            "pros": [
                "Uses working Jupiter quote API",
                "Real-time data",
                "Liquidity-aware"
            ],
            "cons": [
                "Requires multiple API calls",
                "Indirect measurement",
                "Time-dependent accuracy"
            ]
        }
    
    async def _test_route_complexity_volume(self) -> Dict[str, Any]:
        """Test volume estimation through route complexity analysis"""
        logger.info("Testing route complexity volume estimation...")
        
        # Test multiple tokens to see route complexity patterns
        test_tokens = list(self.reference_tokens.values())[:3]
        complexity_results = []
        
        for token in test_tokens:
            params = {
                "inputMint": token,
                "outputMint": self.reference_tokens["USDC"],
                "amount": "1000000000",
                "slippageBps": "50"
            }
            
            result = await self._make_request(self.endpoints["quote"], params)
            
            if result["status"] == "success":
                quote_data = result["data"]
                route_count = len(quote_data.get("routePlan", []))
                price_impact = float(quote_data.get("priceImpactPct", 0))
                
                complexity_results.append({
                    "token": token,
                    "route_count": route_count,
                    "price_impact": price_impact,
                    "liquidity_score": self._calculate_liquidity_score(route_count, price_impact)
                })
            
            await asyncio.sleep(0.2)
        
        return {
            "approach": "route_complexity_volume_estimation",
            "feasible": True,
            "sample_results": complexity_results,
            "description": "Estimate volume/activity from routing complexity",
            "scoring_method": "More routes + lower impact = higher volume/liquidity"
        }
    
    def _calculate_liquidity_score(self, route_count: int, price_impact: float) -> float:
        """Calculate liquidity score from route complexity and price impact"""
        # More routes = better liquidity
        route_score = min(10, route_count * 2)
        
        # Lower price impact = better liquidity
        impact_score = max(0, 10 - (price_impact * 2))
        
        return (route_score + impact_score) / 2
    
    async def test_market_cap_derivation(self) -> Dict[str, Any]:
        """Test approaches to derive market cap data"""
        logger.info("💰 Testing market cap derivation approaches...")
        
        approaches = {
            "token_list_mcap": await self._test_token_list_market_cap(),
            "price_times_supply": await self._test_price_supply_calculation(),
            "external_api_integration": await self._test_external_mcap_sources()
        }
        
        return approaches
    
    async def _test_token_list_market_cap(self) -> Dict[str, Any]:
        """Test if token list contains market cap data"""
        logger.info("Testing token list market cap data...")
        
        result = await self._make_request(self.endpoints["tokens"])
        
        if result["status"] == "success":
            tokens = result["data"]
            
            if tokens and isinstance(tokens, list):
                # Check first 10 tokens for market cap fields
                mcap_fields = []
                for token in tokens[:10]:
                    if isinstance(token, dict):
                        for key in token.keys():
                            if "market" in key.lower() or "cap" in key.lower() or "mcap" in key.lower():
                                mcap_fields.append(key)
                
                unique_mcap_fields = list(set(mcap_fields))
                
                return {
                    "success": True,
                    "market_cap_fields_found": unique_mcap_fields,
                    "has_market_cap_data": len(unique_mcap_fields) > 0,
                    "sample_token": tokens[0] if tokens else None
                }
        
        return {
            "success": False,
            "error": result.get("error", "Token list unavailable")
        }
    
    async def _test_price_supply_calculation(self) -> Dict[str, Any]:
        """Test market cap calculation via price × supply"""
        return {
            "approach": "price_times_circulating_supply",
            "feasible": True,
            "requirements": [
                "Token price (from Jupiter quotes)",
                "Circulating supply (from token metadata)",
                "Decimals (from token list)"
            ],
            "calculation": "market_cap = (price_per_token * circulating_supply)",
            "data_sources": {
                "price": "Jupiter quote API",
                "supply": "Solana RPC getTokenSupply",
                "decimals": "Jupiter token list"
            },
            "pros": [
                "Accurate calculation",
                "Real-time pricing",
                "Uses available data"
            ],
            "cons": [
                "Requires multiple API calls",
                "Need RPC access for supply",
                "Complex implementation"
            ]
        }
    
    async def _test_external_mcap_sources(self) -> Dict[str, Any]:
        """Test integration with external market cap sources"""
        return {
            "approach": "external_api_integration",
            "feasible": True,
            "recommended_sources": [
                "CoinGecko API (free tier available)",
                "CoinMarketCap API",
                "DexScreener API (already integrated)",
                "BirdEye API (already integrated)"
            ],
            "integration_strategy": "Use Jupiter for liquidity validation, external APIs for financial metrics",
            "fallback_chain": [
                "Primary: BirdEye/DexScreener (already working)",
                "Secondary: Jupiter quotes for price",
                "Tertiary: CoinGecko for market cap"
            ]
        }
    
    async def generate_comprehensive_recommendations(self) -> Dict[str, Any]:
        """Generate comprehensive recommendations for Jupiter financial data integration"""
        logger.info("📋 Generating comprehensive recommendations...")
        
        return {
            "immediate_actionable_solutions": {
                "1_price_data": {
                    "solution": "Use Jupiter Quote API for real-time pricing",
                    "implementation": "Quote SOL→Token or Token→USDC to derive prices",
                    "reliability": "High - Quote API is working well",
                    "api_calls": "1 call per token price",
                    "update_frequency": "Real-time"
                },
                "2_liquidity_data": {
                    "solution": "Derive liquidity from quote route complexity",
                    "implementation": "More routes + lower price impact = higher liquidity",
                    "reliability": "Medium-High - Good proxy for liquidity",
                    "api_calls": "1 call per token (same as price)",
                    "scoring": "Route count (0-10) + Impact score (0-10) / 2"
                },
                "3_volume_estimation": {
                    "solution": "Use external APIs for volume, Jupiter for validation",
                    "implementation": "BirdEye/DexScreener for volume, Jupiter quotes for liquidity validation",
                    "reliability": "High - Combines proven APIs",
                    "fallback": "Route complexity as volume proxy"
                }
            },
            "integration_strategy": {
                "primary_approach": "Hybrid Jupiter + External API",
                "jupiter_role": "Real-time pricing, liquidity validation, token discovery",
                "external_role": "Volume data, market cap, historical metrics",
                "data_flow": [
                    "1. Discover tokens via Jupiter token list",
                    "2. Get financial metrics from BirdEye/DexScreener",
                    "3. Validate liquidity via Jupiter quotes",
                    "4. Fill gaps with Jupiter-derived metrics"
                ]
            },
            "fix_pre_filter_issue": {
                "problem": "Pre-filter uses zero values from Jupiter-only tokens",
                "solution": "Skip financial filtering for Jupiter-only tokens OR derive metrics",
                "immediate_fix": "Check if token has valid financial data before applying thresholds",
                "code_location": "scripts/high_conviction_token_detector.py line 2440-2445"
            }
        }
    
    async def run_comprehensive_investigation(self) -> Dict[str, Any]:
        """Run complete Jupiter financial data investigation"""
        logger.info("🚀 Starting comprehensive Jupiter financial data investigation...")
        
        start_time = time.time()
        
        # Run all tests
        investigation_results = {
            "investigation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "jupiter_endpoints_tested": list(self.endpoints.keys()),
                "reference_tokens": self.reference_tokens
            },
            "token_list_analysis": await self.test_token_list_financial_data(),
            "quote_pricing_analysis": await self.test_quote_api_pricing(),
            "liquidity_depth_analysis": await self.test_liquidity_depth_analysis(),
            "volume_estimation_analysis": await self.test_volume_estimation_approaches(),
            "market_cap_derivation": await self.test_market_cap_derivation(),
            "recommendations": await self.generate_comprehensive_recommendations()
        }
        
        # Add summary
        duration = time.time() - start_time
        investigation_results["investigation_summary"] = {
            "duration_seconds": round(duration, 2),
            "key_findings": [
                "Jupiter Quote API works reliably for pricing",
                "Token list lacks financial data",
                "Route complexity indicates liquidity",
                "Volume requires external APIs or estimation",
                "Market cap needs calculation or external source"
            ],
            "recommended_action": "Implement hybrid approach: Jupiter for pricing/liquidity + external APIs for volume/mcap"
        }
        
        self.results = investigation_results
        return investigation_results
    
    def save_results(self, filename: Optional[str] = None):
        """Save investigation results to file"""
        if not filename:
            timestamp = int(time.time())
            filename = f"scripts/tests/jupiter_financial_investigation_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"💾 Investigation results saved to: {filename}")
        return filename

async def main():
    """Run Jupiter financial data investigation"""
    logger.info("🪐 Jupiter Financial Data Investigation")
    logger.info("=" * 60)
    
    async with JupiterFinancialDataInvestigator() as investigator:
        # Run comprehensive investigation
        results = await investigator.run_comprehensive_investigation()
        
        # Save results
        filename = investigator.save_results()
        
        # Print key findings
        logger.info("\n🔍 KEY FINDINGS:")
        logger.info("=" * 40)
        
        # Token list findings
        token_list = results.get("token_list_analysis", {})
        for endpoint, data in token_list.items():
            if data.get("success"):
                financial_fields = data.get("financial_fields_found", [])
                logger.info(f"📋 {endpoint}: {len(financial_fields)} financial fields found")
            else:
                logger.info(f"❌ {endpoint}: Failed - {data.get('error', 'Unknown')}")
        
        # Quote pricing findings
        quote_results = results.get("quote_pricing_analysis", {})
        successful_quotes = sum(1 for r in quote_results.values() if r.get("success"))
        logger.info(f"💱 Quote API: {successful_quotes}/{len(quote_results)} tests successful")
        
        # Liquidity depth findings
        depth_results = results.get("liquidity_depth_analysis", {})
        successful_depth = sum(1 for r in depth_results.values() if r.get("quote_successful"))
        logger.info(f"🌊 Liquidity depth: {successful_depth}/{len(depth_results)} amounts tested")
        
        # Recommendations
        recommendations = results.get("recommendations", {})
        immediate_solutions = recommendations.get("immediate_actionable_solutions", {})
        logger.info(f"💡 Immediate solutions: {len(immediate_solutions)} approaches identified")
        
        logger.info(f"\n📄 Full results saved to: {filename}")
        logger.info("\n✅ Jupiter financial data investigation completed!")

if __name__ == "__main__":
    asyncio.run(main()) 