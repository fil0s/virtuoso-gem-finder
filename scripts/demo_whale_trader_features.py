#!/usr/bin/env python3
"""
Demo Script for Whale & Trader Features

This script demonstrates individual whale and trader functionality with examples.
Use this to showcase specific features or for debugging individual components.

Usage:
    python scripts/demo_whale_trader_features.py [--feature FEATURE_NAME]
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from api.birdeye_connector import BirdeyeAPI
from services.whale_discovery_service import WhaleDiscoveryService, WhaleProfile
# WhaleActivityAnalyzer deprecated - functionality moved to WhaleSharkMovementTracker
from services.whale_shark_movement_tracker import WhaleSharkMovementTracker, WhaleActivityType
from services.strategic_coordination_analyzer import StrategicCoordinationAnalyzer, CoordinationType
from services.logger_setup import LoggerSetup
from core.config_manager import get_config_manager
from services.rate_limiter_service import RateLimiterService
from core.cache_manager import CacheManager

class WhaleTraderDemo:
    """Demonstrates whale and trader functionality with examples"""
    
    def __init__(self):
        self.logger_setup = LoggerSetup('WhaleTraderDemo', log_level="INFO")
        self.logger = self.logger_setup.logger
        
        # Initialize core services
        self.config = get_config_manager().get_config()
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiterService()
        
        # Initialize BirdeyeAPI
        birdeye_config = self.config.get('BIRDEYE_API', {})
        self.birdeye_api = BirdeyeAPI(
            config=birdeye_config,
            logger=self.logger,
            cache_manager=self.cache_manager,
            rate_limiter=self.rate_limiter
        )
        
        # Initialize whale and trader services
        self.whale_discovery = WhaleDiscoveryService(self.birdeye_api, self.logger)
        self.whale_analyzer = WhaleSharkMovementTracker(self.birdeye_api, self.logger, whale_discovery_service=self.whale_discovery)
        self.coordination_analyzer = StrategicCoordinationAnalyzer(self.logger)
    
    async def demo_whale_database(self):
        """Demo whale database functionality"""
        print("\n🐋 WHALE DATABASE DEMO")
        print("=" * 50)
        
        # Show current whale database stats
        stats = self.whale_analyzer.get_whale_database_stats()
        print(f"Total whales in database: {stats['total_whales']}")
        print(f"Tier distribution: {stats['tier_distribution']}")
        print(f"Average position size: ${stats['avg_position_size']:,.0f}")
        print(f"Average success rate: {stats['avg_success_rate']:.2%}")
        print(f"Has discovery service: {stats['has_discovery_service']}")
        
        # Show whale tiers
        print(f"\n🏆 WHALE TIER CLASSIFICATION:")
        tier_dist = stats['tier_distribution']
        print(f"  Tier 1 (Mega Whales): {tier_dist.get(1, 0)} whales")
        print(f"  Tier 2 (Large Whales): {tier_dist.get(2, 0)} whales")
        print(f"  Tier 3 (Medium Whales): {tier_dist.get(3, 0)} whales")
        
        # Show some example whales
        print(f"\n🐋 EXAMPLE WHALE PROFILES:")
        whale_db = self.whale_analyzer.whale_database
        for i, (address, data) in enumerate(list(whale_db.items())[:3]):
            print(f"  {i+1}. {address[:8]}... - {data.get('name', 'Unknown')}")
            print(f"     Tier: {data.get('tier')}, Success Rate: {data.get('success_rate', 0):.2%}")
            print(f"     Avg Position: ${data.get('avg_position', 0):,.0f}")
    
    async def demo_whale_activity_analysis(self):
        """Demo whale activity analysis with sample data"""
        print("\n🐋 WHALE ACTIVITY ANALYSIS DEMO")
        print("=" * 50)
        
        # Create sample token data
        sample_tokens = [
            {
                'symbol': 'EXAMPLE',
                'address': 'ExampleTokenAddress123456789',
                'market_cap': 10_000_000,  # $10M market cap
                'volume_24h': 2_000_000,   # $2M volume
                'holders_data': {},
                'top_traders': [],
                'unique_trader_count': 150,
                'creation_time': 1643723400  # Recent timestamp
            }
        ]
        
        for token in sample_tokens:
            print(f"\n📊 Analyzing {token['symbol']}:")
            print(f"  Market Cap: ${token['market_cap']:,.0f}")
            print(f"  24h Volume: ${token['volume_24h']:,.0f}")
            print(f"  Unique Traders: {token['unique_trader_count']}")
            
            # Analyze whale activity
            whale_signal = await self.whale_analyzer.analyze_whale_activity(
                token['address'], token
            )
            
            # Get whale grade
            whale_grade = self.whale_analyzer.get_whale_activity_grade(whale_signal)
            
            print(f"\n🎯 WHALE ANALYSIS RESULTS:")
            print(f"  Activity Type: {whale_signal.type.value}")
            print(f"  Confidence: {whale_signal.confidence:.2f}")
            print(f"  Score Impact: {whale_signal.score_impact:+d}")
            print(f"  Whale Count: {whale_signal.whale_count}")
            print(f"  Total Value: ${whale_signal.total_value:,.0f}")
            print(f"  Whale Grade: {whale_grade}")
            print(f"  Details: {whale_signal.details}")
            
            # Explain activity types
            print(f"\n📚 ACTIVITY TYPE MEANINGS:")
            for activity_type in WhaleActivityType:
                print(f"  {activity_type.value}: ", end="")
                if activity_type == WhaleActivityType.ACCUMULATION:
                    print("Whales are buying heavily (positive signal)")
                elif activity_type == WhaleActivityType.DISTRIBUTION:
                    print("Whales are selling/exiting (negative signal)")
                elif activity_type == WhaleActivityType.ROTATION:
                    print("Whales changing positions (neutral signal)")
                elif activity_type == WhaleActivityType.INSTITUTIONAL_FLOW:
                    print("Institution-scale movements (high impact)")
                elif activity_type == WhaleActivityType.SMART_MONEY_ENTRY:
                    print("Proven performers entering (strong positive)")
                elif activity_type == WhaleActivityType.COORDINATED_BUY:
                    print("Multiple whales coordinating (very positive)")
                elif activity_type == WhaleActivityType.STEALTH_ACCUMULATION:
                    print("Quiet accumulation over time (positive)")
    
    async def demo_strategic_coordination(self):
        """Demo strategic coordination analysis"""
        print("\n🎯 STRATEGIC COORDINATION ANALYSIS DEMO")
        print("=" * 50)
        
        # Create sample coordination scenarios
        coordination_scenarios = [
            {
                'name': 'Smart Money Entry',
                'token_symbol': 'SMART_TOKEN',
                'volume_24h': 5_000_000,
                'market_cap': 20_000_000,
                'unique_trader_count': 200,
                'creation_time': 1643723400 - 7200,  # 2 hours ago
                'trader_list': [
                    "5yb3D1KBy13czATSYGLUbZrYJvRvFQiH9XYkAeG2nDzH",  # Smart money
                    "HrwRZw4ZpEGgkzgDY1LrU8rgJZeYCNwRaf9LNkWJHRjH",  # Smart money
                    "65CmecDnuFAYJv8D8Ax3m3eNEGe4NQvrJV2GJPFMtATH",  # Smart money
                    "RandomTrader1234567890123456789012345678",      # Unknown
                ]
            },
            {
                'name': 'Retail Pump',
                'token_symbol': 'RETAIL_TOKEN',
                'volume_24h': 50_000_000,  # Very high volume
                'market_cap': 1_000_000,   # Small market cap
                'unique_trader_count': 50,  # Few traders
                'creation_time': 1643723400 - 3600,  # 1 hour ago
                'trader_list': [
                    "RandomTrader1111111111111111111111111111",
                    "RandomTrader2222222222222222222222222222",
                    "RandomTrader3333333333333333333333333333",
                ]
            }
        ]
        
        for scenario in coordination_scenarios:
            print(f"\n📊 Scenario: {scenario['name']}")
            print(f"  Token: {scenario['token_symbol']}")
            print(f"  Volume/Market Cap Ratio: {scenario['volume_24h']/scenario['market_cap']:.1f}x")
            print(f"  Unique Traders: {scenario['unique_trader_count']}")
            print(f"  Smart Money Wallets: {sum(1 for addr in scenario['trader_list'] if addr in self.coordination_analyzer.smart_money_wallets)}")
            
            # Analyze coordination
            signal = self.coordination_analyzer.analyze_coordination_patterns(scenario)
            grade = self.coordination_analyzer.get_opportunity_grade(signal)
            
            print(f"\n🎯 COORDINATION ANALYSIS:")
            print(f"  Type: {signal.type.value}")
            print(f"  Opportunity Grade: {grade}")
            print(f"  Confidence: {signal.confidence:.2f}")
            print(f"  Score Impact: {signal.score_impact:+d}")
            print(f"  Timing Factor: {signal.timing_factor:.2f}")
            print(f"  Details: {signal.details}")
        
        # Explain coordination types
        print(f"\n📚 COORDINATION TYPE MEANINGS:")
        for coord_type in CoordinationType:
            print(f"  {coord_type.value}: ", end="")
            if coord_type == CoordinationType.SMART_ACCUMULATION:
                print("Grade A - Smart money accumulating (follow these)")
            elif coord_type == CoordinationType.INSTITUTIONAL_BUILD:
                print("Grade A - Institutional building positions (follow these)")
            elif coord_type == CoordinationType.MOMENTUM_COORDINATION:
                print("Grade B - Good momentum with coordination (consider these)")
            elif coord_type == CoordinationType.EARLY_COORDINATION:
                print("Grade B - Early stage coordination (consider these)")
            elif coord_type == CoordinationType.MIXED_SIGNALS:
                print("Grade C - Mixed signals, unclear direction (neutral)")
            elif coord_type == CoordinationType.RETAIL_PUMP:
                print("Grade D - Retail-driven pump (avoid these)")
            elif coord_type == CoordinationType.WASH_TRADING:
                print("Grade F - Wash trading detected (avoid these)")
    
    async def demo_whale_discovery_criteria(self):
        """Demo whale discovery validation criteria"""
        print("\n🔍 WHALE DISCOVERY CRITERIA DEMO")
        print("=" * 50)
        
        # Show validation criteria
        criteria = self.whale_discovery.validation_criteria
        thresholds = self.whale_discovery.tier_thresholds
        
        print(f"🎯 WHALE VALIDATION CRITERIA:")
        print(f"  Minimum Success Rate: {criteria['min_success_rate']:.0%}")
        print(f"  Minimum Total P&L: ${criteria['min_total_pnl']:,.0f}")
        print(f"  Minimum Tokens Traded: {criteria['min_tokens_traded']}")
        print(f"  Minimum Average Position: ${criteria['min_avg_position']:,.0f}")
        print(f"  Minimum Confidence Score: {criteria['min_confidence_score']:.0%}")
        print(f"  Minimum Activity Days: {criteria['min_activity_days']}")
        
        print(f"\n🏆 WHALE TIER THRESHOLDS:")
        for tier, threshold in thresholds.items():
            tier_name = {1: "Mega Whales", 2: "Large Whales", 3: "Medium Whales"}[tier]
            print(f"  Tier {tier} ({tier_name}): ${threshold:,.0f}+ average positions")
        
        print(f"\n📊 DISCOVERY SOURCES & WEIGHTS:")
        sources = self.whale_discovery.discovery_sources
        for source, weight in sources.items():
            print(f"  {source.replace('_', ' ').title()}: {weight:.0%} weight")
        
        # Show discovery stats
        stats = self.whale_discovery.get_discovery_stats()
        print(f"\n📈 CURRENT DISCOVERY STATS:")
        print(f"  Total Whales Discovered: {stats.get('total_whales', 0)}")
        print(f"  Discovery Sources Available: {len(sources)}")
        print(f"  Validation Criteria: {len(criteria)} checks")
    
    async def run_demo(self, feature: str = "all"):
        """Run the selected demo features"""
        print("🐋 WHALE & TRADER FUNCTIONALITY DEMO")
        print("=" * 60)
        
        try:
            if feature == "all" or feature == "database":
                await self.demo_whale_database()
            
            if feature == "all" or feature == "activity":
                await self.demo_whale_activity_analysis()
            
            if feature == "all" or feature == "coordination":
                await self.demo_strategic_coordination()
            
            if feature == "all" or feature == "discovery":
                await self.demo_whale_discovery_criteria()
            
            print("\n🎯 DEMO COMPLETE!")
            print("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Demo failed: {e}", exc_info=True)
        finally:
            await self.birdeye_api.close_session()

async def main():
    """Main demo execution function"""
    parser = argparse.ArgumentParser(description='Demo whale and trader functionality')
    parser.add_argument('--feature', 
                      choices=['all', 'database', 'activity', 'coordination', 'discovery'],
                      default='all',
                      help='Feature to demo (default: all)')
    
    args = parser.parse_args()
    
    demo = WhaleTraderDemo()
    await demo.run_demo(feature=args.feature)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1) 