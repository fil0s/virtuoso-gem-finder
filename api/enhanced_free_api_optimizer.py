#!/usr/bin/env python3
"""
Enhanced Free API Optimizer
Maximizes free API data extraction to minimize expensive Birdeye usage

This module implements a multi-layered approach:
1. Extract maximum data from free APIs (Rugcheck + DexScreener)
2. Intelligent filtering and scoring
3. Strategic routing to expensive APIs only for high-conviction tokens
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class FreeAPIToken:
    """Comprehensive token data from free APIs"""
    address: str
    symbol: str = ""
    name: str = ""
    
    # DexScreener data
    social_signals: Dict[str, Any] = None
    boost_data: Dict[str, Any] = None
    liquidity_analysis: Dict[str, Any] = None
    narrative_strength: float = 0.0
    
    # Rugcheck data
    security_score: float = 0.0
    risk_level: str = "unknown"
    is_secure: bool = False
    
    # Composite scores
    free_api_conviction_score: float = 0.0
    birdeye_priority: str = "low"  # low, medium, high, critical
    recommended_birdeye_depth: str = "basic"  # basic, standard, comprehensive

class EnhancedFreeAPIOptimizer:
    """Maximize free API value before expensive calls"""
    
    def __init__(self, rugcheck_connector=None, dexscreener_connector=None):
        self.rugcheck = rugcheck_connector
        self.dexscreener = dexscreener_connector
        self.logger = logging.getLogger(__name__)
        
        # Cost optimization tracking
        self.optimization_stats = {
            "tokens_analyzed": 0,
            "birdeye_calls_saved": 0,
            "estimated_cost_savings": 0.0,
            "filtering_efficiency": 0.0
        }
    
    async def comprehensive_free_analysis(self, token_addresses: List[str]) -> Dict[str, Any]:
        """Extract maximum value from all free APIs"""
        
        self.logger.info(f"🔍 Starting comprehensive free API analysis for {len(token_addresses)} tokens")
        
        # Phase 1: DexScreener Enhanced Data Extraction
        dexscreener_data = await self._extract_enhanced_dexscreener_data(token_addresses)
        
        # Phase 2: Rugcheck Security & Validation
        rugcheck_data = await self._extract_enhanced_rugcheck_data(token_addresses)
        
        # Phase 3: Cross-API Data Fusion
        fused_tokens = self._fuse_api_data(token_addresses, dexscreener_data, rugcheck_data)
        
        # Phase 4: Intelligent Scoring & Routing
        prioritized_tokens = self._calculate_birdeye_priorities(fused_tokens)
        
        # Phase 5: Cost Optimization Analysis
        cost_analysis = self._analyze_cost_optimization(prioritized_tokens)
        
        return {
            "enhanced_tokens": prioritized_tokens,
            "dexscreener_insights": dexscreener_data,
            "rugcheck_insights": rugcheck_data,
            "cost_optimization": cost_analysis,
            "birdeye_routing": self._generate_birdeye_routing_strategy(prioritized_tokens)
        }
    
    async def _extract_enhanced_dexscreener_data(self, token_addresses: List[str]) -> Dict[str, Any]:
        """Extract ALL available DexScreener data efficiently"""
        
        dexscreener_insights = {
            "token_profiles": [],
            "boosted_tokens": [],
            "top_boosted": [],
            "liquidity_analysis": {},
            "narrative_tokens": {},
            "batch_data": {},
            "social_signals": {}
        }
        
        if not self.dexscreener:
            return dexscreener_insights
        
        try:
            # 1. Token Profiles (Rich metadata + social signals)
            profiles = await self.dexscreener.get_token_profiles()
            dexscreener_insights["token_profiles"] = profiles
            
            # Extract social signals from profiles
            for profile in profiles:
                if hasattr(profile, 'address'):
                    dexscreener_insights["social_signals"][profile.address] = {
                        "social_score": getattr(profile, 'social_score', 0.0),
                        "narrative_strength": getattr(profile, 'narrative_strength', 0.0),
                        "website": getattr(profile, 'website', None),
                        "twitter": getattr(profile, 'twitter', None),
                        "telegram": getattr(profile, 'telegram', None),
                        "description": getattr(profile, 'description', "")
                    }
            
            # 2. Boost Activity Analysis
            boosted = await self.dexscreener.get_boosted_tokens()
            top_boosted = await self.dexscreener.get_top_boosted_tokens()
            dexscreener_insights["boosted_tokens"] = boosted
            dexscreener_insights["top_boosted"] = top_boosted
            
            # 3. Batch Token Data (30x efficiency!)
            if token_addresses:
                batch_data = await self.dexscreener.get_batch_token_data(token_addresses)
                for token_data in batch_data:
                    if "address" in token_data:
                        dexscreener_insights["batch_data"][token_data["address"]] = token_data
            
            # 4. Liquidity Analysis for high-priority tokens
            high_priority_addresses = token_addresses[:20]  # Limit to avoid rate limits
            for address in high_priority_addresses:
                liquidity = await self.dexscreener.get_token_liquidity_analysis(address)
                if liquidity:
                    dexscreener_insights["liquidity_analysis"][address] = liquidity
            
            # 5. Narrative-based Discovery
            narratives = ["AI", "agent", "gaming", "DeFi", "RWA", "meme", "pump", "solana"]
            narrative_results = await self.dexscreener.discover_narrative_tokens(narratives)
            dexscreener_insights["narrative_tokens"] = narrative_results
            
        except Exception as e:
            self.logger.error(f"Error in DexScreener data extraction: {e}")
        
        return dexscreener_insights
    
    async def _extract_enhanced_rugcheck_data(self, token_addresses: List[str]) -> Dict[str, Any]:
        """Extract ALL available Rugcheck data"""
        
        rugcheck_insights = {
            "security_results": {},
            "trending_tokens": [],
            "validation_results": {},
            "quality_routing": {},
            "age_analysis": {}
        }
        
        if not self.rugcheck:
            return rugcheck_insights
        
        try:
            # 1. Comprehensive Security Analysis
            security_results = await self.rugcheck.batch_analyze_tokens(token_addresses)
            rugcheck_insights["security_results"] = {
                addr: {
                    "score": result.score,
                    "risk_level": result.risk_level.value,
                    "is_healthy": result.is_healthy,
                    "issues": result.issues,
                    "warnings": result.warnings
                } for addr, result in security_results.items()
            }
            
            # 2. Trending Token Intelligence
            trending = await self.rugcheck.get_trending_tokens()
            rugcheck_insights["trending_tokens"] = trending
            
            # 3. Pre-validation for Expensive APIs
            validation_results = await self.rugcheck.pre_validate_for_birdeye_analysis(token_addresses)
            rugcheck_insights["validation_results"] = validation_results
            
            # 4. Quality-based Routing
            token_objects = [{"address": addr} for addr in token_addresses]
            quality_routing = self.rugcheck.route_tokens_by_quality(
                token_objects, security_results, validation_results
            )
            rugcheck_insights["quality_routing"] = quality_routing
            
            # 5. Token Age Analysis (for timeframe optimization)
            age_analysis = {}
            for address in token_addresses[:10]:  # Sample for age analysis
                age_info = await self.rugcheck.get_token_age_info(address)
                if age_info:
                    age_analysis[address] = age_info
            rugcheck_insights["age_analysis"] = age_analysis
            
        except Exception as e:
            self.logger.error(f"Error in Rugcheck data extraction: {e}")
        
        return rugcheck_insights
    
    def _fuse_api_data(self, token_addresses: List[str], dexscreener_data: Dict, rugcheck_data: Dict) -> List[FreeAPIToken]:
        """Intelligently combine data from both APIs"""
        
        fused_tokens = []
        
        for address in token_addresses:
            # Initialize token with address
            token = FreeAPIToken(address=address)
            
            # Fuse DexScreener data
            if address in dexscreener_data.get("batch_data", {}):
                batch_info = dexscreener_data["batch_data"][address]
                token.symbol = batch_info.get("symbol", "")
                token.name = batch_info.get("name", "")
            
            # Social signals from DexScreener
            if address in dexscreener_data.get("social_signals", {}):
                token.social_signals = dexscreener_data["social_signals"][address]
                token.narrative_strength = token.social_signals.get("narrative_strength", 0.0)
            
            # Boost data
            for boost_token in dexscreener_data.get("boosted_tokens", []):
                if boost_token.get("tokenAddress") == address:
                    token.boost_data = boost_token
                    break
            
            # Liquidity analysis
            if address in dexscreener_data.get("liquidity_analysis", {}):
                token.liquidity_analysis = dexscreener_data["liquidity_analysis"][address]
            
            # Fuse Rugcheck data
            if address in rugcheck_data.get("security_results", {}):
                security = rugcheck_data["security_results"][address]
                token.security_score = security.get("score", 0.0) or 0.0
                token.risk_level = security.get("risk_level", "unknown")
                token.is_secure = security.get("is_healthy", False)
            
            fused_tokens.append(token)
        
        return fused_tokens
    
    def _calculate_birdeye_priorities(self, tokens: List[FreeAPIToken]) -> List[FreeAPIToken]:
        """Calculate intelligent Birdeye usage priorities"""
        
        for token in tokens:
            priority_score = 0.0
            reasons = []
            
            # Security Score (40% weight)
            if token.security_score:
                security_weight = min(token.security_score / 100.0, 1.0) * 40
                priority_score += security_weight
                if token.security_score >= 80:
                    reasons.append("high_security_score")
            
            # Social Signals (25% weight)
            if token.social_signals:
                social_score = token.social_signals.get("social_score", 0.0)
                narrative_score = token.social_signals.get("narrative_strength", 0.0)
                social_weight = ((social_score + narrative_score) / 2.0) * 25
                priority_score += social_weight
                if social_score > 0.7:
                    reasons.append("strong_social_presence")
            
            # Boost Activity (20% weight)
            if token.boost_data:
                boost_amount = token.boost_data.get("amount", 0)
                boost_total = token.boost_data.get("totalAmount", 1)
                boost_activity = (boost_total - boost_amount) / max(boost_total, 1)
                boost_weight = min(boost_activity, 1.0) * 20
                priority_score += boost_weight
                if boost_activity > 0.5:
                    reasons.append("active_marketing")
            
            # Liquidity Health (15% weight)
            if token.liquidity_analysis:
                liquidity_usd = token.liquidity_analysis.get("total_liquidity_usd", 0)
                pair_count = token.liquidity_analysis.get("pair_count", 0)
                liquidity_score = min(liquidity_usd / 100000, 1.0) * 0.7 + min(pair_count / 5, 1.0) * 0.3
                liquidity_weight = liquidity_score * 15
                priority_score += liquidity_weight
                if liquidity_usd > 50000:
                    reasons.append("healthy_liquidity")
            
            # Set priority and depth based on score
            token.free_api_conviction_score = priority_score
            
            if priority_score >= 70:
                token.birdeye_priority = "critical"
                token.recommended_birdeye_depth = "comprehensive"
            elif priority_score >= 50:
                token.birdeye_priority = "high"
                token.recommended_birdeye_depth = "standard"
            elif priority_score >= 30:
                token.birdeye_priority = "medium"
                token.recommended_birdeye_depth = "basic"
            else:
                token.birdeye_priority = "low"
                token.recommended_birdeye_depth = "skip"
        
        # Sort by priority score
        tokens.sort(key=lambda t: t.free_api_conviction_score, reverse=True)
        return tokens
    
    def _analyze_cost_optimization(self, tokens: List[FreeAPIToken]) -> Dict[str, Any]:
        """Calculate cost savings from intelligent filtering"""
        
        total_tokens = len(tokens)
        skip_count = len([t for t in tokens if t.recommended_birdeye_depth == "skip"])
        basic_count = len([t for t in tokens if t.recommended_birdeye_depth == "basic"])
        standard_count = len([t for t in tokens if t.recommended_birdeye_depth == "standard"])
        comprehensive_count = len([t for t in tokens if t.recommended_birdeye_depth == "comprehensive"])
        
        # Estimated Birdeye costs (adjust based on actual pricing)
        cost_per_basic = 0.002
        cost_per_standard = 0.008
        cost_per_comprehensive = 0.020
        
        # Without optimization (all comprehensive)
        unoptimized_cost = total_tokens * cost_per_comprehensive
        
        # With optimization
        optimized_cost = (
            basic_count * cost_per_basic +
            standard_count * cost_per_standard +
            comprehensive_count * cost_per_comprehensive
        )
        
        cost_savings = unoptimized_cost - optimized_cost
        efficiency = (cost_savings / unoptimized_cost) * 100 if unoptimized_cost > 0 else 0
        
        self.optimization_stats.update({
            "tokens_analyzed": total_tokens,
            "birdeye_calls_saved": skip_count,
            "estimated_cost_savings": cost_savings,
            "filtering_efficiency": efficiency
        })
        
        return {
            "total_tokens": total_tokens,
            "routing": {
                "skip": skip_count,
                "basic": basic_count,
                "standard": standard_count,
                "comprehensive": comprehensive_count
            },
            "cost_analysis": {
                "unoptimized_cost": unoptimized_cost,
                "optimized_cost": optimized_cost,
                "savings": cost_savings,
                "efficiency_percentage": efficiency
            },
            "top_candidates": [
                {
                    "address": t.address,
                    "symbol": t.symbol,
                    "conviction_score": t.free_api_conviction_score,
                    "priority": t.birdeye_priority,
                    "recommended_depth": t.recommended_birdeye_depth
                }
                for t in tokens[:10]  # Top 10 candidates
            ]
        }
    
    def _generate_birdeye_routing_strategy(self, tokens: List[FreeAPIToken]) -> Dict[str, Any]:
        """Generate optimal Birdeye API usage strategy"""
        
        routing_strategy = {
            "immediate_analysis": [],  # Critical priority tokens
            "standard_analysis": [],   # High priority tokens
            "basic_analysis": [],      # Medium priority tokens
            "skip_analysis": [],       # Low priority tokens
            "batch_optimization": {}
        }
        
        for token in tokens:
            token_info = {
                "address": token.address,
                "symbol": token.symbol,
                "conviction_score": token.free_api_conviction_score,
                "reasons": []
            }
            
            # Add reasoning based on free API insights
            if token.is_secure and token.security_score >= 80:
                token_info["reasons"].append("security_validated")
            if token.social_signals and token.social_signals.get("social_score", 0) > 0.7:
                token_info["reasons"].append("strong_social_signals")
            if token.boost_data:
                token_info["reasons"].append("marketing_activity")
            if token.liquidity_analysis and token.liquidity_analysis.get("total_liquidity_usd", 0) > 50000:
                token_info["reasons"].append("healthy_liquidity")
            
            # Route to appropriate analysis tier
            if token.birdeye_priority == "critical":
                routing_strategy["immediate_analysis"].append(token_info)
            elif token.birdeye_priority == "high":
                routing_strategy["standard_analysis"].append(token_info)
            elif token.birdeye_priority == "medium":
                routing_strategy["basic_analysis"].append(token_info)
            else:
                routing_strategy["skip_analysis"].append(token_info)
        
        # Batch optimization suggestions
        routing_strategy["batch_optimization"] = {
            "immediate_batch_size": min(len(routing_strategy["immediate_analysis"]), 5),
            "standard_batch_size": min(len(routing_strategy["standard_analysis"]), 10),
            "basic_batch_size": min(len(routing_strategy["basic_analysis"]), 20),
            "recommended_delay_between_batches": "30s",
            "estimated_total_time": f"{len(routing_strategy['immediate_analysis']) * 2 + len(routing_strategy['standard_analysis']) * 1.5 + len(routing_strategy['basic_analysis']) * 0.5:.1f} minutes"
        }
        
        return routing_strategy

    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get comprehensive optimization performance summary"""
        return {
            "optimization_stats": self.optimization_stats,
            "recommendations": [
                "Use DexScreener batch processing for 30x API efficiency",
                "Leverage social signals for early conviction scoring",
                "Apply Rugcheck security filtering before expensive analysis",
                "Route tokens by priority to optimize Birdeye costs",
                "Use narrative-based discovery for proactive token finding"
            ]
        }

