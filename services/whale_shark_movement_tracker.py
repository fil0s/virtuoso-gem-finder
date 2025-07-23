#!/usr/bin/env python3
"""
Whale & Shark Movement Tracker

Focused analysis of large traders (whales) and smart money (sharks) with minimal API calls.
Tracks movement patterns, positioning, and market impact to understand what big money is doing.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from api.birdeye_connector import BirdeyeAPI
from core.cache_manager import CacheManager
from utils.structured_logger import get_structured_logger


# === WHALE ACTIVITY ANALYZER INTEGRATION ===

class WhaleActivityType(Enum):
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    ROTATION = "rotation"
    INSTITUTIONAL_FLOW = "institutional"
    SMART_MONEY_ENTRY = "smart_entry"
    COORDINATED_BUY = "coordinated_buy"
    STEALTH_ACCUMULATION = "stealth"

@dataclass
class WhaleSignal:
    type: WhaleActivityType
    confidence: float  # 0.0 to 1.0
    score_impact: int  # -20 to +25 points
    whale_count: int
    total_value: float
    timeframe: str
    details: str
    whale_addresses: List[str]


class WhaleSharkMovementTracker:
    """
    Efficient whale and shark movement tracker focused on large trader behavior analysis.
    
    Classifications:
    - Whales: >$100k volume (institutional/major players)
    - Sharks: $10k-$100k volume (smart money/serious traders)
    - Fish: <$10k volume (retail/noise - ignored)
    """
    
    def __init__(self, birdeye_api: BirdeyeAPI, logger: Optional[logging.Logger] = None, whale_discovery_service=None):
        """
        Initialize the whale/shark movement tracker.
        
        Args:
            birdeye_api: Birdeye API instance
            logger: Logger instance
            whale_discovery_service: Optional whale discovery service for dynamic whale database
        """
        self.birdeye_api = birdeye_api
        self.logger = logger or logging.getLogger(__name__)
        self.cache_manager = CacheManager()
        self.structured_logger = get_structured_logger('WhaleSharkMovementTracker')
        
        # Whale discovery service for dynamic whale database updates
        self.whale_discovery_service = whale_discovery_service
        
        # Enhanced discovery service (Phase 2)
        self.enhanced_discovery_service = None
        try:
            from services.whale_discovery_service import WhaleDiscoveryService
            self.enhanced_discovery_service = WhaleDiscoveryService(
                birdeye_api=birdeye_api,
                logger=logger
            )
            self.logger.info("🔍 Enhanced whale discovery service initialized")
        except Exception as e:
            self.logger.debug(f"Enhanced discovery service not available: {e}")
        
        # Known whale database (from WhaleActivityAnalyzer)
        self.whale_database = {
            # Tier 1: Mega Whales (>$50M typical positions)
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": {
                "tier": 1, "name": "Alameda Research", "avg_position": 100_000_000,
                "success_rate": 0.75, "known_for": "early_entry"
            },
            "HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH": {
                "tier": 1, "name": "Jump Trading", "avg_position": 80_000_000,
                "success_rate": 0.85, "known_for": "market_making"
            },
            "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1": {
                "tier": 1, "name": "Wintermute", "avg_position": 60_000_000,
                "success_rate": 0.80, "known_for": "arbitrage"
            },
            # Tier 2: Large Whales ($10M-$50M positions)
            "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh": {
                "tier": 2, "name": "Individual Whale 1", "avg_position": 25_000_000,
                "success_rate": 0.70, "known_for": "momentum_trading"
            },
            "CuieVDEDtLo7FypA9SbLM9saXFdb1dsshEkyErMqkRQq": {
                "tier": 2, "name": "Individual Whale 2", "avg_position": 20_000_000,
                "success_rate": 0.75, "known_for": "early_adoption"
            },
            # Tier 3: Medium Whales ($1M-$10M positions)
            "8UJgxaiQx5nTrdDgph5FiahMmzduuLTLf5WmsPegYA6W": {
                "tier": 3, "name": "Smart Money 1", "avg_position": 5_000_000,
                "success_rate": 0.65, "known_for": "swing_trading"
            },
            "3NC2UjdvoyLFaQGJjSp3JkgeJZkM1VaE1eNCKZP2XGJS": {
                "tier": 3, "name": "Smart Money 2", "avg_position": 3_000_000,
                "success_rate": 0.68, "known_for": "technical_analysis"
            }
        }
        
        # Load discovered whales if discovery service available
        self._load_discovered_whales()
        
        # Cache settings - focused on efficiency
        self.movement_cache_ttl = 900  # 15 minutes for movement data
        
        # Whale/Shark classification thresholds (optimized for real market data)
        self.classification_thresholds = {
            "whale_min_volume": 100000,      # $100k+ = Whale
            "shark_min_volume": 10000,       # $10k-$100k = Shark
            "fish_max_volume": 10000,        # <$10k = Fish (ignored)
            "min_trades": 1,                 # Minimum 1 trade (allow massive single trades)
            "whale_min_avg_trade": 1000,     # Whales: $1k+ average trade size (reduced from $5k)
            "shark_min_avg_trade": 500,      # Sharks: $500+ average trade size
        }
        
        # Movement analysis settings
        self.movement_analysis = {
            "buy_sell_threshold": 0.6,       # 60%+ in one direction = directional bias
            "accumulation_threshold": 0.7,   # 70%+ buying = accumulation
            "distribution_threshold": 0.3,   # 30%- buying = distribution
            "price_impact_threshold": 0.02,  # 2%+ price movement = significant impact
        }
        
        # API efficiency settings
        self.api_strategy = {
            "primary_timeframe": "24h",      # Main analysis timeframe
            "secondary_timeframe": "6h",     # For high-priority tokens only
            "max_api_calls_per_token": 2,   # Hard limit: 1-2 calls max
            "high_priority_volume_threshold": 1000000  # $1M+ = high priority
        }
    
    async def analyze_whale_shark_movements(self, token_address: str, 
                                          priority_level: str = "normal") -> Dict[str, Any]:
        """
        Analyze whale and shark movements for a token with minimal API calls.
        
        Args:
            token_address: Token address to analyze
            priority_level: "normal" (1 API call) or "high" (2 API calls)
            
        Returns:
            Comprehensive whale/shark movement analysis
        """
        cache_key = f"whale_shark_movements_{token_address}_{priority_level}"
        
        # Check cache first
        cached_data = self.cache_manager.get(cache_key)
        if cached_data:
            self.logger.debug(f"🐋 Using cached whale/shark data for {token_address}")
            return cached_data
        
        try:
            self.logger.info(f"🐋 Analyzing whale/shark movements for {token_address} (priority: {priority_level})")
            
            # Efficient API strategy: 1-2 calls maximum
            if priority_level == "high":
                movement_analysis = await self._analyze_high_priority_movements(token_address)
            else:
                movement_analysis = await self._analyze_standard_movements(token_address)
            
            # Cache the results
            self.cache_manager.set(cache_key, movement_analysis, ttl=self.movement_cache_ttl)
            
            self.logger.info(f"✅ Whale/shark analysis completed for {token_address}")
            return movement_analysis
                
        except Exception as e:
            self.logger.error(f"❌ Error analyzing whale/shark movements for {token_address}: {e}")
            return self._get_empty_analysis()
    
    async def _analyze_standard_movements(self, token_address: str) -> Dict[str, Any]:
        """
        Standard analysis using 1 API call (24h volume sorting).
        
        Args:
            token_address: Token address to analyze
            
        Returns:
            Movement analysis based on 24h data
        """
        self.logger.debug(f"📊 Standard movement analysis for {token_address} (1 API call)")
        
        # Single API call: 24h volume sorting to get the biggest players
        traders_data = await self.birdeye_api.get_top_traders_optimized(
            token_address=token_address,
            time_frame="24h",
            sort_by="volume",
            sort_type="desc",
            limit=10
        )
        
        if not traders_data:
            self.logger.warning(f"⚠️ No trader data available for {token_address}")
            return self._get_empty_analysis()
        
        # Classify and analyze movements
        return await self._perform_whale_shark_analysis(
            traders_data, token_address, ["24h"], api_calls_used=1
        )
    
    async def _analyze_high_priority_movements(self, token_address: str) -> Dict[str, Any]:
        """
        High-priority analysis using 2 API calls (24h + 6h volume sorting).
        
        Args:
            token_address: Token address to analyze
            
        Returns:
            Enhanced movement analysis with recent trend data
        """
        self.logger.debug(f"🎯 High-priority movement analysis for {token_address} (2 API calls)")
        
        # API Call 1: 24h volume sorting (main analysis)
        traders_24h = await self.birdeye_api.get_top_traders_optimized(
            token_address=token_address,
            time_frame="24h",
            sort_by="volume",
            sort_type="desc",
            limit=10
        )
        
        # API Call 2: 6h volume sorting (recent trends)
        traders_6h = await self.birdeye_api.get_top_traders_optimized(
            token_address=token_address,
            time_frame="6h",
            sort_by="volume",
            sort_type="desc",
            limit=10
        )
        
        if not traders_24h and not traders_6h:
            self.logger.warning(f"⚠️ No trader data available for {token_address}")
            return self._get_empty_analysis()
        
        # Combine and analyze movements
        combined_analysis = await self._perform_enhanced_whale_shark_analysis(
            traders_24h or [], traders_6h or [], token_address, api_calls_used=2
        )
        
        return combined_analysis
    
    async def _perform_whale_shark_analysis(self, traders_data: List[Dict[str, Any]], 
                                          token_address: str, timeframes: List[str],
                                          api_calls_used: int) -> Dict[str, Any]:
        """
        Perform whale/shark classification and movement analysis.
        
        Args:
            traders_data: Raw trader data from API
            token_address: Token address being analyzed
            timeframes: List of timeframes analyzed
            api_calls_used: Number of API calls used
            
        Returns:
            Comprehensive whale/shark movement analysis
        """
        current_time = int(time.time())
        
        # Classify traders
        whales = []
        sharks = []
        total_whale_volume = 0
        total_shark_volume = 0
        whale_buy_volume = 0
        whale_sell_volume = 0
        shark_buy_volume = 0
        shark_sell_volume = 0
        
        for trader in traders_data:
            try:
                # Extract trader metrics
                volume = trader.get("volume", 0) or 0
                trade_count = trader.get("trade", 0) or 0
                volume_buy = trader.get("volumeBuy", 0) or 0
                volume_sell = trader.get("volumeSell", 0) or 0
                trader_address = trader.get("owner") or trader.get("address", "unknown")
                
                # Calculate derived metrics
                avg_trade_size = volume / max(trade_count, 1)
                buy_ratio = volume_buy / max(volume, 1)
                sell_ratio = volume_sell / max(volume, 1)
                
                # Classify trader
                trader_classification = self._classify_trader(volume, trade_count, avg_trade_size)
                
                if trader_classification == "whale":
                    whales.append({
                        "address": trader_address,
                        "volume": volume,
                        "trade_count": trade_count,
                        "avg_trade_size": avg_trade_size,
                        "volume_buy": volume_buy,
                        "volume_sell": volume_sell,
                        "buy_ratio": buy_ratio,
                        "sell_ratio": sell_ratio,
                        "directional_bias": self._get_directional_bias(buy_ratio),
                        "market_impact": self._estimate_market_impact(volume, avg_trade_size),
                        "classification": "whale"
                    })
                    total_whale_volume += volume
                    whale_buy_volume += volume_buy
                    whale_sell_volume += volume_sell
                    
                elif trader_classification == "shark":
                    sharks.append({
                        "address": trader_address,
                        "volume": volume,
                        "trade_count": trade_count,
                        "avg_trade_size": avg_trade_size,
                        "volume_buy": volume_buy,
                        "volume_sell": volume_sell,
                        "buy_ratio": buy_ratio,
                        "sell_ratio": sell_ratio,
                        "directional_bias": self._get_directional_bias(buy_ratio),
                        "market_impact": self._estimate_market_impact(volume, avg_trade_size),
                        "classification": "shark"
                    })
                    total_shark_volume += volume
                    shark_buy_volume += volume_buy
                    shark_sell_volume += volume_sell
                    
            except Exception as e:
                self.logger.error(f"Error analyzing trader: {e}")
                continue
        
        # Calculate aggregate movement patterns
        whale_movement = self._analyze_group_movement(whales, total_whale_volume, whale_buy_volume, whale_sell_volume)
        shark_movement = self._analyze_group_movement(sharks, total_shark_volume, shark_buy_volume, shark_sell_volume)
        
        # Generate market insights
        market_structure = self._analyze_market_structure(whales, sharks, total_whale_volume, total_shark_volume)
        
        return {
            "token_address": token_address,
            "analysis_timestamp": current_time,
            "api_efficiency": {
                "api_calls_used": api_calls_used,
                "max_calls_allowed": self.api_strategy["max_api_calls_per_token"],
                "efficiency_rating": "excellent" if api_calls_used <= 1 else "good",
                "timeframes_analyzed": timeframes
            },
            
            # Whale Analysis
            "whale_analysis": {
                "count": len(whales),
                "total_volume": total_whale_volume,
                "movement_pattern": whale_movement,
                "top_whales": sorted(whales, key=lambda x: x["volume"], reverse=True)[:3],
                "collective_bias": whale_movement.get("directional_bias", "neutral")
            },
            
            # Shark Analysis  
            "shark_analysis": {
                "count": len(sharks),
                "total_volume": total_shark_volume,
                "movement_pattern": shark_movement,
                "top_sharks": sorted(sharks, key=lambda x: x["volume"], reverse=True)[:3],
                "collective_bias": shark_movement.get("directional_bias", "neutral")
            },
            
            # Market Structure
            "market_structure": market_structure,
            
            # Trading Insights
            "trading_insights": self._generate_trading_insights(whale_movement, shark_movement, market_structure),
            
            # Validation
            "analysis_valid": len(whales) > 0 or len(sharks) > 0
        }
    
    async def _perform_enhanced_whale_shark_analysis(self, traders_24h: List[Dict], 
                                                   traders_6h: List[Dict],
                                                   token_address: str, 
                                                   api_calls_used: int) -> Dict[str, Any]:
        """
        Enhanced analysis combining 24h and 6h data for trend detection.
        
        Args:
            traders_24h: 24h trader data
            traders_6h: 6h trader data  
            token_address: Token address
            api_calls_used: Number of API calls used
            
        Returns:
            Enhanced whale/shark analysis with trend data
        """
        # Perform standard analysis on 24h data
        main_analysis = await self._perform_whale_shark_analysis(
            traders_24h, token_address, ["24h"], api_calls_used=1
        )
        
        # Analyze 6h trends
        recent_analysis = await self._perform_whale_shark_analysis(
            traders_6h, token_address, ["6h"], api_calls_used=1
        )
        
        # Compare trends
        trend_analysis = self._compare_whale_shark_trends(main_analysis, recent_analysis)
        
        # Enhance main analysis with trend data
        enhanced_analysis = main_analysis.copy()
        enhanced_analysis["api_efficiency"]["api_calls_used"] = api_calls_used
        enhanced_analysis["api_efficiency"]["timeframes_analyzed"] = ["24h", "6h"]
        enhanced_analysis["trend_analysis"] = trend_analysis
        enhanced_analysis["recent_activity"] = {
            "6h_whale_count": recent_analysis["whale_analysis"]["count"],
            "6h_shark_count": recent_analysis["shark_analysis"]["count"],
            "6h_whale_volume": recent_analysis["whale_analysis"]["total_volume"],
            "6h_shark_volume": recent_analysis["shark_analysis"]["total_volume"]
        }
        
        # Enhanced trading insights
        enhanced_analysis["trading_insights"] = self._generate_enhanced_trading_insights(
            main_analysis, recent_analysis, trend_analysis
        )
        
        return enhanced_analysis
    
    def _classify_trader(self, volume: float, trade_count: int, avg_trade_size: float) -> str:
        """
        Classify trader as whale, shark, or fish based on volume and behavior.
        
        Args:
            volume: Total trading volume
            trade_count: Number of trades
            avg_trade_size: Average trade size
            
        Returns:
            Classification: "whale", "shark", or "fish"
        """
        # Basic volume thresholds
        if volume >= self.classification_thresholds["whale_min_volume"]:
            # Additional whale criteria
            if (trade_count >= self.classification_thresholds["min_trades"] and
                avg_trade_size >= self.classification_thresholds["whale_min_avg_trade"]):
                return "whale"
        
        elif volume >= self.classification_thresholds["shark_min_volume"]:
            # Additional shark criteria
            if (trade_count >= self.classification_thresholds["min_trades"] and
                avg_trade_size >= self.classification_thresholds["shark_min_avg_trade"]):
                return "shark"
        
        return "fish"  # Below thresholds or doesn't meet criteria
    
    def _get_directional_bias(self, buy_ratio: float) -> str:
        """
        Determine directional bias based on buy/sell ratio.
        
        Args:
            buy_ratio: Ratio of buying volume to total volume
            
        Returns:
            Directional bias: "accumulating", "distributing", or "neutral"
        """
        if buy_ratio >= self.movement_analysis["accumulation_threshold"]:
            return "accumulating"
        elif buy_ratio <= self.movement_analysis["distribution_threshold"]:
            return "distributing"
        else:
            return "neutral"
    
    def _estimate_market_impact(self, volume: float, avg_trade_size: float) -> str:
        """
        Estimate market impact based on volume and trade size.
        
        Args:
            volume: Total trading volume
            avg_trade_size: Average trade size
            
        Returns:
            Market impact: "high", "medium", or "low"
        """
        if volume >= 500000 and avg_trade_size >= 20000:  # $500k+ volume, $20k+ avg trade
            return "high"
        elif volume >= 100000 and avg_trade_size >= 5000:  # $100k+ volume, $5k+ avg trade
            return "medium"
        else:
            return "low"
    
    def _analyze_group_movement(self, traders: List[Dict], total_volume: float, 
                               buy_volume: float, sell_volume: float) -> Dict[str, Any]:
        """
        Analyze collective movement patterns for a group of traders.
        
        Args:
            traders: List of classified traders
            total_volume: Total group volume
            buy_volume: Total group buy volume
            sell_volume: Total group sell volume
            
        Returns:
            Group movement analysis
        """
        if not traders or total_volume == 0:
            return {
                "directional_bias": "neutral",
                "buy_ratio": 0.0,
                "sell_ratio": 0.0,
                "activity_level": "none"
            }
        
        buy_ratio = buy_volume / total_volume
        sell_ratio = sell_volume / total_volume
        
        # Determine activity level
        if total_volume >= 1000000:  # $1M+
            activity_level = "very_high"
        elif total_volume >= 500000:  # $500k+
            activity_level = "high"
        elif total_volume >= 100000:  # $100k+
            activity_level = "medium"
        else:
            activity_level = "low"
        
        return {
            "directional_bias": self._get_directional_bias(buy_ratio),
            "buy_ratio": round(buy_ratio, 3),
            "sell_ratio": round(sell_ratio, 3),
            "activity_level": activity_level,
            "total_volume": total_volume,
            "avg_trader_volume": total_volume / len(traders),
            "dominant_action": "buying" if buy_ratio > 0.6 else "selling" if sell_ratio > 0.6 else "mixed"
        }
    
    def _analyze_market_structure(self, whales: List[Dict], sharks: List[Dict], 
                                 whale_volume: float, shark_volume: float) -> Dict[str, Any]:
        """
        Analyze overall market structure and dynamics.
        
        Args:
            whales: List of whale traders
            sharks: List of shark traders
            whale_volume: Total whale volume
            shark_volume: Total shark volume
            
        Returns:
            Market structure analysis
        """
        total_volume = whale_volume + shark_volume
        
        if total_volume == 0:
            return {
                "structure_type": "unknown",
                "whale_dominance": 0.0,
                "shark_presence": 0.0,
                "market_control": "retail"
            }
        
        whale_dominance = whale_volume / total_volume
        shark_presence = shark_volume / total_volume
        
        # Determine market structure
        if whale_dominance >= 0.7:
            structure_type = "whale_dominated"
            market_control = "institutional"
        elif whale_dominance >= 0.4:
            structure_type = "whale_influenced"
            market_control = "mixed_large"
        elif shark_presence >= 0.5:
            structure_type = "shark_active"
            market_control = "smart_money"
        else:
            structure_type = "fragmented"
            market_control = "retail"
        
        return {
            "structure_type": structure_type,
            "whale_dominance": round(whale_dominance, 3),
            "shark_presence": round(shark_presence, 3),
            "market_control": market_control,
            "total_large_trader_volume": total_volume,
            "whale_count": len(whales),
            "shark_count": len(sharks),
            "concentration_score": round(whale_dominance + (shark_presence * 0.5), 3)
        }
    
    def _generate_trading_insights(self, whale_movement: Dict, shark_movement: Dict, 
                                  market_structure: Dict) -> Dict[str, Any]:
        """
        Generate actionable trading insights based on whale/shark analysis.
        
        Args:
            whale_movement: Whale movement patterns
            shark_movement: Shark movement patterns
            market_structure: Market structure analysis
            
        Returns:
            Trading insights and recommendations
        """
        insights = {
            "signals": [],
            "risk_assessment": "medium",
            "confidence_level": "medium",
            "recommended_action": "monitor",
            "key_observations": []
        }
        
        # Whale signals
        whale_bias = whale_movement.get("directional_bias", "neutral")
        shark_bias = shark_movement.get("directional_bias", "neutral")
        
        if whale_bias == "accumulating" and shark_bias == "accumulating":
            insights["signals"].append("strong_bullish")
            insights["recommended_action"] = "consider_long"
            insights["confidence_level"] = "high"
            insights["key_observations"].append("Both whales and sharks are accumulating")
            
        elif whale_bias == "distributing" and shark_bias == "distributing":
            insights["signals"].append("strong_bearish")
            insights["recommended_action"] = "consider_short"
            insights["confidence_level"] = "high"
            insights["key_observations"].append("Both whales and sharks are distributing")
            
        elif whale_bias == "accumulating" and shark_bias == "neutral":
            insights["signals"].append("whale_accumulation")
            insights["recommended_action"] = "bullish_bias"
            insights["key_observations"].append("Whales accumulating while sharks neutral")
            
        elif whale_bias == "distributing" and shark_bias == "neutral":
            insights["signals"].append("whale_distribution")
            insights["recommended_action"] = "bearish_bias"
            insights["key_observations"].append("Whales distributing while sharks neutral")
            
        elif whale_bias != shark_bias and whale_bias != "neutral" and shark_bias != "neutral":
            insights["signals"].append("divergence")
            insights["recommended_action"] = "caution"
            insights["risk_assessment"] = "high"
            insights["key_observations"].append("Whales and sharks moving in opposite directions")
        
        # Market structure insights
        structure = market_structure.get("structure_type", "unknown")
        if structure == "whale_dominated":
            insights["key_observations"].append("Market dominated by institutional players")
            insights["risk_assessment"] = "low" if whale_bias == "accumulating" else "high"
        elif structure == "shark_active":
            insights["key_observations"].append("Smart money very active")
            insights["confidence_level"] = "high"
        
        return insights
    
    def _compare_whale_shark_trends(self, main_analysis: Dict, recent_analysis: Dict) -> Dict[str, Any]:
        """
        Compare 24h vs 6h trends to identify momentum changes.
        
        Args:
            main_analysis: 24h analysis results
            recent_analysis: 6h analysis results
            
        Returns:
            Trend comparison analysis
        """
        main_whale_bias = main_analysis["whale_analysis"]["collective_bias"]
        recent_whale_bias = recent_analysis["whale_analysis"]["collective_bias"]
        main_shark_bias = main_analysis["shark_analysis"]["collective_bias"]
        recent_shark_bias = recent_analysis["shark_analysis"]["collective_bias"]
        
        trend_signals = []
        
        # Whale trend analysis
        if main_whale_bias != recent_whale_bias:
            trend_signals.append(f"whale_trend_change_{main_whale_bias}_to_{recent_whale_bias}")
        
        # Shark trend analysis
        if main_shark_bias != recent_shark_bias:
            trend_signals.append(f"shark_trend_change_{main_shark_bias}_to_{recent_shark_bias}")
        
        # Momentum analysis
        momentum = "neutral"
        if recent_whale_bias == "accumulating" and recent_shark_bias == "accumulating":
            momentum = "accelerating_bullish"
        elif recent_whale_bias == "distributing" and recent_shark_bias == "distributing":
            momentum = "accelerating_bearish"
        elif main_whale_bias == "neutral" and recent_whale_bias == "accumulating":
            momentum = "emerging_bullish"
        elif main_whale_bias == "neutral" and recent_whale_bias == "distributing":
            momentum = "emerging_bearish"
        
        return {
            "trend_signals": trend_signals,
            "momentum": momentum,
            "whale_trend_change": main_whale_bias != recent_whale_bias,
            "shark_trend_change": main_shark_bias != recent_shark_bias,
            "recent_dominance": {
                "whale_volume_6h": recent_analysis["whale_analysis"]["total_volume"],
                "shark_volume_6h": recent_analysis["shark_analysis"]["total_volume"]
            }
        }
    
    def _generate_enhanced_trading_insights(self, main_analysis: Dict, recent_analysis: Dict, 
                                          trend_analysis: Dict) -> Dict[str, Any]:
        """
        Generate enhanced trading insights with trend data.
        
        Args:
            main_analysis: 24h analysis
            recent_analysis: 6h analysis
            trend_analysis: Trend comparison
            
        Returns:
            Enhanced trading insights
        """
        base_insights = self._generate_trading_insights(
            main_analysis["whale_analysis"]["movement_pattern"],
            main_analysis["shark_analysis"]["movement_pattern"],
            main_analysis["market_structure"]
        )
        
        # Add trend-based insights
        momentum = trend_analysis.get("momentum", "neutral")
        
        if momentum == "accelerating_bullish":
            base_insights["signals"].append("momentum_acceleration_bullish")
            base_insights["confidence_level"] = "very_high"
            base_insights["recommended_action"] = "strong_long"
            
        elif momentum == "accelerating_bearish":
            base_insights["signals"].append("momentum_acceleration_bearish")
            base_insights["confidence_level"] = "very_high"
            base_insights["recommended_action"] = "strong_short"
            
        elif momentum == "emerging_bullish":
            base_insights["signals"].append("emerging_bullish_momentum")
            base_insights["recommended_action"] = "early_long"
            
        elif momentum == "emerging_bearish":
            base_insights["signals"].append("emerging_bearish_momentum")
            base_insights["recommended_action"] = "early_short"
        
        # Add trend change observations
        if trend_analysis.get("whale_trend_change"):
            base_insights["key_observations"].append("Whale behavior changed in recent 6h")
            
        if trend_analysis.get("shark_trend_change"):
            base_insights["key_observations"].append("Shark behavior changed in recent 6h")
        
        base_insights["trend_momentum"] = momentum
        
        return base_insights
    
    def _get_empty_analysis(self) -> Dict[str, Any]:
        """Get empty analysis structure for error cases."""
        return {
            "token_address": "",
            "analysis_timestamp": int(time.time()),
            "api_efficiency": {
                "api_calls_used": 0,
                "max_calls_allowed": self.api_strategy["max_api_calls_per_token"],
                "efficiency_rating": "failed",
                "timeframes_analyzed": []
            },
            "whale_analysis": {
                "count": 0,
                "total_volume": 0,
                "movement_pattern": {"directional_bias": "neutral"},
                "top_whales": [],
                "collective_bias": "neutral"
            },
            "shark_analysis": {
                "count": 0,
                "total_volume": 0,
                "movement_pattern": {"directional_bias": "neutral"},
                "top_sharks": [],
                "collective_bias": "neutral"
            },
            "market_structure": {
                "structure_type": "unknown",
                "whale_dominance": 0.0,
                "shark_presence": 0.0,
                "market_control": "unknown"
            },
            "trading_insights": {
                "signals": [],
                "recommended_action": "avoid",
                "confidence_level": "none"
            },
            "analysis_valid": False
        }
    
    async def batch_analyze_whale_shark_movements(self, token_addresses: List[str], 
                                                 auto_prioritize: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Efficiently analyze whale/shark movements for multiple tokens.
        
        Args:
            token_addresses: List of token addresses to analyze
            auto_prioritize: Automatically determine priority based on volume
            
        Returns:
            Dictionary mapping token addresses to their analyses
        """
        self.logger.info(f"🐋 Batch analyzing whale/shark movements for {len(token_addresses)} tokens")
        
        results = {}
        
        for token_address in token_addresses:
            try:
                # Auto-prioritize based on token characteristics if enabled
                if auto_prioritize:
                    priority = await self._determine_analysis_priority(token_address)
                else:
                    priority = "normal"
                
                # Analyze with determined priority
                analysis = await self.analyze_whale_shark_movements(token_address, priority)
                results[token_address] = analysis
                
                self.logger.debug(f"✅ Completed whale/shark analysis for {token_address} (priority: {priority})")
                
            except Exception as e:
                self.logger.error(f"❌ Failed whale/shark analysis for {token_address}: {e}")
                results[token_address] = self._get_empty_analysis()
        
        self.logger.info(f"🎯 Batch whale/shark analysis completed: {len(results)} tokens processed")
        return results
    
    async def _determine_analysis_priority(self, token_address: str) -> str:
        """
        Determine analysis priority based on token characteristics.
        
        Args:
            token_address: Token address to evaluate
            
        Returns:
            Priority level: "high" or "normal"
        """
        try:
            # Get basic token overview to determine priority
            overview = await self.birdeye_api.get_token_overview(token_address)
            
            if overview and isinstance(overview, dict):
                volume_24h = overview.get("volume", {}).get("h24", 0) or 0
                
                # High priority for high-volume tokens
                if volume_24h >= self.api_strategy["high_priority_volume_threshold"]:
                    return "high"
            
            return "normal"
            
        except Exception as e:
            self.logger.debug(f"Could not determine priority for {token_address}: {e}")
            return "normal"
    
    # === WHALE DATABASE MANAGEMENT ===

    def _load_discovered_whales(self):
        """Load dynamically discovered whales into the database"""
        if self.whale_discovery_service:
            try:
                discovered_whales = self.whale_discovery_service.get_whale_database_for_analyzer()
                
                # Merge discovered whales with existing database
                original_count = len(self.whale_database)
                self.whale_database.update(discovered_whales)
                new_count = len(self.whale_database) - original_count
                
                if new_count > 0:
                    self.logger.info(f"🐋 Loaded {new_count} dynamically discovered whales")
                    self.logger.info(f"   Total whale database size: {len(self.whale_database)} wallets")
                    
            except Exception as e:
                self.logger.warning(f"Failed to load discovered whales: {e}")

    async def refresh_whale_database(self):
        """Refresh the whale database with latest discoveries"""
        if self.whale_discovery_service:
            try:
                new_whales = await self.whale_discovery_service.discover_new_whales(max_discoveries=20)
                if new_whales:
                    self._load_discovered_whales()
                    self.logger.info(f"🔄 Refreshed whale database with {len(new_whales)} new discoveries")
            except Exception as e:
                self.logger.warning(f"Failed to refresh whale database: {e}")
    
    async def run_enhanced_whale_discovery(self, max_tokens: int = 20) -> Dict[str, Any]:
        """
        Run enhanced whale discovery session (Phase 2)
        
        Args:
            max_tokens: Maximum number of tokens to analyze
            
        Returns:
            Discovery session results
        """
        if not self.enhanced_discovery_service:
            self.logger.warning("Enhanced discovery service not available")
            return {"error": "Enhanced discovery service not initialized"}
        
        try:
            self.logger.info(f"🔍 Starting enhanced whale discovery session")
            
            # Run discovery session
            session = await self.enhanced_discovery_service.discover_whales_from_trending_tokens(
                max_tokens=max_tokens
            )
            
            # Get qualified whales
            qualified_whales = self.enhanced_discovery_service.get_qualified_whales()
            
            # Integrate discovered whales into our database
            integrated_count = 0
            for address, whale_metrics in qualified_whales.items():
                if address not in self.whale_database:
                    self.whale_database[address] = {
                        'tier': whale_metrics.tier,
                        'name': f"Discovered {whale_metrics.behavior_type.value.title()} {address[:8]}",
                        'avg_position': whale_metrics.avg_trade_size * 10,  # Estimate position size
                        'success_rate': whale_metrics.confidence_score,
                        'known_for': whale_metrics.behavior_type.value,
                        'discovery_date': whale_metrics.discovery_date.isoformat(),
                        'qualification_level': whale_metrics.qualification_level.value,
                        'total_volume_24h': whale_metrics.total_volume_24h
                    }
                    integrated_count += 1
            
            # Prepare results
            results = {
                "session_id": session.session_id,
                "success": session.success,
                "tokens_analyzed": session.tokens_analyzed,
                "candidates_found": session.candidates_found,
                "whales_qualified": session.whales_qualified,
                "whales_integrated": integrated_count,
                "processing_time_ms": session.processing_time_ms,
                "api_calls_used": session.api_calls_used,
                "discovery_stats": self.enhanced_discovery_service.get_discovery_stats()
            }
            
            if session.success:
                self.logger.info(f"✅ Enhanced discovery completed successfully")
                self.logger.info(f"   📊 Tokens analyzed: {session.tokens_analyzed}")
                self.logger.info(f"   🎯 Candidates found: {session.candidates_found}")
                self.logger.info(f"   🐋 Whales qualified: {session.whales_qualified}")
                self.logger.info(f"   🔗 Whales integrated: {integrated_count}")
                self.logger.info(f"   ⏱️ Processing time: {session.processing_time_ms}ms")
            else:
                self.logger.error(f"❌ Enhanced discovery failed: {session.error_message}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in enhanced whale discovery: {e}")
            return {
                "error": str(e),
                "success": False
            }

    def get_whale_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the current whale database"""
        total_whales = len(self.whale_database)
        tier_counts = {1: 0, 2: 0, 3: 0}
        
        for whale_data in self.whale_database.values():
            tier = whale_data.get('tier', 3)
            tier_counts[tier] += 1
        
        return {
            'total_whales': total_whales,
            'tier_distribution': tier_counts,
            'has_discovery_service': self.whale_discovery_service is not None
        }
    
    # === WHALE ACTIVITY ANALYSIS ===

    async def analyze_whale_activity_patterns(self, token_address: str, token_data: Dict[str, Any], scan_id: Optional[str] = None) -> WhaleSignal:
        """
        Analyze whale activity patterns for advanced signal generation.
        
        Args:
            token_address: Token address to analyze
            token_data: Token data for context
            scan_id: Optional scan identifier
            
        Returns:
            WhaleSignal with activity pattern analysis
        """
        try:
            # Get whale/shark movement data
            movement_data = await self.analyze_whale_shark_movements(token_address, "high")
            
            whales = movement_data.get("whales", [])
            total_whale_volume = sum(w.get("volume", 0) for w in whales)
            whale_addresses = [w.get("owner", "") for w in whales if w.get("owner")]
            
            # Determine activity type based on movement patterns
            activity_type = self._determine_whale_activity_type(movement_data)
            confidence = self._calculate_whale_activity_confidence(movement_data)
            score_impact = self._calculate_whale_score_impact(activity_type, confidence, len(whales))
            
            # Generate detailed analysis
            details = self._generate_whale_activity_details(activity_type, whales, total_whale_volume)
            
            signal = WhaleSignal(
                type=activity_type,
                confidence=confidence,
                score_impact=score_impact,
                whale_count=len(whales),
                total_value=total_whale_volume,
                timeframe="24h",
                details=details,
                whale_addresses=whale_addresses
            )
            
            self.structured_logger.info({
                "event": "whale_activity_analysis",
                "scan_id": scan_id,
                "token_address": token_address,
                "activity_type": activity_type.value,
                "whale_count": len(whales),
                "total_value": total_whale_volume,
                "confidence": confidence,
                "timestamp": int(time.time())
            })
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing whale activity patterns: {e}")
            return WhaleSignal(
                type=WhaleActivityType.ACCUMULATION,
                confidence=0.0,
                score_impact=0,
                whale_count=0,
                total_value=0.0,
                timeframe="error",
                details="Analysis failed",
                whale_addresses=[]
            )

    def _determine_whale_activity_type(self, movement_data: Dict[str, Any]) -> WhaleActivityType:
        """Determine whale activity type from movement data"""
        whale_movement = movement_data.get("whale_analysis", {}).get("movement_pattern", {})
        directional_bias = whale_movement.get("directional_bias", "neutral")
        
        if directional_bias == "accumulating":
            return WhaleActivityType.ACCUMULATION
        elif directional_bias == "distributing":
            return WhaleActivityType.DISTRIBUTION
        else:
            return WhaleActivityType.ROTATION

    def _calculate_whale_activity_confidence(self, movement_data: Dict[str, Any]) -> float:
        """Calculate confidence in whale activity analysis"""
        whale_count = movement_data.get("whale_analysis", {}).get("count", 0)
        total_volume = movement_data.get("whale_analysis", {}).get("total_volume", 0)
        
        # Higher confidence with more whales and higher volume
        confidence = min(0.5 + (whale_count / 20) + (total_volume / 10_000_000), 0.95)
        return confidence

    def _calculate_whale_score_impact(self, activity_type: WhaleActivityType, confidence: float, whale_count: int) -> int:
        """Calculate score impact based on whale activity"""
        base_impact = {
            WhaleActivityType.ACCUMULATION: 20,
            WhaleActivityType.SMART_MONEY_ENTRY: 25,
            WhaleActivityType.COORDINATED_BUY: 22,
            WhaleActivityType.INSTITUTIONAL_FLOW: 18,
            WhaleActivityType.DISTRIBUTION: -15,
            WhaleActivityType.ROTATION: 5,
            WhaleActivityType.STEALTH_ACCUMULATION: 15
        }.get(activity_type, 0)
        
        # Adjust by confidence and whale count
        impact = int(base_impact * confidence * min(1.0 + (whale_count / 10), 2.0))
        return max(-20, min(25, impact))

    def _generate_whale_activity_details(self, activity_type: WhaleActivityType, whales: List[Dict], total_volume: float) -> str:
        """Generate human-readable details about whale activity"""
        whale_count = len(whales)
        
        if activity_type == WhaleActivityType.ACCUMULATION:
            return f"{whale_count} whales accumulating (${total_volume:,.0f} total volume)"
        elif activity_type == WhaleActivityType.DISTRIBUTION:
            return f"{whale_count} whales distributing (${total_volume:,.0f} total volume)"
        else:
            return f"{whale_count} whales active in {activity_type.value} (${total_volume:,.0f} total volume)"