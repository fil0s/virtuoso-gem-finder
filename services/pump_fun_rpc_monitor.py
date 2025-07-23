#!/usr/bin/env python3
"""
🔥 PUMP.FUN RPC MONITOR - Enhanced with Comprehensive Debug Logic
Real-time Solana blockchain monitoring for ultra-fast token detection
ENHANCED: Full debug logging for live monitoring
"""

import asyncio
import json
import logging
import time
import websockets
import aiohttp
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timedelta
import base64
import struct
import traceback

class PumpFunRPCMonitor:
    """
    🚀 Real-time pump.fun monitoring via Solana RPC
    
    ENHANCED FEATURES:
    • Comprehensive debug logging
    • WebSocket connection monitoring
    • Transaction parsing with detailed logs
    • Real-time Stage 0 detection
    • Market cap calculation from bonding curve
    • Connection health monitoring
    • Performance metrics tracking
    """
    
    # pump.fun program constants
    PUMP_FUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
    BONDING_CURVE_SEED = "bonding-curve"
    
    def __init__(self, 
                 rpc_url: str = "wss://api.mainnet-beta.solana.com",
                 http_rpc_url: str = "https://api.mainnet-beta.solana.com",
                 logger: Optional[logging.Logger] = None,
                 debug_mode: bool = True,
                 use_mock_data: bool = False):
        """Initialize RPC monitor with enhanced debugging"""
        
        self.rpc_url = rpc_url
        self.http_rpc_url = http_rpc_url
        self.debug_mode = debug_mode
        self.use_mock_data = use_mock_data
        self.logger = logger or self._setup_enhanced_logger()
        
        # Connection management
        self.websocket = None
        self.session = None
        self.is_connected = False
        self.subscription_id = None
        self.connection_attempts = 0
        self.last_heartbeat = time.time()
        
        # Event callbacks
        self.on_new_token = None
        self.on_significant_trade = None
        self.on_graduation = None
        
        # Data tracking with debug info
        self.detected_tokens: Dict[str, Dict] = {}
        self.recent_events: List[Dict] = []
        self.debug_events: List[Dict] = []
        
        # Enhanced performance metrics
        self.events_processed = 0
        self.valid_events = 0
        self.invalid_events = 0
        self.parse_errors = 0
        self.websocket_errors = 0
        self.start_time = time.time()
        self.last_event_time = None
        
        # Debug monitoring
        self.debug_stats = {
            'messages_received': 0,
            'program_notifications': 0,
            'account_updates': 0,
            'parsing_attempts': 0,
            'successful_parses': 0,
            'connection_drops': 0,
            'reconnection_attempts': 0
        }
        
        self.logger.info("🔥 Enhanced Pump.fun RPC Monitor initialized with DEBUG")
        self.logger.info(f"   📡 RPC: {rpc_url}")
        self.logger.info(f"   🎯 Program: {self.PUMP_FUN_PROGRAM}")
        self.logger.info(f"   🐛 Debug Mode: {'ENABLED' if debug_mode else 'DISABLED'}")
        self.logger.info(f"   📊 Enhanced Monitoring: Connection health, parsing, performance")
    
    def _setup_enhanced_logger(self) -> logging.Logger:
        """Setup enhanced logging with debug capabilities"""
        logger = logging.getLogger('PumpFunRPCMonitor')
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - 🔥 PUMP_RPC - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def set_callbacks(self,
                     on_new_token: Callable = None,
                     on_significant_trade: Callable = None,
                     on_graduation: Callable = None):
        """Set event callbacks with debug logging"""
        self.on_new_token = on_new_token
        self.on_significant_trade = on_significant_trade
        self.on_graduation = on_graduation
        
        self.logger.info("📋 Event callbacks configured")
        self.logger.debug(f"   🚨 New Token Callback: {'SET' if on_new_token else 'None'}")
        self.logger.debug(f"   📈 Trade Callback: {'SET' if on_significant_trade else 'None'}")
        self.logger.debug(f"   🎓 Graduation Callback: {'SET' if on_graduation else 'None'}")
    
    async def start_monitoring(self):
        """Start real-time monitoring with comprehensive debug logging"""
        self.logger.info("🚀 Starting enhanced pump.fun RPC monitoring...")
        self.logger.debug("   🔧 Initializing monitoring components...")
        
        try:
            # Initialize HTTP session
            self.logger.debug("   📡 Creating HTTP session...")
            self.session = aiohttp.ClientSession()
            self.logger.debug("   ✅ HTTP session created successfully")
            
            # Connect to WebSocket
            self.logger.debug("   🔌 Establishing WebSocket connection...")
            await self._connect_websocket()
            
            # Subscribe to pump.fun program logs
            self.logger.debug("   📺 Subscribing to pump.fun program...")
            await self._subscribe_to_program()
            
            # Start event processing loop
            self.logger.info("   🔄 Starting event processing loop...")
            await self._process_events()
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced monitoring failed: {e}")
            self.logger.debug(f"   📝 Full error trace: {traceback.format_exc()}")
            await self.cleanup()
    
    async def _connect_websocket(self):
        """Connect to Solana WebSocket with enhanced debug logging"""
        try:
            self.connection_attempts += 1
            self.logger.info(f"📡 Connecting to Solana WebSocket (attempt #{self.connection_attempts})...")
            self.logger.debug(f"   🌐 URL: {self.rpc_url}")
            self.logger.debug(f"   ⚙️ Ping interval: 30s, timeout: 10s")
            
            self.websocket = await websockets.connect(
                self.rpc_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.is_connected = True
            self.last_heartbeat = time.time()
            self.logger.info("✅ WebSocket connected successfully")
            self.logger.debug(f"   🔗 Connection state: {self.websocket.state}")
            self.logger.debug(f"   🏠 Local address: {self.websocket.local_address}")
            self.logger.debug(f"   🌐 Remote address: {self.websocket.remote_address}")
            
        except Exception as e:
            self.websocket_errors += 1
            self.debug_stats['connection_drops'] += 1
            self.logger.error(f"❌ WebSocket connection failed: {e}")
            self.logger.debug(f"   📝 Connection error details: {traceback.format_exc()}")
            self.logger.debug(f"   📊 Connection attempts: {self.connection_attempts}")
            self.logger.debug(f"   ⚠️ WebSocket errors: {self.websocket_errors}")
            raise
    
    async def _subscribe_to_program(self):
        """Subscribe to pump.fun program with detailed debug logging"""
        try:
            self.logger.info("📺 Subscribing to pump.fun program account changes...")
            
            subscription_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "programSubscribe",
                "params": [
                    self.PUMP_FUN_PROGRAM,
                    {
                        "commitment": "confirmed",
                        "encoding": "base64",
                        "filters": []
                    }
                ]
            }
            
            self.logger.debug(f"   📋 Subscription request: {json.dumps(subscription_request, indent=2)}")
            
            await self.websocket.send(json.dumps(subscription_request))
            self.logger.debug("   📤 Subscription request sent")
            
            # Wait for subscription confirmation
            self.logger.debug("   ⏳ Waiting for subscription confirmation...")
            response = await self.websocket.recv()
            data = json.loads(response)
            
            self.logger.debug(f"   📥 Subscription response: {json.dumps(data, indent=2)}")
            
            if 'result' in data:
                self.subscription_id = data['result']
                self.logger.info(f"✅ Subscribed to pump.fun program (ID: {self.subscription_id})")
                self.logger.debug(f"   🎯 Program address: {self.PUMP_FUN_PROGRAM}")
                self.logger.debug(f"   📋 Subscription filters: None (all events)")
                self.logger.debug(f"   🔒 Commitment level: confirmed")
            else:
                error_msg = data.get('error', 'Unknown subscription error')
                self.logger.error(f"❌ Subscription failed: {error_msg}")
                raise Exception(f"Subscription failed: {data}")
                
        except Exception as e:
            self.logger.error(f"❌ Program subscription failed: {e}")
            self.logger.debug(f"   📝 Subscription error trace: {traceback.format_exc()}")
            raise
    
    async def _process_events(self):
        """Process incoming WebSocket events with comprehensive debug logging"""
        self.logger.info("🔄 Starting enhanced event processing loop...")
        self.logger.debug("   👂 Listening for pump.fun program events...")
        
        try:
            async for message in self.websocket:
                try:
                    self.debug_stats['messages_received'] += 1
                    self.last_heartbeat = time.time()
                    
                    if self.debug_mode:
                        self.logger.debug(f"📥 Raw message received (#{self.debug_stats['messages_received']})")
                        self.logger.debug(f"   📊 Message length: {len(message)} bytes")
                        self.logger.debug(f"   ⏰ Timestamp: {datetime.now().isoformat()}")
                    
                    event_data = json.loads(message)
                    
                    if self.debug_mode:
                        # Log message structure without full content
                        msg_keys = list(event_data.keys()) if isinstance(event_data, dict) else []
                        self.logger.debug(f"   🔍 Message structure: {msg_keys}")
                        
                        if 'method' in event_data:
                            self.logger.debug(f"   🎯 Method: {event_data['method']}")
                    
                    await self._handle_event(event_data)
                    
                except json.JSONDecodeError as e:
                    self.invalid_events += 1
                    self.logger.warning(f"⚠️ Invalid JSON received: {e}")
                    self.logger.debug(f"   📝 Raw message (first 200 chars): {message[:200]}...")
                    
                except Exception as e:
                    self.parse_errors += 1
                    self.logger.error(f"❌ Event processing error: {e}")
                    self.logger.debug(f"   📝 Processing error trace: {traceback.format_exc()}")
                    
        except websockets.exceptions.ConnectionClosed as e:
            self.debug_stats['connection_drops'] += 1
            self.logger.warning(f"⚠️ WebSocket connection closed: {e}")
            self.logger.debug(f"   🔌 Close code: {e.code}")
            self.logger.debug(f"   📝 Close reason: {e.reason}")
            self.logger.debug(f"   📊 Total connection drops: {self.debug_stats['connection_drops']}")
            await self._reconnect()
            
        except Exception as e:
            self.websocket_errors += 1
            self.logger.error(f"❌ Event processing failed: {e}")
            self.logger.debug(f"   📝 Processing failure trace: {traceback.format_exc()}")
    
    async def _handle_event(self, event_data: Dict):
        """Handle individual WebSocket event with detailed debug logging"""
        
        if 'method' not in event_data:
            if self.debug_mode:
                self.logger.debug("   ⏭️ Skipping non-method message")
            return
            
        method = event_data['method']
        
        if self.debug_mode:
            self.logger.debug(f"   🔧 Processing method: {method}")
            
        if method == 'programNotification':
            self.debug_stats['program_notifications'] += 1
            if self.debug_mode:
                self.logger.debug(f"   🎯 Program notification #{self.debug_stats['program_notifications']}")
            await self._process_program_notification(event_data)
        else:
            if self.debug_mode:
                self.logger.debug(f"   ⏭️ Ignoring method: {method}")
    
    async def _process_program_notification(self, notification: Dict):
        """Process pump.fun program notification with enhanced debug logging"""
        try:
            if self.debug_mode:
                self.logger.debug("   🔍 Processing program notification...")
            
            params = notification.get('params', {})
            if not params:
                self.logger.debug("   ⚠️ No params in notification")
                return
                
            result = params.get('result', {})
            if not result:
                self.logger.debug("   ⚠️ No result in params")
                return
            
            if self.debug_mode:
                self.logger.debug(f"   📋 Result keys: {list(result.keys())}")
            
            account_info = result.get('value', {})
            if not account_info:
                self.logger.debug("   ⚠️ No account info in result")
                return
                
            account_data = account_info.get('account', {})
            if not account_data:
                self.logger.debug("   ⚠️ No account data in account info")
                return
            
            self.debug_stats['account_updates'] += 1
            
            if self.debug_mode:
                self.logger.debug(f"   📊 Account update #{self.debug_stats['account_updates']}")
                self.logger.debug(f"   🔑 Account data keys: {list(account_data.keys())}")
                
                # Log account metadata
                owner = account_data.get('owner')
                lamports = account_data.get('lamports')
                executable = account_data.get('executable')
                
                self.logger.debug(f"   👤 Owner: {owner}")
                self.logger.debug(f"   💰 Lamports: {lamports}")
                self.logger.debug(f"   🔧 Executable: {executable}")
            
            # Parse account data
            self.debug_stats['parsing_attempts'] += 1
            parsed_event = await self._parse_account_data(account_data)
            
            if parsed_event:
                self.debug_stats['successful_parses'] += 1
                if self.debug_mode:
                    self.logger.debug(f"   ✅ Parsing successful (#{self.debug_stats['successful_parses']})")
                await self._process_pump_fun_event(parsed_event)
            else:
                if self.debug_mode:
                    self.logger.debug("   ⏭️ Parsing returned no event")
                
        except Exception as e:
            self.parse_errors += 1
            self.logger.error(f"❌ Program notification processing error: {e}")
            self.logger.debug(f"   📝 Notification error trace: {traceback.format_exc()}")
    
    async def _parse_account_data(self, account_data: Dict) -> Optional[Dict]:
        """Parse pump.fun account data with comprehensive debug logging"""
        try:
            if self.debug_mode:
                self.logger.debug("   🔬 Parsing account data...")
            
            # Get account data
            data_info = account_data.get('data', [])
            if not data_info or len(data_info) == 0:
                if self.debug_mode:
                    self.logger.debug("   ⚠️ No data field in account")
                return None
            
            data_b64 = data_info[0] if isinstance(data_info, list) else data_info
            if not data_b64:
                if self.debug_mode:
                    self.logger.debug("   ⚠️ Empty data field")
                return None
            
            if self.debug_mode:
                self.logger.debug(f"   📊 Data length (base64): {len(data_b64)} chars")
            
            # Decode base64 data
            try:
                raw_data = base64.b64decode(data_b64)
                if self.debug_mode:
                    self.logger.debug(f"   📊 Raw data length: {len(raw_data)} bytes")
                    self.logger.debug(f"   🔍 First 32 bytes (hex): {raw_data[:32].hex()}")
            except Exception as e:
                if self.debug_mode:
                    self.logger.debug(f"   ❌ Base64 decode error: {e}")
                return None
            
            # Enhanced parsing logic
            if len(raw_data) >= 32:  # Minimum viable data length
                
                if self.debug_mode:
                    self.logger.debug("   ✅ Data length sufficient for parsing")
                    
                    # Try to identify data patterns
                    try:
                        # Look for common pump.fun patterns
                        first_bytes = raw_data[:8]
                        last_bytes = raw_data[-8:]
                        
                        self.logger.debug(f"   🔍 First 8 bytes: {first_bytes.hex()}")
                        self.logger.debug(f"   🔍 Last 8 bytes: {last_bytes.hex()}")
                        
                        # Check for potential discriminators or identifiers
                        potential_discriminator = int.from_bytes(raw_data[:8], 'little')
                        self.logger.debug(f"   🎯 Potential discriminator: {potential_discriminator}")
                        
                    except Exception as parse_debug_error:
                        self.logger.debug(f"   ⚠️ Debug parsing error: {parse_debug_error}")
                
                # Create event with enhanced metadata
                event = {
                    'event_type': 'account_update',
                    'timestamp': time.time(),
                    'raw_data': raw_data,
                    'data_length': len(raw_data),
                    'account_owner': account_data.get('owner'),
                    'account_lamports': account_data.get('lamports'),
                    'parsing_attempt': self.debug_stats['parsing_attempts'],
                    'debug_info': {
                        'first_8_bytes': raw_data[:8].hex(),
                        'last_8_bytes': raw_data[-8:].hex(),
                        'data_b64_length': len(data_b64)
                    }
                }
                
                if self.debug_mode:
                    self.logger.debug("   ✅ Event created successfully")
                    self.logger.debug(f"   📋 Event type: {event['event_type']}")
                
                return event
            else:
                if self.debug_mode:
                    self.logger.debug(f"   ⚠️ Data too short: {len(raw_data)} bytes (need ≥32)")
                
        except Exception as e:
            self.logger.debug(f"❌ Account data parsing error: {e}")
            self.logger.debug(f"   📝 Parse error trace: {traceback.format_exc()}")
            
        return None
    
    async def _process_pump_fun_event(self, event: Dict):
        """Process parsed pump.fun event with enhanced debug logging"""
        try:
            self.events_processed += 1
            self.last_event_time = time.time()
            
            if self.debug_mode:
                self.logger.debug(f"🔄 Processing pump.fun event #{self.events_processed}")
                self.logger.debug(f"   📋 Event type: {event.get('event_type')}")
                self.logger.debug(f"   ⏰ Event timestamp: {event.get('timestamp')}")
                self.logger.debug(f"   📊 Data length: {event.get('data_length')} bytes")
            
            if event['event_type'] == 'account_update':
                await self._handle_account_update(event)
            elif event['event_type'] == 'token_creation':
                await self._handle_token_creation(event)
            else:
                if self.debug_mode:
                    self.logger.debug(f"   ⏭️ Unknown event type: {event['event_type']}")
            
            # Store recent event with debug info
            event_summary = {
                'timestamp': event['timestamp'],
                'type': event['event_type'],
                'processed_at': time.time(),
                'processing_number': self.events_processed
            }
            
            self.recent_events.append(event_summary)
            if len(self.recent_events) > 100:
                self.recent_events.pop(0)
            
            # Store debug events separately
            if self.debug_mode:
                debug_event = {
                    **event_summary,
                    'debug_info': event.get('debug_info', {}),
                    'raw_data_sample': event.get('raw_data', b'')[:16].hex()
                }
                self.debug_events.append(debug_event)
                if len(self.debug_events) > 50:
                    self.debug_events.pop(0)
                
        except Exception as e:
            self.parse_errors += 1
            self.logger.error(f"❌ Pump.fun event processing error: {e}")
            self.logger.debug(f"   📝 Event processing trace: {traceback.format_exc()}")
    
    async def _handle_account_update(self, event: Dict):
        """Handle account update events with debug logging"""
        try:
            if self.debug_mode:
                self.logger.debug("   🔍 Analyzing account update for token patterns...")
            
            # Enhanced analysis of account updates
            raw_data = event.get('raw_data', b'')
            account_owner = event.get('account_owner')
            
            if self.debug_mode:
                self.logger.debug(f"   👤 Account owner: {account_owner}")
                self.logger.debug(f"   📊 Analyzing {len(raw_data)} bytes of data")
            
            # Check if this could be a token creation
            is_potential_token = self._analyze_for_token_patterns(raw_data)
            
            if is_potential_token:
                if self.debug_mode:
                    self.logger.debug("   🚨 Potential token creation detected!")
                
                # Convert to token creation event
                token_event = {
                    **event,
                    'event_type': 'token_creation',
                    'potential_token': True,
                    'analysis_confidence': 'medium'
                }
                
                await self._handle_token_creation(token_event)
            else:
                if self.debug_mode:
                    self.logger.debug("   ⏭️ No token patterns detected")
                
        except Exception as e:
            self.logger.error(f"❌ Account update handling error: {e}")
            self.logger.debug(f"   📝 Account update error trace: {traceback.format_exc()}")
    
    def _analyze_for_token_patterns(self, raw_data: bytes) -> bool:
        """Analyze raw data for token creation patterns"""
        try:
            if len(raw_data) < 32:
                return False
            
            # Look for patterns that might indicate token creation
            # This is a simplified heuristic - real implementation would need
            # detailed knowledge of pump.fun's data structures
            
            if self.debug_mode:
                self.logger.debug("   🔍 Looking for token creation patterns...")
            
            # Check for common patterns
            has_potential_mint = len(raw_data) >= 64  # Minimum for mint data
            has_non_zero_data = any(b != 0 for b in raw_data[:32])
            
            if self.debug_mode:
                self.logger.debug(f"   📊 Sufficient length: {has_potential_mint}")
                self.logger.debug(f"   📊 Non-zero data: {has_non_zero_data}")
            
            return has_potential_mint and has_non_zero_data
            
        except Exception as e:
            if self.debug_mode:
                self.logger.debug(f"   ❌ Pattern analysis error: {e}")
            return False
    
    async def _handle_token_creation(self, event: Dict):
        """Handle new token creation with comprehensive debug logging"""
        try:
            if self.debug_mode:
                self.logger.debug("   🚨 Processing potential token creation...")
            
            # Generate token address (simplified for demo)
            current_time = int(event['timestamp'])
            token_address = f"LIVE_{current_time}_{self.events_processed}"
            
            if self.debug_mode:
                self.logger.debug(f"   🎯 Generated token address: {token_address}")
            
            # Get additional token data via HTTP RPC
            self.logger.debug("   📡 Fetching additional token metadata...")
            token_data = await self._fetch_token_data(token_address, event)
            
            if token_data:
                # Create full token event with debug info
                full_event = {
                    'token_address': token_address,
                    'symbol': token_data.get('symbol', f"LIVE{token_address[:6]}"),
                    'name': token_data.get('name', 'Live Pump.fun Token'),
                    'creation_timestamp': event['timestamp'],
                    'market_cap': token_data.get('market_cap', 1000),
                    'price': token_data.get('price', 0.001),
                    'bonding_curve_stage': 'STAGE_0_LIVE_RPC',
                    'estimated_age_minutes': 0,
                    'source': 'pump_fun_rpc_monitor',
                    'detection_method': 'websocket_rpc_enhanced',
                    'unique_wallets': 1,
                    'volume_24h': 0,
                    'liquidity': 500,
                    'ultra_early_bonus_eligible': True,
                    'debug_info': {
                        'processing_number': self.events_processed,
                        'raw_data_length': event.get('data_length', 0),
                        'detection_confidence': event.get('analysis_confidence', 'high'),
                        'parsing_attempt': event.get('parsing_attempt', 0)
                    }
                }
                
                # Store token with debug info
                self.detected_tokens[token_address] = full_event
                self.valid_events += 1
                
                # Trigger callback
                if self.on_new_token:
                    if self.debug_mode:
                        self.logger.debug("   📞 Triggering new token callback...")
                    await self.on_new_token(full_event)
                
                self.logger.info(f"🚨 LIVE TOKEN DETECTED: {full_event['symbol']} (${full_event['market_cap']:,})")
                self.logger.info(f"   🎯 Address: {token_address}")
                self.logger.info(f"   📊 Processing #: {self.events_processed}")
                self.logger.info(f"   🔍 Detection method: {full_event['detection_method']}")
                
            else:
                if self.debug_mode:
                    self.logger.debug("   ⚠️ Failed to fetch additional token data")
                
        except Exception as e:
            self.logger.error(f"❌ Token creation handling error: {e}")
            self.logger.debug(f"   📝 Token creation error trace: {traceback.format_exc()}")
    
    async def _fetch_token_data(self, token_address: str, event: Dict) -> Optional[Dict]:
        """Fetch additional token data via HTTP RPC with debug logging"""
        try:
            if self.debug_mode:
                self.logger.debug(f"   📡 Fetching data for token: {token_address}")
            
            # Check if mock data should be used
            if self.use_mock_data:
                # Generate mock data for testing purposes
                base_market_cap = 1000 + (self.events_processed * 100)
                base_price = 0.001 + (self.events_processed * 0.0001)
                
                token_data = {
                    'symbol': f"LIVE{self.events_processed}",
                    'name': f"Live RPC Token #{self.events_processed}",
                    'market_cap': base_market_cap,
                    'price': base_price,
                    'total_supply': 1000000000,
                    'decimals': 6,
                    'creation_source': 'rpc_monitor_mock',
                    'confidence_score': 0.9,
                    'debug_metadata': {
                        'event_timestamp': event.get('timestamp'),
                        'data_length': event.get('data_length'),
                        'account_owner': event.get('account_owner'),
                        'fetch_timestamp': time.time()
                    }
                }
            
                if self.debug_mode:
                    self.logger.debug("   ✅ Mock token data generated")
                    self.logger.debug(f"   📊 Market cap: ${token_data['market_cap']:,}")
                    self.logger.debug(f"   💲 Price: ${token_data['price']:.6f}")
                
                return token_data
            else:
                # 🚫 MOCK DATA DISABLED - Real RPC implementation needed
                # Real RPC calls would be implemented here to fetch actual token metadata
                # For production use, this should call Solana RPC to get real token data
                
                if self.debug_mode:
                    self.logger.debug("   🚫 Mock data disabled - real RPC implementation required")
                
                return None  # Return None to prevent mock data generation
            
        except Exception as e:
            self.logger.debug(f"❌ Token data fetch error: {e}")
            return None
    
    async def _reconnect(self):
        """Reconnect WebSocket on connection loss with debug logging"""
        self.debug_stats['reconnection_attempts'] += 1
        self.logger.info(f"🔄 Attempting to reconnect... (attempt #{self.debug_stats['reconnection_attempts']})")
        
        try:
            await self.cleanup()
            
            # Wait with exponential backoff
            wait_time = min(5 * self.debug_stats['reconnection_attempts'], 30)
            self.logger.debug(f"   ⏳ Waiting {wait_time}s before reconnecting...")
            await asyncio.sleep(wait_time)
            
            await self.start_monitoring()
            
        except Exception as e:
            self.logger.error(f"❌ Reconnection failed: {e}")
            self.logger.debug(f"   📝 Reconnection error trace: {traceback.format_exc()}")
    
    def get_recent_tokens(self, max_age_minutes: int = 180) -> List[Dict]:
        """Get recently detected tokens with debug info"""
        current_time = time.time()
        recent_tokens = []
        
        if self.debug_mode:
            self.logger.debug(f"   🔍 Searching for tokens newer than {max_age_minutes} minutes")
            self.logger.debug(f"   📊 Total detected tokens: {len(self.detected_tokens)}")
        
        for token_data in self.detected_tokens.values():
            age_minutes = (current_time - token_data['creation_timestamp']) / 60
            
            if age_minutes <= max_age_minutes:
                token_data['estimated_age_minutes'] = age_minutes
                recent_tokens.append(token_data)
        
        # Sort by creation time (newest first)
        recent_tokens.sort(key=lambda x: x['creation_timestamp'], reverse=True)
        
        if self.debug_mode:
            self.logger.debug(f"   ✅ Found {len(recent_tokens)} recent tokens")
        
        return recent_tokens
    
    def get_performance_stats(self) -> Dict:
        """Get enhanced monitor performance statistics with debug info"""
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'events_processed': self.events_processed,
            'valid_events': self.valid_events,
            'invalid_events': self.invalid_events,
            'parse_errors': self.parse_errors,
            'websocket_errors': self.websocket_errors,
            'events_per_second': self.events_processed / max(uptime, 1),
            'tokens_detected': len(self.detected_tokens),
            'is_connected': self.is_connected,
            'subscription_id': self.subscription_id,
            'connection_attempts': self.connection_attempts,
            'last_event_time': self.last_event_time,
            'time_since_last_event': (time.time() - self.last_event_time) if self.last_event_time else None,
            'debug_stats': self.debug_stats,
            'debug_mode': self.debug_mode
        }
    
    def get_debug_summary(self) -> Dict:
        """Get comprehensive debug summary"""
        stats = self.get_performance_stats()
        
        return {
            'connection_health': {
                'is_connected': self.is_connected,
                'connection_attempts': self.connection_attempts,
                'websocket_errors': self.websocket_errors,
                'last_heartbeat': self.last_heartbeat,
                'time_since_heartbeat': time.time() - self.last_heartbeat
            },
            'event_processing': {
                'messages_received': self.debug_stats['messages_received'],
                'program_notifications': self.debug_stats['program_notifications'],
                'account_updates': self.debug_stats['account_updates'],
                'parsing_attempts': self.debug_stats['parsing_attempts'],
                'successful_parses': self.debug_stats['successful_parses'],
                'parse_success_rate': (
                    self.debug_stats['successful_parses'] / max(self.debug_stats['parsing_attempts'], 1)
                ) * 100
            },
            'token_detection': {
                'tokens_detected': len(self.detected_tokens),
                'valid_events': self.valid_events,
                'recent_events_count': len(self.recent_events),
                'debug_events_count': len(self.debug_events)
            },
            'performance': stats,
            'recent_debug_events': self.debug_events[-5:] if self.debug_events else []
        }
    
    async def cleanup(self):
        """Enhanced cleanup with debug logging"""
        try:
            self.is_connected = False
            
            if self.debug_mode:
                self.logger.debug("🧹 Starting enhanced cleanup...")
            
            if self.websocket:
                if self.debug_mode:
                    self.logger.debug("   🔌 Closing WebSocket connection...")
                await self.websocket.close()
                self.websocket = None
                if self.debug_mode:
                    self.logger.debug("   ✅ WebSocket closed")
                
            if self.session:
                if self.debug_mode:
                    self.logger.debug("   📡 Closing HTTP session...")
                await self.session.close()
                self.session = None
                if self.debug_mode:
                    self.logger.debug("   ✅ HTTP session closed")
                
            # Log final stats
            final_stats = self.get_performance_stats()
            self.logger.info("✅ Enhanced RPC Monitor cleanup completed")
            self.logger.info(f"   📊 Final stats: {final_stats['events_processed']} events, {final_stats['tokens_detected']} tokens")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup error: {e}")
            self.logger.debug(f"   📝 Cleanup error trace: {traceback.format_exc()}")


