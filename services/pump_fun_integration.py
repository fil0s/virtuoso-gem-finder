# Pump.fun Integration Layer for Stage 0 Detection
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

class PumpFunStage0Integration:
    """Integration layer for pump.fun Stage 0 tokens with enhanced bonding curve analysis"""
    
    def __init__(self, early_detector=None, high_conviction_detector=None):
        self.logger = logging.getLogger('PumpFunStage0Integration')
        self.early_detector = early_detector
        self.high_conviction_detector = high_conviction_detector
        
        # Stage 0 priority queue
        self.stage0_priority_queue = []
        
        # Performance tracking
        self.stage0_tokens_processed = 0
        self.graduation_signals_sent = 0
        
        # Graduation monitoring
        self.graduation_watch_list = []
        
        # NEW: Bonding curve analysis
        self.bonding_curve_tracker = {}  # Track market cap progression
        self.GRADUATION_THRESHOLD = 69000  # $69K graduation threshold
        self.SUPPLY_BURN_AMOUNT = 12000    # $12K supply burn at graduation
        
        self.logger.info("🚀 Stage 0 pump.fun integration initialized with bonding curve analysis")
    
    # NEW: Bonding Curve Analysis Methods
    def track_bonding_curve_progression(self, token_address: str, market_cap: float):
        """Track token progression up the bonding curve"""
        timestamp = time.time()
        
        if token_address not in self.bonding_curve_tracker:
            self.bonding_curve_tracker[token_address] = []
        
        progression_data = {
            'timestamp': timestamp,
            'market_cap': market_cap,
            'graduation_progress_pct': (market_cap / self.GRADUATION_THRESHOLD) * 100
        }
        
        self.bonding_curve_tracker[token_address].append(progression_data)
        
        # Keep only last 50 data points per token
        if len(self.bonding_curve_tracker[token_address]) > 50:
            self.bonding_curve_tracker[token_address] = self.bonding_curve_tracker[token_address][-50:]
    
    def calculate_bonding_curve_velocity(self, token_address: str) -> Dict:
        """Calculate bonding curve velocity (market cap growth per hour)"""
        if token_address not in self.bonding_curve_tracker:
            return {'velocity_per_hour': 0, 'confidence': 0, 'prediction': 'NO_DATA'}
        
        progression_data = self.bonding_curve_tracker[token_address]
        if len(progression_data) < 2:
            return {'velocity_per_hour': 0, 'confidence': 0, 'prediction': 'INSUFFICIENT_DATA'}
        
        # Calculate velocity over last hour of data
        recent_data = [p for p in progression_data if time.time() - p['timestamp'] <= 3600]
        if len(recent_data) < 2:
            recent_data = progression_data[-2:]  # Use last 2 points
        
        time_span_hours = (recent_data[-1]['timestamp'] - recent_data[0]['timestamp']) / 3600
        if time_span_hours == 0:
            time_span_hours = 0.1  # Prevent division by zero
        
        market_cap_change = recent_data[-1]['market_cap'] - recent_data[0]['market_cap']
        velocity_per_hour = market_cap_change / time_span_hours
        
        # Predict graduation timing
        current_market_cap = progression_data[-1]['market_cap']
        remaining_to_graduation = self.GRADUATION_THRESHOLD - current_market_cap
        
        if velocity_per_hour > 0:
            hours_to_graduation = remaining_to_graduation / velocity_per_hour
            if hours_to_graduation <= 6:
                prediction = 'GRADUATION_IMMINENT'
            elif hours_to_graduation <= 24:
                prediction = 'GRADUATION_LIKELY'
            elif hours_to_graduation <= 72:
                prediction = 'GRADUATION_POSSIBLE'
            else:
                prediction = 'GRADUATION_DISTANT'
        else:
            prediction = 'STALLED_OR_DECLINING'
        
        confidence = min(len(progression_data) / 10, 1.0)  # More data = higher confidence
        
        return {
            'velocity_per_hour': velocity_per_hour,
            'hours_to_graduation': hours_to_graduation if velocity_per_hour > 0 else float('inf'),
            'confidence': confidence,
            'prediction': prediction,
            'current_market_cap': current_market_cap,
            'graduation_progress_pct': (current_market_cap / self.GRADUATION_THRESHOLD) * 100
        }
    
    def get_bonding_curve_stage_analysis(self, market_cap: float) -> Dict:
        """Analyze what stage of bonding curve and optimal strategy"""
        graduation_progress = (market_cap / self.GRADUATION_THRESHOLD) * 100
        
        if market_cap < 1000:
            return {
                'stage': 'STAGE_0_ULTRA_EARLY',
                'profit_potential': '10-50x',
                'risk_level': 'EXTREME',
                'wallet_recommendation': 'discovery_scout',
                'position_size_pct': 2.0,
                'strategy': 'IMMEDIATE_ENTRY'
            }
        elif market_cap < 5000:
            return {
                'stage': 'STAGE_0_EARLY_MOMENTUM',
                'profit_potential': '5-25x',
                'risk_level': 'VERY_HIGH',
                'wallet_recommendation': 'discovery_scout',
                'position_size_pct': 1.5,
                'strategy': 'MOMENTUM_ENTRY'
            }
        elif market_cap < 15000:
            return {
                'stage': 'STAGE_1_CONFIRMED_GROWTH',
                'profit_potential': '3-15x',
                'risk_level': 'HIGH',
                'wallet_recommendation': 'conviction_core',
                'position_size_pct': 4.0,
                'strategy': 'CONVICTION_ACCUMULATION'
            }
        elif market_cap < 35000:
            return {
                'stage': 'STAGE_2_EXPANSION',
                'profit_potential': '2-8x',
                'risk_level': 'MEDIUM',
                'wallet_recommendation': 'conviction_core',
                'position_size_pct': 3.0,
                'strategy': 'GROWTH_PARTICIPATION'
            }
        elif market_cap < 55000:
            return {
                'stage': 'STAGE_2_LATE_GROWTH',
                'profit_potential': '1.5-4x',
                'risk_level': 'MEDIUM',
                'wallet_recommendation': 'moonshot_hunter',
                'position_size_pct': 5.0,
                'strategy': 'PRE_GRADUATION_POSITIONING'
            }
        elif market_cap < 65000:
            return {
                'stage': 'STAGE_3_PRE_GRADUATION',
                'profit_potential': '1.2-2x',
                'risk_level': 'LOW',
                'wallet_recommendation': 'moonshot_hunter',
                'position_size_pct': 3.0,
                'strategy': 'GRADUATION_PLAY'
            }
        else:
            return {
                'stage': 'STAGE_3_GRADUATION_IMMINENT',
                'profit_potential': '1.1-1.5x',
                'risk_level': 'VERY_LOW',
                'wallet_recommendation': 'exit_signal',
                'position_size_pct': 0,
                'strategy': 'IMMEDIATE_EXIT'
            }
    
    async def handle_pump_fun_launch(self, event_data: Dict):
        """Handle new pump.fun launch with bonding curve analysis"""
        try:
            token_address = event_data['token_address']
            market_cap = event_data.get('market_cap', 0)
            
            # Track bonding curve progression from launch
            self.track_bonding_curve_progression(token_address, market_cap)
            
            # Get bonding curve stage analysis
            stage_analysis = self.get_bonding_curve_stage_analysis(market_cap)
            
            # Enhanced Stage 0 token with bonding curve data
            enhanced_stage0_token = {
                'token_address': token_address,
                'launch_timestamp': event_data.get('timestamp', time.time()),
                'market_cap': market_cap,
                'bonding_curve_stage': stage_analysis['stage'],
                'profit_potential': stage_analysis['profit_potential'],
                'optimal_wallet': stage_analysis['wallet_recommendation'],
                'recommended_position_pct': stage_analysis['position_size_pct'],
                'entry_strategy': stage_analysis['strategy'],
                'graduation_progress_pct': (market_cap / self.GRADUATION_THRESHOLD) * 100,
                **event_data
            }
            
            # Add to priority queue (newest first for bonding curve advantage)
            self.stage0_priority_queue.insert(0, enhanced_stage0_token)
            
            # Add to graduation watch list for monitoring
            self.graduation_watch_list.append({
                'token_address': token_address,
                'added_timestamp': time.time(),
                'initial_market_cap': market_cap
            })
            
            self.stage0_tokens_processed += 1
            
            self.logger.info(f"🔥 STAGE 0 PRIORITY: {token_address[:8]}... added to front of queue")
            self.logger.info(f"   💰 Market Cap: ${market_cap:,.0f} ({stage_analysis['stage']})")
            self.logger.info(f"   🎯 Strategy: {stage_analysis['strategy']} via {stage_analysis['wallet_recommendation']}")
            
            # Immediate processing for ultra-early launches
            if market_cap < 1000:  # Ultra-early launches get immediate processing
                await self._process_stage0_immediate(enhanced_stage0_token)
                
        except Exception as e:
            self.logger.error(f"❌ Error handling pump.fun launch: {e}")
    
    async def handle_graduation_signal(self, event_data: Dict):
        """Handle graduation to Raydium - PROFIT TAKING SIGNAL"""
        try:
            token_address = event_data['token_address']
            
            # Trigger exit signals
            exit_signal = {
                'token_address': token_address,
                'action': 'TAKE_PROFITS',
                'reason': 'pump_fun_graduation_to_raydium',
                'urgency': 'HIGH',
                'stage': 'graduation_exit',
                'recommended_exit_percentage': 80,  # Take 80% profits
                'graduation_source': event_data.get('graduation_source', 'pump_fun_graduation'),
                'tracking_duration_hours': event_data.get('tracking_duration_hours', 0),
                'market_cap': event_data.get('market_cap', 0),
                'timestamp': event_data.get('timestamp', time.time()),
                **event_data
            }
            
            # Send to high conviction detector for exit processing
            if self.high_conviction_detector and hasattr(self.high_conviction_detector, '_handle_exit_signal'):
                await self.high_conviction_detector._handle_exit_signal(exit_signal)
            
            self.graduation_signals_sent += 1
            
            self.logger.info(f"🎓 EXIT SIGNAL: {token_address[:8]}... graduation detected - TAKE PROFITS!")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling graduation signal: {e}")
    
    async def _process_stage0_immediate(self, stage0_token: Dict):
        """Immediate processing for Stage 0 tokens"""
        try:
            # Enhanced scoring for pump.fun launches
            enhanced_analysis = await self._calculate_stage0_scoring(stage0_token)
            
            # Feed into existing pipeline with enhanced data
            if enhanced_analysis['recommended_action'] == 'IMMEDIATE_ANALYSIS':
                await self._feed_to_existing_pipeline(enhanced_analysis)
            
        except Exception as e:
            self.logger.error(f"❌ Error in Stage 0 immediate processing: {e}")
    
    async def _calculate_stage0_scoring(self, stage0_token: Dict) -> Dict:
        """Calculate enhanced scoring for Stage 0 pump.fun tokens"""
        
        base_score = 75  # High base score for pump.fun launches
        
        # Stage 0 bonuses
        bonuses = {
            'pump_fun_launch_bonus': 25,    # Maximum early detection
            'stage0_priority_bonus': 15,    # Priority processing
            'ultra_early_bonus': 10,        # 0-minute age bonus
        }
        
        total_score = base_score + sum(bonuses.values())
        
        # Determine processing recommendation
        if total_score >= 100:
            recommended_action = 'IMMEDIATE_ANALYSIS'
        elif total_score >= 85:
            recommended_action = 'HIGH_PRIORITY_ANALYSIS'
        else:
            recommended_action = 'STANDARD_ANALYSIS'
        
        return {
            'token_address': stage0_token['token_address'],
            'stage0_score': total_score,
            'bonuses_applied': bonuses,
            'recommended_action': recommended_action,
            'stage': 'stage_0_enhanced',
            'processing_priority': 'ULTRA_HIGH',
            **stage0_token
        }
    
    async def _feed_to_existing_pipeline(self, enhanced_token: Dict):
        """Feed enhanced Stage 0 token to existing detection pipeline"""
        try:
            # Create format compatible with existing system
            pipeline_token = {
                'address': enhanced_token['token_address'],
                'symbol': enhanced_token.get('symbol', 'UNKNOWN'),
                'source': 'pump_fun_stage0',
                'score': enhanced_token['stage0_score'],
                'stage0_enhanced': True,
                'pump_fun_origin': True,
                'priority': 'ULTRA_HIGH',
                **enhanced_token
            }
            
            # Add to existing discovery tokens (if method exists)
            if (self.early_detector and 
                hasattr(self.early_detector, '_last_discovery_tokens')):
                
                # Insert at beginning for priority processing
                if not hasattr(self.early_detector, '_last_discovery_tokens'):
                    self.early_detector._last_discovery_tokens = []
                
                self.early_detector._last_discovery_tokens.insert(0, pipeline_token)
                
                self.logger.info(f"🔗 Stage 0 token {pipeline_token['address'][:8]}... fed to existing pipeline")
            
        except Exception as e:
            self.logger.error(f"❌ Error feeding to existing pipeline: {e}")
    
    def get_stage0_priority_queue(self) -> List[Dict]:
        """🚀 UPDATED: Get REAL Stage 0 priority queue from live pump.fun API"""
        return asyncio.run(self._fetch_live_stage0_tokens())
    
    async def _fetch_live_stage0_tokens(self) -> List[Dict]:
        """Fetch live Stage 0 tokens from pump.fun API"""
        try:
            # Import and use real API client
            from services.pump_fun_api_client import PumpFunAPIClient
            
            if not hasattr(self, '_api_client'):
                self._api_client = PumpFunAPIClient()
                self.logger.info("🔥 Initialized REAL pump.fun API client")
            
            # Fetch latest tokens from real API
            latest_tokens = await self._api_client.get_latest_tokens(limit=25)
            
            if not latest_tokens:
                self.logger.info("🔍 No new tokens from pump.fun API this cycle")
                return self.stage0_priority_queue.copy()  # Return cached if API fails
            
            # Process tokens for Stage 0 queue
            live_stage0_tokens = []
            
            for token in latest_tokens:
                try:
                    age_minutes = token.get('estimated_age_minutes', 9999)
                    market_cap = token.get('market_cap', 0)
                    
                    # Stage 0 criteria: Recent and not too large
                    if (age_minutes <= 180 and  # Last 3 hours
                        market_cap > 100 and     # Some activity
                        market_cap < 200000):    # Not graduated
                        
                        # Convert API token to integration format
                        stage0_token = {
                            'token_address': token.get('token_address', ''),
                            'symbol': token.get('symbol', 'UNKNOWN'),
                            'name': token.get('name', 'Pump.fun Token'),
                            'market_cap': market_cap,
                            'estimated_age_minutes': age_minutes,
                            'pump_fun_stage': token.get('pump_fun_stage', 'STAGE_0'),
                            'bonding_curve_stage': token.get('bonding_curve_stage', ''),
                            'graduation_progress_pct': token.get('graduation_progress_pct', 0),
                            'ultra_early_bonus_eligible': age_minutes <= 10,
                            'source': 'pump_fun_live_api',
                            'api_fetch_timestamp': time.time(),
                            **token  # Include all original data
                        }
                        
                        live_stage0_tokens.append(stage0_token)
                        
                        # Log ultra-early detections
                        if age_minutes <= 10:
                            self.logger.info(f"🚨 LIVE ULTRA-EARLY: {token['symbol']} - {age_minutes:.1f}min old!")
                
                except Exception as e:
                    self.logger.debug(f"Error processing live token: {e}")
                    continue
            
            # Update internal queue with live data
            self.stage0_priority_queue = live_stage0_tokens
            self.stage0_tokens_processed += len(live_stage0_tokens)
            
            self.logger.info(f"🔥 LIVE API: Found {len(live_stage0_tokens)} real Stage 0 tokens")
            
            return live_stage0_tokens
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching live Stage 0 tokens: {e}")
            return self.stage0_priority_queue.copy()  # Return cached on error
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration performance statistics"""
        return {
            'stage0_tokens_processed': self.stage0_tokens_processed,
            'graduation_signals_sent': self.graduation_signals_sent,
            'current_priority_queue_size': len(self.stage0_priority_queue),
            'graduation_watch_list_size': len(self.graduation_watch_list),
            'integration_status': 'ACTIVE',
            'total_calls': self.stage0_tokens_processed + self.graduation_signals_sent
        }

    async def monitor_graduation_progression(self):
        """Continuously monitor tokens for graduation progression"""
        while True:
            try:
                for watch_item in self.graduation_watch_list.copy():
                    token_address = watch_item['token_address']
                    
                    # Get current market cap (would integrate with your price tracking)
                    # For now, simulate progression
                    current_market_cap = watch_item.get('current_market_cap', watch_item['initial_market_cap'])
                    
                    # Track progression
                    self.track_bonding_curve_progression(token_address, current_market_cap)
                    
                    # Get velocity analysis
                    velocity_analysis = self.calculate_bonding_curve_velocity(token_address)
                    
                    # Generate graduation alerts
                    if velocity_analysis['prediction'] == 'GRADUATION_IMMINENT':
                        await self.handle_graduation_signal({
                            'token_address': token_address,
                            'type': 'graduation_imminent',
                            'market_cap': current_market_cap,
                            'velocity_per_hour': velocity_analysis['velocity_per_hour'],
                            'hours_to_graduation': velocity_analysis['hours_to_graduation'],
                            'urgency': 'CRITICAL'
                        })
                    elif velocity_analysis['prediction'] == 'GRADUATION_LIKELY':
                        await self.handle_graduation_signal({
                            'token_address': token_address,
                            'type': 'graduation_warning',
                            'market_cap': current_market_cap,
                            'velocity_per_hour': velocity_analysis['velocity_per_hour'],
                            'hours_to_graduation': velocity_analysis['hours_to_graduation'],
                            'urgency': 'HIGH'
                        })
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"❌ Error monitoring graduation progression: {e}")
                await asyncio.sleep(600)  # Wait longer on error

# Discovery Scout Wallet Integration
class DiscoveryScoutPumpFunHandler:
    """Handles pump.fun tokens for the Discovery Scout automated wallet"""
    
    def __init__(self, discovery_wallet=None):
        self.logger = logging.getLogger('DiscoveryScoutPumpFun')
        self.discovery_wallet = discovery_wallet
        
        # Auto-trading parameters for pump.fun tokens
        self.pump_fun_position_size = 0.015  # 1.5% per pump.fun token
        self.pump_fun_auto_take_profit = 3.0  # 3x profit target
        self.pump_fun_stop_loss = -0.20  # 20% stop loss
        
        # Graduation monitoring
        self.active_pump_fun_positions = {}
        
        self.logger.info("🤖 Discovery Scout pump.fun handler initialized")
    
    async def handle_stage0_auto_trade(self, stage0_token: Dict):
        """Handle automated trading for Stage 0 pump.fun tokens"""
        try:
            token_address = stage0_token['token_address']
            
            # Automated trading criteria for pump.fun tokens
            auto_trade_score = await self._calculate_auto_trade_score(stage0_token)
            
            if auto_trade_score >= 85:  # High confidence threshold
                trade_amount = await self._calculate_pump_fun_position_size()
                
                # Execute automated trade
                success = await self._execute_pump_fun_trade(
                    token_address, 
                    trade_amount, 
                    stage0_token
                )
                
                if success:
                    # Set up automated monitoring
                    await self._setup_pump_fun_monitoring(token_address, stage0_token)
                    
                    self.logger.info(f"🤖 AUTO-TRADED: {token_address[:8]}... (${trade_amount})")
            
        except Exception as e:
            self.logger.error(f"❌ Error in Stage 0 auto-trade: {e}")
    
    async def _calculate_auto_trade_score(self, stage0_token: Dict) -> float:
        """Calculate auto-trading confidence score for pump.fun tokens"""
        
        base_score = 70  # Base score for pump.fun launches
        
        # Auto-trading bonuses
        bonuses = 0
        
        # Ultra-early bonus (0-5 minutes)
        if stage0_token.get('estimated_age_minutes', 0) <= 5:
            bonuses += 20
        
        # High priority bonus
        if stage0_token.get('priority') == 'ULTRA_HIGH':
            bonuses += 10
        
        # Stage 0 confirmed bonus
        if stage0_token.get('stage') == 'stage_0':
            bonuses += 15
        
        return base_score + bonuses
    
    async def _execute_pump_fun_trade(self, token_address: str, amount: float, token_data: Dict) -> bool:
        """Execute automated pump.fun trade"""
        try:
            # This would integrate with your wallet coordination system
            self.logger.info(f"🔥 Executing pump.fun auto-trade: {token_address[:8]}... ${amount}")
            
            # Add to active positions
            self.active_pump_fun_positions[token_address] = {
                'entry_time': time.time(),
                'entry_amount': amount,
                'token_data': token_data,
                'profit_target': self.pump_fun_auto_take_profit,
                'stop_loss': self.pump_fun_stop_loss
            }
            
            return True  # Placeholder for actual trading logic
            
        except Exception as e:
            self.logger.error(f"❌ Error executing pump.fun trade: {e}")
            return False
    
    async def monitor_graduation_exits(self):
        """Monitor pump.fun positions for graduation exit signals"""
        while True:
            try:
                for token_address, position in list(self.active_pump_fun_positions.items()):
                    # Check if token has graduated (would come from graduation monitor)
                    # This would trigger automatic exit
                    pass
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Error monitoring graduation exits: {e}")
                await asyncio.sleep(60) 