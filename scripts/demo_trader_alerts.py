#!/usr/bin/env python3
"""
Trader Alert System Demo

Demonstrates the complete trader performance alert system including:
- Real-time trader monitoring
- Alert generation for various scenarios
- Telegram integration
- Alert management and filtering

This shows how the system provides early warnings about elite trader discoveries
and performance changes before strategies become widely known.
"""

import asyncio
import sys
import os
import time
from datetime import datetime
from typing import List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.trader_performance_analyzer import (
    TraderPerformanceAnalyzer,
    PerformanceTimeframe
)
from services.trader_alert_system import (
    TraderAlertSystem,
    TraderAlert,
    TraderAlertType,
    TraderAlertLevel
)
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager
from services.logger_setup import LoggerSetup

class TraderAlertDemo:
    """Comprehensive demonstration of trader alert system"""
    
    def __init__(self):
        self.logger_setup = LoggerSetup('TraderAlertDemo')
        self.logger = self.logger_setup.logger
        
        self.analyzer = None
        self.alert_system = None
        
    async def initialize(self):
        """Initialize the demo system"""
        try:
            print("🔧 Initializing Trader Alert Demo System...")
            
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
            
            print("✅ Demo system initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing demo system: {e}")
            return False
    
    async def demo_alert_types(self):
        """Demonstrate different types of trader alerts"""
        print("\n🚨 TRADER ALERT TYPES DEMONSTRATION")
        print("=" * 60)
        
        # Demo 1: Single monitoring cycle
        print("\n1️⃣ SINGLE MONITORING CYCLE")
        print("-" * 30)
        print("Running trader discovery and alert generation...")
        
        try:
            start_time = time.time()
            alerts = await self.alert_system.monitor_trader_performance([
                PerformanceTimeframe.HOUR_24,
                PerformanceTimeframe.DAYS_7
            ])
            
            elapsed = time.time() - start_time
            print(f"✅ Completed in {elapsed:.2f} seconds")
            print(f"🚨 Generated {len(alerts)} alerts")
            
            if alerts:
                self._display_alerts_summary(alerts)
            else:
                print("ℹ️ No alerts generated (first run or no significant changes)")
                
        except Exception as e:
            print(f"❌ Error in monitoring cycle: {e}")
    
    def _display_alerts_summary(self, alerts: List[TraderAlert]):
        """Display summary of generated alerts"""
        print(f"\n📊 ALERT SUMMARY ({len(alerts)} total)")
        print("-" * 40)
        
        # Group by type and level
        by_type = {}
        by_level = {}
        
        for alert in alerts:
            alert_type = alert.alert_type.value
            alert_level = alert.alert_level.value
            
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
            by_level[alert_level] = by_level.get(alert_level, 0) + 1
        
        # Display by type
        print("🎯 Alert Types:")
        for alert_type, count in by_type.items():
            type_name = alert_type.replace('_', ' ').title()
            print(f"   {type_name}: {count}")
        
        # Display by level
        print(f"\n🚨 Alert Levels:")
        for level in ['critical', 'high', 'medium', 'low']:
            count = by_level.get(level, 0)
            if count > 0:
                print(f"   {level.upper()}: {count}")
        
        # Show detailed view of top alerts
        top_alerts = sorted(alerts, key=lambda a: a.significance_score, reverse=True)[:3]
        
        if top_alerts:
            print(f"\n⭐ TOP 3 ALERTS:")
            for i, alert in enumerate(top_alerts, 1):
                print(f"\n{i}. [{alert.alert_level.value.upper()}] {alert.title}")
                print(f"   👤 {alert.trader_name} ({alert.trader_address[:8]}...)")
                print(f"   🎯 Score: {alert.discovery_score:.0f}/100 | Significance: {alert.significance_score:.0f}/100")
                print(f"   📝 {alert.recommended_action}")
    
    async def demo_continuous_monitoring(self, cycles: int = 3, interval_seconds: int = 60):
        """Demonstrate continuous monitoring with alerts"""
        print(f"\n🔄 CONTINUOUS MONITORING DEMO")
        print(f"Running {cycles} monitoring cycles with {interval_seconds}s intervals")
        print("=" * 60)
        
        total_alerts = []
        
        for cycle in range(1, cycles + 1):
            print(f"\n🔄 CYCLE {cycle}/{cycles}")
            print(f"🕒 Time: {datetime.now().strftime('%H:%M:%S')}")
            
            try:
                start_time = time.time()
                alerts = await self.alert_system.monitor_trader_performance()
                elapsed = time.time() - start_time
                
                print(f"⏱️  Duration: {elapsed:.2f}s | Alerts: {len(alerts)}")
                
                if alerts:
                    # Show immediate high-priority alerts
                    critical_high = [a for a in alerts 
                                   if a.alert_level in [TraderAlertLevel.CRITICAL, TraderAlertLevel.HIGH]]
                    
                    if critical_high:
                        print(f"🚨 PRIORITY ALERTS:")
                        for alert in critical_high[:2]:  # Show top 2
                            print(f"   [{alert.alert_level.value.upper()}] {alert.title}")
                            print(f"   👤 {alert.trader_name} | Score: {alert.discovery_score:.0f}")
                
                total_alerts.extend(alerts)
                
                # Wait for next cycle
                if cycle < cycles:
                    print(f"⏳ Waiting {interval_seconds}s for next cycle...")
                    await asyncio.sleep(interval_seconds)
                    
            except Exception as e:
                print(f"❌ Error in cycle {cycle}: {e}")
        
        # Final summary
        print(f"\n📊 CONTINUOUS MONITORING SUMMARY")
        print("-" * 40)
        print(f"Total Cycles: {cycles}")
        print(f"Total Alerts: {len(total_alerts)}")
        
        if total_alerts:
            self._display_alerts_summary(total_alerts)
    
    async def demo_alert_filtering(self):
        """Demonstrate alert filtering and management"""
        print(f"\n🔍 ALERT FILTERING & MANAGEMENT DEMO")
        print("=" * 60)
        
        # Get all active alerts
        all_alerts = self.alert_system.get_active_alerts()
        print(f"📊 Total Active Alerts: {len(all_alerts)}")
        
        if not all_alerts:
            print("ℹ️ No active alerts found. Run monitoring first to generate alerts.")
            return
        
        # Filter by different levels
        for level in ['critical', 'high', 'medium', 'low']:
            level_alerts = self.alert_system.get_active_alerts(level)
            print(f"🚨 {level.upper()} alerts: {len(level_alerts)}")
            
            if level_alerts:
                recent = level_alerts[-1]  # Most recent
                time_ago = (time.time() - recent.created_at) / 3600
                print(f"   Most recent: {recent.title} ({time_ago:.1f}h ago)")
        
        # Show system statistics
        stats = self.alert_system.get_alert_stats()
        print(f"\n📈 SYSTEM STATISTICS:")
        print(f"   🎯 Tracked Traders: {stats['tracked_traders']}")
        print(f"   📅 Alerts (24h): {stats['alerts_24h']}")
        print(f"   💾 Total Active: {stats['total_active_alerts']}")
        
        if stats['alert_types_24h']:
            print(f"\n📊 Alert Types (24h):")
            for alert_type, count in stats['alert_types_24h'].items():
                print(f"   {alert_type.replace('_', ' ').title()}: {count}")
    
    async def demo_telegram_integration(self):
        """Demonstrate Telegram alert integration"""
        print(f"\n📱 TELEGRAM INTEGRATION DEMO")
        print("=" * 60)
        
        # Check if Telegram is configured
        try:
            from services.telegram_alerter import TelegramAlerter
            
            # Try to initialize Telegram alerter
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            telegram_config = config.get('TELEGRAM', {})
            if not telegram_config.get('bot_token') or not telegram_config.get('chat_id'):
                print("ℹ️ Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
                print("   Example configuration:")
                print("   TELEGRAM_BOT_TOKEN=your_bot_token")
                print("   TELEGRAM_CHAT_ID=your_chat_id")
                return
            
            # Initialize Telegram alerter
            telegram_alerter = TelegramAlerter(
                config=telegram_config,
                logger_setup=LoggerSetup('TelegramDemo')
            )
            
            # Setup Telegram integration
            self.alert_system.setup_telegram_alerts(telegram_alerter, min_level='high')
            print("✅ Telegram integration enabled for HIGH+ alerts")
            
            # Run monitoring with Telegram alerts
            print("🔄 Running monitoring cycle with Telegram alerts...")
            alerts = await self.alert_system.monitor_trader_performance()
            
            telegram_sent = sum(1 for a in alerts if a.alert_level.value in ['high', 'critical'])
            print(f"📱 Sent {telegram_sent} Telegram notifications")
            
        except ImportError:
            print("❌ Telegram alerter not available")
        except Exception as e:
            print(f"❌ Error setting up Telegram integration: {e}")
    
    async def demo_real_world_scenarios(self):
        """Demonstrate real-world alert scenarios"""
        print(f"\n🌍 REAL-WORLD SCENARIOS DEMO")
        print("=" * 60)
        
        scenarios = [
            {
                'name': "Elite Trader Discovery",
                'description': "New trader achieves elite status with 90+ score",
                'timeframes': [PerformanceTimeframe.HOUR_24]
            },
            {
                'name': "Cross-Timeframe Consistency",
                'description': "Trader excels in both 24h and 7d performance",
                'timeframes': [PerformanceTimeframe.HOUR_24, PerformanceTimeframe.DAYS_7]
            },
            {
                'name': "Performance Monitoring",
                'description': "Track performance changes and tier upgrades",
                'timeframes': [PerformanceTimeframe.DAYS_7]
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{i}. {scenario['name']}")
            print(f"   {scenario['description']}")
            print(f"   Timeframes: {[tf.value for tf in scenario['timeframes']]}")
            
            try:
                alerts = await self.alert_system.monitor_trader_performance(scenario['timeframes'])
                
                relevant_alerts = []
                if scenario['name'] == "Elite Trader Discovery":
                    relevant_alerts = [a for a in alerts if a.alert_type == TraderAlertType.NEW_ELITE_DISCOVERY]
                elif scenario['name'] == "Cross-Timeframe Consistency":
                    relevant_alerts = [a for a in alerts if a.alert_type == TraderAlertType.CONSISTENT_PERFORMER]
                else:
                    relevant_alerts = alerts
                
                print(f"   🚨 Generated {len(relevant_alerts)} relevant alerts")
                
                if relevant_alerts:
                    top_alert = max(relevant_alerts, key=lambda a: a.significance_score)
                    print(f"   ⭐ Top alert: {top_alert.title} (Score: {top_alert.significance_score:.0f})")
                
            except Exception as e:
                print(f"   ❌ Error in scenario: {e}")

async def main():
    """Main demo function"""
    print("🎯 TRADER ALERT SYSTEM COMPREHENSIVE DEMO")
    print("=" * 60)
    print("This demo shows how to discover elite traders before their strategies")
    print("become widely known, giving you a significant market edge.")
    print()
    
    # Initialize demo
    demo = TraderAlertDemo()
    if not await demo.initialize():
        print("❌ Failed to initialize demo system")
        return
    
    try:
        # Run different demo scenarios
        await demo.demo_alert_types()
        
        print("\n" + "="*60)
        input("Press Enter to continue with continuous monitoring demo...")
        
        await demo.demo_continuous_monitoring(cycles=2, interval_seconds=30)
        
        print("\n" + "="*60)
        input("Press Enter to continue with alert filtering demo...")
        
        await demo.demo_alert_filtering()
        
        print("\n" + "="*60)
        input("Press Enter to continue with Telegram integration demo...")
        
        await demo.demo_telegram_integration()
        
        print("\n" + "="*60)
        input("Press Enter to continue with real-world scenarios demo...")
        
        await demo.demo_real_world_scenarios()
        
        print("\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print()
        print("💡 NEXT STEPS:")
        print("1. Set up continuous monitoring with:")
        print("   python scripts/run_trader_monitoring.py --mode continuous")
        print()
        print("2. Configure Telegram alerts in .env:")
        print("   TELEGRAM_BOT_TOKEN=your_bot_token")
        print("   TELEGRAM_CHAT_ID=your_chat_id")
        print()
        print("3. Monitor active alerts with:")
        print("   python scripts/run_trader_monitoring.py --mode alerts")
        print()
        print("🚀 Start discovering elite traders before everyone else!")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Error during demo: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 