#!/usr/bin/env python3
"""
Position Monitor Daemon

Continuously monitors tracked positions and sends exit alerts when degrading conditions are detected.
Integrates with the existing high conviction token detector infrastructure.
"""

import asyncio
import logging
import time
import sys
import signal
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from services.position_tracker import PositionTracker, Position
from services.exit_signal_detector import ExitSignalDetector, ExitSignal
from services.telegram_bot_handler import TelegramBotHandler
from services.telegram_alerter import TelegramAlerter
from services.logger_setup import LoggerSetup
from api.birdeye_connector import BirdeyeAPI
from api.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from core.config_manager import ConfigManager
from utils.structured_logger import get_structured_logger

class PositionMonitor:
    """Daemon that monitors tracked positions and sends exit alerts"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        # Initialize configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Initialize logging
        self.logger_setup = LoggerSetup('PositionMonitor', self.config)
        self.logger = self.logger_setup.logger
        self.structured_logger = get_structured_logger('PositionMonitor')
        
        # Initialize core services
        self.cache_manager = CacheManager(self.config.get('cache', {}), self.logger)
        self.rate_limiter = RateLimiterService(self.config.get('rate_limiting', {}), self.logger)
        
        # Initialize APIs
        birdeye_config = self.config.get('apis', {}).get('birdeye', {})
        self.birdeye_api = BirdeyeAPI(birdeye_config, self.logger, self.cache_manager, self.rate_limiter)
        
        # Initialize position tracking services
        self.position_tracker = PositionTracker(logger=self.logger)
        self.exit_signal_detector = ExitSignalDetector(
            self.birdeye_api, self.position_tracker, self.config, self.logger
        )
        
        # Initialize Telegram services
        telegram_config = self.config.get('telegram', {})
        bot_token = telegram_config.get('bot_token', '')
        chat_id = telegram_config.get('chat_id', '')
        
        if not bot_token or not chat_id:
            self.logger.error("❌ Telegram configuration missing! Please set bot_token and chat_id in config.")
            raise ValueError("Telegram configuration required for position monitoring")
        
        self.telegram_alerter = TelegramAlerter(bot_token, chat_id, self.config, self.logger_setup)
        self.telegram_bot_handler = TelegramBotHandler(
            self.position_tracker, self.telegram_alerter, self.birdeye_api, self.config, self.logger
        )
        
        # Monitoring configuration
        self.monitoring_config = self.config.get('position_monitoring', {})
        self.check_interval_minutes = self.monitoring_config.get('check_interval_minutes', 15)
        self.max_concurrent_analysis = self.monitoring_config.get('max_concurrent_analysis', 5)
        self.enable_auto_close = self.monitoring_config.get('enable_auto_close', False)
        
        # State management
        self.running = False
        self.last_check_time = 0
        self.total_checks = 0
        self.total_alerts_sent = 0
        self.session_start_time = int(time.time())
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🎯 PositionMonitor initialized successfully")
        self.logger.info(f"📊 Check interval: {self.check_interval_minutes} minutes")
        self.logger.info(f"🔄 Max concurrent analysis: {self.max_concurrent_analysis}")
        self.logger.info(f"🤖 Auto-close enabled: {self.enable_auto_close}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    async def start_monitoring(self):
        """Start the position monitoring daemon"""
        self.running = True
        self.logger.info("🚀 Starting position monitoring daemon...")
        
        # Log startup summary
        await self._log_startup_summary()
        
        try:
            while self.running:
                cycle_start_time = time.time()
                
                try:
                    # Run monitoring cycle
                    await self._monitoring_cycle()
                    
                    # Calculate next check time
                    cycle_duration = time.time() - cycle_start_time
                    sleep_time = max(0, (self.check_interval_minutes * 60) - cycle_duration)
                    
                    if sleep_time > 0:
                        self.logger.debug(f"💤 Sleeping for {sleep_time:.1f} seconds until next check")
                        await asyncio.sleep(sleep_time)
                    else:
                        self.logger.warning(f"⚠️ Monitoring cycle took {cycle_duration:.1f}s, longer than interval!")
                
                except Exception as e:
                    self.logger.error(f"❌ Error in monitoring cycle: {e}")
                    # Sleep for a shorter time on error to retry sooner
                    await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            self.logger.info("⌨️ Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"💥 Fatal error in monitoring daemon: {e}")
        finally:
            await self._cleanup()
    
    async def _monitoring_cycle(self):
        """Execute one monitoring cycle"""
        cycle_start = time.time()
        self.total_checks += 1
        
        self.logger.info(f"🔍 Starting monitoring cycle #{self.total_checks}")
        
        # Get all active positions
        active_positions = self.position_tracker.get_all_active_positions()
        
        if not active_positions:
            self.logger.debug("📭 No active positions to monitor")
            return
        
        self.logger.info(f"📊 Monitoring {len(active_positions)} active positions")
        
        # Analyze positions in batches to avoid overwhelming APIs
        batch_size = self.max_concurrent_analysis
        alerts_sent_this_cycle = 0
        
        for i in range(0, len(active_positions), batch_size):
            batch = active_positions[i:i + batch_size]
            
            self.logger.debug(f"🔬 Analyzing batch {i//batch_size + 1}: {len(batch)} positions")
            
            # Analyze batch concurrently
            tasks = [self._analyze_position(position) for position in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for j, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"❌ Error analyzing position {batch[j].id}: {result}")
                elif result:
                    alerts_sent_this_cycle += 1
                    self.total_alerts_sent += 1
            
            # Small delay between batches to be API-friendly
            if i + batch_size < len(active_positions):
                await asyncio.sleep(2)
        
        # Log cycle summary
        cycle_duration = time.time() - cycle_start
        self.last_check_time = int(time.time())
        
        self.logger.info(f"✅ Monitoring cycle #{self.total_checks} completed in {cycle_duration:.1f}s")
        self.logger.info(f"📨 Alerts sent this cycle: {alerts_sent_this_cycle}")
        
        # Log structured data for monitoring
        self.structured_logger.info({
            "event": "monitoring_cycle_completed",
            "cycle_number": self.total_checks,
            "positions_analyzed": len(active_positions),
            "alerts_sent": alerts_sent_this_cycle,
            "duration_seconds": cycle_duration,
            "timestamp": int(time.time())
        })
    
    async def _analyze_position(self, position: Position) -> bool:
        """Analyze a single position and send alerts if needed"""
        try:
            self.logger.debug(f"🔍 Analyzing position {position.id} - {position.token_symbol}")
            
            # Generate exit signal
            exit_signal = await self.exit_signal_detector.analyze_position(position)
            
            # Check if we should send an alert
            should_alert = self._should_send_alert(position, exit_signal)
            
            if should_alert:
                # Send exit alert
                success = await self.telegram_bot_handler.send_exit_alert(position, exit_signal)
                
                if success:
                    self.logger.info(f"🚨 Sent exit alert for {position.token_symbol} (score: {exit_signal.signal_strength:.1f})")
                    
                    # Auto-close position if enabled and signal is critical
                    if (self.enable_auto_close and 
                        exit_signal.signal_strength >= 90 and 
                        exit_signal.recommendation == "EXIT"):
                        
                        # Check user preferences
                        user_prefs = self.position_tracker.get_user_preferences(position.user_id)
                        if user_prefs and user_prefs.auto_close_on_exit_signal:
                            self.position_tracker.close_position(position.id, "auto_exit_signal")
                            self.logger.info(f"🤖 Auto-closed position {position.id} - {position.token_symbol}")
                    
                    return True
                else:
                    self.logger.error(f"❌ Failed to send exit alert for {position.token_symbol}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing position {position.id}: {e}")
            return False
    
    def _should_send_alert(self, position: Position, exit_signal: ExitSignal) -> bool:
        """Determine if an alert should be sent based on signal and previous alerts"""
        
        # Don't alert on error or no-data signals
        if exit_signal.signal_type in ["error", "no_data"]:
            return False
        
        # Check minimum signal strength thresholds
        min_alert_threshold = 60.0  # Only alert on moderate+ signals
        if exit_signal.signal_strength < min_alert_threshold:
            return False
        
        # Check if we've already sent a similar alert recently
        recent_alerts = self.position_tracker.get_position_alerts(position.id, unacknowledged_only=True)
        
        # Don't spam alerts - wait at least 1 hour between exit signals
        for alert in recent_alerts:
            if (alert.alert_type.endswith("_exit") and 
                alert.sent_at > int(time.time()) - 3600):  # 1 hour cooldown
                self.logger.debug(f"🔇 Skipping alert for {position.token_symbol} - recent alert sent")
                return False
        
        # Check user preferences for alert frequency
        user_prefs = self.position_tracker.get_user_preferences(position.user_id)
        if user_prefs:
            min_interval = user_prefs.alert_frequency_minutes * 60
            for alert in recent_alerts:
                if alert.sent_at > int(time.time()) - min_interval:
                    return False
        
        return True
    
    async def _log_startup_summary(self):
        """Log startup summary with current system state"""
        try:
            # Get position statistics
            stats = self.position_tracker.get_statistics()
            
            # Get API status
            birdeye_status = "✅ Connected" if self.birdeye_api.api_key else "❌ No API Key"
            
            self.logger.info("📋 Position Monitor Startup Summary:")
            self.logger.info(f"  📊 Active Positions: {stats['active_positions']}")
            self.logger.info(f"  👥 Total Users: {stats['total_users']}")
            self.logger.info(f"  🚨 Recent Alerts (24h): {stats['recent_alerts_24h']}")
            self.logger.info(f"  🔗 Birdeye API: {birdeye_status}")
            self.logger.info(f"  📱 Telegram: ✅ Configured")
            self.logger.info(f"  ⏱️ Check Interval: {self.check_interval_minutes} minutes")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error generating startup summary: {e}")
    
    async def _cleanup(self):
        """Cleanup resources before shutdown"""
        self.logger.info("🧹 Cleaning up resources...")
        
        try:
            # Close API connections
            if hasattr(self.birdeye_api, 'close'):
                await self.birdeye_api.close()
            
            # Log shutdown summary
            uptime_hours = (time.time() - self.session_start_time) / 3600
            
            self.logger.info("📊 Session Summary:")
            self.logger.info(f"  ⏱️ Uptime: {uptime_hours:.1f} hours")
            self.logger.info(f"  🔍 Total Checks: {self.total_checks}")
            self.logger.info(f"  🚨 Total Alerts: {self.total_alerts_sent}")
            
            if self.total_checks > 0:
                avg_alerts_per_check = self.total_alerts_sent / self.total_checks
                self.logger.info(f"  📈 Avg Alerts/Check: {avg_alerts_per_check:.2f}")
            
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")
        
        self.logger.info("👋 Position Monitor shutdown complete")

async def main():
    """Main entry point for the position monitor daemon"""
    try:
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='Position Monitor Daemon')
        parser.add_argument('--config', '-c', default='config/config.yaml',
                          help='Path to configuration file')
        parser.add_argument('--check-interval', '-i', type=int,
                          help='Check interval in minutes (overrides config)')
        parser.add_argument('--debug', '-d', action='store_true',
                          help='Enable debug logging')
        parser.add_argument('--test-run', '-t', action='store_true',
                          help='Run one monitoring cycle and exit')
        
        args = parser.parse_args()
        
        # Initialize monitor
        monitor = PositionMonitor(args.config)
        
        # Override check interval if specified
        if args.check_interval:
            monitor.check_interval_minutes = args.check_interval
            monitor.logger.info(f"⚙️ Override check interval: {args.check_interval} minutes")
        
        # Set debug logging if requested
        if args.debug:
            monitor.logger.setLevel(logging.DEBUG)
            monitor.logger.info("🐛 Debug logging enabled")
        
        # Run test cycle or start daemon
        if args.test_run:
            monitor.logger.info("🧪 Running test cycle...")
            await monitor._monitoring_cycle()
            monitor.logger.info("✅ Test cycle completed")
        else:
            await monitor.start_monitoring()
    
    except KeyboardInterrupt:
        print("\n⌨️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 


    #!/usr/bin/env python3
"""
Position Monitor Daemon

