#!/usr/bin/env python3
"""
Telegram Mic Check Test Script

Tests the Telegram alert system with a simple "Mic Check" message to verify connectivity
and configuration.
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.telegram_alerter import TelegramAlerter, MinimalTokenMetrics
from services.logger_setup import LoggerSetup
from core.config_manager import ConfigManager


class TelegramMicCheckTest:
    """Test class for Telegram alert system"""
    
    def __init__(self):
        self.logger_setup = LoggerSetup('TelegramMicCheck')
        self.logger = self.logger_setup.logger
        self.telegram_alerter = None
        
    def setup_telegram_alerter(self):
        """Initialize Telegram alerter with configuration"""
        try:
            # Load configuration
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # Check if Telegram is configured
            telegram_config = config.get('TELEGRAM', {})
            self.logger.info(f"📋 Telegram config found: {telegram_config}")
            
            if not telegram_config.get('enabled', False):
                self.logger.error("❌ Telegram is not enabled in configuration")
                self.logger.info("💡 Set TELEGRAM.enabled to true in your config file")
                return False
            
            # Get credentials from environment
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            self.logger.info(f"🔑 Bot token found: {'Yes' if bot_token else 'No'}")
            self.logger.info(f"🆔 Chat ID found: {'Yes' if chat_id else 'No'}")
            
            if bot_token:
                self.logger.info(f"🔑 Bot token starts with: {bot_token[:10]}...")
            if chat_id:
                self.logger.info(f"🆔 Chat ID: {chat_id}")
            
            if not bot_token:
                self.logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
                self.logger.info("💡 Set TELEGRAM_BOT_TOKEN in your .env file or environment")
                return False
                
            if not chat_id:
                self.logger.error("❌ TELEGRAM_CHAT_ID not found in environment variables")
                self.logger.info("💡 Set TELEGRAM_CHAT_ID in your .env file or environment")
                return False
            
            # Initialize Telegram alerter
            self.telegram_alerter = TelegramAlerter(
                bot_token=bot_token,
                chat_id=chat_id,
                config=telegram_config,
                logger_setup=self.logger_setup
            )
            
            self.logger.info("✅ Telegram alerter initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up Telegram alerter: {e}")
            import traceback
            self.logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return False
    
    def send_mic_check_alert(self):
        """Send a simple mic check alert"""
        if not self.telegram_alerter:
            self.logger.error("❌ Telegram alerter not initialized")
            return False
        
        try:
            # Create a simple mic check message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            
            mic_check_message = f"""🎤 <b>MIC CHECK ALERT</b> 🎤

📡 <b>System Status:</b> ONLINE
🕐 <b>Timestamp:</b> {timestamp}
🤖 <b>Bot:</b> Virtuoso Gem Hunter
🔊 <b>Message:</b> Testing... Testing... 1, 2, 3...

✅ <b>Alert System Status:</b> OPERATIONAL
📱 <b>Telegram Integration:</b> WORKING
🚀 <b>Ready for Gem Discovery!</b>

