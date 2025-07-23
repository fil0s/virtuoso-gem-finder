# Phase 2: Core Analytics Implementation (Week 2)

## Prerequisites
✅ Phase 1 must be completed and tested
✅ All Phase 1 integration tests passing
✅ Cache system working (>0% hit rate)

---

## 🔧 Task 2.1: Implement Trend Confirmation System

### Step 1: Create New Trend Analysis Module
**Create File:** `services/trend_confirmation_analyzer.py`

```python
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TrendConfirmationAnalyzer:
    """Multi-timeframe trend confirmation to filter out post-pump tokens"""
    
    def __init__(self, birdeye_api_key: str):
        self.api_key = birdeye_api_key
        self.base_url = "https://public-api.birdeye.so"
        self.required_timeframes = ['1h', '4h', '1d']
        self.ema_periods = [20, 50]
        
        # Trend confirmation requirements
        self.min_timeframe_consensus = 0.67  # 2/3 timeframes must agree
        self.min_trend_score = 60  # Minimum score to pass
        
    async def analyze_trend_structure(self, token_address: str) -> Dict:
        """Comprehensive trend analysis across multiple timeframes"""
        
        logger.info(f"Analyzing trend structure for {token_address}")
        
        try:
            # Fetch OHLCV data for all timeframes
            trend_data = {}
            
            for timeframe in self.required_timeframes:
                logger.debug(f"Fetching {timeframe} data for {token_address}")
                ohlcv = await self._fetch_ohlcv_data(token_address, timeframe)
                
                if ohlcv:
                    trend_data[timeframe] = await self._analyze_timeframe_trend(ohlcv, timeframe)
                else:
                    logger.warning(f"No {timeframe} data available for {token_address}")
                    trend_data[timeframe] = self._default_timeframe_analysis()
            
            # Calculate overall trend metrics
            result = {
                'trend_score': self._calculate_trend_score(trend_data),
                'trend_direction': self._determine_trend_direction(trend_data),
                'ema_alignment': self._check_ema_alignment(trend_data),
                'higher_structure': self._check_higher_structure(trend_data),
                'timeframe_consensus': self._calculate_consensus(trend_data),
                'timeframe_details': trend_data,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Trend analysis for {token_address}: "
                       f"score={result['trend_score']:.1f}, "
                       f"direction={result['trend_direction']}, "
                       f"consensus={result['timeframe_consensus']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in trend analysis for {token_address}: {e}")
            return self._default_trend_analysis()
    
    async def _fetch_ohlcv_data(self, token_address: str, timeframe: str) -> Optional[List[Dict]]:
        """Fetch OHLCV data from Birdeye API"""
        
        # Map timeframes to Birdeye API format
        timeframe_map = {
            '1h': '1H',
            '4h': '4H', 
            '1d': '1D'
        }
        
        endpoint = f"{self.base_url}/defi/history_price"
        params = {
            'address': token_address,
            'address_type': 'token',
            'type': timeframe_map.get(timeframe, '1H'),
            'time_from': int((datetime.now() - timedelta(days=7)).timestamp()),
            'time_to': int(datetime.now().timestamp())
        }
        
        headers = {'X-API-KEY': self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {}).get('items', [])
                    else:
                        logger.error(f"Birdeye API error {response.status} for {token_address}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            return None
    
    async def _analyze_timeframe_trend(self, ohlcv_data: List[Dict], timeframe: str) -> Dict:
        """Analyze trend for a specific timeframe"""
        
        if not ohlcv_data or len(ohlcv_data) < 20:
            return self._default_timeframe_analysis()
        
        try:
            # Extract price data
            closes = [float(item['c']) for item in ohlcv_data]
            highs = [float(item['h']) for item in ohlcv_data]
            lows = [float(item['l']) for item in ohlcv_data]
            volumes = [float(item['v']) for item in ohlcv_data]
            
            # Calculate EMAs
            ema_20 = self._calculate_ema(closes, 20)
            ema_50 = self._calculate_ema(closes, 50)
            
            current_price = closes[-1]
            
            # Analyze trend components
            price_above_ema20 = current_price > ema_20[-1] if ema_20 else False
            price_above_ema50 = current_price > ema_50[-1] if ema_50 else False
            ema_alignment = ema_20[-1] > ema_50[-1] if (ema_20 and ema_50) else False
            
            # Check for higher highs and higher lows
            higher_structure = self._check_higher_highs_lows(highs, lows)
            
            # Calculate momentum
            momentum = self._calculate_momentum(closes)
            
            # Volume confirmation
            volume_trend = self._analyze_volume_trend(volumes)
            
            # Overall timeframe score
            timeframe_score = self._calculate_timeframe_score(
                price_above_ema20, price_above_ema50, ema_alignment,
                higher_structure, momentum, volume_trend
            )
            
            return {
                'timeframe': timeframe,
                'score': timeframe_score,
                'price_above_ema20': price_above_ema20,
                'price_above_ema50': price_above_ema50,
                'ema_alignment': ema_alignment,
                'higher_structure': higher_structure,
                'momentum': momentum,
                'volume_trend': volume_trend,
                'current_price': current_price,
                'ema_20': ema_20[-1] if ema_20 else None,
                'ema_50': ema_50[-1] if ema_50 else None
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {timeframe} trend: {e}")
            return self._default_timeframe_analysis()
    
    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema = [sum(prices[:period]) / period]  # Start with SMA
        
        for price in prices[period:]:
            ema.append((price * multiplier) + (ema[-1] * (1 - multiplier)))
        
        return ema
    
    def _check_higher_highs_lows(self, highs: List[float], lows: List[float]) -> bool:
        """Check for higher highs and higher lows pattern"""
        if len(highs) < 10 or len(lows) < 10:
            return False
        
        # Look at recent 10 periods vs previous 10 periods
        recent_high = max(highs[-10:])
        previous_high = max(highs[-20:-10]) if len(highs) >= 20 else max(highs[:-10])
        
        recent_low = min(lows[-10:])
        previous_low = min(lows[-20:-10]) if len(lows) >= 20 else min(lows[:-10])
        
        return recent_high > previous_high and recent_low > previous_low
    
    def _calculate_momentum(self, closes: List[float]) -> float:
        """Calculate price momentum"""
        if len(closes) < 10:
            return 0
        
        recent_avg = sum(closes[-5:]) / 5
        previous_avg = sum(closes[-15:-10]) / 5 if len(closes) >= 15 else sum(closes[-10:-5]) / 5
        
        momentum = ((recent_avg - previous_avg) / previous_avg) * 100
        return max(min(momentum, 100), -100)  # Cap between -100 and 100
    
    def _analyze_volume_trend(self, volumes: List[float]) -> str:
        """Analyze volume trend"""
        if len(volumes) < 10:
            return 'insufficient_data'
        
        recent_vol = sum(volumes[-5:]) / 5
        previous_vol = sum(volumes[-15:-10]) / 5 if len(volumes) >= 15 else sum(volumes[-10:-5]) / 5
        
        if recent_vol > previous_vol * 1.2:
            return 'increasing'
        elif recent_vol < previous_vol * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_timeframe_score(self, price_above_ema20: bool, price_above_ema50: bool, 
                                 ema_alignment: bool, higher_structure: bool, 
                                 momentum: float, volume_trend: str) -> float:
        """Calculate overall score for this timeframe"""
        
        score = 0
        
        # EMA position (30 points max)
        if price_above_ema20 and price_above_ema50:
            score += 30
        elif price_above_ema20:
            score += 20
        elif price_above_ema50:
            score += 10
        
        # EMA alignment (20 points)
        if ema_alignment:
            score += 20
        
        # Higher structure (25 points)
        if higher_structure:
            score += 25
        
        # Momentum (15 points)
        momentum_score = max(0, momentum) / 100 * 15
        score += momentum_score
        
        # Volume trend (10 points)
        if volume_trend == 'increasing':
            score += 10
        elif volume_trend == 'stable':
            score += 5
        
        return min(score, 100)  # Cap at 100
    
    def require_uptrend_confirmation(self, trend_analysis: Dict) -> bool:
        """Check if token meets mandatory uptrend requirements"""
        
        return (
            trend_analysis.get('trend_score', 0) >= self.min_trend_score and
            trend_analysis.get('ema_alignment', False) and
            trend_analysis.get('higher_structure', False) and
            trend_analysis.get('timeframe_consensus', 0) >= self.min_timeframe_consensus
        )
    
    def _calculate_trend_score(self, trend_data: Dict) -> float:
        """Calculate overall trend score across all timeframes"""
        
        scores = [data.get('score', 0) for data in trend_data.values()]
        if not scores:
            return 0
        
        # Weighted average (1d = 50%, 4h = 30%, 1h = 20%)
        weights = {'1d': 0.5, '4h': 0.3, '1h': 0.2}
        weighted_score = 0
        
        for timeframe, data in trend_data.items():
            weight = weights.get(timeframe, 0)
            weighted_score += data.get('score', 0) * weight
        
        return weighted_score
    
    def _determine_trend_direction(self, trend_data: Dict) -> str:
        """Determine overall trend direction"""
        
        uptrend_count = 0
        downtrend_count = 0
        
        for data in trend_data.values():
            score = data.get('score', 0)
            if score >= 60:
                uptrend_count += 1
            elif score <= 40:
                downtrend_count += 1
        
        if uptrend_count >= 2:
            return 'UPTREND'
        elif downtrend_count >= 2:
            return 'DOWNTREND'
        else:
            return 'SIDEWAYS'
    
    def _check_ema_alignment(self, trend_data: Dict) -> bool:
        """Check if EMAs are aligned across timeframes"""
        
        aligned_count = 0
        total_count = 0
        
        for data in trend_data.values():
            if data.get('price_above_ema20') is not None:
                total_count += 1
                if (data.get('price_above_ema20', False) and 
                    data.get('price_above_ema50', False)):
                    aligned_count += 1
        
        return (aligned_count / total_count) >= 0.67 if total_count > 0 else False
    
    def _check_higher_structure(self, trend_data: Dict) -> bool:
        """Check for higher highs/lows across timeframes"""
        
        structure_count = sum(1 for data in trend_data.values() 
                            if data.get('higher_structure', False))
        
        return structure_count >= 2  # At least 2 timeframes show higher structure
    
    def _calculate_consensus(self, trend_data: Dict) -> float:
        """Calculate consensus across timeframes"""
        
        uptrend_timeframes = sum(1 for data in trend_data.values() 
                               if data.get('score', 0) >= 60)
        
        total_timeframes = len(trend_data)
        
        return uptrend_timeframes / total_timeframes if total_timeframes > 0 else 0
    
    def _default_timeframe_analysis(self) -> Dict:
        """Return default analysis when data is insufficient"""
        return {
            'score': 0,
            'price_above_ema20': False,
            'price_above_ema50': False,
            'ema_alignment': False,
            'higher_structure': False,
            'momentum': 0,
            'volume_trend': 'insufficient_data',
            'error': True
        }
    
    def _default_trend_analysis(self) -> Dict:
        """Return default trend analysis when errors occur"""
        return {
            'trend_score': 0,
            'trend_direction': 'UNKNOWN',
            'ema_alignment': False,
            'higher_structure': False,
            'timeframe_consensus': 0,
            'error': True
        }
```

