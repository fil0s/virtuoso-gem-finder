#!/usr/bin/env python3
"""
Enhanced Detection Strategies - Multi-timeframe hierarchy and early exit logic
Improves detection efficiency and reduces API costs
"""

import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TimeframeCategory(Enum):
    """Token age categories for timeframe selection"""
    ULTRA_NEW = "ultra_new"      # < 15 minutes
    VERY_NEW = "very_new"        # 15min - 1 hour  
    NEW = "new"                  # 1-6 hours
    RECENT = "recent"            # 6-24 hours
    ESTABLISHED = "established"  # 1-7 days
    MATURE = "mature"            # > 7 days

@dataclass
class TimeframeStrategy:
    """Strategy for timeframe selection based on token characteristics"""
    primary_timeframes: List[str]
    fallback_timeframes: List[str]
    max_attempts: int
    quality_threshold: int

class MultiTimeframeHierarchy:
    """
    Intelligent multi-timeframe data collection with hierarchical fallback.
    
    Features:
    - Age-based timeframe selection
    - Quality-based early termination
    - Fallback hierarchy for data availability
    - Cost optimization through smart timeframe selection
    """
    
    # Define all available timeframes in order from shortest to longest
    ALL_TIMEFRAMES = ['1s', '15s', '30s', '1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w']
    
    def __init__(self, api_client):
        """Initialize multi-timeframe hierarchy"""
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
        
        # Strategy mapping based on token age/characteristics
        self.strategies = {
            TimeframeCategory.ULTRA_NEW: TimeframeStrategy(
                primary_timeframes=['1s', '15s'],
                fallback_timeframes=['30s', '1m', '5m'],
                max_attempts=3,
                quality_threshold=20
            ),
            TimeframeCategory.VERY_NEW: TimeframeStrategy(
                primary_timeframes=['15s', '30s'],
                fallback_timeframes=['1m', '5m', '15m'],
                max_attempts=3,
                quality_threshold=25
            ),
            TimeframeCategory.NEW: TimeframeStrategy(
                primary_timeframes=['1m', '5m'],
                fallback_timeframes=['15m', '30m', '1h'],
                max_attempts=3,
                quality_threshold=30
            ),
            TimeframeCategory.RECENT: TimeframeStrategy(
                primary_timeframes=['5m', '15m'],
                fallback_timeframes=['30m', '1h', '2h'],
                max_attempts=2,
                quality_threshold=35
            ),
            TimeframeCategory.ESTABLISHED: TimeframeStrategy(
                primary_timeframes=['15m', '30m'],
                fallback_timeframes=['1h', '2h', '4h'],
                max_attempts=2,
                quality_threshold=40
            ),
            TimeframeCategory.MATURE: TimeframeStrategy(
                primary_timeframes=['1h', '2h'],
                fallback_timeframes=['4h', '6h', '12h'],
                max_attempts=2,
                quality_threshold=45
            )
        }
    
    def categorize_token_age(self, age_hours: float, trading_activity: Dict = None) -> TimeframeCategory:
        """Categorize token based on age and trading activity"""
        
        if age_hours < 0.25:  # < 15 minutes
            return TimeframeCategory.ULTRA_NEW
        elif age_hours < 1:  # 15 min - 1 hour
            return TimeframeCategory.VERY_NEW
        elif age_hours < 6:  # 1-6 hours
            return TimeframeCategory.NEW
        elif age_hours < 24:  # 6-24 hours
            return TimeframeCategory.RECENT
        elif age_hours < 168:  # 1-7 days
            return TimeframeCategory.ESTABLISHED
        else:  # > 7 days
            return TimeframeCategory.MATURE
    
    async def get_optimal_ohlcv_data(self, token_address: str, token_info: Dict = None) -> Dict[str, Any]:
        """
        Get optimal OHLCV data using hierarchical timeframe selection.
        
        Args:
            token_address: Token contract address
            token_info: Optional token metadata (age, trading activity, etc.)
        
        Returns:
            Dict with OHLCV data, selected timeframe, and quality metrics
        """
        # Determine token category
        age_hours = token_info.get('age_hours', 999) if token_info else 999
        category = self.categorize_token_age(age_hours, token_info)
        strategy = self.strategies[category]
        
        self.logger.debug(f"🎯 Token {token_address}: age={age_hours:.1f}h, category={category.value}")
        
        # Try primary timeframes first
        result = await self._try_timeframes(
            token_address, 
            strategy.primary_timeframes, 
            strategy.quality_threshold,
            max_attempts=strategy.max_attempts
        )
        
        if result and result.get('quality_score', 0) >= strategy.quality_threshold:
            result['strategy_used'] = 'primary'
            result['category'] = category.value
            return result
        
        # Fallback to secondary timeframes
        self.logger.debug(f"🔄 Primary timeframes insufficient, trying fallback for {token_address}")
        fallback_result = await self._try_timeframes(
            token_address,
            strategy.fallback_timeframes,
            strategy.quality_threshold // 2,  # Lower threshold for fallback
            max_attempts=2
        )
        
        if fallback_result:
            fallback_result['strategy_used'] = 'fallback'
            fallback_result['category'] = category.value
            return fallback_result
        
        # No suitable data found
        return {
            'data': [],
            'timeframe': strategy.primary_timeframes[0],
            'quality_score': 0,
            'strategy_used': 'failed',
            'category': category.value,
            'reason': 'no_suitable_data'
        }
    
    async def _try_timeframes(self, token_address: str, timeframes: List[str], 
                              quality_threshold: int, max_attempts: int = 3) -> Optional[Dict[str, Any]]:
        """Try multiple timeframes and return best result"""
        
        attempts = 0
        best_result = None
        best_quality = 0
        
        for timeframe in timeframes[:max_attempts]:
            if attempts >= max_attempts:
                break
            
            try:
                self.logger.debug(f"  🔍 Trying timeframe {timeframe} for {token_address}")
                
                # Get OHLCV data for this timeframe
                ohlcv_data = await self.api_client.get_ohlcv_data(token_address, timeframe)
                
                if not ohlcv_data or not ohlcv_data.get('data'):
                    attempts += 1
                    continue
                
                # Assess data quality
                quality_metrics = self._assess_data_quality(ohlcv_data['data'], timeframe)
                quality_score = quality_metrics['quality_score']
                
                self.logger.debug(f"    📊 Quality score: {quality_score} (threshold: {quality_threshold})")
                
                # Update best result
                if quality_score > best_quality:
                    best_quality = quality_score
                    best_result = {
                        'data': ohlcv_data['data'],
                        'timeframe': timeframe,
                        'quality_score': quality_score,
                        'quality_metrics': quality_metrics
                    }
                
                # Early exit if quality is sufficient
                if quality_score >= quality_threshold:
                    self.logger.info(f"✅ Found suitable {timeframe} data for {token_address} (quality: {quality_score})")
                    return best_result
                
                attempts += 1
                
            except Exception as e:
                if "429" in str(e) or "rate limit" in str(e).lower():
                    # Stop trying more timeframes if rate limited
                    self.logger.warning(f"🚫 Rate limited while trying {timeframe} for {token_address}")
                    break
                
                self.logger.debug(f"    ❌ Error with {timeframe}: {e}")
                attempts += 1
                continue
        
        return best_result
    
    def _assess_data_quality(self, ohlcv_data: List[Dict], timeframe: str) -> Dict[str, Any]:
        """Assess quality of OHLCV data"""
        if not ohlcv_data:
            return {'quality_score': 0, 'reason': 'no_data'}
        
        data_points = len(ohlcv_data)
        
        # Count non-zero volumes
        volume_points = sum(1 for candle in ohlcv_data if candle.get('v', 0) > 0)
        volume_ratio = volume_points / data_points if data_points > 0 else 0
        
        # Count price movements (non-flat candles)
        price_movements = sum(1 for candle in ohlcv_data 
                             if candle.get('h', 0) != candle.get('l', 0))
        movement_ratio = price_movements / data_points if data_points > 0 else 0
        
        # Recent data bonus (more recent = higher quality)
        if ohlcv_data:
            latest_time = max(candle.get('unixTime', 0) for candle in ohlcv_data)
            recency_hours = (time.time() - latest_time) / 3600
            recency_bonus = max(0, 10 - recency_hours)  # Bonus points for recent data
        else:
            recency_bonus = 0
        
        # Calculate composite quality score
        base_score = min(50, data_points * 2)  # Base score from data quantity
        volume_score = volume_ratio * 30        # Volume activity score
        movement_score = movement_ratio * 15    # Price movement score
        
        quality_score = base_score + volume_score + movement_score + recency_bonus
        
        return {
            'quality_score': min(100, quality_score),
            'data_points': data_points,
            'volume_ratio': volume_ratio,
            'movement_ratio': movement_ratio,
            'recency_bonus': recency_bonus,
            'timeframe': timeframe,
            'has_sufficient_quality': quality_score > 30
        }


