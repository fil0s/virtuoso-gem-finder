"""
Smart Money Whale Strategy

This strategy discovers tokens based on smart money and whale activity patterns.
Unlike other strategies that use smart money as enrichment, this strategy uses
whale and smart money activity as the primary discovery mechanism.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Set

from api.birdeye_connector import BirdeyeAPI
from .base_token_discovery_strategy import BaseTokenDiscoveryStrategy


class SmartMoneyWhaleStrategy(BaseTokenDiscoveryStrategy):
    """
    Smart Money Whale Strategy - Discover tokens based on whale and smart money activity patterns.
    
    This strategy uses a different approach than other strategies:
    1. Starts with whale movement data and smart money activity
    2. Discovers tokens that whales/smart money are actively trading
    3. Applies additional filters for quality and sustainability
    
    Key differentiators:
    - Uses whale activity as primary discovery mechanism
    - Focuses on skill-based trader analysis
    - Combines size-based (whale) and skill-based (smart money) signals
    - Prioritizes tokens with confluent whale + smart money activity
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the Smart Money Whale Strategy."""
        super().__init__(
            name="Smart Money Whale Strategy",
            description="Discover tokens based on whale and smart money activity patterns.",
            api_parameters={
                # RELAXED: More accessible parameters for broader token discovery
                "sort_by": "volume_24h_usd",
                "sort_type": "desc",
                "min_liquidity": 100000,      # Reduced from 500000 (80% reduction)
                "min_volume_24h_usd": 200000, # Reduced from 1000000 (80% reduction)
                "min_holder": 200,            # Reduced from 1000 (80% reduction)
                "limit": 50                   # Reduced from 100 for efficiency
            },
            min_consecutive_appearances=1,    # Reduced from 2 for faster discovery
            logger=logger
        )
        
        # RELAXED: Smart money whale specific thresholds
        self.whale_smart_money_criteria = {
            # Whale activity requirements - ULTRA RELAXED
            "min_whale_count": 0,                    # ULTRA RELAXED: Allow any whale activity
            "min_whale_volume": 0,                   # ULTRA RELAXED: Allow any whale volume
            "whale_confidence_threshold": 0.0,       # ULTRA RELAXED: Accept any confidence level
            
            # Smart money requirements - ULTRA RELAXED
            "min_smart_traders": 0,                  # ULTRA RELAXED: Allow any smart trader activity
            "smart_money_skill_threshold": 0.0,      # ULTRA RELAXED: Accept any skill level
            "smart_money_confidence_threshold": 0.0, # ULTRA RELAXED: Accept any confidence level
            
            # Confluence requirements - ULTRA RELAXED
            "confluence_bonus_multiplier": 1.1,      # Minimal bonus
            "min_confluence_score": 0.0,            # ULTRA RELAXED: Accept any confluence
            
            # Risk management - ULTRA LENIENT
            "max_whale_concentration": 1.0,          # Allow complete concentration
            "min_whale_diversity": 0,                # No diversity requirement
            "whale_directional_bias_threshold": 0.0, # No directional agreement requirement
        }
        
        # RELAXED: Override risk management for broader discovery
        self.risk_management.update({
            "max_allocation_percentage": 10.0,       # Increased from 7.5 - higher allocation for opportunities
            "min_dexs_with_liquidity": 2,           # Reduced from 3 - fewer DEX requirements
            "suspicious_volume_multiplier": 10.0,    # Increased from 5.0 - more lenient for whale activity
            "min_holder_distribution": 0.3,          # Reduced from 0.5 - more lenient distribution
            "max_concentration_pct": 80.0,           # Increased from 70.0 - allow higher concentration
        })
        
        # Whale and smart money service instances (initialized lazily)
        self._whale_shark_tracker = None
        self._smart_money_detector = None
        
    async def execute(self, birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Execute the Smart Money Whale Strategy.
        
        This strategy has a different execution flow:
        1. Get initial token list (larger set)
        2. Filter by whale and smart money activity
        3. Apply confluence analysis
        4. Rank by combined whale + smart money signals
        
        Args:
            birdeye_api: Initialized Birdeye API instance
            scan_id: Optional scan ID for structured logging
            
        Returns:
            List of tokens with high whale and smart money activity
        """
        execution_start_time = time.time()
        self.structured_logger.info({
            "event": "smart_money_whale_strategy_start", 
            "strategy": self.name, 
            "scan_id": scan_id, 
            "timestamp": int(time.time())
        })
        
        self.logger.info(f"🐋🧠 Executing {self.name} - discovering tokens via whale and smart money activity")
        
        try:
            # Initialize whale and smart money services
            await self._initialize_whale_smart_money_services(birdeye_api)
            
            # Step 1: Get initial token universe (larger set for whale activity)
            initial_tokens = await self._get_initial_token_universe(birdeye_api)
            self.logger.info(f"🎯 Initial token universe: {len(initial_tokens)} tokens")
            
            if not initial_tokens:
                self.logger.warning("No tokens in initial universe")
                return []
            
            # Step 2: Filter by whale activity
            whale_active_tokens = await self._filter_by_whale_activity(initial_tokens, birdeye_api, scan_id)
            self.logger.info(f"🐋 Whale-active tokens: {len(whale_active_tokens)} tokens")
            
            # Step 3: Filter by smart money activity  
            smart_money_tokens = await self._filter_by_smart_money_activity(whale_active_tokens, birdeye_api, scan_id)
            self.logger.info(f"🧠 Smart money active tokens: {len(smart_money_tokens)} tokens")
            
            # Step 4: Apply confluence analysis (tokens with both whale + smart money)
            confluence_tokens = await self._apply_confluence_analysis(smart_money_tokens, birdeye_api, scan_id)
            self.logger.info(f"🎯 High-confluence tokens: {len(confluence_tokens)} tokens")
            
            # Step 5: Final processing and ranking
            processed_tokens = await self.process_results(confluence_tokens, birdeye_api, scan_id)
            
            # Step 6: Rank by combined whale + smart money signals
            final_tokens = await self._rank_by_whale_smart_money_signals(processed_tokens)
            
            execution_time = time.time() - execution_start_time
            self.logger.info(f"✅ {self.name} completed in {execution_time:.2f}s - {len(final_tokens)} high-conviction tokens")
            
            self.structured_logger.info({
                "event": "smart_money_whale_strategy_complete",
                "strategy": self.name,
                "scan_id": scan_id,
                "tokens_found": len(final_tokens),
                "execution_time": execution_time,
                "timestamp": int(time.time())
            })
            
            return final_tokens
            
        except Exception as e:
            self.structured_logger.error({
                "event": "smart_money_whale_strategy_error",
                "strategy": self.name,
                "scan_id": scan_id,
                "error": str(e),
                "timestamp": int(time.time())
            })
            self.logger.error(f"Error executing {self.name}: {e}")
            return []
    
    async def _initialize_whale_smart_money_services(self, birdeye_api: BirdeyeAPI):
        """Initialize whale and smart money services."""
        try:
            # Initialize whale/shark tracker
            if self._whale_shark_tracker is None:
                from services.whale_shark_movement_tracker import WhaleSharkMovementTracker
                self._whale_shark_tracker = WhaleSharkMovementTracker(
                    birdeye_api=birdeye_api,
                    logger=self.logger
                )
                self.logger.info("🐋 Whale/Shark tracker initialized")
            
            # Initialize smart money detector
            if self._smart_money_detector is None:
                from services.smart_money_detector import SmartMoneyDetector
                self._smart_money_detector = SmartMoneyDetector(
                    whale_shark_tracker=self._whale_shark_tracker,
                    logger=self.logger
                )
                self.logger.info("🧠 Smart money detector initialized")
                
        except Exception as e:
            self.logger.error(f"Error initializing whale/smart money services: {e}")
            raise
    
    async def _get_initial_token_universe(self, birdeye_api: BirdeyeAPI) -> List[Dict[str, Any]]:
        """Get initial token universe using base strategy parameters."""
        try:
            # Use the base strategy's token discovery
            params = self.api_parameters.copy()
            sort_by = params.pop("sort_by", "volume_24h_usd")
            sort_type = params.pop("sort_type", "desc")
            limit = params.pop("limit", 100)
            
            # OPTIMIZATION: Reduce limit to 20 instead of 100 to minimize API calls
            # Focus on highest volume tokens where whales are most likely to be active
            limit = min(limit, 20)  # Hard cap at 20 tokens
            
            result = await birdeye_api.get_token_list(
                sort_by=sort_by,
                sort_type=sort_type,
                limit=limit,
                **params
            )
            
            if result and result.get("success") and "data" in result:
                tokens = result.get("data", {}).get("tokens", [])
                
                # OPTIMIZATION: Pre-filter tokens before expensive whale analysis
                # Only analyze tokens that are likely to have whale activity
                filtered_tokens = self._pre_filter_tokens_for_whale_activity(tokens)
                
                self.logger.info(f"🎯 Pre-filtered {len(tokens)} → {len(filtered_tokens)} tokens for whale analysis")
                
                # Filter out major tokens to focus on opportunities
                from services.early_token_detection import filter_major_tokens
                filtered_tokens = filter_major_tokens(filtered_tokens)
                
                return filtered_tokens
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting initial token universe: {e}")
            return []
    
    async def _filter_by_whale_activity(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter tokens by whale activity using whale/shark tracker."""
        whale_active_tokens = []
        
        self.logger.info(f"🐋 Analyzing whale activity for {len(tokens)} tokens")
        
        for token in tokens:
            try:
                token_address = token.get("address")
                if not token_address:
                    continue
                
                # Analyze whale/shark movements
                whale_analysis = await self._whale_shark_tracker.analyze_whale_shark_movements(
                    token_address, priority_level="normal"
                )
                
                # Check if token meets whale activity criteria
                if self._meets_whale_activity_criteria(whale_analysis, token):
                    # Add whale analysis to token
                    token["whale_analysis"] = whale_analysis
                    token["whale_activity_detected"] = True
                    whale_active_tokens.append(token)
                    
                    self.structured_logger.info({
                        "event": "whale_activity_detected",
                        "strategy": self.name,
                        "scan_id": scan_id,
                        "token": token_address,
                        "whale_count": len(whale_analysis.get("whales", [])),
                        "whale_volume": whale_analysis.get("whale_analysis", {}).get("total_volume", 0),
                        "timestamp": int(time.time())
                    })
                    
            except Exception as e:
                self.logger.warning(f"Error analyzing whale activity for {token.get('address', 'unknown')}: {e}")
                continue
        
        return whale_active_tokens
    
    async def _filter_by_smart_money_activity(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter tokens by smart money activity using smart money detector."""
        smart_money_tokens = []
        
        self.logger.info(f"🧠 Analyzing smart money activity for {len(tokens)} tokens")
        
        for token in tokens:
            try:
                token_address = token.get("address")
                if not token_address:
                    continue
                
                # Analyze smart money activity (reuses whale data - no additional API calls!)
                smart_money_analysis = await self._smart_money_detector.analyze_smart_money(
                    token_address, priority_level="normal"
                )
                
                # Check if token meets smart money criteria
                if self._meets_smart_money_criteria(smart_money_analysis, token):
                    # Add smart money analysis to token
                    token["smart_money_analysis"] = smart_money_analysis
                    token["smart_money_detected"] = True
                    smart_money_tokens.append(token)
                    
                    self.structured_logger.info({
                        "event": "smart_money_detected",
                        "strategy": self.name,
                        "scan_id": scan_id,
                        "token": token_address,
                        "skilled_traders": smart_money_analysis.get("skill_metrics", {}).get("skilled_count", 0),
                        "avg_skill_score": smart_money_analysis.get("skill_metrics", {}).get("average_skill_score", 0),
                        "timestamp": int(time.time())
                    })
                    
            except Exception as e:
                self.logger.warning(f"Error analyzing smart money for {token.get('address', 'unknown')}: {e}")
                continue
        
        return smart_money_tokens
    
    async def _apply_confluence_analysis(self, tokens: List[Dict[str, Any]], birdeye_api: BirdeyeAPI, scan_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Apply confluence analysis to find tokens with both whale and smart money activity."""
        confluence_tokens = []
        
        self.logger.info(f"🎯 Applying confluence analysis to {len(tokens)} tokens")
        
        for token in tokens:
            try:
                token_address = token.get("address")
                whale_analysis = token.get("whale_analysis", {})
                smart_money_analysis = token.get("smart_money_analysis", {})
                
                # Calculate confluence score
                confluence_score = self._calculate_confluence_score(whale_analysis, smart_money_analysis)
                token["confluence_score"] = confluence_score
                
                # Check if meets confluence criteria
                if confluence_score >= self.whale_smart_money_criteria["min_confluence_score"]:
                    token["high_confluence"] = True
                    
                    # Apply confluence bonus
                    confluence_bonus = confluence_score * self.whale_smart_money_criteria["confluence_bonus_multiplier"]
                    token["confluence_bonus"] = confluence_bonus
                    
                    confluence_tokens.append(token)
                    
                    self.structured_logger.info({
                        "event": "confluence_detected",
                        "strategy": self.name,
                        "scan_id": scan_id,
                        "token": token_address,
                        "confluence_score": confluence_score,
                        "confluence_bonus": confluence_bonus,
                        "timestamp": int(time.time())
                    })
                    
            except Exception as e:
                self.logger.warning(f"Error in confluence analysis for {token.get('address', 'unknown')}: {e}")
                continue
        
        return confluence_tokens
    
    async def _rank_by_whale_smart_money_signals(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank tokens by combined whale and smart money signals."""
        try:
            for token in tokens:
                # Calculate combined signal score
                combined_score = self._calculate_combined_whale_smart_money_score(token)
                token["combined_whale_smart_money_score"] = combined_score
                
                # Add strategy-specific analysis
                token["strategy_analysis"] = {
                    "strategy_type": "smart_money_whale",
                    "analysis_timestamp": int(time.time()),
                    "whale_signal_strength": self._get_whale_signal_strength(token),
                    "smart_money_signal_strength": self._get_smart_money_signal_strength(token),
                    "confluence_level": self._get_confluence_level(token),
                    "risk_assessment": self._assess_whale_smart_money_risk(token),
                    "conviction_level": self._get_conviction_level(token)
                }
            
            # Sort by combined score (highest first)
            tokens.sort(key=lambda x: x.get("combined_whale_smart_money_score", 0), reverse=True)
            
            # Log top performers
            for i, token in enumerate(tokens[:5]):
                self.logger.info(f"🏆 Top {i+1}: {token.get('symbol')} - Score: {token.get('combined_whale_smart_money_score', 0):.2f}")
            
            return tokens
            
        except Exception as e:
            self.logger.error(f"Error ranking tokens: {e}")
            return tokens
    
    def _meets_whale_activity_criteria(self, whale_analysis: Dict[str, Any], token: Dict[str, Any]) -> bool:
        """Check if token meets whale activity criteria."""
        try:
            whales = whale_analysis.get("whales", [])
            whale_count = len(whales)
            whale_volume = whale_analysis.get("whale_analysis", {}).get("total_volume", 0)
            confidence = whale_analysis.get("confidence", 0.5)
            
            # DEBUG: Log whale analysis details
            token_symbol = token.get("symbol", "Unknown")
            self.logger.debug(f"🐋 Whale analysis for {token_symbol}: whales={whale_count}, volume=${whale_volume:,.0f}, confidence={confidence:.2f}")
            
            # ULTRA RELAXED: Accept any token that has whale analysis data
            # This allows us to see what tokens are being analyzed
            if whale_analysis:
                self.logger.debug(f"✅ {token_symbol} passes ultra-relaxed whale criteria")
                return True
            
            # Fallback: original criteria (should never be reached with ultra-relaxed settings)
            if whale_count < self.whale_smart_money_criteria["min_whale_count"]:
                self.logger.debug(f"❌ {token_symbol} failed whale count: {whale_count} < {self.whale_smart_money_criteria['min_whale_count']}")
                return False
            
            if whale_volume < self.whale_smart_money_criteria["min_whale_volume"]:
                self.logger.debug(f"❌ {token_symbol} failed whale volume: ${whale_volume:,.0f} < ${self.whale_smart_money_criteria['min_whale_volume']:,.0f}")
                return False
            
            if confidence < self.whale_smart_money_criteria["whale_confidence_threshold"]:
                self.logger.debug(f"❌ {token_symbol} failed whale confidence: {confidence:.2f} < {self.whale_smart_money_criteria['whale_confidence_threshold']:.2f}")
                return False
            
            self.logger.debug(f"✅ {token_symbol} passes all whale criteria")
            return True
            
        except Exception as e:
            self.logger.debug(f"Error checking whale criteria: {e}")
            return False
    
    def _meets_smart_money_criteria(self, smart_money_analysis: Dict[str, Any], token: Dict[str, Any]) -> bool:
        """Check if token meets smart money criteria."""
        try:
            skill_metrics = smart_money_analysis.get("skill_metrics", {})
            skilled_count = skill_metrics.get("skilled_count", 0)
            avg_skill_score = skill_metrics.get("average_skill_score", 0.0)
            insights = smart_money_analysis.get("smart_money_insights", {})
            
            # DEBUG: Log smart money analysis details
            token_symbol = token.get("symbol", "Unknown")
            self.logger.debug(f"🧠 Smart money analysis for {token_symbol}: skilled_traders={skilled_count}, avg_skill={avg_skill_score:.2f}, insights={insights}")
            
            # ULTRA RELAXED: Accept any token that has smart money analysis data
            if smart_money_analysis:
                self.logger.debug(f"✅ {token_symbol} passes ultra-relaxed smart money criteria")
                return True
            
            # Fallback: original criteria (should never be reached with ultra-relaxed settings)
            if skilled_count < self.whale_smart_money_criteria["min_smart_traders"]:
                self.logger.debug(f"❌ {token_symbol} failed smart trader count: {skilled_count} < {self.whale_smart_money_criteria['min_smart_traders']}")
                return False
            
            if avg_skill_score < self.whale_smart_money_criteria["smart_money_skill_threshold"]:
                self.logger.debug(f"❌ {token_symbol} failed skill score: {avg_skill_score:.2f} < {self.whale_smart_money_criteria['smart_money_skill_threshold']:.2f}")
                return False
            
            if insights.get("skill_quality") == "low":
                self.logger.debug(f"❌ {token_symbol} failed skill quality check")
                return False
            
            self.logger.debug(f"✅ {token_symbol} passes all smart money criteria")
            return True
            
        except Exception as e:
            self.logger.debug(f"Error checking smart money criteria: {e}")
            return False
    
    def _calculate_confluence_score(self, whale_analysis: Dict[str, Any], smart_money_analysis: Dict[str, Any]) -> float:
        """Calculate confluence score between whale and smart money signals."""
        try:
            confluence_score = 0.0
            
            # Whale signal strength (0-0.5)
            whales = whale_analysis.get("whales", [])
            whale_volume = whale_analysis.get("whale_analysis", {}).get("total_volume", 0)
            whale_strength = min(0.5, (len(whales) / 10) * 0.3 + (whale_volume / 10_000_000) * 0.2)
            confluence_score += whale_strength
            
            # Smart money signal strength (0-0.5)
            skill_metrics = smart_money_analysis.get("skill_metrics", {})
            skilled_count = skill_metrics.get("skilled_count", 0)
            avg_skill_score = skill_metrics.get("average_skill_score", 0.0)
            smart_money_strength = min(0.5, (skilled_count / 10) * 0.25 + avg_skill_score * 0.25)
            confluence_score += smart_money_strength
            
            return min(1.0, confluence_score)
            
        except Exception as e:
            self.logger.debug(f"Error calculating confluence score: {e}")
            return 0.0
    
    def _calculate_combined_whale_smart_money_score(self, token: Dict[str, Any]) -> float:
        """Calculate combined whale and smart money score."""
        try:
            base_score = token.get("score", 50.0)
            
            # Whale contribution (40% weight)
            whale_score = self._get_whale_score(token) * 0.4
            
            # Smart money contribution (40% weight)
            smart_money_score = self._get_smart_money_score(token) * 0.4
            
            # Confluence bonus (20% weight)
            confluence_score = token.get("confluence_score", 0.0) * 0.2
            
            # Apply confluence bonus multiplier
            confluence_bonus = token.get("confluence_bonus", 1.0)
            
            combined_score = (base_score + whale_score + smart_money_score + confluence_score) * confluence_bonus
            
            return min(100.0, combined_score)
            
        except Exception as e:
            self.logger.debug(f"Error calculating combined score: {e}")
            return 0.0
    
    def _get_whale_score(self, token: Dict[str, Any]) -> float:
        """Calculate whale activity score."""
        whale_analysis = token.get("whale_analysis", {})
        whales = whale_analysis.get("whales", [])
        whale_volume = whale_analysis.get("whale_analysis", {}).get("total_volume", 0)
        
        # Score based on whale count and volume
        count_score = min(25.0, len(whales) * 2.5)  # Up to 25 points for whale count
        volume_score = min(25.0, whale_volume / 1_000_000 * 5)  # Up to 25 points for volume
        
        return count_score + volume_score
    
    def _get_smart_money_score(self, token: Dict[str, Any]) -> float:
        """Calculate smart money activity score."""
        smart_money_analysis = token.get("smart_money_analysis", {})
        skill_metrics = smart_money_analysis.get("skill_metrics", {})
        
        skilled_count = skill_metrics.get("skilled_count", 0)
        avg_skill_score = skill_metrics.get("average_skill_score", 0.0)
        
        # Score based on skilled trader count and quality
        count_score = min(25.0, skilled_count * 2.5)  # Up to 25 points for skilled count
        quality_score = avg_skill_score * 25  # Up to 25 points for skill quality
        
        return count_score + quality_score
    
    def _get_whale_signal_strength(self, token: Dict[str, Any]) -> str:
        """Get whale signal strength classification."""
        whale_score = self._get_whale_score(token)
        
        if whale_score >= 40:
            return "very_strong"
        elif whale_score >= 30:
            return "strong"
        elif whale_score >= 20:
            return "moderate"
        else:
            return "weak"
    
    def _get_smart_money_signal_strength(self, token: Dict[str, Any]) -> str:
        """Get smart money signal strength classification."""
        smart_money_score = self._get_smart_money_score(token)
        
        if smart_money_score >= 40:
            return "very_strong"
        elif smart_money_score >= 30:
            return "strong"
        elif smart_money_score >= 20:
            return "moderate"
        else:
            return "weak"
    
    def _get_confluence_level(self, token: Dict[str, Any]) -> str:
        """Get confluence level classification."""
        confluence_score = token.get("confluence_score", 0.0)
        
        if confluence_score >= 0.9:
            return "exceptional"
        elif confluence_score >= 0.8:
            return "high"
        elif confluence_score >= 0.6:
            return "moderate"
        else:
            return "low"
    
    def _assess_whale_smart_money_risk(self, token: Dict[str, Any]) -> str:
        """Assess risk level for whale/smart money token."""
        # Lower risk for tokens with both whale and smart money activity
        confluence_score = token.get("confluence_score", 0.0)
        whale_count = len(token.get("whale_analysis", {}).get("whales", []))
        
        if confluence_score >= 0.8 and whale_count >= 3:
            return "low"
        elif confluence_score >= 0.6 and whale_count >= 2:
            return "moderate"
        else:
            return "high"
    
    def _get_conviction_level(self, token: Dict[str, Any]) -> str:
        """Get conviction level for the token."""
        combined_score = token.get("combined_whale_smart_money_score", 0.0)
        
        if combined_score >= 80:
            return "very_high"
        elif combined_score >= 70:
            return "high"
        elif combined_score >= 60:
            return "moderate"
        else:
            return "low"
    
    def _pre_filter_tokens_for_whale_activity(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Pre-filter tokens to identify those likely to have whale activity.
        This uses only token data already available (no additional API calls).
        """
        whale_candidate_tokens = []
        
        for token in tokens:
            try:
                # Whale activity indicators from token data
                volume_24h = token.get('volume24h', 0) or token.get('volume_24h_usd', 0)
                liquidity = token.get('liquidity', 0) or token.get('liquidityUsd', 0)
                market_cap = token.get('marketCap', 0) or token.get('mc', 0)
                holder_count = token.get('holder', 0) or token.get('holderCount', 0)
                
                # Pre-filtering criteria for whale activity
                whale_indicators = {
                    # High volume suggests active trading (whales need liquidity)
                    "high_volume": volume_24h >= 1000000,  # $1M+ daily volume
                    
                    # Sufficient liquidity for whale-sized trades
                    "adequate_liquidity": liquidity >= 500000,  # $500k+ liquidity
                    
                    # Established token with holder base (whales avoid very new tokens)
                    "established_holders": holder_count >= 1000,
                    
                    # Market cap range where whales operate (not too small, not too large)
                    "whale_market_cap": 10000000 <= market_cap <= 1000000000,  # $10M - $1B
                }
                
                # Score based on whale indicators
                whale_score = sum(1 for indicator in whale_indicators.values() if indicator)
                
                # Require at least 2 out of 4 whale indicators
                if whale_score >= 2:
                    token['whale_pre_filter_score'] = whale_score
                    token['whale_indicators'] = whale_indicators
                    whale_candidate_tokens.append(token)
                    
                    self.logger.debug(f"   ✅ {token.get('symbol', 'UNKNOWN')}: whale score {whale_score}/4")
                else:
                    self.logger.debug(f"   ❌ {token.get('symbol', 'UNKNOWN')}: whale score {whale_score}/4 (filtered out)")
                    
            except Exception as e:
                self.logger.debug(f"Error pre-filtering token {token.get('symbol', 'UNKNOWN')}: {e}")
                continue
        
        return whale_candidate_tokens