### Step 2: Integrate Trend Analysis into Discovery Pipeline
**File:** `services/early_token_detection.py`

**ADD IMPORT at top:**
```python
from services.trend_confirmation_analyzer import TrendConfirmationAnalyzer
```

**ADD to `__init__` method:**
```python
def __init__(self):
    # ... existing initialization ...
    
    # Initialize trend analyzer
    birdeye_api_key = os.getenv('BIRDEYE_API_KEY')
    if not birdeye_api_key:
        raise ValueError("BIRDEYE_API_KEY environment variable required")
    
    self.trend_analyzer = TrendConfirmationAnalyzer(birdeye_api_key)
    logger.info("Initialized TrendConfirmationAnalyzer")
```

**ADD new method for trend filtering:**
```python
async def apply_trend_confirmation_filter(self, tokens: List[Dict]) -> List[Dict]:
    """Apply trend confirmation filter to tokens"""
    
    logger.info(f"Applying trend confirmation to {len(tokens)} tokens")
    
    trend_confirmed_tokens = []
    
    for token in tokens:
        try:
            # Analyze trend structure
            trend_analysis = await self.trend_analyzer.analyze_trend_structure(
                token['address']
            )
            
            # Add trend data to token
            token['trend_analysis'] = trend_analysis
            token['trend_score'] = trend_analysis.get('trend_score', 0)
            
            # Check if token passes trend confirmation
            if self.trend_analyzer.require_uptrend_confirmation(trend_analysis):
                trend_confirmed_tokens.append(token)
                logger.debug(f"✅ {token.get('symbol', 'UNKNOWN')} passed trend confirmation: "
                           f"score={trend_analysis.get('trend_score', 0):.1f}")
            else:
                logger.debug(f"❌ {token.get('symbol', 'UNKNOWN')} failed trend confirmation: "
                           f"score={trend_analysis.get('trend_score', 0):.1f}, "
                           f"direction={trend_analysis.get('trend_direction', 'UNKNOWN')}")
                
        except Exception as e:
            logger.error(f"Error in trend confirmation for {token.get('symbol', 'UNKNOWN')}: {e}")
            # Token fails trend confirmation if analysis fails
            continue
    
    logger.info(f"Trend confirmation passed: {len(trend_confirmed_tokens)}/{len(tokens)} tokens")
    
    return trend_confirmed_tokens
```

