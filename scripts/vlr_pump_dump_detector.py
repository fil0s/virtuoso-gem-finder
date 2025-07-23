#!/usr/bin/env python3
"""
VLR Pump & Dump Detection System
===============================

Advanced early warning system that uses VLR (Volume-to-Liquidity Ratio) patterns
to detect pump & dump schemes before they fully execute.

Key Detection Methods:
1. VLR Velocity Analysis (rate of VLR change)
2. Sustainability Scoring (can this VLR be maintained?)
3. Pattern Recognition (known pump/dump VLR signatures)
4. Cross-Platform Validation (manipulation often shows inconsistencies)
5. Liquidity Flow Analysis (smart money movement patterns)
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class PumpDumpPhase(Enum):
    """Pump & dump cycle phases"""
    ACCUMULATION = "ACCUMULATION"
    PUMP_SETUP = "PUMP_SETUP"
    PUMP_ACTIVE = "PUMP_ACTIVE"
    DISTRIBUTION = "DISTRIBUTION"
    DUMP_IMMINENT = "DUMP_IMMINENT"
    DUMP_ACTIVE = "DUMP_ACTIVE"
    RECOVERY = "RECOVERY"

@dataclass
class VLRSnapshot:
    """Single VLR data point"""
    timestamp: datetime
    vlr: float
    volume_24h: float
    liquidity: float
    price: float
    market_cap: Optional[float] = None

@dataclass
class PumpDumpAlert:
    """Pump & dump detection alert"""
    token_address: str
    symbol: str
    alert_level: AlertLevel
    phase: PumpDumpPhase
    confidence_score: float
    vlr_current: float
    vlr_velocity: float
    sustainability_score: float
    risk_factors: List[str]
    recommended_action: str
    timestamp: datetime

class VLRPumpDumpDetector:
    """Advanced VLR-based pump & dump detection system"""
    
    def __init__(self, lookback_hours: int = 24):
        self.lookback_hours = lookback_hours
        self.vlr_history: Dict[str, List[VLRSnapshot]] = {}
        self.active_alerts: Dict[str, PumpDumpAlert] = {}
        
        # Detection thresholds
        self.thresholds = {
            'vlr_velocity_warning': 0.5,      # VLR change per hour
            'vlr_velocity_critical': 2.0,     # VLR change per hour
            'vlr_unsustainable': 10.0,        # Absolute VLR level
            'vlr_extreme': 15.0,              # Extreme VLR level
            'liquidity_drain_threshold': 0.2,  # 20% liquidity reduction
            'volume_spike_multiplier': 5.0,    # 5x normal volume
            'price_vlr_divergence': 0.3       # 30% divergence threshold
        }
    
    def add_vlr_snapshot(self, token_address: str, symbol: str, vlr: float, 
                        volume_24h: float, liquidity: float, price: float,
                        market_cap: Optional[float] = None):
        """Add new VLR data point for analysis"""
        snapshot = VLRSnapshot(
            timestamp=datetime.now(),
            vlr=vlr,
            volume_24h=volume_24h,
            liquidity=liquidity,
            price=price,
            market_cap=market_cap
        )
        
        if token_address not in self.vlr_history:
            self.vlr_history[token_address] = []
        
        self.vlr_history[token_address].append(snapshot)
        
        # Keep only recent history
        cutoff_time = datetime.now() - timedelta(hours=self.lookback_hours)
        self.vlr_history[token_address] = [
            s for s in self.vlr_history[token_address] 
            if s.timestamp > cutoff_time
        ]
        
        # Analyze for pump/dump patterns
        alert = self.analyze_pump_dump_risk(token_address, symbol)
        if alert:
            self.active_alerts[token_address] = alert
            self._log_alert(alert)
        
        return alert
    
    def analyze_pump_dump_risk(self, token_address: str, symbol: str) -> Optional[PumpDumpAlert]:
        """Comprehensive pump & dump risk analysis"""
        history = self.vlr_history.get(token_address, [])
        if len(history) < 3:
            return None
        
        current = history[-1]
        risk_factors = []
        confidence_score = 0.0
        
        # 1. VLR Velocity Analysis
        vlr_velocity = self._calculate_vlr_velocity(history)
        if vlr_velocity > self.thresholds['vlr_velocity_critical']:
            risk_factors.append(f"Extreme VLR velocity: {vlr_velocity:.2f}/hour")
            confidence_score += 0.3
        elif vlr_velocity > self.thresholds['vlr_velocity_warning']:
            risk_factors.append(f"High VLR velocity: {vlr_velocity:.2f}/hour")
            confidence_score += 0.15
        
        # 2. Absolute VLR Level Analysis
        if current.vlr > self.thresholds['vlr_extreme']:
            risk_factors.append(f"Extreme VLR level: {current.vlr:.2f}")
            confidence_score += 0.4
        elif current.vlr > self.thresholds['vlr_unsustainable']:
            risk_factors.append(f"Unsustainable VLR level: {current.vlr:.2f}")
            confidence_score += 0.2
        
        # 3. Liquidity Drain Analysis
        liquidity_change = self._calculate_liquidity_change(history)
        if liquidity_change < -self.thresholds['liquidity_drain_threshold']:
            risk_factors.append(f"Liquidity draining: {liquidity_change:.1%}")
            confidence_score += 0.25
        
        # 4. Volume Spike Analysis
        volume_multiplier = self._calculate_volume_spike(history)
        if volume_multiplier > self.thresholds['volume_spike_multiplier']:
            risk_factors.append(f"Volume spike: {volume_multiplier:.1f}x normal")
            confidence_score += 0.2
        
        # 5. Price-VLR Divergence Analysis
        divergence = self._calculate_price_vlr_divergence(history)
        if abs(divergence) > self.thresholds['price_vlr_divergence']:
            risk_factors.append(f"Price-VLR divergence: {divergence:.1%}")
            confidence_score += 0.15
        
        # 6. Pattern Recognition
        pattern_risk = self._detect_known_patterns(history)
        if pattern_risk:
            risk_factors.extend(pattern_risk)
            confidence_score += 0.2
        
        # 7. Sustainability Scoring
        sustainability_score = self._calculate_sustainability_score(current, history)
        if sustainability_score < 0.3:
            risk_factors.append(f"Low sustainability: {sustainability_score:.2f}")
            confidence_score += 0.1
        
        # Determine phase and alert level
        if confidence_score < 0.3:
            return None  # Not enough evidence
        
        phase = self._determine_pump_dump_phase(current, history, vlr_velocity)
        alert_level = self._determine_alert_level(confidence_score, current.vlr)
        recommended_action = self._get_recommended_action(phase, alert_level)
        
        return PumpDumpAlert(
            token_address=token_address,
            symbol=symbol,
            alert_level=alert_level,
            phase=phase,
            confidence_score=confidence_score,
            vlr_current=current.vlr,
            vlr_velocity=vlr_velocity,
            sustainability_score=sustainability_score,
            risk_factors=risk_factors,
            recommended_action=recommended_action,
            timestamp=datetime.now()
        )
    
    def _calculate_vlr_velocity(self, history: List[VLRSnapshot]) -> float:
        """Calculate VLR change rate (VLR units per hour)"""
        if len(history) < 2:
            return 0.0
        
        # Use last 3 hours for velocity calculation
        recent_history = history[-6:] if len(history) >= 6 else history
        if len(recent_history) < 2:
            return 0.0
        
        time_diff = (recent_history[-1].timestamp - recent_history[0].timestamp).total_seconds() / 3600
        if time_diff <= 0:
            return 0.0
        
        vlr_diff = recent_history[-1].vlr - recent_history[0].vlr
        return vlr_diff / time_diff
    
    def _calculate_liquidity_change(self, history: List[VLRSnapshot]) -> float:
        """Calculate liquidity change percentage"""
        if len(history) < 6:
            return 0.0
        
        # Compare current to 6 hours ago
        old_liquidity = history[-6].liquidity
        current_liquidity = history[-1].liquidity
        
        if old_liquidity <= 0:
            return 0.0
        
        return (current_liquidity - old_liquidity) / old_liquidity
    
    def _calculate_volume_spike(self, history: List[VLRSnapshot]) -> float:
        """Calculate volume spike multiplier vs baseline"""
        if len(history) < 12:
            return 1.0
        
        # Use first half as baseline, second half as current
        baseline_volumes = [s.volume_24h for s in history[:len(history)//2]]
        current_volumes = [s.volume_24h for s in history[len(history)//2:]]
        
        baseline_avg = sum(baseline_volumes) / len(baseline_volumes)
        current_avg = sum(current_volumes) / len(current_volumes)
        
        if baseline_avg <= 0:
            return 1.0
        
        return current_avg / baseline_avg
    
    def _calculate_price_vlr_divergence(self, history: List[VLRSnapshot]) -> float:
        """Calculate divergence between price and VLR trends"""
        if len(history) < 6:
            return 0.0
        
        # Calculate price change and VLR change over same period
        price_change = (history[-1].price - history[-6].price) / history[-6].price
        vlr_change = (history[-1].vlr - history[-6].vlr) / history[-6].vlr
        
        # Normally price and VLR should move together
        # Divergence indicates potential manipulation
        if vlr_change == 0:
            return 0.0
        
        return (price_change - vlr_change) / abs(vlr_change)
    
    def _detect_known_patterns(self, history: List[VLRSnapshot]) -> List[str]:
        """Detect known pump & dump VLR patterns"""
        patterns = []
        
        if len(history) < 10:
            return patterns
        
        vlrs = [s.vlr for s in history[-10:]]
        
        # Pattern 1: Exponential VLR growth (classic pump setup)
        if self._is_exponential_growth(vlrs):
            patterns.append("Exponential VLR growth pattern detected")
        
        # Pattern 2: VLR plateau at unsustainable levels
        if self._is_unsustainable_plateau(vlrs):
            patterns.append("Unsustainable VLR plateau pattern")
        
        # Pattern 3: VLR spike with immediate decline (pump peak)
        if self._is_spike_and_decline(vlrs):
            patterns.append("VLR spike-and-decline pattern (dump signal)")
        
        # Pattern 4: Staircase VLR pattern (coordinated accumulation)
        if self._is_staircase_pattern(vlrs):
            patterns.append("Staircase VLR pattern (coordinated buying)")
        
        return patterns
    
    def _is_exponential_growth(self, vlrs: List[float]) -> bool:
        """Detect exponential VLR growth pattern"""
        if len(vlrs) < 5:
            return False
        
        # Check if each step is significantly larger than the previous
        ratios = []
        for i in range(1, len(vlrs)):
            if vlrs[i-1] > 0:
                ratios.append(vlrs[i] / vlrs[i-1])
        
        # Exponential if ratios are consistently > 1.5
        return len(ratios) >= 3 and all(r > 1.3 for r in ratios[-3:])
    
    def _is_unsustainable_plateau(self, vlrs: List[float]) -> bool:
        """Detect unsustainable VLR plateau"""
        if len(vlrs) < 5:
            return False
        
        recent_vlrs = vlrs[-5:]
        avg_vlr = sum(recent_vlrs) / len(recent_vlrs)
        
        # Plateau at high level with low variance
        if avg_vlr > 8.0:
            variance = sum((v - avg_vlr) ** 2 for v in recent_vlrs) / len(recent_vlrs)
            return variance < 2.0  # Low variance indicates plateau
        
        return False
    
    def _is_spike_and_decline(self, vlrs: List[float]) -> bool:
        """Detect VLR spike followed by decline"""
        if len(vlrs) < 6:
            return False
        
        # Find peak in recent history
        peak_idx = vlrs.index(max(vlrs[-6:]))
        if peak_idx < len(vlrs) - 3:  # Peak not too recent
            # Check if declining after peak
            post_peak = vlrs[peak_idx:]
            if len(post_peak) >= 3:
                return all(post_peak[i] >= post_peak[i+1] for i in range(len(post_peak)-1))
        
        return False
    
    def _is_staircase_pattern(self, vlrs: List[float]) -> bool:
        """Detect staircase VLR pattern (coordinated buying)"""
        if len(vlrs) < 8:
            return False
        
        # Look for alternating periods of growth and stability
        changes = [vlrs[i+1] - vlrs[i] for i in range(len(vlrs)-1)]
        
        # Staircase if we have alternating significant increases and small changes
        stairs = 0
        for i in range(0, len(changes)-1, 2):
            if i+1 < len(changes):
                if changes[i] > 0.5 and abs(changes[i+1]) < 0.2:  # Big step, then flat
                    stairs += 1
        
        return stairs >= 2
    
    def _calculate_sustainability_score(self, current: VLRSnapshot, history: List[VLRSnapshot]) -> float:
        """Calculate how sustainable the current VLR level is"""
        score = 1.0
        
        # Factor 1: Absolute VLR level (higher = less sustainable)
        if current.vlr > 15.0:
            score *= 0.1
        elif current.vlr > 10.0:
            score *= 0.3
        elif current.vlr > 5.0:
            score *= 0.6
        elif current.vlr > 2.0:
            score *= 0.8
        
        # Factor 2: VLR growth rate (faster = less sustainable)
        if len(history) >= 3:
            vlr_velocity = self._calculate_vlr_velocity(history)
            if vlr_velocity > 3.0:
                score *= 0.2
            elif vlr_velocity > 1.0:
                score *= 0.5
            elif vlr_velocity > 0.5:
                score *= 0.7
        
        # Factor 3: Liquidity support (less liquidity = less sustainable)
        if current.liquidity < 100_000:
            score *= 0.3
        elif current.liquidity < 500_000:
            score *= 0.6
        elif current.liquidity < 1_000_000:
            score *= 0.8
        
        # Factor 4: Market cap vs volume ratio
        if current.market_cap and current.volume_24h > 0:
            volume_to_mcap = current.volume_24h / current.market_cap
            if volume_to_mcap > 2.0:  # Volume > 2x market cap (unsustainable)
                score *= 0.2
            elif volume_to_mcap > 1.0:
                score *= 0.5
        
        return max(0.0, min(1.0, score))
    
    def _determine_pump_dump_phase(self, current: VLRSnapshot, history: List[VLRSnapshot], vlr_velocity: float) -> PumpDumpPhase:
        """Determine current phase of pump & dump cycle"""
        
        # Accumulation: Low VLR with increasing trend
        if current.vlr < 2.0 and vlr_velocity > 0.2:
            return PumpDumpPhase.ACCUMULATION
        
        # Pump Setup: Moderate VLR with high velocity
        if 2.0 <= current.vlr < 5.0 and vlr_velocity > 0.5:
            return PumpDumpPhase.PUMP_SETUP
        
        # Active Pump: High VLR with extreme velocity
        if current.vlr >= 5.0 and vlr_velocity > 1.0:
            return PumpDumpPhase.PUMP_ACTIVE
        
        # Distribution: High VLR but declining velocity
        if current.vlr >= 8.0 and vlr_velocity < 0.5:
            return PumpDumpPhase.DISTRIBUTION
        
        # Dump Imminent: Very high VLR with negative velocity
        if current.vlr >= 10.0 and vlr_velocity < -0.5:
            return PumpDumpPhase.DUMP_IMMINENT
        
        # Dump Active: Rapidly declining VLR
        if vlr_velocity < -2.0:
            return PumpDumpPhase.DUMP_ACTIVE
        
        # Recovery: Low VLR after dump
        if current.vlr < 1.0 and len(history) > 10:
            max_recent_vlr = max(s.vlr for s in history[-10:])
            if max_recent_vlr > 5.0:
                return PumpDumpPhase.RECOVERY
        
        return PumpDumpPhase.ACCUMULATION
    
    def _determine_alert_level(self, confidence_score: float, vlr: float) -> AlertLevel:
        """Determine alert severity level"""
        if confidence_score >= 0.8 or vlr >= 15.0:
            return AlertLevel.CRITICAL
        elif confidence_score >= 0.6 or vlr >= 10.0:
            return AlertLevel.HIGH
        elif confidence_score >= 0.4 or vlr >= 5.0:
            return AlertLevel.MEDIUM
        else:
            return AlertLevel.LOW
    
    def _get_recommended_action(self, phase: PumpDumpPhase, alert_level: AlertLevel) -> str:
        """Get recommended action based on phase and alert level"""
        actions = {
            PumpDumpPhase.ACCUMULATION: {
                AlertLevel.LOW: "Monitor closely for continued VLR growth",
                AlertLevel.MEDIUM: "Consider small short position or avoid new longs",
                AlertLevel.HIGH: "Avoid new positions, prepare exit strategy",
                AlertLevel.CRITICAL: "Exit all positions immediately"
            },
            PumpDumpPhase.PUMP_SETUP: {
                AlertLevel.LOW: "Increase monitoring frequency",
                AlertLevel.MEDIUM: "Reduce position size, set tight stops",
                AlertLevel.HIGH: "Exit 50-75% of position",
                AlertLevel.CRITICAL: "Exit all positions immediately"
            },
            PumpDumpPhase.PUMP_ACTIVE: {
                AlertLevel.LOW: "Set very tight stops, prepare to exit",
                AlertLevel.MEDIUM: "Exit 75% of position immediately",
                AlertLevel.HIGH: "Exit all positions immediately",
                AlertLevel.CRITICAL: "EXIT ALL POSITIONS - DUMP IMMINENT"
            },
            PumpDumpPhase.DISTRIBUTION: {
                AlertLevel.LOW: "Exit 50% of position, monitor for dump signals",
                AlertLevel.MEDIUM: "Exit 75% of position immediately",
                AlertLevel.HIGH: "Exit all positions immediately",
                AlertLevel.CRITICAL: "EXIT ALL - DUMP STARTING"
            },
            PumpDumpPhase.DUMP_IMMINENT: {
                AlertLevel.LOW: "EXIT ALL POSITIONS IMMEDIATELY",
                AlertLevel.MEDIUM: "EXIT ALL POSITIONS IMMEDIATELY",
                AlertLevel.HIGH: "EXIT ALL POSITIONS IMMEDIATELY",
                AlertLevel.CRITICAL: "EXIT ALL POSITIONS IMMEDIATELY"
            },
            PumpDumpPhase.DUMP_ACTIVE: {
                AlertLevel.LOW: "Do not buy - dump in progress",
                AlertLevel.MEDIUM: "Do not buy - dump in progress", 
                AlertLevel.HIGH: "Do not buy - dump in progress",
                AlertLevel.CRITICAL: "Do not buy - major dump in progress"
            },
            PumpDumpPhase.RECOVERY: {
                AlertLevel.LOW: "Monitor for genuine recovery vs dead cat bounce",
                AlertLevel.MEDIUM: "Wait for VLR stabilization before considering entry",
                AlertLevel.HIGH: "Avoid - likely more downside ahead",
                AlertLevel.CRITICAL: "Avoid - major damage, long recovery expected"
            }
        }
        
        return actions.get(phase, {}).get(alert_level, "Monitor situation closely")
    
    def _log_alert(self, alert: PumpDumpAlert):
        """Log pump & dump alert"""
        logger.warning(f"""
