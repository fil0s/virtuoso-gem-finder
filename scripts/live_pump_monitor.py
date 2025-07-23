#!/usr/bin/env python3
"""
🔥 LIVE PUMP.FUN MONITOR - Real-time token detection with comprehensive debug
Monitor live pump.fun launches with enhanced RPC monitoring and detailed logging
"""

import asyncio
import logging
import time
import sys
import os
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Add current directory to path
sys.path.append('.')

class LivePumpMonitor:
    """
    🚀 Live pump.fun monitoring system with comprehensive debug logging
    
    Features:
    • Enhanced RPC monitoring with debug output
    • Real-time token detection logging
    • Performance metrics tracking
    • Connection health monitoring
    • Comprehensive event analysis
    • Live statistics dashboard
    """
    
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.start_time = time.time()
        self.logger = self._setup_logger()
        
        # Monitoring components
        self.rpc_monitor = None
        self.early_gem_detector = None
        
        # Live tracking
        self.tokens_detected = []
        self.events_logged = []
        self.performance_snapshots = []
        
        # Statistics
        self.stats = {
            'monitoring_start': datetime.now(),
            'tokens_detected': 0,
            'events_processed': 0,
            'alerts_sent': 0,
            'uptime_seconds': 0,
            'last_token_time': None,
            'rpc_connections': 0,
            'rpc_disconnections': 0
        }
        
        # Control flags
        self.running = True
        self.force_exit = False
        
        self.logger.info("🔥 Live Pump Monitor initialized")
        self.logger.info(f"   🐛 Debug mode: {'ENABLED' if debug_mode else 'DISABLED'}")
        self.logger.info(f"   📊 Comprehensive logging: ACTIVE")
        self.logger.info(f"   🎯 Target: Real pump.fun token launches")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup enhanced logging for live monitoring"""
        logger = logging.getLogger('LivePumpMonitor')
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        if not logger.handlers:
            # Console handler
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - 🔥 LIVE_MONITOR - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            # File handler for debug logs
            if self.debug_mode:
                file_handler = logging.FileHandler(f'live_monitor_debug_{int(time.time())}.log')
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        
        return logger
    
    async def initialize_monitoring(self):
        """Initialize all monitoring components"""
        self.logger.info("🚀 Initializing live monitoring components...")
        
        try:
            # Initialize enhanced RPC monitor
            self.logger.info("   📡 Setting up enhanced RPC monitor...")
            from services.pump_fun_rpc_monitor import PumpFunRPCMonitor
            
            self.rpc_monitor = PumpFunRPCMonitor(
                debug_mode=True,
                logger=self.logger
            )
            
            # Set up RPC callbacks
            self.rpc_monitor.set_callbacks(
                on_new_token=self._handle_live_token_detection,
                on_significant_trade=self._handle_trade_event,
                on_graduation=self._handle_graduation_event
            )
            
            self.logger.info("   ✅ Enhanced RPC monitor configured")
            
            # Initialize early gem detector
            self.logger.info("   🎯 Setting up early gem detector...")
            from scripts.early_gem_detector import EarlyGemDetector
            
            self.early_gem_detector = EarlyGemDetector(debug_mode=True)
            self.logger.info("   ✅ Early gem detector initialized")
            
            self.logger.info("✅ All monitoring components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Monitoring initialization failed: {e}")
            import traceback
            self.logger.debug(f"   📝 Initialization error trace: {traceback.format_exc()}")
            raise
    
    async def start_live_monitoring(self):
        """Start live monitoring with comprehensive logging"""
        self.logger.info("🚀 STARTING LIVE PUMP.FUN MONITORING")
        self.logger.info("=" * 60)
        self.logger.info(f"   ⏰ Start time: {self.stats['monitoring_start'].isoformat()}")
        self.logger.info(f"   🎯 Monitoring: Real pump.fun token launches")
        self.logger.info(f"   📡 Method: Enhanced Solana RPC + WebSocket")
        self.logger.info(f"   🐛 Debug logging: ENABLED")
        self.logger.info(f"   📊 Performance tracking: ACTIVE")
        print()
        
        try:
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start RPC monitoring in background
            self.logger.info("📡 Starting RPC monitoring...")
            rpc_task = asyncio.create_task(self.rpc_monitor.start_monitoring())
            
            # Start statistics logging
            stats_task = asyncio.create_task(self._log_statistics_loop())
            
            # Start performance monitoring
            perf_task = asyncio.create_task(self._performance_monitoring_loop())
            
            # Start status dashboard
            dashboard_task = asyncio.create_task(self._status_dashboard_loop())
            
            self.logger.info("🔄 All monitoring tasks started - waiting for pump.fun events...")
            self.logger.info("   💡 TIP: Press Ctrl+C for graceful shutdown with statistics")
            print()
            
            # Wait for tasks to complete or interruption
            await asyncio.gather(
                rpc_task,
                stats_task,
                perf_task,
                dashboard_task,
                return_exceptions=True
            )
            
        except KeyboardInterrupt:
            self.logger.info("⏹️ Graceful shutdown requested by user")
            self.running = False
            
        except Exception as e:
            self.logger.error(f"❌ Live monitoring failed: {e}")
            import traceback
            self.logger.debug(f"   📝 Monitoring error trace: {traceback.format_exc()}")
            
        finally:
            await self._shutdown_monitoring()
    
    async def _handle_live_token_detection(self, token_data: Dict):
        """Handle live token detection with comprehensive logging"""
        try:
            self.stats['tokens_detected'] += 1
            self.stats['last_token_time'] = datetime.now()
            
            # Add to our tracking
            enhanced_token = {
                **token_data,
                'detection_number': self.stats['tokens_detected'],
                'detection_timestamp': time.time(),
                'monitor_uptime': time.time() - self.start_time
            }
            
            self.tokens_detected.append(enhanced_token)
            
            # Comprehensive logging
            self.logger.info("🚨 LIVE TOKEN DETECTED!")
            self.logger.info("=" * 40)
            self.logger.info(f"   🎯 Token #{self.stats['tokens_detected']}")
            self.logger.info(f"   📛 Symbol: {token_data['symbol']}")
            self.logger.info(f"   🏠 Address: {token_data['token_address']}")
            self.logger.info(f"   💰 Market Cap: ${token_data['market_cap']:,}")
            self.logger.info(f"   💲 Price: ${token_data['price']:.8f}")
            self.logger.info(f"   🔍 Detection Method: {token_data['detection_method']}")
            self.logger.info(f"   ⏰ Age: {token_data['estimated_age_minutes']:.1f} minutes")
            self.logger.info(f"   🚀 Ultra Early Eligible: {token_data['ultra_early_bonus_eligible']}")
            
            if 'debug_info' in token_data:
                debug_info = token_data['debug_info']
                self.logger.info(f"   🐛 Debug Info:")
                self.logger.info(f"      📊 Processing #: {debug_info.get('processing_number', 'N/A')}")
                self.logger.info(f"      📏 Data Length: {debug_info.get('raw_data_length', 'N/A')} bytes")
                self.logger.info(f"      🎯 Confidence: {debug_info.get('detection_confidence', 'N/A')}")
            
            # 🚀 Try to analyze with early gem detector
            self.logger.info("   🔍 Running early gem analysis...")
            try:
                candidates = [enhanced_token]
                analyzed = await self.early_gem_detector.analyze_early_candidates(candidates)
                
                if analyzed:
                    analysis = analyzed[0]
                    score = analysis['final_score']
                    conviction = analysis['conviction_level']
                    
                    self.logger.info(f"   📊 Early Gem Score: {score:.1f}/100")
                    self.logger.info(f"   🎯 Conviction Level: {conviction}")
                    
                    # Check for high conviction
                    if score >= 45:
                        self.logger.info("   🚨 HIGH CONVICTION OPPORTUNITY!")
                        self.stats['alerts_sent'] += 1
                        
                        # Trigger Telegram alert
                        await self._send_high_conviction_alert(analysis)
                else:
                    self.logger.info("   ⚠️ Analysis failed - no results")
                    
            except Exception as analysis_error:
                self.logger.warning(f"   ⚠️ Analysis error: {analysis_error}")
            
            self.logger.info("=" * 40)
            print()
            
        except Exception as e:
            self.logger.error(f"❌ Token detection handling error: {e}")
            import traceback
            self.logger.debug(f"   📝 Detection error trace: {traceback.format_exc()}")
    
    async def _handle_trade_event(self, trade_data: Dict):
        """Handle significant trade events"""
        self.logger.debug(f"📈 Trade Event: {trade_data}")
        self.events_logged.append({
            'type': 'trade',
            'timestamp': time.time(),
            'data': trade_data
        })
    
    async def _handle_graduation_event(self, graduation_data: Dict):
        """Handle graduation events"""
        self.logger.info(f"🎓 GRADUATION EVENT: {graduation_data}")
        self.events_logged.append({
            'type': 'graduation',
            'timestamp': time.time(),
            'data': graduation_data
        })
    
    async def _log_statistics_loop(self):
        """Periodic statistics logging"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Log every minute
                
                if not self.running:
                    break
                
                # Update stats
                self.stats['uptime_seconds'] = time.time() - self.start_time
                self.stats['events_processed'] = len(self.events_logged)
                
                # Get RPC performance
                rpc_stats = {}
                if self.rpc_monitor:
                    rpc_stats = self.rpc_monitor.get_performance_stats()
                
                self.logger.info("📊 PERIODIC STATISTICS")
                self.logger.info("-" * 30)
                self.logger.info(f"   ⏰ Uptime: {self.stats['uptime_seconds']:.0f}s ({self.stats['uptime_seconds']/60:.1f}m)")
                self.logger.info(f"   🚨 Tokens Detected: {self.stats['tokens_detected']}")
                self.logger.info(f"   📧 Alerts Sent: {self.stats['alerts_sent']}")
                self.logger.info(f"   📊 Events Processed: {self.stats['events_processed']}")
                
                if rpc_stats:
                    self.logger.info(f"   📡 RPC Connected: {rpc_stats['is_connected']}")
                    self.logger.info(f"   🔄 RPC Events: {rpc_stats['events_processed']}")
                    self.logger.info(f"   ⚡ Events/sec: {rpc_stats['events_per_second']:.2f}")
                
                if self.stats['last_token_time']:
                    minutes_ago = (datetime.now() - self.stats['last_token_time']).total_seconds() / 60
                    self.logger.info(f"   🕐 Last Token: {minutes_ago:.1f}m ago")
                
                print()
                
            except Exception as e:
                self.logger.debug(f"Statistics logging error: {e}")
    
    async def _performance_monitoring_loop(self):
        """Monitor performance metrics"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                if not self.running:
                    break
                
                # Capture performance snapshot
                snapshot = {
                    'timestamp': time.time(),
                    'uptime': time.time() - self.start_time,
                    'tokens_detected': self.stats['tokens_detected'],
                    'events_processed': self.stats['events_processed']
                }
                
                if self.rpc_monitor:
                    rpc_stats = self.rpc_monitor.get_performance_stats()
                    snapshot.update({
                        'rpc_connected': rpc_stats['is_connected'],
                        'rpc_events': rpc_stats['events_processed'],
                        'rpc_errors': rpc_stats.get('websocket_errors', 0),
                        'connection_attempts': rpc_stats.get('connection_attempts', 0)
                    })
                
                self.performance_snapshots.append(snapshot)
                
                # Keep only last 24 snapshots (2 hours)
                if len(self.performance_snapshots) > 24:
                    self.performance_snapshots.pop(0)
                
                self.logger.debug(f"📈 Performance snapshot captured: {snapshot}")
                
            except Exception as e:
                self.logger.debug(f"Performance monitoring error: {e}")
    
    async def _status_dashboard_loop(self):
        """Live status dashboard"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                
                if not self.running:
                    break
                
                # Show live dashboard
                uptime_minutes = (time.time() - self.start_time) / 60
                
                self.logger.info("🎯 LIVE STATUS DASHBOARD")
                self.logger.info(f"   ⏰ Uptime: {uptime_minutes:.1f}m")
                self.logger.info(f"   🚨 Tokens: {self.stats['tokens_detected']}")
                self.logger.info(f"   📡 RPC: {'🟢 CONNECTED' if self.rpc_monitor and self.rpc_monitor.is_connected else '🔴 DISCONNECTED'}")
                
                if self.rpc_monitor:
                    try:
                        debug_summary = self.rpc_monitor.get_debug_summary()
                        conn_health = debug_summary['connection_health']
                        event_proc = debug_summary['event_processing']
                        
                        self.logger.info(f"   📥 Messages: {event_proc['messages_received']}")
                        self.logger.info(f"   🎯 Notifications: {event_proc['program_notifications']}")
                        self.logger.info(f"   ✅ Parse Rate: {event_proc['parse_success_rate']:.1f}%")
                        
                        # Connection health
                        time_since_heartbeat = conn_health['time_since_heartbeat']
                        if time_since_heartbeat > 60:
                            self.logger.warning(f"   ⚠️ Last heartbeat: {time_since_heartbeat:.0f}s ago")
                    except:
                        # Fallback to basic stats if debug_summary not available
                        basic_stats = self.rpc_monitor.get_performance_stats()
                        self.logger.info(f"   🔄 Events: {basic_stats['events_processed']}")
                
                print()
                
            except Exception as e:
                self.logger.debug(f"Dashboard error: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"📨 Received signal {signum} - initiating graceful shutdown...")
        self.running = False
    
    async def _shutdown_monitoring(self):
        """Shutdown monitoring with comprehensive summary"""
        self.logger.info("🔄 Shutting down live monitoring...")
        
        try:
            # Cleanup RPC monitor
            if self.rpc_monitor:
                await self.rpc_monitor.cleanup()
            
            # Cleanup early gem detector
            if self.early_gem_detector:
                await self.early_gem_detector.cleanup()
            
            # Final statistics
            final_uptime = time.time() - self.start_time
            
            self.logger.info("📊 FINAL MONITORING SUMMARY")
            self.logger.info("=" * 50)
            self.logger.info(f"   ⏰ Total Uptime: {final_uptime:.0f}s ({final_uptime/60:.1f}m)")
            self.logger.info(f"   🚨 Tokens Detected: {self.stats['tokens_detected']}")
            self.logger.info(f"   📧 Alerts Sent: {self.stats['alerts_sent']}")
            self.logger.info(f"   📊 Events Processed: {self.stats['events_processed']}")
            self.logger.info(f"   📈 Detection Rate: {self.stats['tokens_detected']/(final_uptime/3600):.2f} tokens/hour")
            
            # Show detected tokens
            if self.tokens_detected:
                self.logger.info("\n🎯 DETECTED TOKENS:")
                for i, token in enumerate(self.tokens_detected, 1):
                    self.logger.info(f"   {i}. {token['symbol']} (${token['market_cap']:,}) - {token['detection_method']}")
            
            # Save debug data
            debug_data = {
                'session_stats': self.stats,
                'tokens_detected': self.tokens_detected,
                'events_logged': self.events_logged,
                'performance_snapshots': self.performance_snapshots
            }
            
            debug_filename = f"live_monitor_session_{int(self.start_time)}.json"
            with open(debug_filename, 'w') as f:
                json.dump(debug_data, f, indent=2, default=str)
            
            self.logger.info(f"💾 Debug data saved to: {debug_filename}")
            self.logger.info("✅ Live monitoring shutdown completed")
            
        except Exception as e:
            self.logger.error(f"❌ Shutdown error: {e}")
    
    async def _send_high_conviction_alert(self, analysis: Dict):
        """Send high conviction alert for promising early gems"""
        try:
            self.logger.info("📱 HIGH CONVICTION ALERT - Sending notification")
            
            # Extract key metrics for alert
            candidate = analysis.get('candidate', {})
            score = analysis.get('final_score', 0)
            conviction = analysis.get('conviction_level', 'UNKNOWN')
            
            alert_message = f"""
🚨 HIGH CONVICTION EARLY GEM DETECTED!

🎯 Symbol: {candidate.get('symbol', 'Unknown')}
🏠 Address: {candidate.get('token_address', 'Unknown')}
📊 Score: {score:.1f}/100 ({conviction})
💰 Market Cap: ${candidate.get('market_cap', 0):,}
💲 Price: ${candidate.get('price', 0):.8f}
⏰ Age: {candidate.get('estimated_age_minutes', 0):.1f}m
🔍 Method: {candidate.get('detection_method', 'Unknown')}

🚀 This is a LIVE detection from pump.fun monitoring!
"""
            
            # Send via telegram alerter if available
            if hasattr(self.early_gem_detector, 'telegram_alerter') and self.early_gem_detector.telegram_alerter:
                self.logger.info("   📱 Sending Telegram alert...")
                success = await self.early_gem_detector._send_early_gem_alert(analysis)
                if success:
                    self.logger.info("   ✅ Alert sent successfully")
                else:
                    self.logger.warning("   ⚠️ Alert sending failed")
            else:
                self.logger.info("   ⚠️ Telegram alerter not available")
                self.logger.info(f"   📝 Alert content: {alert_message}")
                
        except Exception as e:
            self.logger.error(f"❌ Alert sending failed: {e}")


async def main():
    """Main entry point for live monitoring"""
    print("🔥 LIVE PUMP.FUN MONITOR - Real-time Token Detection")
    print("=" * 65)
    print("   🎯 Monitoring: Real pump.fun token launches")
    print("   📡 Method: Enhanced Solana RPC + WebSocket")
    print("   🐛 Debug Mode: ENABLED")
    print("   📊 Comprehensive Logging: ACTIVE")
    print()
    print("   💡 This will run continuously until interrupted")
    print("   ⚠️  Use Ctrl+C for graceful shutdown with statistics")
    print()
    
    try:
        monitor = LivePumpMonitor(debug_mode=True)
        await monitor.initialize_monitoring()
        await monitor.start_live_monitoring()
        
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring interrupted by user")
    except Exception as e:
        print(f"\n❌ Monitoring failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