**UPDATE discovery pipeline in `discover_tokens` method:**
```python
async def discover_tokens(self) -> List[Dict]:
    """Main token discovery pipeline with trend confirmation"""
    
    logger.info("🔍 Starting token discovery with trend confirmation")
    
    # Step 1: Initial discovery (existing code)
    initial_tokens = await self._fetch_initial_candidates()
    logger.info(f"Initial candidates: {len(initial_tokens)}")
    
    # Step 2: Quick scoring filter (existing code)
    quick_filtered = await self._apply_quick_scoring(initial_tokens)
    logger.info(f"After quick scoring: {len(quick_filtered)}")
    
    # Step 3: NEW - Trend confirmation filter
    trend_confirmed = await self.apply_trend_confirmation_filter(quick_filtered)
    logger.info(f"After trend confirmation: {len(trend_confirmed)}")
    
    # Step 4: Continue with existing pipeline...
    medium_scored = await self._apply_medium_scoring(trend_confirmed)
    logger.info(f"After medium scoring: {len(medium_scored)}")
    
    # Step 5: Final analysis (existing code)
    final_tokens = await self._apply_full_analysis(medium_scored)
    logger.info(f"Final promising tokens: {len(final_tokens)}")
    
    return final_tokens
```

### ✅ Checkpoint 2.1: Test Trend Confirmation
**Create Test File:** `tests/test_trend_confirmation.py`

