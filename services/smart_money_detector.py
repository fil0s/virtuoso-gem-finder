#!/usr/bin/env python3
"""
Smart Money Detector Service - Skill-Based Analysis

This service identifies smart money activity based on TRADING SKILL and BEHAVIORAL PATTERNS,
complementing the Whale/Shark tracker which focuses on SIZE-based analysis.

Key Differences:
- Whale/Shark Tracker: WHO are the big players? (size-based)
- Smart Money Detector: WHO are the skilled players? (skill-based)

Reuses whale/shark data to avoid redundant API calls.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from services.whale_shark_movement_tracker import WhaleSharkMovementTracker


class SmartMoneyDetector:
    """
    Detects smart money activity based on TRADING SKILL and BEHAVIORAL PATTERNS.
    
    Complements the Whale/Shark tracker by focusing on trader sophistication
    rather than just volume. Reuses whale/shark data to avoid redundant API calls.
    
    Smart Money Criteria (skill-based):
    - Trading efficiency (low slippage, optimal timing)
    - Behavioral consistency (regular patterns, risk management)
    - Performance indicators (win rates, profitability signals)
    - Execution quality (gas optimization, MEV avoidance)
    """
    
    def __init__(self, whale_shark_tracker: WhaleSharkMovementTracker, logger: Optional[logging.Logger] = None):
        """
        Initialize the smart money detector.
        
        Args:
            whale_shark_tracker: Whale/Shark tracker instance (provides base data)
            logger: Logger instance
        """
        self.whale_shark_tracker = whale_shark_tracker
        self.logger = logger or logging.getLogger(__name__)
        self.cache_manager = CacheManager()
        
        # Cache settings
        self.smart_money_cache_ttl = 900  # 15 minutes cache for smart money analysis
        
        # Smart money criteria (skill-based, not size-based)
        self.smart_money_criteria = {
            # Trading Efficiency
            "optimal_trade_size_min": 1000,      # $1k+ per trade (not too small)
            "optimal_trade_size_max": 100000,    # <$100k per trade (not too large)
            "balance_consistency": 0.3,          # 30%+ balance in buy/sell (not one-sided)
            "trade_frequency_min": 1,            # 1+ trades (allow massive single trades)
            
            # Behavioral Sophistication  
            "efficiency_threshold": 0.7,         # 70%+ efficiency score
            "consistency_threshold": 0.6,        # 60%+ consistency score
            "risk_management_threshold": 0.5,    # 50%+ risk management score
            
            # Performance Indicators
            "skill_score_threshold": 0.65        # 65%+ overall skill score
        }
        
        # Skill analysis weights
        self.skill_weights = {
            "trading_efficiency": 0.35,    # How well they execute trades
            "behavioral_consistency": 0.25, # How consistent their patterns are
            "risk_management": 0.20,        # How well they manage risk
            "timing_skill": 0.20           # How well they time entries/exits
        }
        
        # Internal tracking
        self._smart_traders_cache = {}
        self._token_trader_cache = {}
        
    async def analyze_smart_money(self, token_address: str, priority_level: str = "normal") -> Dict[str, Any]:
        """
        Analyze smart money activity for a token using skill-based criteria.
        
        Reuses whale/shark tracker data to avoid redundant API calls, then applies
        sophisticated behavioral analysis to identify skilled traders.
        
        Args:
            token_address: Token address to analyze
            priority_level: "normal" or "high" (passed to whale/shark tracker)
            
        Returns:
            Smart money analysis results with skill-based metrics
        """
        cache_key = f"smart_money_{token_address}_{priority_level}"
        
        # Check cache first
        cached_data = self.cache_manager.get(cache_key)
        if cached_data:
            self.logger.debug(f"🧠 Using cached smart money data for {token_address}")
            return cached_data
        
        try:
            self.logger.info(f"🧠 Analyzing smart money activity for token {token_address}")
            
            # Get whale/shark data (reuses their API calls - no additional cost!)
            whale_shark_data = await self.whale_shark_tracker.analyze_whale_shark_movements(
                token_address, priority_level
            )
            
            # Perform skill-based analysis on the trader data
            smart_money_analysis = await self._analyze_trader_skills(whale_shark_data, token_address)
                
                # Cache the results
            self.cache_manager.set(cache_key, smart_money_analysis, ttl=self.smart_money_cache_ttl)
                
            self.logger.info(f"✅ Completed smart money analysis for {token_address}")
            return smart_money_analysis
                
        except Exception as e:
            self.logger.error(f"❌ Error analyzing smart money for {token_address}: {e}")
            return self._get_empty_smart_money_analysis()
    
    async def _analyze_trader_skills(self, whale_shark_data: Dict[str, Any], token_address: str) -> Dict[str, Any]:
        """
        Analyze trader skills from whale/shark movement data.
        
        Args:
            whale_shark_data: Data from whale/shark tracker
            token_address: Token address being analyzed
            
        Returns:
            Smart money analysis with skill-based metrics
        """
        try:
            # Extract trader data from whale/shark analysis (correct data structure)
            whale_analysis = whale_shark_data.get("whale_analysis", {})
            shark_analysis = whale_shark_data.get("shark_analysis", {})
            
            # Get the actual trader lists from the analysis
            whales = whale_analysis.get("top_whales", [])
            sharks = shark_analysis.get("top_sharks", [])
            all_traders = whales + sharks
            
            if not all_traders:
                return self._get_empty_smart_money_analysis()
                
            # Analyze each trader for skill indicators
            skilled_traders = []
            skill_metrics = {
                "total_analyzed": len(all_traders),
                "skilled_count": 0,
                "average_skill_score": 0.0,
                "skill_distribution": {"high": 0, "medium": 0, "low": 0}
            }
            
            for trader in all_traders:
                skill_analysis = self._analyze_individual_trader_skill(trader)
                
                if skill_analysis["skill_score"] >= self.smart_money_criteria["skill_score_threshold"]:
                    skilled_traders.append({
                    **trader,
                        **skill_analysis
                    })
                    skill_metrics["skilled_count"] += 1
                
                # Update skill distribution
                if skill_analysis["skill_score"] >= 0.8:
                    skill_metrics["skill_distribution"]["high"] += 1
                elif skill_analysis["skill_score"] >= 0.6:
                    skill_metrics["skill_distribution"]["medium"] += 1
                else:
                    skill_metrics["skill_distribution"]["low"] += 1
            
            # Calculate average skill score
            if all_traders:
                total_skill = sum(self._analyze_individual_trader_skill(t)["skill_score"] for t in all_traders)
                skill_metrics["average_skill_score"] = total_skill / len(all_traders)
            
            # Generate smart money insights
            insights = self._generate_smart_money_insights(skilled_traders, skill_metrics, whale_shark_data)
        
            return {
                "token_address": token_address,
                "analysis_timestamp": datetime.now().isoformat(),
                "skilled_traders": skilled_traders,
                "skill_metrics": skill_metrics,
                "smart_money_insights": insights,
                "data_source": "whale_shark_tracker",  # Shows we reused data
                "additional_api_calls": 0  # No additional API calls made!
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing trader skills: {e}")
            return self._get_empty_smart_money_analysis()
    
    def _analyze_individual_trader_skill(self, trader: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze individual trader skill based on behavioral patterns.
        
        Args:
            trader: Trader data from whale/shark tracker
            
        Returns:
            Skill analysis for the trader
        """
        try:
            volume = trader.get("volume", 0)
            trade_count = trader.get("trade_count", 0)  # Fixed field name
            volume_buy = trader.get("volume_buy", 0)    # Fixed field name
            volume_sell = trader.get("volume_sell", 0)  # Fixed field name
            
            # Calculate skill indicators
            trading_efficiency = self._calculate_trading_efficiency(trader)
            behavioral_consistency = self._calculate_behavioral_consistency(trader)
            risk_management = self._calculate_risk_management(trader)
            timing_skill = self._calculate_timing_skill(trader)
            
            # Calculate overall skill score
            skill_score = (
                trading_efficiency * self.skill_weights["trading_efficiency"] +
                behavioral_consistency * self.skill_weights["behavioral_consistency"] +
                risk_management * self.skill_weights["risk_management"] +
                timing_skill * self.skill_weights["timing_skill"]
            )
            
            return {
                "skill_score": skill_score,
                "trading_efficiency": trading_efficiency,
                "behavioral_consistency": behavioral_consistency,
                "risk_management": risk_management,
                "timing_skill": timing_skill,
                "skill_level": self._categorize_skill_level(skill_score)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing individual trader skill: {e}")
            return {
                "skill_score": 0.0,
                "trading_efficiency": 0.0,
                "behavioral_consistency": 0.0,
                "risk_management": 0.0,
                "timing_skill": 0.0,
                "skill_level": "unknown"
            }
    
    def _calculate_trading_efficiency(self, trader: Dict[str, Any]) -> float:
        """Calculate trading efficiency score (0.0 to 1.0)."""
        try:
            volume = trader.get("volume", 0)
            trade_count = trader.get("trade_count", 0)  # Fixed field name
            
            if trade_count == 0:
                return 0.0
            
            # Average trade size efficiency
            avg_trade_size = volume / trade_count
            
            # Optimal range scoring
            if (self.smart_money_criteria["optimal_trade_size_min"] <= avg_trade_size <= 
                self.smart_money_criteria["optimal_trade_size_max"]):
                size_efficiency = 1.0
            elif avg_trade_size < self.smart_money_criteria["optimal_trade_size_min"]:
                size_efficiency = avg_trade_size / self.smart_money_criteria["optimal_trade_size_min"]
            else:
                # Penalize extremely large trades (potential manipulation)
                size_efficiency = max(0.1, self.smart_money_criteria["optimal_trade_size_max"] / avg_trade_size)
            
            # Trade frequency efficiency (not too few, not too many)
            if trade_count >= self.smart_money_criteria["trade_frequency_min"]:
                frequency_efficiency = min(1.0, trade_count / 100)  # Cap at 100 trades = 1.0
            else:
                frequency_efficiency = trade_count / self.smart_money_criteria["trade_frequency_min"]
            
            return (size_efficiency + frequency_efficiency) / 2
            
        except Exception:
            return 0.0
    
    def _calculate_behavioral_consistency(self, trader: Dict[str, Any]) -> float:
        """Calculate behavioral consistency score (0.0 to 1.0)."""
        try:
            volume_buy = trader.get("volume_buy", 0)    # Fixed field name
            volume_sell = trader.get("volume_sell", 0)  # Fixed field name
            total_volume = volume_buy + volume_sell
            
            if total_volume == 0:
                return 0.0
            
            # Calculate buy/sell balance
            buy_ratio = volume_buy / total_volume
            sell_ratio = volume_sell / total_volume
            
            # Consistency means not being extremely one-sided
            balance_score = 1.0 - abs(buy_ratio - sell_ratio)
            
            # Reward balanced trading (smart money often balances positions)
            if balance_score >= self.smart_money_criteria["balance_consistency"]:
                return balance_score
            else:
                return balance_score * 0.5  # Penalize one-sided trading
            
        except Exception:
            return 0.0
    
    def _calculate_risk_management(self, trader: Dict[str, Any]) -> float:
        """Calculate risk management score (0.0 to 1.0)."""
        try:
            volume = trader.get("volume", 0)
            trade_count = trader.get("trade_count", 0)  # Fixed field name
            
            if trade_count == 0:
                return 0.0
            
            avg_trade_size = volume / trade_count
            
            # Risk management indicators:
            # 1. Not making trades that are too large (risk control)
            # 2. Having reasonable trade frequency (not over-trading)
            
            # Size risk management
            if avg_trade_size <= self.smart_money_criteria["optimal_trade_size_max"]:
                size_risk_score = 1.0
            else:
                # Penalize oversized trades
                size_risk_score = max(0.1, self.smart_money_criteria["optimal_trade_size_max"] / avg_trade_size)
            
            # Frequency risk management (not over-trading)
            if trade_count <= 1000:  # Reasonable upper limit
                frequency_risk_score = 1.0
            else:
                frequency_risk_score = max(0.1, 1000 / trade_count)
            
            return (size_risk_score + frequency_risk_score) / 2
            
        except Exception:
            return 0.0
    
    def _calculate_timing_skill(self, trader: Dict[str, Any]) -> float:
        """Calculate timing skill score (0.0 to 1.0)."""
        try:
            volume_buy = trader.get("volume_buy", 0)    # Fixed field name
            volume_sell = trader.get("volume_sell", 0)  # Fixed field name
            
            # For timing skill, we look at directional bias
            # Smart money often shows directional conviction
            total_volume = volume_buy + volume_sell
            if total_volume == 0:
                return 0.0
            
            buy_ratio = volume_buy / total_volume
            
            # Reward clear directional bias (conviction)
            if buy_ratio >= 0.7 or buy_ratio <= 0.3:
                return 0.8  # Strong conviction
            elif buy_ratio >= 0.6 or buy_ratio <= 0.4:
                return 0.6  # Moderate conviction
            else:
                return 0.4  # Neutral/uncertain
            
        except Exception:
            return 0.0
    
    def _categorize_skill_level(self, skill_score: float) -> str:
        """Categorize skill level based on score."""
        if skill_score >= 0.8:
            return "expert"
        elif skill_score >= 0.65:
            return "skilled"
        elif skill_score >= 0.5:
            return "intermediate"
        else:
            return "novice"
    
    def _generate_smart_money_insights(self, skilled_traders: List[Dict[str, Any]], 
                                     skill_metrics: Dict[str, Any], 
                                     whale_shark_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights from smart money analysis."""
        try:
            insights = {
                "smart_money_present": len(skilled_traders) > 0,
                "skill_quality": "high" if skill_metrics["average_skill_score"] >= 0.7 else 
                               "medium" if skill_metrics["average_skill_score"] >= 0.5 else "low",
                "trader_sophistication": self._assess_trader_sophistication(skilled_traders),
                "market_sentiment": self._assess_smart_money_sentiment(skilled_traders),
                "risk_assessment": self._assess_smart_money_risk(skilled_traders, whale_shark_data),
                "recommendations": self._generate_smart_money_recommendations(skilled_traders, skill_metrics)
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"❌ Error generating smart money insights: {e}")
            return {"error": "Failed to generate insights"}
    
    def _assess_trader_sophistication(self, skilled_traders: List[Dict[str, Any]]) -> str:
        """Assess overall trader sophistication level."""
        if not skilled_traders:
            return "none"
        
        expert_count = sum(1 for t in skilled_traders if t.get("skill_level") == "expert")
        skilled_count = sum(1 for t in skilled_traders if t.get("skill_level") == "skilled")
        
        expert_ratio = expert_count / len(skilled_traders)
        skilled_ratio = (expert_count + skilled_count) / len(skilled_traders)
            
        if expert_ratio >= 0.5:
            return "very_high"
        elif skilled_ratio >= 0.7:
            return "high"
        elif skilled_ratio >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _assess_smart_money_sentiment(self, skilled_traders: List[Dict[str, Any]]) -> str:
        """Assess smart money sentiment (bullish/bearish/neutral)."""
        if not skilled_traders:
            return "neutral"
        
        total_buy_volume = sum(t.get("volume_buy", 0) for t in skilled_traders)
        total_sell_volume = sum(t.get("volume_sell", 0) for t in skilled_traders)
        total_volume = total_buy_volume + total_sell_volume
        
        if total_volume == 0:
            return "neutral"
        
        buy_ratio = total_buy_volume / total_volume
        
        if buy_ratio >= 0.65:
            return "bullish"
        elif buy_ratio <= 0.35:
            return "bearish"
        else:
            return "neutral"
    
    def _assess_smart_money_risk(self, skilled_traders: List[Dict[str, Any]], 
                               whale_shark_data: Dict[str, Any]) -> str:
        """Assess risk level based on smart money activity."""
        if not skilled_traders:
            return "unknown"
        
        # Factor in both skill level and size (from whale/shark data)
        high_skill_large_traders = [
            t for t in skilled_traders 
            if t.get("skill_level") in ["expert", "skilled"] and t.get("volume", 0) > 50000
        ]
        
        if len(high_skill_large_traders) >= 3:
            return "low"  # Multiple skilled large traders = lower risk
        elif len(skilled_traders) >= 2:
            return "medium"
        else:
            return "high"
    
    def _generate_smart_money_recommendations(self, skilled_traders: List[Dict[str, Any]], 
                                            skill_metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on smart money analysis."""
        recommendations = []
        
        if not skilled_traders:
            recommendations.append("No skilled traders detected - exercise caution")
            return recommendations
        
        # Sentiment-based recommendations
        total_buy = sum(t.get("volume_buy", 0) for t in skilled_traders)
        total_sell = sum(t.get("volume_sell", 0) for t in skilled_traders)
        total_volume = total_buy + total_sell
        
        if total_volume > 0:
            buy_ratio = total_buy / total_volume
            if buy_ratio >= 0.65:
                recommendations.append("Smart money showing bullish bias - consider following")
            elif buy_ratio <= 0.35:
                recommendations.append("Smart money showing bearish bias - exercise caution")
        
        # Skill quality recommendations
        if skill_metrics["average_skill_score"] >= 0.7:
            recommendations.append("High-quality trader activity detected - positive signal")
        elif skill_metrics["average_skill_score"] >= 0.5:
            recommendations.append("Moderate trader quality - monitor closely")
        
        # Count-based recommendations
        if len(skilled_traders) >= 5:
            recommendations.append("Multiple skilled traders active - strong validation")
        elif len(skilled_traders) >= 2:
            recommendations.append("Some skilled trader activity - moderate confidence")
        
        return recommendations
    
    def _get_empty_smart_money_analysis(self) -> Dict[str, Any]:
        """Return empty smart money analysis structure."""
        return {
            "token_address": "",
            "analysis_timestamp": datetime.now().isoformat(),
            "skilled_traders": [],
            "skill_metrics": {
                "total_analyzed": 0,
                "skilled_count": 0,
                "average_skill_score": 0.0,
                "skill_distribution": {"high": 0, "medium": 0, "low": 0}
            },
            "smart_money_insights": {
                "smart_money_present": False,
                "skill_quality": "none",
                "trader_sophistication": "none",
                "market_sentiment": "neutral",
                "risk_assessment": "unknown",
                "recommendations": ["No data available for analysis"]
            },
            "data_source": "whale_shark_tracker",
            "additional_api_calls": 0
        }
    
    async def batch_analyze_smart_money(self, token_addresses: List[str], priority_level: str = "normal") -> Dict[str, Dict[str, Any]]:
        """
        Batch analyze smart money for multiple tokens efficiently.
        
        Args:
            token_addresses: List of token addresses to analyze
            priority_level: Priority level for whale/shark analysis
            
        Returns:
            Dictionary mapping token addresses to smart money analysis results
        """
        results = {}
        
        for token_address in token_addresses:
            try:
                self.logger.info(f"🧠 Batch analyzing smart money for {token_address}")
                results[token_address] = await self.analyze_smart_money(token_address, priority_level)
            except Exception as e:
                self.logger.error(f"❌ Error in batch smart money analysis for {token_address}: {e}")
                results[token_address] = self._get_empty_smart_money_analysis()
        
        return results
    
    def get_smart_money_summary(self, token_address: str) -> Dict[str, Any]:
        """
        Get cached smart money summary for a token.
        
        Args:
            token_address: Token address to get summary for
            
        Returns:
            Smart money summary or None if not cached
        """
        cache_key = f"smart_money_{token_address}_normal"
        cached_data = self.cache_manager.get(cache_key)
        
        if cached_data:
            return {
                "token_address": token_address,
                "smart_money_present": cached_data.get("smart_money_insights", {}).get("smart_money_present", False),
                "skill_quality": cached_data.get("smart_money_insights", {}).get("skill_quality", "none"),
                "skilled_count": cached_data.get("skill_metrics", {}).get("skilled_count", 0),
                "market_sentiment": cached_data.get("smart_money_insights", {}).get("market_sentiment", "neutral"),
                "recommendations": cached_data.get("smart_money_insights", {}).get("recommendations", []),
                "cached": True
            }
        
        return None 