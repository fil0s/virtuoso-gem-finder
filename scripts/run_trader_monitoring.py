#!/usr/bin/env python3
"""
Trader Performance Monitoring with Alerts

Continuously monitors top trader performance and generates alerts for:
- New elite trader discoveries
- Performance improvements/degradations  
- Tier changes
- Risk profile changes
- Cross-timeframe consistency

Can run as one-time analysis or continuous monitoring daemon.
"""

import asyncio
import sys
import os
import argparse
import time
from datetime import datetime
from typing import List, Dict, Any
import uuid
import psutil
from utils.structured_logger import get_structured_logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.trader_performance_analyzer import (
    TraderPerformanceAnalyzer,
    PerformanceTimeframe
)
from services.trader_alert_system import (
    TraderAlertSystem,
    TraderAlert,
    TraderAlertLevel
)
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager
from services.logger_setup import LoggerSetup

class TraderMonitoringDaemon:
    """Trader performance monitoring with alert system"""
    
    def __init__(self):
        self.logger_setup = LoggerSetup('TraderMonitoring')
        self.logger = self.logger_setup.logger
        
        self.analyzer = None
        self.alert_system = None
        self.running = False
        self.scan_id = str(uuid.uuid4())
        self.structured_logger = get_structured_logger('TraderMonitoringDaemon')
        
    async def initialize(self):
        """Initialize monitoring system"""
        try:
            self.logger.info("🔧 Initializing Trader Monitoring System...")
            
            # Load configuration
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # Initialize Birdeye API
            birdeye_config = config.get('BIRDEYE_API', {})
            birdeye_api = BirdeyeAPI(config=birdeye_config)
            
            # Initialize trader analyzer
            self.analyzer = TraderPerformanceAnalyzer(birdeye_api, self.logger)
            
            # Initialize alert system
            self.alert_system = TraderAlertSystem(self.analyzer, self.logger)
            
            self.logger.info("✅ Trader Monitoring System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing monitoring system: {e}")
            return False
    
    async def run_single_monitoring_cycle(self, timeframes: List[str] = None) -> List[TraderAlert]:
        """Run a single monitoring cycle"""
        self.structured_logger.info({
            "event": "trader_monitor_cycle_start",
            "scan_id": self.scan_id,
            "timestamp": int(time.time()),
            "cpu_percent": psutil.cpu_percent(),
            "memory_mb": psutil.virtual_memory().used // 1024 // 1024
        })
        if timeframes is None:
            timeframes = ["24h", "7d"]
        
        # Convert string timeframes to enum
        tf_enums = []
        for tf in timeframes:
            if tf == "24h":
                tf_enums.append(PerformanceTimeframe.HOUR_24)
            elif tf == "7d":
                tf_enums.append(PerformanceTimeframe.DAYS_7)
            elif tf == "30d":
                tf_enums.append(PerformanceTimeframe.DAYS_30)
        
        self.logger.info(f"🚀 Starting monitoring cycle for timeframes: {timeframes}")
        
        # Run monitoring
        alerts = await self.alert_system.monitor_trader_performance(tf_enums)
        
        self.logger.info(f"✅ Monitoring cycle completed. Generated {len(alerts)} alerts")
        
        self.structured_logger.info({
            "event": "trader_monitor_cycle_end",
            "scan_id": self.scan_id,
            "timestamp": int(time.time()),
            "cpu_percent": psutil.cpu_percent(),
            "memory_mb": psutil.virtual_memory().used // 1024 // 1024
        })
        return alerts
    
    async def run_continuous_monitoring(self, check_interval_minutes: int = 30,
                                      timeframes: List[str] = None):
        """Run continuous monitoring daemon"""
        self.structured_logger.info({
            "event": "trader_monitoring_start",
            "scan_id": self.scan_id,
            "timestamp": int(time.time()),
            "cpu_percent": psutil.cpu_percent(),
            "memory_mb": psutil.virtual_memory().used // 1024 // 1024
        })
        self.running = True
        
        self.logger.info("🔄 Starting continuous trader monitoring...")
        self.logger.info(f"   ⏰ Check interval: {check_interval_minutes} minutes")
        self.logger.info(f"   📊 Timeframes: {timeframes or ['24h', '7d']}")
        
        last_cycle_time = 0
        cycle_count = 0
        
        try:
            while self.running:
                current_time = time.time()
                
                try:
                    cycle_count += 1
                    start_time = time.time()
                    
                    self.logger.info(f"\n🔄 MONITORING CYCLE #{cycle_count}")
                    self.logger.info(f"   🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Run monitoring cycle
                    alerts = await self.run_single_monitoring_cycle(timeframes)
                    
                    # Display cycle results
                    elapsed = time.time() - start_time
                    self._display_cycle_results(alerts, elapsed, cycle_count)
                    
                    last_cycle_time = current_time
                    
                except KeyboardInterrupt:
                    self.logger.info("\n🛑 Monitoring interrupted by user")
                    break
                except Exception as e:
                    self.logger.error(f"❌ Error in monitoring cycle: {e}")
                
                # Wait for next cycle
                sleep_time = check_interval_minutes * 60
                self.logger.info(f"⏱️  Waiting {check_interval_minutes} minutes until next cycle...")
                
                for i in range(sleep_time):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Continuous monitoring stopped")
        finally:
            self.running = False
            self.structured_logger.info({
                "event": "trader_monitoring_end",
                "scan_id": self.scan_id,
                "timestamp": int(time.time()),
                "cpu_percent": psutil.cpu_percent(),
                "memory_mb": psutil.virtual_memory().used // 1024 // 1024
            })
    
    def _display_cycle_results(self, alerts: List[TraderAlert], elapsed_time: float, cycle_count: int):
        """Display results of monitoring cycle"""
        print(f"\n📊 CYCLE #{cycle_count} RESULTS")
        print(f"⏱️  Duration: {elapsed_time:.2f} seconds")
        print(f"🚨 Alerts Generated: {len(alerts)}")
        
        if alerts:
            # Group alerts by level
            alert_levels = {}
            for alert in alerts:
                level = alert.alert_level.value
                if level not in alert_levels:
                    alert_levels[level] = []
                alert_levels[level].append(alert)
            
            print(f"\n🚨 ALERT BREAKDOWN:")
            for level in ['critical', 'high', 'medium', 'low']:
                count = len(alert_levels.get(level, []))
                if count > 0:
                    print(f"   {level.upper()}: {count} alerts")
            
            # Show recent critical and high alerts
            critical_high = [a for a in alerts if a.alert_level in [TraderAlertLevel.CRITICAL, TraderAlertLevel.HIGH]]
            if critical_high:
                print(f"\n🚨 PRIORITY ALERTS:")
                for alert in critical_high[:5]:  # Show top 5
                    print(f"   [{alert.alert_level.value.upper()}] {alert.title}")
                    print(f"   👤 {alert.trader_name} | Score: {alert.discovery_score:.0f} | {alert.current_tier.title()}")
                    print(f"   📝 {alert.recommended_action}")
                    print()
        
        # Show system stats
        if self.alert_system:
            stats = self.alert_system.get_alert_stats()
            print(f"📈 SYSTEM STATS:")
            print(f"   📊 Tracked Traders: {stats['tracked_traders']}")
            print(f"   🚨 Active Alerts (24h): {stats['alerts_24h']}")
            print(f"   💾 Total Active Alerts: {stats['total_active_alerts']}")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.running = False
        self.logger.info("🛑 Stopping trader monitoring...")
    
    async def show_active_alerts(self, alert_level: str = None):
        """Display currently active alerts"""
        if not self.alert_system:
            print("❌ Alert system not initialized")
            return
        
        alerts = self.alert_system.get_active_alerts(alert_level)
        
        if not alerts:
            level_text = f" ({alert_level.upper()})" if alert_level else ""
            print(f"✅ No active trader alerts{level_text}")
            return
        
        print(f"\n🚨 ACTIVE TRADER ALERTS ({len(alerts)})")
        print("=" * 60)
        
        for alert in alerts[-10:]:  # Show last 10
            time_ago = (time.time() - alert.created_at) / 3600
            print(f"[{alert.alert_level.value.upper()}] {alert.title}")
            print(f"   👤 {alert.trader_name} ({alert.trader_address[:8]}...)")
            print(f"   🎯 Score: {alert.discovery_score:.0f}/100 | Risk: {alert.risk_score:.0f}/100")
            print(f"   ⏰ {time_ago:.1f}h ago | Tier: {alert.current_tier.title()}")
            print(f"   📝 {alert.recommended_action}")
            print()
    
    async def show_system_stats(self):
        """Display comprehensive system statistics"""
        if not self.alert_system:
            print("❌ Alert system not initialized")
            return
        
        stats = self.alert_system.get_alert_stats()
        
        print("\n📊 TRADER MONITORING SYSTEM STATS")
        print("=" * 40)
        print(f"🎯 Tracked Traders: {stats['tracked_traders']}")
        print(f"🚨 Active Alerts: {stats['total_active_alerts']}")
        print(f"📅 Alerts (24h): {stats['alerts_24h']}")
        
        if stats['alert_types_24h']:
            print(f"\n📊 ALERT TYPES (24h):")
            for alert_type, count in stats['alert_types_24h'].items():
                print(f"   {alert_type.replace('_', ' ').title()}: {count}")
        
        if stats['alert_levels_24h']:
            print(f"\n🚨 ALERT LEVELS (24h):")
            for level, count in stats['alert_levels_24h'].items():
                print(f"   {level.upper()}: {count}")
        
        last_run = stats.get('last_monitoring_run', 0)
        if last_run:
            last_run_ago = (time.time() - last_run) / 3600
            print(f"\n⏰ Last Monitoring Run: {last_run_ago:.1f} hours ago")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Trader Performance Monitoring with Alerts")
    parser.add_argument("--mode", choices=["single", "continuous", "alerts", "stats"], 
                       default="single", help="Monitoring mode")
    parser.add_argument("--timeframes", nargs="+", choices=["24h", "7d", "30d"], 
                       default=["24h", "7d"], help="Timeframes to monitor")
    parser.add_argument("--interval", type=int, default=30, 
                       help="Check interval in minutes for continuous mode")
    parser.add_argument("--alert-level", choices=["low", "medium", "high", "critical"],
                       help="Filter alerts by level")
    
    args = parser.parse_args()
    
    # Initialize monitoring system
    monitor = TraderMonitoringDaemon()
    if not await monitor.initialize():
        print("❌ Failed to initialize monitoring system")
        return
    
    try:
        if args.mode == "single":
            print("\n🔍 SINGLE MONITORING CYCLE")
            print("=" * 40)
            alerts = await monitor.run_single_monitoring_cycle(args.timeframes)
            monitor._display_cycle_results(alerts, 0, 1)
            
        elif args.mode == "continuous":
            print("\n🔄 CONTINUOUS MONITORING MODE")
            print("=" * 40)
            await monitor.run_continuous_monitoring(args.interval, args.timeframes)
            
        elif args.mode == "alerts":
            await monitor.show_active_alerts(args.alert_level)
            
        elif args.mode == "stats":
            await monitor.show_system_stats()
        
        print("\n💡 USAGE EXAMPLES:")
        print("# Run single monitoring cycle")
        print("python scripts/run_trader_monitoring.py --mode single")
        print()
        print("# Start continuous monitoring (every 30 min)")
        print("python scripts/run_trader_monitoring.py --mode continuous --interval 30")
        print()
        print("# Show active alerts")
        print("python scripts/run_trader_monitoring.py --mode alerts")
        print()
        print("# Show only critical alerts")
        print("python scripts/run_trader_monitoring.py --mode alerts --alert-level critical")
        print()
        print("# Show system statistics")
        print("python scripts/run_trader_monitoring.py --mode stats")
        
    except KeyboardInterrupt:
        print("\n🛑 Monitoring interrupted by user")
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 