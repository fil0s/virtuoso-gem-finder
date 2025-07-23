#!/usr/bin/env python3
"""
🚨 Test Enhanced Telegram Alert System
Tests the new alert format with trading links and detailed scoring breakdown
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.early_gem_detector import EarlyGemDetector

def create_test_token_data():
    """Create comprehensive test token data with full scoring breakdown"""
    return {
        'symbol': 'TESTGEM',
        'name': 'Test Gem Token',
        'address': 'So11111111111111111111111111111111111111112',  # WSOL address for testing
        'score': 185.4,
        'market_cap': 2500000,  # $2.5M
        'liquidity': 450000,    # $450K
        'source': 'pump_fun_stage0',
        'is_fresh_graduate': False,
        'graduation_imminent': False,
        'ultra_early_bonus_eligible': True,
        'enriched': True,
        
        # Scoring breakdown from early gem focused scoring
        'scoring_breakdown': {
            'early_platform_analysis': {
                'score': 48.5,
                'early_signals': [
                    'PUMP_FUN_STAGE_0_LAUNCH',
                    'EXCEPTIONAL_VELOCITY_5K+',
                    'ULTRA_FRESH_0-5_MIN',
                    'PRE_GRADUATION_SWEET_SPOT_50-80%'
                ],
                'pump_fun_stage': 'ULTRA_EARLY',
                'velocity_usd_per_hour': 6500,
                'graduation_progress': 65
            },
            'momentum_analysis': {
                'score': 36.2,
                'volume_surge': 'surging',
                'price_velocity': 'strong_bullish',
                'trading_activity': 85,
                'buy_sell_ratio': 2.8
            },
            'safety_validation': {
                'score': 22.1,
                'security_score': 88,
                'risk_factors': ['low_liquidity'],
                'dex_presence': 7
            },
            'cross_platform_bonus': {
                'score': 8.0,
                'platforms': ['pump_fun', 'birdeye', 'dexscreener'],
                'platform_count': 3
            }
        },
        
        # Enhanced metrics
        'enhanced_metrics': {
            'velocity_score': 0.92,
            'first_100_score': 8.5,
            'liquidity_quality': 7.2,
            'graduation_risk': -2.1
        },
        
        # Velocity confidence data
        'velocity_confidence': {
            'level': 'HIGH',
            'confidence_score': 0.88,
            'coverage_percentage': 83.3,
            'threshold_adjustment': 1.02
        }
    }

def create_test_fresh_graduate_data():
    """Create test data for fresh graduate token"""
    return {
        'symbol': 'FRESHGRAD',
        'name': 'Fresh Graduate Token',
        'address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC address for testing
        'score': 168.2,
        'market_cap': 850000,   # $850K
        'liquidity': 125000,    # $125K
        'source': 'moralis_graduated',
        'is_fresh_graduate': True,
        'graduation_imminent': False,
        'ultra_early_bonus_eligible': False,
        'enriched': True,
        
        # Simplified scoring breakdown for fast track
        'scoring_breakdown': {
            'base_score': 45.0,
            'freshness_bonus': 15.0,
            'market_cap_bonus': 7.0,
            'graduation_bonus': 8.0,
            'urgency_level': '🔥 FRESH',
            'total_score': 75.0,
            'scoring_method': 'fresh_graduate_fast_track',
            'hours_since_graduation': 0.8,
            'market_cap': 850000
        },
        
        # Enhanced metrics
        'enhanced_metrics': {
            'velocity_score': 0.0,  # Not available for fast track
            'first_100_score': 0.0,
            'liquidity_quality': 6.0,
            'graduation_risk': -8.0
        },
        
        # No velocity confidence for fast track
        'velocity_confidence': {}
    }

def create_test_pre_graduation_data():
    """Create test data for pre-graduation token"""
    return {
        'symbol': 'PREGRAD',
        'name': 'Pre Graduation Gem',
        'address': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT address for testing
        'score': 195.8,
        'market_cap': 4200000,  # $4.2M
        'liquidity': 680000,    # $680K
        'source': 'moralis_bonding',
        'is_fresh_graduate': False,
        'graduation_imminent': True,
        'ultra_early_bonus_eligible': False,
        'enriched': True,
        
        # Pre-graduation scoring breakdown
        'scoring_breakdown': {
            'early_platform_analysis': {
                'score': 50.0,  # Max score for imminent graduation
                'early_signals': [
                    'IMMINENT_GRADUATION_95%+',
                    'STRONG_MARKET_CAP',
                    'PRE_GRADUATION_DISCOVERY'
                ],
                'bonding_curve_progress': 96.5,
                'estimated_graduation_hours': 0.3
            }
        },
        
        # Enhanced metrics
        'enhanced_metrics': {
            'velocity_score': 0.95,
            'first_100_score': 9.2,
            'liquidity_quality': 8.8,
            'graduation_risk': 2.5  # High graduation risk (positive)
        },
        
        # Velocity confidence data
        'velocity_confidence': {
            'level': 'EARLY_DETECTION',
            'confidence_score': 0.95,
            'coverage_percentage': 66.7,
            'threshold_adjustment': 0.95  # 5% bonus
        }
    }

async def test_enhanced_alerts():
    """Test the enhanced alert system with different token types"""
    print("🚨 TESTING ENHANCED TELEGRAM ALERT SYSTEM")
    print("=" * 60)
    
    try:
        # Initialize detector
        detector = EarlyGemDetector(debug_mode=True)
        
        # Test tokens
        test_tokens = [
            ("Ultra Early Token", create_test_token_data()),
            ("Fresh Graduate", create_test_fresh_graduate_data()),
            ("Pre-Graduation Token", create_test_pre_graduation_data())
        ]
        
        print(f"📱 Telegram Alerts: {'✅ ENABLED' if detector.telegram_alerter else '❌ DISABLED'}")
        print()
        
        for test_name, token_data in test_tokens:
            print(f"🧪 Testing {test_name}:")
            print(f"   💎 Symbol: {token_data['symbol']}")
            print(f"   📊 Score: {token_data['score']:.1f}")
            print(f"   💰 Market Cap: ${token_data['market_cap']:,.0f}")
            print(f"   🔍 Source: {token_data['source']}")
            print()
            
            # Send test alert
            if detector.telegram_alerter:
                detector._send_early_gem_alert(token_data)
                print(f"   ✅ Alert sent for {token_data['symbol']}")
            else:
                print(f"   ⚠️ Telegram not configured - showing alert format:")
                # Create a mock alert to show the format
                detector.telegram_alerter = MockTelegramAlerter()
                detector._send_early_gem_alert(token_data)
                detector.telegram_alerter = None
            
            print("-" * 40)
        
        print("✅ Enhanced alert testing completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

class MockTelegramAlerter:
    """Mock Telegram alerter to show alert format without sending"""
    
    def send_message(self, message: str) -> bool:
        print("📱 MOCK TELEGRAM ALERT:")
        print("=" * 50)
        print(message)
        print("=" * 50)
        return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enhanced_alerts()) 