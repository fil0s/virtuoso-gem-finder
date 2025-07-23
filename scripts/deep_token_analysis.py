#!/usr/bin/env python3
"""
Deep Token Analysis Tool

This script provides comprehensive, in-depth analysis of specific tokens including:
- Detailed trending analysis with momentum calculations
- Smart money detection with trader quality scoring
- Holder distribution analysis with concentration metrics
- Risk assessment with multiple factors
- Market data analysis
- Comparative scoring breakdown
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.birdeye_connector import BirdeyeAPI
from services.trending_token_monitor import TrendingTokenMonitor
from services.smart_money_detector import SmartMoneyDetector
from services.holder_distribution_analyzer import HolderDistributionAnalyzer
from utils.env_loader import load_environment
import yaml

# Test token addresses
TEST_TOKENS = [
    "9b1BzC1af9gQBtegh5WcuFB6ARBYQk7PgURW1aogpump",
    "9civd7ktdbBtSUgkyduxQoHhBLtThf9xr1Kvj5dcpump", 
    "rCDpCrYepyYffZz7AQhBV1LMJvWo7mps8fWr4Bvpump",
    "69G8CpUVZAxbPMiEBrfCCCH445NwFxH6PzVL693Xpump",
    "4jXJcKQoojvFuA7MSzJLpgDvXyiACqLnMyh6ULEEnVhg",
    "8jFpBJoJwHkYLgNgequJJu6CMt3LkY3P6QndUupLpump"
]

class DeepTokenAnalyzer:
    def __init__(self, birdeye_api, logger):
        self.birdeye_api = birdeye_api
        self.logger = logger
        self.trending_monitor = TrendingTokenMonitor(birdeye_api, logger)
        self.smart_money_detector = SmartMoneyDetector(birdeye_api, logger)
        self.holder_analyzer = HolderDistributionAnalyzer(birdeye_api, logger)
    
    async def get_token_metadata(self, token_address: str) -> Dict[str, Any]:
        """Get comprehensive token metadata."""
        try:
            # Get token overview
            overview = await self.birdeye_api.get_token_overview(token_address)
            
            # Get token security info
            security = await self.birdeye_api.get_token_security(token_address)
            
            # Get price data
            price_data = await self.birdeye_api.get_token_price(token_address)
            
            # Get trading volume
            volume_data = await self.birdeye_api.get_token_volume(token_address)
            
            return {
                "overview": overview,
                "security": security,
                "price": price_data,
                "volume": volume_data,
                "metadata_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.warning(f"Failed to get metadata for {token_address}: {e}")
            return {}
    
    async def analyze_trending_details(self, token_address: str) -> Dict[str, Any]:
        """Deep analysis of trending status."""
        print(f"🔍 Deep Trending Analysis for {token_address[:8]}...")
        
        # Get trending status
        trending_status = await self.trending_monitor.check_token_trending_status(token_address)
        
        # Get all trending tokens for context
        all_trending = await self.trending_monitor.get_trending_tokens(limit=100)
        
        # Calculate trending metrics
        analysis = {
            "is_trending": trending_status.get("is_trending", False),
            "trending_rank": trending_status.get("trending_rank"),
            "trending_score": trending_status.get("trending_score", 0),
            "score_boost": trending_status.get("score_boost", 1.0),
            "total_trending_tokens": len(all_trending),
            "trending_percentile": None,
            "momentum_analysis": {},
            "competitive_position": {}
        }
        
        if analysis["is_trending"] and analysis["trending_rank"]:
            # Calculate percentile position
            analysis["trending_percentile"] = (1 - (analysis["trending_rank"] / len(all_trending))) * 100
            
            # Analyze momentum relative to other trending tokens
            if len(all_trending) > 0:
                scores = [t.get("score", 0) for t in all_trending if t.get("score")]
                if scores:
                    analysis["momentum_analysis"] = {
                        "score_vs_avg": analysis["trending_score"] - (sum(scores) / len(scores)),
                        "score_vs_median": analysis["trending_score"] - sorted(scores)[len(scores)//2],
                        "top_10_percent": analysis["trending_rank"] <= len(all_trending) * 0.1,
                        "top_25_percent": analysis["trending_rank"] <= len(all_trending) * 0.25
                    }
        
        # Competitive analysis
        if len(all_trending) >= 5:
            top_5 = all_trending[:5]
            analysis["competitive_position"] = {
                "in_top_5": analysis["trending_rank"] and analysis["trending_rank"] <= 5,
                "top_5_scores": [t.get("score", 0) for t in top_5],
                "distance_from_top_5": max(0, (analysis["trending_rank"] or 999) - 5) if analysis["trending_rank"] else None
            }
        
        return analysis
    
    async def analyze_smart_money_details(self, token_address: str) -> Dict[str, Any]:
        """Deep analysis of smart money activity."""
        print(f"🧠 Deep Smart Money Analysis for {token_address[:8]}...")
        
        # Get trader analysis
        trader_analysis = await self.smart_money_detector.analyze_token_traders(token_address, limit=50)
        
        # Get top traders data for detailed analysis
        top_traders_data = await self.birdeye_api.get_token_top_traders(token_address, limit=50)
        
        analysis = {
            "smart_traders_count": trader_analysis.get("smart_traders_count", 0),
            "smart_money_level": trader_analysis.get("smart_money_level", "none"),
            "score_boost": trader_analysis.get("score_boost", 1.0),
            "total_traders_analyzed": len(top_traders_data.get("items", [])),
            "trader_quality_breakdown": {},
            "trading_patterns": {},
            "risk_indicators": {}
        }
        
        if top_traders_data.get("items"):
            traders = top_traders_data["items"]
            
            # Analyze trader quality distribution
            volumes = [t.get("volume_24h", 0) for t in traders if t.get("volume_24h")]
            profits = [t.get("pnl", 0) for t in traders if t.get("pnl")]
            
            if volumes:
                analysis["trader_quality_breakdown"] = {
                    "avg_volume_24h": sum(volumes) / len(volumes),
                    "median_volume_24h": sorted(volumes)[len(volumes)//2],
                    "high_volume_traders": len([v for v in volumes if v > 100000]),  # >$100k
                    "volume_concentration": max(volumes) / sum(volumes) if sum(volumes) > 0 else 0
                }
            
            if profits:
                profitable_traders = [p for p in profits if p > 0]
                analysis["trading_patterns"] = {
                    "profitable_trader_ratio": len(profitable_traders) / len(profits),
                    "avg_profit": sum(profitable_traders) / len(profitable_traders) if profitable_traders else 0,
                    "total_pnl": sum(profits),
                    "profit_concentration": max(profits) / sum(profits) if sum(profits) > 0 else 0
                }
            
            # Risk indicators
            analysis["risk_indicators"] = {
                "low_trader_count": len(traders) < 10,
                "high_concentration": analysis["trader_quality_breakdown"].get("volume_concentration", 0) > 0.5,
                "mostly_unprofitable": analysis["trading_patterns"].get("profitable_trader_ratio", 0) < 0.3,
                "suspicious_activity": False  # Could add more sophisticated detection
            }
        
        return analysis
    
    async def analyze_holder_distribution_details(self, token_address: str) -> Dict[str, Any]:
        """Deep analysis of holder distribution."""
        print(f"👥 Deep Holder Distribution Analysis for {token_address[:8]}...")
        
        # Get holder analysis
        holder_analysis = await self.holder_analyzer.analyze_holder_distribution(token_address, limit=100)
        
        # Get raw holder data for detailed analysis
        holder_data = await self.birdeye_api.get_token_holders(token_address, limit=100)
        
        analysis = {
            "total_holders": holder_analysis.get("total_holders", 0),
            "risk_level": holder_analysis.get("risk_assessment", {}).get("risk_level", "unknown"),
            "is_high_risk": holder_analysis.get("risk_assessment", {}).get("is_high_risk", True),
            "score_multiplier": holder_analysis.get("score_adjustment", {}).get("score_multiplier", 1.0),
            "concentration_metrics": {},
            "distribution_analysis": {},
            "whale_analysis": {},
            "risk_factors": {}
        }
        
        if holder_data.get("items"):
            holders = holder_data["items"]
            balances = [float(h.get("ui_amount", 0)) for h in holders]
            total_supply = sum(balances) if balances else 1
            
            # Concentration metrics
            if len(balances) >= 10:
                top_10_concentration = sum(balances[:10]) / total_supply
                top_5_concentration = sum(balances[:5]) / total_supply
                top_1_concentration = balances[0] / total_supply if balances else 0
                
                analysis["concentration_metrics"] = {
                    "top_1_holder_percent": top_1_concentration * 100,
                    "top_5_holders_percent": top_5_concentration * 100,
                    "top_10_holders_percent": top_10_concentration * 100,
                    "gini_coefficient": self._calculate_gini_coefficient(balances),
                    "concentration_score": top_10_concentration  # Higher = more concentrated
                }
            
            # Distribution analysis
            if balances:
                analysis["distribution_analysis"] = {
                    "largest_holder": max(balances),
                    "smallest_holder": min(balances),
                    "median_holding": sorted(balances)[len(balances)//2],
                    "mean_holding": sum(balances) / len(balances),
                    "holding_ratio": max(balances) / min(balances) if min(balances) > 0 else float('inf')
                }
            
            # Whale analysis (holders with >1% of supply)
            whale_threshold = total_supply * 0.01
            whales = [b for b in balances if b > whale_threshold]
            analysis["whale_analysis"] = {
                "whale_count": len(whales),
                "whale_percentage": len(whales) / len(balances) * 100,
                "whale_total_holdings": sum(whales) / total_supply * 100,
                "largest_whale_percent": max(whales) / total_supply * 100 if whales else 0
            }
            
            # Risk factors
            analysis["risk_factors"] = {
                "extreme_concentration": analysis["concentration_metrics"].get("top_10_holders_percent", 0) > 70,
                "single_whale_dominance": analysis["concentration_metrics"].get("top_1_holder_percent", 0) > 50,
                "low_holder_count": len(holders) < 50,
                "high_whale_ratio": analysis["whale_analysis"]["whale_percentage"] > 20,
                "suspicious_distribution": analysis["distribution_analysis"].get("holding_ratio", 0) > 1000000
            }
        
        return analysis
    
    def _calculate_gini_coefficient(self, balances: List[float]) -> float:
        """Calculate Gini coefficient for wealth distribution."""
        if not balances or len(balances) < 2:
            return 0.0
        
        # Sort balances
        sorted_balances = sorted(balances)
        n = len(sorted_balances)
        
        # Calculate Gini coefficient
        cumsum = sum(sorted_balances[i] * (i + 1) for i in range(n))
        total = sum(sorted_balances)
        
        if total == 0:
            return 0.0
        
        gini = (2 * cumsum) / (n * total) - (n + 1) / n
        return gini
    
    async def calculate_composite_risk_score(self, token_address: str, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive risk score based on all analyses."""
        print(f"⚖️ Calculating Composite Risk Score for {token_address[:8]}...")
        
        risk_factors = {
            "trending_risk": 0,
            "smart_money_risk": 0,
            "holder_risk": 0,
            "overall_risk": 0
        }
        
        # Trending risk (lower trending = higher risk)
        trending = analyses.get("trending", {})
        if not trending.get("is_trending", False):
            risk_factors["trending_risk"] = 0.7  # High risk if not trending
        elif trending.get("trending_rank", 999) > 50:
            risk_factors["trending_risk"] = 0.4  # Medium risk if low trending rank
        else:
            risk_factors["trending_risk"] = 0.1  # Low risk if high trending rank
        
        # Smart money risk
        smart_money = analyses.get("smart_money", {})
        smart_traders = smart_money.get("smart_traders_count", 0)
        if smart_traders == 0:
            risk_factors["smart_money_risk"] = 0.8  # High risk if no smart money
        elif smart_traders < 5:
            risk_factors["smart_money_risk"] = 0.5  # Medium risk if few smart traders
        else:
            risk_factors["smart_money_risk"] = 0.2  # Low risk if many smart traders
        
        # Holder risk
        holder = analyses.get("holder_distribution", {})
        concentration = holder.get("concentration_metrics", {}).get("top_10_holders_percent", 0)
        if concentration > 80:
            risk_factors["holder_risk"] = 0.9  # Very high risk
        elif concentration > 60:
            risk_factors["holder_risk"] = 0.6  # High risk
        elif concentration > 40:
            risk_factors["holder_risk"] = 0.3  # Medium risk
        else:
            risk_factors["holder_risk"] = 0.1  # Low risk
        
        # Calculate overall risk (weighted average)
        weights = {"trending_risk": 0.2, "smart_money_risk": 0.3, "holder_risk": 0.5}
        risk_factors["overall_risk"] = sum(
            risk_factors[factor] * weight for factor, weight in weights.items()
        )
        
        # Risk level classification
        overall_risk = risk_factors["overall_risk"]
        if overall_risk > 0.7:
            risk_level = "EXTREME"
        elif overall_risk > 0.5:
            risk_level = "HIGH"
        elif overall_risk > 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "risk_factors": risk_factors,
            "risk_level": risk_level,
            "risk_percentage": overall_risk * 100,
            "investment_recommendation": self._get_investment_recommendation(overall_risk),
            "key_concerns": self._identify_key_concerns(analyses)
        }
    
    def _get_investment_recommendation(self, risk_score: float) -> str:
        """Get investment recommendation based on risk score."""
        if risk_score > 0.8:
            return "AVOID - Extremely high risk of loss"
        elif risk_score > 0.6:
            return "HIGH CAUTION - Only for experienced traders with high risk tolerance"
        elif risk_score > 0.4:
            return "MODERATE CAUTION - Suitable for diversified portfolio with risk management"
        elif risk_score > 0.2:
            return "ACCEPTABLE - Good fundamentals with manageable risks"
        else:
            return "FAVORABLE - Strong fundamentals and low risk profile"
    
    def _identify_key_concerns(self, analyses: Dict[str, Any]) -> List[str]:
        """Identify key risk concerns from analyses."""
        concerns = []
        
        # Trending concerns
        trending = analyses.get("trending", {})
        if not trending.get("is_trending", False):
            concerns.append("Token not currently trending - may lack market momentum")
        
        # Smart money concerns
        smart_money = analyses.get("smart_money", {})
        if smart_money.get("smart_traders_count", 0) == 0:
            concerns.append("No smart money detected - may lack institutional interest")
        
        if smart_money.get("risk_indicators", {}).get("mostly_unprofitable", False):
            concerns.append("Most traders are unprofitable - negative sentiment")
        
        # Holder concerns
        holder = analyses.get("holder_distribution", {})
        if holder.get("risk_factors", {}).get("extreme_concentration", False):
            concerns.append("Extreme holder concentration - high rug pull risk")
        
        if holder.get("risk_factors", {}).get("single_whale_dominance", False):
            concerns.append("Single whale holds majority - market manipulation risk")
        
        if holder.get("risk_factors", {}).get("low_holder_count", False):
            concerns.append("Low holder count - limited community support")
        
        return concerns
    
    async def generate_detailed_report(self, token_address: str) -> Dict[str, Any]:
        """Generate comprehensive detailed report for a token."""
        print(f"\n{'='*80}")
        print(f"🔬 DEEP ANALYSIS: {token_address}")
        print(f"{'='*80}")
        
        # Get all analyses
        metadata = await self.get_token_metadata(token_address)
        trending_analysis = await self.analyze_trending_details(token_address)
        smart_money_analysis = await self.analyze_smart_money_details(token_address)
        holder_analysis = await self.analyze_holder_distribution_details(token_address)
        
        # Small delays between major analysis sections
        await asyncio.sleep(1)
        
        # Calculate composite risk
        all_analyses = {
            "trending": trending_analysis,
            "smart_money": smart_money_analysis,
            "holder_distribution": holder_analysis
        }
        
        risk_assessment = await self.calculate_composite_risk_score(token_address, all_analyses)
        
        # Compile comprehensive report
        report = {
            "token_address": token_address,
            "analysis_timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "trending_analysis": trending_analysis,
            "smart_money_analysis": smart_money_analysis,
            "holder_distribution_analysis": holder_analysis,
            "risk_assessment": risk_assessment,
            "summary": self._generate_executive_summary(token_address, all_analyses, risk_assessment)
        }
        
        # Print summary
        self._print_analysis_summary(report)
        
        return report
    
    def _generate_executive_summary(self, token_address: str, analyses: Dict[str, Any], risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of the analysis."""
        trending = analyses["trending"]
        smart_money = analyses["smart_money"]
        holder = analyses["holder_distribution"]
        
        return {
            "overall_score": (1 - risk_assessment["risk_factors"]["overall_risk"]) * 100,
            "risk_level": risk_assessment["risk_level"],
            "investment_recommendation": risk_assessment["investment_recommendation"],
            "key_strengths": self._identify_strengths(analyses),
            "key_weaknesses": risk_assessment["key_concerns"],
            "market_position": {
                "trending_status": "Trending" if trending["is_trending"] else "Not Trending",
                "smart_money_interest": smart_money["smart_money_level"].title(),
                "holder_quality": "Poor" if holder["is_high_risk"] else "Good"
            },
            "quick_verdict": self._get_quick_verdict(risk_assessment["risk_factors"]["overall_risk"])
        }
    
    def _identify_strengths(self, analyses: Dict[str, Any]) -> List[str]:
        """Identify key strengths from analyses."""
        strengths = []
        
        trending = analyses["trending"]
        smart_money = analyses["smart_money"]
        holder = analyses["holder_distribution"]
        
        if trending["is_trending"]:
            strengths.append(f"Currently trending (rank #{trending['trending_rank']})")
        
        if smart_money["smart_traders_count"] > 0:
            strengths.append(f"Smart money detected ({smart_money['smart_traders_count']} smart traders)")
        
        if not holder["is_high_risk"]:
            strengths.append("Healthy holder distribution")
        
        if trending.get("momentum_analysis", {}).get("top_10_percent", False):
            strengths.append("Top 10% trending momentum")
        
        return strengths
    
    def _get_quick_verdict(self, risk_score: float) -> str:
        """Get quick verdict based on risk score."""
        if risk_score > 0.8:
            return "🔴 AVOID"
        elif risk_score > 0.6:
            return "🟠 HIGH RISK"
        elif risk_score > 0.4:
            return "🟡 MODERATE RISK"
        elif risk_score > 0.2:
            return "🟢 ACCEPTABLE"
        else:
            return "✅ FAVORABLE"
    
    def _print_analysis_summary(self, report: Dict[str, Any]):
        """Print formatted analysis summary."""
        summary = report["summary"]
        risk = report["risk_assessment"]
        
        print(f"\n📊 EXECUTIVE SUMMARY")
        print(f"{'─'*50}")
        print(f"🎯 Overall Score: {summary['overall_score']:.1f}/100")
        print(f"⚠️ Risk Level: {summary['risk_level']}")
        print(f"💡 Quick Verdict: {summary['quick_verdict']}")
        print(f"📈 Investment Rec: {summary['investment_recommendation']}")
        
        print(f"\n🔍 MARKET POSITION")
        print(f"{'─'*30}")
        for key, value in summary["market_position"].items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        
        if summary["key_strengths"]:
            print(f"\n✅ KEY STRENGTHS")
            print(f"{'─'*20}")
            for strength in summary["key_strengths"]:
                print(f"   • {strength}")
        
        if summary["key_weaknesses"]:
            print(f"\n⚠️ KEY CONCERNS")
            print(f"{'─'*20}")
            for weakness in summary["key_weaknesses"]:
                print(f"   • {weakness}")
        
        print(f"\n📈 DETAILED METRICS")
        print(f"{'─'*25}")
        print(f"   Trending Risk: {risk['risk_factors']['trending_risk']*100:.1f}%")
        print(f"   Smart Money Risk: {risk['risk_factors']['smart_money_risk']*100:.1f}%")
        print(f"   Holder Risk: {risk['risk_factors']['holder_risk']*100:.1f}%")

async def main():
    """Main function to run deep analysis on all test tokens."""
    print("🔬 Deep Token Analysis Tool")
    print("=" * 80)
    print(f"📅 Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Analyzing {len(TEST_TOKENS)} tokens in detail")
    print()
    
    # Load environment and config
    load_environment()
    
    config_file = 'config/config.enhanced.yaml'
    if not os.path.exists(config_file):
        config_file = 'config/config.yaml'
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize services
    from core.cache_manager import CacheManager
    from services.rate_limiter_service import RateLimiterService
    from services.logger_setup import LoggerSetup
    
    logger_setup = LoggerSetup('DeepTokenAnalysis')
    logger = logger_setup.logger
    
    cache_manager = CacheManager()
    rate_limiter = RateLimiterService()
    
    birdeye_config = config.get('BIRDEYE_API', {})
    birdeye_config['api_key'] = os.environ.get('BIRDEYE_API_KEY')
    
    birdeye_api = BirdeyeAPI(
        config=birdeye_config,
        logger=logger,
        cache_manager=cache_manager,
        rate_limiter=rate_limiter
    )
    
    # Initialize deep analyzer
    analyzer = DeepTokenAnalyzer(birdeye_api, logger)
    
    # Analyze each token
    all_reports = {}
    
    for i, token_address in enumerate(TEST_TOKENS, 1):
        print(f"\n🔍 ANALYZING TOKEN {i}/{len(TEST_TOKENS)}")
        print(f"📍 Address: {token_address}")
        
        try:
            report = await analyzer.generate_detailed_report(token_address)
            all_reports[token_address] = report
            
            # Delay between tokens to respect rate limits
            if i < len(TEST_TOKENS):
                print(f"\n⏳ Waiting 5 seconds before next analysis...")
                await asyncio.sleep(5)
                
        except Exception as e:
            print(f"❌ Failed to analyze {token_address}: {e}")
            logger.error(f"Analysis failed for {token_address}: {e}")
    
    # Save comprehensive results
    results_dir = Path("scripts/results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"deep_token_analysis_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(all_reports, f, indent=2)
    
    # Generate comparative summary
    print(f"\n🏆 COMPARATIVE ANALYSIS SUMMARY")
    print("=" * 80)
    
    if all_reports:
        # Sort by overall score
        sorted_tokens = sorted(
            all_reports.items(),
            key=lambda x: x[1]["summary"]["overall_score"],
            reverse=True
        )
        
        print(f"📊 TOKEN RANKINGS (by Overall Score):")
        print(f"{'─'*50}")
        
        for i, (addr, report) in enumerate(sorted_tokens, 1):
            summary = report["summary"]
            print(f"{i:2d}. {addr[:8]}... - {summary['overall_score']:5.1f}/100 - {summary['quick_verdict']}")
        
        # Risk distribution
        risk_levels = {}
        for report in all_reports.values():
            risk_level = report["summary"]["risk_level"]
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
        
        print(f"\n📈 RISK DISTRIBUTION:")
        print(f"{'─'*25}")
        for risk_level, count in risk_levels.items():
            print(f"   {risk_level}: {count} token(s)")
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    print(f"🎉 Deep analysis complete!")

if __name__ == "__main__":
    asyncio.run(main()) 