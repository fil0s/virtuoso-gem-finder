#!/usr/bin/env python3
"""
Enhanced DEX Leverage Strategy

Transforms basic Orca/Raydium usage into sophisticated token discovery system.
Leverages advanced features like:
- Yield farming intelligence
- Cross-DEX arbitrage detection  
- Trending pool analysis
- Quality scoring systems
- Batch processing optimization
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.orca_connector import OrcaConnector
from api.raydium_connector import RaydiumConnector
from services.logger_setup import LoggerSetup

class EnhancedDEXLeverageStrategy:
    """
    Advanced DEX leverage strategy that maximizes Orca and Raydium capabilities
    """
    
    def __init__(self):
        self.logger_setup = LoggerSetup(__name__, log_level="INFO")
        self.logger = self.logger_setup.logger
        
        # Strategy configurations
        self.config = {
            "yield_farming": {
                "min_apy": 50.0,  # Minimum APY for opportunities
                "min_liquidity": 10000,  # Minimum liquidity for safety
                "max_risk_score": 70  # Maximum risk tolerance
            },
            "trending_analysis": {
                "min_volume_24h": 5000,  # Minimum volume for trending
                "volume_growth_threshold": 50.0,  # % growth for trending status
                "liquidity_threshold": 25000  # Minimum liquidity for quality
            },
            "cross_dex_arbitrage": {
                "min_price_diff": 2.0,  # Minimum price difference %
                "min_liquidity_both": 15000,  # Minimum liquidity on both sides
                "max_slippage": 5.0  # Maximum acceptable slippage
            },
            "quality_scoring": {
                "liquidity_weight": 0.4,
                "volume_weight": 0.3,
                "apy_weight": 0.2,
                "diversity_weight": 0.1
            }
        }
        
        # Results storage
        self.results = {
            "yield_opportunities": [],
            "trending_tokens": [],
            "arbitrage_opportunities": [],
            "quality_rankings": [],
            "cross_dex_analysis": {},
            "performance_metrics": {}
        }
        
    async def __aenter__(self):
        """Initialize API connectors"""
        self.orca = OrcaConnector()
        self.raydium = RaydiumConnector()
        
        await self.orca.__aenter__()
        await self.raydium.__aenter__()
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up API connectors"""
        if hasattr(self, 'orca'):
            await self.orca.__aexit__(exc_type, exc_val, exc_tb)
        if hasattr(self, 'raydium'):
            await self.raydium.__aexit__(exc_type, exc_val, exc_tb)

    async def discover_yield_farming_opportunities(self) -> List[Dict[str, Any]]:
        """
        ENHANCED: Discover high-yield farming opportunities using Raydium's advanced features
        """
        self.logger.info("🌾 Discovering yield farming opportunities...")
        
        start_time = time.time()
        
        # Use Raydium's advanced APY discovery
        high_apy_opportunities = await self.raydium.get_high_apy_opportunities(
            min_apy=self.config["yield_farming"]["min_apy"],
            min_liquidity=self.config["yield_farming"]["min_liquidity"]
        )
        
        enhanced_opportunities = []
        
        for opportunity in high_apy_opportunities:
            # Calculate risk score
            risk_score = self._calculate_yield_risk_score(opportunity)
            
            # Enhanced opportunity data
            enhanced_opp = {
                "token_name": opportunity.get("name", "Unknown"),
                "apy": opportunity.get("apy", 0),
                "liquidity": opportunity.get("liquidity", 0),
                "volume_24h": opportunity.get("volume_24h", 0),
                "risk_score": risk_score,
                "safety_rating": self._get_safety_rating(risk_score),
                "yield_category": self._categorize_yield_opportunity(opportunity),
                "dex": "Raydium",
                "discovery_method": "high_apy_scan",
                "pair_data": opportunity.get("pair_data", {})
            }
            
            # Only include opportunities within risk tolerance
            if risk_score <= self.config["yield_farming"]["max_risk_score"]:
                enhanced_opportunities.append(enhanced_opp)
        
        # Sort by yield-adjusted risk score
        enhanced_opportunities.sort(
            key=lambda x: x["apy"] / (1 + x["risk_score"] / 100), 
            reverse=True
        )
        
        self.results["yield_opportunities"] = enhanced_opportunities
        
        processing_time = time.time() - start_time
        self.logger.info(f"✅ Found {len(enhanced_opportunities)} yield opportunities in {processing_time:.2f}s")
        
        return enhanced_opportunities
    
    async def discover_trending_tokens_advanced(self) -> List[Dict[str, Any]]:
        """
        ENHANCED: Use both Orca and Raydium trending analysis for token discovery
        """
        self.logger.info("📈 Discovering trending tokens across DEXs...")
        
        start_time = time.time()
        
        # Get trending from both DEXs in parallel
        orca_trending_task = self.orca.get_trending_pools(
            min_volume_24h=self.config["trending_analysis"]["min_volume_24h"]
        )
        raydium_trending_task = self.raydium.get_volume_trending_pairs(
            min_volume_24h=self.config["trending_analysis"]["min_volume_24h"],
            limit=100
        )
        
        orca_trending, raydium_trending = await asyncio.gather(
            orca_trending_task, raydium_trending_task
        )
        
        # Process Orca trending tokens
        trending_tokens = []
        
        for pool in orca_trending:
            # Extract token addresses from pool
            tokens = self._extract_tokens_from_orca_pool(pool)
            
            for token_addr, token_data in tokens.items():
                trending_tokens.append({
                    "token_address": token_addr,
                    "symbol": token_data.get("symbol", "Unknown"),
                    "dex": "Orca",
                    "pool_type": "Whirlpool",
                    "liquidity": pool.get("liquidity", 0),
                    "volume_24h": pool.get("volume_24h", 0),
                    "trending_score": self._calculate_orca_trending_score(pool),
                    "discovery_method": "orca_trending_pools",
                    "pool_data": pool
                })
        
        # Process Raydium trending tokens
        for pair in raydium_trending:
            # Extract token addresses from pair
            tokens = self._extract_tokens_from_raydium_pair(pair)
            
            for token_addr, token_data in tokens.items():
                trending_tokens.append({
                    "token_address": token_addr,
                    "symbol": token_data.get("symbol", "Unknown"),
                    "dex": "Raydium",
                    "pool_type": pair.get("pool_type", "AMM"),
                    "liquidity": pair.get("liquidity", 0),
                    "volume_24h": pair.get("volume_24h", 0),
                    "apy": pair.get("apy", 0),
                    "trending_score": self._calculate_raydium_trending_score(pair),
                    "discovery_method": "raydium_trending_pairs",
                    "pair_data": pair
                })
        
        # Remove duplicates and merge cross-DEX data
        unique_trending = self._merge_cross_dex_trending_data(trending_tokens)
        
        # Sort by combined trending score
        unique_trending.sort(key=lambda x: x.get("combined_trending_score", 0), reverse=True)
        
        self.results["trending_tokens"] = unique_trending
        
        processing_time = time.time() - start_time
        self.logger.info(f"✅ Found {len(unique_trending)} trending tokens in {processing_time:.2f}s")
        
        return unique_trending
    
    async def detect_cross_dex_arbitrage_opportunities(self, token_addresses: List[str]) -> List[Dict[str, Any]]:
        """
        ENHANCED: Detect arbitrage opportunities between Orca and Raydium
        """
        self.logger.info(f"⚖️ Analyzing {len(token_addresses)} tokens for cross-DEX arbitrage...")
        
        start_time = time.time()
        arbitrage_opportunities = []
        
        # Use batch processing for efficiency
        orca_batch_task = self.orca.get_batch_token_analytics(token_addresses)
        raydium_batch_task = self.raydium.get_batch_token_analytics(token_addresses)
        
        orca_data, raydium_data = await asyncio.gather(orca_batch_task, raydium_batch_task)
        
        for token_addr in token_addresses:
            orca_info = orca_data.get(token_addr, {})
            raydium_info = raydium_data.get(token_addr, {})
            
            # Both DEXs must have the token
            if not (orca_info.get("found") and raydium_info.get("found")):
                continue
            
            # Calculate arbitrage potential
            arbitrage_analysis = self._analyze_arbitrage_opportunity(
                token_addr, orca_info, raydium_info
            )
            
            if arbitrage_analysis["profitable"]:
                arbitrage_opportunities.append(arbitrage_analysis)
        
        # Sort by profit potential
        arbitrage_opportunities.sort(key=lambda x: x["profit_potential"], reverse=True)
        
        self.results["arbitrage_opportunities"] = arbitrage_opportunities
        
        processing_time = time.time() - start_time
        self.logger.info(f"✅ Found {len(arbitrage_opportunities)} arbitrage opportunities in {processing_time:.2f}s")
        
        return arbitrage_opportunities
    
    async def generate_enhanced_token_quality_rankings(self, token_addresses: List[str]) -> List[Dict[str, Any]]:
        """
        ENHANCED: Generate comprehensive token quality rankings using both DEXs
        """
        self.logger.info(f"🏆 Generating quality rankings for {len(token_addresses)} tokens...")
        
        start_time = time.time()
        
        # Get comprehensive data from both DEXs
        orca_batch_task = self.orca.get_batch_token_analytics(token_addresses)
        raydium_batch_task = self.raydium.get_batch_token_analytics(token_addresses)
        
        orca_data, raydium_data = await asyncio.gather(orca_batch_task, raydium_batch_task)
        
        quality_rankings = []
        
        for token_addr in token_addresses:
            orca_info = orca_data.get(token_addr, {})
            raydium_info = raydium_data.get(token_addr, {})
            
            # Calculate comprehensive quality score
            quality_analysis = self._calculate_comprehensive_quality_score(
                token_addr, orca_info, raydium_info
            )
            
            quality_rankings.append(quality_analysis)
        
        # Sort by quality score
        quality_rankings.sort(key=lambda x: x["overall_quality_score"], reverse=True)
        
        self.results["quality_rankings"] = quality_rankings
        
        processing_time = time.time() - start_time
        self.logger.info(f"✅ Generated quality rankings in {processing_time:.2f}s")
        
        return quality_rankings
    
    async def run_comprehensive_dex_analysis(self, token_addresses: List[str]) -> Dict[str, Any]:
        """
        ENHANCED: Run comprehensive analysis leveraging all advanced DEX features
        """
        self.logger.info("🚀 Running comprehensive enhanced DEX analysis...")
        
        analysis_start = time.time()
        
        # Run all enhanced strategies in parallel
        tasks = [
            self.discover_yield_farming_opportunities(),
            self.discover_trending_tokens_advanced(),
            self.detect_cross_dex_arbitrage_opportunities(token_addresses),
            self.generate_enhanced_token_quality_rankings(token_addresses)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        yield_opportunities = results[0] if not isinstance(results[0], Exception) else []
        trending_tokens = results[1] if not isinstance(results[1], Exception) else []
        arbitrage_opportunities = results[2] if not isinstance(results[2], Exception) else []
        quality_rankings = results[3] if not isinstance(results[3], Exception) else []
        
        # Generate comprehensive insights
        comprehensive_analysis = {
            "analysis_timestamp": datetime.now().isoformat(),
            "processing_time_seconds": time.time() - analysis_start,
            "enhanced_features_used": [
                "yield_farming_intelligence",
                "cross_dex_trending_analysis", 
                "arbitrage_detection",
                "comprehensive_quality_scoring",
                "batch_processing_optimization"
            ],
            "results_summary": {
                "yield_opportunities_found": len(yield_opportunities),
                "trending_tokens_discovered": len(trending_tokens),
                "arbitrage_opportunities": len(arbitrage_opportunities),
                "tokens_quality_ranked": len(quality_rankings),
                "total_insights_generated": len(yield_opportunities) + len(trending_tokens) + len(arbitrage_opportunities)
            },
            "top_insights": {
                "best_yield_opportunity": yield_opportunities[0] if yield_opportunities else None,
                "hottest_trending_token": trending_tokens[0] if trending_tokens else None,
                "best_arbitrage_opportunity": arbitrage_opportunities[0] if arbitrage_opportunities else None,
                "highest_quality_token": quality_rankings[0] if quality_rankings else None
            },
            "detailed_results": {
                "yield_opportunities": yield_opportunities,
                "trending_tokens": trending_tokens,
                "arbitrage_opportunities": arbitrage_opportunities,
                "quality_rankings": quality_rankings
            },
            "performance_metrics": {
                "orca_api_calls": getattr(self.orca, 'api_calls_made', 0),
                "raydium_api_calls": getattr(self.raydium, 'api_calls_made', 0),
                "data_points_collected": self._count_total_data_points(),
                "efficiency_score": self._calculate_efficiency_score()
            }
        }
        
        self.results["comprehensive_analysis"] = comprehensive_analysis
        
        total_time = time.time() - analysis_start
        self.logger.info(f"✅ Comprehensive enhanced DEX analysis completed in {total_time:.2f}s")
        
        return comprehensive_analysis
    
    def _calculate_yield_risk_score(self, opportunity: Dict[str, Any]) -> float:
        """Calculate risk score for yield opportunity (0-100, lower is safer)"""
        liquidity = opportunity.get("liquidity", 0)
        volume = opportunity.get("volume_24h", 0)
        apy = opportunity.get("apy", 0)
        
        # Risk factors
        liquidity_risk = max(0, 50 - (liquidity / 1000))  # Higher liquidity = lower risk
        volume_risk = max(0, 30 - (volume / 500))  # Higher volume = lower risk
        apy_risk = min(20, apy / 10)  # Very high APY = higher risk
        
        return min(100, liquidity_risk + volume_risk + apy_risk)
    
    def _get_safety_rating(self, risk_score: float) -> str:
        """Convert risk score to safety rating"""
        if risk_score <= 30:
            return "Low Risk"
        elif risk_score <= 50:
            return "Medium Risk"
        elif risk_score <= 70:
            return "High Risk"
        else:
            return "Very High Risk"
    
    def _categorize_yield_opportunity(self, opportunity: Dict[str, Any]) -> str:
        """Categorize yield opportunity type"""
        apy = opportunity.get("apy", 0)
        
        if apy >= 200:
            return "Ultra High Yield"
        elif apy >= 100:
            return "High Yield"
        elif apy >= 50:
            return "Medium Yield"
        else:
            return "Conservative Yield"
    
    def _extract_tokens_from_orca_pool(self, pool: Dict[str, Any]) -> Dict[str, Dict]:
        """Extract token information from Orca pool data"""
        tokens = {}
        
        # Extract token addresses and metadata from pool structure
        # This would be implemented based on actual Orca pool structure
        if "token_a" in pool:
            tokens[pool["token_a"]["address"]] = {
                "symbol": pool["token_a"].get("symbol", "Unknown"),
                "name": pool["token_a"].get("name", "Unknown")
            }
        
        if "token_b" in pool:
            tokens[pool["token_b"]["address"]] = {
                "symbol": pool["token_b"].get("symbol", "Unknown"),
                "name": pool["token_b"].get("name", "Unknown")
            }
        
        return tokens
    
    def _extract_tokens_from_raydium_pair(self, pair: Dict[str, Any]) -> Dict[str, Dict]:
        """Extract token information from Raydium pair data"""
        tokens = {}
        
        # Extract token addresses and metadata from pair structure
        # This would be implemented based on actual Raydium pair structure
        if "base_mint" in pair:
            tokens[pair["base_mint"]] = {
                "symbol": pair.get("base_symbol", "Unknown"),
                "name": pair.get("base_name", "Unknown")
            }
        
        if "quote_mint" in pair:
            tokens[pair["quote_mint"]] = {
                "symbol": pair.get("quote_symbol", "Unknown"),
                "name": pair.get("quote_name", "Unknown")
            }
        
        return tokens
    
    def _calculate_orca_trending_score(self, pool: Dict[str, Any]) -> float:
        """Calculate trending score for Orca pool"""
        volume = pool.get("volume_24h", 0)
        liquidity = pool.get("liquidity", 0)
        
        # Normalize and weight factors
        volume_score = min(50, volume / 1000)
        liquidity_score = min(30, liquidity / 2000)
        
        return volume_score + liquidity_score
    
    def _calculate_raydium_trending_score(self, pair: Dict[str, Any]) -> float:
        """Calculate trending score for Raydium pair"""
        volume = pair.get("volume_24h", 0)
        liquidity = pair.get("liquidity", 0)
        apy = pair.get("apy", 0)
        
        # Normalize and weight factors
        volume_score = min(40, volume / 1000)
        liquidity_score = min(25, liquidity / 2000)
        apy_score = min(15, apy / 20)
        
        return volume_score + liquidity_score + apy_score
    
    def _merge_cross_dex_trending_data(self, trending_tokens: List[Dict]) -> List[Dict]:
        """Merge trending data from multiple DEXs for same tokens"""
        token_map = defaultdict(lambda: {"dexs": [], "combined_data": {}})
        
        # Group by token address
        for token in trending_tokens:
            addr = token["token_address"]
            token_map[addr]["dexs"].append(token["dex"])
            
            # Merge data
            if not token_map[addr]["combined_data"]:
                token_map[addr]["combined_data"] = token.copy()
            else:
                # Combine metrics from multiple DEXs
                existing = token_map[addr]["combined_data"]
                existing["liquidity"] += token.get("liquidity", 0)
                existing["volume_24h"] += token.get("volume_24h", 0)
                existing["trending_score"] += token.get("trending_score", 0)
                
                # Track multi-DEX presence
                existing["multi_dex"] = True
                existing["dex_count"] = len(token_map[addr]["dexs"])
        
        # Convert back to list and calculate combined scores
        merged_tokens = []
        for addr, data in token_map.items():
            token_data = data["combined_data"]
            token_data["combined_trending_score"] = token_data.get("trending_score", 0)
            
            # Bonus for multi-DEX presence
            if len(data["dexs"]) > 1:
                token_data["combined_trending_score"] *= 1.5
                token_data["multi_dex_bonus"] = True
            
            merged_tokens.append(token_data)
        
        return merged_tokens
    
    def _analyze_arbitrage_opportunity(self, token_addr: str, orca_info: Dict, raydium_info: Dict) -> Dict[str, Any]:
        """Analyze arbitrage opportunity between DEXs"""
        # This would implement actual arbitrage calculation
        # For now, simplified example
        
        orca_liquidity = orca_info.get("total_liquidity", 0)
        raydium_liquidity = raydium_info.get("total_liquidity", 0)
        
        # Simplified arbitrage detection (would need actual price data)
        liquidity_diff = abs(orca_liquidity - raydium_liquidity)
        min_liquidity = min(orca_liquidity, raydium_liquidity)
        
        if min_liquidity > self.config["cross_dex_arbitrage"]["min_liquidity_both"]:
            profit_potential = liquidity_diff / min_liquidity * 100
            
            return {
                "token_address": token_addr,
                "profitable": profit_potential > self.config["cross_dex_arbitrage"]["min_price_diff"],
                "profit_potential": profit_potential,
                "orca_liquidity": orca_liquidity,
                "raydium_liquidity": raydium_liquidity,
                "arbitrage_type": "liquidity_imbalance",
                "confidence": min(90, profit_potential * 10)  # Simplified confidence
            }
        
        return {
            "token_address": token_addr,
            "profitable": False,
            "profit_potential": 0,
            "reason": "insufficient_liquidity"
        }
    
    def _calculate_comprehensive_quality_score(self, token_addr: str, orca_info: Dict, raydium_info: Dict) -> Dict[str, Any]:
        """Calculate comprehensive quality score using both DEXs"""
        weights = self.config["quality_scoring"]
        
        # Aggregate metrics from both DEXs
        total_liquidity = orca_info.get("total_liquidity", 0) + raydium_info.get("total_liquidity", 0)
        total_volume = orca_info.get("total_volume_24h", 0) + raydium_info.get("total_volume_24h", 0)
        avg_apy = (orca_info.get("avg_apy", 0) + raydium_info.get("avg_apy", 0)) / 2
        pool_diversity = orca_info.get("pool_count", 0) + raydium_info.get("pool_count", 0) + raydium_info.get("pair_count", 0)
        
        # Calculate weighted scores
        liquidity_score = min(100, total_liquidity / 1000) * weights["liquidity_weight"]
        volume_score = min(100, total_volume / 500) * weights["volume_weight"]
        apy_score = min(100, avg_apy / 2) * weights["apy_weight"]
        diversity_score = min(100, pool_diversity * 10) * weights["diversity_weight"]
        
        overall_score = liquidity_score + volume_score + apy_score + diversity_score
        
        return {
            "token_address": token_addr,
            "overall_quality_score": overall_score,
            "liquidity_score": liquidity_score,
            "volume_score": volume_score,
            "apy_score": apy_score,
            "diversity_score": diversity_score,
            "total_liquidity": total_liquidity,
            "total_volume_24h": total_volume,
            "avg_apy": avg_apy,
            "pool_diversity": pool_diversity,
            "dex_presence": {
                "orca": orca_info.get("found", False),
                "raydium": raydium_info.get("found", False),
                "multi_dex": orca_info.get("found", False) and raydium_info.get("found", False)
            }
        }
    
    def _count_total_data_points(self) -> int:
        """Count total data points collected"""
        total = 0
        for result_set in self.results.values():
            if isinstance(result_set, list):
                total += len(result_set)
        return total
    
    def _calculate_efficiency_score(self) -> float:
        """Calculate efficiency score based on data points per API call"""
        total_calls = getattr(self.orca, 'api_calls_made', 0) + getattr(self.raydium, 'api_calls_made', 0)
        total_data_points = self._count_total_data_points()
        
        if total_calls == 0:
            return 0
        
        return total_data_points / total_calls
    
    def save_results(self, filename: Optional[str] = None):
        """Save enhanced analysis results"""
        if not filename:
            timestamp = int(time.time())
            filename = f"scripts/results/enhanced_dex_leverage_analysis_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.logger.info(f"💾 Enhanced DEX analysis results saved to {filename}")
        return filename

# Demo function
async def demo_enhanced_dex_leverage():
    """Demo of enhanced DEX leverage capabilities"""
    
    print("🚀 ENHANCED DEX LEVERAGE STRATEGY DEMO")
    print("="*60)
    
    # Sample tokens for testing
    sample_tokens = [
        "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN",  # TRUMP (known to exist)
        "Dz9mQ9NzkBcCsuGPFJ3r1bS4wgqKMHBPiVuniW8Mbonk",  # USELESS
        "DtR4D9FtVoTX2569gaL837ZgrB6wNjj6tkmnX9Rdk9B2",  # aura
    ]
    
    async with EnhancedDEXLeverageStrategy() as strategy:
        # Run comprehensive analysis
        results = await strategy.run_comprehensive_dex_analysis(sample_tokens)
        
        # Display results
        print(f"\n📊 ENHANCED ANALYSIS RESULTS:")
        print(f"Processing Time: {results['processing_time_seconds']:.2f}s")
        print(f"Yield Opportunities: {results['results_summary']['yield_opportunities_found']}")
        print(f"Trending Tokens: {results['results_summary']['trending_tokens_discovered']}")
        print(f"Arbitrage Opportunities: {results['results_summary']['arbitrage_opportunities']}")
        print(f"Quality Rankings Generated: {results['results_summary']['tokens_quality_ranked']}")
        
        # Show top insights
        if results['top_insights']['best_yield_opportunity']:
            yield_opp = results['top_insights']['best_yield_opportunity']
            print(f"\n🌾 Best Yield Opportunity:")
            print(f"   Token: {yield_opp['token_name']}")
            print(f"   APY: {yield_opp['apy']:.2f}%")
            print(f"   Safety: {yield_opp['safety_rating']}")
        
        if results['top_insights']['hottest_trending_token']:
            trending = results['top_insights']['hottest_trending_token']
            print(f"\n📈 Hottest Trending Token:")
            print(f"   Symbol: {trending['symbol']}")
            print(f"   DEX: {trending['dex']}")
            print(f"   Volume 24h: ${trending['volume_24h']:,.2f}")
        
        # Save results
        filename = strategy.save_results()
        print(f"\n💾 Full results saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(demo_enhanced_dex_leverage())