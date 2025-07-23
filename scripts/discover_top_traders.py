#!/usr/bin/env python3
"""
Top Trader Discovery Script

Discovers and analyzes the best performing traders using Birdeye API.
Provides comprehensive analysis for 24h and 7-day timeframes with
performance metrics, risk assessment, and trading patterns.

Features:
- Multi-timeframe trader discovery (24h, 7d)
- Performance analysis with PnL, ROI, win rate
- Risk-adjusted scoring and tier classification
- Trading pattern analysis and recommendations
- Integration with existing whale database
"""

import asyncio
import os
import sys
import argparse
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.trader_performance_analyzer import (
    TraderPerformanceAnalyzer, 
    PerformanceTimeframe, 
    TraderProfile,
    TraderTier
)
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager

class TopTraderDiscovery:
    """Demo class for discovering and analyzing top traders"""
    
    def __init__(self):
        self.analyzer = None
        
    async def initialize(self):
        """Initialize the trader performance analyzer"""
        try:
            print("🔧 Initializing Trader Performance Analyzer...")
            
            # Load configuration
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # Initialize Birdeye API
            birdeye_config = config.get('BIRDEYE_API', {})
            birdeye_api = BirdeyeAPI(config=birdeye_config)
            
            # Initialize trader analyzer
            self.analyzer = TraderPerformanceAnalyzer(birdeye_api)
            
            print("✅ Trader Performance Analyzer initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing analyzer: {e}")
            return False
        
        return True

    async def discover_24h_top_traders(self, max_traders: int = 20):
        """Discover top traders for 24h timeframe"""
        print("\n" + "="*60)
        print("🚀 DISCOVERING TOP TRADERS - 24 HOUR TIMEFRAME")
        print("="*60)
        
        try:
            # Discover top traders
            top_traders = await self.analyzer.discover_top_traders(
                timeframe=PerformanceTimeframe.HOUR_24,
                max_traders=max_traders
            )
            
            if not top_traders:
                print("❌ No traders discovered for 24h timeframe")
                return []
            
            # Display results
            await self._display_trader_rankings(top_traders, "24 Hour")
            
            return top_traders
            
        except Exception as e:
            print(f"❌ Error discovering 24h traders: {e}")
            return []

    async def discover_7d_top_traders(self, max_traders: int = 20):
        """Discover top traders for 7-day timeframe"""
        print("\n" + "="*60)
        print("📊 DISCOVERING TOP TRADERS - 7 DAY TIMEFRAME")
        print("="*60)
        
        try:
            # Discover top traders
            top_traders = await self.analyzer.discover_top_traders(
                timeframe=PerformanceTimeframe.DAYS_7,
                max_traders=max_traders
            )
            
            if not top_traders:
                print("❌ No traders discovered for 7-day timeframe")
                return []
            
            # Display results
            await self._display_trader_rankings(top_traders, "7 Day")
            
            return top_traders
            
        except Exception as e:
            print(f"❌ Error discovering 7-day traders: {e}")
            return []

    async def _display_trader_rankings(self, traders: List[TraderProfile], timeframe_name: str):
        """Display comprehensive trader rankings"""
        print(f"\n🏆 TOP {len(traders)} TRADERS - {timeframe_name.upper()} PERFORMANCE")
        print("-" * 80)
        
        # Header
        print(f"{'Rank':<4} {'Address':<12} {'Tier':<12} {'Score':<6} {'PnL':<12} {'ROI':<8} {'Win%':<6} {'Risk':<6} {'Tags'}")
        print("-" * 80)
        
        for i, trader in enumerate(traders, 1):
            # Get primary performance data
            primary_perf = trader.performance_7d or trader.performance_24h
            
            pnl_str = f"${primary_perf.total_pnl:,.0f}" if primary_perf else "N/A"
            roi_str = f"{primary_perf.roi_percentage:.1f}%" if primary_perf else "N/A"
            win_rate_str = f"{primary_perf.win_rate:.1%}" if primary_perf else "N/A"
            tags_str = ", ".join(trader.tags[:2]) if trader.tags else "none"
            
            # Color coding based on tier
            tier_display = self._get_tier_display(trader.tier)
            
            address_short = trader.address[:10] + '...'
            score_str = f"{trader.discovery_score:.0f}"
            risk_str = f"{trader.risk_score:.0f}"
            
            print(f"{i:<4} {address_short:<12} {tier_display:<12} "
                  f"{score_str:<6} {pnl_str:<12} {roi_str:<8} "
                  f"{win_rate_str:<6} {risk_str:<6} {tags_str}")
        
        # Summary statistics
        await self._display_summary_stats(traders, timeframe_name)

    def _get_tier_display(self, tier: TraderTier) -> str:
        """Get colored tier display"""
        tier_colors = {
            TraderTier.ELITE: "🌟 Elite",
            TraderTier.PROFESSIONAL: "💎 Pro", 
            TraderTier.ADVANCED: "🔥 Adv",
            TraderTier.INTERMEDIATE: "📈 Int",
            TraderTier.NOVICE: "🆕 Nov"
        }
        return tier_colors.get(tier, "❓ Unknown")

    async def _display_summary_stats(self, traders: List[TraderProfile], timeframe_name: str):
        """Display summary statistics for discovered traders"""
        if not traders:
            return
        
        print(f"\n📊 {timeframe_name.upper()} SUMMARY STATISTICS")
        print("-" * 40)
        
        # Calculate aggregated metrics
        total_traders = len(traders)
        
        # Performance metrics (using 7d if available, otherwise 24h)
        performances = [t.performance_7d or t.performance_24h for t in traders if t.performance_7d or t.performance_24h]
        
        if performances:
            avg_pnl = sum(p.total_pnl for p in performances) / len(performances)
            avg_roi = sum(p.roi_percentage for p in performances) / len(performances)
            avg_win_rate = sum(p.win_rate for p in performances) / len(performances)
            total_volume = sum(p.total_trades for p in performances)
            
            print(f"Total Traders Analyzed: {total_traders}")
            print(f"Average PnL: ${avg_pnl:,.0f}")
            print(f"Average ROI: {avg_roi:.1f}%")
            print(f"Average Win Rate: {avg_win_rate:.1%}")
            print(f"Total Trades Analyzed: {total_volume:,}")
        
        # Tier distribution
        tier_counts = {}
        for trader in traders:
            tier_counts[trader.tier] = tier_counts.get(trader.tier, 0) + 1
        
        print(f"\n🏅 TIER DISTRIBUTION:")
        for tier in TraderTier:
            count = tier_counts.get(tier, 0)
            percentage = (count / total_traders) * 100 if total_traders > 0 else 0
            print(f"  {self._get_tier_display(tier)}: {count} ({percentage:.1f}%)")

    async def analyze_specific_trader(self, trader_address: str):
        """Analyze a specific trader in detail"""
        print(f"\n🔍 DETAILED TRADER ANALYSIS: {trader_address}")
        print("="*60)
        
        try:
            # Get comprehensive performance summary
            summary = await self.analyzer.get_trader_performance_summary(trader_address)
            
            if not summary:
                print("❌ Could not analyze trader - insufficient data")
                return
            
            # Display comprehensive analysis
            print(f"Trader Address: {summary['trader_address']}")
            print(f"Tier: {summary['tier'].title()}")
            print(f"Discovery Score: {summary['discovery_score']:.0f}/100")
            print(f"Risk Score: {summary['risk_score']:.0f}/100")
            print(f"Portfolio Value: ${summary['portfolio_value']:,.0f}")
            print(f"Tokens in Portfolio: {summary['tokens_traded']}")
            
            # 24h Performance
            if summary['performance_24h']:
                perf_24h = summary['performance_24h']
                print(f"\n📈 24 HOUR PERFORMANCE:")
                print(f"  PnL: ${perf_24h['total_pnl']:,.0f}")
                print(f"  ROI: {perf_24h['roi_percentage']:.1f}%")
                print(f"  Win Rate: {perf_24h['win_rate']:.1%}")
                print(f"  Total Trades: {perf_24h['total_trades']}")
                print(f"  Avg Position: ${perf_24h['avg_position_size']:,.0f}")
                print(f"  Largest Win: ${perf_24h['largest_win']:,.0f}")
                print(f"  Max Drawdown: {perf_24h['max_drawdown']:.1%}")
            
            # 7d Performance
            if summary['performance_7d']:
                perf_7d = summary['performance_7d']
                print(f"\n📊 7 DAY PERFORMANCE:")
                print(f"  PnL: ${perf_7d['total_pnl']:,.0f}")
                print(f"  ROI: {perf_7d['roi_percentage']:.1f}%")
                print(f"  Win Rate: {perf_7d['win_rate']:.1%}")
                print(f"  Total Trades: {perf_7d['total_trades']}")
                print(f"  Avg Position: ${perf_7d['avg_position_size']:,.0f}")
                print(f"  Largest Win: ${perf_7d['largest_win']:,.0f}")
                print(f"  Sharpe Ratio: {perf_7d['sharpe_ratio']:.2f}")
            
        except Exception as e:
            print(f"❌ Error analyzing trader: {e}")

    async def compare_timeframes(self, max_traders: int = 10):
        """Compare top traders across 24h and 7d timeframes"""
        print("\n" + "="*80)
        print("🔄 TIMEFRAME COMPARISON - 24H vs 7D TOP TRADERS")
        print("="*80)
        
        try:
            # Get top traders for both timeframes
            print("🔍 Discovering 24h top traders...")
            traders_24h = await self.analyzer.discover_top_traders(
                PerformanceTimeframe.HOUR_24, max_traders
            )
            
            print("🔍 Discovering 7d top traders...")
            traders_7d = await self.analyzer.discover_top_traders(
                PerformanceTimeframe.DAYS_7, max_traders
            )
            
            # Compare results
            self._compare_trader_lists(traders_24h, traders_7d)
            
        except Exception as e:
            print(f"❌ Error in timeframe comparison: {e}")

    def _compare_trader_lists(self, traders_24h: List[TraderProfile], traders_7d: List[TraderProfile]):
        """Compare two lists of traders"""
        if not traders_24h or not traders_7d:
            print("❌ Insufficient data for comparison")
            return
        
        # Find common traders
        addrs_24h = {t.address for t in traders_24h}
        addrs_7d = {t.address for t in traders_7d}
        common_addrs = addrs_24h.intersection(addrs_7d)
        
        print(f"\n📊 COMPARISON RESULTS:")
        print(f"Top 24h Traders: {len(traders_24h)}")
        print(f"Top 7d Traders: {len(traders_7d)}")
        print(f"Common Traders: {len(common_addrs)}")
        print(f"Overlap Percentage: {len(common_addrs) / max(len(addrs_24h), len(addrs_7d)) * 100:.1f}%")
        
        if common_addrs:
            print(f"\n🤝 CONSISTENT TOP PERFORMERS:")
            for addr in list(common_addrs)[:5]:  # Show top 5 common
                trader_24h = next((t for t in traders_24h if t.address == addr), None)
                trader_7d = next((t for t in traders_7d if t.address == addr), None)
                
                if trader_24h and trader_7d:
                    print(f"  {addr[:10]}... - "
                          f"24h: {trader_24h.discovery_score:.0f}, "
                          f"7d: {trader_7d.discovery_score:.0f}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Discover Top Traders using Birdeye API")
    parser.add_argument("--timeframe", choices=["24h", "7d", "both"], default="both",
                       help="Timeframe for analysis")
    parser.add_argument("--max-traders", type=int, default=20,
                       help="Maximum number of traders to discover")
    parser.add_argument("--analyze-trader", type=str,
                       help="Analyze specific trader wallet address")
    parser.add_argument("--compare", action="store_true",
                       help="Compare 24h vs 7d top traders")
    
    args = parser.parse_args()
    
    # Initialize discovery system
    discovery = TopTraderDiscovery()
    if not await discovery.initialize():
        print("❌ Failed to initialize trader discovery system")
        return
    
    try:
        # Analyze specific trader if requested
        if args.analyze_trader:
            await discovery.analyze_specific_trader(args.analyze_trader)
            return
        
        # Compare timeframes if requested
        if args.compare:
            await discovery.compare_timeframes(args.max_traders)
            return
        
        # Discover traders for specified timeframe(s)
        if args.timeframe in ["24h", "both"]:
            await discovery.discover_24h_top_traders(args.max_traders)
        
        if args.timeframe in ["7d", "both"]:
            await discovery.discover_7d_top_traders(args.max_traders)
        
        print("\n✅ Trader discovery completed successfully!")
        print("\n💡 NEXT STEPS:")
        print("1. Use --analyze-trader <address> for detailed analysis")
        print("2. Use --compare to see 24h vs 7d consistency")
        print("3. Check data/trader_performance/ for cached results")
        
    except KeyboardInterrupt:
        print("\n🛑 Discovery interrupted by user")
    except Exception as e:
        print(f"❌ Error during discovery: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 