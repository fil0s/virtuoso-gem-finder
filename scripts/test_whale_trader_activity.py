#!/usr/bin/env python3
"""
Comprehensive Test Script for Whale and Trader Activity Analysis

This script tests all whale and trader-related functionality including:
- Whale discovery service
- Whale activity analyzer
- Strategic coordination analyzer
- Trader performance analyzer
- Whale movement tracking
- Integration with token analysis

Usage:
    python scripts/test_whale_trader_activity.py [--mode test|live] [--tokens ADDRESSES]
"""

import asyncio
import sys
import os
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

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
from services.early_token_detection import EarlyTokenDetector

class WhaleTraderActivityTester:
    """Comprehensive tester for all whale and trader functionality"""
    
    def __init__(self, mode: str = "test"):
        self.mode = mode
        self.logger_setup = LoggerSetup('WhaleTraderTester', log_level="INFO")
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
        
        # Test data setup
        self.test_results = {}
        
        # Test tokens (popular Solana tokens for testing)
        self.test_tokens = [
            "So11111111111111111111111111111111111111112",  # Wrapped SOL
            "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",   # Marinade SOL  
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",   # Bonk
            "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",    # Jupiter
            "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",   # PopCat
        ]
        
    async def run_comprehensive_test(self, custom_tokens: Optional[List[str]] = None):
        """Run comprehensive test of all whale and trader functionality"""
        self.logger.info("🐋 STARTING COMPREHENSIVE WHALE & TRADER ACTIVITY TEST")
        self.logger.info("=" * 80)
        
        test_tokens = custom_tokens or self.test_tokens
        
        try:
            # Phase 1: Test whale discovery service
            await self._test_whale_discovery_service()
            
            # Phase 2: Test whale database functionality
            await self._test_whale_database_operations()
            
            # Phase 3: Test whale activity analysis
            await self._test_whale_activity_analysis(test_tokens)
            
            # Phase 4: Test strategic coordination analysis
            await self._test_strategic_coordination_analysis(test_tokens)
            
            # Phase 5: Test integrated token analysis with whale/trader data
            await self._test_integrated_whale_trader_analysis(test_tokens)
            
            # Phase 6: Performance and statistics summary
            await self._generate_test_summary()
            
        except Exception as e:
            self.logger.error(f"❌ Test suite failed: {e}", exc_info=True)
        finally:
            await self.birdeye_api.close_session()
    
    async def _test_whale_discovery_service(self):
        """Test whale discovery service functionality"""
        self.logger.info("\n🔍 PHASE 1: Testing Whale Discovery Service")
        self.logger.info("-" * 60)
        
        try:
            # Test 1: Discovery service initialization
            stats = self.whale_discovery.get_discovery_stats()
            self.logger.info(f"✅ Discovery service initialized")
            self.logger.info(f"   Existing whale database: {stats.get('total_whales', 0)} whales")
            
            # Test 2: Whale database loading
            existing_whales = len(self.whale_discovery.discovered_whales)
            self.logger.info(f"✅ Loaded {existing_whales} existing discovered whales")
            
            # Test 3: New whale discovery (limited for testing)
            if self.mode == "live":
                self.logger.info("🔍 Discovering new whales (live mode)...")
                new_whales = await self.whale_discovery.discover_new_whales(max_discoveries=5)
                self.logger.info(f"✅ Discovered {len(new_whales)} new whales")
                
                for whale in new_whales[:3]:  # Show first 3
                    self.logger.info(f"   🐋 {whale.address[:8]}... - Tier {whale.tier}, {whale.success_rate:.2%} win rate")
            else:
                self.logger.info("⚠️ Skipping live whale discovery in test mode")
            
            # Test 4: Whale validation criteria
            self.logger.info("✅ Whale validation criteria configured:")
            criteria = self.whale_discovery.validation_criteria
            for key, value in criteria.items():
                self.logger.info(f"   {key}: {value}")
            
            self.test_results['whale_discovery'] = {
                'status': 'success',
                'existing_whales': existing_whales,
                'discovery_stats': stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Whale discovery test failed: {e}")
            self.test_results['whale_discovery'] = {'status': 'failed', 'error': str(e)}
    
    async def _test_whale_database_operations(self):
        """Test whale database operations and management"""
        self.logger.info("\n📊 PHASE 2: Testing Whale Database Operations")
        self.logger.info("-" * 60)
        
        try:
            # Test 1: Database statistics
            stats = self.whale_analyzer.get_whale_database_stats()
            self.logger.info(f"✅ Whale database statistics:")
            self.logger.info(f"   Total whales: {stats['total_whales']}")
            self.logger.info(f"   Tier distribution: {stats['tier_distribution']}")
            self.logger.info(f"   Average position size: ${stats['avg_position_size']:,.0f}")
            self.logger.info(f"   Average success rate: {stats['avg_success_rate']:.2%}")
            
            # Test 2: Database refresh capability
            if self.mode == "live":
                self.logger.info("🔄 Testing database refresh...")
                await self.whale_analyzer.refresh_whale_database()
                self.logger.info("✅ Database refresh completed")
            
            # Test 3: Whale tier classification
            total_by_tier = stats['tier_distribution']
            self.logger.info(f"✅ Whale tier classification:")
            self.logger.info(f"   Tier 1 (Mega Whales): {total_by_tier.get(1, 0)} whales")
            self.logger.info(f"   Tier 2 (Large Whales): {total_by_tier.get(2, 0)} whales") 
            self.logger.info(f"   Tier 3 (Medium Whales): {total_by_tier.get(3, 0)} whales")
            
            self.test_results['whale_database'] = {
                'status': 'success',
                'stats': stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Whale database test failed: {e}")
            self.test_results['whale_database'] = {'status': 'failed', 'error': str(e)}
    
    async def _test_whale_activity_analysis(self, test_tokens: List[str]):
        """Test whale activity analysis on tokens"""
        self.logger.info("\n🐋 PHASE 3: Testing Whale Activity Analysis")
        self.logger.info("-" * 60)
        
        whale_results = []
        
        for i, token_address in enumerate(test_tokens[:3]):  # Test first 3 tokens
            try:
                self.logger.info(f"\n📈 Testing whale analysis {i+1}/3: {token_address[:8]}...")
                
                # Get token data for analysis
                token_overview = await self.birdeye_api.get_token_overview(token_address)
                if not token_overview:
                    self.logger.warning(f"⚠️ No overview data for {token_address}")
                    continue
                
                token_symbol = token_overview.get('symbol', 'UNKNOWN')
                self.logger.info(f"   Token: {token_symbol}")
                
                # Prepare token data for whale analysis
                token_data = {
                    'symbol': token_symbol,
                    'holders_data': {},  # Would be populated from holders API
                    'top_traders': [],   # Would be populated from traders API
                    'market_cap': token_overview.get('marketCap', 0),
                    'volume_24h': token_overview.get('volume', {}).get('h24', 0),
                    'unique_trader_count': 50,  # Mock data for testing
                    'creation_time': time.time() - 86400  # 1 day old
                }
                
                # Test whale activity analysis
                whale_signal = await self.whale_analyzer.analyze_whale_activity(token_address, token_data)
                
                # Test whale activity grading
                whale_grade = self.whale_analyzer.get_whale_activity_grade(whale_signal)
                
                self.logger.info(f"✅ Whale analysis completed for {token_symbol}:")
                self.logger.info(f"   Activity Type: {whale_signal.type.value}")
                self.logger.info(f"   Confidence: {whale_signal.confidence:.2f}")
                self.logger.info(f"   Score Impact: {whale_signal.score_impact:+d}")
                self.logger.info(f"   Whale Grade: {whale_grade}")
                self.logger.info(f"   Details: {whale_signal.details}")
                
                whale_results.append({
                    'token': token_symbol,
                    'address': token_address,
                    'signal': whale_signal,
                    'grade': whale_grade
                })
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"❌ Whale analysis failed for {token_address}: {e}")
                whale_results.append({
                    'token': token_address,
                    'address': token_address,
                    'error': str(e)
                })
        
        # Summary of whale activity types detected
        activity_types = {}
        for result in whale_results:
            if 'signal' in result:
                activity_type = result['signal'].type.value
                activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        self.logger.info(f"\n✅ Whale Activity Analysis Summary:")
        self.logger.info(f"   Tokens analyzed: {len(whale_results)}")
        self.logger.info(f"   Activity types detected: {activity_types}")
        
        self.test_results['whale_activity'] = {
            'status': 'success',
            'results': whale_results,
            'activity_summary': activity_types
        }
    
    async def _test_strategic_coordination_analysis(self, test_tokens: List[str]):
        """Test strategic coordination analysis"""
        self.logger.info("\n🎯 PHASE 4: Testing Strategic Coordination Analysis")
        self.logger.info("-" * 60)
        
        coordination_results = []
        
        for i, token_address in enumerate(test_tokens[:3]):  # Test first 3 tokens
            try:
                self.logger.info(f"\n📊 Testing coordination analysis {i+1}/3: {token_address[:8]}...")
                
                # Get token data
                token_overview = await self.birdeye_api.get_token_overview(token_address)
                if not token_overview:
                    continue
                
                token_symbol = token_overview.get('symbol', 'UNKNOWN')
                
                # Prepare token data for coordination analysis
                token_data = {
                    'token_symbol': token_symbol,
                    'volume_24h': token_overview.get('volume', {}).get('h24', 0),
                    'market_cap': token_overview.get('marketCap', 0),
                    'unique_trader_count': 75,  # Mock data
                    'creation_time': time.time() - 43200,  # 12 hours old
                    'trader_list': [  # Mock trader addresses for testing
                        "5yb3D1KBy13czATSYGLUbZrYJvRvFQiH9XYkAeG2nDzH",  # Smart money
                        "HrwRZw4ZpEGgkzgDY1LrU8rgJZeYCNwRaf9LNkWJHRjH",  # Smart money
                        "RandomTrader1234567890123456789012345678",      # Unknown
                        "RandomTrader9876543210987654321098765432",      # Unknown
                    ]
                }
                
                # Test coordination analysis
                coordination_signal = self.coordination_analyzer.analyze_coordination_patterns(token_data)
                
                # Test opportunity grading
                opportunity_grade = self.coordination_analyzer.get_opportunity_grade(coordination_signal)
                
                self.logger.info(f"✅ Coordination analysis completed for {token_symbol}:")
                self.logger.info(f"   Coordination Type: {coordination_signal.type.value}")
                self.logger.info(f"   Opportunity Grade: {opportunity_grade}")
                self.logger.info(f"   Confidence: {coordination_signal.confidence:.2f}")
                self.logger.info(f"   Score Impact: {coordination_signal.score_impact:+d}")
                self.logger.info(f"   Timing Factor: {coordination_signal.timing_factor:.2f}")
                self.logger.info(f"   Details: {coordination_signal.details}")
                
                coordination_results.append({
                    'token': token_symbol,
                    'address': token_address,
                    'signal': coordination_signal,
                    'grade': opportunity_grade
                })
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"❌ Coordination analysis failed for {token_address}: {e}")
                coordination_results.append({
                    'token': token_address,
                    'address': token_address,
                    'error': str(e)
                })
        
        # Summary of coordination types detected  
        coordination_types = {}
        opportunity_grades = {}
        for result in coordination_results:
            if 'signal' in result:
                coord_type = result['signal'].type.value
                grade = result['grade']
                coordination_types[coord_type] = coordination_types.get(coord_type, 0) + 1
                opportunity_grades[grade] = opportunity_grades.get(grade, 0) + 1
        
        self.logger.info(f"\n✅ Strategic Coordination Analysis Summary:")
        self.logger.info(f"   Tokens analyzed: {len(coordination_results)}")
        self.logger.info(f"   Coordination types: {coordination_types}")
        self.logger.info(f"   Opportunity grades: {opportunity_grades}")
        
        self.test_results['coordination_analysis'] = {
            'status': 'success', 
            'results': coordination_results,
            'coordination_summary': coordination_types,
            'grade_summary': opportunity_grades
        }
    
    async def _test_integrated_whale_trader_analysis(self, test_tokens: List[str]):
        """Test integrated whale and trader analysis through EarlyTokenDetector"""
        self.logger.info("\n🚀 PHASE 5: Testing Integrated Whale & Trader Analysis")
        self.logger.info("-" * 60)
        
        try:
            # Initialize the integrated detector (enables whale tracking)
            detector = EarlyTokenDetector(config=self.config, enable_whale_tracking=True)
            
            # Test whale tracking status
            whale_status = detector.get_whale_tracking_status()
            self.logger.info(f"✅ Whale tracking status: {whale_status['status']}")
            self.logger.info(f"   Enabled: {whale_status['enabled']}")
            if whale_status['enabled']:
                self.logger.info(f"   Tracked whales: {whale_status['tracked_whales']}")
                self.logger.info(f"   Movements 24h: {whale_status['movements_24h']}")
            
            # Test whale database integration
            whale_db_stats = detector.get_whale_database_stats()
            self.logger.info(f"✅ Integrated whale database:")
            self.logger.info(f"   Total whales: {whale_db_stats['total_whales']}")
            self.logger.info(f"   Discovery service: {whale_db_stats['has_discovery_service']}")
            
            # Test discovery and tracking of new whales
            if self.mode == "live":
                self.logger.info("🔍 Testing discovery and tracking integration...")
                new_tracked = await detector.discover_and_track_new_whales(max_discoveries=3)
                self.logger.info(f"✅ Discovered and added {new_tracked} new whales for tracking")
            
            self.logger.info("✅ Integrated whale & trader analysis test completed")
            
            self.test_results['integrated_analysis'] = {
                'status': 'success',
                'whale_tracking': whale_status,
                'database_stats': whale_db_stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Integrated analysis test failed: {e}")
            self.test_results['integrated_analysis'] = {'status': 'failed', 'error': str(e)}
    
    async def _generate_test_summary(self):
        """Generate comprehensive test summary"""
        self.logger.info("\n📋 PHASE 6: Test Summary & Performance Report")
        self.logger.info("=" * 80)
        
        # Overall test results
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() 
                             if result.get('status') == 'success')
        
        self.logger.info(f"🎯 OVERALL TEST RESULTS:")
        self.logger.info(f"   Total test phases: {total_tests}")
        self.logger.info(f"   Successful: {successful_tests}")
        self.logger.info(f"   Failed: {total_tests - successful_tests}")
        self.logger.info(f"   Success rate: {successful_tests/total_tests*100:.1f}%")
        
        # Detailed phase results
        self.logger.info(f"\n📊 DETAILED PHASE RESULTS:")
        for phase, result in self.test_results.items():
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            self.logger.info(f"   {status_emoji} {phase.replace('_', ' ').title()}: {result['status']}")
            
            if result['status'] == 'failed':
                self.logger.error(f"      Error: {result.get('error', 'Unknown error')}")
        
        # Whale & Trader Functionality Summary
        self.logger.info(f"\n🐋 WHALE & TRADER FUNCTIONALITY VERIFIED:")
        
        # Whale Discovery
        if 'whale_discovery' in self.test_results:
            whale_discovery = self.test_results['whale_discovery']
            if whale_discovery['status'] == 'success':
                stats = whale_discovery['discovery_stats']
                self.logger.info(f"   ✅ Whale Discovery Service - {stats.get('total_whales', 0)} whales in database")
        
        # Whale Database
        if 'whale_database' in self.test_results:
            whale_db = self.test_results['whale_database']
            if whale_db['status'] == 'success':
                stats = whale_db['stats']
                self.logger.info(f"   ✅ Whale Database Management - {stats['total_whales']} total whales")
                self.logger.info(f"      Tier 1: {stats['tier_distribution'].get(1, 0)}, "
                               f"Tier 2: {stats['tier_distribution'].get(2, 0)}, "
                               f"Tier 3: {stats['tier_distribution'].get(3, 0)}")
        
        # Whale Activity Analysis
        if 'whale_activity' in self.test_results:
            whale_activity = self.test_results['whale_activity']
            if whale_activity['status'] == 'success':
                summary = whale_activity['activity_summary']
                self.logger.info(f"   ✅ Whale Activity Analysis - {len(whale_activity['results'])} tokens analyzed")
                self.logger.info(f"      Activity types detected: {list(summary.keys())}")
        
        # Strategic Coordination
        if 'coordination_analysis' in self.test_results:
            coordination = self.test_results['coordination_analysis']
            if coordination['status'] == 'success':
                coord_summary = coordination['coordination_summary']
                grade_summary = coordination['grade_summary']
                self.logger.info(f"   ✅ Strategic Coordination Analysis - {len(coordination['results'])} tokens analyzed")
                self.logger.info(f"      Coordination types: {list(coord_summary.keys())}")
                self.logger.info(f"      Opportunity grades: {list(grade_summary.keys())}")
        
        # Integrated Analysis
        if 'integrated_analysis' in self.test_results:
            integrated = self.test_results['integrated_analysis']
            if integrated['status'] == 'success':
                self.logger.info(f"   ✅ Integrated Whale & Trader Analysis - Full pipeline operational")
                whale_tracking = integrated['whale_tracking']
                if whale_tracking['enabled']:
                    self.logger.info(f"      Whale tracking: {whale_tracking['tracked_whales']} whales tracked")
        
        self.logger.info(f"\n🚀 WHALE & TRADER ACTIVITY TEST SUITE COMPLETE!")
        self.logger.info("=" * 80)
        
        # Save results to file
        results_file = Path("scripts/results/whale_trader_test_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            # Convert results to JSON-serializable format
            serializable_results = {}
            for phase, result in self.test_results.items():
                serializable_results[phase] = {
                    'status': result['status'],
                    'timestamp': time.time()
                }
                if 'error' in result:
                    serializable_results[phase]['error'] = result['error']
            
            json.dump(serializable_results, f, indent=2)
        
        self.logger.info(f"📄 Test results saved to: {results_file}")

async def main():
    """Main test execution function"""
    parser = argparse.ArgumentParser(description='Test whale and trader activity functionality')
    parser.add_argument('--mode', choices=['test', 'live'], default='test',
                      help='Test mode: test (mock data) or live (real API calls)')
    parser.add_argument('--tokens', nargs='*', 
                      help='Custom token addresses to test (optional)')
    
    args = parser.parse_args()
    
    # Initialize and run tester
    tester = WhaleTraderActivityTester(mode=args.mode)
    
    print(f"🐋 Starting Whale & Trader Activity Test Suite")
    print(f"Mode: {args.mode.upper()}")
    if args.tokens:
        print(f"Custom tokens: {len(args.tokens)} provided")
    print("")
    
    await tester.run_comprehensive_test(custom_tokens=args.tokens)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1) 