Continuously monitors tracked positions and sends exit alerts when degrading conditions are detected.
Integrates with the existing high conviction token detector infrastructure.
"""

import asyncio
import logging
import time
import sys
import signal
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from services.position_tracker import PositionTracker, Position
from services.exit_signal_detector import ExitSignalDetector, ExitSignal
from services.telegram_bot_handler import TelegramBotHandler
from services.telegram_alerter import TelegramAlerter
from services.logger_setup import LoggerSetup
from api.birdeye_connector import BirdeyeAPI
from api.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from core.config_manager import ConfigManager
from utils.structured_logger import get_structured_logger

class PositionMonitor:
    """Daemon that monitors tracked positions and sends exit alerts"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        # Initialize configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Initialize logging
        self.logger_setup = LoggerSetup('PositionMonitor', self.config)
        self.logger = self.logger_setup.logger
        self.structured_logger = get_structured_logger('PositionMonitor')
        
        # Initialize core services
        self.cache_manager = CacheManager(self.config.get('cache', {}), self.logger)
        self.rate_limiter = RateLimiterService(self.config.get('rate_limiting', {}), self.logger)
        
        # Initialize APIs
        birdeye_config = self.config.get('apis', {}).get('birdeye', {})
        self.birdeye_api = BirdeyeAPI(birdeye_config, self.logger, self.cache_manager, self.rate_limiter)
        
        # Initialize position tracking services
        self.position_tracker = PositionTracker(logger=self.logger)
        self.exit_signal_detector = ExitSignalDetector(
            self.birdeye_api, self.position_tracker, self.config, self.logger
        )
        
        # Initialize Telegram services
        telegram_config = self.config.get('telegram', {})
        bot_token = telegram_config.get('bot_token', '')
        chat_id = telegram_config.get('chat_id', '')
        
        if not bot_token or not chat_id:
            self.logger.error("❌ Telegram configuration missing! Please set bot_token and chat_id in config.")
            raise ValueError("Telegram configuration required for position monitoring")
        
        self.telegram_alerter = TelegramAlerter(bot_token, chat_id, self.config, self.logger_setup)
        self.telegram_bot_handler = TelegramBotHandler(
            self.position_tracker, self.telegram_alerter, self.birdeye_api, self.config, self.logger
        )
        
        # Monitoring configuration
        self.monitoring_config = self.config.get('position_monitoring', {})
        self.check_interval_minutes = self.monitoring_config.get('check_interval_minutes', 15)
        self.max_concurrent_analysis = self.monitoring_config.get('max_concurrent_analysis', 5)
        self.enable_auto_close = self.monitoring_config.get('enable_auto_close', False)
        
        # State management
        self.running = False
        self.last_check_time = 0
        self.total_checks = 0
        self.total_alerts_sent = 0
        self.session_start_time = int(time.time())
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("🎯 PositionMonitor initialized successfully")
        self.logger.info(f"📊 Check interval: {self.check_interval_minutes} minutes")
        self.logger.info(f"🔄 Max concurrent analysis: {self.max_concurrent_analysis}")
        self.logger.info(f"🤖 Auto-close enabled: {self.enable_auto_close}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    async def start_monitoring(self):
        """Start the position monitoring daemon"""
        self.running = True
        self.logger.info("🚀 Starting position monitoring daemon...")
        
        # Log startup summary
        await self._log_startup_summary()
        
        try:
            while self.running:
                cycle_start_time = time.time()
                
                try:
                    # Run monitoring cycle
                    await self._monitoring_cycle()
                    
                    # Calculate next check time
                    cycle_duration = time.time() - cycle_start_time
                    sleep_time = max(0, (self.check_interval_minutes * 60) - cycle_duration)
                    
                    if sleep_time > 0:
                        self.logger.debug(f"💤 Sleeping for {sleep_time:.1f} seconds until next check")
                        await asyncio.sleep(sleep_time)
                    else:
                        self.logger.warning(f"⚠️ Monitoring cycle took {cycle_duration:.1f}s, longer than interval!")
                
                except Exception as e:
                    self.logger.error(f"❌ Error in monitoring cycle: {e}")
                    # Sleep for a shorter time on error to retry sooner
                    await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            self.logger.info("⌨️ Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"💥 Fatal error in monitoring daemon: {e}")
        finally:
            await self._cleanup()
    
    async def _monitoring_cycle(self):
        """Execute one monitoring cycle"""
        cycle_start = time.time()
        self.total_checks += 1
        
        self.logger.info(f"🔍 Starting monitoring cycle #{self.total_checks}")
        
        # Get all active positions
        active_positions = self.position_tracker.get_all_active_positions()
        
        if not active_positions:
            self.logger.debug("📭 No active positions to monitor")
            return
        
        self.logger.info(f"📊 Monitoring {len(active_positions)} active positions")
        
        # Analyze positions in batches to avoid overwhelming APIs
        batch_size = self.max_concurrent_analysis
        alerts_sent_this_cycle = 0
        
        for i in range(0, len(active_positions), batch_size):
            batch = active_positions[i:i + batch_size]
            
            self.logger.debug(f"🔬 Analyzing batch {i//batch_size + 1}: {len(batch)} positions")
            
            # Analyze batch concurrently
            tasks = [self._analyze_position(position) for position in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for j, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"❌ Error analyzing position {batch[j].id}: {result}")
                elif result:
                    alerts_sent_this_cycle += 1
                    self.total_alerts_sent += 1
            
            # Small delay between batches to be API-friendly
            if i + batch_size < len(active_positions):
                await asyncio.sleep(2)
        
        # Log cycle summary
        cycle_duration = time.time() - cycle_start
        self.last_check_time = int(time.time())
        
        self.logger.info(f"✅ Monitoring cycle #{self.total_checks} completed in {cycle_duration:.1f}s")
        self.logger.info(f"📨 Alerts sent this cycle: {alerts_sent_this_cycle}")
        
        # Log structured data for monitoring
        self.structured_logger.info({
            "event": "monitoring_cycle_completed",
            "cycle_number": self.total_checks,
            "positions_analyzed": len(active_positions),
            "alerts_sent": alerts_sent_this_cycle,
            "duration_seconds": cycle_duration,
            "timestamp": int(time.time())
        })
    
    async def _analyze_position(self, position: Position) -> bool:
        """Analyze a single position and send alerts if needed"""
        try:
            self.logger.debug(f"🔍 Analyzing position {position.id} - {position.token_symbol}")
            
            # Generate exit signal
            exit_signal = await self.exit_signal_detector.analyze_position(position)
            
            # Check if we should send an alert
            should_alert = self._should_send_alert(position, exit_signal)
            
            if should_alert:
                # Send exit alert
                success = await self.telegram_bot_handler.send_exit_alert(position, exit_signal)
                
                if success:
                    self.logger.info(f"🚨 Sent exit alert for {position.token_symbol} (score: {exit_signal.signal_strength:.1f})")
                    
                    # Auto-close position if enabled and signal is critical
                    if (self.enable_auto_close and 
                        exit_signal.signal_strength >= 90 and 
                        exit_signal.recommendation == "EXIT"):
                        
                        # Check user preferences
                        user_prefs = self.position_tracker.get_user_preferences(position.user_id)
                        if user_prefs and user_prefs.auto_close_on_exit_signal:
                            self.position_tracker.close_position(position.id, "auto_exit_signal")
                            self.logger.info(f"🤖 Auto-closed position {position.id} - {position.token_symbol}")
                    
                    return True
                else:
                    self.logger.error(f"❌ Failed to send exit alert for {position.token_symbol}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing position {position.id}: {e}")
            return False
    
    def _should_send_alert(self, position: Position, exit_signal: ExitSignal) -> bool:
        """Determine if an alert should be sent based on signal and previous alerts"""
        
        # Don't alert on error or no-data signals
        if exit_signal.signal_type in ["error", "no_data"]:
            return False
        
        # Check minimum signal strength thresholds
        min_alert_threshold = 60.0  # Only alert on moderate+ signals
        if exit_signal.signal_strength < min_alert_threshold:
            return False
        
        # Check if we've already sent a similar alert recently
        recent_alerts = self.position_tracker.get_position_alerts(position.id, unacknowledged_only=True)
        
        # Don't spam alerts - wait at least 1 hour between exit signals
        for alert in recent_alerts:
            if (alert.alert_type.endswith("_exit") and 
                alert.sent_at > int(time.time()) - 3600):  # 1 hour cooldown
                self.logger.debug(f"🔇 Skipping alert for {position.token_symbol} - recent alert sent")
                return False
        
        # Check user preferences for alert frequency
        user_prefs = self.position_tracker.get_user_preferences(position.user_id)
        if user_prefs:
            min_interval = user_prefs.alert_frequency_minutes * 60
            for alert in recent_alerts:
                if alert.sent_at > int(time.time()) - min_interval:
                    return False
        
        return True
    
    async def _log_startup_summary(self):
        """Log startup summary with current system state"""
        try:
            # Get position statistics
            stats = self.position_tracker.get_statistics()
            
            # Get API status
            birdeye_status = "✅ Connected" if self.birdeye_api.api_key else "❌ No API Key"
            
            self.logger.info("📋 Position Monitor Startup Summary:")
            self.logger.info(f"  📊 Active Positions: {stats['active_positions']}")
            self.logger.info(f"  👥 Total Users: {stats['total_users']}")
            self.logger.info(f"  🚨 Recent Alerts (24h): {stats['recent_alerts_24h']}")
            self.logger.info(f"  🔗 Birdeye API: {birdeye_status}")
            self.logger.info(f"  📱 Telegram: ✅ Configured")
            self.logger.info(f"  ⏱️ Check Interval: {self.check_interval_minutes} minutes")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error generating startup summary: {e}")
    
    async def _cleanup(self):
        """Cleanup resources before shutdown"""
        self.logger.info("🧹 Cleaning up resources...")
        
        try:
            # Close API connections
            if hasattr(self.birdeye_api, 'close'):
                await self.birdeye_api.close()
            
            # Log shutdown summary
            uptime_hours = (time.time() - self.session_start_time) / 3600
            
            self.logger.info("📊 Session Summary:")
            self.logger.info(f"  ⏱️ Uptime: {uptime_hours:.1f} hours")
            self.logger.info(f"  🔍 Total Checks: {self.total_checks}")
            self.logger.info(f"  🚨 Total Alerts: {self.total_alerts_sent}")
            
            if self.total_checks > 0:
                avg_alerts_per_check = self.total_alerts_sent / self.total_checks
                self.logger.info(f"  📈 Avg Alerts/Check: {avg_alerts_per_check:.2f}")
            
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")
        
        self.logger.info("👋 Position Monitor shutdown complete")

async def main():
    """Main entry point for the position monitor daemon"""
    try:
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='Position Monitor Daemon')
        parser.add_argument('--config', '-c', default='config/config.yaml',
                          help='Path to configuration file')
        parser.add_argument('--check-interval', '-i', type=int,
                          help='Check interval in minutes (overrides config)')
        parser.add_argument('--debug', '-d', action='store_true',
                          help='Enable debug logging')
        parser.add_argument('--test-run', '-t', action='store_true',
                          help='Run one monitoring cycle and exit')
        
        args = parser.parse_args()
        
        # Initialize monitor
        monitor = PositionMonitor(args.config)
        
        # Override check interval if specified
        if args.check_interval:
            monitor.check_interval_minutes = args.check_interval
            monitor.logger.info(f"⚙️ Override check interval: {args.check_interval} minutes")
        
        # Set debug logging if requested
        if args.debug:
            monitor.logger.setLevel(logging.DEBUG)
            monitor.logger.info("🐛 Debug logging enabled")
        
        # Run test cycle or start daemon
        if args.test_run:
            monitor.logger.info("🧪 Running test cycle...")
            await monitor._monitoring_cycle()
            monitor.logger.info("✅ Test cycle completed")
        else:
            await monitor.start_monitoring()
    
    except KeyboardInterrupt:
        print("\n⌨️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())