<i>This is a test message to verify Telegram alert functionality.</i>"""

            self.logger.info(f"📤 Sending message with length: {len(mic_check_message)} characters")
            
            # Send the message
            success = self.telegram_alerter.send_message(mic_check_message)
            
            if success:
                self.logger.info("✅ Mic check alert sent successfully!")
                return True
            else:
                self.logger.error("❌ Failed to send mic check alert")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error sending mic check alert: {e}")
            import traceback
            self.logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return False
    
    def test_simple_message(self):
        """Send a very simple test message to isolate issues"""
        if not self.telegram_alerter:
            self.logger.error("❌ Telegram alerter not initialized")
            return False
        
        try:
            simple_message = "🎤 Test message from Virtuoso Gem Hunter"
            self.logger.info(f"📤 Sending simple test message: {simple_message}")
            
            success = self.telegram_alerter.send_message(simple_message)
            
            if success:
                self.logger.info("✅ Simple test message sent successfully!")
                return True
            else:
                self.logger.error("❌ Failed to send simple test message")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error sending simple test message: {e}")
            import traceback
            self.logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return False
    
    def send_gem_alert_test(self):
        """Send a test gem alert using the full gem alert system"""
        if not self.telegram_alerter:
            self.logger.error("❌ Telegram alerter not initialized") 
            return False
        
        try:
            # Create mock token metrics for testing
            mock_metrics = MinimalTokenMetrics(
                symbol="MICTEST",
                address="MicTest1234567890ABCDEFabcdef1234567890ABCDEF",
                price=0.000123,
                name="Mic Check Test Token",
                market_cap=50000,
                liquidity=25000,
                volume_24h=15000,
                holders=1337,
                price_change_24h=42.0,
                score=85.5
            )
            
            # Create enhanced data for testing
            enhanced_data = {
                'discovery_strategy': 'MicCheckTestStrategy',
                'discovery_details': {
                    'source': 'Telegram Test Suite',
                    'discovery_time': datetime.now().isoformat(),
                    'test_mode': True
                },
                'enhanced_pump_dump_analysis': {
                    'current_phase': 'TEST_PHASE',
                    'phase_confidence': 0.95,
                    'risk_level': 'LOW',
                    'sustainability_score': 88
                }
            }
            
            # Send gem alert
            self.telegram_alerter.send_gem_alert(
                metrics=mock_metrics,
                score=85.5,
                enhanced_data=enhanced_data,
                scan_id="mic_check_test"
            )
            
            self.logger.info("✅ Test gem alert sent successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error sending test gem alert: {e}")
            import traceback
            self.logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return False
    
    def run_full_test(self):
        """Run complete Telegram alert system test"""
        self.logger.info("🎤 Starting Telegram Mic Check Test...")
        self.logger.info("=" * 50)
        
        # Step 1: Setup Telegram alerter
        self.logger.info("📱 Step 1: Setting up Telegram alerter...")
        if not self.setup_telegram_alerter():
            self.logger.error("❌ Failed to setup Telegram alerter")
            return False
        
        # Step 2: Send simple test message
        self.logger.info("📤 Step 2: Sending simple test message...")
        if not self.test_simple_message():
            self.logger.error("❌ Simple test message failed")
            return False
        
        # Step 3: Send mic check alert
        self.logger.info("🎤 Step 3: Sending mic check alert...")
        if not self.send_mic_check_alert():
            self.logger.error("❌ Mic check alert failed")
            return False
        
        # Step 4: Send test gem alert
        self.logger.info("💎 Step 4: Sending test gem alert...")
        if not self.send_gem_alert_test():
            self.logger.error("❌ Test gem alert failed")
            return False
        
        self.logger.info("=" * 50)
        self.logger.info("✅ All Telegram tests completed successfully!")
        self.logger.info("📱 Check your Telegram chat for the test messages")
        
        return True


def main():
    """Main test function"""
    print("🎤 Virtuoso Gem Hunter - Telegram Mic Check Test")
    print("=" * 60)
    
    # Show environment info
    print(f"🔑 TELEGRAM_BOT_TOKEN present: {'Yes' if os.getenv('TELEGRAM_BOT_TOKEN') else 'No'}")
    print(f"🆔 TELEGRAM_CHAT_ID present: {'Yes' if os.getenv('TELEGRAM_CHAT_ID') else 'No'}")
    print()
    
    # Initialize test class
    test = TelegramMicCheckTest()
    
    # Run full test suite
    success = test.run_full_test()
    
    if success:
        print("\n✅ SUCCESS: Telegram alert system is working!")
        print("📱 Check your Telegram chat for the test messages")
    else:
        print("\n❌ FAILED: Telegram alert system test failed")
        print("🔧 Check your configuration and credentials")
        print("📋 Check the logs for detailed error information")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 