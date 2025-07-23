#!/usr/bin/env python3
"""
Whale Movement Tracking Demo

Demonstrates real-time whale movement tracking with alerts and analysis.
Shows how to monitor whale wallets and detect significant trading activity.
"""

import asyncio
import os
import sys
import signal
from typing import Dict, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.whale_movement_tracker import WhaleMovementTracker
from services.whale_discovery_service import WhaleDiscoveryService
from api.birdeye_connector import BirdeyeAPI
from core.config_manager import ConfigManager

class WhaleTrackingDemo:
    """Demonstration of whale movement tracking system"""
    
    def __init__(self):
        self.running = True
        self.tracker = None
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down whale tracking...")
        self.running = False

    async def run_demo(self):
        """Run the whale tracking demonstration"""
        print("🐋 WHALE MOVEMENT TRACKING SYSTEM")
        print("Real-time monitoring of whale wallet activity")
        print("=" * 60)
        
        # Initialize services
        await self._initialize_services()
        
        if not self.tracker:
            print("❌ Failed to initialize whale tracking services")
            return
        
        # Show initial status
        await self._show_tracking_status()
        
        # Add some demo whales if database is empty
        await self._ensure_demo_whales()
        
        # Start background monitoring
        monitoring_task = asyncio.create_task(
            self.tracker.start_monitoring(check_interval_seconds=60)  # Check every minute for demo
        )
        
        # Start demo monitoring loop
        demo_task = asyncio.create_task(self._demo_monitoring_loop())
        
        try:
            # Run until interrupted
            await asyncio.gather(monitoring_task, demo_task)
        except asyncio.CancelledError:
            print("🏁 Whale tracking demo completed")

    async def _initialize_services(self):
        """Initialize all required services"""
        try:
            print("🔧 Initializing services...")
            
            # Load configuration
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # Initialize API
            birdeye_config = config.get('BIRDEYE_API', {})
            birdeye_api = BirdeyeAPI(config=birdeye_config)
            
            # Initialize whale discovery service
            discovery_service = WhaleDiscoveryService(birdeye_api)
            
            # Initialize whale movement tracker
            self.tracker = WhaleMovementTracker(
                birdeye_api=birdeye_api,
                whale_discovery_service=discovery_service
            )
            
            print("✅ Services initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing services: {e}")

    async def _show_tracking_status(self):
        """Show current whale tracking status"""
        stats = self.tracker.get_tracking_stats()
        
        print("\n📊 CURRENT TRACKING STATUS:")
        print(f"   🐋 Tracked Whales: {stats['tracked_whales']}")
        print(f"   📈 Movements (24h): {stats['movements_24h']}")
        print(f"   🚨 Active Alerts: {stats['active_alerts']}")
        print(f"   💰 Total Value (24h): ${stats['total_value_24h']:,.0f}")
        print(f"   📊 Avg Movement Size: ${stats['avg_movement_size']:,.0f}")
        
        # Show recent alerts
        alerts = self.tracker.get_active_alerts()
        if alerts:
            print(f"\n🚨 RECENT ALERTS ({len(alerts)}):")
            for alert in alerts[-5:]:  # Show last 5 alerts
                print(f"   [{alert.alert_level.value.upper()}] {alert.whale_name}: ${alert.total_value:,.0f}")
                print(f"      {alert.recommended_action}")

    async def _ensure_demo_whales(self):
        """Ensure we have some whales to track for demo purposes"""
        stats = self.tracker.get_tracking_stats()
        
        if stats['tracked_whales'] < 5:
            print("\n🔍 Discovering whales for tracking demo...")
            
            # Discover some whales for the demo
            discovery_service = self.tracker.whale_discovery_service
            if discovery_service:
                try:
                    new_whales = await discovery_service.discover_new_whales(max_discoveries=10)
                    print(f"✅ Discovered {len(new_whales)} whales for tracking")
                    
                    # Update tracker with new whales
                    for whale in new_whales:
                        await self.tracker.add_whale_for_tracking(whale.address)
                        
                except Exception as e:
                    print(f"⚠️ Could not discover whales: {e}")
                    # Add some demo whale addresses
                    demo_whales = [
                        "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",  # Example whale
                        "HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH",  # Example whale
                    ]
                    
                    for whale_addr in demo_whales:
                        await self.tracker.add_whale_for_tracking(whale_addr)
                    
                    print(f"🐋 Added {len(demo_whales)} demo whales for tracking")

    async def _demo_monitoring_loop(self):
        """Demo monitoring loop that shows real-time updates"""
        last_movement_count = 0
        last_alert_count = 0
        
        print("\n🔄 Starting real-time monitoring...")
        print("Press Ctrl+C to stop monitoring")
        print("-" * 40)
        
        while self.running:
            try:
                # Get current stats
                stats = self.tracker.get_tracking_stats()
                current_movements = stats['movements_24h']
                current_alerts = stats['active_alerts']
                
                # Check for new movements
                if current_movements > last_movement_count:
                    new_movements = current_movements - last_movement_count
                    print(f"📈 NEW: {new_movements} whale movements detected!")
                    
                    # Show recent movements
                    recent_movements = self.tracker.get_recent_movements(1)  # Last hour
                    for movement in recent_movements[-new_movements:]:
                        print(f"   🐋 {movement.description}")
                        print(f"      Alert Level: {movement.alert_level.value} | Confidence: {movement.confidence:.2%}")
                
                # Check for new alerts
                if current_alerts > last_alert_count:
                    new_alerts = current_alerts - last_alert_count
                    print(f"🚨 NEW: {new_alerts} whale alerts generated!")
                    
                    # Show recent alerts
                    recent_alerts = self.tracker.get_active_alerts()
                    for alert in recent_alerts[-new_alerts:]:
                        print(f"   🚨 [{alert.alert_level.value.upper()}] {alert.whale_name}")
                        print(f"      💰 Value: ${alert.total_value:,.0f} | Score: {alert.significance_score:.0f}/100")
                        print(f"      📝 {alert.recommended_action}")
                
                # Update counters
                last_movement_count = current_movements
                last_alert_count = current_alerts
                
                # Show periodic status updates
                if int(asyncio.get_event_loop().time()) % 300 == 0:  # Every 5 minutes
                    print(f"⏰ Status Update - Tracking {stats['tracked_whales']} whales, "
                          f"{current_movements} movements (24h), {current_alerts} active alerts")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)

