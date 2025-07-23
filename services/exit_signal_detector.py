import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import statistics

from services.position_tracker import Position, PositionTracker
from api.birdeye_connector import BirdeyeAPI
from scripts.cross_platform_token_analyzer import CrossPlatformAnalyzer
from services.enhanced_cache_manager import EnhancedPositionCacheManager

@dataclass
class ExitSignal:
    """Represents an exit signal for a position"""
    position_id: int
    signal_strength: float  # 0-100, higher = stronger exit signal
    signal_type: str  # exit_recommended, profit_target, stop_loss, time_limit
    factors: Dict[str, float]  # Individual factor scores
    recommendation: str  # HOLD, REDUCE, EXIT
    confidence: float  # 0-1, confidence in the signal
    message: str  # Human readable explanation
    timestamp: int

class ExitSignalDetector:
    """Detects exit signals for tracked positions based on degrading conditions with enhanced caching"""
    
    def __init__(self, birdeye_api: BirdeyeAPI, position_tracker: PositionTracker, 
                 config: Dict[str, Any], logger: Optional[logging.Logger] = None,
                 enhanced_cache: Optional[EnhancedPositionCacheManager] = None):
        self.birdeye_api = birdeye_api
        self.position_tracker = position_tracker
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Enhanced caching for cost optimization
        if enhanced_cache:
            self.enhanced_cache = enhanced_cache
        else:
            # Create enhanced cache if not provided
            from core.cache_manager import CacheManager
            base_cache = CacheManager()
            self.enhanced_cache = EnhancedPositionCacheManager(base_cache, self.logger)
        
        # Initialize cross-platform analyzer for additional data
        self.cross_platform_analyzer = CrossPlatformAnalyzer(config, logger)
        
        # Exit signal thresholds (configurable)
        self.exit_thresholds = {
            "weak_exit": 40.0,      # Weak exit signal
            "moderate_exit": 60.0,   # Moderate exit signal  
            "strong_exit": 80.0,     # Strong exit signal
            "critical_exit": 90.0    # Critical exit signal
        }
        
        # Factor weights for exit score calculation
        self.factor_weights = {
            "volume_degradation": 0.25,
            "price_momentum": 0.25, 
            "whale_activity": 0.20,
            "community_sentiment": 0.15,
            "technical_indicators": 0.15
        }
        
        self.logger.info("🎯 ExitSignalDetector initialized with enhanced caching")
    
    async def analyze_position(self, position: Position) -> ExitSignal:
        """Analyze a single position and generate exit signal with enhanced caching"""
        try:
            self.logger.debug(f"🔍 Analyzing position {position.id} - {position.token_symbol}")
            
            # Register token for enhanced caching
            self.enhanced_cache.register_tracked_token(position.token_address, is_position=True)
            
            # Get current token data with caching
            current_data = await self._get_current_token_data_cached(position.token_address)
            if not current_data:
                return self._create_no_data_signal(position)
            
            # Update position with current price
            if 'price' in current_data:
                self.position_tracker.update_position_price(position.id, current_data['price'])
                position.current_price = current_data['price']
            
            # Calculate individual factor scores using cached data
            factors = {}
            
            # 1. Volume degradation analysis
            factors['volume_degradation'] = await self._analyze_volume_degradation_cached(
                position, current_data
            )
            
            # 2. Price momentum analysis  
            factors['price_momentum'] = await self._analyze_price_momentum_cached(
                position, current_data
            )
            
            # 3. Whale activity analysis
            factors['whale_activity'] = await self._analyze_whale_activity_cached(
                position, current_data
            )
            
            # 4. Community sentiment analysis
            factors['community_sentiment'] = await self._analyze_community_sentiment_cached(
                position, current_data
            )
            
            # 5. Technical indicators analysis
            factors['technical_indicators'] = await self._analyze_technical_indicators_cached(
                position, current_data
            )
            
            # Calculate overall exit score
            exit_score = self._calculate_exit_score(factors)
            
            # Add time-based modifiers
            exit_score = self._apply_time_modifiers(position, exit_score)
            
            # Check profit targets and stop losses
            exit_score = self._apply_price_targets(position, exit_score)
            
            # Generate recommendation and signal
            signal = self._generate_exit_signal(position, exit_score, factors)
            
            self.logger.debug(f"📊 Position {position.id} exit score: {exit_score:.1f}")
            return signal
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing position {position.id}: {e}")
            return self._create_error_signal(position, str(e))
    
    async def analyze_all_positions(self) -> List[ExitSignal]:
        """Analyze all active positions and return exit signals with batch optimization"""
        active_positions = self.position_tracker.get_all_active_positions()
        
        if not active_positions:
            self.logger.debug("📭 No active positions to analyze")
            return []
        
        self.logger.info(f"🔍 Analyzing {len(active_positions)} active positions")
        
        # Pre-warm cache for all position tokens
        position_addresses = [pos.token_address for pos in active_positions]
        tokens_needing_data = self.enhanced_cache.warm_cache_for_positions(position_addresses)
        
        # Batch fetch data for tokens that need cache warming
        if tokens_needing_data:
            await self._batch_warm_cache(tokens_needing_data)
        
        # Analyze positions concurrently for better performance
        tasks = [self.analyze_position(position) for position in active_positions]
        signals = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid signals
        valid_signals = []
        for i, signal in enumerate(signals):
            if isinstance(signal, Exception):
                self.logger.error(f"❌ Error analyzing position {active_positions[i].id}: {signal}")
            else:
                valid_signals.append(signal)
        
        # Log cache performance
        cache_stats = self.enhanced_cache.get_cache_statistics()
        self.logger.info(f"💰 Cache performance: {cache_stats['hit_rate_percent']:.1f}% hit rate, "
                        f"saved ~${cache_stats['estimated_cost_savings_usd']:.4f}")
        
        return valid_signals
    
    async def _batch_warm_cache(self, token_addresses: List[str]):
        """Batch warm cache for multiple tokens to reduce API costs"""
        try:
            # Use batch APIs to warm cache efficiently
            batch_size = 30  # Optimized based on testing
            
            for i in range(0, len(token_addresses), batch_size):
                batch = token_addresses[i:i + batch_size]
                
                # Batch get token overviews
                overviews = await self.birdeye_api.batch_get_token_overviews(batch)
                for address, overview in overviews.items():
                    if overview:
                        self.enhanced_cache.set_enhanced("position_token_overview", address, overview)
                
                # Batch get multi-price data
                prices = await self.birdeye_api.get_multi_price(batch)
                for address, price_data in prices.items():
                    if price_data:
                        self.enhanced_cache.set_enhanced("position_price", address, price_data)
                
                # Rate limiting between batches
                await asyncio.sleep(0.5)
                
            self.logger.info(f"🔥 Cache warmed for {len(token_addresses)} position tokens")
            
        except Exception as e:
            self.logger.error(f"❌ Error warming cache: {e}")
    
    async def _get_current_token_data_cached(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get current token data from cache or API with intelligent caching"""
        try:
            # Check cache first for position token overview
            cached_overview = self.enhanced_cache.get_enhanced("position_token_overview", token_address)
            
            if cached_overview:
                self.logger.debug(f"✅ Using cached overview data for {token_address}")
                overview_data = cached_overview
            else:
                # Get from API and cache
                overview_data = await self.birdeye_api.get_token_overview(token_address)
                if overview_data:
                    self.enhanced_cache.set_enhanced("position_token_overview", token_address, overview_data)
                else:
                    return None
            
            # Enhance with cross-platform data (cached separately)
            try:
                cross_platform_data = self.enhanced_cache.get_enhanced("cross_platform_correlation", token_address)
                if not cross_platform_data:
                    # Only fetch if not cached (expensive operation)
                    cross_platform_data = await self.cross_platform_analyzer.analyze_token(token_address)
                    if cross_platform_data:
                        self.enhanced_cache.set_enhanced("cross_platform_correlation", token_address, cross_platform_data)
                
                if cross_platform_data:
                    overview_data.update(cross_platform_data)
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Could not get cross-platform data for {token_address}: {e}")
            
            return overview_data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting token data for {token_address}: {e}")
            return None
    
    async def _analyze_volume_degradation_cached(self, position: Position, current_data: Dict) -> float:
        """Analyze volume degradation with caching optimization"""
        try:
            # Check cache for volume analysis
            cache_key = f"volume_analysis_{position.token_address}"
            cached_analysis = self.enhanced_cache.get_enhanced("position_volume", position.token_address, cache_key)
            
            if cached_analysis:
                return cached_analysis.get('degradation_score', 0.0)
            
            # Get entry conditions
            entry_conditions = position.get_entry_conditions_dict()
            entry_volume = entry_conditions.get('volume_24h', 0)
            
            # Get current volume
            current_volume = current_data.get('volume', {})
            if isinstance(current_volume, dict):
                current_volume_24h = current_volume.get('h24', 0)
            else:
                current_volume_24h = current_volume or 0
            
            if entry_volume <= 0 or current_volume_24h <= 0:
                return 0.0  # No data to compare
            
            # Calculate volume decline percentage
            volume_decline = (entry_volume - current_volume_24h) / entry_volume
            
            # Score based on decline severity
            if volume_decline >= 0.5:  # >50% decline
                score = 25.0
            elif volume_decline >= 0.3:  # >30% decline
                score = 15.0
            elif volume_decline >= 0.2:  # >20% decline
                score = 10.0
            elif volume_decline >= 0.1:  # >10% decline
                score = 5.0
            else:
                score = 0.0
            
            # Cache the analysis
            analysis_result = {
                'degradation_score': score,
                'volume_decline': volume_decline,
                'entry_volume': entry_volume,
                'current_volume': current_volume_24h,
                'timestamp': int(time.time())
            }
            self.enhanced_cache.set_enhanced("position_volume", position.token_address, analysis_result, cache_key)
            
            self.logger.debug(f"📉 Volume degradation score: {score:.1f} (decline: {volume_decline:.1%})")
            return score
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing volume degradation: {e}")
            return 0.0
    
    async def _analyze_price_momentum_cached(self, position: Position, current_data: Dict) -> float:
        """Analyze price momentum reversal with caching optimization"""
        try:
            # Check cache for momentum analysis
            cache_key = f"momentum_analysis_{position.token_address}"
            cached_analysis = self.enhanced_cache.get_enhanced("position_momentum", position.token_address, cache_key)
            
            if cached_analysis:
                return cached_analysis.get('momentum_score', 0.0)
            
            # Get OHLCV data for momentum analysis
            ohlcv_data = await self.birdeye_api.get_ohlcv_data(
                position.token_address, time_frame='5m', limit=20
            )
            
            if not ohlcv_data or len(ohlcv_data) < 10:
                return 0.0  # Not enough data
            
            # Calculate momentum indicators
            prices = [float(candle.get('c', 0)) for candle in ohlcv_data[-10:]]
            volumes = [float(candle.get('v', 0)) for candle in ohlcv_data[-10:]]
            
            if not prices or not volumes:
                return 0.0
            
            # Calculate price momentum (simple moving average slope)
            recent_prices = prices[-5:]
            older_prices = prices[-10:-5]
            
            recent_avg = statistics.mean(recent_prices)
            older_avg = statistics.mean(older_prices)
            
            momentum = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
            
            # Calculate volume-weighted momentum
            recent_volumes = volumes[-5:]
            older_volumes = volumes[-10:-5]
            
            volume_ratio = (statistics.mean(recent_volumes) / statistics.mean(older_volumes) 
                           if statistics.mean(older_volumes) > 0 else 1)
            
            # Score based on momentum reversal
            score = 0.0
            
            # Negative momentum (price declining)
            if momentum < -0.05:  # >5% decline
                score = 25.0
            elif momentum < -0.03:  # >3% decline
                score = 15.0
            elif momentum < -0.01:  # >1% decline
                score = 10.0
            
            # Reduce score if volume is also declining (double negative)
            if volume_ratio < 0.7:  # Volume down >30%
                score *= 1.5  # Increase exit signal
            
            # Cache the analysis
            analysis_result = {
                'momentum_score': score,
                'momentum': momentum,
                'volume_ratio': volume_ratio,
                'timestamp': int(time.time())
            }
            self.enhanced_cache.set_enhanced("position_momentum", position.token_address, analysis_result, cache_key)
            
            self.logger.debug(f"📊 Price momentum score: {score:.1f} (momentum: {momentum:.3f})")
            return min(score, 25.0)  # Cap at maximum
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing price momentum: {e}")
            return 0.0
    
    async def _analyze_whale_activity_cached(self, position: Position, current_data: Dict) -> float:
        """Analyze whale activity changes with caching optimization"""
        try:
            # Check cache for whale activity analysis
            cache_key = f"whale_activity_analysis_{position.token_address}"
            cached_analysis = self.enhanced_cache.get_enhanced("position_whale_activity", position.token_address, cache_key)
            
            if cached_analysis:
                return cached_analysis.get('whale_activity_score', 0.0)
            
            # Get current top traders
            current_traders = await self.birdeye_api.get_top_traders_optimized(
                position.token_address, time_frame="1h", sort_by="volume", limit=10
            )
            
            if not current_traders:
                return 0.0
            
            # Analyze trading patterns
            sell_volume = 0
            buy_volume = 0
            smart_money_selling = 0
            
            for trader in current_traders:
                volume = trader.get('volume', 0)
                side = trader.get('side', 'unknown')
                wallet = trader.get('wallet', '')
                
                # Check if this is a known smart money wallet
                is_smart_money = self.birdeye_api._is_smart_money_wallet(wallet)
                
                if side == 'sell':
                    sell_volume += volume
                    if is_smart_money:
                        smart_money_selling += volume
                elif side == 'buy':
                    buy_volume += volume
            
            total_volume = sell_volume + buy_volume
            if total_volume <= 0:
                return 0.0
            
            # Calculate sell pressure
            sell_ratio = sell_volume / total_volume
            smart_money_sell_ratio = smart_money_selling / total_volume if total_volume > 0 else 0
            
            # Score based on selling pressure
            score = 0.0
            
            # Heavy selling pressure
            if sell_ratio > 0.7:  # >70% selling
                score = 20.0
            elif sell_ratio > 0.6:  # >60% selling
                score = 15.0
            elif sell_ratio > 0.55:  # >55% selling
                score = 10.0
            
            # Bonus for smart money selling
            if smart_money_sell_ratio > 0.1:  # Smart money selling >10% of volume
                score += 10.0
            
            # Cache the analysis
            analysis_result = {
                'whale_activity_score': score,
                'sell_ratio': sell_ratio,
                'smart_money_sell_ratio': smart_money_sell_ratio,
                'timestamp': int(time.time())
            }
            self.enhanced_cache.set_enhanced("position_whale_activity", position.token_address, analysis_result, cache_key)
            
            self.logger.debug(f"🐋 Whale activity score: {score:.1f} (sell ratio: {sell_ratio:.2f})")
            return min(score, 20.0)  # Cap at maximum
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing whale activity: {e}")
            return 0.0
    
    async def _analyze_community_sentiment_cached(self, position: Position, current_data: Dict) -> float:
        """Analyze community sentiment decline with caching optimization"""
        try:
            # Check cache for community sentiment analysis
            cache_key = f"community_sentiment_analysis_{position.token_address}"
            cached_analysis = self.enhanced_cache.get_enhanced("position_community_sentiment", position.token_address, cache_key)
            
            if cached_analysis:
                return cached_analysis.get('sentiment_score', 0.0)
            
            # This would integrate with social media APIs in a full implementation
            # For now, we'll use proxy indicators from token data
            
            entry_conditions = position.get_entry_conditions_dict()
            
            # Check for declining social metrics (if available)
            score = 0.0
            
            # Placeholder for social sentiment analysis
            # In a full implementation, this would:
            # 1. Check Twitter/X mentions and sentiment
            # 2. Monitor Telegram group activity
            # 3. Analyze Discord activity
            # 4. Check Reddit discussions
            # 5. Monitor holder growth rate
            
            # For now, use holder count as a proxy
            current_holders = current_data.get('holders', 0)
            entry_holders = entry_conditions.get('holders', current_holders)
            
            if entry_holders > 0:
                holder_change = (current_holders - entry_holders) / entry_holders
                
                # Declining holder count indicates weakening community
                if holder_change < -0.1:  # >10% decline in holders
                    score = 15.0
                elif holder_change < -0.05:  # >5% decline
                    score = 10.0
                elif holder_change < 0:  # Any decline
                    score = 5.0
            
            # Cache the analysis
            analysis_result = {
                'sentiment_score': score,
                'holder_change': holder_change,
                'timestamp': int(time.time())
            }
            self.enhanced_cache.set_enhanced("position_community_sentiment", position.token_address, analysis_result, cache_key)
            
            self.logger.debug(f"👥 Community sentiment score: {score:.1f}")
            return score
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing community sentiment: {e}")
            return 0.0
    
    async def _analyze_technical_indicators_cached(self, position: Position, current_data: Dict) -> float:
        """Analyze technical indicators with caching optimization"""
        try:
            # Check cache for technical analysis
            cache_key = f"technical_analysis_{position.token_address}"
            cached_analysis = self.enhanced_cache.get_enhanced("position_technical_indicators", position.token_address, cache_key)
            
            if cached_analysis:
                return cached_analysis.get('technical_score', 0.0)
            
            # Get OHLCV data for technical analysis
            ohlcv_data = await self.birdeye_api.get_ohlcv_data(
                position.token_address, time_frame='15m', limit=30
            )
            
            if not ohlcv_data or len(ohlcv_data) < 20:
                return 0.0
            
            score = 0.0
            
            # Calculate RSI (Relative Strength Index)
            closes = [float(candle.get('c', 0)) for candle in ohlcv_data[-14:]]
            if len(closes) >= 14:
                rsi = self._calculate_rsi(closes)
                
                # Overbought conditions (RSI > 70) suggest potential reversal
                if rsi > 80:
                    score += 8.0
                elif rsi > 70:
                    score += 5.0
            
            # Check for support level breaks
            lows = [float(candle.get('l', 0)) for candle in ohlcv_data[-10:]]
            current_price = position.current_price
            
            if lows:
                recent_support = min(lows[-5:])  # Support from last 5 periods
                older_support = min(lows[-10:-5])  # Support from previous 5 periods
                
                # If current price breaks below recent support
                if current_price < recent_support * 0.98:  # 2% below support
                    score += 7.0
                elif current_price < recent_support:
                    score += 4.0
            
            # Cache the analysis
            analysis_result = {
                'technical_score': score,
                'rsi': rsi,
                'recent_support': recent_support,
                'older_support': older_support,
                'timestamp': int(time.time())
            }
            self.enhanced_cache.set_enhanced("position_technical_indicators", position.token_address, analysis_result, cache_key)
            
            self.logger.debug(f"📈 Technical indicators score: {score:.1f}")
            return min(score, 15.0)  # Cap at maximum
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing technical indicators: {e}")
            return 0.0
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI if not enough data
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = statistics.mean(gains[-period:])
        avg_loss = statistics.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_exit_score(self, factors: Dict[str, float]) -> float:
        """Calculate overall exit score from individual factors"""
        total_score = 0.0
        
        for factor, score in factors.items():
            weight = self.factor_weights.get(factor, 0.0)
            total_score += score * weight
        
        return min(total_score, 100.0)  # Cap at 100
    
    def _apply_time_modifiers(self, position: Position, base_score: float) -> float:
        """Apply time-based modifiers to exit score"""
        hold_time_hours = position.get_hold_time_hours()
        
        # Get user preferences for max hold time
        user_prefs = self.position_tracker.get_user_preferences(position.user_id)
        max_hold_hours = user_prefs.max_hold_time_hours if user_prefs else 48
        
        # Time-based score increases
        if hold_time_hours > max_hold_hours:
            # Force exit after max hold time
            return 100.0
        elif hold_time_hours > max_hold_hours * 0.8:  # 80% of max time
            base_score += 15.0
        elif hold_time_hours > max_hold_hours * 0.6:  # 60% of max time
            base_score += 10.0
        elif hold_time_hours > 4:  # After 4 hours
            base_score += 5.0
        
        return min(base_score, 100.0)
    
    def _apply_price_targets(self, position: Position, base_score: float) -> float:
        """Apply profit target and stop loss checks"""
        current_price = position.current_price
        entry_price = position.entry_price
        
        if entry_price <= 0:
            return base_score
        
        # Check profit target
        if position.profit_target and current_price >= position.profit_target:
            return 100.0  # Force exit at profit target
        
        # Check stop loss
        if position.stop_loss and current_price <= position.stop_loss:
            return 100.0  # Force exit at stop loss
        
        # Add score based on current P&L
        pnl_percent = position.get_pnl_percent()
        
        # Reduce exit score for profitable positions (unless very profitable)
        if pnl_percent > 50:  # >50% profit, consider taking some
            base_score += 20.0
        elif pnl_percent > 30:  # >30% profit
            base_score += 10.0
        elif pnl_percent > 0:  # Any profit
            base_score -= 5.0  # Slight bias to hold profitable positions
        elif pnl_percent < -15:  # >15% loss
            base_score += 15.0  # Encourage exit on large losses
        elif pnl_percent < -10:  # >10% loss
            base_score += 10.0
        
        return min(base_score, 100.0)
    
    def _generate_exit_signal(self, position: Position, exit_score: float, 
                            factors: Dict[str, float]) -> ExitSignal:
        """Generate final exit signal based on score and factors"""
        
        # Determine signal type and recommendation
        if exit_score >= self.exit_thresholds["critical_exit"]:
            signal_type = "critical_exit"
            recommendation = "EXIT"
            confidence = 0.9
        elif exit_score >= self.exit_thresholds["strong_exit"]:
            signal_type = "strong_exit"
            recommendation = "EXIT"
            confidence = 0.8
        elif exit_score >= self.exit_thresholds["moderate_exit"]:
            signal_type = "moderate_exit"
            recommendation = "REDUCE"
            confidence = 0.7
        elif exit_score >= self.exit_thresholds["weak_exit"]:
            signal_type = "weak_exit"
            recommendation = "HOLD"
            confidence = 0.6
        else:
            signal_type = "hold"
            recommendation = "HOLD"
            confidence = 0.5
        
        # Generate human-readable message
        message = self._generate_signal_message(position, exit_score, factors, recommendation)
        
        return ExitSignal(
            position_id=position.id,
            signal_strength=exit_score,
            signal_type=signal_type,
            factors=factors,
            recommendation=recommendation,
            confidence=confidence,
            message=message,
            timestamp=int(time.time())
        )
    
    def _generate_signal_message(self, position: Position, exit_score: float, 
                               factors: Dict[str, float], recommendation: str) -> str:
        """Generate human-readable signal message"""
        pnl_percent = position.get_pnl_percent()
        hold_time = position.get_hold_time_hours()
        
        # Find top contributing factors
        top_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:3]
        
        message_parts = [
            f"🎯 {position.token_symbol} Position Analysis",
            f"📊 Exit Score: {exit_score:.1f}/100",
            f"💰 P&L: {pnl_percent:+.1f}%",
            f"⏰ Hold Time: {hold_time:.1f}h",
            f"🎯 Recommendation: {recommendation}",
            ""
        ]
        
        if top_factors:
            message_parts.append("🔍 Key Factors:")
            for factor, score in top_factors:
                if score > 5:  # Only show significant factors
                    factor_name = factor.replace('_', ' ').title()
                    message_parts.append(f"• {factor_name}: {score:.1f}")
        
        return "\n".join(message_parts)
    
    def _create_no_data_signal(self, position: Position) -> ExitSignal:
        """Create signal when no current data is available"""
        return ExitSignal(
            position_id=position.id,
            signal_strength=0.0,
            signal_type="no_data",
            factors={},
            recommendation="HOLD",
            confidence=0.0,
            message=f"⚠️ No current data available for {position.token_symbol}",
            timestamp=int(time.time())
        )
    
    def _create_error_signal(self, position: Position, error: str) -> ExitSignal:
        """Create signal when analysis fails"""
        return ExitSignal(
            position_id=position.id,
            signal_strength=0.0,
            signal_type="error",
            factors={},
            recommendation="HOLD",
            confidence=0.0,
            message=f"❌ Analysis error for {position.token_symbol}: {error}",
            timestamp=int(time.time())
        ) 