#!/usr/bin/env python3
"""
Enhanced DexScreener Integration for High Conviction Token Discovery
Leverages all available DexScreener API endpoints for comprehensive analysis
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode

@dataclass
class TokenProfile:
    """Enhanced token profile with social signals"""
    address: str
    chain_id: str
    description: str
    website: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    social_score: float = 0.0
    narrative_strength: float = 0.0

@dataclass
class LiquidityAnalysis:
    """Token liquidity analysis across DEXes"""
    total_liquidity_usd: float
    pair_count: int
    primary_dex: str
    liquidity_distribution: Dict[str, float]
    best_entry_pair: Optional[str] = None

@dataclass
class EnhancedTokenData:
    """Comprehensive token data combining all signals"""
    address: str
    symbol: str
    name: str
    price_usd: float
    market_cap: float
    volume_24h: float
    price_change_24h: float
    
    # DexScreener specific data
    boost_data: Optional[Dict] = None
    profile: Optional[TokenProfile] = None
    liquidity: Optional[LiquidityAnalysis] = None
    
    # Composite scores
    technical_score: float = 0.0
    fundamental_score: float = 0.0
    social_score: float = 0.0
    conviction_score: float = 0.0

class EnhancedDexScreenerConnector:
    """Enhanced DexScreener API connector using all available endpoints"""
    
    def __init__(self):
        self.base_url = "https://api.dexscreener.com"
        self.session = None
        
        # Rate limits per endpoint (requests per minute)
        self.rate_limits = {
            "profiles": 60,
            "boosts": 60, 
            "pairs": 300,
            "search": 300,
            "tokens": 300
        }
        
        # API statistics
        self.api_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "endpoints_used": set(),
            "response_times": []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make tracked API request with error handling"""
        start_time = time.time()
        self.api_stats["total_calls"] += 1
        self.api_stats["endpoints_used"].add(endpoint)
        
        url = f"{self.base_url}{endpoint}"
        if params:
            url += f"?{urlencode(params)}"
        
        try:
            async with self.session.get(url) as response:
                response_time = (time.time() - start_time) * 1000
                self.api_stats["response_times"].append(response_time)
                
                if response.status == 200:
                    self.api_stats["successful_calls"] += 1
                    data = await response.json()
                    logging.info(f"✅ DexScreener {endpoint}: {response.status} ({response_time:.1f}ms)")
                    return data
                else:
                    self.api_stats["failed_calls"] += 1
                    logging.warning(f"❌ DexScreener {endpoint}: {response.status} ({response_time:.1f}ms)")
                    return None
                    
        except Exception as e:
            self.api_stats["failed_calls"] += 1
            logging.error(f"🔴 DexScreener {endpoint} error: {e}")
            return None

    async def get_token_profiles(self) -> List[TokenProfile]:
        """Get latest token profiles with rich metadata"""
        data = await self._make_request("/token-profiles/latest/v1")
        if not data:
            return []
        
        profiles = []
        for item in data:
            # Extract social links
            website = None
            twitter = None
            telegram = None
            
            for link in item.get("links", []):
                link_type = link.get("type", "").lower()
                url = link.get("url", "")
                
                if link_type == "twitter" or "twitter.com" in url or "x.com" in url:
                    twitter = url
                elif link_type == "telegram" or "t.me" in url:
                    telegram = url
                elif link.get("label", "").lower() == "website":
                    website = url
            
            # Calculate social score
            social_score = 0.0
            if website: social_score += 0.3
            if twitter: social_score += 0.4
            if telegram: social_score += 0.3
            
            # Calculate narrative strength based on description
            description = item.get("description", "")
            narrative_strength = min(len(description) / 500, 1.0)  # Normalize to 0-1
            
            profile = TokenProfile(
                address=item.get("tokenAddress", ""),
                chain_id=item.get("chainId", ""),
                description=description,
                website=website,
                twitter=twitter,
                telegram=telegram,
                social_score=social_score,
                narrative_strength=narrative_strength
            )
            profiles.append(profile)
        
        logging.info(f"📋 Retrieved {len(profiles)} token profiles")
        return profiles

    async def get_batch_token_data(self, token_addresses: List[str], chain_id: str = "solana") -> List[Dict]:
        """Efficiently batch fetch token data (up to 30 tokens)"""
        if not token_addresses:
            return []
        
        # Split into batches of 30 (API limit)
        batches = [token_addresses[i:i+30] for i in range(0, len(token_addresses), 30)]
        all_data = []
        
        for batch in batches:
            addresses_str = ",".join(batch)
            endpoint = f"/tokens/v1/{chain_id}/{addresses_str}"
            data = await self._make_request(endpoint)
            
            if data:
                all_data.extend(data)
        
        logging.info(f"📊 Batch processed {len(token_addresses)} tokens in {len(batches)} requests")
        return all_data

    async def get_token_liquidity_analysis(self, token_address: str, chain_id: str = "solana") -> Optional[LiquidityAnalysis]:
        """Analyze token liquidity across all DEXes"""
        endpoint = f"/token-pairs/v1/{chain_id}/{token_address}"
        data = await self._make_request(endpoint)
        
        if not data:
            return None
        
        total_liquidity = 0.0
        liquidity_by_dex = {}
        best_pair = None
        best_liquidity = 0.0
        
        for pair in data:
            liquidity = pair.get("liquidity", {})
            pair_liquidity = liquidity.get("usd", 0.0)
            dex_id = pair.get("dexId", "unknown")
            
            total_liquidity += pair_liquidity
            liquidity_by_dex[dex_id] = liquidity_by_dex.get(dex_id, 0.0) + pair_liquidity
            
            if pair_liquidity > best_liquidity:
                best_liquidity = pair_liquidity
                best_pair = pair.get("pairAddress")
        
        # Find primary DEX
        primary_dex = max(liquidity_by_dex, key=liquidity_by_dex.get) if liquidity_by_dex else "unknown"
        
        return LiquidityAnalysis(
            total_liquidity_usd=total_liquidity,
            pair_count=len(data),
            primary_dex=primary_dex,
            liquidity_distribution=liquidity_by_dex,
            best_entry_pair=best_pair
        )

    async def search_tokens_by_criteria(self, query: str) -> List[Dict]:
        """Search for tokens matching specific criteria"""
        params = {"q": query}
        data = await self._make_request("/latest/dex/search", params)
        
        if not data or "pairs" not in data:
            return []
        
        logging.info(f"🔍 Search '{query}' found {len(data['pairs'])} results")
        return data["pairs"]

    async def discover_narrative_tokens(self, narratives: List[str]) -> Dict[str, List[Dict]]:
        """Discover tokens by searching for specific narratives"""
        results = {}
        
        for narrative in narratives:
            tokens = await self.search_tokens_by_criteria(narrative)
            if tokens:
                results[narrative] = tokens
        
        return results

    def calculate_conviction_score(self, token_data: EnhancedTokenData) -> float:
        """Calculate comprehensive conviction score"""
        # Technical indicators (40% weight)
        technical_score = 0.0
        if token_data.volume_24h > 100000:  # High volume
            technical_score += 0.3
        if token_data.price_change_24h > 0:  # Positive momentum
            technical_score += 0.2
        if token_data.market_cap > 1000000:  # Reasonable market cap
            technical_score += 0.3
        if token_data.liquidity and token_data.liquidity.total_liquidity_usd > 50000:
            technical_score += 0.2
        
        # Fundamental indicators (30% weight)
        fundamental_score = 0.0
        if token_data.profile:
            fundamental_score += token_data.profile.narrative_strength * 0.5
            fundamental_score += token_data.profile.social_score * 0.5
        
        # Social/Marketing indicators (30% weight)
        social_score = 0.0
        if token_data.boost_data:
            boost_total = token_data.boost_data.get("totalAmount", 0)
            boost_current = token_data.boost_data.get("amount", 0)
            boost_consumption = (boost_total - boost_current) / max(boost_total, 1)
            
            social_score += min(boost_consumption, 1.0) * 0.5  # Boost activity
            social_score += min(boost_total / 1000, 1.0) * 0.5  # Boost investment
        
        # Weighted combination
        conviction_score = (
            technical_score * 0.4 +
            fundamental_score * 0.3 +
            social_score * 0.3
        )
        
        # Update token data
        token_data.technical_score = technical_score
        token_data.fundamental_score = fundamental_score
        token_data.social_score = social_score
        token_data.conviction_score = conviction_score
        
        return conviction_score

