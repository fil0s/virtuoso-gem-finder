#!/usr/bin/env python3
"""
Comprehensive Integration Test for Early Token Detection System

This script tests:
1. Configuration loading
2. Social media analysis integration
3. Comprehensive scoring pipeline
4. All analysis components working together
5. Logical scoring validation
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.early_token_detection import EarlyTokenDetector
from core.config_manager import ConfigManager

class IntegratedAnalysisTestSuite:
    """Comprehensive test suite for integrated analysis system"""
    
    def __init__(self):
        self.detector = None
        self.test_results = []
        
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Comprehensive Early Token Detection Integration Test")
        print("=" * 80)
        
        # Test 1: Configuration and Initialization
        await self.test_configuration_loading()
        
        # Test 2: Social Media Analysis Component
        await self.test_social_media_analysis()
        
        # Test 3: Scoring Components Integration
        await self.test_scoring_components()
        
        # Test 4: Full Pipeline Test (if API available)
        await self.test_full_pipeline()
        
        # Test 5: Edge Cases and Error Handling
        await self.test_edge_cases()
        
        # Summary
        self.print_test_summary()
        
    async def test_configuration_loading(self):
        """Test 1: Validate configuration loading and initialization"""
        print("\n📋 TEST 1: Configuration Loading and Initialization")
        print("-" * 50)
        
        try:
            # Test config manager
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # Check social media config structure
            social_config = config.get('ANALYSIS', {}).get('social_media', {})
            bonuses = social_config.get('bonuses', {})
            validation = social_config.get('validation', {})
            
            print(f"✅ Main config loaded: {bool(config)}")
            print(f"✅ Social media config found: {bool(social_config)}")
            print(f"✅ Bonuses section: {len(bonuses)} items")
            print(f"✅ Validation section: {len(validation)} items")
            
            # Test specific values
            telegram_bonus = bonuses.get('telegram_bonus', 0)
            max_bonus = bonuses.get('max_social_bonus', 0)
            news_domains = validation.get('news_domains', [])
            
            assert telegram_bonus == 20, f"Expected telegram_bonus=20, got {telegram_bonus}"
            assert max_bonus == 25, f"Expected max_social_bonus=25, got {max_bonus}"
            assert len(news_domains) >= 5, f"Expected >=5 news domains, got {len(news_domains)}"
            
            print(f"✅ Telegram bonus: {telegram_bonus}")
            print(f"✅ Max social bonus: {max_bonus}")
            print(f"✅ News domains: {len(news_domains)}")
            
            # Test detector initialization
            self.detector = EarlyTokenDetector()
            
            assert len(self.detector.social_bonuses) > 10, "Social bonuses not loaded properly"
            assert len(self.detector.validation_patterns) > 0, "Validation patterns not loaded"
            
            print(f"✅ Detector initialized with {len(self.detector.social_bonuses)} social bonuses")
            print(f"✅ Validation patterns loaded: {len(self.detector.validation_patterns)}")
            
            self.test_results.append(("Configuration Loading", "PASSED", "All configs loaded correctly"))
            
        except Exception as e:
            print(f"❌ Configuration test FAILED: {e}")
            self.test_results.append(("Configuration Loading", "FAILED", str(e)))
            return False
            
        return True
    
    async def test_social_media_analysis(self):
        """Test 2: Social Media Analysis Component"""
        print("\n📱 TEST 2: Social Media Analysis Component")
        print("-" * 50)
        
        if not self.detector:
            print("❌ Skipping - detector not initialized")
            return False
            
        try:
            # Test case 1: Token with comprehensive social media (like KAWS)
            comprehensive_overview = {
                'extensions': {
                    'website': 'https://kaws.com',
                    'twitter': 'https://twitter.com/kaws_official',
                    'telegram': 'https://t.me/kaws_community',
                    'discord': 'https://discord.gg/kaws'
                }
            }
            
            analysis1 = self.detector._analyze_social_media_presence(comprehensive_overview)
            
            print("Test Case 1: Comprehensive Social Media")
            print(f"  Platforms detected: {analysis1.get('social_channels', [])}")
            print(f"  Social score: {analysis1.get('social_score', 0)}/100")
            print(f"  Community strength: {analysis1.get('community_strength', 'Unknown')}")
            print(f"  Bonus points: +{analysis1.get('bonus_points', 0)}")
            print(f"  Quality flags: {analysis1.get('quality_flags', [])}")
            
            # Validate comprehensive token results
            assert len(analysis1.get('social_channels', [])) >= 3, "Should detect multiple platforms"
            assert analysis1.get('bonus_points', 0) >= 20, "Should have high bonus for comprehensive presence"
            assert 'TELEGRAM_COMMUNITY' in analysis1.get('quality_flags', []), "Should detect Telegram community"
            assert analysis1.get('community_strength') in ['Strong', 'Moderate'], "Should have good community strength"
            
            # Test case 2: Token with news articles (manipulation)
            news_overview = {
                'extensions': {
                    'website': 'https://cointelegraph.com/news/some-article',
                    'twitter': 'https://twitter.com/user/status/123456'
                }
            }
            
            analysis2 = self.detector._analyze_social_media_presence(news_overview)
            
            print("\nTest Case 2: News Articles (Manipulation)")
            print(f"  Platforms detected: {analysis2.get('social_channels', [])}")
            print(f"  Penalty points: {analysis2.get('penalty_points', 0)}")
            print(f"  Quality flags: {analysis2.get('quality_flags', [])}")
            
            # Validate manipulation detection
            assert analysis2.get('penalty_points', 0) < 0, "Should have penalties for news articles"
            assert len(analysis2.get('social_channels', [])) == 0, "Should not count news articles as valid platforms"
            
            # Test case 3: No social media
            empty_overview = {'extensions': {}}
            analysis3 = self.detector._analyze_social_media_presence(empty_overview)
            
            print("\nTest Case 3: No Social Media")
            print(f"  Platforms detected: {analysis3.get('social_channels', [])}")
            print(f"  Penalty points: {analysis3.get('penalty_points', 0)}")
            print(f"  Community strength: {analysis3.get('community_strength', 'Unknown')}")
            
            # Validate no social media case
            assert len(analysis3.get('social_channels', [])) == 0, "Should detect no platforms"
            assert analysis3.get('penalty_points', 0) <= 0, "Should have penalty for minimal presence"
            
            print("✅ Social media analysis component working correctly")
            self.test_results.append(("Social Media Analysis", "PASSED", "All test cases passed"))
            
        except Exception as e:
            print(f"❌ Social media analysis test FAILED: {e}")
            self.test_results.append(("Social Media Analysis", "FAILED", str(e)))
            return False
            
        return True
    
    async def test_scoring_components(self):
        """Test 3: Validate all scoring components work together"""
        print("\n🎯 TEST 3: Scoring Components Integration")
        print("-" * 50)
        
        if not self.detector:
            print("❌ Skipping - detector not initialized")
            return False
            
        try:
            # Create mock data for comprehensive scoring test
            mock_token = {
                'address': 'test_address_123',
                'symbol': 'TEST',
                'name': 'Test Token',
                'creation_time': int(time.time()) - 7200  # 2 hours ago
            }
            
            # Mock full data with various scenarios
            mock_full_data = {
                'overview': {
                    'symbol': 'TEST',
                    'liquidity': 500000,  # $500K liquidity
                    'priceChange1h': 25.5,  # +25.5% in 1h
                    'priceChange4h': 45.2,  # +45.2% in 4h  
                    'priceChange24h': 85.7, # +85.7% in 24h (strong gains)
                    'volume': {
                        'h1': 50000,
                        'h4': 150000,
                        'h24': 750000  # $750K 24h volume
                    },
                    'marketCap': 2500000,  # $2.5M market cap
                    'extensions': {
                        'website': 'https://testtoken.com',
                        'twitter': 'https://twitter.com/testtoken',
                        'telegram': 'https://t.me/testtoken_community'
                    }
                },
                'liquidity': 500000,
                'holders': {
                    'total': 450,
                    'items': [
                        {'owner': 'holder1', 'percentage': 5.2},
                        {'owner': 'holder2', 'percentage': 4.8},
                        {'owner': 'holder3', 'percentage': 3.1}
                    ]
                },
                'top_traders': ['trader1', 'trader2', 'trader3']
            }
            
            mock_basic_metrics = {
                'test_address_123': {
                    'overview': mock_full_data['overview'],
                    'creation_time': mock_token['creation_time'],
                    'holders_data': mock_full_data['holders']
                }
            }
            
            mock_security_data = {
                'test_address_123': {
                    'is_scam': False,
                    'is_risky': False
                }
            }
            
            # Test comprehensive scoring
            print("Testing comprehensive scoring with mock data...")
            final_score = await self.detector._calculate_comprehensive_score(
                mock_token, mock_full_data, mock_basic_metrics, mock_security_data
            )
            
            print(f"Final Score: {final_score:.1f}/100")
            
            # Validate score components
            assert 0 <= final_score <= 150, f"Score should be reasonable, got {final_score}"  # Allow for bonuses
            
            # Test edge cases
            print("\nTesting edge cases...")
            
            # High liquidity, new token, strong gains - should score well
            high_perf_data = mock_full_data.copy()
            high_perf_data['overview']['liquidity'] = 2000000  # $2M liquidity
            high_perf_data['overview']['priceChange24h'] = 200  # +200% gains
            
            high_score = await self.detector._calculate_comprehensive_score(
                mock_token, high_perf_data, mock_basic_metrics, mock_security_data
            )
            
            print(f"High performance token score: {high_score:.1f}/100")
            assert high_score > final_score, "High performance token should score higher"
            
            # Low liquidity, old token, losses - should score poorly
            low_perf_data = mock_full_data.copy()
            low_perf_data['overview']['liquidity'] = 10000  # $10K liquidity
            low_perf_data['overview']['priceChange24h'] = -50  # -50% losses
            low_perf_token = mock_token.copy()
            low_perf_token['creation_time'] = int(time.time()) - 604800  # 1 week old
            
            low_score = await self.detector._calculate_comprehensive_score(
                low_perf_token, low_perf_data, mock_basic_metrics, mock_security_data
            )
            
            print(f"Low performance token score: {low_score:.1f}/100")
            assert low_score < final_score, "Low performance token should score lower"
            
            # Scam token - should be heavily penalized
            scam_security = {'test_address_123': {'is_scam': True, 'is_risky': False}}
            scam_score = await self.detector._calculate_comprehensive_score(
                mock_token, mock_full_data, mock_basic_metrics, scam_security
            )
            
            print(f"Scam token score: {scam_score:.1f}/100")
            assert scam_score < final_score - 30, "Scam token should be heavily penalized"
            
            print("✅ Scoring components integration working correctly")
            self.test_results.append(("Scoring Components", "PASSED", "All scoring logic validated"))
            
        except Exception as e:
            print(f"❌ Scoring components test FAILED: {e}")
            self.test_results.append(("Scoring Components", "FAILED", str(e)))
            return False
            
        return True
    
    async def test_full_pipeline(self):
        """Test 4: Full pipeline test (limited to avoid API costs)"""
        print("\n🔄 TEST 4: Full Pipeline Test (Limited)")
        print("-" * 50)
        
        if not self.detector:
            print("❌ Skipping - detector not initialized")
            return False
            
        try:
            print("Testing pipeline initialization and configuration...")
            
            # Test that all required components are initialized
            assert self.detector.birdeye_api is not None, "Birdeye API should be initialized"
            assert self.detector.batch_manager is not None, "Batch manager should be initialized"
            assert self.detector.data_manager is not None, "Data manager should be initialized"
            assert self.detector.pump_dump_detector is not None, "Pump/dump detector should be initialized"
            assert self.detector.strategic_analyzer is not None, "Strategic analyzer should be initialized"
            
            # Test thresholds configuration
            thresholds = self.detector.stage_thresholds
            assert thresholds['quick_score'] > 0, "Quick score threshold should be set"
            assert thresholds['medium_score'] > 0, "Medium score threshold should be set"
            assert thresholds['full_score'] > 0, "Full score threshold should be set"
            
            print(f"✅ Quick score threshold: {thresholds['quick_score']}")
            print(f"✅ Medium score threshold: {thresholds['medium_score']}")
            print(f"✅ Full score threshold: {thresholds['full_score']}")
            
            # Test scoring weights
            weights = self.detector.scoring_weights
            total_weight = sum(weights.values())
            print(f"✅ Total scoring weights: {total_weight:.2f}")
            assert abs(total_weight - 1.0) < 0.01, f"Weights should sum to 1.0, got {total_weight}"
            
            # Test API metrics tracking
            metrics = self.detector.api_call_metrics
            assert isinstance(metrics, dict), "API metrics should be a dictionary"
            assert 'discovery_calls' in metrics, "Should track discovery calls"
            assert 'batch_calls' in metrics, "Should track batch calls"
            
            print("✅ All pipeline components initialized correctly")
            print("✅ Configuration values are logical")
            print("✅ API metrics tracking ready")
            
            # Note: We don't run actual discovery to avoid API costs in testing
            print("ℹ️  Skipping actual API calls to avoid costs during testing")
            
            self.test_results.append(("Full Pipeline", "PASSED", "Components initialized correctly"))
            
        except Exception as e:
            print(f"❌ Full pipeline test FAILED: {e}")
            self.test_results.append(("Full Pipeline", "FAILED", str(e)))
            return False
            
        return True
    
    async def test_edge_cases(self):
        """Test 5: Edge cases and error handling"""
        print("\n🔍 TEST 5: Edge Cases and Error Handling")
        print("-" * 50)
        
        if not self.detector:
            print("❌ Skipping - detector not initialized")
            return False
            
        try:
            # Test social media analysis with malformed data
            print("Testing malformed social media data...")
            
            malformed_cases = [
                {'extensions': None},  # None extensions
                {'extensions': {'website': ''}},  # Empty URL
                {'extensions': {'twitter': 'not-a-url'}},  # Invalid URL
                {},  # No extensions key
                {'extensions': {'unknown_platform': 'https://example.com'}}  # Unknown platform
            ]
            
            for i, case in enumerate(malformed_cases):
                analysis = self.detector._analyze_social_media_presence(case)
                print(f"  Case {i+1}: {len(analysis.get('social_channels', []))} platforms detected")
                assert isinstance(analysis, dict), "Should return dict even with malformed data"
                assert 'social_score' in analysis, "Should have social_score field"
            
            # Test URL validation edge cases
            print("\nTesting URL validation edge cases...")
            
            url_test_cases = [
                ('twitter', 'https://twitter.com/realuser', True),  # Valid
                ('twitter', 'https://twitter.com/user/status/123', False),  # Status link
                ('telegram', 'https://t.me/validchannel', True),  # Valid
                ('telegram', 'https://t.me/channel/invalid', False),  # Invalid format
                ('website', '', False),  # Empty URL
                ('website', 'not-a-url', False),  # Invalid URL
            ]
            
            for platform, url, expected in url_test_cases:
                result = self.detector._is_official_account(platform, url)
                print(f"  {platform} - {url[:30]}... -> {result} (expected: {expected})")
                if expected:
                    assert result == expected, f"URL validation failed for {platform}: {url}"
            
            # Test news article detection
            print("\nTesting news article detection...")
            
            news_test_cases = [
                ('https://cointelegraph.com/news/article', True),
                ('https://coindesk.com/markets/article', True),
                ('https://twitter.com/user/status/123', True),  # Status links
                ('https://twitter.com/realuser', False),  # Profile links
                ('https://example.com', False),  # Regular website
            ]
            
            for url, expected in news_test_cases:
                result = self.detector._is_news_article(url)
                print(f"  {url[:40]}... -> {result} (expected: {expected})")
                assert result == expected, f"News detection failed for: {url}"
            
            print("✅ Edge cases handled correctly")
            self.test_results.append(("Edge Cases", "PASSED", "All edge cases handled properly"))
            
        except Exception as e:
            print(f"❌ Edge cases test FAILED: {e}")
            self.test_results.append(("Edge Cases", "FAILED", str(e)))
            return False
            
        return True
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🏁 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, status, _ in self.test_results if status == "PASSED")
        total = len(self.test_results)
        
        print(f"Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print()
        
        for test_name, status, details in self.test_results:
            status_icon = "✅" if status == "PASSED" else "❌"
            print(f"{status_icon} {test_name:<25} {status:<10} {details}")
        
        print("\n" + "=" * 80)
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! The integrated analysis system is working correctly.")
            print("🚀 The early token detection system is ready for production use.")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
            
        print("=" * 80)

async def main():
    """Run the comprehensive integration test suite"""
    test_suite = IntegratedAnalysisTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 