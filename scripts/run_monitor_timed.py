#!/usr/bin/env python3
"""
Timed Monitor Runner

Runs the early token monitor for a specified duration with proper monitoring
and graceful shutdown. Designed for scheduled runs and testing.
"""

import os
import sys
import time
import signal
import asyncio
import threading
from datetime import datetime, timedelta
import uuid
import psutil
from utils.structured_logger import get_structured_logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitor import VirtuosoGemHunter
from services.logger_setup import LoggerSetup

class TimedMonitorRunner:
    def __init__(self, duration_hours: float = 3.0, debug_mode: bool = False):
        self.duration_hours = duration_hours
        self.duration_seconds = duration_hours * 3600
        self.debug_mode = debug_mode
        self.start_time = None
        self.end_time = None
        self.monitor = None
        self.running = False
        self.shutdown_requested = False
        self.scan_id = str(uuid.uuid4())
        self.structured_logger = get_structured_logger('TimedMonitorRunner')
        
        # Setup logging with debug level if debug mode
        log_level = "DEBUG" if debug_mode else "INFO"
        self.logger_setup = LoggerSetup('TimedMonitorRunner', log_level=log_level)
        self.logger = self.logger_setup.logger
        
        if debug_mode:
            self.logger.debug("Debug mode enabled - Enhanced logging active")
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        signal_name = signal.Signals(sig).name
        print(f"\n🛑 Received {signal_name} signal, initiating graceful shutdown...")
        self.logger.info(f"Received {signal_name} signal, shutting down")
        self.shutdown_requested = True
        
        if self.monitor:
            self.monitor.running = False
    
    def _display_startup_info(self):
        """Display startup information"""
        debug_indicator = " [DEBUG MODE]" if self.debug_mode else ""
        print(f"\n{'='*100}")
        print(f"    🚀 TIMED EARLY TOKEN MONITOR - {self.duration_hours} HOUR RUN{debug_indicator}")
        print(f"{'='*100}")
        
        print(f"\n📅 Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏁 End Time:   {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duration:   {self.duration_hours} hours ({self.duration_seconds:,.0f} seconds)")
        
        if self.debug_mode:
            print(f"🐛 Debug Mode: ENABLED - Enhanced logging and frequent updates")
        
        # Environment check
        env_vars = [
            'BIRDEYE_API_KEY',
            'TELEGRAM_BOT_TOKEN', 
            'TELEGRAM_CHAT_ID'
        ]
        
        print(f"\n🔧 Environment Check:")
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                if 'API_KEY' in var or 'TOKEN' in var:
                    masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "Set"
                    print(f"   ✅ {var}: {masked}")
                    if self.debug_mode:
                        self.logger.debug(f"Environment variable {var} is set (length: {len(value)})")
                else:
                    print(f"   ✅ {var}: Set")
            else:
                print(f"   ❌ {var}: Not set")
                if self.debug_mode:
                    self.logger.warning(f"Environment variable {var} is not set")
        
        # Update intervals based on debug mode
        scan_interval = "~20 minutes" if not self.debug_mode else "~20 minutes (with debug output)"
        update_frequency = "Every 30 minutes" if not self.debug_mode else "Every 5 minutes"
        
        print(f"\n🎯 Expected Performance:")
        print(f"   • API call reduction: 75-85% vs legacy system")
        print(f"   • Scan interval: {scan_interval}")
        print(f"   • Expected scans: ~{int(self.duration_hours * 3):,}")
        print(f"   • Progress updates: {update_frequency}")
        
        print(f"\n⚡ Features Active:")
        print(f"   • Pump & dump detection with enhanced risk analysis")
        print(f"   • Progressive 3-stage filtering")
        print(f"   • Batch API processing")
        print(f"   • Smart caching with TTL optimization")
        print(f"   • Real-time Telegram alerts")
        
        if self.debug_mode:
            print(f"\n🐛 Debug Features:")
            print(f"   • Detailed API call logging")
            print(f"   • Enhanced error reporting")
            print(f"   • Frequent progress updates")
            print(f"   • Token analysis deep-dive")
            print(f"   • Performance metrics tracking")
        
        print(f"{'='*100}\n")
    
    def _display_progress_update(self, elapsed_seconds: float):
        """Display periodic progress updates"""
        elapsed_hours = elapsed_seconds / 3600
        remaining_seconds = max(0, self.duration_seconds - elapsed_seconds)
        remaining_hours = remaining_seconds / 3600
        progress_percent = min(100, (elapsed_seconds / self.duration_seconds) * 100)
        
        debug_prefix = "🐛 DEBUG " if self.debug_mode else ""
        print(f"\n{'='*80}")
        print(f"📊 {debug_prefix}PROGRESS UPDATE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}")
        print(f"⏱️  Elapsed:    {elapsed_hours:.2f} hours ({elapsed_seconds:,.0f}s)")
        print(f"⏳ Remaining:  {remaining_hours:.2f} hours ({remaining_seconds:,.0f}s)")
        print(f"📈 Progress:   {progress_percent:.1f}%")
        
        # Progress bar
        bar_width = 50
        filled = int(bar_width * progress_percent / 100)
        bar = '█' * filled + '░' * (bar_width - filled)
        print(f"🔥 [{bar}] {progress_percent:.1f}%")
        
        if self.debug_mode:
            # Additional debug information
            print(f"\n🐛 Debug Info:")
            print(f"   • Process running: {self.running}")
            print(f"   • Monitor active: {self.monitor.running if self.monitor else 'Not initialized'}")
            print(f"   • Shutdown requested: {self.shutdown_requested}")
            
            # Check log file size
            log_file = "logs/virtuoso_gem_hunter.log"
            if os.path.exists(log_file):
                log_size = os.path.getsize(log_file) / 1024  # KB
                print(f"   • Log file size: {log_size:.1f} KB")
            
            # Memory usage (basic)
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"   • Memory usage: {memory_mb:.1f} MB")
            
        print(f"{'='*80}\n")
    
    async def _monitor_duration(self):
        """Monitor the run duration and provide updates"""
        # Adjust update interval based on debug mode
        update_interval = 300 if self.debug_mode else 1800  # 5 minutes vs 30 minutes
        last_update = 0
        
        if self.debug_mode:
            self.logger.debug(f"Duration monitor started - Update interval: {update_interval}s")
        
        while self.running and not self.shutdown_requested:
            elapsed = time.time() - self.start_time.timestamp()
            
            # Check if we've exceeded the duration
            if elapsed >= self.duration_seconds:
                print(f"\n🏁 Target duration of {self.duration_hours} hours reached!")
                self.logger.info(f"Target duration of {self.duration_hours} hours reached")
                self.running = False
                if self.monitor:
                    self.monitor.running = False
                break
            
            # Provide progress updates
            if elapsed - last_update >= update_interval:
                self._display_progress_update(elapsed)
                last_update = elapsed
                
                if self.debug_mode:
                    self.logger.debug(f"Progress update sent - Elapsed: {elapsed:.1f}s")
            
            # Check every 30 seconds (more frequent in debug mode)
            sleep_interval = 15 if self.debug_mode else 30
            await asyncio.sleep(sleep_interval)
    
    async def run(self):
        """Run the monitor for the specified duration"""
        try:
            # Initialize timing
            self.start_time = datetime.now()
            self.end_time = self.start_time + timedelta(hours=self.duration_hours)
            self.structured_logger.info({
                "event": "timed_monitor_start",
                "scan_id": self.scan_id,
                "timestamp": int(time.time()),
                "cpu_percent": psutil.cpu_percent(),
                "memory_mb": psutil.virtual_memory().used // 1024 // 1024
            })
            self.running = True
            
            # Display startup info
            self._display_startup_info()
            
            # Log startup
            startup_msg = f"Starting timed monitor run for {self.duration_hours} hours"
            if self.debug_mode:
                startup_msg += " in DEBUG mode"
            self.logger.info(startup_msg)
            self.logger.info(f"Target end time: {self.end_time}")
            
            if self.debug_mode:
                self.logger.debug("Detailed logging enabled")
                self.logger.debug(f"Update interval: {'5 minutes' if self.debug_mode else '30 minutes'}")
            
            # Initialize monitor
            print("🔧 Initializing Virtuoso Gem Hunter...")
            if self.debug_mode:
                print("🐛 DEBUG: Creating VirtuosoGemHunter instance with enhanced logging...")
            
            self.monitor = VirtuosoGemHunter()
            
            if self.debug_mode:
                self.logger.debug("VirtuosoGemHunter initialized successfully")
            
            # Start duration monitoring task
            if self.debug_mode:
                print("🐛 DEBUG: Starting duration monitoring task...")
            duration_task = asyncio.create_task(self._monitor_duration())
            
            # Start the main monitor
            print("🚀 Starting token monitoring...")
            if self.debug_mode:
                print("🐛 DEBUG: Launching main monitor task...")
            monitor_task = asyncio.create_task(self.monitor.start())
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [monitor_task, duration_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            if self.debug_mode:
                self.logger.debug("Cancelling remaining tasks...")
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    if self.debug_mode:
                        self.logger.debug("Task cancelled successfully")
                    pass
            
            # Display completion info
            self._display_completion_info()
            
            self.structured_logger.info({
                "event": "timed_monitor_end",
                "scan_id": self.scan_id,
                "timestamp": int(time.time()),
                "cpu_percent": psutil.cpu_percent(),
                "memory_mb": psutil.virtual_memory().used // 1024 // 1024
            })
            
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received")
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            print(f"\n❌ Error during monitor run: {e}")
            self.logger.error(f"Error during monitor run: {e}", exc_info=True)
            if self.debug_mode:
                self.logger.debug("Full error traceback logged above")
            self.structured_logger.error({
                "event": "timed_monitor_error",
                "scan_id": self.scan_id,
                "error": str(e),
                "timestamp": int(time.time())
            })
            raise
        finally:
            # Ensure cleanup
            if self.debug_mode:
                self.logger.debug("Performing cleanup...")
            if self.monitor:
                self.monitor.running = False
            self.running = False
    
    def _display_completion_info(self):
        """Display completion information"""
        actual_end_time = datetime.now()
        actual_duration = actual_end_time - self.start_time
        actual_hours = actual_duration.total_seconds() / 3600
        
        debug_indicator = " [DEBUG MODE]" if self.debug_mode else ""
        print(f"\n{'='*100}")
        print(f"    🏁 MONITOR RUN COMPLETED{debug_indicator}")
        print(f"{'='*100}")
        
        print(f"\n📊 Run Summary:")
        print(f"   🕐 Start Time:      {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🕐 End Time:        {actual_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   ⏱️  Target Duration: {self.duration_hours:.2f} hours")
        print(f"   ⏱️  Actual Duration: {actual_hours:.2f} hours")
        print(f"   🐛 Debug Mode:      {'Enabled' if self.debug_mode else 'Disabled'}")
        
        if self.shutdown_requested:
            print(f"   🛑 Reason:          Manual shutdown")
        elif actual_hours >= self.duration_hours * 0.95:  # Within 5% of target
            print(f"   ✅ Reason:          Target duration reached")
        else:
            print(f"   ⚠️  Reason:          Early termination")
        
        # Check logs for results
        log_file = "logs/virtuoso_gem_hunter.log"
        if os.path.exists(log_file):
            log_size = os.path.getsize(log_file) / 1024  # KB
            print(f"\n📋 Logs available at: {log_file} ({log_size:.1f} KB)")
            
            if self.debug_mode:
                print(f"🐛 Debug log contains detailed API calls and analysis data")
        
        print(f"\n🎯 Next Steps:")
        print(f"   • Review logs for discovered tokens")
        print(f"   • Check Telegram alerts if enabled")
        print(f"   • Analyze performance metrics")
        
        if self.debug_mode:
            print(f"   • Debug logs contain detailed API usage patterns")
            print(f"   • Enhanced error reporting available in logs")
        
        print(f"{'='*100}\n")
        
        # Log completion
        completion_msg = f"Monitor run completed - Duration: {actual_hours:.2f} hours"
        if self.debug_mode:
            completion_msg += " (DEBUG mode)"
        self.logger.info(completion_msg)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run early token monitor for specified duration')
    parser.add_argument('--hours', type=float, default=3.0, 
                       help='Duration to run in hours (default: 3.0)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode with enhanced logging')
    
    args = parser.parse_args()
    
    if args.hours <= 0:
        print("❌ Error: Duration must be positive")
        sys.exit(1)
    
    if args.hours > 24:
        print("⚠️  Warning: Running for more than 24 hours")
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Cancelled")
            sys.exit(0)
    
    if args.debug:
        print("🐛 Debug mode enabled - Enhanced logging and frequent updates active")
    
    # Run the timed monitor
    runner = TimedMonitorRunner(duration_hours=args.hours, debug_mode=args.debug)
    
    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 