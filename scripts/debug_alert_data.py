#!/usr/bin/env python3
"""
🔍 Debug Alert Data Structure
Examines the actual token data structure being passed to alerts
"""

import os
import sys
import json
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.early_gem_detector import EarlyGemDetector

def debug_token_data_structure():
    """Debug the token data structure to understand missing scoring breakdown"""
    print("🔍 DEBUGGING ALERT DATA STRUCTURE")
    print("=" * 60)
    
    try:
        # Initialize detector
        detector = EarlyGemDetector(debug_mode=True)
        
        # Mock token data similar to what we see in the actual alerts
        sample_token = {
            'symbol': 'pulled',
            'name': 'me and the girl i',
            'address': '5DTK4GXFfhQLDVXdfN8skHyYiiwyg9oYaaLQz6HYpump',
            'score': 176.2,
            'market_cap': 56000,
            'liquidity': 25000,
            'source': 'moralis_graduated',
            'is_fresh_graduate': False,
            'graduation_imminent': False,
            'ultra_early_bonus_eligible': False,
            'enriched': True
        }
        
        print("📊 Sample Token Data Structure:")
        print(json.dumps(sample_token, indent=2))
        print()
        
        # Check what scoring_breakdown and enhanced_metrics would look like
        print("🔍 Expected Data Structure for Enhanced Alerts:")
        print("=" * 50)
        
        expected_structure = {
            'scoring_breakdown': {
                'early_platform_analysis': {
                    'score': 48.5,
                    'early_signals': ['FRESH_GRADUATE', 'STRONG_VELOCITY'],
                    'pump_fun_stage': 'GRADUATED',
                    'graduation_progress': 100
                },
                'momentum_analysis': {
                    'score': 36.2,
                    'volume_surge': 'strong',
                    'price_velocity': 'bullish',
                    'trading_activity': 85
                },
                'safety_validation': {
                    'score': 22.1,
                    'security_score': 88,
                    'risk_factors': ['low_liquidity']
                },
                'cross_platform_bonus': {
                    'score': 8.0,
                    'platforms': ['moralis', 'dexscreener'],
                    'platform_count': 2
                }
            },
            'enhanced_metrics': {
                'velocity_score': 0.85,
                'first_100_score': 7.5,
                'liquidity_quality': 6.8,
                'graduation_risk': -2.0
            },
            'velocity_confidence': {
                'level': 'HIGH',
                'confidence_score': 0.88,
                'coverage_percentage': 83.3,
                'threshold_adjustment': 1.02
            }
        }
        
        print(json.dumps(expected_structure, indent=2))
        print()
        
        # Test the alert generation with both structures
        print("🧪 Testing Alert Generation:")
        print("=" * 30)
        
        print("1. Current Data Structure (missing enhanced data):")
        if detector.telegram_alerter:
            print("   - Would send actual alert")
        else:
            print("   - Telegram not configured, showing format:")
            detector.telegram_alerter = MockAlerter()
            detector._send_early_gem_alert(sample_token)
            detector.telegram_alerter = None
        
        print("\n" + "-" * 50 + "\n")
        
        print("2. Enhanced Data Structure (with scoring breakdown):")
        enhanced_token = {**sample_token, **expected_structure}
        
        if detector.telegram_alerter:
            print("   - Would send actual alert")
        else:
            print("   - Telegram not configured, showing format:")
            detector.telegram_alerter = MockAlerter()
            detector._send_early_gem_alert(enhanced_token)
            detector.telegram_alerter = None
        
        print("\n✅ Debug analysis completed!")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

class MockAlerter:
    """Mock alerter to show the alert format"""
    
    def send_message(self, message: str) -> bool:
        print("📱 ALERT FORMAT:")
        print("=" * 40)
        print(message)
        print("=" * 40)
        return True

if __name__ == "__main__":
    debug_token_data_structure() 