🚨 PUMP & DUMP ALERT 🚨
Token: {alert.symbol} ({alert.token_address})
Alert Level: {alert.alert_level.value}
Phase: {alert.phase.value}
Confidence: {alert.confidence_score:.1%}
Current VLR: {alert.vlr_current:.2f}
VLR Velocity: {alert.vlr_velocity:.2f}/hour
Sustainability: {alert.sustainability_score:.2f}
Risk Factors: {', '.join(alert.risk_factors)}
Recommended Action: {alert.recommended_action}
Timestamp: {alert.timestamp}
        """)
    
    def get_active_alerts(self) -> Dict[str, PumpDumpAlert]:
        """Get all active pump & dump alerts"""
        return self.active_alerts.copy()
    
    def clear_old_alerts(self, hours: int = 24):
        """Clear alerts older than specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        self.active_alerts = {
            addr: alert for addr, alert in self.active_alerts.items()
            if alert.timestamp > cutoff
        }

# Demo usage
async def demo_pump_dump_detection():
    """Demonstrate pump & dump detection with simulated data"""
    detector = VLRPumpDumpDetector()
    
    print("🚨 VLR Pump & Dump Detection Demo")
    print("=" * 50)
    
    # Simulate pump & dump scenario
    scenarios = [
        # Normal token behavior
        {"symbol": "NORMAL", "vlr_sequence": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0], "description": "Normal growth"},
        
        # Pre-pump accumulation
        {"symbol": "PREPUMP", "vlr_sequence": [0.2, 0.4, 0.8, 1.5, 2.8, 4.2], "description": "Pre-pump accumulation"},
        
        # Active pump
        {"symbol": "PUMPING", "vlr_sequence": [1.0, 3.0, 8.0, 15.0, 22.0, 18.0], "description": "Active pump & early dump"},
        
        # Post-dump recovery
        {"symbol": "DUMPED", "vlr_sequence": [25.0, 15.0, 8.0, 3.0, 1.5, 0.8], "description": "Post-dump decline"}
    ]
    
    for scenario in scenarios:
        print(f"\n📊 Scenario: {scenario['description']} ({scenario['symbol']})")
        print("-" * 40)
        
        token_address = f"demo_{scenario['symbol'].lower()}"
        
        for i, vlr in enumerate(scenario['vlr_sequence']):
            # Simulate realistic volume and liquidity
            base_liquidity = 1_000_000
            volume = vlr * base_liquidity
            price = 1.0 + (i * 0.5)  # Simulate price increase
            
            alert = detector.add_vlr_snapshot(
                token_address=token_address,
                symbol=scenario['symbol'],
                vlr=vlr,
                volume_24h=volume,
                liquidity=base_liquidity,
                price=price,
                market_cap=price * 1_000_000
            )
            
            if alert:
                print(f"⚠️  VLR {vlr:.1f}: {alert.alert_level.value} - {alert.phase.value}")
                print(f"   Action: {alert.recommended_action}")
            else:
                print(f"✅ VLR {vlr:.1f}: No significant risk detected")
            
            # Simulate time passage
            await asyncio.sleep(0.1)
    
    print(f"\n📈 Detection Summary:")
    print(f"Active Alerts: {len(detector.get_active_alerts())}")
    for addr, alert in detector.get_active_alerts().items():
        print(f"  • {alert.symbol}: {alert.alert_level.value} ({alert.confidence_score:.1%} confidence)")

if __name__ == "__main__":
    asyncio.run(demo_pump_dump_detection()) 