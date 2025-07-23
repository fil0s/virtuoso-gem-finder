"""
Liquidity Growth Strategy

This strategy finds tokens rapidly gaining liquidity, 
a leading indicator for price movements.
"""

import logging
import time
from typing import Dict, List, Any, Optional

from api.birdeye_connector import BirdeyeAPI
from .base_token_discovery_strategy import BaseTokenDiscoveryStrategy


class LiquidityGrowthStrategy(BaseTokenDiscoveryStrategy):
    """
    Liquidity Growth Detector - Find tokens rapidly gaining liquidity, 
    a leading indicator for price movements.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the Liquidity Growth Detector Strategy."""
        super().__init__(
            name="Liquidity Growth Strategy",
            description="Find tokens rapidly gaining liquidity, a leading indicator for price movements.",
            api_parameters={
                "sort_by": "liquidity",
                "sort_type": "desc",
                "min_liquidity": 50000,  # Relaxed from 1000000 for broader discovery
                "min_volume_24h_usd": 25000,  # Relaxed from 200000 for broader discovery  
                "min_holder": 250,  # Relaxed from 1000 for broader discovery
                "limit": 50
            },
            min_consecutive_appearances=2,  # Relaxed from 3
            logger=logger
        )
        
        # Market cap filtering configuration (moved from API parameters)
        self.market_cap_filters = {
            "min_market_cap": 500000,  # $500K minimum (relaxed from $1M)
            "max_market_cap": 100000000,  # $100M maximum
        }
    
    async def process_results(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process results with additional filtering for Liquidity Growth Strategy.
        ENHANCED: Now includes holder distribution analysis for liquidity quality.
        FIXED: Market cap filtering moved to post-processing to fix API parameter error.
        
        Risk Management:
        - Verify distributed liquidity
        - Watch for single-wallet provision
        - Monitor 7-day liquidity stability
        - ENHANCED: Holder distribution analysis
        - FIXED: Market cap range filtering in post-processing
        """
        processed_tokens = await super().process_results(tokens, birdeye_api, scan_id)
        filtered_tokens = []
        
        for token in processed_tokens:
            # FIXED: Apply market cap filtering in post-processing since API doesn't support it
            market_cap = token.get("marketCap", 0)
            if market_cap > 0:  # Only apply filter if market cap data is available
                if market_cap < self.market_cap_filters["min_market_cap"]:
                    self.logger.debug(f"Skipping {token.get('symbol')} - market cap ${market_cap:,.0f} below minimum ${self.market_cap_filters['min_market_cap']:,.0f}")
                    continue
                if market_cap > self.market_cap_filters["max_market_cap"]:
                    self.logger.debug(f"Skipping {token.get('symbol')} - market cap ${market_cap:,.0f} above maximum ${self.market_cap_filters['max_market_cap']:,.0f}")
                    continue
            
            # Calculate liquidity-to-market-cap ratio
            liquidity = token.get("liquidity", 0)
            
            if market_cap > 0:
                liq_to_mcap_ratio = liquidity / market_cap
                
                # Add ratio to token data
                token["liq_to_mcap_ratio"] = liq_to_mcap_ratio
                
                # Skip tokens with very low liquidity relative to market cap
                if liq_to_mcap_ratio < 0.05:  # Less than 5% of market cap in liquidity
                    continue
            
            # ENHANCED: Check holder distribution quality
            holder_analysis = token.get('holder_analysis', {})
            holder_risk_level = holder_analysis.get('risk_level', 'unknown')
            
            # Skip tokens with high concentration risk
            if holder_risk_level == 'high':
                self.logger.info(f"Skipping {token.get('symbol')} due to high holder concentration risk")
                continue
            # Check for growing holder count
            holders = token.get("holder", 0)
            prev_holders = token.get("strategy_data", {}).get("last_data", {}).get("holder", 0)
            
            if prev_holders and holders <= prev_holders:
                continue
            
            # ENHANCED: Add strategy-specific analysis
            token["strategy_analysis"] = {
                "strategy_type": "liquidity_growth",
                "analysis_timestamp": int(time.time()),
                "liquidity_quality_score": self._calculate_liquidity_quality(token),
                "growth_sustainability": self._calculate_growth_sustainability(token),
                "holder_distribution_quality": holder_analysis.get('distribution_score', 0),
                "liquidity_concentration_risk": holder_analysis.get('whale_concentration', 0),
                "market_cap_category": self._categorize_market_cap(market_cap),
                "market_cap_filter_passed": True  # Since we got here, it passed the filter
            }
                
            # Add to filtered tokens
            filtered_tokens.append(token)
            
        self.logger.info(f"💧 Liquidity Growth + Market Cap Filter: {len(processed_tokens)} -> {len(filtered_tokens)} tokens")
        return filtered_tokens 
    
    def _categorize_market_cap(self, market_cap: float) -> str:
        """Categorize market cap for analysis."""
        if market_cap >= 1_000_000_000:
            return "Large Cap"
        elif market_cap >= 100_000_000:
            return "Mid Cap"
        elif market_cap >= 10_000_000:
            return "Small Cap"
        elif market_cap >= 1_000_000:
            return "Micro Cap"
        else:
            return "Nano Cap"
    
    def _calculate_liquidity_quality(self, token: Dict[str, Any]) -> float:
        """Calculate liquidity quality score based on multiple factors."""
        base_score = 0.5
        
        # Liquidity to market cap ratio
        liq_to_mcap = token.get('liq_to_mcap_ratio', 0)
        if 0.1 <= liq_to_mcap <= 0.5:  # Healthy range 10-50%
            base_score += 0.2
        elif liq_to_mcap > 0.05:  # At least 5%
            base_score += 0.1
        
        # Holder distribution quality
        holder_quality = token.get('holder_quality_score', 0.5)
        base_score += (holder_quality - 0.5) * 0.3
        
        # Smart money involvement
        smart_money_score = token.get('smart_money_score', 0)
        base_score += smart_money_score * 0.2
        
        # Trending status indicates quality liquidity
        if token.get('is_trending'):
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_growth_sustainability(self, token: Dict[str, Any]) -> float:
        """Calculate growth sustainability based on distribution and activity."""
        base_score = 0.5
        
        # Holder distribution indicates sustainable growth
        holder_analysis = token.get('holder_analysis', {})
        
        # Good distribution = sustainable growth
        distribution_score = holder_analysis.get('distribution_score', 0)
        base_score += distribution_score * 0.3
        
        # Low concentration risk = more sustainable
        whale_concentration = holder_analysis.get('whale_concentration', 0)
        if whale_concentration < 0.3:  # Less than 30% whale concentration
            base_score += 0.2
        elif whale_concentration > 0.6:  # High whale concentration
            base_score -= 0.2
        
        # Smart money presence indicates sustainability
        smart_money_score = token.get('smart_money_score', 0)
        base_score += smart_money_score * 0.2
        
        # Growing holder count
        holders = token.get("holder", 0)
        if holders > 2000:  # Large holder base
            base_score += 0.1
        elif holders > 1000:  # Decent holder base
            base_score += 0.05
        
        return max(0.0, min(1.0, base_score)) 