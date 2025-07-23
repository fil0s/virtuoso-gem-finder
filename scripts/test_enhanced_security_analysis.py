#!/usr/bin/env python3
"""
Enhanced Security Analysis Test Script

This script tests the enhanced security analysis with concentration metrics
from the Birdeye token security endpoint.
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv()

from services.early_token_detection import EarlyTokenDetector
from api.birdeye_connector import BirdeyeAPI
from services.logger_setup import LoggerSetup
from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from core.config_manager import ConfigManager


class EnhancedSecurityAnalysisTester:
    """Test enhanced security analysis with concentration metrics"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Initialize logger
        self.logger = LoggerSetup("test_enhanced_security")
        
        # Initialize services
        cache_config = self.config.get('CACHING', {
            "enabled": True,
            "default_ttl_seconds": 3600,
            "max_memory_items": 512,
            "file_cache_dir": "temp/app_cache"
        })
        self.cache_manager = CacheManager(cache_config)
        
        # Initialize rate limiter  
        birdeye_config = self.config.get('BIRDEYE', {})
        self.rate_limiter = RateLimiterService(birdeye_config)
        
        # Initialize early token detector (use same config to ensure API key consistency)
        self.detector = EarlyTokenDetector(self.config, enable_whale_tracking=False)
        
        # Use the detector's BirdeyeAPI instance which has the proper API key
        self.birdeye_api = self.detector.birdeye_api
        
        self.test_results = {}
        
    async def run_tests(self):
        """Run comprehensive enhanced security analysis tests"""
        self.logger.info("🚀 Starting Enhanced Security Analysis Testing...")
        self.logger.info("=" * 80)
        
        test_cases = [
            self._test_security_data_extraction,
            self._test_concentration_analysis,
            self._test_position_sizing_recommendations,
            self._test_medium_analysis_enhancement,
            self._test_full_analysis_enhancement,
            self._test_edge_cases
        ]
        
        for test_case in test_cases:
            try:
                await test_case()
            except Exception as e:
                self.logger.error(f"❌ Test failed: {test_case.__name__}: {e}")
                self.test_results[test_case.__name__] = {"status": "failed", "error": str(e)}
        
        # Print summary
        self._print_test_summary()
        
    async def _test_security_data_extraction(self):
        """Test 1: Verify security data extraction and parsing"""
        self.logger.info("\n🔍 TEST 1: Security Data Extraction and Parsing")
        self.logger.info("-" * 60)
        
        # Get some trending tokens for testing
        trending_tokens = await self.birdeye_api.get_trending_tokens()
        if not trending_tokens:
            self.logger.warning("No trending tokens found, using fallback addresses")
            test_addresses = [
                "So11111111111111111111111111111111111111112",  # SOL
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            ]
        else:
            test_addresses = trending_tokens[:3]
        
        successful_tests = 0
        
        for i, address in enumerate(test_addresses):
            try:
                self.logger.info(f"\n📊 Testing security data for token {i+1}/3: {address[:8]}...")
                
                # Fetch security data
                security_data = await self.birdeye_api.get_token_security(address)
                
                if security_data:
                    self.logger.info(f"✅ Security data retrieved for {address[:8]}")
                    
                    # Check for concentration metrics
                    concentration_metrics = [
                        'top10HolderPercent', 'top10UserPercent', 'creatorPercentage',
                        'top10HolderBalance', 'totalSupply'
                    ]
                    
                    available_metrics = []
                    for metric in concentration_metrics:
                        if metric in security_data:
                            available_metrics.append(metric)
                            value = security_data[metric]
                            if metric.endswith('Percent'):
                                self.logger.info(f"  📈 {metric}: {value:.2%}")
                            else:
                                self.logger.info(f"  📈 {metric}: {value:,.0f}")
                    
                    self.logger.info(f"  🎯 Available concentration metrics: {len(available_metrics)}/{len(concentration_metrics)}")
                    
                    # Test concentration analysis
                    if len(available_metrics) >= 3:
                        concentration_analysis = self.detector._analyze_token_concentration(
                            security_data, f"TEST_{i+1}"
                        )
                        self.logger.info(f"  🔍 Concentration Analysis:")
                        self.logger.info(f"    Risk Level: {concentration_analysis['risk_level']}")
                        self.logger.info(f"    Summary: {concentration_analysis['summary']}")
                        self.logger.info(f"    Score Impact: {concentration_analysis['score']:+d}")
                        successful_tests += 1
                    else:
                        self.logger.warning(f"  ⚠️ Insufficient concentration metrics for analysis")
                        
                else:
                    self.logger.warning(f"❌ No security data for {address[:8]}")
                    
            except Exception as e:
                self.logger.error(f"❌ Error testing {address[:8]}: {e}")
        
        self.test_results['security_data_extraction'] = {
            "status": "success" if successful_tests > 0 else "failed",
            "successful_tests": successful_tests,
            "total_tests": len(test_addresses)
        }
        
        self.logger.info(f"\n✅ Security data extraction test completed: {successful_tests}/{len(test_addresses)} successful")
        
    async def _test_concentration_analysis(self):
        """Test 2: Test concentration analysis with various scenarios"""
        self.logger.info("\n🎯 TEST 2: Concentration Analysis Scenarios")
        self.logger.info("-" * 60)
        
        # Create test scenarios with different concentration levels
        test_scenarios = [
            {
                "name": "High Concentration Risk",
                "data": {
                    "top10HolderPercent": 0.85,  # 85%
                    "top10UserPercent": 0.60,    # 60% 
                    "creatorPercentage": 0.20,   # 20%
                    "top10HolderBalance": 850000000,
                    "totalSupply": 1000000000
                }
            },
            {
                "name": "Medium Concentration Risk", 
                "data": {
                    "top10HolderPercent": 0.55,  # 55%
                    "top10UserPercent": 0.35,    # 35%
                    "creatorPercentage": 0.08,   # 8%
                    "top10HolderBalance": 550000000,
                    "totalSupply": 1000000000
                }
            },
            {
                "name": "Low Concentration Risk",
                "data": {
                    "top10HolderPercent": 0.25,  # 25%
                    "top10UserPercent": 0.20,    # 20%
                    "creatorPercentage": 0.02,   # 2%
                    "top10HolderBalance": 250000000,
                    "totalSupply": 1000000000
                }
            },
            {
                "name": "Creator Dump Risk",
                "data": {
                    "top10HolderPercent": 0.40,  # 40%
                    "top10UserPercent": 0.25,    # 25%
                    "creatorPercentage": 0.25,   # 25% - High creator risk
                    "top10HolderBalance": 400000000,
                    "totalSupply": 1000000000
                }
            }
        ]
        
        successful_scenarios = 0
        
        for scenario in test_scenarios:
            try:
                self.logger.info(f"\n📊 Testing: {scenario['name']}")
                
                # Test concentration analysis
                analysis = self.detector._analyze_token_concentration(
                    scenario['data'], scenario['name'].replace(' ', '_')
                )
                
                self.logger.info(f"  🎯 Risk Level: {analysis['risk_level']}")
                self.logger.info(f"  📈 Summary: {analysis['summary']}")
                self.logger.info(f"  🚀 Score Impact: {analysis['score']:+d}")
                self.logger.info(f"  📝 Details: {', '.join(analysis['details'])}")
                
                # Test advanced concentration scoring
                advanced_analysis = self.detector._calculate_advanced_concentration_score(
                    scenario['data'], scenario['name'].replace(' ', '_'), 10_000_000  # $10M market cap
                )
                
                self.logger.info(f"  🏆 Advanced Score: {advanced_analysis['score']:.1f}/10")
                self.logger.info(f"  💰 Liquidity Risk: {advanced_analysis['liquidity_risk']}")
                self.logger.info(f"  👤 Creator Risk: {advanced_analysis['creator_risk']}")
                
                # Test position sizing
                position_size = self.detector._get_position_sizing_recommendation(
                    scenario['data'], 10_000_000
                )
                self.logger.info(f"  📊 Position Sizing: {position_size}")
                
                successful_scenarios += 1
                
            except Exception as e:
                self.logger.error(f"❌ Error in scenario '{scenario['name']}': {e}")
        
        self.test_results['concentration_analysis'] = {
            "status": "success" if successful_scenarios == len(test_scenarios) else "failed",
            "successful_scenarios": successful_scenarios,
            "total_scenarios": len(test_scenarios)
        }
        
        self.logger.info(f"\n✅ Concentration analysis test completed: {successful_scenarios}/{len(test_scenarios)} scenarios passed")
        
    async def _test_position_sizing_recommendations(self):
        """Test 3: Position sizing recommendations"""
        self.logger.info("\n💰 TEST 3: Position Sizing Recommendations")
        self.logger.info("-" * 60)
        
        position_test_cases = [
            {"conc": 0.80, "creator": 0.20, "expected": "MICRO_POSITION"},    # 2 risk factors: HIGH_CONCENTRATION (>70%) + HIGH_CREATOR_RISK (>15%)
            {"conc": 0.60, "creator": 0.10, "expected": "REDUCED_POSITION"},  # No risk factors, but 60% > 55% threshold
            {"conc": 0.45, "creator": 0.05, "expected": "NORMAL_POSITION"},   # No risk factors: 45% > 35% threshold
            {"conc": 0.35, "creator": 0.03, "expected": "STANDARD_POSITION"}, # 35% = threshold boundary, so <= 35%
            {"conc": 0.20, "creator": 0.02, "expected": "STANDARD_POSITION"}  # Low concentration < 35%
        ]
        
        correct_recommendations = 0
        
        for i, test_case in enumerate(position_test_cases):
            try:
                security_data = {
                    "top10HolderPercent": test_case["conc"],
                    "creatorPercentage": test_case["creator"],
                    "top10HolderBalance": test_case["conc"] * 1000000000,
                    "totalSupply": 1000000000
                }
                
                recommendation = self.detector._get_position_sizing_recommendation(
                    security_data, 5_000_000  # $5M market cap
                )
                
                self.logger.info(f"  📊 Test {i+1}: Conc={test_case['conc']:.0%}, Creator={test_case['creator']:.0%}")
                self.logger.info(f"    Expected: {test_case['expected']}")
                self.logger.info(f"    Actual: {recommendation}")
                
                if recommendation == test_case["expected"]:
                    self.logger.info(f"    ✅ PASS")
                    correct_recommendations += 1
                else:
                    self.logger.warning(f"    ❌ FAIL - Recommendation mismatch")
                    
            except Exception as e:
                self.logger.error(f"❌ Error in position sizing test {i+1}: {e}")
        
        self.test_results['position_sizing'] = {
            "status": "success" if correct_recommendations == len(position_test_cases) else "partial",
            "correct_recommendations": correct_recommendations,
            "total_tests": len(position_test_cases)
        }
        
        self.logger.info(f"\n✅ Position sizing test completed: {correct_recommendations}/{len(position_test_cases)} correct")
        
    async def _test_medium_analysis_enhancement(self):
        """Test 4: Enhanced medium analysis"""
        self.logger.info("\n🔍 TEST 4: Enhanced Medium Analysis")
        self.logger.info("-" * 60)
        
        # Create mock tokens for testing
        mock_tokens = [
            {"address": "TestToken1", "symbol": "TEST1", "name": "Test Token 1"},
            {"address": "TestToken2", "symbol": "TEST2", "name": "Test Token 2"}
        ]
        
        # Create mock security data
        mock_security_data = {
            "TestToken1": {
                "is_scam": False,
                "is_risky": False,
                "top10HolderPercent": 0.30,  # Good distribution
                "top10UserPercent": 0.25,
                "creatorPercentage": 0.03,
                "totalSupply": 1000000000
            },
            "TestToken2": {
                "is_scam": False,
                "is_risky": True,
                "top10HolderPercent": 0.75,  # High concentration
                "top10UserPercent": 0.50,
                "creatorPercentage": 0.18,   # High creator risk
                "totalSupply": 1000000000
            }
        }
        
        try:
            # Mock the quick scores method to return fixed values
            async def mock_quick_scores(tokens, basic_metrics):
                return [(token, 50.0) for token in tokens]
            
            # Temporarily replace the method
            original_method = self.detector._calculate_quick_scores
            self.detector._calculate_quick_scores = mock_quick_scores
            
            # Test medium scoring
            scored_tokens = await self.detector._calculate_medium_scores(
                mock_tokens, {}, mock_security_data
            )
            
            # Restore original method
            self.detector._calculate_quick_scores = original_method
            
            self.logger.info(f"  📊 Medium analysis results:")
            for token, score in scored_tokens:
                self.logger.info(f"    {token['symbol']}: {score:.1f} points")
            
            # Verify scoring logic
            if len(scored_tokens) == 2:
                token1_score = next(score for token, score in scored_tokens if token['symbol'] == 'TEST1')
                token2_score = next(score for token, score in scored_tokens if token['symbol'] == 'TEST2')
                
                if token1_score > token2_score:
                    self.logger.info(f"  ✅ PASS - Good token scored higher ({token1_score:.1f} > {token2_score:.1f})")
                    self.test_results['medium_analysis'] = {"status": "success"}
                else:
                    self.logger.warning(f"  ❌ FAIL - Poor token scored higher ({token2_score:.1f} > {token1_score:.1f})")
                    self.test_results['medium_analysis'] = {"status": "failed"}
            else:
                self.logger.error(f"  ❌ FAIL - Expected 2 tokens, got {len(scored_tokens)}")
                self.test_results['medium_analysis'] = {"status": "failed"}
                
        except Exception as e:
            self.logger.error(f"❌ Error in medium analysis test: {e}")
            self.test_results['medium_analysis'] = {"status": "failed", "error": str(e)}
        
    async def _test_full_analysis_enhancement(self):
        """Test 5: Enhanced full analysis integration"""
        self.logger.info("\n🚀 TEST 5: Enhanced Full Analysis Integration")
        self.logger.info("-" * 60)
        
        # Test with real token data if available
        try:
            trending_tokens = await self.birdeye_api.get_trending_tokens()
            if trending_tokens:
                test_address = trending_tokens[0]
                
                self.logger.info(f"  📊 Testing full analysis with: {test_address[:8]}...")
                
                # Get security data
                security_data = await self.birdeye_api.get_token_security(test_address)
                
                if security_data:
                    self.logger.info(f"  ✅ Security data retrieved")
                    
                    # Test concentration summary
                    concentration_summary = self.detector._get_concentration_summary(
                        security_data, "FULL_TEST"
                    )
                    
                    self.logger.info(f"  📈 Concentration Summary:")
                    self.logger.info(f"    Risk Level: {concentration_summary['risk_level']}")
                    self.logger.info(f"    Top 10 Holders: {concentration_summary['top10_holders_percent']:.1f}%")
                    self.logger.info(f"    Top 10 Users: {concentration_summary['top10_users_percent']:.1f}%")
                    self.logger.info(f"    Creator: {concentration_summary['creator_percent']:.1f}%")
                    self.logger.info(f"    Score Impact: {concentration_summary['score_impact']:+d}")
                    
                    # Test position sizing
                    position_sizing = self.detector._get_position_sizing_recommendation(
                        security_data, 10_000_000
                    )
                    self.logger.info(f"  💰 Position Sizing: {position_sizing}")
                    
                    self.test_results['full_analysis'] = {"status": "success"}
                    
                else:
                    self.logger.warning(f"  ⚠️ No security data available for testing")
                    self.test_results['full_analysis'] = {"status": "partial", "reason": "no_security_data"}
            else:
                self.logger.warning(f"  ⚠️ No trending tokens available for testing")
                self.test_results['full_analysis'] = {"status": "partial", "reason": "no_test_tokens"}
                
        except Exception as e:
            self.logger.error(f"❌ Error in full analysis test: {e}")
            self.test_results['full_analysis'] = {"status": "failed", "error": str(e)}
        
    async def _test_edge_cases(self):
        """Test 6: Edge cases and error handling"""
        self.logger.info("\n⚠️ TEST 6: Edge Cases and Error Handling")
        self.logger.info("-" * 60)
        
        edge_cases = [
            {"name": "Empty security data", "data": {}},
            {"name": "Missing concentration fields", "data": {"is_scam": False}},
            {"name": "Zero values", "data": {
                "top10HolderPercent": 0,
                "top10UserPercent": 0,
                "creatorPercentage": 0,
                "totalSupply": 0
            }},
            {"name": "Invalid data types", "data": {
                "top10HolderPercent": "invalid",
                "top10UserPercent": None,
                "creatorPercentage": -1
            }}
        ]
        
        successful_edge_cases = 0
        
        for edge_case in edge_cases:
            try:
                self.logger.info(f"  🧪 Testing: {edge_case['name']}")
                
                # These should not crash
                concentration_analysis = self.detector._analyze_token_concentration(
                    edge_case['data'], "EDGE_TEST"
                )
                
                position_sizing = self.detector._get_position_sizing_recommendation(
                    edge_case['data'], 1_000_000
                )
                
                concentration_summary = self.detector._get_concentration_summary(
                    edge_case['data'], "EDGE_TEST"
                )
                
                self.logger.info(f"    ✅ PASS - No crashes, graceful handling")
                self.logger.info(f"    Risk Level: {concentration_analysis['risk_level']}")
                self.logger.info(f"    Position Sizing: {position_sizing}")
                
                successful_edge_cases += 1
                
            except Exception as e:
                self.logger.error(f"    ❌ FAIL - Exception: {e}")
        
        self.test_results['edge_cases'] = {
            "status": "success" if successful_edge_cases == len(edge_cases) else "failed",
            "successful_cases": successful_edge_cases,
            "total_cases": len(edge_cases)
        }
        
        self.logger.info(f"\n✅ Edge cases test completed: {successful_edge_cases}/{len(edge_cases)} handled gracefully")
        
    def _print_test_summary(self):
        """Print comprehensive test summary"""
        self.logger.info("\n" + "=" * 80)
        self.logger.info("🎯 ENHANCED SECURITY ANALYSIS TEST SUMMARY")
        self.logger.info("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'success')
        partial_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'partial')
        failed_tests = sum(1 for result in self.test_results.values() if result.get('status') == 'failed')
        
        self.logger.info(f"📊 Total Tests: {total_tests}")
        self.logger.info(f"✅ Successful: {successful_tests}")
        self.logger.info(f"⚠️ Partial: {partial_tests}")
        self.logger.info(f"❌ Failed: {failed_tests}")
        self.logger.info(f"🎯 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        self.logger.info("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status_icon = {"success": "✅", "partial": "⚠️", "failed": "❌"}.get(result['status'], "❓")
            self.logger.info(f"  {status_icon} {test_name}: {result['status'].upper()}")
            
            if 'error' in result:
                self.logger.info(f"      Error: {result['error']}")
            
        # Overall assessment
        if successful_tests == total_tests:
            self.logger.info("\n🎉 ALL TESTS PASSED - Enhanced security analysis is working perfectly!")
        elif successful_tests + partial_tests == total_tests:
            self.logger.info("\n⚠️ TESTS COMPLETED WITH WARNINGS - Most functionality working")
        else:
            self.logger.warning("\n❌ SOME TESTS FAILED - Review implementation")
        
        self.logger.info("=" * 80)
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.birdeye_api:
            await self.birdeye_api.close_session()
        self.logger.info("🧹 Cleanup completed")


async def main():
    """Main test execution"""
    tester = EnhancedSecurityAnalysisTester()
    
    try:
        await tester.run_tests()
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        tester.logger.error(f"💥 Unexpected error in tests: {e}")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 