# Usage Example
async def demonstrate_optimization():
    """Demonstrate the enhanced free API optimization"""
    
    optimizer = EnhancedFreeAPIOptimizer()
    
    # Sample token addresses
    test_tokens = [
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "So11111111111111111111111111111111111111112",   # SOL
        # Add more test tokens...
    ]
    
    print("🚀 Enhanced Free API Optimization Demo")
    print("=" * 50)
    
    # Run comprehensive analysis
    results = await optimizer.comprehensive_free_analysis(test_tokens)
    
    # Display optimization results
    cost_analysis = results["cost_optimization"]
    print(f"💰 Cost Optimization Results:")
    print(f"   Total Tokens: {cost_analysis['total_tokens']}")
    print(f"   Estimated Savings: ${cost_analysis['cost_analysis']['savings']:.3f}")
    print(f"   Efficiency: {cost_analysis['cost_analysis']['efficiency_percentage']:.1f}%")
    
    # Show routing strategy
    routing = results["birdeye_routing"]
    print(f"\n🎯 Birdeye Routing Strategy:")
    print(f"   Critical Priority: {len(routing['immediate_analysis'])} tokens")
    print(f"   High Priority: {len(routing['standard_analysis'])} tokens")
    print(f"   Medium Priority: {len(routing['basic_analysis'])} tokens")
    print(f"   Skip Analysis: {len(routing['skip_analysis'])} tokens")
    
    return results

if __name__ == "__main__":
    asyncio.run(demonstrate_optimization()) 