async def run_whale_tracking_analysis():
    """Run whale tracking analysis without continuous monitoring"""
    print("🐋 WHALE TRACKING ANALYSIS")
    print("=" * 40)
    
    # Initialize services
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    birdeye_config = config.get('BIRDEYE_API', {})
    birdeye_api = BirdeyeAPI(config=birdeye_config)
    
    discovery_service = WhaleDiscoveryService(birdeye_api)
    tracker = WhaleMovementTracker(birdeye_api, discovery_service)
    
    # Show current status
    stats = tracker.get_tracking_stats()
    print(f"📊 Tracking {stats['tracked_whales']} whale wallets")
    
    # Manually check for movements
    print("🔍 Checking for recent whale movements...")
    
    # This would trigger a manual check
    await tracker._check_whale_movements()
    
    # Show results
    recent_movements = tracker.get_recent_movements(24)
    active_alerts = tracker.get_active_alerts()
    
    print(f"\n📈 RECENT MOVEMENTS ({len(recent_movements)}):")
    for movement in recent_movements[-10:]:  # Show last 10
        print(f"   🐋 {movement.description}")
        print(f"      Time: {movement.timestamp} | Alert: {movement.alert_level.value}")
    
    print(f"\n🚨 ACTIVE ALERTS ({len(active_alerts)}):")
    for alert in active_alerts[-5:]:  # Show last 5
        print(f"   [{alert.alert_level.value.upper()}] {alert.whale_name}")
        print(f"   💰 ${alert.total_value:,.0f} | {alert.recommended_action}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Whale Movement Tracking Demo")
    parser.add_argument("--mode", choices=["monitor", "analyze"], default="monitor",
                       help="Run mode: monitor (continuous) or analyze (one-time)")
    
    args = parser.parse_args()
    
    if args.mode == "monitor":
        demo = WhaleTrackingDemo()
        asyncio.run(demo.run_demo())
    else:
        asyncio.run(run_whale_tracking_analysis())

if __name__ == "__main__":
    main() 