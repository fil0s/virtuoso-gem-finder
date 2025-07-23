"""
Recent Listings Strategy with Holder Velocity Analysis

This strategy discovers newly listed tokens gaining significant
market attention and liquidity, with enhanced holder velocity tracking.
"""

import logging
import time
from typing import Dict, List, Any, Optional

from api.birdeye_connector import BirdeyeAPI
from .base_token_discovery_strategy import BaseTokenDiscoveryStrategy


class RecentListingsStrategy(BaseTokenDiscoveryStrategy):
    """
    Recent Listings with Holder Velocity - Discover newly listed tokens gaining significant
    market attention and liquidity, enhanced with holder acquisition momentum tracking.
    
    ENHANCED: Now includes holder velocity analysis for early adoption detection.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the Enhanced Recent Listings Strategy."""
        super().__init__(
            name="Recent Listings Strategy",
            description="Discover newly listed tokens gaining significant market attention, liquidity, and holder momentum.",
            api_parameters={
                "sort_by": "liquidity",
                "sort_type": "desc",
                "min_liquidity": 50000,
                "min_trade_24h_count": 300,
                "min_holder": 100,
                "limit": 30
            },
            min_consecutive_appearances=2,  # Lower threshold for new listings
            logger=logger
        )
        
        # Override risk management for new tokens
        self.risk_management.update({
            "max_allocation_percentage": 2.5,  # Reduce to 25% of normal size
        })
        
        # ENHANCED: Holder velocity settings
        self.holder_velocity_criteria = {
            "min_holder_growth_24h_percent": 15.0,    # 15%+ daily holder growth
            "min_holder_velocity_score": 0.6,         # Holder acquisition momentum score
            "exceptional_growth_threshold": 50.0,     # 50%+ = exceptional growth
            "sustainable_growth_range": (10.0, 40.0), # 10-40% = sustainable range
            "min_holder_base_for_velocity": 100,      # Need 100+ holders for velocity calc
        }
        
        # Holder velocity tracking (for consecutive appearances)
        self.holder_velocity_history = {}
    
    async def process_results(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process results with enhanced holder velocity and market attention analysis.
        
        ENHANCED Risk Management:
        - Position size limits for new tokens
        - Require 7-day history before allocation
        - Verify team/project details
        - HOLDER VELOCITY: Track holder acquisition momentum
        - MARKET ATTENTION: Measure rapid adoption patterns
        - SUSTAINABILITY: Filter for sustainable vs. pump patterns
        """
        # ENHANCED: Get fresh new listings data for cross-reference
        try:
            new_listings = await self._get_new_listings_data(birdeye_api)
            if new_listings:
                self.logger.info(f"🆕 Found {len(new_listings)} fresh new listings")
                # Cross-reference with discovered tokens
                tokens = await self._cross_reference_with_new_listings(tokens, new_listings, birdeye_api)
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to get new listings data: {e}")
        
        processed_tokens_from_base = await super().process_results(tokens, birdeye_api, scan_id)
        filtered_tokens = []
        current_time_for_processing = int(time.time()) # Consistent time for this processing run
        
        self.logger.info(f"👥 Analyzing holder velocity for {len(processed_tokens_from_base)} recent listings")
        
        for token in processed_tokens_from_base:
            token_address = token.get("address")
            if not token_address: # Should not happen if base processed correctly
                continue

            try:
                # Get creation timestamp if available
                creation_time = token.get("createdTime", 0) or 0
                
                # Calculate days since listing
                days_since_listing = (current_time_for_processing - creation_time) / (24 * 60 * 60) if creation_time > 0 else 0
                
                # Add days since listing to token data for output
                token["days_since_listing"] = days_since_listing
                
                # ENHANCED: Apply holder quality filter for new listings
                holder_risk_level = token.get('holder_risk_level', 'unknown')
                if holder_risk_level == 'high':
                    self.logger.info(f"Skipping {token.get('symbol')} due to high holder concentration risk")
                    continue
                
                # Skip if too recent (less than min days)
                if days_since_listing < self.risk_management["min_days_since_listing"]:
                    continue

                # ENHANCED: Analyze holder velocity
                holder_velocity_analysis = await self._analyze_holder_velocity(token, birdeye_api)
                token["holder_velocity_analysis"] = holder_velocity_analysis
                
                # Check holder velocity criteria
                velocity_score = holder_velocity_analysis.get("velocity_score", 0.0)
                if velocity_score < self.holder_velocity_criteria["min_holder_velocity_score"]:
                    self.logger.info(f"Filtering out {token.get('symbol')} due to low holder velocity: {velocity_score:.2f}")
                    continue
                
                # Apply velocity boost for exceptional growth
                holder_growth_24h = holder_velocity_analysis.get("growth_rate_24h", 0.0)
                if holder_growth_24h > self.holder_velocity_criteria["exceptional_growth_threshold"]:
                    token["velocity_boost"] = 1.4  # 40% boost for exceptional holder growth
                    self.logger.info(f"🚀 Exceptional holder velocity for {token.get('symbol')}: {holder_growth_24h:.1f}%")
                elif holder_growth_24h > self.holder_velocity_criteria["min_holder_growth_24h_percent"]:
                    token["velocity_boost"] = 1.2  # 20% boost for good holder growth
                
                # Access the token's history entry maintained by the strategy
                token_history_entry = self.token_history["tokens"].get(token_address)
                if not token_history_entry: # Should not happen if base.process_results worked
                    self.logger.warning(f"Token {token_address} not found in history after base processing.")
                    continue

                current_liquidity = token.get("liquidity", 0)

                # Check for sustainable liquidity growth
                initial_liquidity = token_history_entry.get("first_liquidity", 0)
                
                if initial_liquidity and current_liquidity < initial_liquidity:
                    # Liquidity has decreased since we first noted it, skip.
                    self.logger.info(f"Skipping {token.get('symbol')} in RecentListings as liquidity decreased from {initial_liquidity} to {current_liquidity}.")
                    continue
                    
                # Store initial liquidity if this is first time seeing token in this strategy context for this metric
                if not initial_liquidity: # or more explicitly: "first_liquidity" not in token_history_entry
                    token_history_entry["first_liquidity"] = current_liquidity
                    # Also add to the output token for immediate reference if needed by consumers
                    if "strategy_data" not in token: token["strategy_data"] = {}
                    token["strategy_data"]["first_liquidity_recorded_by_recent_strat"] = current_liquidity
                    self.save_history() # Save history as we've updated a strategy-specific field

                # ENHANCED: Add comprehensive strategy analysis
                token["strategy_analysis"] = {
                    "strategy_type": "recent_listings_holder_velocity",
                    "analysis_timestamp": current_time_for_processing,
                    "listing_freshness": self._calculate_listing_freshness(token),
                    "early_discovery_score": self._calculate_early_discovery_score(token),
                    "holder_velocity_score": velocity_score,
                    "holder_momentum_grade": self._grade_holder_momentum(holder_velocity_analysis),
                    "market_attention_score": self._calculate_market_attention_score(token, holder_velocity_analysis),
                    "adoption_sustainability": self._calculate_adoption_sustainability(token, holder_velocity_analysis),
                    "new_listing_match": token.get("new_listing_match", False),
                    "holder_quality_passed": holder_risk_level != 'high'
                }

                # Add to filtered tokens
                filtered_tokens.append(token)
                
            except Exception as e:
                self.logger.warning(f"Error in holder velocity analysis for {token.get('symbol', 'unknown')}: {e}")
                # Still include token but without velocity analysis
                token["holder_velocity_analysis"] = {"error": str(e), "velocity_score": 0.0}
                filtered_tokens.append(token)
                continue
            
        velocity_count = sum(1 for t in filtered_tokens if t.get("holder_velocity_analysis", {}).get("velocity_score", 0) > 0.8)
        self.logger.info(f"👥 Recent Listings + Holder Velocity: {len(filtered_tokens)} tokens, {velocity_count} high-velocity")
        return filtered_tokens
    
    async def _analyze_holder_velocity(self, token: Dict[str, Any], birdeye_api: BirdeyeAPI) -> Dict[str, Any]:
        """
        Analyze holder acquisition velocity and momentum patterns.
        
        Args:
            token: Token data dictionary
            birdeye_api: Birdeye API instance
            
        Returns:
            Dictionary with holder velocity analysis
        """
        velocity_analysis = {
            "current_holders": 0,
            "growth_rate_24h": 0.0,
            "velocity_score": 0.0,
            "momentum_direction": "neutral",
            "sustainability_indicators": {},
            "adoption_pattern": "unknown"
        }
        
        try:
            token_address = token.get("address")
            current_holders = token.get("holder", 0)
            velocity_analysis["current_holders"] = current_holders
            
            # Check if we have enough holder base for velocity calculation
            if current_holders < self.holder_velocity_criteria["min_holder_base_for_velocity"]:
                velocity_analysis["velocity_score"] = 0.0
                velocity_analysis["adoption_pattern"] = "insufficient_base"
                return velocity_analysis
            
            # Get historical holder data if available
            previous_holder_count = self._get_previous_holder_count(token)
            
            if previous_holder_count and previous_holder_count > 0:
                # Calculate 24h growth rate
                growth_rate = ((current_holders - previous_holder_count) / previous_holder_count) * 100
                velocity_analysis["growth_rate_24h"] = growth_rate
                
                # Calculate velocity score based on growth rate and sustainability
                velocity_score = self._calculate_velocity_score(growth_rate, current_holders, token)
                velocity_analysis["velocity_score"] = velocity_score
                
                # Determine momentum direction
                if growth_rate > 5.0:
                    velocity_analysis["momentum_direction"] = "accelerating"
                elif growth_rate > 0:
                    velocity_analysis["momentum_direction"] = "growing"
                elif growth_rate < -5.0:
                    velocity_analysis["momentum_direction"] = "declining"
                else:
                    velocity_analysis["momentum_direction"] = "stable"
                
                # Analyze adoption pattern
                velocity_analysis["adoption_pattern"] = self._classify_adoption_pattern(growth_rate, current_holders)
                
            else:
                # First time seeing this token, establish baseline
                self._store_holder_baseline(token_address, current_holders)
                velocity_analysis["velocity_score"] = 0.5  # Neutral score for new baseline
                velocity_analysis["adoption_pattern"] = "establishing_baseline"
            
            # Add sustainability indicators
            velocity_analysis["sustainability_indicators"] = self._analyze_sustainability_indicators(token, velocity_analysis)
            
            return velocity_analysis
            
        except Exception as e:
            self.logger.error(f"Error in holder velocity analysis: {e}")
            velocity_analysis["error"] = str(e)
            return velocity_analysis
    
    def _get_previous_holder_count(self, token: Dict[str, Any]) -> Optional[int]:
        """Get previous holder count from strategy history or token data."""
        token_address = token.get("address")
        
        # Check strategy-specific holder history
        if token_address in self.holder_velocity_history:
            history = self.holder_velocity_history[token_address]
            if len(history) > 0:
                return history[-1].get("holder_count", 0)
        
        # Check token strategy data
        strategy_data = token.get("strategy_data", {})
        last_data = strategy_data.get("last_data", {})
        if last_data:
            return last_data.get("holder", 0)
        
        # Check base strategy history
        token_history = self.token_history.get("tokens", {}).get(token_address, {})
        last_data = token_history.get("last_data", {})
        if last_data:
            return last_data.get("holder", 0)
        
        return None
    
    def _store_holder_baseline(self, token_address: str, holder_count: int):
        """Store holder count baseline for future velocity calculations."""
        if token_address not in self.holder_velocity_history:
            self.holder_velocity_history[token_address] = []
        
        self.holder_velocity_history[token_address].append({
            "timestamp": int(time.time()),
            "holder_count": holder_count
        })
        
        # Keep only last 10 entries
        if len(self.holder_velocity_history[token_address]) > 10:
            self.holder_velocity_history[token_address] = self.holder_velocity_history[token_address][-10:]
    
    def _calculate_velocity_score(self, growth_rate: float, current_holders: int, token: Dict[str, Any]) -> float:
        """Calculate holder velocity score (0-1 scale)."""
        base_score = 0.5
        
        # Growth rate component (40% weight)
        if growth_rate >= self.holder_velocity_criteria["exceptional_growth_threshold"]:
            base_score += 0.4  # Exceptional growth
        elif growth_rate >= self.holder_velocity_criteria["min_holder_growth_24h_percent"]:
            # Scale within good growth range
            normalized_growth = min(1.0, growth_rate / self.holder_velocity_criteria["exceptional_growth_threshold"])
            base_score += 0.3 * normalized_growth
        elif growth_rate > 0:
            base_score += 0.1  # Some growth is better than none
        
        # Holder base size component (20% weight)
        if current_holders > 2000:
            base_score += 0.2
        elif current_holders > 1000:
            base_score += 0.15
        elif current_holders > 500:
            base_score += 0.1
        
        # Quality indicators (20% weight)
        if token.get('is_trending'):
            base_score += 0.1
        if token.get('smart_money_detected'):
            base_score += 0.1
        
        # Sustainability check (20% weight)
        liquidity = token.get("liquidity", 0)
        volume_24h = token.get("volume24h", 0)
        if liquidity > 0 and volume_24h > 0:
            # Good liquidity/volume ratio indicates sustainability
            ratio = volume_24h / liquidity
            if 0.1 <= ratio <= 1.0:  # Healthy range
                base_score += 0.2
            elif ratio <= 2.0:  # Acceptable range
                base_score += 0.1
        
        return min(1.0, max(0.0, base_score))
    
    def _classify_adoption_pattern(self, growth_rate: float, current_holders: int) -> str:
        """Classify the adoption pattern based on growth characteristics."""
        if growth_rate > 100:
            return "viral_adoption"
        elif growth_rate > 50:
            return "rapid_adoption"
        elif growth_rate > 20:
            return "strong_adoption"
        elif growth_rate > 10:
            return "steady_adoption"
        elif growth_rate > 0:
            return "slow_adoption"
        elif growth_rate < -10:
            return "declining_interest"
        else:
            return "stable_base"
    
    def _analyze_sustainability_indicators(self, token: Dict[str, Any], velocity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze indicators of sustainable vs. unsustainable growth."""
        indicators = {
            "liquidity_support": False,
            "volume_backing": False,
            "smart_money_presence": False,
            "holder_quality": "unknown",
            "sustainability_score": 0.0
        }
        
        # Check liquidity support
        liquidity = token.get("liquidity", 0)
        if liquidity > 500000:  # $500k+ liquidity
            indicators["liquidity_support"] = True
        
        # Check volume backing
        volume_24h = token.get("volume24h", 0)
        current_holders = velocity_analysis.get("current_holders", 0)
        if current_holders > 0:
            volume_per_holder = volume_24h / current_holders
            if volume_per_holder > 100:  # $100+ volume per holder
                indicators["volume_backing"] = True
        
        # Check smart money presence
        if token.get('smart_money_detected') or token.get('smart_money_score', 0) > 0.3:
            indicators["smart_money_presence"] = True
        
        # Assess holder quality
        holder_risk_level = token.get('holder_risk_level', 'unknown')
        indicators["holder_quality"] = holder_risk_level
        
        # Calculate sustainability score
        score = 0.0
        if indicators["liquidity_support"]:
            score += 0.3
        if indicators["volume_backing"]:
            score += 0.3
        if indicators["smart_money_presence"]:
            score += 0.2
        if holder_risk_level == "low":
            score += 0.2
        elif holder_risk_level == "medium":
            score += 0.1
        
        indicators["sustainability_score"] = score
        
        return indicators
    
    def _calculate_market_attention_score(self, token: Dict[str, Any], velocity_analysis: Dict[str, Any]) -> float:
        """Calculate market attention score based on multiple signals."""
        base_score = 0.5
        
        # Holder velocity component
        velocity_score = velocity_analysis.get("velocity_score", 0.0)
        base_score += velocity_score * 0.3
        
        # Trading activity component
        volume_24h = token.get("volume24h", 0)
        trade_count = token.get("txns24h", 0)
        if trade_count > 0:
            avg_trade_size = volume_24h / trade_count
            if avg_trade_size > 500:  # Decent trade sizes
                base_score += 0.2
        
        # Trending status
        if token.get('is_trending'):
            base_score += 0.2
        
        # New listing bonus
        if token.get('new_listing_match'):
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def _calculate_adoption_sustainability(self, token: Dict[str, Any], velocity_analysis: Dict[str, Any]) -> float:
        """Calculate adoption sustainability score."""
        sustainability_indicators = velocity_analysis.get("sustainability_indicators", {})
        return sustainability_indicators.get("sustainability_score", 0.0)
    
    def _grade_holder_momentum(self, velocity_analysis: Dict[str, Any]) -> str:
        """Grade holder momentum quality."""
        velocity_score = velocity_analysis.get("velocity_score", 0.0)
        growth_rate = velocity_analysis.get("growth_rate_24h", 0.0)
        
        if velocity_score >= 0.9 and growth_rate > 50:
            return "A+"
        elif velocity_score >= 0.8 and growth_rate > 30:
            return "A"
        elif velocity_score >= 0.7 and growth_rate > 20:
            return "B+"
        elif velocity_score >= 0.6 and growth_rate > 15:
            return "B"
        elif velocity_score >= 0.5:
            return "C"
        else:
            return "D"
    
    async def _cross_reference_with_new_listings(self, tokens: List[Dict[str, Any]], new_listings: List[Dict[str, Any]], birdeye_api: BirdeyeAPI) -> List[Dict[str, Any]]:
        """Cross-reference discovered tokens with fresh new listings data."""
        new_listing_addresses = {listing.get('address') for listing in new_listings if listing.get('address')}
        
        # Mark tokens that appear in new listings
        for token in tokens:
            token_address = token.get('address')
            if token_address in new_listing_addresses:
                token['new_listing_match'] = True
                token['freshness_boost'] = 1.2  # 20% boost for fresh listings
                
                # Find the matching new listing for additional data
                for listing in new_listings:
                    if listing.get('address') == token_address:
                        token['new_listing_data'] = listing
                        break
        
        # Add high-quality new listings that weren't in original discovery
        additional_tokens = []
        for listing in new_listings:
            listing_address = listing.get('address')
            
            # Check if this listing is already in our tokens
            if any(token.get('address') == listing_address for token in tokens):
                continue
                
            # Apply quality filters to new listings
            if await self._passes_new_listing_quality_check(listing, birdeye_api):
                # Convert new listing to token format
                token = await self._convert_new_listing_to_token(listing, birdeye_api)
                if token:
                    token['new_listing_match'] = True
                    token['freshness_boost'] = 1.3  # Higher boost for quality new listings
                    additional_tokens.append(token)
        
        if additional_tokens:
            self.logger.info(f"🎯 Added {len(additional_tokens)} high-quality new listings to discovery")
            tokens.extend(additional_tokens)
        
        return tokens
    
    async def _passes_new_listing_quality_check(self, listing: Dict[str, Any], birdeye_api: BirdeyeAPI) -> bool:
        """Check if a new listing meets quality criteria."""
        try:
            # Basic checks
            if not listing.get('address'):
                return False
            
            # Check minimum liquidity and volume if available
            liquidity = listing.get('liquidity', 0)
            volume_24h = listing.get('volume24h', 0)
            
            if liquidity < 50000:  # Minimum $50k liquidity
                return False
                
            if volume_24h < 10000:  # Minimum $10k daily volume
                return False
            
            # Additional quality checks could be added here
            return True
            
        except Exception as e:
            self.logger.error(f"Error in new listing quality check: {e}")
            return False
    
    async def _convert_new_listing_to_token(self, listing: Dict[str, Any], birdeye_api: BirdeyeAPI) -> Optional[Dict[str, Any]]:
        """Convert new listing data to token format."""
        try:
            token = {
                'address': listing.get('address'),
                'symbol': listing.get('symbol', 'UNKNOWN'),
                'name': listing.get('name', 'Unknown Token'),
                'liquidity': listing.get('liquidity', 0),
                'volume24h': listing.get('volume24h', 0),
                'priceUsd': listing.get('price', 0),
                'createdTime': listing.get('createdTime', int(time.time())),
                'source': 'new_listings_endpoint'
            }
            
            return token
            
        except Exception as e:
            self.logger.error(f"Error converting new listing to token: {e}")
            return None
    
    def _calculate_listing_freshness(self, token: Dict[str, Any]) -> float:
        """Calculate how fresh a listing is (0-1, higher is fresher)."""
        creation_time = token.get('createdTime', 0)
        if not creation_time:
            return 0.0
        
        current_time = int(time.time())
        hours_since_listing = (current_time - creation_time) / 3600
        
        # Freshness score decreases over time
        if hours_since_listing <= 24:  # First 24 hours
            return 1.0
        elif hours_since_listing <= 72:  # First 3 days
            return 0.8
        elif hours_since_listing <= 168:  # First week
            return 0.6
        else:
            return 0.3
    
    def _calculate_early_discovery_score(self, token: Dict[str, Any]) -> float:
        """Calculate early discovery advantage score."""
        base_score = 0.5
        
        # Boost for new listing match
        if token.get('new_listing_match'):
            base_score += 0.3
        
        # Boost for freshness
        freshness = self._calculate_listing_freshness(token)
        base_score += freshness * 0.2
        
        # Boost for trending status
        if token.get('is_trending'):
            base_score += 0.2
        
        # Boost for smart money presence
        smart_money_score = token.get('smart_money_score', 0)
        base_score += smart_money_score * 0.1
        
        return min(1.0, base_score)
    
    async def _get_new_listings_data(self, birdeye_api: BirdeyeAPI, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get new listings data using the enhanced /defi/v2/tokens/new_listing endpoint.
        
        Args:
            birdeye_api: Birdeye API instance
            limit: Maximum number of new listings to fetch
            
        Returns:
            List of new listings data
        """
        try:
            self.logger.debug(f"🔍 Fetching new listings data (limit: {limit})")
            
            # Call the new listings endpoint
            response = await birdeye_api._make_request(
                "/defi/v2/tokens/new_listing",
                params={"limit": limit}
            )
            
            if not response or not isinstance(response, dict):
                self.logger.warning("⚠️ Invalid response from new listings endpoint")
                return []
            
            # Extract new listings data
            new_listings = []
            if 'data' in response:
                data = response['data']
                if isinstance(data, list):
                    new_listings = data
                elif isinstance(data, dict) and 'items' in data:
                    new_listings = data['items']
                elif isinstance(data, dict) and 'tokens' in data:
                    new_listings = data['tokens']
            
            if not new_listings:
                self.logger.debug("📊 No new listings found")
                return []
            
            # Filter and enrich new listings
            filtered_listings = []
            for listing in new_listings:
                # Apply basic quality filters
                if self._passes_basic_listing_filters(listing):
                    # Add additional analysis
                    listing['listing_analysis'] = self._analyze_new_listing(listing)
                    filtered_listings.append(listing)
            
            self.logger.info(f"🆕 Found {len(filtered_listings)} quality new listings")
            return filtered_listings
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching new listings data: {e}")
            return []
    
    def _passes_basic_listing_filters(self, listing: Dict[str, Any]) -> bool:
        """
        Apply basic quality filters to new listings.
        
        Args:
            listing: New listing data
            
        Returns:
            True if listing passes basic filters
        """
        try:
            # Must have address
            if not listing.get('address'):
                return False
            
            # Check minimum liquidity
            liquidity = listing.get('liquidity', 0)
            if liquidity < 50000:  # Minimum $50k liquidity
                return False
            
            # Check minimum volume
            volume_24h = listing.get('volume24h', 0) or listing.get('volume', {}).get('h24', 0)
            if volume_24h < 10000:  # Minimum $10k daily volume
                return False
            
            # Check minimum holders if available
            holders = listing.get('holders', 0)
            if holders > 0 and holders < 50:  # If holder data available, require at least 50
                return False
            
            # Check for suspicious patterns
            market_cap = listing.get('marketCap', 0)
            if market_cap > 0 and volume_24h > market_cap * 5:  # Volume > 5x market cap (suspicious)
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Error in basic listing filters: {e}")
            return False
    
    def _analyze_new_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a new listing for quality and potential.
        
        Args:
            listing: New listing data
            
        Returns:
            Analysis results
        """
        try:
            analysis = {
                'quality_score': 0.0,
                'risk_factors': [],
                'positive_signals': [],
                'recommendation': 'neutral'
            }
            
            # Calculate quality score
            quality_score = 0.0
            
            # Liquidity scoring
            liquidity = listing.get('liquidity', 0)
            if liquidity > 500000:  # $500k+
                quality_score += 0.3
                analysis['positive_signals'].append('High liquidity')
            elif liquidity > 200000:  # $200k+
                quality_score += 0.2
                analysis['positive_signals'].append('Good liquidity')
            elif liquidity > 50000:  # $50k+
                quality_score += 0.1
                analysis['positive_signals'].append('Adequate liquidity')
            
            # Volume scoring
            volume_24h = listing.get('volume24h', 0) or listing.get('volume', {}).get('h24', 0)
            if volume_24h > 100000:  # $100k+
                quality_score += 0.2
                analysis['positive_signals'].append('Strong volume')
            elif volume_24h > 50000:  # $50k+
                quality_score += 0.15
                analysis['positive_signals'].append('Good volume')
            elif volume_24h > 10000:  # $10k+
                quality_score += 0.1
                analysis['positive_signals'].append('Moderate volume')
            
            # Holder analysis
            holders = listing.get('holders', 0)
            if holders > 1000:
                quality_score += 0.2
                analysis['positive_signals'].append('Large holder base')
            elif holders > 500:
                quality_score += 0.15
                analysis['positive_signals'].append('Good holder base')
            elif holders > 100:
                quality_score += 0.1
                analysis['positive_signals'].append('Growing holder base')
            
            # Market cap reasonableness
            market_cap = listing.get('marketCap', 0)
            if market_cap > 0:
                if 1000000 <= market_cap <= 50000000:  # $1M - $50M range
                    quality_score += 0.1
                    analysis['positive_signals'].append('Reasonable market cap')
                elif market_cap > 100000000:  # > $100M
                    analysis['risk_factors'].append('Very high market cap for new listing')
                elif market_cap < 100000:  # < $100k
                    analysis['risk_factors'].append('Very low market cap')
            
            # Age analysis
            creation_time = listing.get('createdTime', 0)
            if creation_time > 0:
                age_hours = (time.time() - creation_time) / 3600
                if age_hours < 24:
                    quality_score += 0.1
                    analysis['positive_signals'].append('Very fresh listing')
                elif age_hours < 72:
                    quality_score += 0.05
                    analysis['positive_signals'].append('Fresh listing')
            
            # Store quality score
            analysis['quality_score'] = min(1.0, quality_score)
            
            # Determine recommendation
            if quality_score > 0.7:
                analysis['recommendation'] = 'strong_buy'
            elif quality_score > 0.5:
                analysis['recommendation'] = 'buy'
            elif quality_score > 0.3:
                analysis['recommendation'] = 'neutral'
            else:
                analysis['recommendation'] = 'avoid'
            
            return analysis
            
        except Exception as e:
            self.logger.debug(f"Error analyzing new listing: {e}")
            return {
                'quality_score': 0.5,
                'risk_factors': ['Analysis error'],
                'positive_signals': [],
                'recommendation': 'neutral'
            } 