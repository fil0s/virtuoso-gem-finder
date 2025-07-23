"""
Strategic Coordination Analyzer

This analyzer transforms manipulation detection into opportunity identification by:
- Detecting EARLY coordination by smart money (positive signal)
- Distinguishing quality coordination from retail pumps
- Using timing and actor quality to determine opportunity vs risk
- Converting "manipulation" patterns into actionable intelligence

Philosophy: "Hunt coordination opportunities, avoid manipulation traps"
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class CoordinationType(Enum):
    SMART_ACCUMULATION = "smart_accumulation"      # Grade A: Follow these
    INSTITUTIONAL_BUILD = "institutional_build"    # Grade A: Follow these  
    MOMENTUM_COORDINATION = "momentum_coordination" # Grade B: Consider these
    EARLY_COORDINATION = "early_coordination"      # Grade B: Consider these
    MIXED_SIGNALS = "mixed_signals"                # Grade C: Neutral
    RETAIL_PUMP = "retail_pump"                    # Grade D: Avoid these
    WASH_TRADING = "wash_trading"                  # Grade F: Avoid these

@dataclass
class CoordinationSignal:
    type: CoordinationType
    confidence: float  # 0.0 to 1.0
    score_impact: int  # -50 to +50 points
    details: str
    quality_factors: Dict[str, Any]
    timing_factor: float  # 0.0 to 1.0 (earlier = higher)

class StrategicCoordinationAnalyzer:
    """
    Analyzes coordination patterns to identify opportunities vs risks.
    
    Transforms traditional "manipulation detection" into strategic intelligence
    by focusing on ACTOR QUALITY and TIMING rather than just coordination itself.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Smart money wallet database (expandable)
        self.smart_money_wallets = {
            # Tier 1: Proven performers (highest weight)
            "5yb3D1KBy13czATSYGLUbZrYJvRvFQiH9XYkAeG2nDzH": {"tier": 1, "name": "Solana Foundation", "success_rate": 0.95},
            "HrwRZw4ZpEGgkzgDY1LrU8rgJZeYCNwRaf9LNkWJHRjH": {"tier": 1, "name": "Solana Foundation", "success_rate": 0.95},
            "65CmecDnuFAYJv8D8Ax3m3eNEGe4NQvrJV2GJPFMtATH": {"tier": 1, "name": "Jump Capital", "success_rate": 0.90},
            "9iDWyYZ5VHBCxxmWZogoY3Z6FSbKsX7xKTLSrMJRYmb": {"tier": 1, "name": "Multicoin Capital", "success_rate": 0.85},
            
            # Tier 2: Good performers (medium weight)
            "CXWNm8HKVGA2jX8tfZEfW9NjJdmfrmQUgLyYCcNnPrAL": {"tier": 2, "name": "Three Arrows Capital", "success_rate": 0.75},
            "AySc5J6asYDPLCgk9Lzn3ebPfEtWYGDWYTzNxJyf5dan": {"tier": 2, "name": "Top Trader 1", "success_rate": 0.80},
            "HHvNuiQF21eSYo1o9KN5QFpqwGf7dDM2EbCkZ5CJ9ihD": {"tier": 2, "name": "Top Trader 2", "success_rate": 0.78},
            
            # Tier 3: Moderate performers (lower weight)
            "E9bQjuJxF5xiZwBFKjgFC4P4kfMv3aJKJaXw3EPxLKVw": {"tier": 3, "name": "Top Trader 3", "success_rate": 0.65},
        }
        
        # Protocol wallets (neutral - institutional activity)
        self.protocol_wallets = {
            "DEX1CZAcuP3vfiGP7BmSbZY5AAv81TzjX4JR6Tmy2rZ": "Orca Protocol",
            "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1": "Raydium Protocol"
        }
        
        # Configuration thresholds
        self.thresholds = {
            'smart_money_bonus_threshold': 2,    # Minimum smart wallets for bonus
            'early_detection_hours': 12,         # Consider "early" if detected within this window
            'volume_quality_ratio': 20.0,        # Volume/mcap ratio above this = suspicious
            'extreme_volume_ratio': 50.0,        # Volume/mcap ratio above this = extreme manipulation
            'min_trader_diversity': 10,          # Minimum traders for healthy activity
            'institutional_volume_threshold': 1000000,  # $1M+ volume = institutional scale
        }

    def analyze_coordination_patterns(self, token_data: Dict[str, Any]) -> CoordinationSignal:
        """
        Main analysis function that determines coordination type and opportunity grade.
        
        Args:
            token_data: Token analysis data including trader info, volume, timing
            
        Returns:
            CoordinationSignal with type, confidence, and score impact
        """
        token_symbol = token_data.get('token_symbol', 'UNKNOWN')
        self.logger.info(f"[STRATEGIC] Starting coordination analysis for {token_symbol}")
        
        # Extract key metrics
        volume_24h = token_data.get('volume_24h', 0)
        market_cap = token_data.get('market_cap', 0)
        unique_traders = token_data.get('unique_trader_count', 0)
        creation_time = token_data.get('creation_time', time.time())
        trader_list = token_data.get('trader_list', [])  # List of trader addresses
        
        # Calculate timing factor (earlier detection = higher value)
        timing_factor = self._calculate_timing_factor(creation_time)
        
        # Analyze trader quality
        trader_analysis = self._analyze_trader_quality(trader_list)
        
        # Analyze volume patterns
        volume_analysis = self._analyze_volume_patterns(volume_24h, market_cap, unique_traders)
        
        # Determine coordination type based on combined analysis
        coordination_type = self._determine_coordination_type(
            trader_analysis, volume_analysis, timing_factor, token_data
        )
        
        # Calculate confidence and score impact
        confidence = self._calculate_confidence(trader_analysis, volume_analysis, timing_factor)
        score_impact = self._calculate_score_impact(coordination_type, confidence, timing_factor)
        
        # Build detailed signal
        signal = CoordinationSignal(
            type=coordination_type,
            confidence=confidence,
            score_impact=score_impact,
            details=self._build_signal_details(coordination_type, trader_analysis, volume_analysis, timing_factor),
            quality_factors={
                'trader_analysis': trader_analysis,
                'volume_analysis': volume_analysis,
                'timing_factor': timing_factor
            },
            timing_factor=timing_factor
        )
        
        self.logger.info(f"[STRATEGIC] {token_symbol} - Coordination Analysis:")
        self.logger.info(f"  🎯 Type: {coordination_type.value}")
        self.logger.info(f"  📊 Confidence: {confidence:.2f}")
        self.logger.info(f"  🚀 Score Impact: {score_impact:+d}")
        self.logger.info(f"  ⏰ Timing Factor: {timing_factor:.2f}")
        self.logger.info(f"  📝 Details: {signal.details}")
        
        return signal

    def _calculate_timing_factor(self, creation_time: float) -> float:
        """Calculate timing factor - earlier detection gets higher scores."""
        if not creation_time:
            return 0.5  # Default if no creation time
            
        age_hours = (time.time() - creation_time) / 3600
        
        if age_hours <= 2:
            return 1.0  # Perfect timing - very early detection
        elif age_hours <= 6:
            return 0.9  # Excellent timing
        elif age_hours <= 12:
            return 0.7  # Good timing
        elif age_hours <= 24:
            return 0.5  # Moderate timing
        elif age_hours <= 72:
            return 0.3  # Late timing
        else:
            return 0.1  # Very late timing

    def _analyze_trader_quality(self, trader_list: List[str]) -> Dict[str, Any]:
        """Analyze the quality and composition of traders."""
        analysis = {
            'smart_money_count': 0,
            'smart_money_wallets': [],
            'smart_money_tiers': [],
            'protocol_count': 0,
            'unknown_count': 0,
            'total_traders': len(trader_list) if trader_list else 0,
            'quality_score': 0.0,
            'trader_composition': 'unknown'
        }
        
        if not trader_list:
            return analysis
        
        # Analyze each trader
        for trader in trader_list:
            # Handle both string addresses and dict objects
            if isinstance(trader, dict):
                trader_address = trader.get('owner', '') or trader.get('address', '') or trader.get('wallet_address', '')
            else:
                trader_address = str(trader) if trader else ''
                
            # Skip empty addresses
            if not trader_address:
                continue
            
            if trader_address in self.smart_money_wallets:
                wallet_info = self.smart_money_wallets[trader_address]
                analysis['smart_money_count'] += 1
                analysis['smart_money_wallets'].append(trader_address)
                analysis['smart_money_tiers'].append(wallet_info['tier'])
            elif trader_address in self.protocol_wallets:
                analysis['protocol_count'] += 1
            else:
                analysis['unknown_count'] += 1
        
        # Calculate quality score
        smart_ratio = analysis['smart_money_count'] / len(trader_list)
        protocol_ratio = analysis['protocol_count'] / len(trader_list)
        
        # Weight by tier quality
        tier_weight = 0
        if analysis['smart_money_tiers']:
            tier_weight = sum(1.0/tier for tier in analysis['smart_money_tiers']) / len(analysis['smart_money_tiers'])
        
        analysis['quality_score'] = (smart_ratio * 0.7) + (protocol_ratio * 0.2) + (tier_weight * 0.1)
        
        # Determine composition
        if smart_ratio >= 0.5:
            analysis['trader_composition'] = 'smart_money_dominated'
        elif smart_ratio >= 0.2:
            analysis['trader_composition'] = 'mixed_quality'
        elif protocol_ratio >= 0.3:
            analysis['trader_composition'] = 'protocol_heavy'
        else:
            analysis['trader_composition'] = 'retail_dominated'
        
        return analysis

    def _analyze_volume_patterns(self, volume_24h: float, market_cap: float, unique_traders: int) -> Dict[str, Any]:
        """Analyze volume patterns for manipulation vs organic activity."""
        analysis = {
            'volume_mcap_ratio': 0.0,
            'volume_per_trader': 0.0,
            'volume_quality': 'unknown',
            'manipulation_risk': 0.0,
            'organic_score': 0.5
        }
        
        if volume_24h <= 0:
            return analysis
        
        # Calculate ratios
        if market_cap > 0:
            analysis['volume_mcap_ratio'] = volume_24h / market_cap
        
        if unique_traders > 0:
            analysis['volume_per_trader'] = volume_24h / unique_traders
        
        # Assess volume quality
        if analysis['volume_mcap_ratio'] > self.thresholds['extreme_volume_ratio']:
            analysis['volume_quality'] = 'extreme_manipulation'
            analysis['manipulation_risk'] = 0.9
            analysis['organic_score'] = 0.1
        elif analysis['volume_mcap_ratio'] > self.thresholds['volume_quality_ratio']:
            analysis['volume_quality'] = 'suspicious_manipulation'
            analysis['manipulation_risk'] = 0.7
            analysis['organic_score'] = 0.3
        elif analysis['volume_per_trader'] > 1000000:  # >$1M per trader
            analysis['volume_quality'] = 'concentrated_activity'
            analysis['manipulation_risk'] = 0.6
            analysis['organic_score'] = 0.4
        elif unique_traders >= self.thresholds['min_trader_diversity']:
            analysis['volume_quality'] = 'healthy_organic'
            analysis['manipulation_risk'] = 0.2
            analysis['organic_score'] = 0.8
        else:
            analysis['volume_quality'] = 'moderate_activity'
            analysis['manipulation_risk'] = 0.4
            analysis['organic_score'] = 0.6
        
        return analysis

    def _determine_coordination_type(self, trader_analysis: Dict, volume_analysis: Dict, 
                                   timing_factor: float, token_data: Dict) -> CoordinationType:
        """Determine the type of coordination based on all factors."""
        
        # Extract key metrics
        smart_money_count = trader_analysis['smart_money_count']
        quality_score = trader_analysis['quality_score']
        trader_composition = trader_analysis['trader_composition']
        volume_quality = volume_analysis['volume_quality']
        manipulation_risk = volume_analysis['manipulation_risk']
        volume_mcap_ratio = volume_analysis['volume_mcap_ratio']
        
        # Decision tree for coordination type
        
        # Grade F: Obvious manipulation (avoid completely)
        if volume_quality == 'extreme_manipulation':
            return CoordinationType.WASH_TRADING
        
        # Grade D: Retail pump patterns (avoid) - ENHANCED DETECTION
        if (trader_composition == 'retail_dominated' and 
            (volume_quality in ['suspicious_manipulation', 'concentrated_activity'] or
             volume_mcap_ratio > 3.0)):  # Any retail + high volume ratio = pump
            return CoordinationType.RETAIL_PUMP
        
        # Additional retail pump detection for high volume ratios with no smart money
        if (smart_money_count == 0 and 
            volume_mcap_ratio > 2.5 and
            trader_analysis['total_traders'] <= 15):  # Few traders, high volume, no smart money
            return CoordinationType.RETAIL_PUMP
        
        # Grade A: Smart money accumulation (follow these!)
        if (smart_money_count >= 3 and 
            quality_score >= 0.4 and 
            timing_factor >= 0.7 and
            volume_quality in ['healthy_organic', 'moderate_activity']):
            return CoordinationType.SMART_ACCUMULATION
        
        # Grade A: Institutional building (follow these!)
        if (trader_composition in ['smart_money_dominated', 'mixed_quality'] and
            volume_analysis['volume_per_trader'] > self.thresholds['institutional_volume_threshold'] and
            volume_quality != 'extreme_manipulation'):
            return CoordinationType.INSTITUTIONAL_BUILD
        
        # Grade B: Early coordination (consider these)
        if (timing_factor >= 0.8 and 
            smart_money_count >= 1 and
            manipulation_risk <= 0.5):
            return CoordinationType.EARLY_COORDINATION
        
        # Grade B: Momentum coordination (consider these)
        if (trader_composition == 'mixed_quality' and
            volume_quality in ['healthy_organic', 'moderate_activity']):
            return CoordinationType.MOMENTUM_COORDINATION
        
        # Grade C: Mixed signals (neutral)
        return CoordinationType.MIXED_SIGNALS

    def _calculate_confidence(self, trader_analysis: Dict, volume_analysis: Dict, timing_factor: float) -> float:
        """Calculate confidence in the coordination assessment."""
        
        # Base confidence from data quality
        base_confidence = 0.5
        
        # Boost confidence based on data completeness
        if trader_analysis['total_traders'] >= 10:
            base_confidence += 0.2
        elif trader_analysis['total_traders'] >= 5:
            base_confidence += 0.1
        
        # Boost confidence based on smart money presence
        if trader_analysis['smart_money_count'] >= 3:
            base_confidence += 0.2
        elif trader_analysis['smart_money_count'] >= 1:
            base_confidence += 0.1
        
        # Boost confidence based on volume quality clarity
        if volume_analysis['volume_quality'] in ['extreme_manipulation', 'healthy_organic']:
            base_confidence += 0.1
        
        # Boost confidence based on timing
        base_confidence += timing_factor * 0.1
        
        return min(1.0, base_confidence)

    def _calculate_score_impact(self, coordination_type: CoordinationType, confidence: float, timing_factor: float) -> int:
        """Calculate the score impact based on coordination type and confidence."""
        
        # Base score impacts by type - OPPORTUNITY-FOCUSED APPROACH
        base_impacts = {
            CoordinationType.SMART_ACCUMULATION: +35,      # Major bonus
            CoordinationType.INSTITUTIONAL_BUILD: +30,     # Major bonus
            CoordinationType.EARLY_COORDINATION: +20,      # Good bonus
            CoordinationType.MOMENTUM_COORDINATION: +15,   # Moderate bonus
            CoordinationType.MIXED_SIGNALS: 0,             # Neutral
            CoordinationType.RETAIL_PUMP: 0,               # CHANGED: Neutral (opportunity if timed right)
            CoordinationType.WASH_TRADING: -20,            # REDUCED: Light penalty (could signal upcoming moves)
        }
        
        base_impact = base_impacts[coordination_type]
        
        # SPECIAL: Opportunity-within-risk adjustments
        if coordination_type == CoordinationType.RETAIL_PUMP:
            # Retail pumps can be profitable if caught early with strong momentum
            if timing_factor >= 0.8:  # Very early detection
                base_impact = +5  # Small bonus for early pump detection
            elif timing_factor >= 0.6:  # Moderately early
                base_impact = 0   # Neutral - could be profitable
            else:
                base_impact = -10  # Late detection = likely missing the opportunity
                
        elif coordination_type == CoordinationType.WASH_TRADING:
            # Wash trading might signal preparation for real moves
            if timing_factor >= 0.9:  # Extremely early detection
                base_impact = -10  # Very light penalty - could be prep phase
            elif timing_factor >= 0.7:  # Early detection  
                base_impact = -15  # Light penalty - monitor for real moves
            else:
                base_impact = -30  # Standard penalty for late-detected wash trading
        
        # Apply confidence and timing multipliers for positive signals
        if base_impact > 0:
            multiplier = confidence * (0.5 + timing_factor * 0.5)
            final_impact = int(base_impact * multiplier)
        else:
            # For negative signals, confidence increases penalty
            multiplier = confidence * 0.8  # Reduced penalty multiplier for opportunities
            final_impact = int(base_impact * multiplier)
        
        return final_impact

    def _build_signal_details(self, coordination_type: CoordinationType, trader_analysis: Dict, 
                            volume_analysis: Dict, timing_factor: float) -> str:
        """Build a detailed explanation of the coordination signal."""
        
        details = []
        
        # Coordination type explanation
        type_explanations = {
            CoordinationType.SMART_ACCUMULATION: "🚀 Smart money accumulation detected",
            CoordinationType.INSTITUTIONAL_BUILD: "🏛️ Institutional position building",
            CoordinationType.EARLY_COORDINATION: "⚡ Early coordination opportunity",
            CoordinationType.MOMENTUM_COORDINATION: "📈 Quality momentum building",
            CoordinationType.MIXED_SIGNALS: "🤔 Mixed coordination signals",
            CoordinationType.RETAIL_PUMP: "⚡ Retail pump opportunity (early detection)",
            CoordinationType.WASH_TRADING: "🔍 Wash trading detected (monitor for real moves)"
        }
        
        details.append(type_explanations[coordination_type])
        
        # Add key metrics
        if trader_analysis['smart_money_count'] > 0:
            details.append(f"Smart money: {trader_analysis['smart_money_count']} wallets")
        
        if volume_analysis['volume_mcap_ratio'] > 0:
            details.append(f"Vol/MCap: {volume_analysis['volume_mcap_ratio']:.1f}x")
        
        if timing_factor > 0.7:
            details.append(f"Early detection (timing: {timing_factor:.2f})")
        elif timing_factor < 0.3:
            details.append(f"Late detection (timing: {timing_factor:.2f})")
        
        return " | ".join(details)

    def get_opportunity_grade(self, signal: CoordinationSignal) -> str:
        """Get letter grade for the coordination opportunity."""
        grade_map = {
            CoordinationType.SMART_ACCUMULATION: "A+",
            CoordinationType.INSTITUTIONAL_BUILD: "A",
            CoordinationType.EARLY_COORDINATION: "B+",
            CoordinationType.MOMENTUM_COORDINATION: "B",
            CoordinationType.MIXED_SIGNALS: "C",
            CoordinationType.RETAIL_PUMP: "C+",      # UPGRADED: Can be profitable if timed right
            CoordinationType.WASH_TRADING: "D+"      # UPGRADED: Monitor for opportunities
        }
        
        base_grade = grade_map[signal.type]
        
        # Special upgrades for early detection of risky patterns
        if signal.type == CoordinationType.RETAIL_PUMP and signal.timing_factor >= 0.8:
            return "B-"  # Early pump detection can be very profitable
        elif signal.type == CoordinationType.WASH_TRADING and signal.timing_factor >= 0.9:
            return "C"   # Early wash trading detection might signal upcoming moves
        
        # Standard upgrades based on high confidence and early timing
        if signal.confidence >= 0.8 and signal.timing_factor >= 0.8:
            if base_grade == "A":
                return "A+"
            elif base_grade == "B":
                return "B+"
        
        return base_grade 