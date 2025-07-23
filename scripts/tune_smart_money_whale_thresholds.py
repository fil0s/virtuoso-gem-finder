#!/usr/bin/env python3

"""
Smart Money Whale Strategy Threshold Tuning System

This script progressively scales down thresholds in descending order to find the optimal
balance between selectivity and opportunity discovery for the SmartMoneyWhaleStrategy.

Features:
- 5 threshold levels from strictest to most relaxed
- Smart scaling based on parameter types
- Progressive execution with detailed analysis
- Performance tracking and optimization insights
- Configuration export for production use
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.strategies.smart_money_whale_strategy import SmartMoneyWhaleStrategy
from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from services.logger_setup import LoggerSetup


@dataclass
class ThresholdLevel:
    """Represents a threshold configuration level."""
    name: str
    description: str
    criteria: Dict[str, Any]
    risk_management: Dict[str, Any]
    selectivity_level: str  # "maximum", "high", "medium", "low", "minimum"


class ThresholdTuner:
    """Tunes Smart Money Whale Strategy thresholds systematically."""
    
    def __init__(self):
        # Setup enhanced logging
        self.logger = LoggerSetup(__name__)
        
        # Tracking data
        self.tuning_results = []
        self.api_call_count = 0
        self.total_execution_time = 0
        
        # Define threshold levels
        self.threshold_levels = self._define_threshold_levels()
        
        self.logger.info("🎯 Smart Money Whale Strategy Threshold Tuner Initialized")
    
    def _define_threshold_levels(self) -> List[ThresholdLevel]:
        """Define 5 threshold levels in descending order of strictness."""
        
        # Base (current) thresholds - Level 1 (Strictest)
        base_criteria = {
            "min_whale_count": 2,
            "min_whale_volume": 500000,
            "whale_confidence_threshold": 0.6,
            "min_smart_traders": 3,
            "smart_money_skill_threshold": 0.65,
            "smart_money_confidence_threshold": 0.7,
            "confluence_bonus_multiplier": 1.5,
            "min_confluence_score": 0.8,
            "max_whale_concentration": 0.4,
            "min_whale_diversity": 3,
            "whale_directional_bias_threshold": 0.7
        }
        
        base_risk_management = {
            "max_allocation_percentage": 7.5,
            "suspicious_volume_multiplier": 5.0,
            "min_holder_distribution": 0.5,
            "max_concentration_pct": 70.0,
            "min_dexs_with_liquidity": 3,
            "min_days_since_listing": 2
        }
        
        levels = []
        
        # Level 1: Maximum Selectivity (Current)
        levels.append(ThresholdLevel(
            name="Level 1: Maximum Selectivity",
            description="Ultra-strict criteria for highest conviction plays only",
            criteria=base_criteria.copy(),
            risk_management=base_risk_management.copy(),
            selectivity_level="maximum"
        ))
        
        # Level 2: High Selectivity (20% relaxed)
        level2_criteria = base_criteria.copy()
        level2_criteria.update({
            "min_whale_count": 2,  # Keep same (minimum viable)
            "min_whale_volume": int(500000 * 0.8),  # 400k
            "whale_confidence_threshold": 0.6 * 0.9,  # 0.54
            "min_smart_traders": 2,  # Reduce by 1
            "smart_money_skill_threshold": 0.65 * 0.9,  # 0.585
            "smart_money_confidence_threshold": 0.7 * 0.9,  # 0.63
            "confluence_bonus_multiplier": 1.5 * 0.95,  # 1.425
            "min_confluence_score": 0.8 * 0.85,  # 0.68
            "max_whale_concentration": 0.4 * 1.1,  # 0.44 (allow slightly more concentration)
            "min_whale_diversity": 2,  # Reduce by 1
            "whale_directional_bias_threshold": 0.7 * 0.9  # 0.63
        })
        
        level2_risk = base_risk_management.copy()
        level2_risk.update({
            "max_allocation_percentage": 7.5 * 1.1,  # 8.25%
            "min_holder_distribution": 0.5 * 0.9,  # 0.45
            "max_concentration_pct": 70.0 * 1.05,  # 73.5%
            "min_dexs_with_liquidity": 2,  # Reduce by 1
            "min_days_since_listing": 1  # Reduce by 1
        })
        
        levels.append(ThresholdLevel(
            name="Level 2: High Selectivity",
            description="Slightly relaxed criteria for quality opportunities",
            criteria=level2_criteria,
            risk_management=level2_risk,
            selectivity_level="high"
        ))
        
        # Level 3: Medium Selectivity (40% relaxed)
        level3_criteria = base_criteria.copy()
        level3_criteria.update({
            "min_whale_count": 1,  # Minimum possible
            "min_whale_volume": int(500000 * 0.6),  # 300k
            "whale_confidence_threshold": 0.6 * 0.8,  # 0.48
            "min_smart_traders": 2,  # Keep at reduced level
            "smart_money_skill_threshold": 0.65 * 0.8,  # 0.52
            "smart_money_confidence_threshold": 0.7 * 0.8,  # 0.56
            "confluence_bonus_multiplier": 1.5 * 0.9,  # 1.35
            "min_confluence_score": 0.8 * 0.7,  # 0.56
            "max_whale_concentration": 0.4 * 1.25,  # 0.5
            "min_whale_diversity": 2,  # Keep at reduced level
            "whale_directional_bias_threshold": 0.7 * 0.8  # 0.56
        })
        
        level3_risk = base_risk_management.copy()
        level3_risk.update({
            "max_allocation_percentage": 7.5 * 1.2,  # 9%
            "min_holder_distribution": 0.5 * 0.8,  # 0.4
            "max_concentration_pct": 70.0 * 1.1,  # 77%
            "min_dexs_with_liquidity": 2,  # Keep reduced
            "min_days_since_listing": 1  # Keep reduced
        })
        
        levels.append(ThresholdLevel(
            name="Level 3: Medium Selectivity",
            description="Balanced criteria for broader opportunity capture",
            criteria=level3_criteria,
            risk_management=level3_risk,
            selectivity_level="medium"
        ))
        
        # Level 4: Low Selectivity (60% relaxed)
        level4_criteria = base_criteria.copy()
        level4_criteria.update({
            "min_whale_count": 1,  # Minimum
            "min_whale_volume": int(500000 * 0.4),  # 200k
            "whale_confidence_threshold": 0.6 * 0.7,  # 0.42
            "min_smart_traders": 1,  # Minimum viable
            "smart_money_skill_threshold": 0.65 * 0.7,  # 0.455
            "smart_money_confidence_threshold": 0.7 * 0.7,  # 0.49
            "confluence_bonus_multiplier": 1.5 * 0.85,  # 1.275
            "min_confluence_score": 0.8 * 0.6,  # 0.48
            "max_whale_concentration": 0.4 * 1.4,  # 0.56
            "min_whale_diversity": 1,  # Minimum
            "whale_directional_bias_threshold": 0.7 * 0.7  # 0.49
        })
        
        level4_risk = base_risk_management.copy()
        level4_risk.update({
            "max_allocation_percentage": 7.5 * 1.3,  # 9.75%
            "min_holder_distribution": 0.5 * 0.7,  # 0.35
            "max_concentration_pct": 70.0 * 1.15,  # 80.5%
            "min_dexs_with_liquidity": 1,  # Minimum
            "min_days_since_listing": 0  # No minimum
        })
        
        levels.append(ThresholdLevel(
            name="Level 4: Low Selectivity",
            description="Relaxed criteria for maximum opportunity discovery",
            criteria=level4_criteria,
            risk_management=level4_risk,
            selectivity_level="low"
        ))
        
        # Level 5: Minimum Viable (80% relaxed)
        level5_criteria = base_criteria.copy()
        level5_criteria.update({
            "min_whale_count": 1,  # Minimum
            "min_whale_volume": int(500000 * 0.2),  # 100k
            "whale_confidence_threshold": 0.6 * 0.6,  # 0.36
            "min_smart_traders": 1,  # Minimum
            "smart_money_skill_threshold": 0.65 * 0.6,  # 0.39
            "smart_money_confidence_threshold": 0.7 * 0.6,  # 0.42
            "confluence_bonus_multiplier": 1.5 * 0.8,  # 1.2
            "min_confluence_score": 0.8 * 0.5,  # 0.4
            "max_whale_concentration": 0.4 * 1.5,  # 0.6
            "min_whale_diversity": 1,  # Minimum
            "whale_directional_bias_threshold": 0.7 * 0.6  # 0.42
        })
        
        level5_risk = base_risk_management.copy()
        level5_risk.update({
            "max_allocation_percentage": 7.5 * 1.4,  # 10.5%
            "min_holder_distribution": 0.5 * 0.6,  # 0.3
            "max_concentration_pct": 70.0 * 1.2,  # 84%
            "min_dexs_with_liquidity": 1,  # Minimum
            "min_days_since_listing": 0  # No minimum
        })
        
        levels.append(ThresholdLevel(
            name="Level 5: Minimum Viable",
            description="Most relaxed criteria for comprehensive market scanning",
            criteria=level5_criteria,
            risk_management=level5_risk,
            selectivity_level="minimum"
        ))
        
        return levels
    
    async def run_threshold_tuning(self, stop_on_first_success: bool = False) -> Dict[str, Any]:
        """Run threshold tuning across all levels."""
        
        self.logger.info("\n🎯 SMART MONEY WHALE THRESHOLD TUNING")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Testing {len(self.threshold_levels)} threshold levels")
        self.logger.info(f"🛑 Stop on first success: {stop_on_first_success}")
        
        start_time = time.time()
        
        # Initialize services
        birdeye_api = await self._initialize_services()
        
        try:
            # Test each threshold level
            for i, level in enumerate(self.threshold_levels, 1):
                self.logger.info(f"\n🔍 TESTING {level.name}")
                self.logger.info("=" * 50)
                self.logger.info(f"📝 {level.description}")
                self.logger.info(f"🎚️ Selectivity: {level.selectivity_level.upper()}")
                
                # Run strategy with this threshold level
                level_result = await self._test_threshold_level(level, birdeye_api, i)
                self.tuning_results.append(level_result)
                
                # Display immediate results
                self._display_level_results(level_result)
                
                # Check if we should stop
                if stop_on_first_success and level_result["tokens_found"] > 0:
                    self.logger.info(f"\n✅ SUCCESS! Found {level_result['tokens_found']} tokens at {level.name}")
                    self.logger.info("🛑 Stopping as requested (stop_on_first_success=True)")
                    break
            
            # Generate comprehensive analysis
            self.total_execution_time = time.time() - start_time
            analysis = self._generate_comprehensive_analysis()
            
            # Save results
            await self._save_tuning_results(analysis)
            
            return analysis
            
        finally:
            await birdeye_api.close()
            self.logger.info("✅ API connections properly closed")
    
    async def _initialize_services(self) -> BirdeyeAPI:
        """Initialize required services."""
        
        self.logger.info("🔧 Initializing services...")
        
        # Check API key
        api_key = os.getenv('BIRDEYE_API_KEY')
        if not api_key:
            raise ValueError("BIRDEYE_API_KEY environment variable not set")
        
        # Initialize services
        cache_manager = CacheManager()
        rate_limiter = RateLimiterService()
        
        # Create config for BirdeyeAPI
        config = {
            'api_key': api_key,
            'base_url': 'https://public-api.birdeye.so',
            'rate_limit': 100,
            'request_timeout_seconds': 20,
            'cache_ttl_default_seconds': 300,
            'cache_ttl_error_seconds': 60,
            'max_retries': 3,
            'backoff_factor': 2
        }
        
        # Create logger for BirdeyeAPI
        birdeye_logger = LoggerSetup("BirdeyeAPI")
        
        birdeye_api = BirdeyeAPI(config, birdeye_logger, cache_manager, rate_limiter)
        
        self.logger.info("✅ Services initialized successfully")
        return birdeye_api
    
    async def _test_threshold_level(self, level: ThresholdLevel, birdeye_api: BirdeyeAPI, level_num: int) -> Dict[str, Any]:
        """Test a specific threshold level."""
        
        level_start_time = time.time()
        scan_id = f"threshold_tune_L{level_num}_{int(time.time())}"
        
        try:
            # Create strategy with this threshold level
            strategy = SmartMoneyWhaleStrategy()
            
            # Override the strategy's criteria and risk management
            strategy.whale_smart_money_criteria.update(level.criteria)
            strategy.risk_management.update(level.risk_management)
            
            self.logger.info(f"🎯 Testing with criteria:")
            for key, value in level.criteria.items():
                self.logger.info(f"   {key}: {value}")
            
            # Track API calls for this level
            initial_api_count = self.api_call_count
            
            # Run discovery
            tokens = await strategy.execute(birdeye_api, scan_id)
            
            # Calculate metrics
            level_duration = time.time() - level_start_time
            level_api_calls = self.api_call_count - initial_api_count
            
            # Analyze token quality if any found
            quality_metrics = self._analyze_token_quality(tokens) if tokens else {}
            
            result = {
                "level_name": level.name,
                "level_number": level_num,
                "selectivity_level": level.selectivity_level,
                "description": level.description,
                "criteria": level.criteria,
                "risk_management": level.risk_management,
                "execution_time": level_duration,
                "api_calls": level_api_calls,
                "tokens_found": len(tokens),
                "tokens": tokens[:5] if tokens else [],  # Store top 5 for analysis
                "quality_metrics": quality_metrics,
                "success": len(tokens) > 0,
                "scan_id": scan_id
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error testing {level.name}: {e}")
            return {
                "level_name": level.name,
                "level_number": level_num,
                "selectivity_level": level.selectivity_level,
                "error": str(e),
                "success": False,
                "tokens_found": 0,
                "execution_time": time.time() - level_start_time
            }
    
    def _analyze_token_quality(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the quality of discovered tokens."""
        
        if not tokens:
            return {}
        
        # Calculate quality metrics
        total_whales = sum(len(t.get('whale_analysis', {}).get('whales', [])) for t in tokens)
        total_smart_traders = sum(t.get('smart_money_analysis', {}).get('skill_metrics', {}).get('skilled_count', 0) for t in tokens)
        avg_confluence = sum(t.get('confluence_score', 0) for t in tokens) / len(tokens)
        avg_combined_score = sum(t.get('combined_whale_smart_money_score', 0) for t in tokens) / len(tokens)
        
        # Risk distribution
        risk_levels = [t.get('strategy_analysis', {}).get('risk_assessment', 'unknown') for t in tokens]
        risk_distribution = {level: risk_levels.count(level) for level in set(risk_levels)}
        
        # Conviction distribution
        conviction_levels = [t.get('strategy_analysis', {}).get('conviction_level', 'unknown') for t in tokens]
        conviction_distribution = {level: conviction_levels.count(level) for level in set(conviction_levels)}
        
        return {
            "total_whales": total_whales,
            "total_smart_traders": total_smart_traders,
            "avg_confluence_score": avg_confluence,
            "avg_combined_score": avg_combined_score,
            "avg_whales_per_token": total_whales / len(tokens) if tokens else 0,
            "avg_smart_traders_per_token": total_smart_traders / len(tokens) if tokens else 0,
            "risk_distribution": risk_distribution,
            "conviction_distribution": conviction_distribution,
            "quality_score": self._calculate_quality_score(avg_confluence, avg_combined_score, risk_distribution, conviction_distribution)
        }
    
    def _calculate_quality_score(self, avg_confluence: float, avg_combined_score: float, 
                               risk_dist: Dict[str, int], conviction_dist: Dict[str, int]) -> float:
        """Calculate an overall quality score for the token set."""
        
        # Base score from confluence and combined scores
        base_score = (avg_confluence * 50) + (avg_combined_score / 100 * 30)
        
        # Risk adjustment (lower risk = higher score)
        total_tokens = sum(risk_dist.values())
        if total_tokens > 0:
            low_risk_ratio = risk_dist.get('low', 0) / total_tokens
            medium_risk_ratio = risk_dist.get('medium', 0) / total_tokens
            high_risk_ratio = risk_dist.get('high', 0) / total_tokens
            
            risk_adjustment = (low_risk_ratio * 10) + (medium_risk_ratio * 5) - (high_risk_ratio * 5)
        else:
            risk_adjustment = 0
        
        # Conviction adjustment (higher conviction = higher score)
        if total_tokens > 0:
            high_conviction_ratio = conviction_dist.get('high', 0) / total_tokens
            medium_conviction_ratio = conviction_dist.get('medium', 0) / total_tokens
            
            conviction_adjustment = (high_conviction_ratio * 10) + (medium_conviction_ratio * 5)
        else:
            conviction_adjustment = 0
        
        return min(100, max(0, base_score + risk_adjustment + conviction_adjustment))
    
    def _display_level_results(self, result: Dict[str, Any]):
        """Display results for a threshold level."""
        
        if result.get("success", False):
            self.logger.info(f"✅ SUCCESS: Found {result['tokens_found']} tokens")
            self.logger.info(f"⏱️ Execution time: {result['execution_time']:.2f}s")
            self.logger.info(f"🌐 API calls: {result['api_calls']}")
            
            quality = result.get("quality_metrics", {})
            if quality:
                self.logger.info(f"🏆 Quality Score: {quality.get('quality_score', 0):.1f}/100")
                self.logger.info(f"🐋 Avg Whales/Token: {quality.get('avg_whales_per_token', 0):.1f}")
                self.logger.info(f"🧠 Avg Smart Traders/Token: {quality.get('avg_smart_traders_per_token', 0):.1f}")
                self.logger.info(f"🤝 Avg Confluence: {quality.get('avg_confluence_score', 0):.3f}")
        else:
            if "error" in result:
                self.logger.error(f"❌ ERROR: {result['error']}")
            else:
                self.logger.warning(f"❌ No tokens found")
                self.logger.info(f"⏱️ Execution time: {result['execution_time']:.2f}s")
    
    def _generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive analysis of all threshold levels."""
        
        self.logger.info("\n📊 COMPREHENSIVE THRESHOLD ANALYSIS")
        self.logger.info("=" * 60)
        
        # Find successful levels
        successful_levels = [r for r in self.tuning_results if r.get("success", False)]
        
        # Performance analysis
        if successful_levels:
            # Best performing level by quality
            best_quality = max(successful_levels, key=lambda x: x.get("quality_metrics", {}).get("quality_score", 0))
            
            # Most efficient level (tokens per API call)
            most_efficient = max(successful_levels, key=lambda x: x["tokens_found"] / max(1, x.get("api_calls", 1)))
            
            # Fastest level
            fastest = min(successful_levels, key=lambda x: x["execution_time"])
            
            self.logger.info(f"🏆 BEST QUALITY: {best_quality['level_name']}")
            self.logger.info(f"   Quality Score: {best_quality.get('quality_metrics', {}).get('quality_score', 0):.1f}/100")
            self.logger.info(f"   Tokens Found: {best_quality['tokens_found']}")
            
            self.logger.info(f"\n⚡ MOST EFFICIENT: {most_efficient['level_name']}")
            self.logger.info(f"   Tokens/API Call: {most_efficient['tokens_found'] / max(1, most_efficient.get('api_calls', 1)):.3f}")
            self.logger.info(f"   Total API Calls: {most_efficient.get('api_calls', 0)}")
            
            self.logger.info(f"\n🚀 FASTEST: {fastest['level_name']}")
            self.logger.info(f"   Execution Time: {fastest['execution_time']:.2f}s")
            self.logger.info(f"   Tokens Found: {fastest['tokens_found']}")
            
        else:
            self.logger.warning("❌ No successful threshold levels found")
            self.logger.info("💡 Consider further relaxing criteria or checking market conditions")
        
        # Threshold effectiveness analysis
        self._analyze_threshold_effectiveness()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_execution_time": self.total_execution_time,
            "levels_tested": len(self.tuning_results),
            "successful_levels": len(successful_levels),
            "results": self.tuning_results,
            "best_performers": {
                "best_quality": best_quality if successful_levels else None,
                "most_efficient": most_efficient if successful_levels else None,
                "fastest": fastest if successful_levels else None
            },
            "recommendations": recommendations,
            "summary": {
                "success_rate": len(successful_levels) / len(self.tuning_results) if self.tuning_results else 0,
                "total_tokens_found": sum(r.get("tokens_found", 0) for r in self.tuning_results),
                "avg_execution_time": sum(r.get("execution_time", 0) for r in self.tuning_results) / len(self.tuning_results) if self.tuning_results else 0
            }
        }
        
        return analysis
    
    def _analyze_threshold_effectiveness(self):
        """Analyze which thresholds are most effective/restrictive."""
        
        self.logger.info(f"\n🔍 THRESHOLD EFFECTIVENESS ANALYSIS")
        self.logger.info("-" * 50)
        
        # Compare success rates across selectivity levels
        selectivity_performance = {}
        for result in self.tuning_results:
            level = result.get("selectivity_level", "unknown")
            if level not in selectivity_performance:
                selectivity_performance[level] = {"attempts": 0, "successes": 0, "total_tokens": 0}
            
            selectivity_performance[level]["attempts"] += 1
            if result.get("success", False):
                selectivity_performance[level]["successes"] += 1
                selectivity_performance[level]["total_tokens"] += result.get("tokens_found", 0)
        
        for level, perf in selectivity_performance.items():
            success_rate = perf["successes"] / perf["attempts"] if perf["attempts"] > 0 else 0
            avg_tokens = perf["total_tokens"] / perf["successes"] if perf["successes"] > 0 else 0
            
            self.logger.info(f"📊 {level.upper()}: {success_rate:.1%} success rate, {avg_tokens:.1f} avg tokens when successful")
    
    def _generate_recommendations(self) -> Dict[str, Any]:
        """Generate optimization recommendations."""
        
        successful_levels = [r for r in self.tuning_results if r.get("success", False)]
        
        if not successful_levels:
            return {
                "status": "no_success",
                "recommendation": "Consider further relaxing thresholds or checking market conditions",
                "suggested_actions": [
                    "Check if API is returning data correctly",
                    "Verify whale and smart money services are functioning",
                    "Consider market conditions (low activity periods)",
                    "Test with different time frames",
                    "Review base token filtering criteria"
                ]
            }
        
        # Find optimal threshold level
        best_quality = max(successful_levels, key=lambda x: x.get("quality_metrics", {}).get("quality_score", 0))
        
        return {
            "status": "success",
            "optimal_level": best_quality["level_name"],
            "optimal_criteria": best_quality["criteria"],
            "optimal_risk_management": best_quality["risk_management"],
            "expected_performance": {
                "tokens_per_scan": best_quality["tokens_found"],
                "quality_score": best_quality.get("quality_metrics", {}).get("quality_score", 0),
                "execution_time": best_quality["execution_time"],
                "api_calls": best_quality.get("api_calls", 0)
            },
            "tuning_insights": [
                f"Optimal selectivity level: {best_quality['selectivity_level']}",
                f"Quality vs quantity balance achieved at Level {best_quality['level_number']}",
                f"Expected {best_quality['tokens_found']} tokens per scan with {best_quality.get('quality_metrics', {}).get('quality_score', 0):.1f}/100 quality",
                "Consider using this configuration for production"
            ]
        }
    
    async def _save_tuning_results(self, analysis: Dict[str, Any]):
        """Save tuning results to file."""
        
        # Save comprehensive results
        results_dir = Path("scripts/results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = int(time.time())
        results_file = results_dir / f"threshold_tuning_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        self.logger.info(f"\n💾 Results saved to: {results_file}")
        
        # Save optimal configuration if found
        if analysis["recommendations"]["status"] == "success":
            config_file = results_dir / f"optimal_whale_config_{timestamp}.json"
            optimal_config = {
                "criteria": analysis["recommendations"]["optimal_criteria"],
                "risk_management": analysis["recommendations"]["optimal_risk_management"],
                "performance_metrics": analysis["recommendations"]["expected_performance"],
                "generated_at": datetime.now().isoformat(),
                "source": "threshold_tuning_analysis"
            }
            
            with open(config_file, 'w') as f:
                json.dump(optimal_config, f, indent=2)
            
            self.logger.info(f"⚙️ Optimal config saved to: {config_file}")


async def main():
    """Main execution function."""
    
    tuner = ThresholdTuner()
    
    try:
        # Run threshold tuning
        # Set stop_on_first_success=True to stop at first successful level
        # Set stop_on_first_success=False to test all levels for comprehensive analysis
        analysis = await tuner.run_threshold_tuning(stop_on_first_success=False)
        
        print("\n🎉 THRESHOLD TUNING COMPLETE!")
        print(f"📊 Tested {analysis['levels_tested']} levels")
        print(f"✅ {analysis['successful_levels']} successful levels")
        print(f"🎯 Total tokens found: {analysis['summary']['total_tokens_found']}")
        
        if analysis["recommendations"]["status"] == "success":
            print(f"\n🏆 OPTIMAL CONFIGURATION FOUND:")
            print(f"   Level: {analysis['recommendations']['optimal_level']}")
            print(f"   Expected tokens per scan: {analysis['recommendations']['expected_performance']['tokens_per_scan']}")
            print(f"   Quality score: {analysis['recommendations']['expected_performance']['quality_score']:.1f}/100")
        
    except KeyboardInterrupt:
        tuner.logger.info("\n🛑 Threshold tuning interrupted by user")
        
    except Exception as e:
        tuner.logger.error(f"❌ Threshold tuning failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 