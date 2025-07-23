"""
Bonding Curve Analyzer for Pump.fun Tokens
Tracks tokens from $0 to $69K graduation with velocity analysis and graduation prediction
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio

class BondingCurveAnalyzer:
    """Analyzes pump.fun bonding curve progression for optimal entry/exit timing"""
    
    def __init__(self):
        self.logger = logging.getLogger('BondingCurveAnalyzer')
        
        # Pump.fun bonding curve constants
        self.GRADUATION_THRESHOLD = 69000  # $69K market cap for Raydium graduation
        self.SUPPLY_BURN_AMOUNT = 12000    # $12K worth of supply burned at graduation
        
        # Bonding curve velocity tracking
        self.token_progressions = {}  # Track market cap over time for each token
        
        # Graduation prediction thresholds
        self.GRADUATION_WARNING_THRESHOLD = 55000   # 80% toward graduation
        self.GRADUATION_URGENT_THRESHOLD = 65000    # 94% toward graduation
        
        self.logger.info("🔥 Bonding Curve Analyzer initialized - tracking pump.fun progression to graduation")
    
    def track_token_progression(self, token_address: str, current_market_cap: float, timestamp: float = None):
        """Track a token's progression up the bonding curve"""
        if timestamp is None:
            timestamp = time.time()
            
        # Ensure market_cap is numeric
        try:
            current_market_cap = float(current_market_cap) if current_market_cap is not None else 0.0
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid market_cap value for {token_address}: {current_market_cap}")
            current_market_cap = 0.0
        
        if token_address not in self.token_progressions:
            self.token_progressions[token_address] = []
        
        self.token_progressions[token_address].append({
            'timestamp': timestamp,
            'market_cap': current_market_cap,
            'graduation_progress': (current_market_cap / self.GRADUATION_THRESHOLD) * 100
        })
        
        # Keep only last 100 data points per token
        if len(self.token_progressions[token_address]) > 100:
            self.token_progressions[token_address] = self.token_progressions[token_address][-100:]
    
    def calculate_bonding_curve_velocity(self, token_address: str, hours_lookback: float = 1.0) -> Dict:
        """Calculate how fast a token is moving up the bonding curve"""
        if token_address not in self.token_progressions:
            return {'velocity_per_hour': 0, 'acceleration': 0, 'confidence': 0}
        
        progression_data = self.token_progressions[token_address]
        if len(progression_data) < 2:
            return {'velocity_per_hour': 0, 'acceleration': 0, 'confidence': 0}
        
        # Filter to lookback period
        cutoff_time = time.time() - (hours_lookback * 3600)
        recent_data = [p for p in progression_data if p['timestamp'] >= cutoff_time]
        
        if len(recent_data) < 2:
            recent_data = progression_data[-2:]  # Use last 2 points
        
        # Calculate velocity (market cap growth per hour)
        time_span_hours = (recent_data[-1]['timestamp'] - recent_data[0]['timestamp']) / 3600
        if time_span_hours == 0:
            time_span_hours = 0.1  # Prevent division by zero
        
        market_cap_change = recent_data[-1]['market_cap'] - recent_data[0]['market_cap']
        velocity_per_hour = market_cap_change / time_span_hours
        
        # Calculate acceleration (change in velocity)
        acceleration = 0
        if len(recent_data) >= 3:
            mid_point = len(recent_data) // 2
            early_velocity = (recent_data[mid_point]['market_cap'] - recent_data[0]['market_cap']) / \
                           ((recent_data[mid_point]['timestamp'] - recent_data[0]['timestamp']) / 3600)
            late_velocity = (recent_data[-1]['market_cap'] - recent_data[mid_point]['market_cap']) / \
                          ((recent_data[-1]['timestamp'] - recent_data[mid_point]['timestamp']) / 3600)
            acceleration = late_velocity - early_velocity
        
        # Confidence based on data points and consistency
        confidence = min(len(recent_data) / 10, 1.0)  # More data = higher confidence
        
        return {
            'velocity_per_hour': velocity_per_hour,
            'acceleration': acceleration,
            'confidence': confidence,
            'data_points': len(recent_data),
            'time_span_hours': time_span_hours
        }
    
    def predict_graduation_timing(self, token_address: str) -> Dict:
        """Predict when a token will reach $69K graduation threshold"""
        if token_address not in self.token_progressions:
            return {'predicted_hours': None, 'confidence': 0, 'likelihood': 'UNKNOWN'}
        
        progression_data = self.token_progressions[token_address]
        if not progression_data:
            return {'predicted_hours': None, 'confidence': 0, 'likelihood': 'UNKNOWN'}
        
        current_market_cap = progression_data[-1]['market_cap']
        remaining_to_graduation = self.GRADUATION_THRESHOLD - current_market_cap
        
        if remaining_to_graduation <= 0:
            return {'predicted_hours': 0, 'confidence': 1.0, 'likelihood': 'GRADUATED'}
        
        # Get velocity analysis
        velocity_data = self.calculate_bonding_curve_velocity(token_address, hours_lookback=2.0)
        velocity_per_hour = velocity_data['velocity_per_hour']
        
        if velocity_per_hour <= 0:
            return {'predicted_hours': float('inf'), 'confidence': 0, 'likelihood': 'STALLED'}
        
        # Predict graduation time based on current velocity
        predicted_hours = remaining_to_graduation / velocity_per_hour
        
        # Factor in acceleration for more accurate prediction
        if velocity_data['acceleration'] > 0:
            # Accelerating - graduation will come faster
            predicted_hours *= 0.8
        elif velocity_data['acceleration'] < 0:
            # Decelerating - graduation will take longer
            predicted_hours *= 1.2
        
        # Determine likelihood
        if predicted_hours <= 6:
            likelihood = 'IMMINENT'
        elif predicted_hours <= 24:
            likelihood = 'LIKELY'
        elif predicted_hours <= 72:
            likelihood = 'POSSIBLE'
        else:
            likelihood = 'UNLIKELY'
        
        return {
            'predicted_hours': predicted_hours,
            'confidence': velocity_data['confidence'],
            'likelihood': likelihood,
            'current_market_cap': current_market_cap,
            'remaining_to_graduation': remaining_to_graduation,
            'velocity_per_hour': velocity_per_hour
        }
    
    def get_bonding_curve_stage(self, market_cap: float) -> Dict:
        """Determine what stage of the bonding curve a token is in"""
        # Ensure market_cap is numeric (handle string inputs from APIs)
        try:
            market_cap = float(market_cap) if market_cap is not None else 0.0
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid market_cap value: {market_cap}, defaulting to 0")
            market_cap = 0.0
            
        graduation_progress = (market_cap / self.GRADUATION_THRESHOLD) * 100
        
        if market_cap < 1000:
            stage = 'STAGE_0_LAUNCH'
            profit_potential = '10-50x'
            risk_level = 'EXTREME'
        elif market_cap < 5000:
            stage = 'STAGE_0_MOMENTUM'
            profit_potential = '5-25x'
            risk_level = 'VERY_HIGH'
        elif market_cap < 15000:
            stage = 'STAGE_1_GROWTH'
            profit_potential = '3-15x'
            risk_level = 'HIGH'
        elif market_cap < 35000:
            stage = 'STAGE_2_EXPANSION'
            profit_potential = '2-8x'
            risk_level = 'MEDIUM'
        elif market_cap < 55000:
            stage = 'STAGE_2_MATURATION'
            profit_potential = '1.5-4x'
            risk_level = 'MEDIUM'
        elif market_cap < 65000:
            stage = 'STAGE_3_PRE_GRADUATION'
            profit_potential = '1.2-2x'
            risk_level = 'LOW'
        else:
            stage = 'STAGE_3_GRADUATION_IMMINENT'
            profit_potential = '1.1-1.5x'
            risk_level = 'VERY_LOW'
        
        return {
            'stage': stage,
            'profit_potential': profit_potential,
            'risk_level': risk_level,
            'graduation_progress_pct': graduation_progress,
            'graduation_progress_dollars': market_cap,
            'remaining_to_graduation': max(0, self.GRADUATION_THRESHOLD - market_cap)
        }
    
    def calculate_optimal_position_sizing(self, market_cap: float, wallet_type: str) -> Dict:
        """Calculate optimal position sizing based on bonding curve stage"""
        # Type conversion handled in get_bonding_curve_stage
        stage_info = self.get_bonding_curve_stage(market_cap)
        stage = stage_info['stage']
        
        # Position sizing by wallet type and bonding curve stage
        position_recommendations = {
            'discovery_scout': {
                'STAGE_0_LAUNCH': 2.0,        # 2% - maximum early opportunity
                'STAGE_0_MOMENTUM': 1.5,      # 1.5% - confirmed momentum
                'STAGE_1_GROWTH': 1.0,        # 1% - growth phase
                'STAGE_2_EXPANSION': 0.5,     # 0.5% - later stage
                'STAGE_2_MATURATION': 0.2,    # 0.2% - minimal exposure
                'STAGE_3_PRE_GRADUATION': 0,  # 0% - too late for discovery
                'STAGE_3_GRADUATION_IMMINENT': 0
            },
            'conviction_core': {
                'STAGE_0_LAUNCH': 1.0,        # 1% - early but risky
                'STAGE_0_MOMENTUM': 3.0,      # 3% - optimal entry
                'STAGE_1_GROWTH': 4.0,        # 4% - maximum conviction
                'STAGE_2_EXPANSION': 3.0,     # 3% - good opportunity
                'STAGE_2_MATURATION': 2.0,    # 2% - reduced exposure
                'STAGE_3_PRE_GRADUATION': 1.0, # 1% - minimal
                'STAGE_3_GRADUATION_IMMINENT': 0
            },
            'moonshot_hunter': {
                'STAGE_0_LAUNCH': 0,          # 0% - too early/risky
                'STAGE_0_MOMENTUM': 0,        # 0% - still too early
                'STAGE_1_GROWTH': 1.0,        # 1% - early moonshot
                'STAGE_2_EXPANSION': 3.0,     # 3% - building conviction
                'STAGE_2_MATURATION': 5.0,    # 5% - maximum moonshot
                'STAGE_3_PRE_GRADUATION': 3.0, # 3% - pre-graduation surge
                'STAGE_3_GRADUATION_IMMINENT': 1.0  # 1% - graduation play
            }
        }
        
        recommended_position = position_recommendations.get(wallet_type, {}).get(stage, 0)
        
        return {
            'recommended_position_pct': recommended_position,
            'stage': stage,
            'reasoning': f"{wallet_type.replace('_', ' ').title()} optimal for {stage.replace('_', ' ').lower()}",
            'profit_potential': stage_info['profit_potential'],
            'risk_level': stage_info['risk_level']
        }
    
    def generate_graduation_alerts(self, token_address: str, current_market_cap: float) -> List[Dict]:
        """Generate graduation alerts based on bonding curve progression"""
        alerts = []
        
        # Track progression
        self.track_token_progression(token_address, current_market_cap)
        
        # Get prediction
        graduation_prediction = self.predict_graduation_timing(token_address)
        
        # Generate alerts based on thresholds
        if current_market_cap >= self.GRADUATION_URGENT_THRESHOLD:
            alerts.append({
                'urgency': 'CRITICAL',
                'message': f'🚨 GRADUATION IMMINENT: {token_address[:8]}... at ${current_market_cap:,.0f} (94% to graduation)',
                'action': 'IMMEDIATE_EXIT',
                'recommended_exit_pct': 90,
                'predicted_graduation_hours': graduation_prediction.get('predicted_hours', 'Unknown')
            })
        
        elif current_market_cap >= self.GRADUATION_WARNING_THRESHOLD:
            alerts.append({
                'urgency': 'HIGH',
                'message': f'⚠️ GRADUATION WARNING: {token_address[:8]}... at ${current_market_cap:,.0f} (80% to graduation)',
                'action': 'PARTIAL_EXIT',
                'recommended_exit_pct': 50,
                'predicted_graduation_hours': graduation_prediction.get('predicted_hours', 'Unknown')
            })
        
        # Velocity-based alerts
        velocity_data = self.calculate_bonding_curve_velocity(token_address)
        if velocity_data['velocity_per_hour'] > 10000:  # Very fast growth
            alerts.append({
                'urgency': 'MEDIUM',
                'message': f'🔥 RAPID BONDING CURVE: {token_address[:8]}... velocity ${velocity_data["velocity_per_hour"]:,.0f}/hour',
                'action': 'MONITOR_CLOSELY',
                'recommended_exit_pct': 0,
                'velocity_per_hour': velocity_data['velocity_per_hour']
            })
        
        return alerts
    
    def get_analytics_summary(self, token_address: str) -> Dict:
        """Get comprehensive bonding curve analytics for a token"""
        if token_address not in self.token_progressions:
            return {'error': 'Token not being tracked'}
        
        progression_data = self.token_progressions[token_address]
        if not progression_data:
            return {'error': 'No progression data available'}
        
        current_market_cap = progression_data[-1]['market_cap']
        
        # Get all analyses
        stage_info = self.get_bonding_curve_stage(current_market_cap)
        velocity_data = self.calculate_bonding_curve_velocity(token_address)
        graduation_prediction = self.predict_graduation_timing(token_address)
        
        # Calculate total progression
        if len(progression_data) > 1:
            total_growth = current_market_cap - progression_data[0]['market_cap']
            total_growth_pct = (total_growth / progression_data[0]['market_cap']) * 100 if progression_data[0]['market_cap'] > 0 else 0
        else:
            total_growth = 0
            total_growth_pct = 0
        
        return {
            'token_address': token_address,
            'current_market_cap': current_market_cap,
            'stage_analysis': stage_info,
            'velocity_analysis': velocity_data,
            'graduation_prediction': graduation_prediction,
            'progression_stats': {
                'total_growth_dollars': total_growth,
                'total_growth_percent': total_growth_pct,
                'data_points_tracked': len(progression_data),
                'tracking_duration_hours': (progression_data[-1]['timestamp'] - progression_data[0]['timestamp']) / 3600
            },
            'alerts': self.generate_graduation_alerts(token_address, current_market_cap)
        } 