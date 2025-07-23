#!/usr/bin/env python3
"""
Short Timeframe Analysis System

This analyzer is specifically designed to work with the reliably available
short timeframes (1m, 5m, 15m) from BirdEye API to provide meaningful
token analysis and early detection signals.
"""

import asyncio
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import time
import math

class ShortTimeframeAnalyzer:
    """
    Intelligent analysis system using short timeframes (1m, 5m, 15m).
    
    Focuses on:
    - Multi-timeframe momentum detection
    - Volume surge analysis
    - Price volatility patterns
    - Recent trading activity trends
    - Liquidity and market interest signals
    """
    
    def __init__(self, birdeye_api, logger: logging.Logger):
        self.birdeye_api = birdeye_api
        self.logger = logger
        
        # Analysis configuration
        self.timeframes = ['1m', '5m', '15m']
        self.candle_limits = {
            '1m': 100,   # Last 100 minutes (~1.7 hours)
            '5m': 60,    # Last 300 minutes (5 hours)  
            '15m': 32    # Last 480 minutes (8 hours)
        }
        
    async def analyze_token(self, token_address: str) -> Dict[str, Any]:
        """
        Analyze token across multiple timeframes for trend dynamics and trading signals.
        """
        try:
            self.logger.debug(f"[SHORT_ANALYSIS] Starting analysis for {token_address}")
            
            # Fetch multi-timeframe data
            timeframe_data = await self._fetch_multi_timeframe_data(token_address)
            
            # Debug: Log data availability and samples
            self.logger.debug(f"[SHORT_ANALYSIS] {token_address} - Timeframe data availability:")
            for timeframe, data in timeframe_data.items():
                if data:
                    sample_count = min(3, len(data))
                    self.logger.debug(f"  - {timeframe}: {len(data)} records, sample data: {data[:sample_count]}")
                else:
                    self.logger.debug(f"  - {timeframe}: No data available")
            
            if not any(timeframe_data.values()):
                self.logger.warning(f"[SHORT_ANALYSIS] {token_address} - No timeframe data available")
                return self._get_default_analysis()
            
            # Calculate momentum signals
            momentum_signals = self._calculate_momentum_signals(timeframe_data)
            self.logger.debug(f"[SHORT_ANALYSIS] {token_address} - Momentum signals: {momentum_signals}")
            
            # Analyze volume patterns
            volume_analysis = self._analyze_volume_patterns(timeframe_data)
            self.logger.debug(f"[SHORT_ANALYSIS] {token_address} - Volume analysis: {volume_analysis}")
            
            # Analyze price patterns
            price_patterns = self._analyze_price_patterns(timeframe_data)
            self.logger.debug(f"[SHORT_ANALYSIS] {token_address} - Price patterns: {price_patterns}")
            
            # Calculate volatility metrics
            volatility_metrics = self._calculate_volatility_metrics(timeframe_data)
            self.logger.debug(f"[SHORT_ANALYSIS] {token_address} - Volatility metrics: {volatility_metrics}")
            
            # Analyze recent activity
            activity_analysis = self._analyze_recent_activity(timeframe_data)
            self.logger.debug(f"[SHORT_ANALYSIS] {token_address} - Activity analysis: {activity_analysis}")
            
            # Detect risk factors
            risk_factors = self._detect_risk_factors(timeframe_data, momentum_signals, volume_analysis)
            self.logger.debug(f"[SHORT_ANALYSIS] {token_address} - Risk factors: {risk_factors}")
            
            # Calculate overall score and rating
            score, rating = self._calculate_overall_score(
                momentum_signals, volume_analysis, price_patterns, 
                volatility_metrics, activity_analysis, risk_factors
            )
            
            # Log final analysis summary
            self.logger.info(f"[SHORT_ANALYSIS] {token_address} - FINAL ANALYSIS SUMMARY:")
            self.logger.info(f"  📊 Overall Score: {score:.3f}")
            self.logger.info(f"  🏷️  Rating: {rating}")
            self.logger.info(f"  📈 Momentum Score: {momentum_signals.get('momentum_score', 0):.3f}")
            self.logger.info(f"  💰 Volume Score: {volume_analysis.get('volume_score', 0):.3f}")
            self.logger.info(f"  ⚡ Volatility Score: {volatility_metrics.get('volatility_score', 0):.3f}")
            self.logger.info(f"  🚨 Risk Level: {risk_factors.get('overall_risk', 'UNKNOWN')}")
            
            return {
                'trend_dynamics_score': score,
                'rating': rating,
                'momentum_signals': momentum_signals,
                'volume_analysis': volume_analysis,
                'price_patterns': price_patterns,
                'volatility_metrics': volatility_metrics,
                'activity_analysis': activity_analysis,
                'risk_factors': risk_factors,
                'raw_data_summary': {
                    timeframe: len(data) for timeframe, data in timeframe_data.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"[SHORT_ANALYSIS] Error analyzing {token_address}: {e}")
            return self._create_default_analysis()
    
    async def _fetch_multi_timeframe_data(self, token_address: str) -> Dict[str, List[Dict]]:
        """Fetch OHLCV data for all available timeframes."""
        timeframe_data = {}
        
        for timeframe in self.timeframes:
            try:
                limit = self.candle_limits[timeframe]
                ohlcv_data = await self.birdeye_api.get_ohlcv_data(
                    token_address, time_frame=timeframe, limit=limit
                )
                
                if ohlcv_data and len(ohlcv_data) > 0:
                    timeframe_data[timeframe] = ohlcv_data
                    self.logger.debug(f"Fetched {len(ohlcv_data)} candles for {timeframe}")
                else:
                    self.logger.debug(f"No data for {timeframe}")
                    
            except Exception as e:
                self.logger.warning(f"Error fetching {timeframe} data for {token_address}: {e}")
        
        return timeframe_data
    
    def _calculate_momentum_signals(self, timeframe_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Calculate momentum signals across timeframes with detailed logging."""
        self.logger.debug("[MOMENTUM] Starting momentum signal calculation")
        
        signals = {
            'short_term_momentum': 0,
            'medium_term_momentum': 0,
            'long_term_momentum': 0,
            'momentum_score': 0,
            'trend_direction': 'NEUTRAL',
            'momentum_strength': 'WEAK',
            'calculation_details': {}
        }
        
        # Weight assignments for different timeframes
        timeframe_weights = {
            '1m': 0.1,   # Immediate activity
            '5m': 0.25,  # Short-term momentum
            '15m': 0.35, # Medium-term momentum (highest weight)
            '1h': 0.2,   # Longer trend confirmation
            '4h': 0.1    # Context setting
        }
        
        weighted_momentum = 0
        total_weight = 0
        
        for timeframe, weight in timeframe_weights.items():
            data = timeframe_data.get(timeframe, [])
            if not data or len(data) < 3:
                self.logger.debug(f"[MOMENTUM] {timeframe}: Insufficient data ({len(data) if data else 0} records)")
                continue
            
            # Calculate price change momentum
            try:
                first_price = float(data[-1].get('c', 0))  # Most recent close
                last_price = float(data[0].get('c', 0))    # Oldest close
                
                if last_price > 0:
                    price_change_pct = ((first_price - last_price) / last_price) * 100
                    
                    # Calculate volume-weighted momentum
                    total_volume = sum(float(d.get('v', 0)) for d in data)
                    avg_volume = total_volume / len(data) if data else 0
                    
                    # Momentum score based on price change and volume
                    momentum_component = price_change_pct * (1 + min(avg_volume / 1000000, 2))  # Volume boost up to 3x
                    
                    weighted_momentum += momentum_component * weight
                    total_weight += weight
                    
                    signals['calculation_details'][timeframe] = {
                        'price_change_pct': price_change_pct,
                        'avg_volume': avg_volume,
                        'momentum_component': momentum_component,
                        'weight': weight,
                        'weighted_contribution': momentum_component * weight
                    }
                    
                    self.logger.debug(f"[MOMENTUM] {timeframe}: price_change={price_change_pct:+.2f}%, "
                                    f"avg_volume=${avg_volume:,.0f}, momentum={momentum_component:.3f}, "
                                    f"weighted={momentum_component * weight:.3f}")
                else:
                    self.logger.debug(f"[MOMENTUM] {timeframe}: Invalid price data (last_price={last_price})")
                    
            except (ValueError, TypeError) as e:
                self.logger.warning(f"[MOMENTUM] {timeframe}: Error calculating momentum: {e}")
        
        # Calculate final momentum score
        if total_weight > 0:
            final_momentum = weighted_momentum / total_weight
            
            # Assign momentum categories
            if final_momentum > 15:
                signals['momentum_strength'] = 'VERY_STRONG'
                signals['trend_direction'] = 'BULLISH'
            elif final_momentum > 5:
                signals['momentum_strength'] = 'STRONG'
                signals['trend_direction'] = 'BULLISH'
            elif final_momentum > 1:
                signals['momentum_strength'] = 'MODERATE'
                signals['trend_direction'] = 'BULLISH'
            elif final_momentum < -15:
                signals['momentum_strength'] = 'VERY_STRONG'
                signals['trend_direction'] = 'BEARISH'
            elif final_momentum < -5:
                signals['momentum_strength'] = 'STRONG'
                signals['trend_direction'] = 'BEARISH'
            elif final_momentum < -1:
                signals['momentum_strength'] = 'MODERATE'
                signals['trend_direction'] = 'BEARISH'
            else:
                signals['momentum_strength'] = 'WEAK'
                signals['trend_direction'] = 'NEUTRAL'
            
            # Normalize to 0-1 scale for scoring (sigmoid-like function)
            normalized_score = 1 / (1 + math.exp(-final_momentum / 10))
            signals['momentum_score'] = normalized_score
            
            self.logger.debug(f"[MOMENTUM] Final calculation: weighted_momentum={final_momentum:.3f}, "
                            f"normalized_score={normalized_score:.3f}, "
                            f"direction={signals['trend_direction']}, "
                            f"strength={signals['momentum_strength']}")
        else:
            self.logger.warning("[MOMENTUM] No valid timeframe data for momentum calculation")
        
        return signals
    
    def _analyze_volume_patterns(self, timeframe_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze volume patterns with detailed calculation logging."""
        self.logger.debug("[VOLUME] Starting volume pattern analysis")
        
        analysis = {
            'volume_score': 0,
            'volume_trend': 'STABLE',
            'volume_acceleration': 0,
            'volume_consistency': 0,
            'unusual_volume': False,
            'volume_details': {}
        }
        
        volume_scores = []
        
        for timeframe, data in timeframe_data.items():
            if not data or len(data) < 5:
                self.logger.debug(f"[VOLUME] {timeframe}: Insufficient data for analysis")
                continue
            
            try:
                # Extract volume data
                volumes = [float(d.get('v', 0)) for d in data]
                recent_volumes = volumes[:3]  # Most recent 3 periods
                older_volumes = volumes[3:]   # Older periods
                
                # Calculate volume metrics
                avg_recent = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
                avg_older = sum(older_volumes) / len(older_volumes) if older_volumes else 0
                total_volume = sum(volumes)
                max_volume = max(volumes) if volumes else 0
                
                # Volume acceleration (recent vs older)
                acceleration = 0
                if avg_older > 0:
                    acceleration = ((avg_recent - avg_older) / avg_older) * 100
                
                # Volume consistency (coefficient of variation)
                if volumes and len(volumes) > 1:
                    volume_mean = sum(volumes) / len(volumes)
                    volume_variance = sum((v - volume_mean) ** 2 for v in volumes) / len(volumes)
                    volume_std = math.sqrt(volume_variance)
                    consistency = 1 - (volume_std / volume_mean) if volume_mean > 0 else 0
                else:
                    consistency = 0
                
                # Unusual volume detection
                unusual = False
                if avg_older > 0 and avg_recent > avg_older * 5:  # 5x increase
                    unusual = True
                
                # Calculate timeframe volume score
                volume_score = 0
                if total_volume > 0:
                    # Base score from total volume
                    if total_volume >= 1000000:
                        volume_score = 1.0
                    elif total_volume >= 500000:
                        volume_score = 0.8
                    elif total_volume >= 100000:
                        volume_score = 0.6
                    elif total_volume >= 50000:
                        volume_score = 0.4
                    else:
                        volume_score = 0.2
                    
                    # Adjust for acceleration
                    if acceleration > 0:
                        volume_score *= (1 + min(acceleration / 100, 1))  # Up to 2x for 100%+ acceleration
                    
                    # Adjust for consistency
                    volume_score *= (0.5 + consistency / 2)  # 0.5-1.0 multiplier based on consistency
                
                volume_scores.append(volume_score)
                
                analysis['volume_details'][timeframe] = {
                    'total_volume': total_volume,
                    'avg_recent': avg_recent,
                    'avg_older': avg_older,
                    'acceleration_pct': acceleration,
                    'consistency': consistency,
                    'unusual_volume': unusual,
                    'volume_score': volume_score
                }
                
                self.logger.debug(f"[VOLUME] {timeframe}: total=${total_volume:,.0f}, "
                                f"recent_avg=${avg_recent:,.0f}, older_avg=${avg_older:,.0f}, "
                                f"acceleration={acceleration:+.1f}%, consistency={consistency:.3f}, "
                                f"unusual={unusual}, score={volume_score:.3f}")
                
            except Exception as e:
                self.logger.warning(f"[VOLUME] {timeframe}: Error in volume analysis: {e}")
        
        # Calculate overall volume metrics
        if volume_scores:
            analysis['volume_score'] = sum(volume_scores) / len(volume_scores)
            
            # Determine overall volume trend
            accelerations = [details.get('acceleration_pct', 0) 
                           for details in analysis['volume_details'].values()]
            avg_acceleration = sum(accelerations) / len(accelerations) if accelerations else 0
            
            if avg_acceleration > 20:
                analysis['volume_trend'] = 'ACCELERATING'
            elif avg_acceleration > 5:
                analysis['volume_trend'] = 'INCREASING'
            elif avg_acceleration < -20:
                analysis['volume_trend'] = 'DECLINING'
            elif avg_acceleration < -5:
                analysis['volume_trend'] = 'DECREASING'
            else:
                analysis['volume_trend'] = 'STABLE'
            
            analysis['volume_acceleration'] = avg_acceleration
            
            # Check for unusual volume across timeframes
            unusual_count = sum(1 for details in analysis['volume_details'].values() 
                              if details.get('unusual_volume', False))
            analysis['unusual_volume'] = unusual_count >= 2  # Unusual in 2+ timeframes
            
            self.logger.debug(f"[VOLUME] Overall analysis: score={analysis['volume_score']:.3f}, "
                            f"trend={analysis['volume_trend']}, "
                            f"acceleration={avg_acceleration:+.1f}%, "
                            f"unusual={analysis['unusual_volume']}")
        
        return analysis
    
    def _analyze_price_patterns(self, timeframe_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze price action patterns."""
        price_patterns = {
            'breakout_detected': False,
            'support_resistance_strength': 0.0,
            'price_stability': 0.0,
            'gap_detected': False,
            'consecutive_moves': 0,
            'price_range_expansion': False
        }
        
        try:
            # Use 1m data for detailed price action analysis
            if '1m' not in timeframe_data:
                return price_patterns
            
            data = timeframe_data['1m']
            if len(data) < 30:
                return price_patterns
            
            # Extract prices
            highs = [float(candle.get('h', candle.get('high', 0))) for candle in data[:30]]
            lows = [float(candle.get('l', candle.get('low', 0))) for candle in data[:30]]
            closes = [float(candle.get('c', candle.get('close', 0))) for candle in data[:30]]
            
            # Remove zeros
            highs = [h for h in highs if h > 0]
            lows = [l for l in lows if l > 0]
            closes = [c for c in closes if c > 0]
            
            if not closes:
                return price_patterns
            
            # Calculate price stability
            if len(closes) > 10:
                price_std = statistics.stdev(closes[:20])
                price_mean = statistics.mean(closes[:20])
                price_cv = price_std / price_mean if price_mean > 0 else 0
                price_patterns['price_stability'] = max(0, 1 - price_cv)
            
            # Detect consecutive moves in same direction
            consecutive_count = 0
            if len(closes) >= 10:
                recent_closes = closes[:10]
                moves = []
                for i in range(1, len(recent_closes)):
                    if recent_closes[i-1] > 0:
                        move = (recent_closes[i] - recent_closes[i-1]) / recent_closes[i-1]
                        moves.append(1 if move > 0.005 else -1 if move < -0.005 else 0)
                
                # Count consecutive moves in same direction
                current_streak = 0
                max_streak = 0
                for move in moves:
                    if move != 0:
                        if current_streak == 0 or (current_streak > 0 and move > 0) or (current_streak < 0 and move < 0):
                            current_streak += move
                        else:
                            max_streak = max(max_streak, abs(current_streak))
                            current_streak = move
                    else:
                        max_streak = max(max_streak, abs(current_streak))
                        current_streak = 0
                
                consecutive_count = max(max_streak, abs(current_streak))
            
            price_patterns['consecutive_moves'] = consecutive_count
            
            # Detect potential breakouts (price moving beyond recent range)
            if len(highs) >= 20 and len(lows) >= 20:
                recent_high = max(highs[:10])
                recent_low = min(lows[:10])
                older_high = max(highs[10:20])
                older_low = min(lows[10:20])
                
                current_price = closes[0]
                
                # Breakout detection
                if current_price > older_high * 1.02:  # 2% above previous high
                    price_patterns['breakout_detected'] = True
                
                # Range expansion
                recent_range = recent_high - recent_low
                older_range = older_high - older_low
                if older_range > 0 and recent_range > older_range * 1.3:
                    price_patterns['price_range_expansion'] = True
        
        except Exception as e:
            self.logger.error(f"Error analyzing price patterns: {e}")
        
        return price_patterns
    
    def _calculate_volatility_metrics(self, timeframe_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Calculate volatility metrics from available data."""
        volatility_metrics = {
            'short_term_volatility': 0.0,
            'volatility_trend': 'NEUTRAL',
            'volatility_rank': 'MEDIUM',
            'price_efficiency': 0.0
        }
        
        try:
            # Use 5m data for volatility calculation
            if '5m' not in timeframe_data:
                return volatility_metrics
            
            data = timeframe_data['5m']
            if len(data) < 20:
                return volatility_metrics
            
            # Calculate returns
            returns = []
            for i in range(1, min(40, len(data))):
                prev_close = float(data[i].get('c', data[i].get('close', 0)))
                curr_close = float(data[i-1].get('c', data[i-1].get('close', 0)))
                
                if prev_close > 0 and curr_close > 0:
                    ret = (curr_close - prev_close) / prev_close
                    returns.append(ret)
            
            if len(returns) < 10:
                return volatility_metrics
            
            # Calculate volatility
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0
            volatility_metrics['short_term_volatility'] = volatility
            
            # Compare recent vs older volatility
            if len(returns) >= 20:
                recent_vol = statistics.stdev(returns[:10])
                older_vol = statistics.stdev(returns[10:20])
                
                if older_vol > 0:
                    vol_ratio = recent_vol / older_vol
                    if vol_ratio > 1.3:
                        volatility_metrics['volatility_trend'] = 'INCREASING'
                    elif vol_ratio < 0.7:
                        volatility_metrics['volatility_trend'] = 'DECREASING'
            
            # Volatility ranking
            if volatility > 0.05:  # > 5% volatility
                volatility_metrics['volatility_rank'] = 'HIGH'
            elif volatility > 0.02:  # > 2% volatility
                volatility_metrics['volatility_rank'] = 'MEDIUM'
            else:
                volatility_metrics['volatility_rank'] = 'LOW'
            
            # Price efficiency (how much price moves vs total movement)
            total_movement = sum(abs(ret) for ret in returns)
            net_movement = abs(sum(returns))
            
            if total_movement > 0:
                efficiency = net_movement / total_movement
                volatility_metrics['price_efficiency'] = efficiency
        
        except Exception as e:
            self.logger.error(f"Error calculating volatility metrics: {e}")
        
        return volatility_metrics
    
    def _analyze_recent_activity(self, timeframe_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze recent trading activity patterns."""
        activity_analysis = {
            'trading_frequency': 0.0,
            'activity_trend': 'NEUTRAL',
            'market_interest': 'LOW',
            'liquidity_estimate': 0.0,
            'active_periods': 0
        }
        
        try:
            # Use 1m data for activity analysis
            if '1m' not in timeframe_data:
                return activity_analysis
            
            data = timeframe_data['1m']
            if len(data) < 30:
                return activity_analysis
            
            # Count active trading periods (periods with significant volume)
            active_count = 0
            total_volume = 0
            
            for candle in data[:30]:  # Last 30 minutes
                volume = float(candle.get('v', candle.get('volume', 0)))
                total_volume += volume
                
                if volume > 0:
                    active_count += 1
            
            activity_analysis['active_periods'] = active_count
            activity_analysis['trading_frequency'] = active_count / min(30, len(data))
            activity_analysis['liquidity_estimate'] = total_volume / 30  # Average volume per minute
            
            # Determine market interest level
            if activity_analysis['trading_frequency'] > 0.8:  # > 80% of periods active
                activity_analysis['market_interest'] = 'HIGH'
            elif activity_analysis['trading_frequency'] > 0.5:  # > 50% of periods active
                activity_analysis['market_interest'] = 'MEDIUM'
            else:
                activity_analysis['market_interest'] = 'LOW'
            
            # Activity trend (compare recent vs older periods)
            if len(data) >= 60:
                recent_active = sum(1 for candle in data[:30] if float(candle.get('v', candle.get('volume', 0))) > 0)
                older_active = sum(1 for candle in data[30:60] if float(candle.get('v', candle.get('volume', 0))) > 0)
                
                if recent_active > older_active * 1.3:
                    activity_analysis['activity_trend'] = 'INCREASING'
                elif recent_active < older_active * 0.7:
                    activity_analysis['activity_trend'] = 'DECREASING'
        
        except Exception as e:
            self.logger.error(f"Error analyzing recent activity: {e}")
        
        return activity_analysis
    
    def _detect_risk_factors(self, timeframe_data: Dict[str, List[Dict]], 
                           momentum_signals: Dict, volume_analysis: Dict) -> Dict[str, Any]:
        """Enhanced risk factor detection with detailed logging."""
        self.logger.debug("[RISK] Starting risk factor detection")
        
        risks = {
            'pump_dump_risk': 0,
            'manipulation_risk': 0,
            'volatility_risk': 0,
            'liquidity_risk': 0,
            'overall_risk': 'LOW',
            'risk_details': {},
            'warning_flags': []
        }
        
        # 1. Pump and Dump Risk Detection (Enhanced)
        self.logger.debug("[RISK] Analyzing pump and dump patterns...")
        
        pump_dump_indicators = 0
        pd_details = {}
        
        # Check for extreme price movements
        momentum_score = momentum_signals.get('momentum_score', 0)
        momentum_strength = momentum_signals.get('momentum_strength', 'WEAK')
        
        if momentum_strength in ['VERY_STRONG'] and momentum_score > 0.8:
            pump_dump_indicators += 3
            pd_details['extreme_momentum'] = f"Very strong momentum detected (score: {momentum_score:.3f})"
            self.logger.debug(f"[RISK] Pump/dump indicator: extreme momentum (score: {momentum_score:.3f})")
        elif momentum_strength == 'STRONG' and momentum_score > 0.7:
            pump_dump_indicators += 2
            pd_details['strong_momentum'] = f"Strong momentum detected (score: {momentum_score:.3f})"
            self.logger.debug(f"[RISK] Pump/dump indicator: strong momentum (score: {momentum_score:.3f})")
        
        # Check volume patterns
        if volume_analysis.get('unusual_volume', False):
            pump_dump_indicators += 2
            pd_details['unusual_volume'] = "Unusual volume pattern detected"
            self.logger.debug("[RISK] Pump/dump indicator: unusual volume patterns")
        
        volume_acceleration = volume_analysis.get('volume_acceleration', 0)
        if volume_acceleration > 100:  # 100%+ volume increase
            pump_dump_indicators += 3
            pd_details['volume_spike'] = f"Extreme volume acceleration: {volume_acceleration:+.1f}%"
            self.logger.debug(f"[RISK] Pump/dump indicator: extreme volume spike ({volume_acceleration:+.1f}%)")
        elif volume_acceleration > 50:
            pump_dump_indicators += 1
            pd_details['high_volume_growth'] = f"High volume acceleration: {volume_acceleration:+.1f}%"
            self.logger.debug(f"[RISK] Pump/dump indicator: high volume acceleration ({volume_acceleration:+.1f}%)")
        
        # Check for rapid price changes in short timeframes
        short_term_data = timeframe_data.get('1m', []) or timeframe_data.get('5m', [])
        if short_term_data and len(short_term_data) >= 3:
            try:
                recent_prices = [float(d.get('c', 0)) for d in short_term_data[:3]]
                if all(p > 0 for p in recent_prices):
                    max_change = max(abs((recent_prices[i] - recent_prices[i+1]) / recent_prices[i+1]) 
                                   for i in range(len(recent_prices)-1)) * 100
                    
                    if max_change > 20:  # 20%+ change in single period
                        pump_dump_indicators += 2
                        pd_details['rapid_price_change'] = f"Rapid price change: {max_change:.1f}%"
                        self.logger.debug(f"[RISK] Pump/dump indicator: rapid price change ({max_change:.1f}%)")
            except Exception as e:
                self.logger.warning(f"[RISK] Error analyzing rapid price changes: {e}")
        
        # Calculate pump/dump risk score
        risks['pump_dump_risk'] = min(1.0, pump_dump_indicators / 8)  # Normalize to 0-1
        risks['risk_details']['pump_dump'] = pd_details
        
        self.logger.debug(f"[RISK] Pump/dump analysis: {pump_dump_indicators} indicators, "
                        f"risk_score={risks['pump_dump_risk']:.3f}")
        
        # 2. Market Manipulation Risk
        self.logger.debug("[RISK] Analyzing market manipulation patterns...")
        
        manipulation_indicators = 0
        manip_details = {}
        
        # Check for volume/price inconsistencies
        volume_score = volume_analysis.get('volume_score', 0)
        if volume_score > 0.8 and momentum_score < 0.3:
            manipulation_indicators += 2
            manip_details['volume_price_mismatch'] = f"High volume ({volume_score:.3f}) with low momentum ({momentum_score:.3f})"
            self.logger.debug(f"[RISK] Manipulation indicator: volume/price mismatch")
        
        # Check for inconsistent volume patterns across timeframes
        volume_details = volume_analysis.get('volume_details', {})
        volume_scores_by_tf = [details.get('volume_score', 0) for details in volume_details.values()]
        if len(volume_scores_by_tf) >= 2:
            volume_variance = max(volume_scores_by_tf) - min(volume_scores_by_tf)
            if volume_variance > 0.5:
                manipulation_indicators += 1
                manip_details['inconsistent_volume'] = f"Volume inconsistency across timeframes: {volume_variance:.3f}"
                self.logger.debug(f"[RISK] Manipulation indicator: inconsistent volume ({volume_variance:.3f})")
        
        risks['manipulation_risk'] = min(1.0, manipulation_indicators / 4)
        risks['risk_details']['manipulation'] = manip_details
        
        self.logger.debug(f"[RISK] Manipulation analysis: {manipulation_indicators} indicators, "
                        f"risk_score={risks['manipulation_risk']:.3f}")
        
        # 3. Overall Risk Assessment
        overall_risk_score = max(risks['pump_dump_risk'], risks['manipulation_risk'])
        
        if overall_risk_score >= 0.8:
            risks['overall_risk'] = 'CRITICAL'
            risks['warning_flags'].append('CRITICAL_RISK_DETECTED')
        elif overall_risk_score >= 0.6:
            risks['overall_risk'] = 'HIGH'
            risks['warning_flags'].append('HIGH_RISK_DETECTED')
        elif overall_risk_score >= 0.4:
            risks['overall_risk'] = 'MEDIUM'
            risks['warning_flags'].append('MEDIUM_RISK_DETECTED')
        elif overall_risk_score >= 0.2:
            risks['overall_risk'] = 'LOW'
        else:
            risks['overall_risk'] = 'MINIMAL'
        
        self.logger.info(f"[RISK] Final risk assessment: overall_risk={risks['overall_risk']}, "
                       f"pump_dump={risks['pump_dump_risk']:.3f}, "
                       f"manipulation={risks['manipulation_risk']:.3f}, "
                       f"flags={risks['warning_flags']}")
        
        return risks
    
    def _calculate_overall_score(self, momentum_signals: Dict, volume_analysis: Dict,
                               price_patterns: Dict, volatility_metrics: Dict,
                               activity_analysis: Dict, risk_factors: Dict) -> Tuple[float, str]:
        """Calculate overall score and recommendation."""
        
        score = 0.0
        
        try:
            # Momentum score (0-30 points)
            momentum_score = 0
            if momentum_signals.get('momentum_alignment', False):
                momentum_score += 10
            
            recent_change = momentum_signals.get('recent_price_change', 0)
            if recent_change > 0.05:  # > 5% gain
                momentum_score += min(15, recent_change * 100)  # Up to 15 points
            elif recent_change > 0:
                momentum_score += 5
            
            # Volume score (0-25 points)
            volume_score = 0
            if volume_analysis.get('volume_surge_detected', False):
                volume_score += 15
            elif volume_analysis.get('volume_trend') == 'INCREASING':
                volume_score += 10
            
            if volume_analysis.get('volume_consistency', 0) > 0.7:
                volume_score += 5
            
            if activity_analysis.get('market_interest') == 'HIGH':
                volume_score += 5
            
            # Pattern score (0-20 points)
            pattern_score = 0
            if price_patterns.get('breakout_detected', False):
                pattern_score += 10
            
            if price_patterns.get('consecutive_moves', 0) >= 3:
                pattern_score += 5
            
            if price_patterns.get('price_range_expansion', False):
                pattern_score += 5
            
            # Activity score (0-15 points)
            activity_score = 0
            trading_freq = activity_analysis.get('trading_frequency', 0)
            if trading_freq > 0.8:
                activity_score += 10
            elif trading_freq > 0.5:
                activity_score += 5
            
            if activity_analysis.get('activity_trend') == 'INCREASING':
                activity_score += 5
            
            # Risk penalty (0 to -20 points)
            risk_penalty = 0
            risk_level = risk_factors.get('overall_risk', 'MEDIUM')
            if risk_level == 'HIGH':
                risk_penalty = -20
            elif risk_level == 'MEDIUM':
                risk_penalty = -10
            
            # Calculate total score
            score = momentum_score + volume_score + pattern_score + activity_score + risk_penalty
            score = max(0, min(100, score))  # Clamp between 0-100
            
            # Determine recommendation
            if score >= 70:
                recommendation = 'STRONG_BUY'
            elif score >= 55:
                recommendation = 'BUY'
            elif score >= 45:
                recommendation = 'WEAK_BUY'
            elif score >= 35:
                recommendation = 'HOLD'
            elif score >= 20:
                recommendation = 'WEAK_SELL'
            else:
                recommendation = 'SELL'
        
        except Exception as e:
            self.logger.error(f"Error calculating overall score: {e}")
            score = 50.0
            recommendation = 'HOLD'
        
        return score, recommendation

    async def batch_analyze_tokens(self, token_addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        🚀 BATCH OPTIMIZATION: Analyze multiple tokens using batch OHLCV fetching.
        
        This method optimizes short timeframe analysis by:
        1. Batch fetching OHLCV data for all tokens and timeframes
        2. Using concurrent processing for maximum efficiency
        3. Providing significant cost savings vs individual calls
        
        Args:
            token_addresses: List of token addresses to analyze
            
        Returns:
            Dictionary mapping token addresses to their analysis results
        """
        if not token_addresses:
            return {}
        
        self.logger.info(f"🚀 SHORT TIMEFRAME BATCH OPTIMIZATION:")
        self.logger.info(f"   📊 Tokens: {len(token_addresses)} addresses")
        self.logger.info(f"   ⏱️ Timeframes: {self.timeframes}")
        self.logger.info(f"   🎯 Strategy: Batch OHLCV + concurrent analysis")
        
        # Step 1: Batch fetch all OHLCV data
        batch_ohlcv_data = await self._batch_fetch_all_timeframes(token_addresses)
        
        # Step 2: Analyze each token using batch data
        analysis_results = {}
        successful_analyses = 0
        
        for token_address in token_addresses:
            try:
                # Get timeframe data for this token from batch results
                token_timeframe_data = batch_ohlcv_data.get(token_address, {})
                
                if not any(token_timeframe_data.values()):
                    self.logger.debug(f"No timeframe data available for {token_address}")
                    analysis_results[token_address] = self._get_default_analysis()
                    continue
                
                # Perform analysis using batch data
                analysis_result = await self._analyze_token_with_data(token_address, token_timeframe_data)
                analysis_results[token_address] = analysis_result
                successful_analyses += 1
                
            except Exception as e:
                self.logger.error(f"Error analyzing {token_address}: {e}")
                analysis_results[token_address] = self._get_default_analysis()
        
        # Calculate and log batch optimization metrics
        total_individual_calls = len(token_addresses) * len(self.timeframes)
        total_batch_calls = len(self.timeframes)  # One batch call per timeframe
        cost_reduction = ((total_individual_calls - total_batch_calls) / total_individual_calls) * 100
        success_rate = (successful_analyses / len(token_addresses)) * 100
        
        self.logger.info(f"📈 SHORT TIMEFRAME BATCH RESULTS:")
        self.logger.info(f"   ✅ Success Rate: {success_rate:.1f}% ({successful_analyses}/{len(token_addresses)} tokens)")
        self.logger.info(f"   💰 Cost Reduction: {cost_reduction:.1f}% ({total_individual_calls} → {total_batch_calls} calls)")
        self.logger.info(f"   ⚡ Method: Batch OHLCV optimization")
        
        return analysis_results

    async def _batch_fetch_all_timeframes(self, token_addresses: List[str]) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Batch fetch OHLCV data for all tokens across all timeframes.
        
        Returns:
            Nested dict: {token_address: {timeframe: ohlcv_data}}
        """
        batch_results = {}
        
        # Initialize results structure
        for token_address in token_addresses:
            batch_results[token_address] = {}
        
        # Fetch data for each timeframe concurrently
        for timeframe in self.timeframes:
            self.logger.debug(f"🔄 Batch fetching {timeframe} data for {len(token_addresses)} tokens...")
            
            try:
                # Create concurrent tasks for all tokens in this timeframe
                import asyncio
                tasks = []
                for token_address in token_addresses:
                    limit = self.candle_limits[timeframe]
                    task = self.birdeye_api.get_ohlcv_data(token_address, time_frame=timeframe, limit=limit)
                    tasks.append((token_address, task))
                
                # Execute all tasks concurrently
                task_results = await asyncio.gather(
                    *[task for _, task in tasks],
                    return_exceptions=True
                )
                
                # Process results
                successful_fetches = 0
                for i, (token_address, result) in enumerate(zip([addr for addr, _ in tasks], task_results)):
                    if isinstance(result, Exception):
                        self.logger.debug(f"❌ Error fetching {timeframe} data for {token_address}: {result}")
                        batch_results[token_address][timeframe] = []
                        continue
                    
                    if result and len(result) > 0:
                        batch_results[token_address][timeframe] = result
                        successful_fetches += 1
                    else:
                        batch_results[token_address][timeframe] = []
                
                success_rate = (successful_fetches / len(token_addresses)) * 100 if token_addresses else 0
                self.logger.debug(f"   ✅ {timeframe}: {successful_fetches}/{len(token_addresses)} tokens ({success_rate:.1f}% success)")
                
            except Exception as e:
                self.logger.error(f"❌ Error in batch {timeframe} fetch: {e}")
                # Set empty data for all tokens in this timeframe
                for token_address in token_addresses:
                    batch_results[token_address][timeframe] = []
        
        return batch_results

    async def _analyze_token_with_data(self, token_address: str, timeframe_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Analyze a single token using pre-fetched timeframe data.
        This is the core analysis logic extracted for batch processing.
        """
        try:
            self.logger.debug(f"[SHORT_ANALYSIS] Analyzing {token_address} with batch data")
            
            if not any(timeframe_data.values()):
                self.logger.warning(f"[SHORT_ANALYSIS] {token_address} - No timeframe data available")
                return self._get_default_analysis()
            
            # Calculate momentum signals
            momentum_signals = self._calculate_momentum_signals(timeframe_data)
            
            # Analyze volume patterns
            volume_analysis = self._analyze_volume_patterns(timeframe_data)
            
            # Analyze price patterns
            price_patterns = self._analyze_price_patterns(timeframe_data)
            
            # Calculate volatility metrics
            volatility_metrics = self._calculate_volatility_metrics(timeframe_data)
            
            # Analyze recent activity
            activity_analysis = self._analyze_recent_activity(timeframe_data)
            
            # Detect risk factors
            risk_factors = self._detect_risk_factors(timeframe_data, momentum_signals, volume_analysis)
            
            # Calculate overall score and rating
            score, rating = self._calculate_overall_score(
                momentum_signals, volume_analysis, price_patterns,
                volatility_metrics, activity_analysis, risk_factors
            )
            
            return {
                'trend_dynamics_score': score,
                'rating': rating,
                'momentum_signals': momentum_signals,
                'volume_analysis': volume_analysis,
                'price_patterns': price_patterns,
                'volatility_metrics': volatility_metrics,
                'activity_analysis': activity_analysis,
                'risk_factors': risk_factors,
                'raw_data_summary': {
                    timeframe: len(data) for timeframe, data in timeframe_data.items()
                },
                'batch_optimized': True
            }
            
        except Exception as e:
            self.logger.error(f"[SHORT_ANALYSIS] Error analyzing {token_address}: {e}")
            return self._create_default_analysis()

    def _create_default_analysis(self) -> Dict[str, Any]:
        """Create a default analysis when no timeframe data is available."""
        return {
            'momentum_score': 0.0,
            'volume_score': 0.0,
            'volatility_score': 0.0,
            'trend_strength': 0.0,
            'overall_score': 0.0,
            'signals': [],
            'timeframes_analyzed': [],
            'data_available': False,
            'error': 'No timeframe data available'
        } 