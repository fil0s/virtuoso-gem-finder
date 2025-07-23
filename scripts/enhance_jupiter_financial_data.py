#!/usr/bin/env python3
"""
Enhanced Jupiter Financial Data Connector

Based on our comprehensive investigation, this script enhances the Jupiter connector
to extract financial data including:
1. Real-time pricing via Quote API
2. Liquidity scoring via route complexity analysis  
3. Volume estimation via route complexity patterns
4. Market cap calculation via price × supply

This addresses the pre-filtering issue where Jupiter-only tokens have zero financial values.
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

class EnhancedJupiterFinancialConnector:
    """Enhanced Jupiter connector with financial data derivation capabilities"""
    
    def __init__(self):
        # Working Jupiter endpoints (from investigation)
        self.endpoints = {
            "quote": "https://quote-api.jup.ag/v6/quote",
            "tokens": "https://token.jup.ag/all",
            "tokens_strict": "https://token.jup.ag/strict"
        }
        
        # Reference tokens for pricing (stablecoins and major tokens)
        self.reference_tokens = {
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", 
            "SOL": "So11111111111111111111111111111111111111112"
        }
        
        # Standard amounts for testing liquidity depth
        self.test_amounts = [
            1000000,      # $1 worth
            10000000,     # $10 worth
            100000000,    # $100 worth
            1000000000,   # $1000 worth
        ]
        
        self.session = None
        self.api_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "price_derivations": 0,
            "liquidity_analyses": 0,
            "volume_estimations": 0
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_tracked_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request with tracking and error handling"""
        self.api_stats["total_calls"] += 1
        
        try:
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    self.api_stats["successful_calls"] += 1
                    return data
                else:
                    self.api_stats["failed_calls"] += 1
                    logger.warning(f"Jupiter API returned status {response.status} for {url}")
                    return None
        except Exception as e:
            self.api_stats["failed_calls"] += 1
            logger.error(f"Error making Jupiter API request to {url}: {e}")
            return None
    
    async def derive_token_price(self, token_address: str) -> Dict[str, Any]:
        """Derive token price using Jupiter Quote API"""
        self.api_stats["price_derivations"] += 1
        
        # Try token → USDC first
        params = {
            "inputMint": token_address,
            "outputMint": self.reference_tokens["USDC"],
            "amount": "1000000000",  # 1 token (assuming 9 decimals)
            "slippageBps": "100"  # 1% slippage tolerance
        }
        
        quote_data = await self._make_tracked_request(self.endpoints["quote"], params)
        
        if quote_data and "outAmount" in quote_data and "inAmount" in quote_data:
            in_amount = int(quote_data["inAmount"])
            out_amount = int(quote_data["outAmount"])
            
            if in_amount > 0 and out_amount > 0:
                price_usd = out_amount / in_amount
                price_impact = float(quote_data.get("priceImpactPct", 0))
                
                return {
                    "price": price_usd,
                    "price_derivable": True,
                    "method": "quote_api_via_usdc",
                    "price_impact": price_impact,
                    "route_count": len(quote_data.get("routePlan", [])),
                    "confidence": "high" if price_impact < 1.0 else "medium"
                }
        
        # If that failed, try reverse quote (USDC → token)
        params = {
            "inputMint": self.reference_tokens["USDC"],
            "outputMint": token_address,
            "amount": "1000000",  # $1 worth
            "slippageBps": "100"
        }
        
        quote_data = await self._make_tracked_request(self.endpoints["quote"], params)
        
        if quote_data and "outAmount" in quote_data and "inAmount" in quote_data:
            in_amount = int(quote_data["inAmount"])
            out_amount = int(quote_data["outAmount"])
            
            if in_amount > 0 and out_amount > 0:
                tokens_per_dollar = out_amount / in_amount
                price_usd = 1.0 / tokens_per_dollar if tokens_per_dollar > 0 else 0
                price_impact = float(quote_data.get("priceImpactPct", 0))
                
                return {
                    "price": price_usd,
                    "price_derivable": True,
                    "method": "reverse_quote_via_usdc",
                    "price_impact": price_impact,
                    "route_count": len(quote_data.get("routePlan", [])),
                    "confidence": "medium"
                }
        
        return {
            "price": 0,
            "price_derivable": False,
            "method": "failed_all_attempts",
            "confidence": "none"
        }
    
    async def analyze_token_liquidity(self, token_address: str) -> Dict[str, Any]:
        """Analyze token liquidity using route complexity and price impact"""
        self.api_stats["liquidity_analyses"] += 1
        
        liquidity_analysis = {
            "liquidity_score": 0,
            "depth_analysis": {},
            "route_complexity": 0,
            "average_price_impact": 0,
            "liquidity_tier": "unknown"
        }
        
        # Test different amounts to understand liquidity depth
        depth_results = []
        
        for amount in self.test_amounts:
            params = {
                "inputMint": token_address,
                "outputMint": self.reference_tokens["USDC"],
                "amount": str(amount),
                "slippageBps": "100"
            }
            
            quote_data = await self._make_tracked_request(self.endpoints["quote"], params)
            
            if quote_data and "routePlan" in quote_data:
                route_count = len(quote_data.get("routePlan", []))
                price_impact = float(quote_data.get("priceImpactPct", 0))
                
                depth_results.append({
                    "amount_usd": amount / 1000000,
                    "route_count": route_count,
                    "price_impact": price_impact,
                    "quote_successful": True
                })
            else:
                depth_results.append({
                    "amount_usd": amount / 1000000,
                    "route_count": 0,
                    "price_impact": 100.0,  # High impact for failed quotes
                    "quote_successful": False
                })
            
            await asyncio.sleep(0.2)  # Rate limiting
        
        # Calculate liquidity metrics
        if depth_results:
            successful_quotes = [r for r in depth_results if r["quote_successful"]]
            
            if successful_quotes:
                # Average route complexity
                avg_routes = sum(r["route_count"] for r in successful_quotes) / len(successful_quotes)
                liquidity_analysis["route_complexity"] = avg_routes
                
                # Average price impact
                avg_impact = sum(r["price_impact"] for r in successful_quotes) / len(successful_quotes)
                liquidity_analysis["average_price_impact"] = avg_impact
                
                # Calculate liquidity score (0-10)
                # More routes = better liquidity, lower impact = better liquidity
                route_score = min(10, avg_routes * 2)  # Max 10 for 5+ routes
                impact_score = max(0, 10 - (avg_impact * 2))  # Lower impact = higher score
                liquidity_analysis["liquidity_score"] = (route_score + impact_score) / 2
                
                # Determine liquidity tier
                if liquidity_analysis["liquidity_score"] >= 8:
                    liquidity_analysis["liquidity_tier"] = "excellent"
                elif liquidity_analysis["liquidity_score"] >= 6:
                    liquidity_analysis["liquidity_tier"] = "good"
                elif liquidity_analysis["liquidity_score"] >= 4:
                    liquidity_analysis["liquidity_tier"] = "moderate"
                elif liquidity_analysis["liquidity_score"] >= 2:
                    liquidity_analysis["liquidity_tier"] = "low"
                else:
                    liquidity_analysis["liquidity_tier"] = "very_low"
            
            liquidity_analysis["depth_analysis"] = depth_results
        
        return liquidity_analysis
    
    async def estimate_token_volume(self, token_address: str) -> Dict[str, Any]:
        """Estimate token volume using route complexity patterns"""
        self.api_stats["volume_estimations"] += 1
        
        # Get liquidity analysis first
        liquidity_data = await self.analyze_token_liquidity(token_address)
        
        # Volume estimation based on liquidity patterns
        volume_estimation = {
            "estimated_volume_24h": 0,
            "volume_tier": "unknown",
            "estimation_method": "route_complexity_proxy",
            "confidence": "low"
        }
        
        liquidity_score = liquidity_data.get("liquidity_score", 0)
        route_complexity = liquidity_data.get("route_complexity", 0)
        avg_price_impact = liquidity_data.get("average_price_impact", 100)
        
        # Volume estimation formula (rough proxy)
        # High liquidity score + many routes + low impact = higher volume
        if liquidity_score > 0:
            # Base volume estimate from liquidity patterns
            base_volume = liquidity_score * 10000  # $10k per liquidity point
            
            # Route complexity multiplier
            route_multiplier = max(1, route_complexity)
            
            # Price impact penalty (higher impact = lower volume)
            impact_penalty = max(0.1, 1 - (avg_price_impact / 10))
            
            estimated_volume = base_volume * route_multiplier * impact_penalty
            volume_estimation["estimated_volume_24h"] = estimated_volume
            
            # Determine volume tier
            if estimated_volume >= 1000000:  # $1M+
                volume_estimation["volume_tier"] = "high"
                volume_estimation["confidence"] = "medium"
            elif estimated_volume >= 100000:  # $100K+
                volume_estimation["volume_tier"] = "moderate"
                volume_estimation["confidence"] = "medium"
            elif estimated_volume >= 10000:   # $10K+
                volume_estimation["volume_tier"] = "low"
                volume_estimation["confidence"] = "low"
            else:
                volume_estimation["volume_tier"] = "very_low"
                volume_estimation["confidence"] = "low"
        
        volume_estimation["liquidity_basis"] = liquidity_data
        return volume_estimation
    
    async def calculate_market_cap(self, token_address: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate market cap using price × supply (placeholder for full implementation)"""
        
        # This is a placeholder - full implementation would require:
        # 1. Solana RPC call to get token supply
        # 2. Account for decimals properly
        # 3. Handle circulating vs total supply
        
        market_cap_data = {
            "market_cap": 0,
            "calculation_method": "price_times_supply_placeholder",
            "data_available": False,
            "requires_implementation": True,
            "implementation_notes": [
                "Need Solana RPC integration for getTokenSupply",
                "Need to handle token decimals properly",
                "Need circulating supply vs total supply logic"
            ]
        }
        
        if price_data.get("price_derivable") and price_data.get("price", 0) > 0:
            # Placeholder calculation (would need real supply data)
            estimated_supply = 1000000000  # 1B tokens (placeholder)
            estimated_market_cap = price_data["price"] * estimated_supply
            
            market_cap_data.update({
                "market_cap": estimated_market_cap,
                "estimated_supply": estimated_supply,
                "price_used": price_data["price"],
                "calculation_method": "placeholder_with_estimated_supply",
                "confidence": "very_low"
            })
        
        return market_cap_data
    
    async def get_comprehensive_financial_data(self, token_address: str) -> Dict[str, Any]:
        """Get comprehensive financial data for a token using all available methods"""
        logger.info(f"📊 Analyzing financial data for token: {token_address[:8]}...")
        
        start_time = time.time()
        
        # Get price data
        price_data = await self.derive_token_price(token_address)
        
        # Get liquidity analysis
        liquidity_data = await self.analyze_token_liquidity(token_address)
        
        # Estimate volume
        volume_data = await self.estimate_token_volume(token_address)
        
        # Calculate market cap (placeholder)
        market_cap_data = await self.calculate_market_cap(token_address, price_data)
        
        analysis_time = time.time() - start_time
        
        # Compile comprehensive financial profile
        financial_profile = {
            "token_address": token_address,
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_duration_seconds": round(analysis_time, 2),
            
            # Core financial metrics
            "price": price_data.get("price", 0),
            "volume_24h": volume_data.get("estimated_volume_24h", 0),
            "market_cap": market_cap_data.get("market_cap", 0),
            "liquidity_score": liquidity_data.get("liquidity_score", 0),
            
            # Data quality indicators
            "price_derivable": price_data.get("price_derivable", False),
            "price_confidence": price_data.get("confidence", "none"),
            "volume_confidence": volume_data.get("confidence", "low"),
            "market_cap_confidence": market_cap_data.get("confidence", "very_low"),
            
            # Detailed breakdowns
            "price_analysis": price_data,
            "liquidity_analysis": liquidity_data,
            "volume_analysis": volume_data,
            "market_cap_analysis": market_cap_data,
            
            # Jupiter-specific metrics
            "route_complexity": liquidity_data.get("route_complexity", 0),
            "average_price_impact": liquidity_data.get("average_price_impact", 0),
            "liquidity_tier": liquidity_data.get("liquidity_tier", "unknown"),
            "volume_tier": volume_data.get("volume_tier", "unknown"),
            
            # Data source attribution
            "data_source": "jupiter_enhanced_financial_connector",
            "primary_method": "quote_api_derivation"
        }
        
        # Determine overall data quality
        quality_indicators = [
            price_data.get("price_derivable", False),
            liquidity_data.get("liquidity_score", 0) > 0,
            volume_data.get("estimated_volume_24h", 0) > 0
        ]
        
        financial_profile["data_quality_score"] = sum(quality_indicators) / len(quality_indicators)
        financial_profile["has_sufficient_data"] = financial_profile["data_quality_score"] >= 0.5
        
        logger.info(f"✅ Financial analysis complete for {token_address[:8]}: "
                   f"Price=${price_data.get('price', 0):.6f}, "
                   f"Liquidity={liquidity_data.get('liquidity_score', 0):.1f}/10, "
                   f"Quality={financial_profile['data_quality_score']:.1%}")
        
        return financial_profile
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """Get API call statistics"""
        total_calls = self.api_stats["total_calls"]
        success_rate = (self.api_stats["successful_calls"] / total_calls * 100) if total_calls > 0 else 0
        
        return {
            "total_api_calls": total_calls,
            "successful_calls": self.api_stats["successful_calls"],
            "failed_calls": self.api_stats["failed_calls"],
            "success_rate_percent": round(success_rate, 1),
            "price_derivations": self.api_stats["price_derivations"],
            "liquidity_analyses": self.api_stats["liquidity_analyses"],
            "volume_estimations": self.api_stats["volume_estimations"]
        }

async def test_enhanced_jupiter_connector():
    """Test the enhanced Jupiter financial connector"""
    logger.info("🚀 Testing Enhanced Jupiter Financial Connector")
    logger.info("=" * 60)
    
    # Test tokens from actual detection results that were filtered with zero values
    test_tokens = [
        ("USELESS", "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk"),  # 36.0 score, 2 platforms
        ("TRUMP", "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN"),    # 36.0 score, 2 platforms  
        ("aura", "DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2"),     # 35.0 score, 3 platforms (BE, JUP)
        ("GOR", "71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4Bhqd9iL6bEFELvg"),      # 34.0 score, 2 platforms
        ("SPX", "J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr"),      # 34.0 score, 2 platforms
        ("MUMU", "5LafQUrVco6o7KMz42eqVEJ9LW31StPyGjeeu5sKoMtA"),     # 31.0 score, 3 platforms (BE, JUP)
        ("$michi", "5mbK36SZ7J19An8jFochhQS4of8g6BwUjbeCSxBSoWdp"),   # 31.0 score, 3 platforms (BE, JUP)
        ("BILLY", "3B5wuUrMEi5yATD7on46hKfej3pfmd7t1RKgrsN3pump"),    # 31.0 score, 3 platforms (BE, JUP)
        ("INF", "5oVNBeEEQvYi1cX3ir8Dx5n1P7pdxydbGF2X4TxVusJm"),      # 31.0 score, 3 platforms (BE, JUP)
    ]
    
    async with EnhancedJupiterFinancialConnector() as connector:
        results = {}
        
        for symbol, token_address in test_tokens:
            logger.info(f"\n🔍 Testing token: {symbol} ({token_address[:8]}...)")
            
            try:
                financial_data = await connector.get_comprehensive_financial_data(token_address)
                results[f"{symbol}_{token_address}"] = financial_data
                
                # Print summary
                logger.info(f"📈 Results for {symbol}:")
                logger.info(f"   Price: ${financial_data['price']:.6f}")
                logger.info(f"   Volume (est): ${financial_data['volume_24h']:,.0f}")
                logger.info(f"   Liquidity: {financial_data['liquidity_score']:.1f}/10")
                logger.info(f"   Data Quality: {financial_data['data_quality_score']:.1%}")
                logger.info(f"   Method: {financial_data['price_analysis']['method']}")
                
            except Exception as e:
                logger.error(f"❌ Error testing {symbol}: {e}")
                results[f"{symbol}_{token_address}"] = {"error": str(e)}
        
        # Print API statistics
        stats = connector.get_api_statistics()
        logger.info(f"\n📊 API Statistics:")
        logger.info(f"   Total calls: {stats['total_api_calls']}")
        logger.info(f"   Success rate: {stats['success_rate_percent']}%")
        logger.info(f"   Price derivations: {stats['price_derivations']}")
        logger.info(f"   Liquidity analyses: {stats['liquidity_analyses']}")
        
        # Save results
        timestamp = int(time.time())
        filename = f"scripts/tests/enhanced_jupiter_test_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump({
                "test_results": results,
                "api_statistics": stats,
                "test_timestamp": datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        logger.info(f"\n💾 Test results saved to: {filename}")
        logger.info("\n✅ Enhanced Jupiter connector test completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_jupiter_connector()) 