```python
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.trend_confirmation_analyzer import TrendConfirmationAnalyzer

async def test_trend_confirmation():
    """Test trend confirmation system"""
    
    # Mock Birdeye API key for testing
    analyzer = TrendConfirmationAnalyzer("test_api_key")
    
    # Test EMA calculation
    test_prices = [100, 102, 104, 103, 105, 107, 106, 108, 110, 109]
    ema = analyzer._calculate_ema(test_prices, 5)
    assert len(ema) > 0, "EMA calculation failed"
    print("✅ EMA calculation working")
    
    # Test higher highs/lows detection
    highs = [100, 102, 105, 103, 108, 110, 107, 112, 115, 113]
    lows = [95, 97, 100, 98, 103, 105, 102, 107, 110, 108]
    higher_structure = analyzer._check_higher_highs_lows(highs, lows)
    print(f"✅ Higher structure detection: {higher_structure}")
    
    # Test momentum calculation
    closes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
    momentum = analyzer._calculate_momentum(closes)
    assert momentum > 0, "Momentum should be positive for uptrending prices"
    print(f"✅ Momentum calculation: {momentum:.2f}")
    
    # Test timeframe score calculation
    score = analyzer._calculate_timeframe_score(
        price_above_ema20=True,
        price_above_ema50=True,
        ema_alignment=True,
        higher_structure=True,
        momentum=5.0,
        volume_trend='increasing'
    )
    assert score > 80, f"Strong trend should score >80, got {score}"
    print(f"✅ Timeframe scoring: {score}")
    
    print("🎉 All trend confirmation tests passed!")

if __name__ == "__main__":
    asyncio.run(test_trend_confirmation())
```

