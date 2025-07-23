"""
Enhanced Whale Discovery Service - Phase 2 Implementation
Dynamically discovers and qualifies whale addresses based on trading patterns
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, Counter

from utils.logger_setup import LoggerSetup


class WhaleQualificationLevel(Enum):
    """Whale qualification levels based on discovery analysis"""
    UNQUALIFIED = "unqualified"
    CANDIDATE = "candidate"
    QUALIFIED = "qualified"
    VERIFIED = "verified"
    ELITE = "elite"


class WhaleBehaviorType(Enum):
    """Enhanced whale behavior classification"""
    ACCUMULATOR = "accumulator"           # Consistent buying patterns
    DISTRIBUTOR = "distributor"           # Consistent selling patterns
    ROTATOR = "rotator"                   # Mixed trading patterns
    SCALPER = "scalper"                   # High-frequency trading
    HODLER = "hodler"                     # Long-term holding patterns
    ARBITRAGEUR = "arbitrageur"           # Cross-market trading
    INSTITUTIONAL = "institutional"       # Large, coordinated movements
    SMART_MONEY = "smart_money"          # Early entry/exit patterns


@dataclass
class WhaleCandidate:
    """Represents a potential whale during discovery process"""
    address: str
    total_volume: float = 0.0
    trade_count: int = 0
    token_count: int = 0  # Number of different tokens traded
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    avg_trade_size: float = 0.0
    max_trade_size: float = 0.0
    tokens_traded: Set[str] = field(default_factory=set)
    behavior_indicators: Dict[str, float] = field(default_factory=dict)
    qualification_level: WhaleQualificationLevel = WhaleQualificationLevel.UNQUALIFIED
    behavior_type: Optional[WhaleBehaviorType] = None
    confidence_score: float = 0.0
    
    def update_metrics(self, volume: float, token_address: str, timestamp: datetime = None):
        """Update whale candidate metrics with new trading data"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self.total_volume += volume
        self.trade_count += 1
        self.tokens_traded.add(token_address)
        self.token_count = len(self.tokens_traded)
        self.last_seen = max(self.last_seen, timestamp)
        self.avg_trade_size = self.total_volume / self.trade_count
        self.max_trade_size = max(self.max_trade_size, volume)


@dataclass
class WhaleMetrics:
    """Detailed metrics for qualified whales"""
    address: str
    qualification_level: WhaleQualificationLevel
    behavior_type: WhaleBehaviorType
    total_volume_30d: float = 0.0
    total_volume_7d: float = 0.0
    total_volume_24h: float = 0.0
    trade_frequency: float = 0.0  # Trades per day
    token_diversity: int = 0  # Number of different tokens
    avg_trade_size: float = 0.0
    consistency_score: float = 0.0  # How consistent their trading patterns are
    impact_score: float = 0.0  # Market impact of their trades
    discovery_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0
    tier: int = 3  # Default to tier 3, can be promoted