async def demonstrate_enhanced_discovery():
    """Demonstrate enhanced DexScreener integration"""
    async with EnhancedDexScreenerConnector() as connector:
        print("🚀 Enhanced DexScreener Integration Demo")
        print("=" * 50)
        
        # 1. Get token profiles for fundamental analysis
        print("\n📋 Fetching Token Profiles...")
        profiles = await connector.get_token_profiles()
        print(f"Found {len(profiles)} token profiles")
        
        if profiles:
            top_profile = max(profiles, key=lambda p: p.social_score + p.narrative_strength)
            print(f"🏆 Top Profile: {top_profile.address}")
            print(f"   📝 Description: {top_profile.description[:100]}...")
            print(f"   🌐 Website: {top_profile.website}")
            print(f"   🐦 Twitter: {top_profile.twitter}")
            print(f"   📱 Telegram: {top_profile.telegram}")
            print(f"   📊 Social Score: {top_profile.social_score:.2f}")
        
        # 2. Demonstrate narrative-based discovery
        print("\n🔍 Narrative-Based Discovery...")
        narratives = ["AI", "gaming", "DeFi", "meme"]
        narrative_results = await connector.discover_narrative_tokens(narratives)
        
        for narrative, tokens in narrative_results.items():
            print(f"   🎯 '{narrative}': {len(tokens)} tokens found")
        
        # 3. Batch process token data
        if profiles:
            print("\n📊 Batch Token Processing...")
            addresses = [p.address for p in profiles[:10]]  # Top 10
            batch_data = await connector.get_batch_token_data(addresses)
            print(f"Processed {len(batch_data)} tokens in batch")
        
        # 4. Liquidity analysis
        if profiles:
            print("\n💧 Liquidity Analysis...")
            token_address = profiles[0].address
            liquidity = await connector.get_token_liquidity_analysis(token_address)
            
            if liquidity:
                print(f"   💰 Total Liquidity: ${liquidity.total_liquidity_usd:,.2f}")
                print(f"   🔄 Trading Pairs: {liquidity.pair_count}")
                print(f"   🏆 Primary DEX: {liquidity.primary_dex}")
                print(f"   🎯 Best Entry Pair: {liquidity.best_entry_pair}")
        
        # 5. API Performance Summary
        print("\n📈 API Performance Summary")
        print(f"   📞 Total Calls: {connector.api_stats['total_calls']}")
        print(f"   ✅ Successful: {connector.api_stats['successful_calls']}")
        print(f"   ❌ Failed: {connector.api_stats['failed_calls']}")
        print(f"   🌐 Endpoints Used: {len(connector.api_stats['endpoints_used'])}")
        
        if connector.api_stats['response_times']:
            avg_response = sum(connector.api_stats['response_times']) / len(connector.api_stats['response_times'])
            print(f"   ⚡ Avg Response Time: {avg_response:.1f}ms")

if __name__ == "__main__":
    asyncio.run(demonstrate_enhanced_discovery()) 