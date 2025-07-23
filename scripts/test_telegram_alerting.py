#!/usr/bin/env python3
"""
Test Telegram Alerting for Early Gem Detector

This script tests if Telegram alerting is properly configured and working.
"""

import sys
import os
import yaml
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.telegram_alerter import TelegramAlerter, MinimalTokenMetrics
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config():
    """Load configuration"""
    try:
        with open("config/config.yaml", 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return {}

def test_telegram_config():
    """Test Telegram configuration"""
    print("🔧 TELEGRAM ALERTING TEST")
    print("=" * 50)
    
    # Load config
    config = load_config()
    telegram_config = config.get('TELEGRAM', {})
    
    print(f"📋 Configuration Check:")
    print(f"   Enabled: {telegram_config.get('enabled', False)}")
    print(f"   Alert Format: {telegram_config.get('alert_format', 'basic')}")
    print(f"   Max Alerts/Hour: {telegram_config.get('max_alerts_per_hour', 10)}")
    
    # Check environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print(f"🔑 Environment Variables:")
    print(f"   TELEGRAM_BOT_TOKEN: {'✅ SET' if bot_token else '❌ MISSING'}")
    print(f"   TELEGRAM_CHAT_ID: {'✅ SET' if chat_id else '❌ MISSING'}")
    
    if not telegram_config.get('enabled', False):
        print("❌ Telegram alerts are DISABLED in configuration")
        return False
        
    if not bot_token or not chat_id:
        print("❌ Telegram credentials are MISSING")
        return False
        
    return True, telegram_config, bot_token, chat_id

def test_telegram_alerter():
    """Test the Telegram alerter"""
    
    # Check configuration
    config_result = test_telegram_config()
    if config_result is False:
        return False
        
    enabled, telegram_config, bot_token, chat_id = config_result
    
    print(f"\n🚀 Testing Telegram Alerter...")
    
    try:
        # Create a simple logger wrapper
        import logging
        
        class LoggerSetup:
            def __init__(self):
                self.logger = logging.getLogger('TelegramTest')
                self.logger.setLevel(logging.INFO)
                if not self.logger.handlers:
                    handler = logging.StreamHandler()
                    formatter = logging.Formatter('%(levelname)s - %(message)s')
                    handler.setFormatter(formatter)
                    self.logger.addHandler(handler)
        
        # Initialize Telegram alerter
        alerter = TelegramAlerter(
            bot_token=bot_token,
            chat_id=chat_id,
            config=telegram_config,
            logger_setup=LoggerSetup()
        )
        
        print("✅ Telegram alerter initialized successfully")
        
        # Test with a mock early gem alert
        print("\n📱 Sending test early gem alert...")
        
        # Create test token metrics
        test_metrics = MinimalTokenMetrics(
            symbol="TEST",
            address="TestAddress123456789",
            name="Test Early Gem Token",
            price=0.000123,
            market_cap=50000,
            liquidity=25000,
            volume_24h=15000,
            holders=150,
            price_change_24h=25.5,
            score=42.8
        )
        
        # Create test message similar to early gem detector
        test_message = f"""
🚨 🔥 EARLY GEM ALERT 🔥 ENRICHED

💎 **{test_metrics.symbol}**
📊 Score: **{test_metrics.score:.1f}**/100
💰 Market Cap: **${test_metrics.market_cap:,.0f}**
🔍 Source: telegram_test

🏠 `{test_metrics.address}`

#{test_metrics.symbol}EarlyGem #PumpFun #TelegramTest
        """.strip()
        
        # Send the alert using the correct method
        success = alerter.send_message(test_message)
        
        if success:
            print("✅ Test alert sent successfully!")
            print("📱 Check your Telegram chat for the test message")
            return True
        else:
            print("❌ Failed to send test alert")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Telegram alerter: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print(f"🎯 Early Gem Detector - Telegram Alert Test")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_telegram_alerter()
    
    print(f"\n📊 TEST RESULTS:")
    if success:
        print("✅ Telegram alerting is WORKING!")
        print("🚀 Early gem detector should be able to send alerts")
    else:
        print("❌ Telegram alerting has ISSUES")
        print("🔧 Please check configuration and credentials")
    
    print(f"\n💡 To enable alerting in early gem detector:")
    print(f"   python scripts/early_gem_detector.py --single")

if __name__ == "__main__":
    main() 