@dataclass
class DiscoverySession:
    """Tracks a whale discovery session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    tokens_analyzed: int = 0
    candidates_found: int = 0
    whales_qualified: int = 0
    api_calls_used: int = 0
    processing_time_ms: int = 0
    success: bool = False
    error_message: Optional[str] = None


class WhaleDiscoveryService:
    """
    Enhanced whale discovery service that dynamically identifies whale addresses
    based on trading patterns across multiple tokens
    """
    
    def __init__(self, birdeye_api, logger=None, config=None):
        self.birdeye_api = birdeye_api
        self.logger = logger or LoggerSetup("WhaleDiscoveryService").logger
        self.config = config or self._get_default_config()
        
        # Discovery state
        self.candidates: Dict[str, WhaleCandidate] = {}
        self.qualified_whales: Dict[str, WhaleMetrics] = {}
        self.discovery_sessions: List[DiscoverySession] = []
        
        # Cache for performance
        self.trader_cache: Dict[str, List] = {}
        self.cache_ttl = 3600  # 1 hour
        self.last_cache_cleanup = time.time()
        
        self.logger.info("🔍 WhaleDiscoveryService initialized")
        self.logger.info(f"   📊 Discovery thresholds: {self.config['qualification_thresholds']}")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for whale discovery"""
        return {
            "qualification_thresholds": {
                "min_volume_24h": 100000,      # $100k minimum 24h volume
                "min_volume_7d": 500000,       # $500k minimum 7d volume
                "min_trade_count": 10,         # Minimum number of trades
                "min_token_diversity": 3,      # Must trade at least 3 different tokens
                "min_avg_trade_size": 10000,   # $10k minimum average trade size
                "min_consistency_score": 0.6,  # 60% consistency threshold
            },
            "behavior_analysis": {
                "accumulation_threshold": 0.7,  # 70% buy vs sell ratio
                "distribution_threshold": 0.3,  # 30% buy vs sell ratio
                "scalping_frequency": 50,       # 50+ trades per day
                "hodler_min_hold_days": 7,      # 7+ days holding period
            },
            "discovery_scope": {
                "max_tokens_per_session": 20,   # Analyze top 20 tokens
                "max_traders_per_token": 50,    # Top 50 traders per token
                "discovery_frequency_hours": 6, # Run discovery every 6 hours
            },
            "tier_assignment": {
                "tier_1_min_volume": 5000000,   # $5M+ for tier 1
                "tier_2_min_volume": 1000000,   # $1M+ for tier 2
                "tier_3_min_volume": 100000,    # $100k+ for tier 3
            }
        }
    
    async def discover_whales_from_trending_tokens(self, max_tokens: int = None) -> DiscoverySession:
        """
        Discover whales by analyzing top traders across trending tokens
        """
        session_id = f"discovery_{int(time.time())}"
        session = DiscoverySession(
            session_id=session_id,
            start_time=datetime.now()
        )
        
        try:
            self.logger.info(f"🔍 Starting whale discovery session: {session_id}")
            
            # Get trending tokens to analyze
            max_tokens = max_tokens or self.config["discovery_scope"]["max_tokens_per_session"]
            trending_tokens = await self._get_trending_tokens(max_tokens)
            session.tokens_analyzed = len(trending_tokens)
            
            self.logger.info(f"📊 Analyzing {len(trending_tokens)} trending tokens for whale discovery")
            
            # Analyze traders across all tokens
            all_traders = {}
            for token_address in trending_tokens:
                try:
                    traders = await self._get_top_traders_for_token(token_address)
                    session.api_calls_used += 1
                    
                    for trader in traders:
                        trader_address = trader.get('address', '')
                        if trader_address:
                            if trader_address not in all_traders:
                                all_traders[trader_address] = []
                            all_traders[trader_address].append({
                                'token': token_address,
                                'volume': trader.get('volume', 0),
                                'trades': trader.get('trades', 0),
                                'timestamp': datetime.now()
                            })
                    
                except Exception as e:
                    self.logger.warning(f"Error analyzing token {token_address}: {e}")
                    continue
            
            # Process trader data to identify whale candidates
            candidates_found = 0
            for trader_address, trading_data in all_traders.items():
                candidate = await self._analyze_trader_for_whale_qualification(
                    trader_address, trading_data
                )
                
                if candidate and candidate.qualification_level != WhaleQualificationLevel.UNQUALIFIED:
                    self.candidates[trader_address] = candidate
                    candidates_found += 1
            
            session.candidates_found = candidates_found
            
            # Qualify candidates as whales
            whales_qualified = await self._qualify_whale_candidates()
            session.whales_qualified = whales_qualified
            
            session.end_time = datetime.now()
            session.processing_time_ms = int((session.end_time - session.start_time).total_seconds() * 1000)
            session.success = True
            
            self.logger.info(f"✅ Discovery session completed: {session_id}")
            self.logger.info(f"   📊 Tokens analyzed: {session.tokens_analyzed}")
            self.logger.info(f"   🎯 Candidates found: {session.candidates_found}")
            self.logger.info(f"   🐋 Whales qualified: {session.whales_qualified}")
            self.logger.info(f"   ⏱️ Processing time: {session.processing_time_ms}ms")
            
        except Exception as e:
            session.end_time = datetime.now()
            session.error_message = str(e)
            session.success = False
            self.logger.error(f"❌ Discovery session failed: {e}")
        
        self.discovery_sessions.append(session)
        return session
    
    async def _get_trending_tokens(self, limit: int) -> List[str]:
        """Get list of trending token addresses"""
        try:
            # Use birdeye API to get trending tokens (fallback to token list if trending not available)
            try:
                trending_data = await self.birdeye_api.get_token_list(
                    sort_by="volume_24h_usd",
                    sort_type="desc",
                    limit=limit,
                    min_volume_24h_usd=1000000  # $1M+ volume for active tokens
                )
            except Exception as e:
                self.logger.warning(f"Could not get token list: {e}")
                trending_data = None
            
            if trending_data and 'data' in trending_data:
                tokens_data = trending_data['data']
                if isinstance(tokens_data, dict) and 'tokens' in tokens_data:
                    # Handle token list response format
                    return [token.get('address', '') for token in tokens_data['tokens'] if token.get('address')]
                elif isinstance(tokens_data, list):
                    # Handle direct list response
                    return [token.get('address', '') for token in tokens_data if token.get('address')]
            
            # Fallback to some known active tokens if trending fails
            fallback_tokens = [
                "So11111111111111111111111111111111111111112",  # SOL
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
            ]
            
            self.logger.warning("Using fallback tokens for discovery")
            return fallback_tokens[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting trending tokens: {e}")
            return []
    
    async def _get_top_traders_for_token(self, token_address: str) -> List[Dict]:
        """Get top traders for a specific token"""
        try:
            # Check cache first
            cache_key = f"traders_{token_address}"
            if cache_key in self.trader_cache:
                cached_data, timestamp = self.trader_cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Get top traders from API
            max_traders = self.config["discovery_scope"]["max_traders_per_token"]
            traders_data = await self.birdeye_api.get_top_traders_optimized(
                token_address, 
                time_frame="24h",
                limit=max_traders
            )
            
            traders = []
            if traders_data and 'items' in traders_data:
                traders = traders_data['items']
            
            # Cache the result
            self.trader_cache[cache_key] = (traders, time.time())
            
            return traders
            
        except Exception as e:
            self.logger.error(f"Error getting top traders for {token_address}: {e}")
            return []
    
    async def _analyze_trader_for_whale_qualification(
        self, 
        trader_address: str, 
        trading_data: List[Dict]
    ) -> Optional[WhaleCandidate]:
        """Analyze a trader's data to determine whale qualification"""
        try:
            if not trading_data:
                return None
            
            # Calculate basic metrics
            total_volume = sum(trade.get('volume', 0) for trade in trading_data)
            total_trades = sum(trade.get('trades', 0) for trade in trading_data)
            unique_tokens = len(set(trade.get('token', '') for trade in trading_data))
            
            # Create candidate
            candidate = WhaleCandidate(
                address=trader_address,
                total_volume=total_volume,
                trade_count=total_trades,
                token_count=unique_tokens,
                tokens_traded=set(trade.get('token', '') for trade in trading_data)
            )
            
            if total_trades > 0:
                candidate.avg_trade_size = total_volume / total_trades
                candidate.max_trade_size = max(trade.get('volume', 0) for trade in trading_data)
            
            # Analyze behavior patterns
            behavior_score = await self._analyze_behavior_patterns(trading_data)
            candidate.behavior_indicators = behavior_score
            
            # Determine qualification level
            qualification = await self._determine_qualification_level(candidate)
            candidate.qualification_level = qualification
            
            # Determine behavior type
            behavior_type = await self._classify_behavior_type(candidate)
            candidate.behavior_type = behavior_type
            
            # Calculate confidence score
            confidence = await self._calculate_confidence_score(candidate)
            candidate.confidence_score = confidence
            
            return candidate
            
        except Exception as e:
            self.logger.error(f"Error analyzing trader {trader_address}: {e}")
            return None
    
    async def _analyze_behavior_patterns(self, trading_data: List[Dict]) -> Dict[str, float]:
        """Analyze trading behavior patterns"""
        patterns = {
            "volume_consistency": 0.0,
            "frequency_score": 0.0,
            "diversity_score": 0.0,
            "size_consistency": 0.0
        }
        
        if not trading_data:
            return patterns
        
        volumes = [trade.get('volume', 0) for trade in trading_data]
        
        # Volume consistency (lower variance = higher consistency)
        if len(volumes) > 1:
            avg_volume = sum(volumes) / len(volumes)
            variance = sum((v - avg_volume) ** 2 for v in volumes) / len(volumes)
            patterns["volume_consistency"] = max(0, 1 - (variance / avg_volume if avg_volume > 0 else 1))
        
        # Frequency score (more trades = higher frequency)
        patterns["frequency_score"] = min(1.0, len(trading_data) / 100)
        
        # Diversity score (more tokens = higher diversity)
        unique_tokens = len(set(trade.get('token', '') for trade in trading_data))
        patterns["diversity_score"] = min(1.0, unique_tokens / 10)
        
        # Size consistency
        if volumes:
            max_vol = max(volumes)
            min_vol = min(volumes)
            if max_vol > 0:
                patterns["size_consistency"] = min_vol / max_vol
        
        return patterns
    
    async def _determine_qualification_level(self, candidate: WhaleCandidate) -> WhaleQualificationLevel:
        """Determine whale qualification level based on metrics"""
        thresholds = self.config["qualification_thresholds"]
        
        # Check basic requirements
        if (candidate.total_volume < thresholds["min_volume_24h"] or
            candidate.trade_count < thresholds["min_trade_count"] or
            candidate.token_count < thresholds["min_token_diversity"] or
            candidate.avg_trade_size < thresholds["min_avg_trade_size"]):
            return WhaleQualificationLevel.UNQUALIFIED
        
        # Calculate overall score
        score = 0.0
        
        # Volume score (0-0.4)
        volume_score = min(0.4, candidate.total_volume / 10000000)  # Max at $10M
        score += volume_score
        
        # Consistency score (0-0.3)
        consistency = candidate.behavior_indicators.get("volume_consistency", 0)
        score += consistency * 0.3
        
        # Diversity score (0-0.2)
        diversity = min(1.0, candidate.token_count / 10)
        score += diversity * 0.2
        
        # Trade size score (0-0.1)
        size_score = min(0.1, candidate.avg_trade_size / 1000000)  # Max at $1M
        score += size_score
        
        # Determine qualification level
        if score >= 0.9:
            return WhaleQualificationLevel.ELITE
        elif score >= 0.7:
            return WhaleQualificationLevel.VERIFIED
        elif score >= 0.5:
            return WhaleQualificationLevel.QUALIFIED
        elif score >= 0.3:
            return WhaleQualificationLevel.CANDIDATE
        else:
            return WhaleQualificationLevel.UNQUALIFIED
    
    async def _classify_behavior_type(self, candidate: WhaleCandidate) -> WhaleBehaviorType:
        """Classify whale behavior type based on patterns"""
        # Default classification logic - can be enhanced with more sophisticated analysis
        
        if candidate.avg_trade_size > 1000000:  # $1M+ average
            return WhaleBehaviorType.INSTITUTIONAL
        elif candidate.trade_count > 100:  # High frequency
            return WhaleBehaviorType.SCALPER
        elif candidate.token_count > 10:  # High diversity
            return WhaleBehaviorType.ARBITRAGEUR
        elif candidate.behavior_indicators.get("volume_consistency", 0) > 0.8:
            return WhaleBehaviorType.ACCUMULATOR
        else:
            return WhaleBehaviorType.ROTATOR
    
    async def _calculate_confidence_score(self, candidate: WhaleCandidate) -> float:
        """Calculate confidence score for whale qualification"""
        score = 0.0
        
        # Volume confidence (0-0.4)
        if candidate.total_volume > 1000000:  # $1M+
            score += 0.4
        elif candidate.total_volume > 500000:  # $500k+
            score += 0.3
        elif candidate.total_volume > 100000:  # $100k+
            score += 0.2
        
        # Consistency confidence (0-0.3)
        consistency = candidate.behavior_indicators.get("volume_consistency", 0)
        score += consistency * 0.3
        
        # Diversity confidence (0-0.2)
        diversity_score = min(1.0, candidate.token_count / 5)
        score += diversity_score * 0.2
        
        # Trade count confidence (0-0.1)
        trade_score = min(1.0, candidate.trade_count / 50)
        score += trade_score * 0.1
        
        return min(1.0, score)
    
    async def _qualify_whale_candidates(self) -> int:
        """Convert qualified candidates to whale metrics"""
        qualified_count = 0
        
        for address, candidate in self.candidates.items():
            if candidate.qualification_level in [
                WhaleQualificationLevel.QUALIFIED,
                WhaleQualificationLevel.VERIFIED,
                WhaleQualificationLevel.ELITE
            ]:
                # Convert to whale metrics
                whale_metrics = WhaleMetrics(
                    address=address,
                    qualification_level=candidate.qualification_level,
                    behavior_type=candidate.behavior_type,
                    total_volume_24h=candidate.total_volume,
                    trade_frequency=candidate.trade_count,  # Simplified
                    token_diversity=candidate.token_count,
                    avg_trade_size=candidate.avg_trade_size,
                    consistency_score=candidate.behavior_indicators.get("volume_consistency", 0),
                    confidence_score=candidate.confidence_score,
                    tier=self._assign_tier(candidate.total_volume)
                )
                
                self.qualified_whales[address] = whale_metrics
                qualified_count += 1
                
                self.logger.info(f"🐋 Qualified new whale: {address[:8]}...")
                self.logger.info(f"   💰 Volume: ${candidate.total_volume:,.2f}")
                self.logger.info(f"   🎯 Confidence: {candidate.confidence_score:.2f}")
                self.logger.info(f"   🏷️ Type: {candidate.behavior_type.value}")
                self.logger.info(f"   ⭐ Tier: {whale_metrics.tier}")
        
        return qualified_count
    
    def _assign_tier(self, volume: float) -> int:
        """Assign tier based on volume"""
        tier_config = self.config["tier_assignment"]
        
        if volume >= tier_config["tier_1_min_volume"]:
            return 1
        elif volume >= tier_config["tier_2_min_volume"]:
            return 2
        else:
            return 3
    
    def get_qualified_whales(self) -> Dict[str, WhaleMetrics]:
        """Get all qualified whales"""
        return self.qualified_whales.copy()
    
    def get_discovery_stats(self) -> Dict:
        """Get discovery service statistics"""
        total_sessions = len(self.discovery_sessions)
        successful_sessions = sum(1 for s in self.discovery_sessions if s.success)
        
        return {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "success_rate": successful_sessions / total_sessions if total_sessions > 0 else 0,
            "total_candidates": len(self.candidates),
            "qualified_whales": len(self.qualified_whales),
            "qualification_rate": len(self.qualified_whales) / len(self.candidates) if self.candidates else 0,
            "last_discovery": self.discovery_sessions[-1].start_time if self.discovery_sessions else None
        }
    
    async def cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, (data, timestamp) in self.trader_cache.items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.trader_cache[key]
        
        self.last_cache_cleanup = current_time
        
        if expired_keys:
            self.logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries") 