class EarlyExitStrategy:
    """
    Early exit logic to stop processing when sufficient high-quality candidates are found.
    
    Features:
    - Stage-based exit criteria
    - Quality-based thresholds
    - Cost optimization through early termination
    - Dynamic threshold adjustment
    """
    
    def __init__(self, config: Dict = None):
        """Initialize early exit strategy"""
        
        default_config = {
            'stage_thresholds': {
                'discovery': {'max_candidates': 500, 'quality_threshold': 0},
                'triage': {'max_candidates': 100, 'high_quality_target': 20, 'quality_threshold': 60},
                'enhanced': {'max_candidates': 50, 'high_quality_target': 10, 'quality_threshold': 70},
                'deep_analysis': {'max_candidates': 20, 'high_quality_target': 5, 'quality_threshold': 80},
                'final': {'max_candidates': 10, 'high_quality_target': 3, 'quality_threshold': 85}
            },
            'early_exit_enabled': True,
            'quality_score_key': 'final_score',
            'minimum_processing': 5  # Always process at least this many
        }
        
        self.config = {**default_config, **(config or {})}
        self.logger = logging.getLogger(__name__)
        
        # Statistics tracking
        self.stats = {
            'early_exits': 0,
            'candidates_saved': 0,
            'stages_skipped': []
        }
    
    def should_exit_early(self, stage: str, candidates: List[Dict], processed_count: int = 0) -> Tuple[bool, str]:
        """
        Determine if processing should exit early at current stage.
        
        Args:
            stage: Current processing stage
            candidates: List of candidates with scores
            processed_count: Number already processed in this stage
            
        Returns:
            Tuple of (should_exit, reason)
        """
        if not self.config['early_exit_enabled']:
            return False, "early_exit_disabled"
        
        if stage not in self.config['stage_thresholds']:
            return False, f"unknown_stage_{stage}"
        
        thresholds = self.config['stage_thresholds'][stage]
        quality_key = self.config['quality_score_key']
        
        # Always process minimum number
        if processed_count < self.config['minimum_processing']:
            return False, "minimum_not_met"
        
        # Check if we have enough high-quality candidates
        high_quality_target = thresholds.get('high_quality_target', 0)
        quality_threshold = thresholds.get('quality_threshold', 0)
        
        if high_quality_target > 0 and quality_threshold > 0:
            high_quality_count = sum(
                1 for candidate in candidates 
                if candidate.get(quality_key, 0) >= quality_threshold
            )
            
            if high_quality_count >= high_quality_target:
                reason = f"sufficient_quality_found_{high_quality_count}_of_{high_quality_target}"
                self.logger.info(f"🎯 Early exit at {stage}: Found {high_quality_count} high-quality candidates (target: {high_quality_target})")
                self._record_early_exit(stage, len(candidates) - processed_count)
                return True, reason
        
        # Check maximum candidates limit
        max_candidates = thresholds.get('max_candidates', float('inf'))
        if len(candidates) >= max_candidates:
            reason = f"max_candidates_reached_{len(candidates)}"
            self.logger.info(f"🛑 Early exit at {stage}: Maximum candidates reached ({len(candidates)})")
            self._record_early_exit(stage, 0)
            return True, reason
        
        return False, "continue_processing"
    
    def prioritize_candidates(self, candidates: List[Dict], stage: str) -> List[Dict]:
        """
        Prioritize candidates for processing to maximize early exit effectiveness.
        
        Args:
            candidates: List of candidates to prioritize
            stage: Current processing stage
            
        Returns:
            Sorted candidates list (highest priority first)
        """
        quality_key = self.config['quality_score_key']
        
        # Define priority factors based on stage
        priority_factors = {
            'discovery': ['bonding_curve_progress', 'market_cap'],
            'triage': ['graduation_imminent', 'priority', 'market_cap'],
            'enhanced': [quality_key, 'volume_24h', 'price_change_24h'],
            'deep_analysis': [quality_key, 'enhanced_score', 'conviction_score'],
            'final': [quality_key, 'final_conviction', 'overall_score']
        }
        
        factors = priority_factors.get(stage, [quality_key])
        
        def calculate_priority_score(candidate):
            """Calculate composite priority score"""
            score = 0
            
            for factor in factors:
                value = candidate.get(factor, 0)
                
                # Handle boolean flags
                if isinstance(value, bool):
                    score += 100 if value else 0
                # Handle string priorities
                elif isinstance(value, str):
                    priority_map = {'ultra_high': 100, 'high': 75, 'medium': 50, 'low': 25}
                    score += priority_map.get(value, 0)
                # Handle numeric values
                elif isinstance(value, (int, float)):
                    score += min(100, max(0, float(value)))
            
            return score / len(factors)  # Normalize by number of factors
        
        # Sort candidates by priority score (descending)
        prioritized = sorted(candidates, key=calculate_priority_score, reverse=True)
        
        self.logger.debug(f"📊 Prioritized {len(candidates)} candidates for {stage} processing")
        return prioritized
    
    def optimize_batch_size(self, stage: str, total_candidates: int) -> int:
        """
        Optimize batch size for processing to enable early exits.
        
        Args:
            stage: Current processing stage
            total_candidates: Total number of candidates
            
        Returns:
            Optimal batch size
        """
        thresholds = self.config['stage_thresholds'].get(stage, {})
        target_quality = thresholds.get('high_quality_target', 10)
        
        # Process in smaller batches for stages where early exit is likely
        if stage in ['enhanced', 'deep_analysis']:
            # Process 2x the target to increase early exit chances
            return min(total_candidates, max(5, target_quality * 2))
        else:
            # Larger batches for discovery stages
            return min(total_candidates, 25)
    
    def _record_early_exit(self, stage: str, candidates_saved: int):
        """Record early exit statistics"""
        self.stats['early_exits'] += 1
        self.stats['candidates_saved'] += candidates_saved
        self.stats['stages_skipped'].append(stage)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get early exit statistics"""
        return {
            **self.stats,
            'early_exit_enabled': self.config['early_exit_enabled'],
            'total_candidates_saved': self.stats['candidates_saved']
        }