**Run Test:**
```bash
python tests/test_trend_confirmation.py
```

---

## 🔧 Task 2.2: Implement Relative Strength Analysis

### Step 1: Create Relative Strength Analyzer
**Create File:** `services/relative_strength_analyzer.py`

```python
import logging
import statistics
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RelativeStrengthAnalyzer:
    """Compare token performance against universe benchmarks"""
    
    def __init__(self):
        self.min_universe_size = 50  # Minimum tokens needed for reliable comparison
        self.rs_percentile_threshold = 60  # Must be in top 40%
        self.outperformance_timeframes = ['1h', '4h', '24h']
        
    async def calculate_relative_performance(self, token_data: Dict, universe_data: List[Dict]) -> Dict:
        """Calculate comprehensive relative strength metrics"""
        
        token_symbol = token_data.get('symbol', 'UNKNOWN')
        logger.debug(f"Calculating relative performance for {token_symbol}")
        
        try:
            if len(universe_data) < self.min_universe_size:
                logger.warning(f"Universe too small: {len(universe_data)} < {self.min_universe_size}")
                return self._default_rs_analysis()
            
            # Extract token returns
            token_returns = self._extract_token_returns(token_data)
            
            # Calculate universe benchmarks
            universe_returns = self._calculate_universe_returns(universe_data)
            
            # Calculate relative strength metrics
            rs_metrics = {
                'rs_score': self._calculate_rs_score(token_returns, universe_returns),
                'percentile_rank': self._calculate_percentile_rank(token_returns, universe_returns),
                'outperformance_1h': token_returns.get('1h', 0) - universe_returns['median_1h'],
                'outperformance_4h': token_returns.get('4h', 0) - universe_returns['median_4h'],
                'outperformance_24h': token_returns.get('24h', 0) - universe_returns['median_24h'],
                'consistency_score': self._calculate_consistency_score(token_returns, universe_returns),
                'market_leadership': self._is_market_leader(token_returns, universe_returns),
                'relative_volume': self._calculate_relative_volume(token_data, universe_data),
                'universe_size': len(universe_data),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            logger.debug(f"RS metrics for {token_symbol}: "
                        f"score={rs_metrics['rs_score']:.1f}, "
                        f"percentile={rs_metrics['percentile_rank']:.1f}, "
                        f"outperf_1h={rs_metrics['outperformance_1h']:.2f}%")
            
            return rs_metrics
            
        except Exception as e:
            logger.error(f"Error calculating relative performance for {token_symbol}: {e}")
            return self._default_rs_analysis()
    
    def _extract_token_returns(self, token_data: Dict) -> Dict:
        """Extract returns data from token"""
        
        return {
            '1h': float(token_data.get('price_change_1h', 0)),
            '4h': float(token_data.get('price_change_4h', 0)),
            '24h': float(token_data.get('price_change_24h', 0)),
            'volume_24h': float(token_data.get('volume_24h', 0))
        }
    
    def _calculate_universe_returns(self, universe_data: List[Dict]) -> Dict:
        """Calculate universe benchmark statistics"""
        
        returns_1h = []
        returns_4h = []
        returns_24h = []
        volumes_24h = []
        
        for token in universe_data:
            try:
                returns_1h.append(float(token.get('price_change_1h', 0)))
                returns_4h.append(float(token.get('price_change_4h', 0)))
                returns_24h.append(float(token.get('price_change_24h', 0)))
                volumes_24h.append(float(token.get('volume_24h', 0)))
            except (ValueError, TypeError):
                continue
        
        # Calculate statistics
        universe_stats = {
            'median_1h': statistics.median(returns_1h) if returns_1h else 0,
            'mean_1h': statistics.mean(returns_1h) if returns_1h else 0,
            'median_4h': statistics.median(returns_4h) if returns_4h else 0,
            'mean_4h': statistics.mean(returns_4h) if returns_4h else 0,
            'median_24h': statistics.median(returns_24h) if returns_24h else 0,
            'mean_24h': statistics.mean(returns_24h) if returns_24h else 0,
            'median_volume': statistics.median(volumes_24h) if volumes_24h else 0,
            'returns_1h': returns_1h,
            'returns_4h': returns_4h,
            'returns_24h': returns_24h,
            'volumes_24h': volumes_24h
        }
        
        return universe_stats
    
    def _calculate_rs_score(self, token_returns: Dict, universe_returns: Dict) -> float:
        """Calculate relative strength score (0-100)"""
        
        # Weight different timeframes
        weights = {'1h': 0.2, '4h': 0.3, '24h': 0.5}
        
        total_score = 0
        
        for timeframe, weight in weights.items():
            token_return = token_returns.get(timeframe, 0)
            universe_median = universe_returns.get(f'median_{timeframe}', 0)
            
            # Calculate relative performance
            if universe_median != 0:
                relative_perf = (token_return - universe_median) / abs(universe_median)
            else:
                relative_perf = token_return / 100  # Normalize if universe median is 0
            
            # Convert to 0-100 scale (capped)
            timeframe_score = max(0, min(100, 50 + (relative_perf * 50)))
            total_score += timeframe_score * weight
        
        return total_score
    
    def _calculate_percentile_rank(self, token_returns: Dict, universe_returns: Dict) -> float:
        """Calculate percentile rank within universe"""
        
        timeframe_percentiles = []
        
        for timeframe in ['1h', '4h', '24h']:
            token_return = token_returns.get(timeframe, 0)
            universe_returns_list = universe_returns.get(f'returns_{timeframe}', [])
            
            if universe_returns_list:
                # Count how many tokens this token outperformed
                outperformed = sum(1 for r in universe_returns_list if token_return > r)
                percentile = (outperformed / len(universe_returns_list)) * 100
                timeframe_percentiles.append(percentile)
        
        # Return average percentile across timeframes
        return statistics.mean(timeframe_percentiles) if timeframe_percentiles else 0
    
    def _calculate_consistency_score(self, token_returns: Dict, universe_returns: Dict) -> float:
        """Calculate consistency of outperformance"""
        
        outperformance_count = 0
        total_timeframes = 0
        
        for timeframe in ['1h', '4h', '24h']:
            token_return = token_returns.get(timeframe, 0)
            universe_median = universe_returns.get(f'median_{timeframe}', 0)
            
            total_timeframes += 1
            if token_return > universe_median:
                outperformance_count += 1
        
        return (outperformance_count / total_timeframes) * 100 if total_timeframes > 0 else 0
    
    def _is_market_leader(self, token_returns: Dict, universe_returns: Dict) -> bool:
        """Determine if token is a market leader (top 20%)"""
        
        percentile_rank = self._calculate_percentile_rank(token_returns, universe_returns)
        return percentile_rank >= 80  # Top 20%
    
    def _calculate_relative_volume(self, token_data: Dict, universe_data: List[Dict]) -> float:
        """Calculate volume relative to universe"""
        
        token_volume = float(token_data.get('volume_24h', 0))
        universe_volumes = [float(t.get('volume_24h', 0)) for t in universe_data]
        
        if not universe_volumes:
            return 0
        
        median_volume = statistics.median(universe_volumes)
        
        if median_volume > 0:
            return (token_volume / median_volume) * 100
        else:
            return 0
    
    def filter_by_relative_strength(self, tokens: List[Dict]) -> List[Dict]:
        """Filter tokens based on relative strength requirements"""
        
        logger.info(f"Applying relative strength filter to {len(tokens)} tokens")
        
        if len(tokens) < self.min_universe_size:
            logger.warning(f"Token universe too small for reliable RS analysis: {len(tokens)}")
            return tokens  # Return all tokens if universe is too small
        
        rs_filtered_tokens = []
        
        for i, token in enumerate(tokens):
            try:
                # Use all other tokens as universe for comparison
                universe_data = tokens[:i] + tokens[i+1:]
                
                # Calculate relative performance
                rs_analysis = await self.calculate_relative_performance(token, universe_data)
                
                # Add RS data to token
                token['relative_strength'] = rs_analysis
                token['rs_score'] = rs_analysis.get('rs_score', 0)
                
                # Check if token passes RS requirements
                if self._passes_rs_requirements(rs_analysis):
                    rs_filtered_tokens.append(token)
                    logger.debug(f"✅ {token.get('symbol', 'UNKNOWN')} passed RS filter: "
                               f"percentile={rs_analysis.get('percentile_rank', 0):.1f}")
                else:
                    logger.debug(f"❌ {token.get('symbol', 'UNKNOWN')} failed RS filter: "
                               f"percentile={rs_analysis.get('percentile_rank', 0):.1f}")
                    
            except Exception as e:
                logger.error(f"Error in RS analysis for {token.get('symbol', 'UNKNOWN')}: {e}")
                continue
        
        logger.info(f"Relative strength filter passed: {len(rs_filtered_tokens)}/{len(tokens)} tokens")
        
        return rs_filtered_tokens
    
    def _passes_rs_requirements(self, rs_analysis: Dict) -> bool:
        """Check if token meets relative strength requirements"""
        
        return (
            rs_analysis.get('percentile_rank', 0) >= self.rs_percentile_threshold and
            rs_analysis.get('outperformance_1h', -100) > 0 and
            rs_analysis.get('outperformance_4h', -100) > 0 and
            rs_analysis.get('consistency_score', 0) >= 67  # Must outperform in 2/3 timeframes
        )
    
    def _default_rs_analysis(self) -> Dict:
        """Return default RS analysis when calculation fails"""
        
        return {
            'rs_score': 0,
            'percentile_rank': 0,
            'outperformance_1h': 0,
            'outperformance_4h': 0,
            'outperformance_24h': 0,
            'consistency_score': 0,
            'market_leadership': False,
            'relative_volume': 0,
            'error': True
        }
```

