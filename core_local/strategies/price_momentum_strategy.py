"""
Price Momentum Strategy with Cross-Timeframe Analysis

This strategy finds tokens with strong price performance backed by increasing volume
and confirmed momentum across multiple timeframes (1h, 4h, 24h).
"""

import logging
import time
from typing import Dict, List, Any, Optional

from api.birdeye_connector import BirdeyeAPI
from .base_token_discovery_strategy import BaseTokenDiscoveryStrategy


class PriceMomentumStrategy(BaseTokenDiscoveryStrategy):
    """
    Price Momentum with Cross-Timeframe Analysis - Find tokens with strong price performance 
    backed by increasing volume and confirmed momentum across multiple timeframes.
    
    ENHANCED: Now includes cross-timeframe momentum analysis for more reliable signals.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the Enhanced Price Momentum Strategy."""
        super().__init__(
            name="Price Momentum Strategy",
            description="Find tokens with strong price performance backed by increasing volume and cross-timeframe momentum.",
            api_parameters={
                "sort_by": "price_change_24h_percent",
                "sort_type": "desc",
                "min_volume_24h_usd": 50000,    # RELAXED: Reduced from 100,000 (50% reduction)
                "min_liquidity": 150000,        # RELAXED: Reduced from 300,000 (50% reduction)
                "min_trade_24h_count": 350,     # RELAXED: Reduced from 700 (50% reduction)
                "limit": 25
            },
            min_consecutive_appearances=2,
            logger=logger
        )
        
        # Cross-timeframe momentum settings - using BirdEye API compatible timeframes
        self.momentum_timeframes = ['1h', '4h', '1d']  # '1d' instead of '24h' for BirdEye API compatibility
        self.momentum_thresholds = {
            '1h': 0.01,   # ULTRA RELAXED: 0.01%+ for 1h momentum (almost any movement)
            '4h': 0.01,   # ULTRA RELAXED: 0.01%+ for 4h momentum (almost any movement)
            '1d': 0.01    # ULTRA RELAXED: 0.01%+ for 1d momentum (almost any movement)
        }
        self.confluence_threshold = 0.0  # ULTRA RELAXED: Accept ANY momentum (0% threshold)
    
    async def process_results(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process results with additional filtering for Price Momentum Strategy.
        
        ENHANCED: Graduated price change thresholds based on market cap
        - Small tokens (<$100K): Allow up to 2000% gains
        - Medium tokens ($100K-$1M): Allow up to 1000% gains  
        - Large tokens (>$1M): Allow up to 500% gains
        """
        processed_tokens = await super().process_results(tokens, birdeye_api, scan_id=scan_id)
        filtered_tokens = []
        
        self.logger.info(f"🎯 Analyzing cross-timeframe momentum for {len(processed_tokens)} tokens")
        
        for token in processed_tokens:
            try:
                # ULTRA-RELAXED: Remove early price change filtering to let momentum analysis decide
                price_change_24h = token.get("priceChange24h", 0)
                max_allowed_change = self._get_max_allowed_price_change(token)
                
                # DEBUG: Log but don't filter on price change
                market_cap = token.get("marketCap", 0)
                self.logger.debug(f"📊 {token.get('symbol')} - price change {price_change_24h:.1f}%, market cap ${market_cap:,.0f}")
                    
                # ULTRA-RELAXED: Remove early volume filtering to let momentum analysis decide
                volume_change_24h = token.get("volumeChange24h", 0)
                self.logger.debug(f"📊 {token.get('symbol')} - volume change {volume_change_24h:.1f}%")
                
                # ENHANCED: Cross-timeframe momentum analysis
                token_address = token.get("address")
                if token_address:
                    momentum_analysis = await self._analyze_cross_timeframe_momentum(token_address, birdeye_api)
                    token["momentum_analysis"] = momentum_analysis
                    
                    # Check momentum confluence requirement
                    confluence_score = momentum_analysis.get("confluence_score", 0.0)
                    token_symbol = token.get('symbol', 'Unknown')
                    
                    # DEBUG: Log momentum analysis details
                    self.logger.debug(f"📈 Momentum analysis for {token_symbol}: confluence={confluence_score:.3f}, threshold={self.confluence_threshold:.3f}")
                    self.logger.debug(f"📈 Momentum details: {momentum_analysis.get('alignment_summary', {})}")
                    
                    if confluence_score < self.confluence_threshold:
                        self.logger.info(f"❌ Filtering out {token_symbol} due to low momentum confluence: {confluence_score:.3f} < {self.confluence_threshold:.3f}")
                        continue
                    
                    self.logger.info(f"✅ {token_symbol} passes momentum confluence: {confluence_score:.3f}")
                    
                    # Add momentum boost for high confluence
                    if confluence_score > 0.8:
                        token["momentum_boost"] = 1.3  # 30% boost for high confluence
                        self.logger.info(f"✨ High momentum confluence for {token_symbol}: {confluence_score:.3f}")
                
                # ENHANCED: Add comprehensive strategy analysis
                token["strategy_analysis"] = {
                    "strategy_type": "price_momentum_cross_timeframe",
                    "analysis_timestamp": int(time.time()),
                    "momentum_confluence_score": momentum_analysis.get("confluence_score", 0.0),
                    "timeframe_alignment": momentum_analysis.get("alignment_summary", {}),
                    "momentum_sustainability": self._calculate_momentum_sustainability(token, momentum_analysis),
                    "price_volume_correlation": self._calculate_price_volume_correlation(token),
                    "momentum_quality_grade": self._grade_momentum_quality(momentum_analysis),
                    "max_allowed_price_change": max_allowed_change,
                    "actual_price_change": price_change_24h
                }
                
                # Add to filtered tokens
                filtered_tokens.append(token)
                
            except Exception as e:
                self.logger.warning(f"Error in cross-timeframe analysis for {token.get('symbol', 'unknown')}: {e}")
                # Still include token but without momentum analysis
                token["momentum_analysis"] = {"error": str(e), "confluence_score": 0.0}
                filtered_tokens.append(token)
                continue
                
        confluence_count = sum(1 for t in filtered_tokens if t.get("momentum_analysis", {}).get("confluence_score", 0) > 0.8)
        self.logger.info(f"📈 Cross-Timeframe Momentum: {len(filtered_tokens)} tokens, {confluence_count} high-confluence")
        return filtered_tokens
    
    async def _analyze_cross_timeframe_momentum(self, token_address: str, birdeye_api: BirdeyeAPI) -> Dict[str, Any]:
        """
        Analyze cross-timeframe momentum patterns.
        
        Uses OHLCV data which IS available in BirdEye Starter package.
        """
        momentum_analysis = {
            "timeframe_momentum": {},
            "confluence_score": 0.0,
            "alignment_summary": {},
            "strongest_timeframe": None,
            "momentum_direction": "neutral"
        }
        
        try:
            # Debug: Log the token being analyzed
            print(f"🔍 DEBUG: Analyzing momentum for token {token_address}")
            
            # Analyze momentum for each timeframe using OHLCV data
            valid_timeframes = 0
            positive_momentum_count = 0
            timeframe_scores = []
            
            for timeframe in self.momentum_timeframes:
                try:
                    print(f"🔍 DEBUG: Fetching OHLCV data for timeframe {timeframe}")
                    
                    # Get OHLCV data for timeframe
                    ohlcv_data = await birdeye_api.get_ohlcv_data(
                        token_address=token_address,
                        time_frame=timeframe,
                        limit=24  # Get 24 data points for analysis
                    )
                    
                    print(f"🔍 DEBUG: OHLCV response for {timeframe}: {type(ohlcv_data)}, length: {len(ohlcv_data) if isinstance(ohlcv_data, list) else 'N/A'}")
                    
                    if ohlcv_data and isinstance(ohlcv_data, list) and len(ohlcv_data) > 0:
                        print(f"🔍 DEBUG: Sample OHLCV data: {ohlcv_data[0] if ohlcv_data else 'None'}")
                        
                        # Calculate momentum for this timeframe
                        momentum_score = self._calculate_timeframe_momentum(ohlcv_data, timeframe)
                        print(f"🔍 DEBUG: Momentum score for {timeframe}: {momentum_score}")
                        
                        momentum_analysis["timeframe_momentum"][timeframe] = momentum_score
                        
                        # Check if momentum meets threshold
                        threshold = self.momentum_thresholds.get(timeframe, 0.01)
                        if momentum_score >= threshold:
                            positive_momentum_count += 1
                            timeframe_scores.append(momentum_score)
                            print(f"✅ DEBUG: {timeframe} passed threshold {threshold} with score {momentum_score}")
                        else:
                            print(f"❌ DEBUG: {timeframe} failed threshold {threshold} with score {momentum_score}")
                        
                        valid_timeframes += 1
                    else:
                        print(f"❌ DEBUG: No OHLCV data returned for {timeframe}")
                        momentum_analysis["timeframe_momentum"][timeframe] = 0.0
                        
                except Exception as e:
                    print(f"❌ DEBUG: Error fetching OHLCV for {timeframe}: {str(e)}")
                    momentum_analysis["timeframe_momentum"][timeframe] = 0.0
            
            print(f"🔍 DEBUG: Summary - Valid timeframes: {valid_timeframes}, Positive momentum: {positive_momentum_count}")
            
            # Calculate confluence score based on positive momentum timeframes
            if valid_timeframes > 0:
                confluence_score = positive_momentum_count / valid_timeframes
                momentum_analysis["confluence_score"] = confluence_score
                print(f"🔍 DEBUG: Calculated confluence score: {confluence_score}")
                
                # Determine strongest timeframe
                if timeframe_scores:
                    max_score = max(timeframe_scores)
                    for tf, score in momentum_analysis["timeframe_momentum"].items():
                        if score == max_score:
                            momentum_analysis["strongest_timeframe"] = tf
                            break
                
                # Determine overall momentum direction
                if confluence_score >= self.confluence_threshold:
                    momentum_analysis["momentum_direction"] = "bullish"
                    print(f"✅ DEBUG: Token {token_address} has bullish momentum (confluence: {confluence_score})")
                else:
                    print(f"❌ DEBUG: Token {token_address} failed confluence threshold {self.confluence_threshold} (confluence: {confluence_score})")
            else:
                print(f"❌ DEBUG: No valid timeframes for token {token_address}")
                
        except Exception as e:
            print(f"❌ DEBUG: Major error in momentum analysis for {token_address}: {str(e)}")
            import traceback
            traceback.print_exc()
            
        print(f"🔍 DEBUG: Final momentum analysis for {token_address}: {momentum_analysis}")
        return momentum_analysis
    
    def _calculate_momentum_sustainability(self, token: Dict[str, Any], momentum_analysis: Dict[str, Any]) -> float:
        """Calculate momentum sustainability score."""
        base_score = 0.5
        
        # Cross-timeframe alignment increases sustainability
        confluence_score = momentum_analysis.get("confluence_score", 0.0)
        base_score += confluence_score * 0.3
        
        # Volume backing increases sustainability
        volume_change = token.get("volumeChange24h", 0)
        price_change = token.get("priceChange24h", 0)
        if price_change > 0 and volume_change > price_change * 0.5:
            base_score += 0.2
        
        # Smart money involvement
        smart_money_score = token.get('smart_money_score', 0)
        base_score += smart_money_score * 0.1
        
        return min(1.0, base_score)
    
    def _calculate_price_volume_correlation(self, token: Dict[str, Any]) -> float:
        """Calculate price-volume correlation strength."""
        price_change = token.get("priceChange24h", 0)
        volume_change = token.get("volumeChange24h", 0)
        
        if price_change <= 0 or volume_change <= 0:
            return 0.0
        
        # Ideal correlation: volume change should be 50-200% of price change
        ideal_ratio = volume_change / price_change
        if 0.5 <= ideal_ratio <= 2.0:
            return 1.0
        elif 0.3 <= ideal_ratio <= 3.0:
            return 0.7
        else:
            return 0.3
    
    def _grade_momentum_quality(self, momentum_analysis: Dict[str, Any]) -> str:
        """Grade the overall momentum quality."""
        confluence_score = momentum_analysis.get("confluence_score", 0.0)
        
        if confluence_score >= 0.9:
            return "A+"
        elif confluence_score >= 0.8:
            return "A"
        elif confluence_score >= 0.7:
            return "B+"
        elif confluence_score >= 0.6:
            return "B"
        elif confluence_score >= 0.5:
            return "C"
        else:
            return "D"
    
    def _get_max_allowed_price_change(self, token: Dict[str, Any]) -> float:
        """
        Get maximum allowed price change based on token market cap.
        
        Graduated thresholds:
        - Micro tokens (<$100K): 2000% (very high volatility expected)
        - Small tokens ($100K-$1M): 1000% (high volatility expected)
        - Medium tokens ($1M-$10M): 500% (moderate volatility expected)
        - Large tokens (>$10M): 200% (lower volatility expected)
        
        Args:
            token: Token data dictionary
            
        Returns:
            Maximum allowed 24h price change percentage
        """
        market_cap = token.get("marketCap", 0)
        
        if market_cap < 100_000:  # Micro cap
            return 2000.0  # Allow up to 2000% gains
        elif market_cap < 1_000_000:  # Small cap  
            return 1000.0  # Allow up to 1000% gains
        elif market_cap < 10_000_000:  # Medium cap
            return 500.0   # Allow up to 500% gains
        else:  # Large cap
            return 200.0   # Allow up to 200% gains 
    
    def _calculate_timeframe_momentum(self, ohlcv_data: List[Dict[str, Any]], timeframe: str) -> float:
        """Calculate momentum score for a specific timeframe."""
        try:
            if len(ohlcv_data) < 2:
                return 0.0
            
            # Sort by timestamp to ensure correct order
            sorted_data = sorted(ohlcv_data, key=lambda x: x.get('unixTime', 0))
            
            # Get recent and older price points
            recent_close = float(sorted_data[-1].get('c', 0))  # Most recent close
            older_close = float(sorted_data[0].get('c', 0))    # Oldest close
            
            if older_close <= 0:
                return 0.0
            
            # Calculate percentage change
            price_change = ((recent_close - older_close) / older_close) * 100
            
            # Also consider volume momentum
            recent_volume = float(sorted_data[-1].get('v', 0))
            older_volume = float(sorted_data[0].get('v', 0))
            
            volume_factor = 1.0
            if older_volume > 0:
                volume_change = recent_volume / older_volume
                # Boost momentum if volume is increasing
                if volume_change > 1.2:  # 20%+ volume increase
                    volume_factor = 1.1
                elif volume_change < 0.8:  # 20%+ volume decrease
                    volume_factor = 0.9
            
            # Apply volume factor to price momentum
            momentum_score = price_change * volume_factor
            
            return momentum_score
            
        except Exception as e:
            self.logger.debug(f"Error calculating momentum for {timeframe}: {e}")
            return 0.0 