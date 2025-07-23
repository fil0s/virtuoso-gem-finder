"""
High Trading Activity Strategy

This strategy discovers tokens with unusually high trading activity
relative to market cap.
"""

import logging
import time
from typing import Dict, List, Any, Optional

from api.birdeye_connector import BirdeyeAPI
from .base_token_discovery_strategy import BaseTokenDiscoveryStrategy


class HighTradingActivityStrategy(BaseTokenDiscoveryStrategy):
    """
    High Trading Activity Filter - Discover tokens with unusually high trading activity
    relative to market cap.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the High Trading Activity Filter Strategy."""
        super().__init__(
            name="High Trading Activity Strategy",
            description="Discover tokens with unusually high trading activity relative to market cap.",
            api_parameters={
                "sort_by": "trade_24h_count",
                "sort_type": "desc",
                "min_liquidity": 75000,      # Relaxed from 150000
                "min_volume_24h_usd": 37500, # Relaxed from 75000
                "min_holder": 200,           # Relaxed from 400
                "limit": 40                  # Increased from 30
            },
            min_consecutive_appearances=2,   # Relaxed from 3
            logger=logger
        )
    
    async def process_results(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process results with additional filtering for High Trading Activity Strategy.
        ENHANCED: Now includes smart money analysis from top traders.
        
        Risk Management:
        - Verify trade count distribution
        - Identify bot/wash trade patterns
        - Compare with historical activity
        - ENHANCED: Smart money validation
        """
        processed_tokens = await super().process_results(tokens, birdeye_api, scan_id=scan_id)
        filtered_tokens = []
        
        for token in processed_tokens:
            # Calculate trade count to market cap ratio
            trade_count = token.get("txns24h", 0)
            market_cap = token.get("marketCap", 0)
            
            if market_cap > 0:
                trades_per_mcap = (trade_count * 1000000) / market_cap  # Trades per $1M market cap
                
                # Add ratio to token data
                token["trades_per_mcap"] = trades_per_mcap
                
                # Skip tokens with abnormally high trading activity (potential wash trading) - relaxed threshold
                if trades_per_mcap > 750:  # Relaxed from 500 to 750 trades per $1M market cap
                    self.logger.warning(f"Skipping token {token.get('symbol')} due to potential wash trading")
                    continue
            
            # ENHANCED: Smart money validation for high activity tokens
            trader_analysis = token.get('trader_analysis', {})
            smart_money_score = trader_analysis.get('smart_money_score', 0)
            total_traders = trader_analysis.get('total_traders', 0)
            
            # Filter out tokens with poor trader quality (unless very few traders)
            if total_traders > 5 and smart_money_score < 0.1:
                self.logger.info(f"Filtering out {token.get('symbol')} due to low smart money presence despite high activity")
                continue
            
            # ENHANCED: Add strategy-specific analysis
            token["strategy_analysis"] = {
                "strategy_type": "high_trading_activity",
                "analysis_timestamp": int(time.time()),
                "trading_velocity": self._calculate_trading_velocity(token),
                "activity_sustainability": self._calculate_activity_sustainability(token),
                "smart_money_validation": smart_money_score > 0.3,
                "trader_quality_score": trader_analysis.get('overall_trader_quality', 0),
                "wash_trading_risk": trades_per_mcap > 300 if market_cap > 0 else False
            }
            
            # Add to filtered tokens
            filtered_tokens.append(token)
            
        self.logger.info(f"🧠 High Activity + Smart Money filtering: {len(processed_tokens)} -> {len(filtered_tokens)} tokens")
        return filtered_tokens 
    
    def _calculate_trading_velocity(self, token: Dict[str, Any]) -> float:
        """Calculate trading velocity score (0-1, higher is more active)."""
        trade_count = token.get("txns24h", 0)
        volume_24h = token.get("volume24h", 0)
        
        if trade_count == 0:
            return 0.0
        
        # Average trade size
        avg_trade_size = volume_24h / trade_count if trade_count > 0 else 0
        
        # Velocity score based on trade frequency and average size
        frequency_score = min(1.0, trade_count / 1000)  # Normalize to 1000 trades
        size_score = min(1.0, avg_trade_size / 1000)    # Normalize to $1000 avg trade
        
        return (frequency_score * 0.7) + (size_score * 0.3)
    
    def _calculate_activity_sustainability(self, token: Dict[str, Any]) -> float:
        """Calculate activity sustainability score based on multiple factors."""
        base_score = 0.5
        
        # Check smart money involvement
        smart_money_score = token.get('smart_money_score', 0)
        base_score += smart_money_score * 0.3
        
        # Check if trending (indicates sustained interest)
        if token.get('is_trending'):
            base_score += 0.2
        
        # Check holder quality
        holder_quality = token.get('holder_quality_score', 0.5)
        base_score += (holder_quality - 0.5) * 0.2  # Adjust based on distribution quality
        
        # Penalize potential wash trading
        trades_per_mcap = token.get('trades_per_mcap', 0)
        if trades_per_mcap > 300:
            base_score -= 0.2
        
        return max(0.0, min(1.0, base_score)) 