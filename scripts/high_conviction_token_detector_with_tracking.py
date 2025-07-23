#!/usr/bin/env python3
"""
Enhanced High Conviction Token Detector with Position Tracking Integration

This enhanced version of the high conviction detector adds position tracking capabilities:
- Adds "Track Position" buttons to high-scoring token alerts
- Integrates with the position tracking system
- Provides seamless workflow from detection to position management

Based on the original high_conviction_token_detector.py with position tracking enhancements.
"""

import asyncio
import logging
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import original detector functionality
from scripts.high_conviction_token_detector import HighConvictionTokenDetector
from services.position_tracker import PositionTracker
from services.telegram_bot_handler import TelegramBotHandler
from services.telegram_alerter import TelegramAlerter, MinimalTokenMetrics
from services.logger_setup import LoggerSetup
from core.config_manager import ConfigManager

class EnhancedHighConvictionDetector(HighConvictionTokenDetector):
    """Enhanced detector with position tracking integration"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        # Initialize parent detector
        super().__init__(config_path)
        
        # Initialize position tracking services
        self.position_tracker = PositionTracker(logger=self.logger)
        
        # Initialize enhanced Telegram bot handler
        telegram_config = self.config.get('telegram', {})
        bot_token = telegram_config.get('bot_token', '')
        chat_id = telegram_config.get('chat_id', '')
        
        if bot_token and chat_id:
            self.telegram_bot_handler = TelegramBotHandler(
                self.position_tracker, self.telegram_alerter, self.birdeye_api, 
                self.config, self.logger
            )
            self.position_tracking_enabled = True
            self.logger.info("🎯 Position tracking integration enabled")
        else:
            self.telegram_bot_handler = None
            self.position_tracking_enabled = False
            self.logger.warning("⚠️ Position tracking disabled - Telegram configuration missing")
        
        # Configuration for position tracking alerts
        self.tracking_config = self.config.get('position_tracking', {})
        self.min_score_for_tracking = self.tracking_config.get('min_score_for_tracking', 7.0)
        self.auto_suggest_tracking = self.tracking_config.get('auto_suggest_tracking', True)
        
        self.logger.info(f"📊 Position tracking threshold: {self.min_score_for_tracking}")
    
    async def send_enhanced_alert(self, token_data: Dict[str, Any], score: float, 
                                scan_id: Optional[str] = None) -> bool:
        """
        Send enhanced alert with position tracking integration
        
        Args:
            token_data: Token analysis data
            score: Conviction score
            scan_id: Optional scan identifier
            
        Returns:
            True if alert sent successfully
        """
        try:
            # Create minimal token metrics for the alert
            metrics = self._create_token_metrics(token_data, score)
            
            # Send the standard gem alert first
            success = await self._send_standard_alert(metrics, score, token_data, scan_id)
            
            if not success:
                return False
            
            # If position tracking is enabled and score is high enough, send tracking suggestion
            if (self.position_tracking_enabled and 
                self.auto_suggest_tracking and 
                score >= self.min_score_for_tracking):
                
                await self._send_tracking_suggestion(metrics, score, token_data, scan_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error sending enhanced alert: {e}")
            return False
    
    def _create_token_metrics(self, token_data: Dict[str, Any], score: float) -> MinimalTokenMetrics:
        """Create MinimalTokenMetrics from token analysis data"""
        
        # Extract basic token info
        address = token_data.get('address', '')
        symbol = token_data.get('symbol', 'UNKNOWN')
        name = token_data.get('name', symbol)
        
        # Extract price and market data
        price = float(token_data.get('price', 0))
        market_cap = float(token_data.get('market_cap', 0))
        liquidity = float(token_data.get('liquidity', 0))
        volume_24h = float(token_data.get('volume_24h', 0))
        holders = int(token_data.get('holders', 0))
        price_change_24h = float(token_data.get('price_change_24h', 0))
        
        # Extract whale data if available
        whale_holdings = {}
        if 'whale_analysis' in token_data:
            whale_data = token_data['whale_analysis']
            if isinstance(whale_data, dict) and 'top_holders' in whale_data:
                for holder in whale_data['top_holders'][:5]:  # Top 5 whales
                    if isinstance(holder, dict):
                        addr = holder.get('address', '')
                        percentage = holder.get('percentage', 0)
                        if addr and percentage > 0:
                            whale_holdings[addr] = percentage
        
        # Extract volume trend and risk factors
        volume_trend = token_data.get('volume_trend', 'unknown')
        volume_acceleration = float(token_data.get('volume_acceleration', 0))
        tx_count_trend = token_data.get('tx_count_trend', 'unknown')
        
        risk_factors = []
        if 'risk_analysis' in token_data:
            risk_data = token_data['risk_analysis']
            if isinstance(risk_data, dict):
                risk_factors = risk_data.get('risk_factors', [])
        
        return MinimalTokenMetrics(
            symbol=symbol,
            address=address,
            price=price,
            name=name,
            mcap=market_cap,
            liquidity=liquidity,
            volume_24h=volume_24h,
            holders=holders,
            price_change_24h=price_change_24h,
            market_cap=market_cap,
            score=score,
            whale_holdings=whale_holdings,
            volume_trend=volume_trend,
            volume_acceleration=volume_acceleration,
            tx_count_trend=tx_count_trend,
            risk_factors=risk_factors
        )
    
    async def _send_standard_alert(self, metrics: MinimalTokenMetrics, score: float, 
                                 token_data: Dict[str, Any], scan_id: Optional[str]) -> bool:
        """Send the standard gem alert"""
        try:
            # Extract enhanced data for the alert
            enhanced_data = self._extract_enhanced_data(token_data)
            
            # Send via the standard telegram alerter
            self.telegram_alerter.send_gem_alert(
                metrics=metrics,
                score=score,
                enhanced_data=enhanced_data,
                scan_id=scan_id
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error sending standard alert: {e}")
            return False
    
    async def _send_tracking_suggestion(self, metrics: MinimalTokenMetrics, score: float,
                                      token_data: Dict[str, Any], scan_id: Optional[str]):
        """Send position tracking suggestion"""
        try:
            if not self.telegram_bot_handler:
                return
            
            # Create tracking suggestion message
            suggestion_message = self._build_tracking_suggestion_message(metrics, score)
            
            # Send via telegram alerter
            self.telegram_alerter.send_message(suggestion_message)
            
            self.logger.info(f"📈 Sent position tracking suggestion for {metrics.symbol} (score: {score:.1f})")
            
        except Exception as e:
            self.logger.error(f"❌ Error sending tracking suggestion: {e}")
    
    def _build_tracking_suggestion_message(self, metrics: MinimalTokenMetrics, score: float) -> str:
        """Build position tracking suggestion message"""
        
        # Score-based messaging
        if score >= 9.0:
            urgency = "🔥 PREMIUM OPPORTUNITY"
            suggestion = "Consider immediate position tracking"
        elif score >= 8.0:
            urgency = "🚀 HIGH CONVICTION"
            suggestion = "Strong candidate for position tracking"
        else:
            urgency = "📈 PROMISING SIGNAL"
            suggestion = "Consider tracking if aligned with strategy"
        
        # Build message
        lines = [
            f"🎯 <b>POSITION TRACKING SUGGESTION</b>",
            f"{urgency}",
            "",
            f"<b>Token:</b> {metrics.name} ({metrics.symbol})",
            f"<b>Score:</b> {score:.1f}/10",
            f"<b>Current Price:</b> ${metrics.price:.6f}",
            "",
            f"💡 <b>Suggestion:</b> {suggestion}",
            "",
            f"📱 <b>Quick Commands:</b>",
            f"<code>/track {metrics.address} {metrics.price:.6f}</code>",
            f"<code>/track {metrics.address} {metrics.price:.6f} 1000</code> (with $1000 size)",
            f"<code>/track {metrics.address} {metrics.price:.6f} 1000 25 10</code> (with 25% profit, 10% stop)",
            "",
            f"🔗 <b>Address:</b> <code>{metrics.address}</code>",
            "",
            f"ℹ️ Use <code>/help</code> for all position tracking commands"
        ]
        
        return "\n".join(lines)
    
    def _extract_enhanced_data(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enhanced data for alerts from token analysis"""
        enhanced_data = {}
        
        # Extract pump/dump analysis
        if 'pump_dump_analysis' in token_data:
            enhanced_data['enhanced_pump_dump_analysis'] = token_data['pump_dump_analysis']
        
        # Extract metadata analysis
        if 'metadata_analysis' in token_data:
            enhanced_data['enhanced_metadata_analysis'] = token_data['metadata_analysis']
        
        # Extract security info
        if 'security_analysis' in token_data:
            enhanced_data['security_info'] = token_data['security_analysis']
        
        return enhanced_data
    
    async def run_detection_cycle(self, max_tokens: int = 50, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Run enhanced detection cycle with position tracking integration
        
        Args:
            max_tokens: Maximum tokens to analyze
            scan_id: Optional scan identifier
            
        Returns:
            List of high conviction tokens found
        """
        try:
            self.logger.info(f"🔍 Starting enhanced detection cycle (max_tokens={max_tokens})")
            
            # Run the standard detection cycle
            high_conviction_tokens = []
            
            # Use the parent class detection logic
            discovered_tokens = await self.early_token_detector.discover_and_analyze(max_tokens)
            
            if not discovered_tokens:
                self.logger.warning("📭 No tokens discovered in this cycle")
                return []
            
            self.logger.info(f"🔍 Analyzing {len(discovered_tokens)} discovered tokens for high conviction signals")
            
            # Filter and score tokens
            for token_data in discovered_tokens:
                try:
                    # Calculate conviction score (using existing logic)
                    score = self._calculate_conviction_score(token_data)
                    
                    # Check if it meets our high conviction threshold
                    if score >= self.high_conviction_threshold:
                        token_data['conviction_score'] = score
                        high_conviction_tokens.append(token_data)
                        
                        # Send enhanced alert with position tracking
                        await self.send_enhanced_alert(token_data, score, scan_id)
                        
                        self.logger.info(f"🎯 High conviction token found: {token_data.get('symbol', 'UNKNOWN')} (score: {score:.1f})")
                
                except Exception as e:
                    self.logger.error(f"❌ Error processing token {token_data.get('address', 'UNKNOWN')}: {e}")
                    continue
            
            # Log cycle summary
            self.logger.info(f"✅ Detection cycle completed: {len(high_conviction_tokens)} high conviction tokens found")
            
            return high_conviction_tokens
            
        except Exception as e:
            self.logger.error(f"❌ Error in enhanced detection cycle: {e}")
            return []
    
    def _calculate_conviction_score(self, token_data: Dict[str, Any]) -> float:
        """
        Calculate conviction score for a token (using existing logic)
        This would use the same scoring logic as the original detector
        """
        # This would use the existing scoring logic from the parent class
        # For now, return the score if it exists, otherwise calculate basic score
        
        if 'score' in token_data:
            return float(token_data['score'])
        
        # Basic scoring fallback (would be replaced with actual logic)
        score = 0.0
        
        # Price momentum (0-2 points)
        price_change = token_data.get('price_change_24h', 0)
        if price_change > 50:
            score += 2.0
        elif price_change > 20:
            score += 1.5
        elif price_change > 10:
            score += 1.0
        
        # Volume (0-2 points)
        volume = token_data.get('volume_24h', 0)
        if volume > 1000000:
            score += 2.0
        elif volume > 500000:
            score += 1.5
        elif volume > 100000:
            score += 1.0
        
        # Liquidity (0-2 points)
        liquidity = token_data.get('liquidity', 0)
        if liquidity > 500000:
            score += 2.0
        elif liquidity > 250000:
            score += 1.5
        elif liquidity > 100000:
            score += 1.0
        
        # Market cap (0-2 points)
        market_cap = token_data.get('market_cap', 0)
        if 1000000 <= market_cap <= 50000000:  # Sweet spot
            score += 2.0
        elif market_cap <= 100000000:
            score += 1.0
        
        # Holders (0-2 points)
        holders = token_data.get('holders', 0)
        if holders > 1000:
            score += 2.0
        elif holders > 500:
            score += 1.5
        elif holders > 100:
            score += 1.0
        
        return min(score, 10.0)  # Cap at 10.0
    
    async def start_daemon(self, check_interval_minutes: int = 10):
        """
        Start the enhanced detection daemon with position tracking
        
        Args:
            check_interval_minutes: Minutes between detection cycles
        """
        self.logger.info(f"🚀 Starting enhanced high conviction detector daemon")
        self.logger.info(f"⏱️ Check interval: {check_interval_minutes} minutes")
        self.logger.info(f"🎯 Position tracking: {'✅ Enabled' if self.position_tracking_enabled else '❌ Disabled'}")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                cycle_start = time.time()
                
                self.logger.info(f"🔄 Starting detection cycle #{cycle_count}")
                
                try:
                    # Run detection cycle
                    scan_id = f"enhanced_detection_{int(time.time())}"
                    tokens_found = await self.run_detection_cycle(scan_id=scan_id)
                    
                    # Log cycle results
                    cycle_duration = time.time() - cycle_start
                    self.logger.info(f"✅ Cycle #{cycle_count} completed in {cycle_duration:.1f}s - {len(tokens_found)} tokens found")
                    
                    # Show position tracking stats if enabled
                    if self.position_tracking_enabled:
                        stats = self.position_tracker.get_statistics()
                        self.logger.info(f"📊 Position tracking stats: {stats['active_positions']} active, {stats['total_users']} users")
                
                except Exception as e:
                    self.logger.error(f"❌ Error in detection cycle #{cycle_count}: {e}")
                
                # Wait for next cycle
                sleep_time = check_interval_minutes * 60
                self.logger.info(f"💤 Sleeping for {sleep_time} seconds until next cycle...")
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self.logger.info("⌨️ Daemon stopped by user")
        except Exception as e:
            self.logger.error(f"💥 Fatal error in daemon: {e}")
        finally:
            # Cleanup
            if hasattr(self, 'birdeye_api'):
                await self.birdeye_api.close()
            self.logger.info("👋 Enhanced detector daemon shutdown complete")

async def main():
    """Main entry point for enhanced high conviction detector"""
    try:
        import argparse
        
        parser = argparse.ArgumentParser(description='Enhanced High Conviction Token Detector with Position Tracking')
        parser.add_argument('--config', '-c', default='config/config.yaml',
                          help='Path to configuration file')
        parser.add_argument('--daemon', '-d', action='store_true',
                          help='Run as daemon (continuous monitoring)')
        parser.add_argument('--interval', '-i', type=int, default=10,
                          help='Check interval in minutes for daemon mode')
        parser.add_argument('--max-tokens', '-m', type=int, default=50,
                          help='Maximum tokens to analyze per cycle')
        parser.add_argument('--single-run', '-s', action='store_true',
                          help='Run single detection cycle and exit')
        
        args = parser.parse_args()
        
        # Initialize enhanced detector
        detector = EnhancedHighConvictionDetector(args.config)
        
        if args.daemon:
            # Run as daemon
            await detector.start_daemon(args.interval)
        elif args.single_run:
            # Single detection cycle
            scan_id = f"single_run_{int(time.time())}"
            tokens = await detector.run_detection_cycle(args.max_tokens, scan_id)
            print(f"✅ Found {len(tokens)} high conviction tokens")
            for token in tokens:
                print(f"  🎯 {token.get('symbol', 'UNKNOWN')} - Score: {token.get('conviction_score', 0):.1f}")
        else:
            print("❌ Please specify --daemon or --single-run mode")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⌨️ Interrupted by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 