"""
Volume Momentum Strategy

This strategy identifies tokens with significant trading activity growth
that may indicate emerging trends or market interest.
"""

import logging
import time
from typing import Dict, List, Any, Optional

from api.birdeye_connector import BirdeyeAPI
from .base_token_discovery_strategy import BaseTokenDiscoveryStrategy


class VolumeMomentumStrategy(BaseTokenDiscoveryStrategy):
    """
    Volume Momentum Strategy - Identify tokens with significant trading activity growth
    that may indicate emerging trends or market interest.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the Volume Momentum Strategy."""
        super().__init__(
            name="Volume Momentum Strategy",
            description="Identify tokens with significant trading activity growth that may indicate emerging trends or market interest.",
            api_parameters={
                "sort_by": "volume_24h_change_percent",
                "sort_type": "desc",
                "min_liquidity": 50000,      # Relaxed from 100000
                "min_volume_24h_usd": 25000, # Relaxed from 50000
                "min_holder": 250,           # Relaxed from 500
                "limit": 30                  # Increased from 20
            },
            min_consecutive_appearances=2,   # Relaxed from 3
            logger=logger
        )
    
    async def process_results(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process results with additional filtering for Volume Momentum Strategy.
        ENHANCED: Now includes trending token cross-reference and momentum validation.
        
        Risk Management:
        - Exclude suspicious volume patterns
        - Verify volume across multiple DEXs/pools
        - Check holder concentration metrics
        - ENHANCED: Trending momentum validation
        """
        # ENHANCED: Get trending tokens for cross-reference
        trending_addresses = set()
        try:
            # Use the trending monitor from base strategy
            trending_monitor = self._get_trending_monitor(birdeye_api)
            trending_tokens = await trending_monitor.get_trending_tokens(birdeye_api, limit=100)
            if trending_tokens:
                trending_addresses = {token.get('address') for token in trending_tokens if token.get('address')}
                self.logger.info(f"📈 Cross-referencing with {len(trending_addresses)} trending tokens")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to get trending tokens: {e}")
        
        processed_tokens = await super().process_results(tokens, birdeye_api, scan_id)
        filtered_tokens = []
        
        for token in processed_tokens:
            # Skip tokens with suspicious volume patterns
            volume_24h = token.get("volume24h", 0)
            volume_7d = token.get("volume7d", 0) or volume_24h * 7  # Estimate if not available
            
            # Check for abnormal volume spikes (relaxed threshold)
            suspicious_multiplier = self.risk_management["suspicious_volume_multiplier"] * 1.5  # Relaxed by 50%
            if volume_24h > volume_7d / 4 * suspicious_multiplier:
                self.logger.warning(f"Skipping token {token.get('symbol')} due to suspicious volume spike")
                continue
            
            # ENHANCED: Check trending status for momentum validation
            token_address = token.get('address')
            is_trending_match = token_address in trending_addresses
            
            # Add trending boost if token is also trending
            if is_trending_match:
                token['trending_momentum_match'] = True
                token['momentum_boost'] = 1.3  # 30% boost for trending + volume momentum
            
            # ENHANCED: Add strategy-specific analysis
            token["strategy_analysis"] = {
                "strategy_type": "volume_momentum",
                "analysis_timestamp": int(time.time()),
                "momentum_score": self._calculate_momentum_score(token),
                "volume_sustainability": self._calculate_volume_sustainability(token),
                "trending_confirmation": is_trending_match,
                "volume_quality_score": self._calculate_volume_quality(token)
            }
                
            # Add to filtered tokens
            filtered_tokens.append(token)
            
        trending_matches = sum(1 for t in filtered_tokens if t.get('trending_momentum_match'))
        self.logger.info(f"📈 Volume Momentum + Trending: {len(filtered_tokens)} tokens, {trending_matches} trending matches")
        return filtered_tokens 
    
    def _calculate_momentum_score(self, token: Dict[str, Any]) -> float:
        """Calculate momentum score based on volume changes and trends."""
        base_score = 0.5
        
        # Volume change percentage
        volume_change = token.get('volume_24h_change_percent', 0)
        if volume_change > 100:  # >100% increase
            base_score += 0.3
        elif volume_change > 50:  # >50% increase
            base_score += 0.2
        elif volume_change > 20:  # >20% increase
            base_score += 0.1
        
        # Trending confirmation
        if token.get('trending_momentum_match'):
            base_score += 0.2
        
        # Smart money involvement
        smart_money_score = token.get('smart_money_score', 0)
        base_score += smart_money_score * 0.1
        
        return min(1.0, base_score)
    
    def _calculate_volume_sustainability(self, token: Dict[str, Any]) -> float:
        """Calculate volume sustainability score."""
        base_score = 0.5
        
        # Check if volume growth is backed by trending status
        if token.get('is_trending'):
            base_score += 0.2
        
        # Check holder quality (good distribution = sustainable volume)
        holder_quality = token.get('holder_quality_score', 0.5)
        base_score += (holder_quality - 0.5) * 0.3
        
        # Check smart money involvement
        smart_money_score = token.get('smart_money_score', 0)
        base_score += smart_money_score * 0.2
        
        # Penalize suspicious volume patterns
        volume_24h = token.get("volume24h", 0)
        volume_7d = token.get("volume7d", 0) or volume_24h * 7
        if volume_24h > volume_7d / 3:  # Very high spike
            base_score -= 0.2
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_volume_quality(self, token: Dict[str, Any]) -> float:
        """Calculate volume quality score based on multiple factors."""
        base_score = 0.5
        
        # Volume to market cap ratio
        volume_24h = token.get("volume24h", 0)
        market_cap = token.get("marketCap", 0)
        
        if market_cap > 0:
            volume_to_mcap = volume_24h / market_cap
            if 0.1 <= volume_to_mcap <= 2.0:  # Healthy range
                base_score += 0.2
            elif volume_to_mcap > 5.0:  # Too high, suspicious
                base_score -= 0.3
        
        # Trade count to volume ratio (average trade size)
        trade_count = token.get("txns24h", 0)
        if trade_count > 0:
            avg_trade_size = volume_24h / trade_count
            if 100 <= avg_trade_size <= 10000:  # Reasonable trade sizes
                base_score += 0.2
            elif avg_trade_size < 10:  # Very small trades, potential manipulation
                base_score -= 0.2
        
        # Trending confirmation adds quality
        if token.get('trending_momentum_match'):
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score)) 