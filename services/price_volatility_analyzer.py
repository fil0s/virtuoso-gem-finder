"""
Price Volatility Analyzer

Advanced price volatility analysis including multiple volatility metrics,
trend analysis, support/resistance detection, and volatility scoring.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
import statistics
import math
from datetime import datetime, timedelta

class PriceVolatilityAnalyzer:
    """
    Comprehensive price volatility and trend analysis
    """
    
    def __init__(self, birdeye_api, logger, config: Dict = None):
        self.birdeye_api = birdeye_api
        self.logger = logger
        self.config = config or {}
        
        # Configuration defaults
        self.lookback_hours = self.config.get('volatility_lookback_hours', 24)
        self.min_price_points = self.config.get('min_price_points', 10)
        self.high_volatility_threshold = self.config.get('high_volatility_threshold', 0.15)  # 15%
        self.extreme_volatility_threshold = self.config.get('extreme_volatility_threshold', 0.30)  # 30%
        
    async def analyze_price_volatility(self, token_address: str) -> Dict[str, Any]:
        """
        Comprehensive price volatility analysis
        """
        self.logger.info(f"📈 Starting price volatility analysis for {token_address[:8]}...")
        
        analysis = {
            'token_address': token_address,
            'analysis_timestamp': datetime.now().isoformat(),
            'price_data_available': False,
            'price_points_analyzed': 0,
            'timeframe_hours': self.lookback_hours,
            'current_price': 0,
            'volatility_metrics': {},
            'trend_analysis': {},
            'price_levels': {},
            'volatility_scoring': {},
            'stability_assessment': {},
            'volatility_alerts': [],
            'errors': []
        }
        
        try:
            # Fetch price data
            price_data = await self._fetch_price_data(token_address)
            
            if not price_data or len(price_data) < self.min_price_points:
                analysis['errors'].append(f"Insufficient price data (need {self.min_price_points}, got {len(price_data) if price_data else 0})")
                return analysis
            
            analysis['price_data_available'] = True
            analysis['price_points_analyzed'] = len(price_data)
            analysis['current_price'] = price_data[0]['price'] if price_data else 0
            
            # Calculate volatility metrics
            analysis['volatility_metrics'] = self._calculate_volatility_metrics(price_data)
            
            # Trend analysis
            analysis['trend_analysis'] = self._analyze_price_trends(price_data)
            
            # Support/resistance levels
            analysis['price_levels'] = self._identify_price_levels(price_data)
            
            # Volatility scoring
            analysis['volatility_scoring'] = self._calculate_volatility_scores(analysis)
            
            # Stability assessment
            analysis['stability_assessment'] = self._assess_price_stability(analysis)
            
            # Generate alerts
            analysis['volatility_alerts'] = self._generate_volatility_alerts(analysis)
            
            self.logger.info(f"✅ Price volatility analysis completed for {token_address[:8]}")
            
        except Exception as e:
            self.logger.error(f"❌ Price volatility analysis failed: {e}")
            analysis['errors'].append(f"Analysis failed: {str(e)}")
            
        return analysis
    
    async def _fetch_price_data(self, token_address: str) -> Optional[List[Dict]]:
        """
        Fetch price data from transactions
        """
        try:
            # Get recent transactions to extract price data
            transactions = await self.birdeye_api.get_token_transactions(
                token_address, 
                limit=50, 
                max_pages=5  # Up to 250 transactions
            )
            
            if not transactions:
                return None
            
            price_data = []
            current_time = datetime.now().timestamp()
            cutoff_time = current_time - (self.lookback_hours * 3600)
            
            for tx in transactions:
                try:
                    tx_time = tx.get('blockUnixTime', 0)
                    if tx_time < cutoff_time:
                        continue
                    
                    # Extract price from transaction
                    price = self._extract_transaction_price(tx)
                    if price > 0:
                        price_data.append({
                            'timestamp': tx_time,
                            'price': price,
                            'age_hours': (current_time - tx_time) / 3600
                        })
                        
                except Exception as e:
                    continue
            
            # Sort by timestamp (oldest first)
            price_data.sort(key=lambda x: x['timestamp'])
            
            # Remove duplicates and outliers
            price_data = self._clean_price_data(price_data)
            
            return price_data
            
        except Exception as e:
            self.logger.warning(f"Error fetching price data: {e}")
            return None
    
    def _extract_transaction_price(self, transaction: Dict) -> float:
        """
        Extract price from transaction data
        """
        try:
            # Try different price extraction methods
            
            # Method 1: Direct price field
            if 'price' in transaction:
                return float(transaction['price'])
            
            # Method 2: Calculate from quote/base amounts
            quote_amount = transaction.get('quoteAmount', 0)
            base_amount = transaction.get('baseAmount', 0)
            
            if quote_amount > 0 and base_amount > 0:
                return float(quote_amount) / float(base_amount)
            
            # Method 3: From nested data structures
            if 'quote' in transaction and 'base' in transaction:
                quote_data = transaction['quote']
                base_data = transaction['base']
                
                quote_amount = quote_data.get('amount', 0) if isinstance(quote_data, dict) else 0
                base_amount = base_data.get('amount', 0) if isinstance(base_data, dict) else 0
                
                if quote_amount > 0 and base_amount > 0:
                    return float(quote_amount) / float(base_amount)
            
            # Method 4: From volumeUsd and amount
            volume_usd = transaction.get('volumeUsd', 0)
            amount = transaction.get('amount', 0)
            
            if volume_usd > 0 and amount > 0:
                return float(volume_usd) / float(amount)
            
            return 0
            
        except Exception:
            return 0
    
    def _clean_price_data(self, price_data: List[Dict]) -> List[Dict]:
        """
        Clean price data by removing outliers and duplicates
        """
        if len(price_data) < 3:
            return price_data
        
        # Remove obvious outliers (prices that are >10x or <0.1x the median)
        prices = [p['price'] for p in price_data]
        median_price = statistics.median(prices)
        
        cleaned_data = []
        for data_point in price_data:
            price = data_point['price']
            if median_price * 0.1 <= price <= median_price * 10:
                cleaned_data.append(data_point)
        
        # Fix: Less aggressive deduplication - allow multiple prices per minute
        # Group by minute instead of exact timestamp to preserve stable price variations
        seen_minutes = {}
        final_data = []
        
        for data_point in reversed(cleaned_data):  # Start from latest
            timestamp = data_point['timestamp']
            # Round to minute for grouping
            minute_key = int(timestamp // 60) * 60
            
            # Keep up to 3 data points per minute to preserve price variations
            if minute_key not in seen_minutes:
                seen_minutes[minute_key] = []
            
            if len(seen_minutes[minute_key]) < 3:
                seen_minutes[minute_key].append(data_point)
                final_data.append(data_point)
        
        # Sort by timestamp (chronological order)
        final_data.sort(key=lambda x: x['timestamp'])
        
        return final_data
    
    def _calculate_volatility_metrics(self, price_data: List[Dict]) -> Dict[str, Any]:
        """
        Calculate comprehensive volatility metrics
        """
        if len(price_data) < 2:
            return {}
        
        prices = [p['price'] for p in price_data]
        
        # Calculate price changes (returns)
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                return_pct = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(return_pct)
        
        if not returns:
            return {}
        
        # Basic volatility metrics
        volatility_std = statistics.stdev(returns) if len(returns) > 1 else 0
        volatility_cv = volatility_std / statistics.mean(prices) if statistics.mean(prices) > 0 else 0
        
        # Price range metrics
        max_price = max(prices)
        min_price = min(prices)
        price_range_pct = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
        
        # Average True Range (ATR) approximation
        atr = self._calculate_atr_approximation(price_data)
        
        # Volatility over different timeframes
        short_term_volatility = self._calculate_timeframe_volatility(price_data, hours=6)
        medium_term_volatility = self._calculate_timeframe_volatility(price_data, hours=12)
        
        # Bollinger Band analysis
        bollinger_analysis = self._calculate_bollinger_bands(prices)
        
        metrics = {
            'standard_deviation': volatility_std,
            'coefficient_of_variation': volatility_cv,
            'price_range_percentage': price_range_pct,
            'max_price': max_price,
            'min_price': min_price,
            'average_true_range': atr,
            'short_term_volatility_6h': short_term_volatility,
            'medium_term_volatility_12h': medium_term_volatility,
            'bollinger_analysis': bollinger_analysis,
            'volatility_classification': self._classify_volatility(volatility_std),
            'return_statistics': {
                'mean_return': statistics.mean(returns),
                'max_return': max(returns),
                'min_return': min(returns),
                'positive_returns': sum(1 for r in returns if r > 0),
                'negative_returns': sum(1 for r in returns if r < 0)
            }
        }
        
        return metrics
    
    def _calculate_atr_approximation(self, price_data: List[Dict]) -> float:
        """
        Calculate Average True Range approximation
        """
        if len(price_data) < 2:
            return 0
        
        true_ranges = []
        for i in range(1, len(price_data)):
            current_price = price_data[i]['price']
            previous_price = price_data[i-1]['price']
            
            # Simplified ATR (just price difference)
            true_range = abs(current_price - previous_price)
            true_ranges.append(true_range)
        
        return statistics.mean(true_ranges) if true_ranges else 0
    
    def _calculate_timeframe_volatility(self, price_data: List[Dict], hours: int) -> float:
        """
        Calculate volatility for specific timeframe
        """
        current_time = datetime.now().timestamp()
        cutoff_time = current_time - (hours * 3600)
        
        timeframe_data = [p for p in price_data if p['timestamp'] >= cutoff_time]
        
        if len(timeframe_data) < 2:
            return 0
        
        prices = [p['price'] for p in timeframe_data]
        returns = []
        
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                return_pct = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(return_pct)
        
        return statistics.stdev(returns) if len(returns) > 1 else 0
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20) -> Dict[str, Any]:
        """
        Calculate Bollinger Bands analysis
        """
        if len(prices) < period:
            period = len(prices)
        
        if period < 2:
            return {}
        
        # Use available data
        recent_prices = prices[-period:]
        
        mean_price = statistics.mean(recent_prices)
        std_price = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0
        
        upper_band = mean_price + (2 * std_price)
        lower_band = mean_price - (2 * std_price)
        current_price = prices[-1]
        
        # Bollinger Band position
        if upper_band > lower_band:
            bb_position = (current_price - lower_band) / (upper_band - lower_band)
        else:
            bb_position = 0.5
        
        analysis = {
            'upper_band': upper_band,
            'middle_band': mean_price,
            'lower_band': lower_band,
            'current_price': current_price,
            'bb_position': bb_position,
            'bb_width': upper_band - lower_band,
            'squeeze_indicator': std_price < (mean_price * 0.02),  # Narrow bands
            'position_interpretation': self._interpret_bb_position(bb_position)
        }
        
        return analysis
    
    def _interpret_bb_position(self, position: float) -> str:
        """
        Interpret Bollinger Band position
        """
        if position >= 0.8:
            return "Near upper band (potentially overbought)"
        elif position >= 0.6:
            return "Above middle (bullish)"
        elif position >= 0.4:
            return "Near middle (neutral)"
        elif position >= 0.2:
            return "Below middle (bearish)"
        else:
            return "Near lower band (potentially oversold)"
    
    def _classify_volatility(self, volatility_std: float) -> str:
        """
        Classify volatility level
        """
        if volatility_std >= self.extreme_volatility_threshold:
            return "Extremely volatile"
        elif volatility_std >= self.high_volatility_threshold:
            return "Highly volatile"
        elif volatility_std >= 0.05:  # 5%
            return "Moderately volatile"
        elif volatility_std >= 0.02:  # 2%
            return "Low volatility"
        else:
            return "Very stable"
    
    def _analyze_price_trends(self, price_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze price trends using linear regression and momentum
        """
        if len(price_data) < 3:
            return {}
        
        prices = [p['price'] for p in price_data]
        timestamps = [p['timestamp'] for p in price_data]
        
        # Linear regression for trend
        trend_analysis = self._calculate_linear_trend(timestamps, prices)
        
        # Moving averages
        ma_analysis = self._calculate_moving_averages(prices)
        
        # Momentum analysis
        momentum_analysis = self._calculate_momentum(prices)
        
        # Support/resistance trend
        sr_trend = self._analyze_support_resistance_trend(price_data)
        
        analysis = {
            'linear_trend': trend_analysis,
            'moving_averages': ma_analysis,
            'momentum': momentum_analysis,
            'support_resistance_trend': sr_trend,
            'overall_trend_direction': self._determine_overall_trend(trend_analysis, ma_analysis, momentum_analysis)
        }
        
        return analysis
    
    def _calculate_linear_trend(self, timestamps: List[float], prices: List[float]) -> Dict[str, Any]:
        """
        Calculate linear regression trend
        """
        if len(timestamps) != len(prices) or len(prices) < 2:
            return {}
        
        n = len(prices)
        x = list(range(n))  # Use index instead of timestamp for simplicity
        y = prices
        
        # Calculate linear regression
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        intercept = y_mean - slope * x_mean
        
        # Calculate R-squared
        y_pred = [slope * x[i] + intercept for i in range(n)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Trend strength and direction
        trend_strength = abs(slope) / y_mean if y_mean > 0 else 0
        trend_direction = "upward" if slope > 0 else "downward" if slope < 0 else "sideways"
        
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_squared,
            'trend_strength': trend_strength,
            'trend_direction': trend_direction,
            'trend_reliability': r_squared  # Higher R² = more reliable trend
        }
    
    def _calculate_moving_averages(self, prices: List[float]) -> Dict[str, Any]:
        """
        Calculate moving averages analysis
        """
        if len(prices) < 3:
            return {}
        
        current_price = prices[-1]
        
        # Short-term MA (last 25% of data points)
        short_period = max(3, len(prices) // 4)
        short_ma = statistics.mean(prices[-short_period:])
        
        # Long-term MA (last 75% of data points)
        long_period = max(5, (len(prices) * 3) // 4)
        long_ma = statistics.mean(prices[-long_period:])
        
        # MA cross analysis
        ma_cross = "bullish" if short_ma > long_ma else "bearish"
        
        # Price vs MA analysis
        price_vs_short = (current_price - short_ma) / short_ma if short_ma > 0 else 0
        price_vs_long = (current_price - long_ma) / long_ma if long_ma > 0 else 0
        
        return {
            'short_term_ma': short_ma,
            'long_term_ma': long_ma,
            'current_price': current_price,
            'ma_cross_signal': ma_cross,
            'price_vs_short_ma_pct': price_vs_short * 100,
            'price_vs_long_ma_pct': price_vs_long * 100,
            'ma_divergence': abs(short_ma - long_ma) / long_ma if long_ma > 0 else 0
        }
    
    def _calculate_momentum(self, prices: List[float]) -> Dict[str, Any]:
        """
        Calculate price momentum indicators
        """
        if len(prices) < 4:
            return {}
        
        # Rate of change over different periods
        current_price = prices[-1]
        
        # Short-term momentum (last 25% of data)
        short_period = max(2, len(prices) // 4)
        short_momentum = (current_price - prices[-short_period]) / prices[-short_period] if prices[-short_period] > 0 else 0
        
        # Medium-term momentum (last 50% of data)
        medium_period = max(3, len(prices) // 2)
        medium_momentum = (current_price - prices[-medium_period]) / prices[-medium_period] if prices[-medium_period] > 0 else 0
        
        # Momentum classification
        momentum_strength = max(abs(short_momentum), abs(medium_momentum))
        
        if momentum_strength >= 0.2:  # 20%
            momentum_class = "Strong"
        elif momentum_strength >= 0.1:  # 10%
            momentum_class = "Moderate"
        elif momentum_strength >= 0.05:  # 5%
            momentum_class = "Weak"
        else:
            momentum_class = "Neutral"
        
        return {
            'short_term_momentum': short_momentum,
            'medium_term_momentum': medium_momentum,
            'momentum_strength': momentum_strength,
            'momentum_classification': momentum_class,
            'momentum_direction': "positive" if short_momentum > 0 else "negative"
        }
    
    def _analyze_support_resistance_trend(self, price_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze support and resistance level trends
        """
        if len(price_data) < 5:
            return {}
        
        prices = [p['price'] for p in price_data]
        
        # Find local minima (support) and maxima (resistance)
        supports = []
        resistances = []
        
        for i in range(1, len(prices) - 1):
            if prices[i] < prices[i-1] and prices[i] < prices[i+1]:
                supports.append(prices[i])
            elif prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                resistances.append(prices[i])
        
        current_price = prices[-1]
        
        analysis = {
            'support_levels': supports[-3:] if len(supports) >= 3 else supports,  # Last 3 supports
            'resistance_levels': resistances[-3:] if len(resistances) >= 3 else resistances,  # Last 3 resistances
            'nearest_support': max(supports) if supports else min(prices),
            'nearest_resistance': min(resistances) if resistances else max(prices),
            'support_strength': len(supports),
            'resistance_strength': len(resistances)
        }
        
        # Calculate distance to support/resistance
        if analysis['nearest_support'] > 0:
            analysis['distance_to_support_pct'] = ((current_price - analysis['nearest_support']) / analysis['nearest_support']) * 100
        
        if analysis['nearest_resistance'] > 0:
            analysis['distance_to_resistance_pct'] = ((analysis['nearest_resistance'] - current_price) / current_price) * 100
        
        return analysis
    
    def _determine_overall_trend(self, linear_trend: Dict, ma_analysis: Dict, momentum_analysis: Dict) -> str:
        """
        Determine overall trend direction
        """
        trend_signals = []
        
        # Linear trend signal
        if linear_trend.get('trend_direction') == 'upward':
            trend_signals.append(1)
        elif linear_trend.get('trend_direction') == 'downward':
            trend_signals.append(-1)
        else:
            trend_signals.append(0)
        
        # MA cross signal
        if ma_analysis.get('ma_cross_signal') == 'bullish':
            trend_signals.append(1)
        else:
            trend_signals.append(-1)
        
        # Momentum signal
        if momentum_analysis.get('momentum_direction') == 'positive':
            trend_signals.append(1)
        else:
            trend_signals.append(-1)
        
        # Calculate overall trend
        trend_sum = sum(trend_signals)
        
        if trend_sum >= 2:
            return "Bullish"
        elif trend_sum <= -2:
            return "Bearish"
        else:
            return "Neutral"
    
    def _identify_price_levels(self, price_data: List[Dict]) -> Dict[str, Any]:
        """
        Identify key price levels (support/resistance)
        """
        if len(price_data) < 5:
            return {}
        
        prices = [p['price'] for p in price_data]
        current_price = prices[-1]
        
        # Statistical levels
        mean_price = statistics.mean(prices)
        median_price = statistics.median(prices)
        std_price = statistics.stdev(prices) if len(prices) > 1 else 0
        
        # Key levels
        levels = {
            'current_price': current_price,
            'mean_price': mean_price,
            'median_price': median_price,
            'standard_deviation': std_price,
            'upper_1_std': mean_price + std_price,
            'lower_1_std': mean_price - std_price,
            'upper_2_std': mean_price + (2 * std_price),
            'lower_2_std': mean_price - (2 * std_price),
            'price_percentiles': {
                '95th': sorted(prices)[int(len(prices) * 0.95)] if len(prices) > 20 else max(prices),
                '75th': sorted(prices)[int(len(prices) * 0.75)] if len(prices) > 4 else sorted(prices)[-2],
                '25th': sorted(prices)[int(len(prices) * 0.25)] if len(prices) > 4 else sorted(prices)[1],
                '5th': sorted(prices)[int(len(prices) * 0.05)] if len(prices) > 20 else min(prices)
            }
        }
        
        # Level analysis
        levels['price_position'] = self._analyze_price_position(current_price, levels)
        
        return levels
    
    def _analyze_price_position(self, current_price: float, levels: Dict) -> Dict[str, Any]:
        """
        Analyze current price position relative to key levels
        """
        mean_price = levels['mean_price']
        std_price = levels['standard_deviation']
        
        # Standard deviation position
        if std_price > 0:
            std_position = (current_price - mean_price) / std_price
        else:
            std_position = 0
        
        # Percentile position
        percentiles = levels['price_percentiles']
        
        position_analysis = {
            'std_deviation_position': std_position,
            'above_mean': current_price > mean_price,
            'above_median': current_price > levels['median_price'],
            'percentile_range': self._determine_percentile_range(current_price, percentiles),
            'position_interpretation': self._interpret_price_position(std_position)
        }
        
        return position_analysis
    
    def _determine_percentile_range(self, current_price: float, percentiles: Dict) -> str:
        """
        Determine which percentile range the current price falls into
        """
        if current_price >= percentiles['95th']:
            return "Above 95th percentile"
        elif current_price >= percentiles['75th']:
            return "75th-95th percentile"
        elif current_price >= percentiles['25th']:
            return "25th-75th percentile"
        elif current_price >= percentiles['5th']:
            return "5th-25th percentile"
        else:
            return "Below 5th percentile"
    
    def _interpret_price_position(self, std_position: float) -> str:
        """
        Interpret price position relative to standard deviations
        """
        if std_position >= 2:
            return "Extremely high (>2 std above mean)"
        elif std_position >= 1:
            return "High (1-2 std above mean)"
        elif std_position >= 0.5:
            return "Above average (0.5-1 std above mean)"
        elif std_position >= -0.5:
            return "Near average (within 0.5 std)"
        elif std_position >= -1:
            return "Below average (0.5-1 std below mean)"
        elif std_position >= -2:
            return "Low (1-2 std below mean)"
        else:
            return "Extremely low (>2 std below mean)"
    
    def _calculate_volatility_scores(self, analysis: Dict) -> Dict[str, Any]:
        """
        Calculate comprehensive volatility scores
        """
        volatility_metrics = analysis.get('volatility_metrics', {})
        trend_analysis = analysis.get('trend_analysis', {})
        
        # Base volatility score (0-100, lower is better for stability)
        std_dev = volatility_metrics.get('standard_deviation', 0)
        volatility_score = min(100, std_dev * 500)  # Scale to 0-100
        
        # Trend reliability score (0-100, higher is better)
        r_squared = trend_analysis.get('linear_trend', {}).get('r_squared', 0)
        trend_reliability_score = r_squared * 100
        
        # Price stability score (0-100, higher is better)
        price_range_pct = volatility_metrics.get('price_range_percentage', 0)
        stability_score = max(0, 100 - price_range_pct)
        
        # Overall volatility grade
        overall_score = (100 - volatility_score + trend_reliability_score + stability_score) / 3
        
        if overall_score >= 80:
            grade = "A"
        elif overall_score >= 70:
            grade = "B"
        elif overall_score >= 60:
            grade = "C"
        elif overall_score >= 50:
            grade = "D"
        else:
            grade = "F"
        
        return {
            'volatility_score': volatility_score,
            'trend_reliability_score': trend_reliability_score,
            'stability_score': stability_score,
            'overall_score': overall_score,
            'volatility_grade': grade,
            'risk_level': self._determine_volatility_risk_level(volatility_score)
        }
    
    def _determine_volatility_risk_level(self, volatility_score: float) -> str:
        """
        Determine volatility risk level
        """
        if volatility_score >= 75:
            return "Extreme"
        elif volatility_score >= 50:
            return "High"
        elif volatility_score >= 25:
            return "Medium"
        else:
            return "Low"
    
    def _assess_price_stability(self, analysis: Dict) -> Dict[str, Any]:
        """
        Assess overall price stability
        """
        volatility_metrics = analysis.get('volatility_metrics', {})
        volatility_scoring = analysis.get('volatility_scoring', {})
        trend_analysis = analysis.get('trend_analysis', {})
        
        # Stability factors
        factors = []
        stability_score = 100
        
        # Volatility factor
        volatility_class = volatility_metrics.get('volatility_classification', '')
        if 'Extremely' in volatility_class:
            factors.append("Extremely high volatility")
            stability_score -= 40
        elif 'Highly' in volatility_class:
            factors.append("High volatility")
            stability_score -= 30
        elif 'Moderately' in volatility_class:
            factors.append("Moderate volatility")
            stability_score -= 20
        
        # Trend consistency factor
        trend_reliability = trend_analysis.get('linear_trend', {}).get('r_squared', 0)
        if trend_reliability < 0.3:
            factors.append("Inconsistent price trend")
            stability_score -= 15
        
        # Price range factor
        price_range = volatility_metrics.get('price_range_percentage', 0)
        if price_range > 100:  # >100% range
            factors.append("Extreme price range")
            stability_score -= 25
        elif price_range > 50:  # >50% range
            factors.append("Large price range")
            stability_score -= 15
        
        # Bollinger band analysis
        bb_analysis = volatility_metrics.get('bollinger_analysis', {})
        if bb_analysis.get('squeeze_indicator'):
            factors.append("Price compression detected")
            stability_score += 10  # Squeeze can indicate upcoming stability
        
        stability_score = max(0, stability_score)
        
        # Overall assessment
        if stability_score >= 80:
            assessment = "Very stable"
        elif stability_score >= 60:
            assessment = "Stable"
        elif stability_score >= 40:
            assessment = "Moderately stable"
        elif stability_score >= 20:
            assessment = "Unstable"
        else:
            assessment = "Highly unstable"
        
        return {
            'stability_score': stability_score,
            'stability_assessment': assessment,
            'stability_factors': factors,
            'recommendation': self._get_stability_recommendation(assessment)
        }
    
    def _get_stability_recommendation(self, assessment: str) -> str:
        """
        Get trading recommendation based on stability
        """
        if assessment in ["Very stable", "Stable"]:
            return "Suitable for conservative trading"
        elif assessment == "Moderately stable":
            return "Moderate risk - suitable for balanced trading"
        elif assessment == "Unstable":
            return "High risk - suitable only for aggressive trading"
        else:
            return "Extreme risk - avoid or use very tight stops"
    
    def _generate_volatility_alerts(self, analysis: Dict) -> List[str]:
        """
        Generate volatility-based alerts
        """
        alerts = []
        
        volatility_metrics = analysis.get('volatility_metrics', {})
        volatility_scoring = analysis.get('volatility_scoring', {})
        stability_assessment = analysis.get('stability_assessment', {})
        
        # Extreme volatility alerts
        volatility_class = volatility_metrics.get('volatility_classification', '')
        if 'Extremely' in volatility_class:
            alerts.append("🚨 EXTREME VOLATILITY: Price movements are extremely volatile")
        elif 'Highly' in volatility_class:
            alerts.append("⚠️ HIGH VOLATILITY: Significant price swings detected")
        
        # Risk level alerts
        risk_level = volatility_scoring.get('risk_level', '')
        if risk_level == 'Extreme':
            alerts.append("🚨 EXTREME VOLATILITY RISK: Unsuitable for conservative trading")
        elif risk_level == 'High':
            alerts.append("⚠️ HIGH VOLATILITY RISK: Use caution and tight stops")
        
        # Stability alerts
        stability_score = stability_assessment.get('stability_score', 100)
        if stability_score < 20:
            alerts.append("🚨 PRICE INSTABILITY: Highly unstable price action")
        elif stability_score < 40:
            alerts.append("⚠️ PRICE INSTABILITY: Unstable price movements")
        
        # Bollinger band alerts
        bb_analysis = volatility_metrics.get('bollinger_analysis', {})
        bb_position = bb_analysis.get('bb_position', 0.5)
        
        if bb_position >= 0.9:
            alerts.append("⚠️ OVERBOUGHT: Price near upper Bollinger band")
        elif bb_position <= 0.1:
            alerts.append("⚠️ OVERSOLD: Price near lower Bollinger band")
        
        return alerts 