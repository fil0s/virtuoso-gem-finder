import asyncio
import json
import logging
import time
import websockets
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.rpc.config import RpcTransactionLogsFilterMentions
from solana.rpc.websocket_api import connect
import struct
import aiohttp
import os

class PumpFunMonitor:
    """
    Real-time monitor for pump.fun token launches and graduation events.
    Integrates with existing Stage 2 detection system for ultra-early discovery.
    """
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com", 
                 ws_url: str = "wss://api.mainnet-beta.solana.com/"):
        self.logger = logging.getLogger('PumpFunMonitor')
        self.client = Client(rpc_url)
        self.ws_url = ws_url
        
        # Pump.fun program addresses
        self.PUMP_FUN_PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
        self.RAYDIUM_PROGRAM = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
        
        # Graduation threshold (approximately $69K market cap)
        self.GRADUATION_THRESHOLD = 69000
        
        # Event callbacks
        self.on_new_token: Optional[Callable] = None
        self.on_graduation: Optional[Callable] = None
        self.on_significant_trade: Optional[Callable] = None
        
        # Token tracking
        self.tracked_tokens: Dict[str, Dict] = {}
        self.graduation_candidates: Dict[str, Dict] = {}
        
        # Performance tracking
        self.tokens_detected = 0
        self.graduations_detected = 0
        self.false_positives = 0
        
        # Production-ready connection management
        self.connection_active = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # seconds
        
        # Live API endpoints for pump.fun data
        self.api_endpoints = {
            'trending': 'https://client-api-v2.pump.fun/coins/by-market-cap/',
            'token_data': 'https://api.pump.fun/coins/',
            'trades': 'https://pumpportal.fun/api/trades-by-token/'
        }
        
        self.logger.info("🚀 Pump.fun monitor initialized with live connections")
    
    async def start_monitoring(self):
        """Start production-ready pump.fun monitoring with intelligent fallback"""
        self.logger.info("🔥 Starting pump.fun real-time monitoring (Production Mode)...")
        
        # PRODUCTION STRATEGY: Prioritize stable API polling, optional WebSocket
        monitoring_tasks = [
            # PRIMARY: Stable API polling (always works)
            self._monitor_with_recovery(self._poll_pump_fun_api, "api_polling"),
        ]
        
        # OPTIONAL: Add WebSocket monitoring only if explicitly enabled
        enable_websocket = os.getenv('ENABLE_PUMP_FUN_WEBSOCKET', 'false').lower() == 'true'
        
        if enable_websocket:
            self.logger.info("🌐 WebSocket monitoring enabled (experimental)")
            monitoring_tasks.extend([
                self._monitor_with_recovery(self._monitor_new_tokens, "new_tokens"),
                self._monitor_with_recovery(self._monitor_graduations, "graduations"),
            ])
        else:
            self.logger.info("📡 API-only monitoring mode (production stable)")
        
        await asyncio.gather(*monitoring_tasks, return_exceptions=True)
    
    async def _monitor_with_recovery(self, monitor_func, monitor_name: str):
        """Wrapper for monitoring functions with automatic recovery"""
        while True:
            try:
                self.logger.info(f"🔄 Starting {monitor_name} monitoring...")
                await monitor_func()
            except Exception as e:
                self.logger.error(f"❌ Error in {monitor_name} monitoring: {e}")
                self.reconnect_attempts += 1
                
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    self.logger.error(f"💥 Max reconnection attempts reached for {monitor_name}")
                    break
                    
                wait_time = min(self.reconnect_delay * (2 ** self.reconnect_attempts), 300)
                self.logger.info(f"🔄 Reconnecting {monitor_name} in {wait_time}s...")
                await asyncio.sleep(wait_time)
    
    async def _poll_pump_fun_api(self):
        """Poll pump.fun API endpoints for new token data"""
        self.logger.info("📡 Starting pump.fun API polling...")
        
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    # Poll trending tokens
                    await self._poll_trending_tokens(session)
                    
                    # Poll for new tokens
                    await self._poll_new_tokens(session)
                    
                    # Wait before next poll (don't overwhelm API)
                    await asyncio.sleep(30)  # Poll every 30 seconds
                    
                except Exception as e:
                    self.logger.error(f"❌ API polling error: {e}")
                    await asyncio.sleep(60)  # Wait longer on error
    
    async def _poll_trending_tokens(self, session: aiohttp.ClientSession):
        """Poll pump.fun trending tokens API"""
        try:
            async with session.get(self.api_endpoints['trending'], timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process trending tokens for Stage 0 candidates
                    for token in data.get('data', []):
                        if self._is_stage0_candidate(token):
                            await self._process_stage0_token(token)
                            
        except Exception as e:
            self.logger.debug(f"Trending API poll error: {e}")
    
    async def _poll_new_tokens(self, session: aiohttp.ClientSession):
        """Poll for newly created tokens"""
        try:
            # This would connect to pump.fun's new token feed
            # For now, we'll use the trending endpoint and filter for very new tokens
            async with session.get(self.api_endpoints['trending'] + "?sort=created&limit=50", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for token in data.get('data', []):
                        # Check if token is very new (Stage 0)
                        if self._is_ultra_early_stage0(token):
                            await self._handle_new_token_detection(token)
                            
        except Exception as e:
            self.logger.debug(f"New tokens API poll error: {e}")
    
    def _is_stage0_candidate(self, token_data: Dict) -> bool:
        """Check if token qualifies as Stage 0 candidate"""
        market_cap = token_data.get('market_cap', 0)
        
        # Stage 0: Under $10K market cap
        if market_cap < 10000:
            return True
            
        return False
    
    def _is_ultra_early_stage0(self, token_data: Dict) -> bool:
        """Check if token is ultra-early Stage 0 (just launched)"""
        market_cap = token_data.get('market_cap', 0)
        created_timestamp = token_data.get('created_timestamp', 0)
        
        # Ultra-early: Under $5K market cap and created within last hour
        current_time = time.time()
        age_hours = (current_time - created_timestamp) / 3600 if created_timestamp else 999
        
        return market_cap < 5000 and age_hours < 1
    
    async def _handle_new_token_detection(self, token_data: Dict):
        """Handle detection of new Stage 0 token"""
        token_address = token_data.get('mint', token_data.get('address', ''))
        
        if token_address and token_address not in self.tracked_tokens:
            self.tokens_detected += 1
            
            # Create Stage 0 token event
            stage0_event = {
                'type': 'pump_fun_stage0_launch',
                'token_address': token_address,
                'symbol': token_data.get('symbol', 'UNKNOWN'),
                'name': token_data.get('name', 'Unknown Token'),
                'market_cap': token_data.get('market_cap', 0),
                'creator': token_data.get('creator', ''),
                'timestamp': time.time(),
                'stage': 'stage_0_ultra_early',
                'priority': 'ULTRA_HIGH',
                'estimated_age_minutes': 0,
                'pump_fun_origin': True,
                'bonding_curve_stage': 'STAGE_0_LAUNCH'
            }
            
            # Track this token
            self.tracked_tokens[token_address] = stage0_event
            
            self.logger.info(f"🔥 STAGE 0 DETECTED: {token_data.get('symbol', 'UNKNOWN')} (${token_data.get('market_cap', 0):,})")
            
            # Call callback if set
            if self.on_new_token:
                await self.on_new_token(stage0_event)
    
    async def _monitor_new_tokens(self):
        """Monitor pump.fun program for new token creates with WebSocket"""
        try:
            async with connect(self.ws_url) as websocket:
                # Subscribe to pump.fun program logs
                await websocket.logs_subscribe(
                    RpcTransactionLogsFilterMentions(self.PUMP_FUN_PROGRAM),
                    commitment="confirmed"
                )
                
                self.logger.info("🎯 WebSocket monitoring pump.fun program for new token launches...")
                self.connection_active = True
                self.reconnect_attempts = 0  # Reset on successful connection
                
                async for message in websocket:
                    try:
                        # Robust message type checking
                        if isinstance(message, dict) and message.get('method') == 'logsNotification':
                            await self._process_token_creation(message)
                        elif not isinstance(message, dict):
                            # Skip non-dict messages (lists, strings, etc.)
                            continue
                    except Exception as e:
                        self.logger.debug(f"WebSocket message processing error: {e}")
                        
        except Exception as e:
            self.connection_active = False
            self.logger.error(f"❌ Error in new token monitoring: {e}")
            raise  # Let the recovery wrapper handle this
    
    async def _monitor_graduations(self):
        """Monitor for tokens graduating from pump.fun to Raydium with WebSocket"""
        try:
            async with connect(self.ws_url) as websocket:
                # Subscribe to Raydium program for new pools
                await websocket.logs_subscribe(
                    RpcTransactionLogsFilterMentions(self.RAYDIUM_PROGRAM),
                    commitment="confirmed"
                )
                
                self.logger.info("🎓 WebSocket monitoring Raydium program for pump.fun graduations...")
                
                async for message in websocket:
                    try:
                        # Robust message type checking
                        if isinstance(message, dict) and message.get('method') == 'logsNotification':
                            await self._process_graduation_event(message)
                        elif not isinstance(message, dict):
                            # Skip non-dict messages silently
                            continue
                    except Exception as e:
                        self.logger.debug(f"WebSocket graduation processing error: {e}")
                        
        except Exception as e:
            self.logger.error(f"❌ Error in graduation monitoring: {e}")
            raise
    
    async def _process_token_creation(self, message):
        """Process new token creation events with robust error handling"""
        try:
            # Handle unexpected message formats
            if not isinstance(message, dict):
                self.logger.debug(f"Unexpected message format: {type(message)}, skipping")
                return
            
            # Safely extract nested data with fallbacks
            params = message.get('params')
            if not params or not isinstance(params, dict):
                return
                
            result = params.get('result')
            if not result or not isinstance(result, dict):
                return
                
            value = result.get('value')
            if not value or not isinstance(value, dict):
                return
            
            logs = value.get('logs', [])
            signature = value.get('signature', '')
            
            if not logs or not signature:
                return
            
            # Look for pump.fun token creation patterns
            for log in logs:
                if isinstance(log, str) and ('Program log: Created token:' in log or 'initialize' in log.lower()):
                    # Extract token address from transaction
                    token_data = await self._extract_token_data(signature)
                    
                    if token_data:
                        await self._handle_new_token(token_data)
                        
        except Exception as e:
            self.logger.debug(f"Token creation processing error: {e}")
    
    async def _process_graduation_event(self, message):
        """Process token graduation events with robust error handling"""
        try:
            # Handle unexpected message formats
            if not isinstance(message, dict):
                self.logger.debug(f"Unexpected message format: {type(message)}, skipping")
                return
            
            # Safely extract nested data with fallbacks
            params = message.get('params')
            if not params or not isinstance(params, dict):
                return
                
            result = params.get('result')
            if not result or not isinstance(result, dict):
                return
                
            value = result.get('value')
            if not value or not isinstance(value, dict):
                return
            
            logs = value.get('logs', [])
            signature = value.get('signature', '')
            
            if not logs or not signature:
                return
            
            # Look for Raydium pool creation patterns
            for log in logs:
                if isinstance(log, str) and ('initialize' in log.lower() or 'pool' in log.lower()):
                    graduation_data = await self._extract_graduation_data(signature)
                    
                    if graduation_data:
                        await self._handle_graduation(graduation_data)
                        
        except Exception as e:
            self.logger.debug(f"Graduation processing error: {e}")
    
    async def _extract_token_data(self, signature: str) -> Optional[Dict]:
        """Extract token data from transaction signature"""
        try:
            # Get transaction details
            transaction = self.client.get_transaction(signature, max_supported_transaction_version=0)
            
            if not transaction or not transaction.value:
                return None
            
            # Parse transaction for token creation details
            # This would involve parsing the transaction accounts and data
            # For now, return basic structure
            
            return {
                'signature': signature,
                'timestamp': time.time(),
                'detected_at': datetime.now().isoformat(),
                'source': 'pump_fun_monitor',
                'stage': 'stage_0_launch'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting token data: {e}")
            return None
    
    async def _extract_graduation_data(self, signature: str) -> Optional[Dict]:
        """Extract graduation data from Raydium transaction"""
        try:
            transaction = self.client.get_transaction(signature, max_supported_transaction_version=0)
            
            if not transaction or not transaction.value:
                return None
            
            # Parse for token address that graduated
            # Implementation would parse Raydium pool creation transaction
            
            return {
                'signature': signature,
                'timestamp': time.time(),
                'graduated_at': datetime.now().isoformat(),
                'source': 'raydium_monitor'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting graduation data: {e}")
            return None
    
    async def _handle_new_token(self, token_data: Dict):
        """Handle new token detection"""
        token_address = token_data.get('address')
        if not token_address:
            return
        
        # Add to tracking
        self.tracked_tokens[token_address] = {
            **token_data,
            'tracked_since': time.time(),
            'stage': 'stage_0_launch'
        }
        
        self.tokens_detected += 1
        
        self.logger.info(f"🚀 NEW TOKEN DETECTED: {token_address[:8]}... (Total: {self.tokens_detected})")
        
        # Trigger callback for integration with existing system
        if self.on_new_token:
            await self.on_new_token({
                'type': 'new_token_launch',
                'token_address': token_address,
                'detection_source': 'pump_fun_launch',
                'stage': 'stage_0',
                'priority': 'ultra_high',  # Highest priority for earliest detection
                **token_data
            })
    
    async def _handle_graduation(self, graduation_data: Dict):
        """Handle token graduation to Raydium"""
        token_address = graduation_data.get('token_address')
        if not token_address:
            return
        
        # Remove from tracking (graduated)
        if token_address in self.tracked_tokens:
            token_data = self.tracked_tokens.pop(token_address)
            
            # Calculate tracking duration
            tracking_duration = time.time() - token_data.get('tracked_since', time.time())
            
            self.graduations_detected += 1
            
            self.logger.info(f"🎓 GRADUATION DETECTED: {token_address[:8]}... after {tracking_duration/3600:.1f}h tracking")
            
            # Trigger callback for exit signals
            if self.on_graduation:
                await self.on_graduation({
                    'type': 'graduation_confirmed',
                    'token_address': token_address,
                    'graduation_source': 'raydium_pool_creation',
                    'tracking_duration_hours': tracking_duration / 3600,
                    'stage': 'graduation_exit_signal',
                    'action_recommended': 'TAKE_PROFITS',
                    **graduation_data
                })
    
    async def _handle_significant_trade(self, token_address: str, token_data: Dict, volume: float):
        """Handle significant trading activity"""
        self.logger.info(f"📈 SIGNIFICANT ACTIVITY: {token_address[:8]}... volume spike to ${volume:,.0f}")
        
        if self.on_significant_trade:
            await self.on_significant_trade({
                'type': 'volume_spike',
                'token_address': token_address,
                'new_volume': volume,
                'previous_volume': token_data.get('last_volume', 0),
                'spike_multiplier': volume / max(token_data.get('last_volume', 1), 1),
                'stage': 'momentum_building',
                **token_data
            })
    
    async def _get_token_volume(self, token_address: str) -> float:
        """Get current 24h volume for token (placeholder)"""
        # This would integrate with your existing API systems
        return 0.0
    
    async def _get_token_market_cap(self, token_address: str) -> float:
        """Get current market cap for token (placeholder)"""
        # This would integrate with your existing API systems
        return 0.0
    
    def set_callbacks(self, on_new_token: Callable = None, 
                     on_graduation: Callable = None,
                     on_significant_trade: Callable = None):
        """Set event callbacks for integration"""
        self.on_new_token = on_new_token
        self.on_graduation = on_graduation
        self.on_significant_trade = on_significant_trade
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring performance statistics"""
        return {
            'tokens_detected': self.tokens_detected,
            'graduations_detected': self.graduations_detected,
            'currently_tracking': len(self.tracked_tokens),
            'graduation_candidates': len(self.graduation_candidates),
            'detection_rate': self.tokens_detected / max(time.time() - getattr(self, 'start_time', time.time()), 1),
            'false_positive_rate': self.false_positives / max(self.tokens_detected, 1)
        }

# Integration helper for existing system
class PumpFunIntegration:
    """Integration layer between pump.fun monitor and existing detection system"""
    
    def __init__(self, early_detector, high_conviction_detector):
        self.early_detector = early_detector
        self.high_conviction_detector = high_conviction_detector
        self.monitor = PumpFunMonitor()
        self.logger = logging.getLogger('PumpFunIntegration')
        
        # Set up callbacks
        self.monitor.set_callbacks(
            on_new_token=self._handle_new_token_discovery,
            on_graduation=self._handle_graduation_event,
            on_significant_trade=self._handle_momentum_event
        )
    
    async def _handle_new_token_discovery(self, event_data: Dict):
        """Integrate new token discovery with existing pipeline"""
        try:
            # Add to early detection pipeline with highest priority
            token_address = event_data['token_address']
            
            # Create enhanced token data for existing system
            enhanced_data = {
                'address': token_address,
                'source': 'pump_fun_launch',
                'stage_0_bonus': 25,  # Maximum early detection bonus
                'pump_fun_launch': True,
                'detection_priority': 'ultra_high',
                'estimated_age_minutes': 0,  # Caught at launch
                **event_data
            }
            
            # Feed into existing discovery pipeline
            if hasattr(self.early_detector, '_process_priority_token'):
                await self.early_detector._process_priority_token(enhanced_data)
            
            self.logger.info(f"🔥 Pump.fun token {token_address[:8]}... fed into Stage 2 pipeline")
            
        except Exception as e:
            self.logger.error(f"❌ Error integrating new token: {e}")
    
    async def _handle_graduation_event(self, event_data: Dict):
        """Handle graduation events as exit signals"""
        try:
            token_address = event_data['token_address']
            
            # Trigger exit signals in high conviction detector
            if hasattr(self.high_conviction_detector, '_handle_graduation_exit_signal'):
                await self.high_conviction_detector._handle_graduation_exit_signal(event_data)
            
            self.logger.info(f"🎓 Graduation exit signal triggered for {token_address[:8]}...")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling graduation event: {e}")
    
    async def _handle_momentum_event(self, event_data: Dict):
        """Handle momentum events for position sizing"""
        try:
            token_address = event_data['token_address']
            
            # Enhance scoring for tokens showing momentum
            if hasattr(self.high_conviction_detector, '_apply_momentum_bonus'):
                await self.high_conviction_detector._apply_momentum_bonus(event_data)
            
            self.logger.info(f"📈 Momentum bonus applied to {token_address[:8]}...")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling momentum event: {e}")
    
    async def start_integrated_monitoring(self):
        """Start integrated pump.fun monitoring"""
        self.logger.info("🚀 Starting integrated pump.fun monitoring...")
        await self.monitor.start_monitoring() 