### Step 2: Integrate RS Analysis into Discovery Pipeline
**File:** `services/early_token_detection.py`

**ADD IMPORT:**
```python
from services.relative_strength_analyzer import RelativeStrengthAnalyzer
```

**ADD to `__init__`:**
```python
# Initialize relative strength analyzer
self.rs_analyzer = RelativeStrengthAnalyzer()
logger.info("Initialized RelativeStrengthAnalyzer")
```

**UPDATE discovery pipeline in `discover_tokens` method:**
```python
# Step 4: NEW - Relative strength filter (after trend confirmation)
rs_filtered = await self.rs_analyzer.filter_by_relative_strength(trend_confirmed)
logger.info(f"After relative strength filter: {len(rs_filtered)}")

# Step 5: Continue with existing pipeline...
medium_scored = await self._apply_medium_scoring(rs_filtered)
```

### ✅ Checkpoint 2.2: Test Relative Strength Analysis
**Create Test File:** `tests/test_relative_strength.py`

```python
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.relative_strength_analyzer import RelativeStrengthAnalyzer

async def test_relative_strength():
    """Test relative strength analysis"""
    
    analyzer = RelativeStrengthAnalyzer()
    
    # Create test universe
    universe_data = [
        {'symbol': 'TOKEN1', 'price_change_1h': 1.0, 'price_change_4h': 2.0, 'price_change_24h': 5.0, 'volume_24h': 100000},
        {'symbol': 'TOKEN2', 'price_change_1h': -1.0, 'price_change_4h': 0.5, 'price_change_24h': 2.0, 'volume_24h': 50000},
        {'symbol': 'TOKEN3', 'price_change_1h': 3.0, 'price_change_4h': 5.0, 'price_change_24h': 10.0, 'volume_24h': 200000},
        {'symbol': 'TOKEN4', 'price_change_1h': 0.0, 'price_change_4h': 1.0, 'price_change_24h': 3.0, 'volume_24h': 75000},
        {'symbol': 'TOKEN5', 'price_change_1h': -2.0, 'price_change_4h': -1.0, 'price_change_24h': 0.0, 'volume_24h': 25000}
    ]
    
    # Test token (strong performer)
    test_token = {
        'symbol': 'STRONG', 
        'price_change_1h': 4.0, 
        'price_change_4h': 6.0, 
        'price_change_24h': 12.0, 
        'volume_24h': 300000
    }
    
    # Calculate relative performance
    rs_analysis = await analyzer.calculate_relative_performance(test_token, universe_data)
    
    assert rs_analysis['rs_score'] > 70, f"Strong token should have high RS score, got {rs_analysis['rs_score']}"
    assert rs_analysis['percentile_rank'] > 80, f"Strong token should have high percentile rank, got {rs_analysis['percentile_rank']}"
    assert rs_analysis['market_leadership'] == True, "Strong token should be market leader"
    
    print(f"✅ RS Score: {rs_analysis['rs_score']:.1f}")
    print(f"✅ Percentile Rank: {rs_analysis['percentile_rank']:.1f}")
    print(f"✅ Market Leadership: {rs_analysis['market_leadership']}")
    
    # Test filtering
    all_tokens = universe_data + [test_token]
    filtered_tokens = await analyzer.filter_by_relative_strength(all_tokens)
    
    # Strong token should pass, weak ones should be filtered out
    assert len(filtered_tokens) <= len(all_tokens), "Filtering should reduce token count"
    strong_token_passed = any(t['symbol'] == 'STRONG' for t in filtered_tokens)
    assert strong_token_passed, "Strong token should pass RS filter"
    
    print(f"✅ Filtering: {len(filtered_tokens)}/{len(all_tokens)} tokens passed")
    print("🎉 All relative strength tests passed!")

if __name__ == "__main__":
    asyncio.run(test_relative_strength())
```

