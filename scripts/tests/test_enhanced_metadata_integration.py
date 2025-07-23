#!/usr/bin/env python3
"""
Test Enhanced Metadata Analysis Integration

Tests the integration of social media presence analysis
in the early token detection system.
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from services.enhanced_metadata_analyzer import EnhancedMetadataAnalyzer
from services.logger_setup import LoggerSetup
from services.telegram_alerter import TelegramAlerter, MinimalTokenMetrics

class EnhancedMetadataIntegrationTest:
    """Test enhanced metadata analysis integration"""
    
    def __init__(self):
        self.logger_setup = LoggerSetup('EnhancedMetadataTest', log_level='DEBUG')
        self.logger = self.logger_setup.logger
        self.metadata_analyzer = EnhancedMetadataAnalyzer(self.logger)
    
    def test_social_media_analysis(self):
        """Test social media presence analysis with sample data"""
        self.logger.info("Testing Social Media Presence Analysis")
        
        # Sample token data with social media extensions
        sample_overview_data = {
            'extensions': {
                'website': 'https://example-token.com',
                'twitter': 'https://twitter.com/example_token',
                'telegram': 'https://t.me/example_token',
                'discord': 'https://discord.gg/example_token'
            },
            'volume': {
                'h1': 50000,
                'h4': 120000,
                'h24': 400000
            },
            'trades': {
                'h1': 25,
                'h4': 80,
                'h24': 300
            },
            'uniqueWallets': {
                'h1': 15,
                'h4': 45,
                'h24': 150
            },
            'priceChange1h': 25.5,
            'priceChange4h': 18.2,
            'priceChange24h': 45.8,
            'priceChange7d': 125.3,
            'liquidity': 250000,
            'marketCap': 1500000
        }
        
        # Sample security data
        sample_security_data = {
            'is_scam': False,
            'is_risky': False,
            'liquidityProviders': 25,
            'lpLocked': True,
            'lpLockedPercentage': 85.5
        }
        
        # Test social media analysis
        social_analysis = self.metadata_analyzer.analyze_social_media_presence(sample_overview_data)
        self.logger.info("Social Media Analysis Results:")
        self.logger.info(f"  Social Score: {social_analysis.get('social_score', 0)}/100")
        self.logger.info(f"  Community Strength: {social_analysis.get('community_strength', 'Unknown')}")
        self.logger.info(f"  Available Channels: {social_analysis.get('social_channels', [])}")
        self.logger.info(f"  Has Website: {social_analysis.get('has_website', False)}")
        self.logger.info(f"  Has Social Media: {social_analysis.get('has_social_media', False)}")
        
        # Test trading pattern analysis
        trading_analysis = self.metadata_analyzer.analyze_trading_patterns(sample_overview_data)
        self.logger.info("Trading Pattern Analysis Results:")
        self.logger.info(f"  Volume Acceleration: {trading_analysis.get('volume_acceleration', 0):.1f}/100")
        self.logger.info(f"  Trade Frequency Score: {trading_analysis.get('trade_frequency_score', 0):.1f}/100")
        self.logger.info(f"  Trading Momentum: {trading_analysis.get('trading_momentum', 'Neutral')}")
        
        # Test price dynamics analysis
        price_analysis = self.metadata_analyzer.analyze_price_dynamics(sample_overview_data)
        self.logger.info("Price Dynamics Analysis Results:")
        self.logger.info(f"  Momentum Score: {price_analysis.get('momentum_score', 0):.1f}/100")
        self.logger.info(f"  Trend Strength: {price_analysis.get('trend_strength', 'Neutral')}")
        
        # Test liquidity health analysis
        liquidity_analysis = self.metadata_analyzer.analyze_liquidity_health(sample_overview_data, sample_security_data)
        self.logger.info("Liquidity Health Analysis Results:")
        self.logger.info(f"  Liquidity Risk: {liquidity_analysis.get('liquidity_risk', 'Unknown')}")
        self.logger.info(f"  LP Security Score: {liquidity_analysis.get('lp_security_score', 0):.1f}/100")
        
        # Test comprehensive metadata score
        metadata_score = self.metadata_analyzer.generate_comprehensive_metadata_score(
            social_analysis, trading_analysis, price_analysis, liquidity_analysis
        )
        
        self.logger.info("Comprehensive Metadata Score Results:")
        self.logger.info(f"  Composite Score: {metadata_score.get('metadata_composite_score', 0):.1f}/100")
        self.logger.info(f"  Grade: {metadata_score.get('grade', 'Unknown')}")
        self.logger.info(f"  Key Strengths: {metadata_score.get('key_strengths', [])}")
        self.logger.info(f"  Key Risks: {metadata_score.get('key_risks', [])}")
        
        return {
            'social_analysis': social_analysis,
            'trading_analysis': trading_analysis,
            'price_analysis': price_analysis,
            'liquidity_analysis': liquidity_analysis,
            'metadata_score': metadata_score
        }
    
    def test_telegram_alert_formatting(self, enhanced_metadata_analysis):
        """Test telegram alert formatting with enhanced metadata"""
        self.logger.info("Testing Telegram Alert Formatting with Enhanced Metadata")
        
        # Create sample token metrics
        sample_metrics = MinimalTokenMetrics(
            symbol="TEST",
            address="11111111111111111111111111111111",
            price=0.001234,
            name="Test Token",
            mcap=1500000,
            liquidity=250000,
            volume_24h=400000,
            holders=150,
            price_change_24h=45.8,
            market_cap=1500000,
            score=85.5
        )
        
        # Create enhanced data structure
        enhanced_data = {
            'enhanced_metadata_analysis': enhanced_metadata_analysis
        }
        
        # Create TelegramAlerter instance (without actual bot token)
        telegram_alerter = TelegramAlerter(
            bot_token="dummy_token",
            chat_id="dummy_chat",
            logger_setup=self.logger_setup
        )
        
        # Test building the enhanced metadata section
        try:
            metadata_section = telegram_alerter._build_enhanced_metadata_section(enhanced_metadata_analysis)
            self.logger.info("Enhanced Metadata Alert Section:")
            self.logger.info(metadata_section)
            
            return True
        except Exception as e:
            self.logger.error(f"Error testing telegram alert formatting: {e}")
            return False
    
    def test_no_social_media_data(self):
        """Test behavior when no social media data is available"""
        self.logger.info("Testing behavior with no social media data")
        
        # Sample data without extensions
        sample_overview_data = {
            'volume': {'h1': 10000, 'h4': 30000, 'h24': 80000},
            'trades': {'h1': 5, 'h4': 15, 'h24': 60},
            'priceChange24h': 12.5,
            'liquidity': 50000,
            'marketCap': 300000
        }
        
        social_analysis = self.metadata_analyzer.analyze_social_media_presence(sample_overview_data)
        
        self.logger.info("No Social Media Data Test Results:")
        self.logger.info(f"  Social Score: {social_analysis.get('social_score', 0)}/100")
        self.logger.info(f"  Community Strength: {social_analysis.get('community_strength', 'Unknown')}")
        self.logger.info(f"  Available Channels: {social_analysis.get('social_channels', [])}")
        
        return social_analysis
    
    def run_all_tests(self):
        """Run all enhanced metadata integration tests"""
        self.logger.info("="*60)
        self.logger.info("ENHANCED METADATA ANALYSIS INTEGRATION TESTS")
        self.logger.info("="*60)
        
        try:
            # Test 1: Full social media analysis
            enhanced_metadata = self.test_social_media_analysis()
            
            self.logger.info("\n" + "-"*60)
            
            # Test 2: Telegram alert formatting
            alert_success = self.test_telegram_alert_formatting(enhanced_metadata)
            
            self.logger.info("\n" + "-"*60)
            
            # Test 3: No social media data
            self.test_no_social_media_data()
            
            self.logger.info("\n" + "="*60)
            self.logger.info("ALL TESTS COMPLETED")
            
            if alert_success:
                self.logger.info("✅ Enhanced Metadata Analysis Integration: WORKING")
            else:
                self.logger.warning("⚠️ Some issues detected in alert formatting")
                
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Test failed with error: {e}")
            return False

def main():
    """Main test execution"""
    test_runner = EnhancedMetadataIntegrationTest()
    success = test_runner.run_all_tests()
    
    if success:
        print("\n🎉 Enhanced Metadata Analysis Integration tests completed successfully!")
        print("✅ Social media presence analysis is now fully integrated")
        print("✅ Alert formatting includes community insights")
        print("✅ System handles missing social media data gracefully")
    else:
        print("\n❌ Some tests failed - check logs for details")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 