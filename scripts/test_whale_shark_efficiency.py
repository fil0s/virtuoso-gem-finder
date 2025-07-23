#!/usr/bin/env python3
"""
Whale/Shark Movement Tracker Efficiency Test

Demonstrates the efficiency improvements of the focused whale/shark approach
vs the previous 5-API-call multi-timeframe analysis.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any

# Import the new whale/shark tracker
from services.whale_shark_movement_tracker import WhaleSharkMovementTracker
from api.birdeye_connector import BirdeyeAPI
from utils.logger_setup import LoggerSetup


class EfficiencyComparison:
    """Compare old vs new approach efficiency."""
    
    def __init__(self):
        """Initialize comparison tool."""
        logger_setup = LoggerSetup(__name__)
        self.logger = logger_setup.logger
        
        # Initialize dependencies
        from core.config_manager import ConfigManager
        from core.cache_manager import CacheManager
        from services.rate_limiter_service import RateLimiterService
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        cache_manager = CacheManager(ttl_default=300)
        rate_limiter = RateLimiterService()
        
        # Initialize Birdeye API
        birdeye_config = config.get('BIRDEYE_API', {})
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
        
        self.whale_shark_tracker = WhaleSharkMovementTracker(self.birdeye_api, self.logger)
        
        # Test tokens for comparison
        self.test_tokens = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",  # WIF
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
            "5z3EqYQo9HiCEs3R84RCDMu2n7anpDMxRhdK8PSWmrRC"   # JUP
        ]
    
    async def run_efficiency_comparison(self) -> Dict[str, Any]:
        """
        Run comprehensive efficiency comparison.
        
        Returns:
            Detailed comparison results
        """
        self.logger.info("🚀 Starting Whale/Shark Efficiency Comparison")
        
        comparison_results = {
            "test_timestamp": int(time.time()),
            "tokens_tested": len(self.test_tokens),
            "old_approach_simulation": {},
            "new_approach_results": {},
            "efficiency_metrics": {},
            "cost_analysis": {},
            "insights_comparison": {}
        }
        
        # Test each token with both approaches
        for i, token_address in enumerate(self.test_tokens, 1):
            self.logger.info(f"📊 Testing token {i}/{len(self.test_tokens)}: {token_address}")
            
            try:
                # Simulate old approach (5 API calls)
                old_approach = await self._simulate_old_approach(token_address)
                comparison_results["old_approach_simulation"][token_address] = old_approach
                
                # Test new approach (1-2 API calls)
                new_approach = await self._test_new_approach(token_address)
                comparison_results["new_approach_results"][token_address] = new_approach
                
                self.logger.info(f"✅ Completed comparison for {token_address}")
                
            except Exception as e:
                self.logger.error(f"❌ Error testing {token_address}: {e}")
                continue
        
        # Calculate efficiency metrics
        comparison_results["efficiency_metrics"] = self._calculate_efficiency_metrics(comparison_results)
        comparison_results["cost_analysis"] = self._analyze_cost_efficiency(comparison_results)
        comparison_results["insights_comparison"] = self._compare_insights_quality(comparison_results)
        
        # Generate summary
        summary = self._generate_efficiency_summary(comparison_results)
        comparison_results["summary"] = summary
        
        self.logger.info("🎯 Efficiency comparison completed")
        return comparison_results
    
    async def _simulate_old_approach(self, token_address: str) -> Dict[str, Any]:
        """
        Simulate the old 5-API-call approach for comparison.
        
        Args:
            token_address: Token to analyze
            
        Returns:
            Simulated old approach results
        """
        start_time = time.time()
        
        # Simulate 5 API calls (as in the old approach)
        api_calls = [
            {"timeframe": "1h", "sort_by": "volume", "purpose": "short_term_volume"},
            {"timeframe": "2h", "sort_by": "trade", "purpose": "short_term_activity"},
            {"timeframe": "6h", "sort_by": "volume", "purpose": "medium_term_volume"},
            {"timeframe": "8h", "sort_by": "trade", "purpose": "medium_term_activity"},
            {"timeframe": "24h", "sort_by": "volume", "purpose": "long_term_volume"}
        ]
        
        results = []
        api_failures = 0
        
        for call_config in api_calls:
            try:
                # Make actual API call to get realistic timing
                result = await self.birdeye_api.get_top_traders_optimized(
                    token_address=token_address,
                    time_frame=call_config["timeframe"],
                    sort_by=call_config["sort_by"],
                    limit=10
                )
                
                if result:
                    results.append({
                        "config": call_config,
                        "traders_found": len(result),
                        "success": True
                    })
                else:
                    api_failures += 1
                    results.append({
                        "config": call_config,
                        "traders_found": 0,
                        "success": False
                    })
                    
            except Exception as e:
                api_failures += 1
                results.append({
                    "config": call_config,
                    "error": str(e),
                    "success": False
                })
        
        end_time = time.time()
        
        return {
            "approach": "old_multi_timeframe",
            "api_calls_made": len(api_calls),
            "api_failures": api_failures,
            "success_rate": (len(api_calls) - api_failures) / len(api_calls),
            "execution_time_seconds": round(end_time - start_time, 2),
            "cost_units": len(api_calls) * 30,  # 30 CU per call
            "results": results,
            "complexity_score": 5  # High complexity with 5 calls
        }
    
    async def _test_new_approach(self, token_address: str) -> Dict[str, Any]:
        """
        Test the new whale/shark focused approach.
        
        Args:
            token_address: Token to analyze
            
        Returns:
            New approach results
        """
        start_time = time.time()
        
        # Test both priority levels
        standard_analysis = await self.whale_shark_tracker.analyze_whale_shark_movements(
            token_address, priority_level="normal"
        )
        
        high_priority_analysis = await self.whale_shark_tracker.analyze_whale_shark_movements(
            token_address, priority_level="high"
        )
        
        end_time = time.time()
        
        return {
            "approach": "new_whale_shark_focused",
            "standard_analysis": {
                "api_calls_used": standard_analysis["api_efficiency"]["api_calls_used"],
                "efficiency_rating": standard_analysis["api_efficiency"]["efficiency_rating"],
                "whales_found": standard_analysis["whale_analysis"]["count"],
                "sharks_found": standard_analysis["shark_analysis"]["count"],
                "analysis_valid": standard_analysis["analysis_valid"],
                "whale_volume": standard_analysis["whale_analysis"]["total_volume"],
                "shark_volume": standard_analysis["shark_analysis"]["total_volume"],
                "trading_signals": len(standard_analysis["trading_insights"]["signals"]),
                "market_structure": standard_analysis["market_structure"]["structure_type"]
            },
            "high_priority_analysis": {
                "api_calls_used": high_priority_analysis["api_efficiency"]["api_calls_used"],
                "efficiency_rating": high_priority_analysis["api_efficiency"]["efficiency_rating"],
                "whales_found": high_priority_analysis["whale_analysis"]["count"],
                "sharks_found": high_priority_analysis["shark_analysis"]["count"],
                "analysis_valid": high_priority_analysis["analysis_valid"],
                "whale_volume": high_priority_analysis["whale_analysis"]["total_volume"],
                "shark_volume": high_priority_analysis["shark_analysis"]["total_volume"],
                "trading_signals": len(high_priority_analysis["trading_insights"]["signals"]),
                "market_structure": high_priority_analysis["market_structure"]["structure_type"],
                "has_trend_analysis": "trend_analysis" in high_priority_analysis
            },
            "execution_time_seconds": round(end_time - start_time, 2),
            "max_cost_units": 60,  # 2 calls * 30 CU = 60 CU max
            "min_cost_units": 30,  # 1 call * 30 CU = 30 CU min
            "complexity_score": 2  # Low complexity with 1-2 calls
        }
    
    def _calculate_efficiency_metrics(self, comparison_results: Dict) -> Dict[str, Any]:
        """
        Calculate efficiency metrics comparing old vs new approaches.
        
        Args:
            comparison_results: Raw comparison data
            
        Returns:
            Efficiency metrics
        """
        old_results = comparison_results["old_approach_simulation"]
        new_results = comparison_results["new_approach_results"]
        
        # Calculate averages
        total_tokens = len(old_results)
        
        # Old approach metrics
        old_avg_api_calls = sum(r["api_calls_made"] for r in old_results.values()) / total_tokens
        old_avg_cost = sum(r["cost_units"] for r in old_results.values()) / total_tokens
        old_avg_time = sum(r["execution_time_seconds"] for r in old_results.values()) / total_tokens
        old_avg_success_rate = sum(r["success_rate"] for r in old_results.values()) / total_tokens
        
        # New approach metrics (using standard analysis)
        new_avg_api_calls = sum(r["standard_analysis"]["api_calls_used"] for r in new_results.values()) / total_tokens
        new_avg_cost = 30 * new_avg_api_calls  # 30 CU per call
        new_avg_time = sum(r["execution_time_seconds"] for r in new_results.values()) / total_tokens
        new_success_rate = sum(1 for r in new_results.values() if r["standard_analysis"]["analysis_valid"]) / total_tokens
        
        # Calculate improvements
        api_call_reduction = (old_avg_api_calls - new_avg_api_calls) / old_avg_api_calls
        cost_reduction = (old_avg_cost - new_avg_cost) / old_avg_cost
        time_improvement = (old_avg_time - new_avg_time) / old_avg_time
        
        return {
            "old_approach": {
                "avg_api_calls": round(old_avg_api_calls, 1),
                "avg_cost_units": round(old_avg_cost, 1),
                "avg_execution_time": round(old_avg_time, 2),
                "avg_success_rate": round(old_avg_success_rate, 3)
            },
            "new_approach": {
                "avg_api_calls": round(new_avg_api_calls, 1),
                "avg_cost_units": round(new_avg_cost, 1),
                "avg_execution_time": round(new_avg_time, 2),
                "success_rate": round(new_success_rate, 3)
            },
            "improvements": {
                "api_call_reduction_pct": round(api_call_reduction * 100, 1),
                "cost_reduction_pct": round(cost_reduction * 100, 1),
                "time_improvement_pct": round(time_improvement * 100, 1),
                "reliability_improvement": new_success_rate > old_avg_success_rate
            }
        }
    
    def _analyze_cost_efficiency(self, comparison_results: Dict) -> Dict[str, Any]:
        """
        Analyze cost efficiency improvements.
        
        Args:
            comparison_results: Comparison data
            
        Returns:
            Cost analysis
        """
        old_results = comparison_results["old_approach_simulation"]
        new_results = comparison_results["new_approach_results"]
        
        # Calculate cost per insight
        total_old_cost = sum(r["cost_units"] for r in old_results.values())
        total_new_cost_standard = len(new_results) * 30  # 1 call per token
        total_new_cost_high = len(new_results) * 60      # 2 calls per token
        
        # Count actionable insights
        total_whales_found = sum(r["standard_analysis"]["whales_found"] for r in new_results.values())
        total_sharks_found = sum(r["standard_analysis"]["sharks_found"] for r in new_results.values())
        total_trading_signals = sum(r["standard_analysis"]["trading_signals"] for r in new_results.values())
        
        return {
            "cost_comparison": {
                "old_total_cost": total_old_cost,
                "new_standard_cost": total_new_cost_standard,
                "new_high_priority_cost": total_new_cost_high,
                "cost_savings_standard": total_old_cost - total_new_cost_standard,
                "cost_savings_high": total_old_cost - total_new_cost_high
            },
            "value_analysis": {
                "whales_identified": total_whales_found,
                "sharks_identified": total_sharks_found,
                "trading_signals_generated": total_trading_signals,
                "cost_per_whale": total_new_cost_standard / max(total_whales_found, 1),
                "cost_per_shark": total_new_cost_standard / max(total_sharks_found, 1),
                "cost_per_signal": total_new_cost_standard / max(total_trading_signals, 1)
            },
            "efficiency_rating": "excellent" if total_new_cost_standard < total_old_cost * 0.5 else "good"
        }
    
    def _compare_insights_quality(self, comparison_results: Dict) -> Dict[str, Any]:
        """
        Compare the quality of insights between approaches.
        
        Args:
            comparison_results: Comparison data
            
        Returns:
            Insights quality comparison
        """
        new_results = comparison_results["new_approach_results"]
        
        # Analyze insight quality
        tokens_with_whales = sum(1 for r in new_results.values() if r["standard_analysis"]["whales_found"] > 0)
        tokens_with_sharks = sum(1 for r in new_results.values() if r["standard_analysis"]["sharks_found"] > 0)
        tokens_with_signals = sum(1 for r in new_results.values() if r["standard_analysis"]["trading_signals"] > 0)
        
        # Market structure insights
        structure_types = [r["standard_analysis"]["market_structure"] for r in new_results.values()]
        structure_distribution = {}
        for structure in structure_types:
            structure_distribution[structure] = structure_distribution.get(structure, 0) + 1
        
        return {
            "insight_coverage": {
                "tokens_with_whales": tokens_with_whales,
                "tokens_with_sharks": tokens_with_sharks,
                "tokens_with_trading_signals": tokens_with_signals,
                "whale_detection_rate": tokens_with_whales / len(new_results),
                "shark_detection_rate": tokens_with_sharks / len(new_results),
                "signal_generation_rate": tokens_with_signals / len(new_results)
            },
            "market_structure_insights": structure_distribution,
            "actionability_score": (tokens_with_whales + tokens_with_sharks + tokens_with_signals) / (len(new_results) * 3),
            "focus_benefits": [
                "Clear whale vs shark classification",
                "Directional bias analysis (accumulating/distributing)",
                "Market structure identification",
                "Actionable trading insights",
                "Reduced noise from irrelevant data"
            ]
        }
    
    def _generate_efficiency_summary(self, comparison_results: Dict) -> Dict[str, Any]:
        """
        Generate executive summary of efficiency improvements.
        
        Args:
            comparison_results: Full comparison results
            
        Returns:
            Executive summary
        """
        metrics = comparison_results["efficiency_metrics"]
        cost = comparison_results["cost_analysis"]
        insights = comparison_results["insights_comparison"]
        
        return {
            "executive_summary": {
                "api_efficiency": f"{metrics['improvements']['api_call_reduction_pct']}% reduction in API calls",
                "cost_efficiency": f"{metrics['improvements']['cost_reduction_pct']}% cost reduction",
                "time_efficiency": f"{metrics['improvements']['time_improvement_pct']}% faster execution",
                "insight_quality": f"{insights['actionability_score']:.1%} actionability score"
            },
            "key_benefits": [
                f"Reduced from {metrics['old_approach']['avg_api_calls']} to {metrics['new_approach']['avg_api_calls']} API calls per token",
                f"Cost savings of {cost['cost_comparison']['cost_savings_standard']} CU per batch",
                f"Focused on actionable whale/shark insights",
                f"Clear market structure analysis",
                f"Eliminated noise from irrelevant timeframes"
            ],
            "recommendation": {
                "approach": "new_whale_shark_focused",
                "priority_usage": "Use 'high' priority only for tokens with >$1M volume",
                "expected_savings": f"{metrics['improvements']['cost_reduction_pct']}% cost reduction",
                "confidence_level": "high"
            }
        }


async def main():
    """Run the efficiency comparison test."""
    print("🚀 Starting Whale/Shark Efficiency Comparison Test")
    print("=" * 60)
    
    comparison = EfficiencyComparison()
    
    try:
        # Run comprehensive comparison
        results = await comparison.run_efficiency_comparison()
        
        # Display summary
        summary = results["summary"]
        print("\n📊 EFFICIENCY COMPARISON RESULTS")
        print("=" * 60)
        
        print(f"\n🎯 Executive Summary:")
        for key, value in summary["executive_summary"].items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n✅ Key Benefits:")
        for benefit in summary["key_benefits"]:
            print(f"  • {benefit}")
        
        print(f"\n💡 Recommendation:")
        rec = summary["recommendation"]
        print(f"  • Approach: {rec['approach']}")
        print(f"  • Priority Usage: {rec['priority_usage']}")
        print(f"  • Expected Savings: {rec['expected_savings']}")
        print(f"  • Confidence: {rec['confidence_level']}")
        
        # Display detailed metrics
        metrics = results["efficiency_metrics"]
        print(f"\n📈 Detailed Metrics:")
        print(f"  Old Approach: {metrics['old_approach']['avg_api_calls']} calls, {metrics['old_approach']['avg_cost_units']} CU")
        print(f"  New Approach: {metrics['new_approach']['avg_api_calls']} calls, {metrics['new_approach']['avg_cost_units']} CU")
        print(f"  Improvements: {metrics['improvements']['api_call_reduction_pct']}% fewer calls, {metrics['improvements']['cost_reduction_pct']}% cost reduction")
        
        # Save detailed results
        output_file = f"scripts/results/whale_shark_efficiency_comparison_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        print("\n🎉 Efficiency comparison completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during efficiency comparison: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())