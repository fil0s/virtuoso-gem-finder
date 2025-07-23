#!/usr/bin/env python3
"""
Strategy Filter Relaxation Analysis & Implementation

This script analyzes why 5 out of 6 strategies found 0 tokens and provides
systematic solutions for relaxing overly restrictive filters.

Key Issues Identified:
1. API parameters too restrictive (high min_liquidity, min_volume, min_holder)
2. Processing filters too strict (suspicious volume multipliers, concentration limits)
3. Consecutive appearances thresholds too high
4. Cross-timeframe analysis requiring too much confluence
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.strategies import (
    VolumeMomentumStrategy,
    RecentListingsStrategy, 
    PriceMomentumStrategy,
    LiquidityGrowthStrategy,
    HighTradingActivityStrategy,
    SmartMoneyWhaleStrategy
)


@dataclass
class FilterAnalysis:
    """Analysis of strategy filter restrictiveness."""
    strategy_name: str
    current_params: Dict[str, Any]
    restrictive_params: List[str]
    recommended_relaxation: Dict[str, Any]
    relaxation_rationale: Dict[str, str]
    expected_improvement: str


class StrategyFilterAnalyzer:
    """Analyzes and provides solutions for overly restrictive strategy filters."""
    
    def __init__(self):
        self.analysis_results = []
        
        # Market context for realistic thresholds
        self.market_context = {
            "typical_new_token_liquidity": 50000,      # $50K typical for new tokens
            "typical_new_token_volume": 25000,         # $25K typical daily volume
            "typical_new_token_holders": 100,          # 100 holders typical start
            "established_token_liquidity": 500000,     # $500K for established
            "established_token_volume": 200000,        # $200K for established
            "established_token_holders": 2000,         # 2K holders for established
        }
    
    def analyze_all_strategies(self) -> List[FilterAnalysis]:
        """Analyze all strategies for overly restrictive filters."""
        
        strategies = [
            VolumeMomentumStrategy(),
            RecentListingsStrategy(),
            PriceMomentumStrategy(),
            LiquidityGrowthStrategy(),
            HighTradingActivityStrategy(),
            SmartMoneyWhaleStrategy()
        ]
        
        print("🔍 ANALYZING STRATEGY FILTER RESTRICTIVENESS")
        print("=" * 80)
        
        for strategy in strategies:
            analysis = self._analyze_strategy_filters(strategy)
            self.analysis_results.append(analysis)
            self._print_strategy_analysis(analysis)
        
        return self.analysis_results
    
    def _analyze_strategy_filters(self, strategy) -> FilterAnalysis:
        """Analyze individual strategy for restrictive filters."""
        
        current_params = strategy.api_parameters.copy()
        restrictive_params = []
        recommended_relaxation = {}
        relaxation_rationale = {}
        
        strategy_name = strategy.name
        
        # Analyze API parameters for restrictiveness
        if "min_liquidity" in current_params:
            current_liq = current_params["min_liquidity"]
            if strategy_name == "Recent Listings Strategy":
                # New tokens need lower liquidity threshold
                if current_liq > self.market_context["typical_new_token_liquidity"]:
                    restrictive_params.append("min_liquidity")
                    recommended_relaxation["min_liquidity"] = 50000  # $50K
                    relaxation_rationale["min_liquidity"] = "New tokens typically start with $50K liquidity"
            else:
                # Established tokens, but still too high
                if current_liq > 200000:
                    restrictive_params.append("min_liquidity")
                    recommended_relaxation["min_liquidity"] = max(100000, current_liq * 0.5)
                    relaxation_rationale["min_liquidity"] = "50% reduction to capture more opportunities"
        
        if "min_volume_24h_usd" in current_params:
            current_vol = current_params["min_volume_24h_usd"]
            if strategy_name == "Recent Listings Strategy":
                if current_vol > self.market_context["typical_new_token_volume"]:
                    restrictive_params.append("min_volume_24h_usd")
                    recommended_relaxation["min_volume_24h_usd"] = 25000  # $25K
                    relaxation_rationale["min_volume_24h_usd"] = "New tokens need lower volume threshold"
            else:
                if current_vol > 75000:
                    restrictive_params.append("min_volume_24h_usd")
                    recommended_relaxation["min_volume_24h_usd"] = max(25000, current_vol * 0.5)
                    relaxation_rationale["min_volume_24h_usd"] = "50% reduction for broader discovery"
        
        if "min_holder" in current_params:
            current_holders = current_params["min_holder"]
            if strategy_name == "Recent Listings Strategy":
                if current_holders > self.market_context["typical_new_token_holders"]:
                    restrictive_params.append("min_holder")
                    recommended_relaxation["min_holder"] = 100
                    relaxation_rationale["min_holder"] = "New tokens start with ~100 holders"
            else:
                if current_holders > 500:
                    restrictive_params.append("min_holder")
                    recommended_relaxation["min_holder"] = max(200, current_holders * 0.4)
                    relaxation_rationale["min_holder"] = "60% reduction for broader market coverage"
        
        if "min_trade_24h_count" in current_params:
            current_trades = current_params["min_trade_24h_count"]
            if current_trades > 300:
                restrictive_params.append("min_trade_24h_count")
                recommended_relaxation["min_trade_24h_count"] = max(200, current_trades * 0.6)
                relaxation_rationale["min_trade_24h_count"] = "40% reduction for active but smaller tokens"
        
        if "min_market_cap" in current_params:
            current_mcap = current_params["min_market_cap"]
            if current_mcap > 500000:
                restrictive_params.append("min_market_cap")
                recommended_relaxation["min_market_cap"] = max(100000, current_mcap * 0.5)
                relaxation_rationale["min_market_cap"] = "Lower market cap for early discovery"
        
        # Analyze consecutive appearances (very restrictive)
        consecutive = strategy.min_consecutive_appearances
        if consecutive > 2:
            restrictive_params.append("min_consecutive_appearances")
            recommended_relaxation["min_consecutive_appearances"] = max(1, consecutive - 1)
            relaxation_rationale["min_consecutive_appearances"] = f"Reduce from {consecutive} to {max(1, consecutive - 1)} for faster discovery"
        
        # Analyze processing filters
        risk_mgmt = strategy.risk_management
        if risk_mgmt.get("suspicious_volume_multiplier", 0) < 5.0:
            restrictive_params.append("suspicious_volume_multiplier")
            recommended_relaxation["suspicious_volume_multiplier"] = 5.0
            relaxation_rationale["suspicious_volume_multiplier"] = "Increase to 5x to allow legitimate volume spikes"
        
        if risk_mgmt.get("min_days_since_listing", 0) > 1:
            restrictive_params.append("min_days_since_listing")
            recommended_relaxation["min_days_since_listing"] = max(0, risk_mgmt.get("min_days_since_listing", 2) - 1)
            relaxation_rationale["min_days_since_listing"] = "Reduce minimum days for earlier discovery"
        
        # Determine expected improvement
        if len(restrictive_params) >= 5:
            expected_improvement = "Major improvement expected (5+ restrictive filters)"
        elif len(restrictive_params) >= 3:
            expected_improvement = "Significant improvement expected (3-4 restrictive filters)"
        elif len(restrictive_params) >= 1:
            expected_improvement = "Moderate improvement expected (1-2 restrictive filters)"
        else:
            expected_improvement = "Minimal improvement (filters already reasonable)"
        
        return FilterAnalysis(
            strategy_name=strategy_name,
            current_params=current_params,
            restrictive_params=restrictive_params,
            recommended_relaxation=recommended_relaxation,
            relaxation_rationale=relaxation_rationale,
            expected_improvement=expected_improvement
        )
    
    def _print_strategy_analysis(self, analysis: FilterAnalysis):
        """Print detailed analysis for a strategy."""
        
        print(f"\n📊 {analysis.strategy_name}")
        print("-" * 50)
        
        if not analysis.restrictive_params:
            print("✅ Filters appear reasonable - no major restrictions identified")
            return
        
        print(f"🚨 Found {len(analysis.restrictive_params)} restrictive parameters:")
        
        for param in analysis.restrictive_params:
            current_val = analysis.current_params.get(param, "N/A")
            recommended_val = analysis.recommended_relaxation.get(param, "N/A")
            rationale = analysis.relaxation_rationale.get(param, "")
            
            print(f"   • {param}:")
            print(f"     Current: {current_val}")
            print(f"     Recommended: {recommended_val}")
            print(f"     Rationale: {rationale}")
        
        print(f"\n💡 {analysis.expected_improvement}")


def main():
    """Main function to analyze strategy filters."""
    
    analyzer = StrategyFilterAnalyzer()
    analyses = analyzer.analyze_all_strategies()
    
    # Print summary
    print(f"\n📋 SUMMARY OF FILTER RESTRICTIVENESS")
    print("=" * 80)
    
    total_restrictive = sum(len(a.restrictive_params) for a in analyses)
    strategies_needing_help = sum(1 for a in analyses if a.restrictive_params)
    
    print(f"🔍 Analysis Results:")
    print(f"   • Total restrictive parameters found: {total_restrictive}")
    print(f"   • Strategies needing filter relaxation: {strategies_needing_help}/6")
    
    print(f"\n🎯 Expected Improvements:")
    for analysis in analyses:
        if analysis.restrictive_params:
            print(f"   • {analysis.strategy_name}: {analysis.expected_improvement}")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Run specific relaxation tests for each strategy")
    print(f"   2. Implement gradual filter relaxation")
    print(f"   3. Monitor token discovery improvements")


if __name__ == "__main__":
    main() 