"""
Whale Activity Analyzer

Advanced whale detection and tracking system for early alpha generation.
Detects large wallet movements, accumulation patterns, and institutional flows
to provide early signals before price movements.

Key Features:
- Large wallet accumulation/distribution detection
- Whale rotation pattern analysis  
- Institutional flow tracking
- Smart money timing analysis
- Dynamic threshold adaptation
- Multi-timeframe whale behavior analysis
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from utils.structured_logger import get_structured_logger

class WhaleActivityType(Enum):
    ACCUMULATION = "accumulation"           # Whales buying heavily  
    DISTRIBUTION = "distribution"           # Whales selling/exiting
    ROTATION = "rotation"                   # Whales changing positions
    INSTITUTIONAL_FLOW = "institutional"    # Institution-scale movements
    SMART_MONEY_ENTRY = "smart_entry"      # Proven performers entering
    COORDINATED_BUY = "coordinated_buy"    # Multiple whales coordinating
    STEALTH_ACCUMULATION = "stealth"       # Quiet accumulation over time

@dataclass
class WhaleSignal:
    type: WhaleActivityType
    confidence: float  # 0.0 to 1.0
    score_impact: int  # -20 to +25 points
    whale_count: int   # Number of whales involved
    total_value: float # Total USD value of activity
    timeframe: str     # When the activity occurred
    details: str       # Human readable description
    whale_addresses: List[str]  # Involved wallet addresses

class WhaleActivityAnalyzer:
    """
    Analyzes whale activity patterns to detect accumulation/distribution
    and provide early alpha signals for token opportunities.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None, whale_discovery_service=None):
        self.logger = logger or logging.getLogger(__name__)
        self.structured_logger = get_structured_logger('WhaleActivityAnalyzer')
        
        # Whale discovery service for dynamic whale database updates
        self.whale_discovery_service = whale_discovery_service
        
        # Known whale and institutional wallets database
        self.whale_database = {
            # Tier 1: Mega Whales (>$50M typical positions)
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": {
                "tier": 1, "name": "Alameda Research", "avg_position": 100_000_000,
                "success_rate": 0.75, "known_for": "early_entry"
            },
            "HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH": {
                "tier": 1, "name": "Jump Trading", "avg_position": 80_000_000,
                "success_rate": 0.85, "known_for": "market_making"
            },
            "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1": {
                "tier": 1, "name": "Wintermute", "avg_position": 60_000_000,
                "success_rate": 0.80, "known_for": "arbitrage"
            },
            
            # Tier 2: Large Whales ($10M-$50M positions)
            "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh": {
                "tier": 2, "name": "Individual Whale 1", "avg_position": 25_000_000,
                "success_rate": 0.70, "known_for": "momentum_trading"
            },
            "CuieVDEDtLo7FypA9SbLM9saXFdb1dsshEkyErMqkRQq": {
                "tier": 2, "name": "Individual Whale 2", "avg_position": 20_000_000,
                "success_rate": 0.75, "known_for": "early_adoption"
            },
            
            # Tier 3: Medium Whales ($1M-$10M positions)
            "8UJgxaiQx5nTrdDgph5FiahMmzduuLTLf5WmsPegYA6W": {
                "tier": 3, "name": "Smart Money 1", "avg_position": 5_000_000,
                "success_rate": 0.65, "known_for": "swing_trading"
            },
            "3NC2UjdvoyLFaQGJjSp3JkgeJZkM1VaE1eNCKZP2XGJS": {
                "tier": 3, "name": "Smart Money 2", "avg_position": 3_000_000,
                "success_rate": 0.68, "known_for": "technical_analysis"
            }
        }
        
        # Load dynamically discovered whales if service is available
        self._load_discovered_whales()
        
        # Dynamic thresholds based on market conditions
        self.thresholds = {
            'large_transaction_usd': 500_000,      # $500K+ = large transaction
            'whale_transaction_usd': 1_000_000,    # $1M+ = whale transaction  
            'institutional_usd': 5_000_000,        # $5M+ = institutional scale
            'accumulation_timeframe_hours': 24,    # Look for accumulation over 24h
            'distribution_warning_ratio': 0.3,     # 30%+ of holdings sold = distribution
            'coordinated_whale_count': 3,          # 3+ whales = coordinated activity
            'stealth_accumulation_days': 7,        # Track accumulation over 7 days
            'min_confidence_threshold': 0.6        # Minimum confidence for signals
        }
        
        # Transaction cache for pattern analysis
        self.transaction_cache = {}
        self.whale_position_cache = {}

    def _load_discovered_whales(self):
        """Load dynamically discovered whales into the database"""
        if self.whale_discovery_service:
            try:
                discovered_whales = self.whale_discovery_service.get_whale_database_for_analyzer()
                
                # Merge discovered whales with existing database
                original_count = len(self.whale_database)
                self.whale_database.update(discovered_whales)
                new_count = len(self.whale_database) - original_count
                
                if new_count > 0:
                    self.logger.info(f"🐋 Loaded {new_count} dynamically discovered whales into analyzer")
                    self.logger.info(f"   Total whale database size: {len(self.whale_database)} wallets")
                    
                    # Log some stats about discovered whales
                    tier_counts = {1: 0, 2: 0, 3: 0}
                    for whale_data in discovered_whales.values():
                        tier = whale_data.get('tier', 3)
                        tier_counts[tier] += 1
                    
                    self.logger.info(f"   Discovered whale distribution - Tier 1: {tier_counts[1]}, Tier 2: {tier_counts[2]}, Tier 3: {tier_counts[3]}")
                    
            except Exception as e:
                self.logger.warning(f"Failed to load discovered whales: {e}")

    async def refresh_whale_database(self):
        """Refresh the whale database with latest discoveries"""
        if self.whale_discovery_service:
            try:
                # Trigger a fresh discovery run (limit to 20 for performance)
                new_whales = await self.whale_discovery_service.discover_new_whales(max_discoveries=20)
                
                if new_whales:
                    # Reload the updated database
                    self._load_discovered_whales()
                    self.logger.info(f"🔄 Refreshed whale database with {len(new_whales)} new discoveries")
                else:
                    self.logger.info("🔄 Whale database refresh complete - no new whales found")
                    
            except Exception as e:
                self.logger.warning(f"Failed to refresh whale database: {e}")

    def get_whale_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the current whale database"""
        total_whales = len(self.whale_database)
        tier_counts = {1: 0, 2: 0, 3: 0}
        total_avg_position = 0
        total_success_rate = 0
        
        for whale_data in self.whale_database.values():
            tier = whale_data.get('tier', 3)
            tier_counts[tier] += 1
            total_avg_position += whale_data.get('avg_position', 0)
            total_success_rate += whale_data.get('success_rate', 0)
        
        return {
            'total_whales': total_whales,
            'tier_distribution': tier_counts,
            'avg_position_size': total_avg_position / total_whales if total_whales > 0 else 0,
            'avg_success_rate': total_success_rate / total_whales if total_whales > 0 else 0,
            'has_discovery_service': self.whale_discovery_service is not None
        }

    async def analyze_whale_activity(self, token_address: str, token_data: Dict[str, Any], scan_id: Optional[str] = None) -> WhaleSignal:
        """
        Main analysis function that detects whale activity patterns
        and returns a signal with scoring impact.
        """
        token_symbol = token_data.get('symbol', 'UNKNOWN')
        self.structured_logger.info({
            "event": "whale_analysis_start",
            "scan_id": scan_id,
            "token_address": token_address,
            "token_symbol": token_symbol,
            "timestamp": int(time.time())
        })
        try:
            # Type checks for all major data structures
            holders_data = token_data.get('holders_data', {})
            top_traders = token_data.get('top_traders', [])
            market_cap = token_data.get('market_cap', 0)
            volume_24h = token_data.get('volume_24h', 0)

            if not isinstance(holders_data, dict):
                self.logger.error(f"[WHALE] holders_data is not a dict for {token_symbol}")
                raise TypeError("holders_data must be a dict")
            if not isinstance(top_traders, list):
                self.logger.error(f"[WHALE] top_traders is not a list for {token_symbol}")
                raise TypeError("top_traders must be a list")

            whale_signals = []
            # 1. Large Holder Accumulation Analysis
            try:
                accumulation_signal = await self._detect_whale_accumulation(
                    token_address, holders_data, market_cap, scan_id
                )
                if accumulation_signal:
                    whale_signals.append(accumulation_signal)
            except Exception as e:
                self.logger.error(f"[WHALE] Error in accumulation analysis for {token_symbol}: {e}")
            # 2. Whale Trading Pattern Analysis
            try:
                trading_signal = await self._analyze_whale_trading_patterns(
                    token_address, top_traders, volume_24h, scan_id
                )
                if trading_signal:
                    whale_signals.append(trading_signal)
            except Exception as e:
                self.logger.error(f"[WHALE] Error in trading pattern analysis for {token_symbol}: {e}")
            # 3. Institutional Flow Detection
            try:
                institutional_signal = await self._detect_institutional_flows(
                    token_address, token_data, scan_id
                )
                if institutional_signal:
                    whale_signals.append(institutional_signal)
            except Exception as e:
                self.logger.error(f"[WHALE] Error in institutional flow analysis for {token_symbol}: {e}")
            # 4. Smart Money Timing Analysis
            try:
                timing_signal = await self._analyze_smart_money_timing(
                    token_address, token_data, scan_id
                )
                if timing_signal:
                    whale_signals.append(timing_signal)
            except Exception as e:
                self.logger.error(f"[WHALE] Error in smart money timing analysis for {token_symbol}: {e}")
            # 5. Coordinated Whale Activity Detection
            try:
                coordination_signal = await self._detect_coordinated_whale_activity(
                    token_address, holders_data, top_traders, scan_id
                )
                if coordination_signal:
                    whale_signals.append(coordination_signal)
            except Exception as e:
                self.logger.error(f"[WHALE] Error in coordinated whale activity analysis for {token_symbol}: {e}")
            # Combine signals into final whale activity assessment
            if whale_signals:
                combined_signal = self._combine_whale_signals(whale_signals, token_symbol)
                self.structured_logger.info({
                    "event": "whale_analysis_complete",
                    "scan_id": scan_id,
                    "token_address": token_address,
                    "token_symbol": token_symbol,
                    "activity_type": combined_signal.type.value,
                    "whale_count": combined_signal.whale_count,
                    "total_value": combined_signal.total_value,
                    "confidence": combined_signal.confidence,
                    "timestamp": int(time.time())
                })
                return combined_signal
            else:
                self.logger.error(f"[WHALE] No valid whale signals for {token_symbol}, returning default error signal.")
                return WhaleSignal(
                    type=WhaleActivityType.ACCUMULATION,
                    confidence=0.0,
                    score_impact=0,
                    whale_count=0,
                    total_value=0.0,
                    timeframe="error",
                    details="error: no valid whale signals",
                    whale_addresses=[]
                )
        except Exception as e:
            self.structured_logger.error({
                "event": "whale_analysis_error",
                "scan_id": scan_id,
                "token_address": token_address,
                "token_symbol": token_symbol,
                "error": str(e),
                "timestamp": int(time.time())
            })
            self.logger.error(f"[WHALE] Exception in analyze_whale_activity for {token_symbol}: {e}")
            return WhaleSignal(
                type=WhaleActivityType.ACCUMULATION,
                confidence=0.0,
                score_impact=0,
                whale_count=0,
                total_value=0.0,
                timeframe="error",
                details=f"error: {e}",
                whale_addresses=[]
            )

    async def _detect_whale_accumulation(self, token_address: str, holders_data: Dict, market_cap: float, scan_id: Optional[str] = None) -> Optional[WhaleSignal]:
        """Detect large wallet accumulation patterns"""
        if not holders_data or not isinstance(holders_data, dict):
            return None
            
        items = holders_data.get('items', [])
        if not items:
            return None
        
        whale_addresses = []
        total_whale_value = 0
        accumulation_strength = 0
        
        for holder in items[:20]:  # Check top 20 holders
            if not isinstance(holder, dict):
                continue
                
            owner = holder.get('owner', '')
            percentage = holder.get('percentage', 0)
            
            # Calculate position value
            position_value = (percentage / 100) * market_cap if market_cap > 0 else 0
            
            # Check if this is a known whale or large position
            is_known_whale = owner in self.whale_database
            is_large_position = position_value >= self.thresholds['whale_transaction_usd']
            
            if is_known_whale or is_large_position:
                whale_addresses.append(owner)
                total_whale_value += position_value
                
                # Bonus for known successful whales
                if is_known_whale:
                    whale_info = self.whale_database[owner]
                    accumulation_strength += whale_info['success_rate'] * 10
                else:
                    accumulation_strength += 5  # Unknown large holder
        
        if len(whale_addresses) >= 2:  # Multiple whales detected
            confidence = min(1.0, len(whale_addresses) / 10 + accumulation_strength / 50)
            
            # Determine activity type and score impact
            if len(whale_addresses) >= 4 and total_whale_value >= self.thresholds['institutional_usd']:
                activity_type = WhaleActivityType.INSTITUTIONAL_FLOW
                score_impact = int(20 + confidence * 5)  # +20 to +25 bonus
            elif len(whale_addresses) >= 3:
                activity_type = WhaleActivityType.COORDINATED_BUY  
                score_impact = int(15 + confidence * 5)  # +15 to +20 bonus
            else:
                activity_type = WhaleActivityType.ACCUMULATION
                score_impact = int(10 + confidence * 5)  # +10 to +15 bonus
            
            signal = WhaleSignal(
                type=activity_type,
                confidence=confidence,
                score_impact=score_impact,
                whale_count=len(whale_addresses),
                total_value=total_whale_value,
                timeframe="current_holdings",
                details=f"{len(whale_addresses)} whales holding ${total_whale_value:,.0f}",
                whale_addresses=whale_addresses
            )
            
            self.structured_logger.info({
                "event": "whale_accumulation_detected",
                "scan_id": scan_id,
                "token_address": token_address,
                "activity_type": signal.type.value if signal else None,
                "whale_count": signal.whale_count if signal else None,
                "total_value": signal.total_value if signal else None,
                "confidence": signal.confidence if signal else None,
                "timestamp": int(time.time())
            })
            return signal
        
        return None

    async def _analyze_whale_trading_patterns(self, token_address: str, top_traders: List, volume_24h: float, scan_id: Optional[str] = None) -> Optional[WhaleSignal]:
        """Analyze recent trading patterns for whale activity"""
        if not top_traders:
            return None
        
        whale_traders = []
        whale_trading_volume = 0
        
        for trader in top_traders[:15]:  # Check top 15 traders
            trader_address = trader.get('owner', trader) if isinstance(trader, dict) else trader
            
            if trader_address in self.whale_database:
                whale_info = self.whale_database[trader_address]
                whale_traders.append({
                    'address': trader_address,
                    'info': whale_info,
                    'estimated_volume': volume_24h / len(top_traders)  # Rough estimate
                })
                whale_trading_volume += volume_24h / len(top_traders)
        
        if len(whale_traders) >= 2:  # Multiple known whales trading
            # Calculate confidence based on whale quality and volume
            total_success_rate = sum(w['info']['success_rate'] for w in whale_traders)
            avg_success_rate = total_success_rate / len(whale_traders)
            
            confidence = min(1.0, avg_success_rate * len(whale_traders) / 3)
            
            if confidence >= self.thresholds['min_confidence_threshold']:
                score_impact = int(12 + confidence * 8)  # +12 to +20 bonus
                
                signal = WhaleSignal(
                    type=WhaleActivityType.SMART_MONEY_ENTRY,
                    confidence=confidence,
                    score_impact=score_impact,
                    whale_count=len(whale_traders),
                    total_value=whale_trading_volume,
                    timeframe="24h_trading",
                    details=f"{len(whale_traders)} known whales actively trading",
                    whale_addresses=[w['address'] for w in whale_traders]
                )
                
                self.structured_logger.info({
                    "event": "whale_trading_pattern_detected",
                    "scan_id": scan_id,
                    "token_address": token_address,
                    "activity_type": signal.type.value if signal else None,
                    "whale_count": signal.whale_count if signal else None,
                    "total_value": signal.total_value if signal else None,
                    "confidence": signal.confidence if signal else None,
                    "timestamp": int(time.time())
                })
                return signal
        
        return None

    async def _detect_institutional_flows(self, token_address: str, token_data: Dict, scan_id: Optional[str] = None) -> Optional[WhaleSignal]:
        """Detect institutional-scale flows"""
        volume_24h = token_data.get('volume_24h', 0)
        market_cap = token_data.get('market_cap', 0)
        unique_traders = token_data.get('unique_trader_count', 0)
        
        # Look for institutional-scale activity patterns
        if (volume_24h >= self.thresholds['institutional_usd'] and 
            market_cap > 0 and unique_traders > 0):
            
            # Calculate average trade size
            avg_trade_size = volume_24h / unique_traders if unique_traders > 0 else 0
            
            # Institutional pattern: High volume, large average trades, moderate trader count
            if (avg_trade_size >= self.thresholds['large_transaction_usd'] and
                unique_traders >= 10 and unique_traders <= 50):  # Sweet spot for institutional
                
                confidence = min(1.0, avg_trade_size / self.thresholds['whale_transaction_usd'])
                score_impact = int(18 + confidence * 7)  # +18 to +25 bonus
                
                signal = WhaleSignal(
                    type=WhaleActivityType.INSTITUTIONAL_FLOW,
                    confidence=confidence,
                    score_impact=score_impact,
                    whale_count=unique_traders,
                    total_value=volume_24h,
                    timeframe="24h_flows",
                    details=f"Institutional flow detected: ${avg_trade_size:,.0f} avg trade",
                    whale_addresses=[]  # Don't have specific addresses
                )
                
                self.structured_logger.info({
                    "event": "institutional_flow_detected",
                    "scan_id": scan_id,
                    "token_address": token_address,
                    "activity_type": signal.type.value if signal else None,
                    "whale_count": signal.whale_count if signal else None,
                    "total_value": signal.total_value if signal else None,
                    "confidence": signal.confidence if signal else None,
                    "timestamp": int(time.time())
                })
                return signal
        
        return None

    async def _analyze_smart_money_timing(self, token_address: str, token_data: Dict, scan_id: Optional[str] = None) -> Optional[WhaleSignal]:
        """Analyze timing of smart money entry"""
        creation_time = token_data.get('creation_time')
        holders_data = token_data.get('holders_data', {})
        
        if not creation_time or not holders_data:
            return None
        
        current_time = time.time()
        token_age_hours = (current_time - creation_time) / 3600
        
        # Look for early smart money entry (within first 24-72 hours)
        if 1 <= token_age_hours <= 72:  # Sweet spot for early entry
            items = holders_data.get('items', [])
            early_smart_money = []
            
            for holder in items[:10]:  # Check top 10 for early smart money
                if not isinstance(holder, dict):
                    continue
                    
                owner = holder.get('owner', '')
                if owner in self.whale_database:
                    whale_info = self.whale_database[owner]
                    if whale_info.get('known_for') in ['early_entry', 'early_adoption']:
                        early_smart_money.append(owner)
            
            if len(early_smart_money) >= 1:  # At least one early adopter whale
                # Higher bonus for earlier entry
                timing_multiplier = max(0.5, (72 - token_age_hours) / 72)
                confidence = min(1.0, len(early_smart_money) / 3 * timing_multiplier)
                
                score_impact = int(10 + confidence * 10 + timing_multiplier * 5)  # +10 to +25
                
                signal = WhaleSignal(
                    type=WhaleActivityType.SMART_MONEY_ENTRY,
                    confidence=confidence,
                    score_impact=score_impact,
                    whale_count=len(early_smart_money),
                    total_value=0,  # Don't have specific values
                    timeframe=f"{token_age_hours:.1f}h_after_launch",
                    details=f"{len(early_smart_money)} early-entry whales detected",
                    whale_addresses=early_smart_money
                )
                
                self.structured_logger.info({
                    "event": "smart_money_timing_detected",
                    "scan_id": scan_id,
                    "token_address": token_address,
                    "activity_type": signal.type.value if signal else None,
                    "whale_count": signal.whale_count if signal else None,
                    "total_value": signal.total_value if signal else None,
                    "confidence": signal.confidence if signal else None,
                    "timestamp": int(time.time())
                })
                return signal
        
        return None

    async def _detect_coordinated_whale_activity(self, token_address: str, holders_data: Dict, top_traders: List, scan_id: Optional[str] = None) -> Optional[WhaleSignal]:
        """Detect coordinated whale buying/accumulation"""
        if not holders_data and not top_traders:
            return None
        
        # Combine holder and trader data to find whale coordination
        all_whale_addresses = set()
        
        # Check holders for whales
        items = holders_data.get('items', []) if holders_data else []
        for holder in items[:15]:
            if isinstance(holder, dict):
                owner = holder.get('owner', '')
                # Ensure owner is a string, not a dict
                if isinstance(owner, str) and owner and owner in self.whale_database:
                    all_whale_addresses.add(owner)  # Add string address, not dict
        
        # Check traders for whales - ENHANCED address extraction with bulletproof type checking
        for trader in top_traders[:15] if top_traders else []:
            trader_address = None
            
            try:
                # Case 1: trader is already a string address
                if isinstance(trader, str) and len(trader) > 20:  # Valid Solana address length
                    trader_address = trader
                
                # Case 2: trader is a dict with address field
                elif isinstance(trader, dict):
                    # Try multiple possible fields for the address, with strict type checking
                    potential_fields = ['owner', 'address', 'wallet', 'user', 'trader', 'wallet_address', 'account']
                    
                    for field in potential_fields:
                        field_value = trader.get(field)
                        
                        # Only accept string values, reject nested dicts/objects
                        if isinstance(field_value, str) and len(field_value) > 20:
                            trader_address = field_value
                            break
                        
                        # If field_value is a dict, try to extract address from it
                        elif isinstance(field_value, dict) and 'address' in field_value:
                            nested_address = field_value.get('address')
                            if isinstance(nested_address, str) and len(nested_address) > 20:
                                trader_address = nested_address
                                break
                
                # Case 3: trader is some other type - convert to string carefully
                elif trader is not None:
                    str_trader = str(trader)
                    # Only use if it looks like a valid address
                    if len(str_trader) > 20 and not str_trader.startswith('<') and not str_trader.startswith('{'):
                        trader_address = str_trader
                
                # Final validation: ensure we have a valid string address
                if trader_address and isinstance(trader_address, str) and len(trader_address) > 20:
                    # Check if this is a known whale
                    if trader_address in self.whale_database:
                        all_whale_addresses.add(trader_address)  # Safe to add string to set
                        self.logger.debug(f"Found whale trader: {trader_address[:8]}...")
                
            except Exception as e:
                # Enhanced error logging with trader type info
                trader_type = type(trader).__name__
                trader_preview = str(trader)[:50] if trader else "None"
                self.logger.warning(f"Error extracting trader address from {trader_type}: {e} | Preview: {trader_preview}")
                continue
        
        # Check for coordination (multiple whales in both holders and traders)
        if len(all_whale_addresses) >= self.thresholds['coordinated_whale_count']:
            # Calculate coordination strength based on whale quality
            total_success_rate = 0
            whale_tiers = []
            
            for whale_addr in all_whale_addresses:
                whale_info = self.whale_database[whale_addr]
                total_success_rate += whale_info['success_rate']
                whale_tiers.append(whale_info['tier'])
            
            avg_success_rate = total_success_rate / len(all_whale_addresses)
            avg_tier = sum(whale_tiers) / len(whale_tiers)
            
            confidence = min(1.0, avg_success_rate * len(all_whale_addresses) / 5)
            
            # Higher bonus for better quality whale coordination
            tier_bonus = max(0, (3 - avg_tier) * 3)  # Tier 1 whales get +6, Tier 3 get +0
            score_impact = int(15 + confidence * 8 + tier_bonus)  # +15 to +29 bonus
            
            self.logger.info(f"[WHALE] {token_address[:8]} - Coordinated activity: {len(all_whale_addresses)} whales")
            
            signal = WhaleSignal(
                type=WhaleActivityType.COORDINATED_BUY,
                confidence=confidence,
                score_impact=min(25, score_impact),  # Cap at +25
                whale_count=len(all_whale_addresses),
                total_value=0,  # Don't have aggregate value
                timeframe="current_positions",
                details=f"{len(all_whale_addresses)} whales coordinating (avg tier {avg_tier:.1f})",
                whale_addresses=list(all_whale_addresses)  # Convert set to list for JSON serialization
            )
            
            self.structured_logger.info({
                "event": "coordinated_whale_activity_detected",
                "scan_id": scan_id,
                "token_address": token_address,
                "activity_type": signal.type.value if signal else None,
                "whale_count": signal.whale_count if signal else None,
                "total_value": signal.total_value if signal else None,
                "confidence": signal.confidence if signal else None,
                "timestamp": int(time.time())
            })
            return signal
        
        return None

    def _combine_whale_signals(self, signals: List[WhaleSignal], token_symbol: str) -> WhaleSignal:
        """Combine multiple whale signals into a single comprehensive signal"""
        if not signals:
            # Return neutral signal if no whale activity detected
            return WhaleSignal(
                type=WhaleActivityType.ACCUMULATION,
                confidence=0.0,
                score_impact=0,
                whale_count=0,
                total_value=0,
                timeframe="no_activity",
                details="No significant whale activity detected",
                whale_addresses=[]
            )
        
        # If only one signal, return it directly
        if len(signals) == 1:
            return signals[0]
        
        # Combine multiple signals - take the strongest positive signal
        best_signal = max(signals, key=lambda s: s.score_impact)
        
        # Aggregate data from all signals
        total_whales = sum(s.whale_count for s in signals)
        total_value = sum(s.total_value for s in signals)
        all_addresses = []
        for s in signals:
            all_addresses.extend(s.whale_addresses)
        unique_addresses = list(set(all_addresses))
        
        # Boost confidence and score for multiple confirmations
        confirmation_bonus = min(5, len(signals) - 1)  # +1 to +5 bonus per additional signal
        
        combined_signal = WhaleSignal(
            type=best_signal.type,
            confidence=min(1.0, best_signal.confidence + len(signals) * 0.1),
            score_impact=min(25, best_signal.score_impact + confirmation_bonus),
            whale_count=max(total_whales, len(unique_addresses)),
            total_value=total_value,
            timeframe="multiple_timeframes",
            details=f"Multiple whale signals: {best_signal.details} (+{confirmation_bonus} confirmation bonus)",
            whale_addresses=unique_addresses
        )
        
        self.logger.info(f"[WHALE] {token_symbol} - Combined {len(signals)} signals into final assessment")
        return combined_signal

    def get_whale_activity_grade(self, signal: WhaleSignal) -> str:
        """Get letter grade for whale activity strength"""
        if signal.score_impact >= 20:
            return "A+"  # Exceptional whale activity
        elif signal.score_impact >= 15:
            return "A"   # Strong whale activity
        elif signal.score_impact >= 10:
            return "B+"  # Good whale activity
        elif signal.score_impact >= 5:
            return "B"   # Moderate whale activity
        elif signal.score_impact >= 0:
            return "C"   # Neutral/No activity
        elif signal.score_impact >= -10:
            return "D"   # Negative whale activity
        else:
            return "F"   # Strong distribution/dumping 