---

## Phase 2 Integration Test

**Create Integration Test:** `tests/test_phase2_integration.py`

```python
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.trend_confirmation_analyzer import TrendConfirmationAnalyzer
from services.relative_strength_analyzer import RelativeStrengthAnalyzer

async def test_phase2_integration():
    """Test Phase 2 components working together"""
    
    print("🧪 Testing Phase 2 Integration...")
    
    # Test 1: Trend Confirmation
    trend_analyzer = TrendConfirmationAnalyzer("test_key")
    
    # Test trend components
    test_prices = [100, 102, 104, 106, 108, 110]
    ema = trend_analyzer._calculate_ema(test_prices, 3)
    assert len(ema) > 0, "EMA calculation failed"
    print("✅ Trend confirmation system initialized")
    
    # Test 2: Relative Strength
    rs_analyzer = RelativeStrengthAnalyzer()
    
    universe = [
        {'price_change_1h': 1, 'price_change_4h': 2, 'price_change_24h': 5, 'volume_24h': 100000},
        {'price_change_1h': -1, 'price_change_4h': 0, 'price_change_24h': 1, 'volume_24h': 50000}
    ]
    
    universe_stats = rs_analyzer._calculate_universe_returns(universe)
    assert 'median_1h' in universe_stats, "Universe calculation failed"
    print("✅ Relative strength system initialized")
    
    # Test 3: Integration compatibility
    # Both systems should work with the same token data format
    test_token = {
        'symbol': 'TEST',
        'address': 'test_address',
        'price_change_1h': 5.0,
        'price_change_4h': 8.0,
        'price_change_24h': 15.0,
        'volume_24h': 200000
    }
    
    # RS analysis should work
    rs_result = await rs_analyzer.calculate_relative_performance(test_token, universe)
    assert 'rs_score' in rs_result, "RS analysis failed"
    print("✅ Token data format compatible between systems")
    
    print("🎉 Phase 2 Integration Test PASSED!")
    print("📋 Ready for Phase 3 implementation")

if __name__ == "__main__":
    asyncio.run(test_phase2_integration())
```

**Run Integration Test:**
```bash
python tests/test_phase2_integration.py
```

---

## Phase 2 Success Criteria Checklist

**Before proceeding to Phase 3, verify:**

- [ ] Trend confirmation system analyzes multiple timeframes
- [ ] >60% of discovered tokens pass trend confirmation  
- [ ] Relative strength analysis compares against universe
- [ ] Only tokens in top 40% (60th percentile) advance
- [ ] Average trend scores improve from 0/5 to 2-3/5
- [ ] Discovery pipeline integrates both systems without errors
- [ ] All Phase 2 tests pass

**If any criteria fail, debug and fix before Phase 3!** 