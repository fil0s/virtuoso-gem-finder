"""
Trader Performance Alert System

Monitors trader performance changes and generates alerts for:
- New elite trader discoveries
- Significant performance improvements/degradations
- Consistent cross-timeframe performers
- Risk profile changes
- Portfolio concentration alerts

Integrates with existing whale tracking and Telegram alert systems.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta

from services.trader_performance_analyzer import (
    TraderPerformanceAnalyzer,
    PerformanceTimeframe,
    TraderTier,
    TraderProfile
)
from utils.structured_logger import get_structured_logger

class TraderAlertType(Enum):
    NEW_ELITE_DISCOVERY = "new_elite_discovery"
    TIER_UPGRADE = "tier_upgrade"
    TIER_DOWNGRADE = "tier_downgrade"
    PERFORMANCE_SPIKE = "performance_spike"
    RISK_CHANGE = "risk_change"
    CONSISTENT_PERFORMER = "consistent_performer"
    PORTFOLIO_CONCENTRATION = "portfolio_concentration"
    UNUSUAL_ACTIVITY = "unusual_activity"

class TraderAlertLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TraderAlert:
    """Trader performance alert"""
    alert_id: str
    trader_address: str
    trader_name: str
    alert_type: TraderAlertType
    alert_level: TraderAlertLevel
    title: str
    description: str
    current_tier: str
    previous_tier: Optional[str]
    discovery_score: float
    risk_score: float
    timeframe: str
    significance_score: float  # 0-100 importance score
    recommended_action: str
    created_at: int
    metadata: Dict[str, Any]  # Additional context data

class TraderAlertSystem:
    """
    Comprehensive trader performance alert system
    """
    
    def __init__(self, trader_analyzer: TraderPerformanceAnalyzer, 
                 logger: Optional[logging.Logger] = None):
        self.trader_analyzer = trader_analyzer
        self.logger = logger or logging.getLogger(__name__)
        
        # Alert configuration
        self.alert_config = {
            'enable_alerts': True,
            'min_elite_discovery_score': 85,     # Minimum score for elite discovery alerts
            'tier_change_significance': 70,      # Minimum significance for tier change alerts
            'performance_spike_threshold': 50,   # % improvement to trigger spike alert
            'risk_change_threshold': 30,         # Risk score change to trigger alert
            'consistency_timeframes': 2,         # Number of timeframes for consistency
            'alert_cooldown_hours': 2,           # Hours between similar alerts
            'max_alerts_per_hour': 15,           # Rate limit alerts
            'enable_telegram': False,            # Telegram notifications
            'telegram_min_level': 'high',        # Minimum level for Telegram alerts
        }
        
        # Data storage
        self.data_dir = Path("data/trader_alerts")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.alerts_db_path = self.data_dir / "trader_alerts.json"
        self.tracker_state_path = self.data_dir / "alert_tracker_state.json"
        
        # Active alerts and tracking
        self.active_alerts: List[TraderAlert] = []
        self.trader_history: Dict[str, Dict] = {}  # Track trader performance history
        self.last_alert_times: Dict[str, int] = {}  # Cooldown tracking
        
        # Optional Telegram integration
        self.telegram_alerter = None
        
        # Load existing state
        self._load_tracker_state()
        
        self.structured_logger = get_structured_logger('TraderWhaleAlerting')
    
    def setup_telegram_alerts(self, telegram_alerter, min_level: str = 'high'):
        """Setup Telegram integration for trader alerts"""
        self.telegram_alerter = telegram_alerter
        self.alert_config['enable_telegram'] = True
        self.alert_config['telegram_min_level'] = min_level
        self.logger.info(f"📱 Telegram alerts enabled for trader discoveries (min level: {min_level})")
    
    async def monitor_trader_performance(self, timeframes: List[PerformanceTimeframe] = None, scan_id: Optional[str] = None) -> List[TraderAlert]:
        """
        Monitor trader performance and generate alerts for significant changes
        
        Args:
            timeframes: List of timeframes to monitor (default: 24h and 7d)
            
        Returns:
            List of generated alerts
        """
        if not self.alert_config['enable_alerts']:
            return []
        
        if timeframes is None:
            timeframes = [PerformanceTimeframe.HOUR_24, PerformanceTimeframe.DAYS_7]
        
        all_alerts = []
        
        for timeframe in timeframes:
            self.logger.info(f"🔍 Monitoring trader performance for {timeframe.value}")
            
            try:
                # Discover current top traders
                current_traders = await self.trader_analyzer.discover_top_traders(timeframe, 50)
                
                # Generate alerts for discoveries and changes
                alerts = await self._process_trader_discoveries(current_traders, timeframe)
                all_alerts.extend(alerts)
                
                # Update trader history
                self._update_trader_history(current_traders, timeframe)
                
            except Exception as e:
                self.logger.error(f"Error monitoring {timeframe.value} traders: {e}")
        
        # Check for cross-timeframe consistency
        consistency_alerts = await self._check_cross_timeframe_consistency()
        all_alerts.extend(consistency_alerts)
        
        # Process and handle all alerts
        for alert in all_alerts:
            await self._handle_alert(alert, scan_id=scan_id)
        
        return all_alerts
    
    async def _process_trader_discoveries(self, current_traders: List[TraderProfile], 
                                        timeframe: PerformanceTimeframe) -> List[TraderAlert]:
        """Process new trader discoveries and changes"""
        alerts = []
        
        for trader in current_traders:
            try:
                # Check for new elite discoveries
                if trader.tier == TraderTier.ELITE:
                    alert = await self._check_new_elite_discovery(trader, timeframe)
                    if alert:
                        alerts.append(alert)
                
                # Check for tier changes
                tier_alert = await self._check_tier_changes(trader, timeframe)
                if tier_alert:
                    alerts.append(tier_alert)
                
                # Check for performance spikes
                spike_alert = await self._check_performance_spikes(trader, timeframe)
                if spike_alert:
                    alerts.append(spike_alert)
                
                # Check for risk changes
                risk_alert = await self._check_risk_changes(trader, timeframe)
                if risk_alert:
                    alerts.append(risk_alert)
                
            except Exception as e:
                self.logger.warning(f"Error processing trader {trader.address[:8]}...: {e}")
        
        return alerts
    
    async def _check_new_elite_discovery(self, trader: TraderProfile, 
                                       timeframe: PerformanceTimeframe) -> Optional[TraderAlert]:
        """Check for new elite trader discoveries"""
        trader_key = f"{trader.address}_{timeframe.value}"
        
        # Check if this is a new elite discovery
        if trader_key not in self.trader_history:
            if (trader.tier == TraderTier.ELITE and 
                trader.discovery_score >= self.alert_config['min_elite_discovery_score']):
                
                return TraderAlert(
                    alert_id=f"elite_{trader.address[:8]}_{int(time.time())}",
                    trader_address=trader.address,
                    trader_name=trader.name,
                    alert_type=TraderAlertType.NEW_ELITE_DISCOVERY,
                    alert_level=TraderAlertLevel.CRITICAL,
                    title=f"🌟 NEW ELITE TRADER DISCOVERED",
                    description=f"Discovered new elite trader with {trader.discovery_score:.0f}/100 score in {timeframe.value}",
                    current_tier=trader.tier.value,
                    previous_tier=None,
                    discovery_score=trader.discovery_score,
                    risk_score=trader.risk_score,
                    timeframe=timeframe.value,
                    significance_score=min(100, trader.discovery_score + 15),  # Bonus for new discovery
                    recommended_action=f"IMMEDIATE: Follow trader and monitor token movements",
                    created_at=int(time.time()),
                    metadata={
                        "performance_24h": asdict(trader.performance_24h) if trader.performance_24h else None,
                        "performance_7d": asdict(trader.performance_7d) if trader.performance_7d else None,
                        "tags": trader.tags,
                        "favorite_tokens": trader.favorite_tokens
                    }
                )
        
        return None
    
    async def _check_tier_changes(self, trader: TraderProfile, 
                                timeframe: PerformanceTimeframe) -> Optional[TraderAlert]:
        """Check for trader tier upgrades/downgrades"""
        trader_key = f"{trader.address}_{timeframe.value}"
        
        if trader_key in self.trader_history:
            previous_tier = self.trader_history[trader_key].get('tier')
            
            if previous_tier and previous_tier != trader.tier.value:
                # Determine if upgrade or downgrade
                tier_order = {
                    TraderTier.NOVICE: 1,
                    TraderTier.INTERMEDIATE: 2,
                    TraderTier.ADVANCED: 3,
                    TraderTier.PROFESSIONAL: 4,
                    TraderTier.ELITE: 5
                }
                
                current_level = tier_order[trader.tier]
                previous_level = tier_order.get(TraderTier(previous_tier), 0)
                
                if current_level > previous_level:
                    # Tier upgrade
                    alert_level = TraderAlertLevel.HIGH if trader.tier == TraderTier.ELITE else TraderAlertLevel.MEDIUM
                    
                    return TraderAlert(
                        alert_id=f"upgrade_{trader.address[:8]}_{int(time.time())}",
                        trader_address=trader.address,
                        trader_name=trader.name,
                        alert_type=TraderAlertType.TIER_UPGRADE,
                        alert_level=alert_level,
                        title=f"📈 TRADER TIER UPGRADE",
                        description=f"Trader upgraded from {previous_tier} to {trader.tier.value} in {timeframe.value}",
                        current_tier=trader.tier.value,
                        previous_tier=previous_tier,
                        discovery_score=trader.discovery_score,
                        risk_score=trader.risk_score,
                        timeframe=timeframe.value,
                        significance_score=self.alert_config['tier_change_significance'],
                        recommended_action=f"MONITOR: Track recent trades and positions",
                        created_at=int(time.time()),
                        metadata={"tier_progression": f"{previous_tier} → {trader.tier.value}"}
                    )
                
                elif current_level < previous_level:
                    # Tier downgrade
                    return TraderAlert(
                        alert_id=f"downgrade_{trader.address[:8]}_{int(time.time())}",
                        trader_address=trader.address,
                        trader_name=trader.name,
                        alert_type=TraderAlertType.TIER_DOWNGRADE,
                        alert_level=TraderAlertLevel.LOW,
                        title=f"📉 TRADER TIER DOWNGRADE",
                        description=f"Trader downgraded from {previous_tier} to {trader.tier.value} in {timeframe.value}",
                        current_tier=trader.tier.value,
                        previous_tier=previous_tier,
                        discovery_score=trader.discovery_score,
                        risk_score=trader.risk_score,
                        timeframe=timeframe.value,
                        significance_score=50,
                        recommended_action=f"CAUTION: Review recent performance and consider reducing follow weight",
                        created_at=int(time.time()),
                        metadata={"tier_regression": f"{previous_tier} → {trader.tier.value}"}
                    )
        
        return None
    
    async def _check_performance_spikes(self, trader: TraderProfile, 
                                      timeframe: PerformanceTimeframe) -> Optional[TraderAlert]:
        """Check for significant performance improvements"""
        trader_key = f"{trader.address}_{timeframe.value}"
        
        if trader_key in self.trader_history:
            previous_score = self.trader_history[trader_key].get('discovery_score', 0)
            
            if previous_score > 0:
                score_improvement = ((trader.discovery_score - previous_score) / previous_score) * 100
                
                if score_improvement >= self.alert_config['performance_spike_threshold']:
                    return TraderAlert(
                        alert_id=f"spike_{trader.address[:8]}_{int(time.time())}",
                        trader_address=trader.address,
                        trader_name=trader.name,
                        alert_type=TraderAlertType.PERFORMANCE_SPIKE,
                        alert_level=TraderAlertLevel.HIGH,
                        title=f"🚀 PERFORMANCE SPIKE",
                        description=f"Trader performance improved {score_improvement:.1f}% in {timeframe.value}",
                        current_tier=trader.tier.value,
                        previous_tier=None,
                        discovery_score=trader.discovery_score,
                        risk_score=trader.risk_score,
                        timeframe=timeframe.value,
                        significance_score=min(100, 60 + (score_improvement / 2)),
                        recommended_action=f"OPPORTUNITY: Investigate recent trades for alpha signals",
                        created_at=int(time.time()),
                        metadata={
                            "score_improvement": score_improvement,
                            "previous_score": previous_score,
                            "current_score": trader.discovery_score
                        }
                    )
        
        return None
    
    async def _check_risk_changes(self, trader: TraderProfile, 
                                timeframe: PerformanceTimeframe) -> Optional[TraderAlert]:
        """Check for significant risk profile changes"""
        trader_key = f"{trader.address}_{timeframe.value}"
        
        if trader_key in self.trader_history:
            previous_risk = self.trader_history[trader_key].get('risk_score', 50)
            risk_change = abs(trader.risk_score - previous_risk)
            
            if risk_change >= self.alert_config['risk_change_threshold']:
                alert_level = TraderAlertLevel.MEDIUM if risk_change >= 50 else TraderAlertLevel.LOW
                risk_direction = "increased" if trader.risk_score > previous_risk else "decreased"
                
                return TraderAlert(
                    alert_id=f"risk_{trader.address[:8]}_{int(time.time())}",
                    trader_address=trader.address,
                    trader_name=trader.name,
                    alert_type=TraderAlertType.RISK_CHANGE,
                    alert_level=alert_level,
                    title=f"⚠️ RISK PROFILE CHANGE",
                    description=f"Trader risk score {risk_direction} by {risk_change:.1f} points in {timeframe.value}",
                    current_tier=trader.tier.value,
                    previous_tier=None,
                    discovery_score=trader.discovery_score,
                    risk_score=trader.risk_score,
                    timeframe=timeframe.value,
                    significance_score=min(90, 40 + risk_change),
                    recommended_action=f"REVIEW: Assess risk tolerance and position sizing",
                    created_at=int(time.time()),
                    metadata={
                        "risk_change": risk_change,
                        "risk_direction": risk_direction,
                        "previous_risk": previous_risk,
                        "current_risk": trader.risk_score
                    }
                )
        
        return None
    
    async def _check_cross_timeframe_consistency(self) -> List[TraderAlert]:
        """Check for traders who are consistent across multiple timeframes"""
        alerts = []
        
        # Find traders who appear in both 24h and 7d top lists
        traders_24h = {addr: data for addr, data in self.trader_history.items() if addr.endswith("_24h")}
        traders_7d = {addr: data for addr, data in self.trader_history.items() if addr.endswith("_7d")}
        
        # Extract base addresses
        addresses_24h = {addr.split("_")[0] for addr in traders_24h.keys()}
        addresses_7d = {addr.split("_")[0] for addr in traders_7d.keys()}
        
        # Find consistent performers
        consistent_addresses = addresses_24h.intersection(addresses_7d)
        
        for address in consistent_addresses:
            try:
                trader_24h = traders_24h.get(f"{address}_24h", {})
                trader_7d = traders_7d.get(f"{address}_7d", {})
                
                # Check if both performances are strong
                score_24h = trader_24h.get('discovery_score', 0)
                score_7d = trader_7d.get('discovery_score', 0)
                tier_24h = trader_24h.get('tier', 'novice')
                tier_7d = trader_7d.get('tier', 'novice')
                
                if (score_24h >= 75 and score_7d >= 75 and
                    tier_24h in ['elite', 'professional'] and tier_7d in ['elite', 'professional']):
                    
                    # Check if we haven't alerted for this trader recently
                    alert_key = f"consistent_{address}"
                    if self._should_send_alert(alert_key):
                        avg_score = (score_24h + score_7d) / 2
                        
                        alert = TraderAlert(
                            alert_id=f"consistent_{address[:8]}_{int(time.time())}",
                            trader_address=address,
                            trader_name=f"Trader {address[:8]}...",
                            alert_type=TraderAlertType.CONSISTENT_PERFORMER,
                            alert_level=TraderAlertLevel.HIGH,
                            title=f"🎯 CONSISTENT TOP PERFORMER",
                            description=f"Trader ranks high in both 24h and 7d timeframes",
                            current_tier=tier_7d,
                            previous_tier=None,
                            discovery_score=avg_score,
                            risk_score=(trader_24h.get('risk_score', 50) + trader_7d.get('risk_score', 50)) / 2,
                            timeframe="multi",
                            significance_score=min(100, avg_score + 10),  # Bonus for consistency
                            recommended_action=f"HIGH PRIORITY: This trader shows consistent excellence across timeframes",
                            created_at=int(time.time()),
                            metadata={
                                "score_24h": score_24h,
                                "score_7d": score_7d,
                                "tier_24h": tier_24h,
                                "tier_7d": tier_7d,
                                "consistency_bonus": 10
                            }
                        )
                        
                        alerts.append(alert)
                        self.last_alert_times[alert_key] = int(time.time())
                        
            except Exception as e:
                self.logger.warning(f"Error checking consistency for {address}: {e}")
        
        return alerts
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Check if enough time has passed since last alert of this type"""
        if alert_key not in self.last_alert_times:
            return True
        
        last_alert_time = self.last_alert_times[alert_key]
        hours_since_last = (time.time() - last_alert_time) / 3600
        
        return hours_since_last >= self.alert_config['alert_cooldown_hours']
    
    def _update_trader_history(self, traders: List[TraderProfile], timeframe: PerformanceTimeframe):
        """Update trader performance history for comparison"""
        for trader in traders:
            trader_key = f"{trader.address}_{timeframe.value}"
            
            self.trader_history[trader_key] = {
                'discovery_score': trader.discovery_score,
                'risk_score': trader.risk_score,
                'tier': trader.tier.value,
                'last_updated': int(time.time()),
                'timeframe': timeframe.value
            }
        
        # Save updated history
        self._save_tracker_state()
    
    async def _handle_alert(self, alert: TraderAlert, scan_id: Optional[str] = None):
        self.structured_logger.info({
            "event": "alert_trigger_attempt",
            "alert_type": "trader",
            "scan_id": scan_id,
            "trader": alert.trader_address,
            "alert_id": alert.alert_id,
            "alert_level": alert.alert_level.value,
            "trigger_reason": alert.alert_type.value,
            "timestamp": int(time.time())
        })
        self.logger.info(f"🚨 TRADER ALERT [{alert.alert_level.value.upper()}]: {alert.title}")
        self.logger.info(f"   👤 Trader: {alert.trader_name} ({alert.trader_address[:8]}...)")
        self.logger.info(f"   🎯 Score: {alert.discovery_score:.0f}/100 | Risk: {alert.risk_score:.0f}/100")
        self.logger.info(f"   🏆 Tier: {alert.current_tier.title()}")
        self.logger.info(f"   📝 Action: {alert.recommended_action}")
        
        # Send Telegram alert if enabled and meets level
        if self.alert_config.get('enable_telegram') and self._should_send_telegram_alert(alert):
            try:
                await self._send_telegram_trader_alert(alert, scan_id=scan_id)
                self.structured_logger.info({
                    "event": "alert_send_result",
                    "alert_type": "trader",
                    "scan_id": scan_id,
                    "trader": alert.trader_address,
                    "alert_id": alert.alert_id,
                    "result": "success",
                    "timestamp": int(time.time())
                })
            except Exception as e:
                self.structured_logger.error({
                    "event": "alert_send_result",
                    "alert_type": "trader",
                    "scan_id": scan_id,
                    "trader": alert.trader_address,
                    "alert_id": alert.alert_id,
                    "result": "error",
                    "error": str(e),
                    "timestamp": int(time.time())
                })
        else:
            self.structured_logger.info({
                "event": "alert_suppressed",
                "alert_type": "trader",
                "scan_id": scan_id,
                "trader": alert.trader_address,
                "alert_id": alert.alert_id,
                "reason": "not_enabled_or_below_level",
                "timestamp": int(time.time())
            })
        
        # Add to active alerts
        self.active_alerts.append(alert)
        
        # Keep only recent alerts (last 24 hours)
        cutoff_time = int(time.time()) - (24 * 3600)
        self.active_alerts = [
            a for a in self.active_alerts
            if a.created_at >= cutoff_time
        ]
        
        # Save alert to database
        await self._save_alert(alert)
    
    def _should_send_telegram_alert(self, alert: TraderAlert) -> bool:
        """Check if alert should be sent to Telegram"""
        level_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        min_level = self.alert_config['telegram_min_level']
        
        alert_level_value = level_order.get(alert.alert_level.value, 0)
        min_level_value = level_order.get(min_level, 3)
        
        return alert_level_value >= min_level_value
    
    async def _send_telegram_trader_alert(self, alert: TraderAlert, scan_id: Optional[str] = None):
        if not self.telegram_alerter:
            return
        # Compose message (simplified for brevity)
        message = f"🚨 <b>Trader Alert</b>\n<b>{alert.trader_name}</b> ({alert.trader_address[:8]}...)\nType: {alert.alert_type.value}\nLevel: {alert.alert_level.value}\n{alert.title}\n{alert.description}"
        try:
            self.telegram_alerter.send_message(message)
        except Exception as e:
            self.structured_logger.error({
                "event": "alert_send_result",
                "alert_type": "trader",
                "scan_id": scan_id,
                "trader": alert.trader_address,
                "alert_id": alert.alert_id,
                "result": "error",
                "error": str(e),
                "timestamp": int(time.time())
            })
    
    async def _save_alert(self, alert: TraderAlert):
        """Save alert to persistent storage"""
        try:
            alerts_data = []
            if self.alerts_db_path.exists():
                with open(self.alerts_db_path, 'r') as f:
                    alerts_data = json.load(f)
            
            alerts_data.append(asdict(alert))
            
            # Keep only last 1000 alerts
            alerts_data = alerts_data[-1000:]
            
            with open(self.alerts_db_path, 'w') as f:
                json.dump(alerts_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving trader alert: {e}")
    
    def _load_tracker_state(self):
        """Load tracker state from disk"""
        try:
            if self.tracker_state_path.exists():
                with open(self.tracker_state_path, 'r') as f:
                    state = json.load(f)
                    self.trader_history = state.get('trader_history', {})
                    self.last_alert_times = state.get('last_alert_times', {})
        except Exception as e:
            self.logger.warning(f"Error loading tracker state: {e}")
    
    def _save_tracker_state(self):
        """Save tracker state to disk"""
        try:
            state = {
                'trader_history': self.trader_history,
                'last_alert_times': self.last_alert_times,
                'last_updated': int(time.time())
            }
            
            with open(self.tracker_state_path, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving tracker state: {e}")
    
    def get_active_alerts(self, alert_level: str = None) -> List[TraderAlert]:
        """Get active trader alerts, optionally filtered by level"""
        alerts = self.active_alerts.copy()
        
        if alert_level:
            alerts = [a for a in alerts if a.alert_level.value == alert_level.lower()]
        
        return alerts
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get trader alert system statistics"""
        current_time = time.time()
        alerts_24h = [a for a in self.active_alerts if (current_time - a.created_at) <= 86400]
        
        alert_counts_by_type = {}
        alert_counts_by_level = {}
        
        for alert in alerts_24h:
            alert_counts_by_type[alert.alert_type.value] = alert_counts_by_type.get(alert.alert_type.value, 0) + 1
            alert_counts_by_level[alert.alert_level.value] = alert_counts_by_level.get(alert.alert_level.value, 0) + 1
        
        return {
            'total_active_alerts': len(self.active_alerts),
            'alerts_24h': len(alerts_24h),
            'tracked_traders': len(self.trader_history),
            'alert_types_24h': alert_counts_by_type,
            'alert_levels_24h': alert_counts_by_level,
            'last_monitoring_run': max(self.trader_history.values(), key=lambda x: x.get('last_updated', 0)).get('last_updated', 0) if self.trader_history else 0
        } 