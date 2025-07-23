#!/usr/bin/env python3
"""
Enhanced Pump and Dump Detection Service

Advanced pattern recognition with trading opportunity identification:
- Distinguishes between pump opportunities and dump warnings
- Provides entry/exit signals for riding artificial pumps
- Implements phase detection (early pump, peak pump, dump start, dump continuation)
"""

import time
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PumpDumpSignal:
    """Represents a pump and dump risk signal"""
    signal_type: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    confidence: float  # 0.0 to 1.0
    description: str
    data_points: Dict[str, Any]
    trading_action: str = 'NEUTRAL'  # 'BUY_OPPORTUNITY', 'SELL_WARNING', 'HOLD', 'AVOID'


@dataclass
class TradingOpportunity:
    """Represents a trading opportunity with entry/exit signals"""
    opportunity_type: str  # 'EARLY_PUMP', 'MOMENTUM_PUMP', 'DUMP_EXIT'
    action: str  # 'ENTER', 'EXIT', 'MONITOR'
    confidence: float
    risk_level: str
    estimated_profit_potential: float  # Percentage
    max_hold_time_minutes: int
    stop_loss_percentage: float
    take_profit_percentage: float
    reasoning: str


class EnhancedPumpDumpDetector:
    """
    Enhanced pump and dump detection with trading opportunity identification.
    
    Key enhancements:
    - Distinguishes between pump (positive) and dump (negative) movements
    - Identifies trading phases: Early Pump, Peak Pump, Dump Start, Dump Continuation
    - Provides entry/exit signals for profitable pump trading
    - Risk-adjusted position sizing recommendations
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        
        # Pump opportunity thresholds (positive movements)
        self.PUMP_OPPORTUNITY_THRESHOLDS = {
            'early_pump_1h': 50.0,        # >50% gain in 1h = early pump opportunity
            'momentum_pump_1h': 150.0,     # >150% gain in 1h = momentum opportunity
            'extreme_pump_1h': 300.0,      # >300% gain in 1h = extreme (exit soon)
            
            'early_pump_4h': 100.0,       # >100% gain in 4h = early pump
            'momentum_pump_4h': 300.0,     # >300% gain in 4h = momentum
            'extreme_pump_4h': 600.0,      # >600% gain in 4h = extreme
            
            'early_pump_24h': 200.0,      # >200% gain in 24h = early pump
            'momentum_pump_24h': 500.0,    # >500% gain in 24h = momentum
            'extreme_pump_24h': 1000.0,    # >1000% gain in 24h = extreme
        }
        
        # Dump warning thresholds (negative movements)
        self.DUMP_WARNING_THRESHOLDS = {
            'moderate_dump_1h': -30.0,     # >30% drop in 1h = moderate dump
            'severe_dump_1h': -50.0,       # >50% drop in 1h = severe dump
            'crash_dump_1h': -70.0,        # >70% drop in 1h = crash
            
            'moderate_dump_4h': -40.0,     # >40% drop in 4h = moderate dump
            'severe_dump_4h': -60.0,       # >60% drop in 4h = severe dump
            'crash_dump_4h': -80.0,        # >80% drop in 4h = crash
        }
        
        # Volume sustainability thresholds
        self.VOLUME_THRESHOLDS = {
            'low_volume_pump': 5.0,        # Volume <5x market cap during pump = risky
            'sustainable_volume': 10.0,    # Volume 10-20x market cap = sustainable
            'excessive_volume': 50.0,      # Volume >50x market cap = manipulation
        }
    
    def analyze_token(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced pump and dump analysis with detailed pattern recognition.
        
        Args:
            token_data: Dictionary containing token metrics
            
        Returns:
            Dictionary with comprehensive pump/dump analysis
        """
        try:
            token_symbol = token_data.get('token_symbol', 'UNKNOWN')
            self.logger.debug(f"[PUMP_DUMP] Starting enhanced analysis for {token_symbol}")
            
            # Debug: Log input data sample
            self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Input data analysis:")
            self.logger.debug(f"  - Price change 1h: {token_data.get('price_change_1h_percent', 'N/A')}%")
            self.logger.debug(f"  - Price change 4h: {token_data.get('price_change_4h_percent', 'N/A')}%")
            self.logger.debug(f"  - Price change 24h: {token_data.get('price_change_24h_percent', 'N/A')}%")
            self.logger.debug(f"  - Volume 24h: ${token_data.get('volume_24h', 0):,.0f}")
            self.logger.debug(f"  - Market cap: ${token_data.get('market_cap', 0):,.0f}")
            self.logger.debug(f"  - Unique traders: {token_data.get('unique_trader_count', 0)}")
            
            # Initialize analysis result
            analysis = {
                'overall_risk_level': 'LOW',
                'risk_score': 0.0,
                'pump_indicators': {},
                'dump_indicators': {},
                'manipulation_signals': {},
                'time_pattern_analysis': {},
                'volume_price_analysis': {},
                'trader_behavior_analysis': {},
                'recommendation': 'MONITOR',
                'warning_flags': [],
                'detailed_breakdown': {}
            }
            
            # Extract key metrics for analysis
            price_1h = float(token_data.get('price_change_1h_percent', 0))
            price_4h = float(token_data.get('price_change_4h_percent', 0)) 
            price_24h = float(token_data.get('price_change_24h_percent', 0))
            volume_24h = float(token_data.get('volume_24h', 0))
            volume_1h = float(token_data.get('volume_1h', 0))
            volume_4h = float(token_data.get('volume_4h', 0))
            market_cap = float(token_data.get('market_cap', 0))
            unique_traders = int(token_data.get('unique_trader_count', 0))
            trade_count = int(token_data.get('trade_count_24h', 0))
            creation_time = token_data.get('creation_time')
            
            # Calculate token age if creation time is available
            token_age_hours = 0
            if creation_time:
                import time
                current_time = time.time()
                token_age_hours = (current_time - creation_time) / 3600
                self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Token age: {token_age_hours:.1f} hours")
            
            # 1. PUMP PATTERN ANALYSIS
            self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Analyzing pump patterns...")
            
            pump_score = 0
            pump_details = {}
            
            # 1a. ENHANCED Extreme price acceleration (multiple timeframes)
            # Special detection for cases like TDCCP (750,000% gains)
            if price_24h > 10000:  # >10,000% gain = EXTREME PUMP
                pump_score += 50
                pump_details['extreme_mega_pump'] = f"EXTREME PUMP: {price_24h:+.1f}% in 24h"
                analysis['warning_flags'].append('EXTREME_PRICE_MOVEMENT')
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - EXTREME MEGA PUMP DETECTED: {price_24h:+.1f}%")
            elif price_24h > 1000:  # >1,000% gain = MEGA PUMP
                pump_score += 40
                pump_details['mega_pump'] = f"MEGA PUMP: {price_24h:+.1f}% in 24h"
                analysis['warning_flags'].append('EXTREME_PRICE_MOVEMENT')
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - MEGA PUMP DETECTED: {price_24h:+.1f}%")
            elif price_24h > 500:  # >500% gain = MASSIVE PUMP
                pump_score += 35
                pump_details['massive_pump'] = f"MASSIVE PUMP: {price_24h:+.1f}% in 24h"
                analysis['warning_flags'].append('EXTREME_PRICE_MOVEMENT')
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - MASSIVE PUMP DETECTED: {price_24h:+.1f}%")
            elif price_24h > 200:  # >200% gain = MAJOR PUMP
                pump_score += 30
                pump_details['major_pump'] = f"MAJOR PUMP: {price_24h:+.1f}% in 24h"
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - MAJOR PUMP DETECTED: {price_24h:+.1f}%")
            elif price_24h > 100:  # >100% gain = PUMP
                pump_score += 25
                pump_details['pump_detected'] = f"PUMP: {price_24h:+.1f}% in 24h"
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - PUMP DETECTED: {price_24h:+.1f}%")
            
            # Shorter timeframe extreme movements
            if price_1h > 500:  # >500% in 1 hour = CRITICAL
                pump_score += 40
                pump_details['extreme_1h_pump'] = f"CRITICAL: {price_1h:+.1f}% in 1 hour"
                analysis['warning_flags'].append('EXTREME_PRICE_MOVEMENT')
                self.logger.critical(f"[PUMP_DUMP] {token_symbol} - CRITICAL 1h pump detected: {price_1h:+.1f}%")
            elif price_1h > 200:  # >200% in 1 hour = EXTREME
                pump_score += 30
                pump_details['extreme_1h_pump'] = f"EXTREME: {price_1h:+.1f}% in 1 hour"
                analysis['warning_flags'].append('EXTREME_PRICE_MOVEMENT')
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Extreme 1h pump detected: {price_1h:+.1f}%")
            elif price_1h > 100:  # >100% in 1 hour
                pump_score += 25
                pump_details['extreme_1h_pump'] = f"{price_1h:+.1f}% in 1 hour"
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Extreme 1h pump detected: {price_1h:+.1f}%")
            elif price_1h > 50:  # >50% in 1 hour
                pump_score += 15
                pump_details['high_1h_pump'] = f"{price_1h:+.1f}% in 1 hour"
                self.logger.debug(f"[PUMP_DUMP] {token_symbol} - High 1h pump detected: {price_1h:+.1f}%")
            elif price_1h > 20:  # >20% in 1 hour
                pump_score += 10
                pump_details['moderate_1h_pump'] = f"{price_1h:+.1f}% in 1 hour"
                self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Moderate 1h pump detected: {price_1h:+.1f}%")
            
            # Enhanced acceleration detection (pump pattern)
            if price_1h > price_4h * 2 and price_4h > price_24h * 0.1 and price_1h > 50:
                acceleration_penalty = 25
                pump_score += acceleration_penalty
                pump_details['acceleration_pattern'] = f"Classic pump acceleration: 1h={price_1h:+.1f}% >> 4h={price_4h:+.1f}% >> 24h={price_24h:+.1f}%"
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - ACCELERATION PATTERN DETECTED: 1h={price_1h:+.1f}% >> 4h={price_4h:+.1f}% >> 24h={price_24h:+.1f}%")
            elif price_1h > price_4h * 1.5 and price_4h > 0:  # 1h gain is 1.5x the 4h gain
                pump_score += 15
                pump_details['price_acceleration'] = f"1h gain ({price_1h:+.1f}%) >> 4h gain ({price_4h:+.1f}%)"
                self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Price acceleration detected: 1h={price_1h:+.1f}% vs 4h={price_4h:+.1f}%")
            
            # 1b. Enhanced Volume surge analysis
            volume_surge_score = 0
            if volume_1h > 0 and volume_24h > 0:
                hourly_avg_volume = volume_24h / 24
                volume_surge_ratio = volume_1h / hourly_avg_volume if hourly_avg_volume > 0 else 0
                
                if volume_surge_ratio > 50:  # 50x normal volume = EXTREME
                    volume_surge_score = 35
                    pump_details['extreme_volume_surge'] = f"EXTREME: {volume_surge_ratio:.1f}x normal volume"
                    analysis['warning_flags'].append('VOLUME_MANIPULATION')
                    self.logger.critical(f"[PUMP_DUMP] {token_symbol} - EXTREME volume surge: {volume_surge_ratio:.1f}x normal")
                elif volume_surge_ratio > 20:  # 20x normal volume = CRITICAL
                    volume_surge_score = 30
                    pump_details['critical_volume_surge'] = f"CRITICAL: {volume_surge_ratio:.1f}x normal volume"
                    analysis['warning_flags'].append('VOLUME_MANIPULATION')
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Critical volume surge: {volume_surge_ratio:.1f}x normal")
                elif volume_surge_ratio > 10:  # 10x normal volume
                    volume_surge_score = 20
                    pump_details['extreme_volume_surge'] = f"{volume_surge_ratio:.1f}x normal volume"
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Extreme volume surge: {volume_surge_ratio:.1f}x normal")
                elif volume_surge_ratio > 5:  # 5x normal volume
                    volume_surge_score = 15
                    pump_details['high_volume_surge'] = f"{volume_surge_ratio:.1f}x normal volume"
                    self.logger.debug(f"[PUMP_DUMP] {token_symbol} - High volume surge: {volume_surge_ratio:.1f}x normal")
                elif volume_surge_ratio > 2:  # 2x normal volume
                    volume_surge_score = 10
                    pump_details['moderate_volume_surge'] = f"{volume_surge_ratio:.1f}x normal volume"
                    self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Moderate volume surge: {volume_surge_ratio:.1f}x normal")
            
            pump_score += volume_surge_score
            
            # 1c. ENHANCED Market cap vs volume relationship (suspicious if volume >> market cap)
            if market_cap > 0 and volume_24h > 0:
                volume_to_mcap_ratio = volume_24h / market_cap
                if volume_to_mcap_ratio > 50:  # Volume > 50x market cap (EXTREME manipulation)
                    pump_score += 40
                    pump_details['extreme_volume_ratio'] = f"EXTREME MANIPULATION: Volume {volume_to_mcap_ratio:.1f}x market cap"
                    analysis['warning_flags'].append('VOLUME_MANIPULATION')
                    self.logger.critical(f"[PUMP_DUMP] {token_symbol} - EXTREME volume manipulation: {volume_to_mcap_ratio:.1f}x market cap")
                elif volume_to_mcap_ratio > 20:  # Volume > 20x market cap (CRITICAL manipulation)
                    pump_score += 30
                    pump_details['critical_volume_ratio'] = f"CRITICAL MANIPULATION: Volume {volume_to_mcap_ratio:.1f}x market cap"
                    analysis['warning_flags'].append('VOLUME_MANIPULATION')
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Critical volume manipulation: {volume_to_mcap_ratio:.1f}x market cap")
                elif volume_to_mcap_ratio > 10:  # Volume > 10x market cap (HIGH manipulation)
                    pump_score += 25
                    pump_details['high_volume_ratio'] = f"HIGH MANIPULATION: Volume {volume_to_mcap_ratio:.1f}x market cap"
                    analysis['warning_flags'].append('VOLUME_MANIPULATION')
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - High volume manipulation: {volume_to_mcap_ratio:.1f}x market cap")
                elif volume_to_mcap_ratio > 5:  # Volume > 5x market cap (suspicious)
                    pump_score += 20
                    pump_details['excessive_volume_ratio'] = f"Volume {volume_to_mcap_ratio:.1f}x market cap"
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Excessive volume ratio: {volume_to_mcap_ratio:.1f}x market cap")
                elif volume_to_mcap_ratio > 2:  # Volume > 2x market cap (suspicious)
                    pump_score += 10
                    pump_details['high_volume_ratio'] = f"Volume {volume_to_mcap_ratio:.1f}x market cap"
                    self.logger.debug(f"[PUMP_DUMP] {token_symbol} - High volume ratio: {volume_to_mcap_ratio:.1f}x market cap")
            
            analysis['pump_indicators'] = {
                'score': pump_score,
                'details': pump_details
            }
            
            # 2. DUMP PATTERN ANALYSIS
            self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Analyzing dump patterns...")
            
            dump_score = 0
            dump_details = {}
            
            # 2a. Enhanced Price crash patterns
            if price_1h < -70:  # >70% drop in 1 hour = EXTREME CRASH
                dump_score += 40
                dump_details['extreme_crash'] = f"EXTREME CRASH: {price_1h:+.1f}% in 1 hour"
                analysis['warning_flags'].append('EXTREME_PRICE_MOVEMENT')
                self.logger.critical(f"[PUMP_DUMP] {token_symbol} - EXTREME crash detected: {price_1h:+.1f}%")
            elif price_1h < -50:  # >50% drop in 1 hour = SEVERE CRASH
                dump_score += 30
                dump_details['severe_crash'] = f"SEVERE CRASH: {price_1h:+.1f}% in 1 hour"
                analysis['warning_flags'].append('EXTREME_PRICE_MOVEMENT')
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Severe crash detected: {price_1h:+.1f}%")
            elif price_1h < -30:  # >30% drop in 1 hour
                dump_score += 25
                dump_details['extreme_1h_crash'] = f"{price_1h:+.1f}% in 1 hour"
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Extreme 1h crash detected: {price_1h:+.1f}%")
            elif price_1h < -15:  # >15% drop in 1 hour
                dump_score += 15
                dump_details['high_1h_crash'] = f"{price_1h:+.1f}% in 1 hour"
                self.logger.debug(f"[PUMP_DUMP] {token_symbol} - High 1h crash detected: {price_1h:+.1f}%")
            
            # Enhanced dump after pump detection (classic pattern)
            if price_24h > 1000 and price_1h < -30:  # Mega pump followed by crash
                dump_score += 35
                dump_details['mega_pump_crash'] = f"MEGA PUMP CRASH: 24h={price_24h:+.1f}%, 1h={price_1h:+.1f}%"
                analysis['warning_flags'].append('PUMP_DUMP_PATTERN')
                self.logger.critical(f"[PUMP_DUMP] {token_symbol} - MEGA PUMP CRASH PATTERN: 24h={price_24h:+.1f}%, 1h={price_1h:+.1f}%")
            elif price_24h > 500 and price_1h < -20:  # Massive pump followed by crash
                dump_score += 30
                dump_details['massive_pump_crash'] = f"MASSIVE PUMP CRASH: 24h={price_24h:+.1f}%, 1h={price_1h:+.1f}%"
                analysis['warning_flags'].append('PUMP_DUMP_PATTERN')
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - MASSIVE PUMP CRASH PATTERN: 24h={price_24h:+.1f}%, 1h={price_1h:+.1f}%")
            elif price_24h > 100 and price_1h < -15:  # Strong pump followed by dump
                dump_score += 25
                dump_details['pump_dump_pattern'] = f"PUMP DUMP: 24h={price_24h:+.1f}%, 1h={price_1h:+.1f}%"
                analysis['warning_flags'].append('PUMP_DUMP_PATTERN')
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - PUMP DUMP PATTERN: 24h={price_24h:+.1f}%, 1h={price_1h:+.1f}%")
            elif price_24h > 50 and price_1h < -10:  # Strong 24h gain but recent crash
                dump_score += 20
                dump_details['dump_after_pump'] = f"24h: {price_24h:+.1f}%, 1h: {price_1h:+.1f}%"
                self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Dump after pump pattern: 24h={price_24h:+.1f}%, 1h={price_1h:+.1f}%")
            
            # 2b. Volume analysis during dumps
            if price_1h < -10 and volume_1h > 0:  # Price crash with volume
                if volume_surge_score > 20:  # High volume during crash = panic selling
                    dump_score += 20
                    dump_details['panic_selling'] = f"PANIC SELLING: {price_1h:+.1f}% with {volume_surge_score} volume score"
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Panic selling detected: {price_1h:+.1f}% with volume")
                elif volume_surge_score > 10:  # Moderate volume during crash
                    dump_score += 15
                    dump_details['panic_selling'] = f"High volume crash: {price_1h:+.1f}% with {volume_surge_score} volume score"
                    self.logger.debug(f"[PUMP_DUMP] {token_symbol} - High volume crash detected: {price_1h:+.1f}% with volume")
            
            analysis['dump_indicators'] = {
                'score': dump_score,
                'details': dump_details
            }
            
            # 3. ENHANCED MANIPULATION SIGNAL ANALYSIS
            self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Analyzing manipulation signals...")
            
            manipulation_score = 0
            manipulation_details = {}
            
            # 3a. Enhanced trader count analysis relative to volume
            if unique_traders > 0 and volume_24h > 0:
                volume_per_trader = volume_24h / unique_traders
                
                if volume_per_trader > 1000000:  # >$1M volume per trader = EXTREME
                    manipulation_score += 35
                    manipulation_details['extreme_volume_per_trader'] = f"EXTREME: ${volume_per_trader:,.0f} per trader"
                    analysis['warning_flags'].append('VOLUME_MANIPULATION')
                    self.logger.critical(f"[PUMP_DUMP] {token_symbol} - EXTREME volume per trader: ${volume_per_trader:,.0f}")
                elif volume_per_trader > 500000:  # >$500k volume per trader = CRITICAL
                    manipulation_score += 30
                    manipulation_details['critical_volume_per_trader'] = f"CRITICAL: ${volume_per_trader:,.0f} per trader"
                    analysis['warning_flags'].append('VOLUME_MANIPULATION')
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Critical volume per trader: ${volume_per_trader:,.0f}")
                elif volume_per_trader > 100000:  # >$100k volume per trader
                    manipulation_score += 20
                    manipulation_details['high_volume_per_trader'] = f"${volume_per_trader:,.0f} per trader"
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - High volume per trader: ${volume_per_trader:,.0f}")
                elif volume_per_trader > 50000:  # >$50k volume per trader
                    manipulation_score += 10
                    manipulation_details['moderate_volume_per_trader'] = f"${volume_per_trader:,.0f} per trader"
                    self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Moderate volume per trader: ${volume_per_trader:,.0f}")
            
            # 3b. Enhanced few traders analysis
            if volume_24h > 1000000 and unique_traders < 5:  # >$1M volume but <5 traders = EXTREME
                manipulation_score += 40
                manipulation_details['extreme_few_traders'] = f"EXTREME: Only {unique_traders} traders for ${volume_24h:,.0f} volume"
                analysis['warning_flags'].append('VOLUME_MANIPULATION')
                self.logger.critical(f"[PUMP_DUMP] {token_symbol} - EXTREME manipulation: {unique_traders} traders, ${volume_24h:,.0f}")
            elif volume_24h > 500000 and unique_traders < 5:  # >$500k volume but <5 traders = CRITICAL
                manipulation_score += 30
                manipulation_details['critical_few_traders'] = f"CRITICAL: Only {unique_traders} traders for ${volume_24h:,.0f} volume"
                analysis['warning_flags'].append('VOLUME_MANIPULATION')
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Critical manipulation: {unique_traders} traders, ${volume_24h:,.0f}")
            elif volume_24h > 100000 and unique_traders < 10:  # >$100k volume but <10 traders
                manipulation_score += 25
                manipulation_details['few_traders_high_volume'] = f"Only {unique_traders} traders for ${volume_24h:,.0f} volume"
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Few traders, high volume: {unique_traders} traders, ${volume_24h:,.0f}")
            elif volume_24h > 50000 and unique_traders < 5:  # >$50k volume but <5 traders
                manipulation_score += 20
                manipulation_details['very_few_traders'] = f"Only {unique_traders} traders for ${volume_24h:,.0f} volume"
                self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Very few traders: {unique_traders} traders, ${volume_24h:,.0f}")
            
            # 3c. Enhanced new token extreme moves analysis
            if token_age_hours > 0 and token_age_hours < 24:  # Less than 24 hours old
                if price_24h > 5000 or price_24h < -90:  # EXTREME moves on new token
                    manipulation_score += 30
                    manipulation_details['new_token_extreme_moves'] = f"EXTREME: {token_age_hours:.1f}h old with {price_24h:+.1f}% move"
                    analysis['warning_flags'].append('NEW_TOKEN_MANIPULATION')
                    self.logger.critical(f"[PUMP_DUMP] {token_symbol} - EXTREME new token manipulation: {token_age_hours:.1f}h old, {price_24h:+.1f}%")
                elif price_24h > 1000 or price_24h < -80:  # MAJOR moves on new token
                    manipulation_score += 25
                    manipulation_details['new_token_major_moves'] = f"MAJOR: {token_age_hours:.1f}h old with {price_24h:+.1f}% move"
                    analysis['warning_flags'].append('NEW_TOKEN_MANIPULATION')
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Major new token manipulation: {token_age_hours:.1f}h old, {price_24h:+.1f}%")
                elif price_24h > 500 or price_24h < -80:  # Extreme moves on new token
                    manipulation_score += 15
                    manipulation_details['new_token_extreme_moves'] = f"{token_age_hours:.1f}h old with {price_24h:+.1f}% move"
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - New token extreme moves: {token_age_hours:.1f}h old, {price_24h:+.1f}%")
            
            analysis['manipulation_signals'] = {
                'score': manipulation_score,
                'details': manipulation_details
            }
            
            # 4. TIME PATTERN ANALYSIS
            self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Analyzing time patterns...")
            
            time_pattern_score = 0
            time_pattern_details = {}
            
            # Check for unsustainable momentum patterns
            if price_1h > 0 and price_4h > 0 and price_24h > 0:
                # Calculate momentum sustainability
                momentum_1h = price_1h
                momentum_4h = price_4h / 4  # Hourly rate
                momentum_24h = price_24h / 24  # Hourly rate
                
                # If 1h momentum is way higher than longer-term rates (unsustainable)
                if momentum_1h > momentum_4h * 5 and momentum_1h > momentum_24h * 10:
                    time_pattern_score += 25
                    time_pattern_details['unsustainable_momentum'] = f"1h momentum ({momentum_1h:.1f}%) >> 4h rate ({momentum_4h:.1f}%) >> 24h rate ({momentum_24h:.1f}%)"
                    self.logger.warning(f"[PUMP_DUMP] {token_symbol} - Unsustainable momentum detected")
                elif momentum_1h > momentum_4h * 3 and momentum_1h > momentum_24h * 5:
                    time_pattern_score += 15
                    time_pattern_details['accelerating_momentum'] = f"Accelerating: 1h={momentum_1h:.1f}%, 4h_rate={momentum_4h:.1f}%, 24h_rate={momentum_24h:.1f}%"
                    self.logger.debug(f"[PUMP_DUMP] {token_symbol} - Accelerating momentum detected")
            
            analysis['time_pattern_analysis'] = {
                'score': time_pattern_score,
                'details': time_pattern_details
            }
            
            # 5. CALCULATE OVERALL RISK SCORE AND LEVEL
            total_score = pump_score + dump_score + manipulation_score + time_pattern_score
            
            # Normalize to 0-1 scale (adjusted for higher possible scores)
            max_possible_score = 200  # Increased due to enhanced scoring
            risk_score = min(1.0, total_score / max_possible_score)
            
            # Determine risk level with enhanced thresholds
            if risk_score >= 0.8 or total_score >= 100:
                risk_level = 'CRITICAL'
                recommendation = 'AVOID'
            elif risk_score >= 0.6 or total_score >= 75:
                risk_level = 'HIGH'
                recommendation = 'AVOID'
            elif risk_score >= 0.4 or total_score >= 50:
                risk_level = 'MEDIUM'
                recommendation = 'CAUTION'
            elif risk_score >= 0.2 or total_score >= 25:
                risk_level = 'LOW'
                recommendation = 'MONITOR'
            else:
                risk_level = 'MINIMAL'
                recommendation = 'MONITOR'
            
            # Update analysis with final results
            analysis.update({
                'overall_risk_level': risk_level,
                'risk_score': risk_score,
                'total_score': total_score,
                'recommendation': recommendation,
                'detailed_breakdown': {
                    'pump_score': pump_score,
                    'dump_score': dump_score,
                    'manipulation_score': manipulation_score,
                    'time_pattern_score': time_pattern_score,
                    'max_possible_score': max_possible_score
                }
            })
            
            # Log final analysis
            self.logger.info(f"[PUMP_DUMP] {token_symbol} - FINAL RISK ANALYSIS:")
            self.logger.info(f"  🔥 Pump Score: {pump_score}")
            self.logger.info(f"  📉 Dump Score: {dump_score}")
            self.logger.info(f"  🤖 Manipulation Score: {manipulation_score}")
            self.logger.info(f"  ⏱️  Time Pattern Score: {time_pattern_score}")
            self.logger.info(f"  📊 Total Score: {total_score}/{max_possible_score}")
            self.logger.info(f"  ⚠️  Risk Score: {risk_score:.3f}")
            self.logger.info(f"  🚨 Risk Level: {risk_level}")
            self.logger.info(f"  🎯 Recommendation: {recommendation}")
            self.logger.info(f"  🏷️  Warning Flags: {analysis['warning_flags']}")
            
            if risk_level in ['CRITICAL', 'HIGH']:
                self.logger.warning(f"[PUMP_DUMP] {token_symbol} - ⚠️  HIGH RISK TOKEN DETECTED - AVOID")
            
            # --- PHASE DETECTION LOGIC ---
            # Default values
            current_phase = 'NEUTRAL'
            phase_confidence = 0.0
            trading_opportunities = []
            profit_potential = 0.0
            # Use price and volume to determine phase
            if price_1h >= self.PUMP_OPPORTUNITY_THRESHOLDS['extreme_pump_1h']:
                current_phase = 'EXTREME_PUMP'
                phase_confidence = min(1.0, (price_1h - self.PUMP_OPPORTUNITY_THRESHOLDS['extreme_pump_1h']) / 200 + 0.8)
                trading_opportunities.append({
                    'opportunity_type': 'EXTREME_PUMP',
                    'action': 'EXIT',
                    'confidence': phase_confidence,
                    'risk_level': risk_level,
                    'estimated_profit_potential': -20.0,
                    'max_hold_time_minutes': 10,
                    'stop_loss_percentage': 10.0,
                    'take_profit_percentage': 0.0,
                    'reasoning': 'Extreme pump detected; exit recommended to avoid crash.'
                })
                profit_potential = -20.0
            elif price_1h >= self.PUMP_OPPORTUNITY_THRESHOLDS['momentum_pump_1h']:
                current_phase = 'MOMENTUM_PUMP'
                phase_confidence = min(1.0, (price_1h - self.PUMP_OPPORTUNITY_THRESHOLDS['momentum_pump_1h']) / 150 + 0.7)
                trading_opportunities.append({
                    'opportunity_type': 'MOMENTUM_PUMP',
                    'action': 'ENTER_HIGH_RISK',
                    'confidence': phase_confidence,
                    'risk_level': risk_level,
                    'estimated_profit_potential': 30.0,
                    'max_hold_time_minutes': 30,
                    'stop_loss_percentage': 15.0,
                    'take_profit_percentage': 20.0,
                    'reasoning': 'Momentum pump detected; high-risk scalp possible.'
                })
                profit_potential = 30.0
            elif price_1h >= self.PUMP_OPPORTUNITY_THRESHOLDS['early_pump_1h']:
                current_phase = 'EARLY_PUMP'
                phase_confidence = min(1.0, (price_1h - self.PUMP_OPPORTUNITY_THRESHOLDS['early_pump_1h']) / 100 + 0.6)
                trading_opportunities.append({
                    'opportunity_type': 'EARLY_PUMP',
                    'action': 'ENTER',
                    'confidence': phase_confidence,
                    'risk_level': risk_level,
                    'estimated_profit_potential': 50.0,
                    'max_hold_time_minutes': 60,
                    'stop_loss_percentage': 20.0,
                    'take_profit_percentage': 40.0,
                    'reasoning': 'Early pump detected; entry opportunity.'
                })
                profit_potential = 50.0
            elif price_1h <= self.DUMP_WARNING_THRESHOLDS['severe_dump_1h']:
                current_phase = 'DUMP_START'
                phase_confidence = min(1.0, abs(price_1h) / 100)
                trading_opportunities.append({
                    'opportunity_type': 'DUMP_START',
                    'action': 'EXIT',
                    'confidence': phase_confidence,
                    'risk_level': risk_level,
                    'estimated_profit_potential': -30.0,
                    'max_hold_time_minutes': 5,
                    'stop_loss_percentage': 10.0,
                    'take_profit_percentage': 0.0,
                    'reasoning': 'Severe dump detected; exit recommended.'
                })
                profit_potential = -30.0
            elif price_1h <= self.DUMP_WARNING_THRESHOLDS['moderate_dump_1h']:
                current_phase = 'DUMP_CONTINUATION'
                phase_confidence = min(1.0, abs(price_1h) / 60)
                trading_opportunities.append({
                    'opportunity_type': 'DUMP_CONTINUATION',
                    'action': 'AVOID',
                    'confidence': phase_confidence,
                    'risk_level': risk_level,
                    'estimated_profit_potential': -10.0,
                    'max_hold_time_minutes': 0,
                    'stop_loss_percentage': 0.0,
                    'take_profit_percentage': 0.0,
                    'reasoning': 'Ongoing dump detected; avoid entry.'
                })
                profit_potential = -10.0
            # Add to analysis output
            analysis['current_phase'] = current_phase
            analysis['phase_confidence'] = phase_confidence
            analysis['trading_opportunities'] = trading_opportunities
            analysis['profit_potential'] = profit_potential
            analysis['overall_risk'] = risk_level
            
            # --- SIGNALS OUTPUT ---
            signals = []
            # Pump signals
            for k, v in pump_details.items():
                if any(word in k.lower() or word in str(v).lower() for word in ['extreme', 'mega', 'critical']):
                    trading_action = 'AVOID'
                else:
                    trading_action = 'BUY_OPPORTUNITY'
                signals.append({
                    'type': 'PUMP',
                    'subtype': k,
                    'severity': 'HIGH' if 'extreme' in k or 'mega' in k or 'critical' in k else 'MEDIUM',
                    'description': v,
                    'stage': 'pump',
                    'trading_action': trading_action
                })
            # Dump signals
            for k, v in dump_details.items():
                if any(word in k.lower() or word in str(v).lower() for word in ['extreme', 'crash', 'panic', 'severe']):
                    trading_action = 'SELL_WARNING'
                else:
                    trading_action = 'AVOID'
                signals.append({
                    'type': 'DUMP',
                    'subtype': k,
                    'severity': 'HIGH' if 'extreme' in k or 'crash' in k or 'panic' in k or 'severe' in k else 'MEDIUM',
                    'description': v,
                    'stage': 'dump',
                    'trading_action': trading_action
                })
            # Manipulation signals
            for k, v in manipulation_details.items():
                signals.append({
                    'type': 'MANIPULATION',
                    'subtype': k,
                    'severity': 'HIGH' if 'extreme' in k or 'critical' in k else 'MEDIUM',
                    'description': v,
                    'stage': 'manipulation',
                    'trading_action': 'AVOID'
                })
            # Add warning flags as generic signals if not already present
            for flag in analysis['warning_flags']:
                if not any(flag in s['description'] for s in signals):
                    signals.append({
                        'type': 'WARNING_FLAG',
                        'subtype': flag,
                        'severity': 'HIGH' if 'EXTREME' in flag or 'CRITICAL' in flag else 'MEDIUM',
                        'description': flag,
                        'stage': 'flag',
                        'trading_action': 'AVOID'
                    })
            analysis['signals'] = signals
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"[PUMP_DUMP] Error analyzing token: {e}")
            return {
                'overall_risk_level': 'UNKNOWN',
                'risk_score': 0.5,  # Default to medium risk if analysis fails
                'pump_indicators': {},
                'dump_indicators': {},
                'manipulation_signals': {},
                'time_pattern_analysis': {},
                'volume_price_analysis': {},
                'trader_behavior_analysis': {},
                'recommendation': 'AVOID',  # Be conservative if analysis fails
                'warning_flags': ['ANALYSIS_ERROR'],
                'detailed_breakdown': {},
                'error': str(e)
            }

    def _calculate_pump_score(self, token_data: Dict[str, Any]) -> float:
        """Calculate pump pattern score with detailed logging."""
        try:
            token_symbol = token_data.get('token_symbol', 'UNKNOWN')
            self.logger.debug(f"[PUMP_SCORE] Calculating pump score for {token_symbol}")
            
            pump_score = 0.0
            score_details = {}
            
            # Price movement scoring
            price_change_1h = token_data.get('price_change_1h_percent', 0)
            price_change_4h = token_data.get('price_change_4h_percent', 0)
            price_change_24h = token_data.get('price_change_24h_percent', 0)
            
            # 1. Short-term price explosion (1 hour)
            if price_change_1h > 200:  # >200% in 1 hour
                pump_score += 40
                score_details['extreme_1h_pump'] = 40
                self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Extreme 1h pump: {price_change_1h:+.1f}% (+40 points)")
            elif price_change_1h > 100:  # >100% in 1 hour
                pump_score += 30
                score_details['high_1h_pump'] = 30
                self.logger.debug(f"[PUMP_SCORE] {token_symbol} - High 1h pump: {price_change_1h:+.1f}% (+30 points)")
            elif price_change_1h > 50:  # >50% in 1 hour
                pump_score += 20
                score_details['moderate_1h_pump'] = 20
                self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Moderate 1h pump: {price_change_1h:+.1f}% (+20 points)")
            elif price_change_1h > 20:  # >20% in 1 hour
                pump_score += 10
                score_details['mild_1h_pump'] = 10
                self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Mild 1h pump: {price_change_1h:+.1f}% (+10 points)")
            
            # 2. Medium-term pump (4 hour)
            if price_change_4h > 500:  # >500% in 4 hours
                pump_score += 25
                score_details['extreme_4h_pump'] = 25
                self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Extreme 4h pump: {price_change_4h:+.1f}% (+25 points)")
            elif price_change_4h > 200:  # >200% in 4 hours
                pump_score += 15
                score_details['high_4h_pump'] = 15
                self.logger.debug(f"[PUMP_SCORE] {token_symbol} - High 4h pump: {price_change_4h:+.1f}% (+15 points)")
            elif price_change_4h > 100:  # >100% in 4 hours
                pump_score += 10
                score_details['moderate_4h_pump'] = 10
                self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Moderate 4h pump: {price_change_4h:+.1f}% (+10 points)")
            
            # 3. Daily pump patterns
            if price_change_24h > 1000:  # >1000% in 24 hours
                pump_score += 20
                score_details['extreme_24h_pump'] = 20
                self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Extreme 24h pump: {price_change_24h:+.1f}% (+20 points)")
            elif price_change_24h > 500:  # >500% in 24 hours
                pump_score += 10
                score_details['high_24h_pump'] = 10
                self.logger.debug(f"[PUMP_SCORE] {token_symbol} - High 24h pump: {price_change_24h:+.1f}% (+10 points)")
            
            # 4. Volume analysis
            volume_24h = token_data.get('volume_24h', 0)
            volume_1h = token_data.get('volume_1h', 0)
            
            if volume_1h > 0 and volume_24h > 0:
                expected_hourly = volume_24h / 24
                volume_ratio = volume_1h / expected_hourly if expected_hourly > 0 else 0
                
                if volume_ratio > 20:  # 20x normal volume
                    pump_score += 20
                    score_details['extreme_volume_surge'] = 20
                    self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Extreme volume surge: {volume_ratio:.1f}x (+20 points)")
                elif volume_ratio > 10:  # 10x normal volume
                    pump_score += 15
                    score_details['high_volume_surge'] = 15
                    self.logger.debug(f"[PUMP_SCORE] {token_symbol} - High volume surge: {volume_ratio:.1f}x (+15 points)")
                elif volume_ratio > 5:  # 5x normal volume
                    pump_score += 10
                    score_details['moderate_volume_surge'] = 10
                    self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Moderate volume surge: {volume_ratio:.1f}x (+10 points)")
            
            # 5. Market cap vs volume relationship
            market_cap = token_data.get('market_cap', 0)
            if market_cap > 0 and volume_24h > 0:
                mcap_volume_ratio = volume_24h / market_cap
                if mcap_volume_ratio > 10:  # Volume >10x market cap
                    pump_score += 15
                    score_details['excessive_volume_ratio'] = 15
                    self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Excessive volume ratio: {mcap_volume_ratio:.1f}x (+15 points)")
                elif mcap_volume_ratio > 5:  # Volume >5x market cap
                    pump_score += 10
                    score_details['high_volume_ratio'] = 10
                    self.logger.debug(f"[PUMP_SCORE] {token_symbol} - High volume ratio: {mcap_volume_ratio:.1f}x (+10 points)")
            
            self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Total pump score: {pump_score:.1f}")
            self.logger.debug(f"[PUMP_SCORE] {token_symbol} - Score breakdown: {score_details}")
            
            return pump_score
            
        except Exception as e:
            self.logger.error(f"[PUMP_SCORE] Error calculating pump score: {e}")
            return 0.0

    def _calculate_dump_score(self, token_data: Dict[str, Any]) -> float:
        """Calculate dump pattern score with detailed logging."""
        try:
            token_symbol = token_data.get('token_symbol', 'UNKNOWN')
            self.logger.debug(f"[DUMP_SCORE] Calculating dump score for {token_symbol}")
            
            dump_score = 0.0
            score_details = {}
            
            # Price movement scoring
            price_change_1h = token_data.get('price_change_1h_percent', 0)
            price_change_4h = token_data.get('price_change_4h_percent', 0)
            price_change_24h = token_data.get('price_change_24h_percent', 0)
            
            # 1. Rapid price crashes
            if price_change_1h < -50:  # >50% drop in 1 hour
                dump_score += 40
                score_details['extreme_1h_crash'] = 40
                self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Extreme 1h crash: {price_change_1h:+.1f}% (+40 points)")
            elif price_change_1h < -30:  # >30% drop in 1 hour
                dump_score += 30
                score_details['high_1h_crash'] = 30
                self.logger.debug(f"[DUMP_SCORE] {token_symbol} - High 1h crash: {price_change_1h:+.1f}% (+30 points)")
            elif price_change_1h < -15:  # >15% drop in 1 hour
                dump_score += 20
                score_details['moderate_1h_crash'] = 20
                self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Moderate 1h crash: {price_change_1h:+.1f}% (+20 points)")
            elif price_change_1h < -10:  # >10% drop in 1 hour
                dump_score += 10
                score_details['mild_1h_crash'] = 10
                self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Mild 1h crash: {price_change_1h:+.1f}% (+10 points)")
            
            # 2. Post-pump dumps (classic pump and dump pattern)
            if price_change_24h > 200 and price_change_1h < -20:  # Big 24h gain but recent crash
                dump_score += 25
                score_details['post_pump_dump'] = 25
                self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Post-pump dump: 24h={price_change_24h:+.1f}%, 1h={price_change_1h:+.1f}% (+25 points)")
            elif price_change_24h > 100 and price_change_1h < -15:  # Moderate pump with crash
                dump_score += 15
                score_details['moderate_post_pump_dump'] = 15
                self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Moderate post-pump dump: 24h={price_change_24h:+.1f}%, 1h={price_change_1h:+.1f}% (+15 points)")
            
            # 3. Sustained crashes
            if price_change_4h < -60:  # >60% drop in 4 hours
                dump_score += 20
                score_details['sustained_4h_crash'] = 20
                self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Sustained 4h crash: {price_change_4h:+.1f}% (+20 points)")
            elif price_change_4h < -40:  # >40% drop in 4 hours
                dump_score += 15
                score_details['significant_4h_crash'] = 15
                self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Significant 4h crash: {price_change_4h:+.1f}% (+15 points)")
            
            # 4. Volume during dumps (panic selling indicator)
            volume_24h = token_data.get('volume_24h', 0)
            volume_1h = token_data.get('volume_1h', 0)
            
            if volume_1h > 0 and volume_24h > 0 and price_change_1h < -10:
                expected_hourly = volume_24h / 24
                volume_ratio = volume_1h / expected_hourly if expected_hourly > 0 else 0
                
                if volume_ratio > 10:  # High volume crash = panic selling
                    dump_score += 15
                    score_details['panic_selling'] = 15
                    self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Panic selling: {volume_ratio:.1f}x volume during {price_change_1h:+.1f}% crash (+15 points)")
                elif volume_ratio > 5:  # Moderate volume crash
                    dump_score += 10
                    score_details['moderate_panic_selling'] = 10
                    self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Moderate panic selling: {volume_ratio:.1f}x volume during {price_change_1h:+.1f}% crash (+10 points)")
            
            self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Total dump score: {dump_score:.1f}")
            self.logger.debug(f"[DUMP_SCORE] {token_symbol} - Score breakdown: {score_details}")
            
            return dump_score
            
        except Exception as e:
            self.logger.error(f"[DUMP_SCORE] Error calculating dump score: {e}")
            return 0.0

    def _analyze_manipulation_patterns(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market manipulation patterns with detailed logging."""
        try:
            token_symbol = token_data.get('token_symbol', 'UNKNOWN')
            self.logger.debug(f"[MANIPULATION] Analyzing manipulation patterns for {token_symbol}")
            
            manipulation_analysis = {
                'score': 0.0,
                'patterns': {},
                'trader_analysis': {},
                'volume_analysis': {},
                'timing_analysis': {}
            }
            
            manipulation_score = 0.0
            
            # 1. Trader concentration analysis
            unique_traders = token_data.get('unique_trader_count', 0)
            volume_24h = token_data.get('volume_24h', 0)
            trade_count = token_data.get('trade_count_24h', 0)
            
            if unique_traders > 0 and volume_24h > 0:
                volume_per_trader = volume_24h / unique_traders
                
                # Very high volume per trader suggests few big players
                if volume_per_trader > 200000:  # >$200k per trader
                    manipulation_score += 25
                    manipulation_analysis['trader_analysis']['high_volume_concentration'] = f"${volume_per_trader:,.0f} per trader"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - High volume concentration: ${volume_per_trader:,.0f} per trader (+25 points)")
                elif volume_per_trader > 100000:  # >$100k per trader
                    manipulation_score += 15
                    manipulation_analysis['trader_analysis']['moderate_volume_concentration'] = f"${volume_per_trader:,.0f} per trader"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - Moderate volume concentration: ${volume_per_trader:,.0f} per trader (+15 points)")
                
                # Very few traders for significant volume
                if volume_24h > 500000 and unique_traders < 10:  # >$500k with <10 traders
                    manipulation_score += 20
                    manipulation_analysis['trader_analysis']['few_big_traders'] = f"{unique_traders} traders for ${volume_24h:,.0f}"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - Few big traders: {unique_traders} traders for ${volume_24h:,.0f} (+20 points)")
                elif volume_24h > 100000 and unique_traders < 5:  # >$100k with <5 traders
                    manipulation_score += 25
                    manipulation_analysis['trader_analysis']['very_few_traders'] = f"{unique_traders} traders for ${volume_24h:,.0f}"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - Very few traders: {unique_traders} traders for ${volume_24h:,.0f} (+25 points)")
            
            # 2. Trade pattern analysis
            if trade_count > 0 and unique_traders > 0:
                trades_per_trader = trade_count / unique_traders
                
                if trades_per_trader > 100:  # >100 trades per trader (possible bot activity)
                    manipulation_score += 15
                    manipulation_analysis['trader_analysis']['high_trades_per_trader'] = f"{trades_per_trader:.1f} trades per trader"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - High trades per trader: {trades_per_trader:.1f} (+15 points)")
                elif trades_per_trader > 50:  # >50 trades per trader
                    manipulation_score += 10
                    manipulation_analysis['trader_analysis']['moderate_trades_per_trader'] = f"{trades_per_trader:.1f} trades per trader"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - Moderate trades per trader: {trades_per_trader:.1f} (+10 points)")
            
            # 3. Market cap vs volume analysis
            market_cap = token_data.get('market_cap', 0)
            if market_cap > 0 and volume_24h > 0:
                mcap_volume_ratio = volume_24h / market_cap
                
                if mcap_volume_ratio > 20:  # Volume >20x market cap (extremely suspicious)
                    manipulation_score += 30
                    manipulation_analysis['volume_analysis']['extreme_volume_ratio'] = f"{mcap_volume_ratio:.1f}x market cap"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - Extreme volume ratio: {mcap_volume_ratio:.1f}x market cap (+30 points)")
                elif mcap_volume_ratio > 10:  # Volume >10x market cap
                    manipulation_score += 20
                    manipulation_analysis['volume_analysis']['high_volume_ratio'] = f"{mcap_volume_ratio:.1f}x market cap"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - High volume ratio: {mcap_volume_ratio:.1f}x market cap (+20 points)")
                elif mcap_volume_ratio > 5:  # Volume >5x market cap
                    manipulation_score += 10
                    manipulation_analysis['volume_analysis']['suspicious_volume_ratio'] = f"{mcap_volume_ratio:.1f}x market cap"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - Suspicious volume ratio: {mcap_volume_ratio:.1f}x market cap (+10 points)")
            
            # 4. New token exploitation analysis
            creation_time = token_data.get('creation_time')
            if creation_time:
                import time
                token_age_hours = (time.time() - creation_time) / 3600
                
                price_change_24h = token_data.get('price_change_24h_percent', 0)
                
                # Very new token with extreme moves
                if token_age_hours < 6 and abs(price_change_24h) > 1000:  # <6h old with >1000% move
                    manipulation_score += 20
                    manipulation_analysis['timing_analysis']['new_token_extreme_move'] = f"{token_age_hours:.1f}h old, {price_change_24h:+.1f}% move"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - New token extreme move: {token_age_hours:.1f}h old, {price_change_24h:+.1f}% (+20 points)")
                elif token_age_hours < 24 and abs(price_change_24h) > 500:  # <24h old with >500% move
                    manipulation_score += 15
                    manipulation_analysis['timing_analysis']['young_token_big_move'] = f"{token_age_hours:.1f}h old, {price_change_24h:+.1f}% move"
                    self.logger.debug(f"[MANIPULATION] {token_symbol} - Young token big move: {token_age_hours:.1f}h old, {price_change_24h:+.1f}% (+15 points)")
            
            manipulation_analysis['score'] = manipulation_score
            
            self.logger.debug(f"[MANIPULATION] {token_symbol} - Total manipulation score: {manipulation_score:.1f}")
            
            return manipulation_analysis
            
        except Exception as e:
            self.logger.error(f"[MANIPULATION] Error analyzing manipulation patterns: {e}")
            return {'score': 0.0, 'patterns': {}, 'error': str(e)}


# Backwards compatibility - keep original class name as alias
PumpDumpDetector = EnhancedPumpDumpDetector 