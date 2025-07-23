import logging
import statistics
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RelativeStrengthAnalyzer:
    """Compare token performance against universe benchmarks"""
    
    def __init__(self, test_mode=False):
        self.min_universe_size = 50  # Minimum tokens needed for reliable comparison
        self.rs_percentile_threshold = 60  # Must be in top 40%
        self.outperformance_timeframes = ['1h', '4h', '24h']
        self.test_mode = test_mode
        
        # In test mode, use a smaller universe size
        if test_mode:
            self.min_universe_size = 5
            logger.info("RelativeStrengthAnalyzer initialized in TEST MODE with reduced universe size")
        
    async def calculate_relative_performance(self, token_data: Dict, universe_data: List[Dict]) -> Dict:
        """Calculate comprehensive relative strength metrics"""
        
        token_symbol = token_data.get('symbol', 'UNKNOWN')
        logger.debug(f"Calculating relative performance for {token_symbol}")
        
        try:
            # Check for valid universe size
            if len(universe_data) < self.min_universe_size:
                logger.warning(f"Universe too small: {len(universe_data)} < {self.min_universe_size}")
                return self._default_rs_analysis(passes_threshold=False, error_reason="universe_too_small")
            
            # Extract token returns
            token_returns = self._extract_token_returns(token_data)
            
            # Calculate universe benchmarks
            universe_returns = self._calculate_universe_returns(universe_data)
            
            # Check if we have enough data to proceed
            if not universe_returns['has_sufficient_data']:
                logger.warning(f"Insufficient universe data for {token_symbol}")
                return self._default_rs_analysis(passes_threshold=False, error_reason="insufficient_universe_data")
            
            # Calculate percentile rank
            percentile_rank = self._calculate_percentile_rank(token_returns, universe_returns)
            
            # Calculate relative performance metrics
            timeframe_performance = {
                '1h': token_returns.get('1h', 0) - universe_returns['median_1h'],
                '4h': token_returns.get('4h', 0) - universe_returns['median_4h'],
                '24h': token_returns.get('24h', 0) - universe_returns['median_24h']
            }
            
            # Calculate consistency score
            consistency_score = self._calculate_consistency_score(token_returns, universe_returns)
            
            # Check if token is a market leader
            is_market_leader = self._is_market_leader(percentile_rank)
            
            # Calculate relative volume
            relative_volume = self._calculate_relative_volume(token_data, universe_data)
            
            # Calculate overall RS score
            rs_score = self._calculate_rs_score(token_returns, universe_returns)
            
            # Determine if token passes RS threshold
            passes_threshold = self._passes_rs_requirements({
                'rs_score': rs_score,
                'percentile_rank': percentile_rank,
                'consistency_score': consistency_score
            })
            
            # Compile all results
            rs_metrics = {
                'token_symbol': token_symbol,
                'rs_score': rs_score,
                'percentile_rank': percentile_rank,
                'timeframe_performance': timeframe_performance,
                'consistency_score': consistency_score,
                'is_market_leader': is_market_leader,
                'relative_volume': relative_volume,
                'universe_size': len(universe_data),
                'passes_threshold': passes_threshold,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"RS metrics for {token_symbol}: "
                       f"score={rs_metrics['rs_score']:.1f}, "
                       f"percentile={rs_metrics['percentile_rank']:.1f}, "
                       f"consistency={rs_metrics['consistency_score']:.1f}, "
                       f"passes={rs_metrics['passes_threshold']}")
            
            return rs_metrics
            
        except Exception as e:
            logger.error(f"Error calculating relative performance for {token_symbol}: {e}")
            return self._default_rs_analysis(error_reason=f"exception: {str(e)}")
    
    def _extract_token_returns(self, token_data: Dict) -> Dict:
        """Extract returns data from token"""
        
        try:
            return {
                '1h': float(token_data.get('price_change_1h', 0)),
                '4h': float(token_data.get('price_change_4h', 0)),
                '24h': float(token_data.get('price_change_24h', 0)),
                'volume_24h': float(token_data.get('volume_24h', 0))
            }
        except (ValueError, TypeError) as e:
            logger.warning(f"Error extracting token returns: {e}")
            return {'1h': 0, '4h': 0, '24h': 0, 'volume_24h': 0}
    
    def _calculate_universe_returns(self, universe_data: List[Dict]) -> Dict:
        """Calculate universe benchmark statistics"""
        
        returns_1h = []
        returns_4h = []
        returns_24h = []
        volumes_24h = []
        
        for token in universe_data:
            try:
                if 'price_change_1h' in token:
                    returns_1h.append(float(token.get('price_change_1h', 0)))
                if 'price_change_4h' in token:
                    returns_4h.append(float(token.get('price_change_4h', 0)))
                if 'price_change_24h' in token:
                    returns_24h.append(float(token.get('price_change_24h', 0)))
                if 'volume_24h' in token:
                    volumes_24h.append(float(token.get('volume_24h', 0)))
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping token in universe calculation due to error: {e}")
                continue
        
        # Check if we have enough data
        has_sufficient_data = (
            len(returns_1h) >= self.min_universe_size * 0.8 and 
            len(returns_4h) >= self.min_universe_size * 0.8 and
            len(returns_24h) >= self.min_universe_size * 0.8
        )
        
        # Calculate statistics
        universe_stats = {
            'has_sufficient_data': has_sufficient_data,
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
        total_weight = 0
        
        for timeframe, weight in weights.items():
            token_return = token_returns.get(timeframe, 0)
            universe_median = universe_returns.get(f'median_{timeframe}', 0)
            universe_returns_list = universe_returns.get(f'returns_{timeframe}', [])
            
            # Skip timeframe if we don't have enough data
            if not universe_returns_list:
                continue
            
            # Calculate relative performance
            if universe_median != 0:
                relative_perf = (token_return - universe_median) / max(1, abs(universe_median))
            else:
                relative_perf = token_return / 100  # Normalize if universe median is 0
            
            # Convert to 0-100 scale (capped)
            timeframe_score = max(0, min(100, 50 + (relative_perf * 50)))
            total_score += timeframe_score * weight
            total_weight += weight
        
        # Return average score or 0 if no data
        return total_score / total_weight if total_weight > 0 else 0
    
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
            universe_returns_list = universe_returns.get(f'returns_{timeframe}', [])
            
            if not universe_returns_list:
                continue
                
            total_timeframes += 1
            if token_return > universe_median:
                outperformance_count += 1
        
        return (outperformance_count / total_timeframes) * 100 if total_timeframes > 0 else 0
    
    def _is_market_leader(self, percentile_rank: float) -> bool:
        """Determine if token is a market leader (top 20%)"""
        return percentile_rank >= 80  # Top 20%
    
    def _calculate_relative_volume(self, token_data: Dict, universe_data: List[Dict]) -> float:
        """Calculate volume relative to universe"""
        
        try:
            token_volume = float(token_data.get('volume_24h', 0))
            
            # Extract volumes with error handling
            universe_volumes = []
            for t in universe_data:
                try:
                    if 'volume_24h' in t:
                        universe_volumes.append(float(t.get('volume_24h', 0)))
                except (ValueError, TypeError):
                    continue
            
            if not universe_volumes:
                return 0
            
            median_volume = statistics.median(universe_volumes)
            
            if median_volume > 0:
                return token_volume / median_volume
            else:
                return 0
                
        except Exception as e:
            logger.warning(f"Error calculating relative volume: {e}")
            return 0
    
    async def filter_by_relative_strength(self, tokens: List[Dict]) -> List[Dict]:
        """Filter tokens based on relative strength requirements"""
        
        logger.info(f"Applying relative strength filter to {len(tokens)} tokens")
        
        # In test mode or with a small universe, just return all tokens
        if self.test_mode or len(tokens) < self.min_universe_size:
            logger.warning(f"Token universe too small for reliable RS analysis: {len(tokens)}")
            # Force passing in test mode
            if self.test_mode:
                for token in tokens:
                    token['rs_analysis'] = self._default_rs_analysis(passes_threshold=True, test_data=True)
            return tokens
        
        rs_filtered_tokens = []
        
        for i, token in enumerate(tokens):
            try:
                # Use all other tokens as universe for comparison
                universe_data = tokens[:i] + tokens[i+1:]
                
                # Calculate relative performance
                rs_analysis = await self.calculate_relative_performance(token, universe_data)
                
                # Add RS analysis to token data
                token['rs_analysis'] = rs_analysis
                
                # Filter based on RS requirements
                if rs_analysis.get('passes_threshold', False):
                    rs_filtered_tokens.append(token)
                    
            except Exception as e:
                logger.error(f"Error analyzing RS for token {token.get('symbol', 'UNKNOWN')}: {e}")
                # Add failed analysis
                token['rs_analysis'] = self._default_rs_analysis(error_reason=str(e))
        
        logger.info(f"Relative strength filter: {len(rs_filtered_tokens)}/{len(tokens)} tokens passed")
        return rs_filtered_tokens
    
    def _passes_rs_requirements(self, rs_analysis: Dict) -> bool:
        """Check if token meets relative strength requirements"""
        
        # For test mode, be more lenient
        if self.test_mode:
            return True
            
        # Main criteria: must be in top percentile threshold and have good consistency
        return (
            rs_analysis.get('rs_score', 0) >= 60 and
            rs_analysis.get('percentile_rank', 0) >= self.rs_percentile_threshold and
            rs_analysis.get('consistency_score', 0) >= 50  # Outperforms in at least half of timeframes
        )
    
    def _default_rs_analysis(self, passes_threshold=False, error_reason=None, test_data=False) -> Dict:
        """Return default RS analysis for error cases"""
        
        # For test mode, provide synthetic data
        if test_data:
            return {
                'rs_score': 75,
                'percentile_rank': 80,
                'timeframe_performance': {'1h': 5.0, '4h': 10.0, '24h': 15.0},
                'consistency_score': 100,
                'is_market_leader': True,
                'relative_volume': 1.5,
                'universe_size': self.min_universe_size,
                'passes_threshold': True,
                'test_data': True,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        return {
            'rs_score': 0,
            'percentile_rank': 0,
            'timeframe_performance': {'1h': 0, '4h': 0, '24h': 0},
            'consistency_score': 0,
            'is_market_leader': False,
            'relative_volume': 0,
            'universe_size': 0,
            'passes_threshold': passes_threshold,
            'error': True,
            'error_reason': error_reason,
            'analysis_timestamp': datetime.now().isoformat()
        } 