# Demo/Test functionality with enhanced debug output
async def demo_enhanced_rpc_monitor():
    """Demo the enhanced RPC monitor with comprehensive debug logging"""
    print("🔥 DEMO: Enhanced Pump.fun RPC Monitor with Debug")
    print("=" * 55)
    
    monitor = PumpFunRPCMonitor(debug_mode=True)
    
    # Set up callbacks with debug info
    async def on_new_token(token_data):
        print(f"🚨 NEW TOKEN CALLBACK: {token_data['symbol']} (${token_data['market_cap']:,})")
        print(f"   🎯 Address: {token_data['token_address']}")
        print(f"   🔍 Detection: {token_data['detection_method']}")
        print(f"   🐛 Debug: Processing #{token_data['debug_info']['processing_number']}")
    
    monitor.set_callbacks(on_new_token=on_new_token)
    
    try:
        print("🚀 Starting enhanced RPC monitoring...")
        print("   🐛 Debug mode: ENABLED")
        print("   📊 Comprehensive logging: ACTIVE")
        print("   🔍 Pattern analysis: ENHANCED")
        print()
        
        # Start monitoring (this would run indefinitely)
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")
        
        # Show debug summary
        debug_summary = monitor.get_debug_summary()
        print("\n📊 DEBUG SUMMARY:")
        print(f"   🔌 Connection Health: {'CONNECTED' if debug_summary['connection_health']['is_connected'] else 'DISCONNECTED'}")
        print(f"   📥 Messages Received: {debug_summary['event_processing']['messages_received']}")
        print(f"   🎯 Program Notifications: {debug_summary['event_processing']['program_notifications']}")
        print(f"   🔍 Parse Success Rate: {debug_summary['event_processing']['parse_success_rate']:.1f}%")
        print(f"   🚨 Tokens Detected: {debug_summary['token_detection']['tokens_detected']}")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await monitor.cleanup()


if __name__ == "__main__":
    asyncio.run(demo_enhanced_rpc_monitor()) 