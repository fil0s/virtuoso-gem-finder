"""
Token Data Manager for centralized data fetching and caching

This manager centralizes all token data fetching to eliminate duplicate API calls
and provides a unified interface for accessing token data across analysis components.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from api.birdeye_connector import BirdeyeAPI
import time
from utils.structured_logger import get_structured_logger

class TokenDataManager:
    """
    Centralized manager for token data fetching.
    Eliminates duplicate API calls by caching data within analysis cycles.
    """
    
    def __init__(self, birdeye_api: BirdeyeAPI, logger: logging.Logger):
        self.birdeye_api = birdeye_api
        self.logger = logger
        
        # Data cache for the current analysis cycle
        self.data_cache = {}
        
        # Track what data has been fetched
        self.fetched_data_types = set()
        
        # Cache configuration
        self.cache_ttl = 300  # 5 minutes default TTL
        
        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
        
        self.structured_logger = get_structured_logger('TokenDataManager')
        
        self.logger.info("📊 TokenDataManager initialized with enhanced caching and performance tracking")
        
    def reset_cache(self):
        """Reset cache for new analysis cycle"""
        self.data_cache = {}
        self.fetched_data_types = set()
    
    async def get_overview(self, token_address: str, scan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get token overview data with caching"""
        cache_key = f"overview_{token_address}"
        
        if cache_key in self.data_cache:
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "overview",
                "cache_hit": True,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return self.data_cache[cache_key]
        
        try:
            overview = await self.birdeye_api.get_token_overview(token_address)
            self.data_cache[cache_key] = overview
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "overview",
                "cache_hit": False,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return overview
        except Exception as e:
            self.structured_logger.error({
                "event": "data_fetch_error",
                "token_address": token_address,
                "data_type": "overview",
                "error": str(e),
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            self.logger.error(f"Error fetching overview for {token_address}: {e}")
            return None
    
    async def get_price_data(self, token_address: str, scan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive price data with smart fallbacks.
        Combines multi_price, historical, and OHLCV data efficiently.
        """
        cache_key = f"price_data_{token_address}"
        
        if cache_key in self.data_cache:
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "price_data",
                "cache_hit": True,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return self.data_cache[cache_key]
        
        price_data = {}
        
        try:
            # Get current price from multi_price (most reliable)
            multi_price_data = await self.birdeye_api.get_multi_price([token_address])
            if multi_price_data and token_address in multi_price_data:
                price_data['current'] = multi_price_data[token_address]
            
            # Get historical price (24h ago)
            twenty_four_hours_ago = int(time.time()) - 86400
            historical_price = await self.birdeye_api.get_historical_price_at_timestamp(
                token_address, twenty_four_hours_ago
            )
            if historical_price:
                price_data['historical_24h'] = historical_price
            
            # Cache the combined price data
            self.data_cache[cache_key] = price_data
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "price_data",
                "cache_hit": False,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return price_data
            
        except Exception as e:
            self.structured_logger.error({
                "event": "data_fetch_error",
                "token_address": token_address,
                "data_type": "price_data",
                "error": str(e),
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            self.logger.error(f"Error fetching price data for {token_address}: {e}")
            return None
    
    async def get_trading_data(self, token_address: str, scan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive trading data including OHLCV, trades, and metrics.
        Uses efficient single OHLCV call and derives multiple timeframes.
        """
        cache_key = f"trading_data_{token_address}"
        
        if cache_key in self.data_cache:
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "trading_data",
                "cache_hit": True,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return self.data_cache[cache_key]
        
        trading_data = {}
        
        try:
            # Get 1-minute OHLCV data (can be aggregated for other timeframes)
            ohlcv_1m = await self.birdeye_api.get_ohlcv_data(token_address, time_frame='1m', limit=1440)  # 24 hours
            if ohlcv_1m:
                trading_data['ohlcv_1m'] = ohlcv_1m
                
                # Derive other timeframes from 1m data to avoid additional API calls
                trading_data['ohlcv_5m'] = self._aggregate_ohlcv(ohlcv_1m, 5)
                trading_data['ohlcv_15m'] = self._aggregate_ohlcv(ohlcv_1m, 15)
                trading_data['ohlcv_1h'] = self._aggregate_ohlcv(ohlcv_1m, 60)
            
            # Get recent trades (using  endpoint)
            recent_trades = await self.birdeye_api.get_token_trades(token_address, limit=50)
            if recent_trades:
                trading_data['recent_trades'] = recent_trades
            
            # Get trade metrics (includes trend dynamics)
            trade_metrics = await self.birdeye_api.get_token_trade_metrics(token_address)
            if trade_metrics:
                trading_data['trade_metrics'] = trade_metrics
            
            self.data_cache[cache_key] = trading_data
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "trading_data",
                "cache_hit": False,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return trading_data
            
        except Exception as e:
            self.structured_logger.error({
                "event": "data_fetch_error",
                "token_address": token_address,
                "data_type": "trading_data",
                "error": str(e),
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            self.logger.error(f"Error fetching trading data for {token_address}: {e}")
            return None
    
    async def get_holder_data(self, token_address: str, limit: int = 10, scan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get token holder data with caching"""
        cache_key = f"holders_{token_address}_{limit}"
        
        if cache_key in self.data_cache:
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "holders",
                "cache_hit": True,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return self.data_cache[cache_key]
        
        try:
            # Get full holder response with total count
            holder_response = await self.birdeye_api.get_token_holders(token_address, limit=limit)
            if holder_response and isinstance(holder_response, dict):
                # Extract holder items for backward compatibility but keep full response
                holder_data = {
                    'items': holder_response.get('items', []),
                    'total': holder_response.get('total', 0),
                    'holder_count': holder_response.get('total', 0)  # Convenience field
                }
                self.data_cache[cache_key] = holder_data
                self.structured_logger.info({
                    "event": "data_fetch",
                    "token_address": token_address,
                    "data_type": "holders",
                    "cache_hit": False,
                    "scan_id": scan_id,
                    "timestamp": int(time.time())
                })
                return holder_data
            else:
                # Return empty structure if API call failed
                empty_data = {'items': [], 'total': 0, 'holder_count': 0}
                self.data_cache[cache_key] = empty_data
                self.structured_logger.info({
                    "event": "data_fetch",
                    "token_address": token_address,
                    "data_type": "holders",
                    "cache_hit": False,
                    "scan_id": scan_id,
                    "timestamp": int(time.time())
                })
                return empty_data
        except Exception as e:
            self.structured_logger.error({
                "event": "data_fetch_error",
                "token_address": token_address,
                "data_type": "holders",
                "error": str(e),
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            self.logger.error(f"Error fetching holders for {token_address}: {e}")
            return {'items': [], 'total': 0, 'holder_count': 0}
    
    async def get_security_data(self, token_address: str, scan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get token security data with caching"""
        cache_key = f"security_{token_address}"
        
        if cache_key in self.data_cache:
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "security_data",
                "cache_hit": True,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return self.data_cache[cache_key]
        
        try:
            security = await self.birdeye_api.get_token_security(token_address)
            self.data_cache[cache_key] = security
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "security_data",
                "cache_hit": False,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return security
        except Exception as e:
            self.structured_logger.error({
                "event": "data_fetch_error",
                "token_address": token_address,
                "data_type": "security_data",
                "error": str(e),
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            self.logger.error(f"Error fetching security data for {token_address}: {e}")
            return None
    
    async def get_all_basic_data(self, token_address: str, scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all basic data needed for initial token scoring.
        Fetches overview, price, and holder data concurrently.
        """
        cache_key = f"basic_data_{token_address}"
        
        if cache_key in self.data_cache:
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "all_basic_data",
                "cache_hit": True,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return self.data_cache[cache_key]
        
        # Fetch basic data concurrently
        overview_task = self.get_overview(token_address, scan_id=scan_id)
        price_task = self.get_price_data(token_address, scan_id=scan_id)
        holders_task = self.get_holder_data(token_address, limit=10, scan_id=scan_id)
        
        overview, price_data, holders = await asyncio.gather(
            overview_task, price_task, holders_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(overview, Exception):
            self.structured_logger.error({
                "event": "data_fetch_error",
                "token_address": token_address,
                "data_type": "overview",
                "error": str(overview),
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            self.logger.error(f"Overview fetch failed for {token_address}: {overview}")
            overview = None
            
        if isinstance(price_data, Exception):
            self.structured_logger.error({
                "event": "data_fetch_error",
                "token_address": token_address,
                "data_type": "price_data",
                "error": str(price_data),
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            self.logger.error(f"Price data fetch failed for {token_address}: {price_data}")
            price_data = None
            
        if isinstance(holders, Exception):
            self.structured_logger.error({
                "event": "data_fetch_error",
                "token_address": token_address,
                "data_type": "holders",
                "error": str(holders),
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            self.logger.error(f"Holders fetch failed for {token_address}: {holders}")
            holders = None
        
        basic_data = {
            'overview': overview,
            'price_data': price_data,
            'holders': holders
        }
        
        self.data_cache[cache_key] = basic_data
        self.structured_logger.info({
            "event": "data_fetch",
            "token_address": token_address,
            "data_type": "all_basic_data",
            "cache_hit": False,
            "scan_id": scan_id,
            "timestamp": int(time.time())
        })
        return basic_data
    
    async def get_full_analysis_data(self, token_address: str, scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all required data for comprehensive token analysis using efficient caching.
        This method centralizes data retrieval to minimize API calls.
        """
        self.structured_logger.info({
            "event": "data_fetch_start",
            "token_address": token_address,
            "data_type": "full_analysis_data",
            "scan_id": scan_id,
            "timestamp": int(time.time())
        })
        self.logger.debug(f"[DATA_MANAGER] Starting full analysis data retrieval for {token_address}")
        
        cache_key = f"full_analysis_data_{token_address}"
        
        # Check cache first
        if cache_key in self.data_cache:
            cache_age = time.time() - self.data_cache[cache_key]['timestamp']
            if cache_age < self.cache_ttl:
                self.logger.debug(f"[DATA_MANAGER] Cache hit for {token_address} (age: {cache_age:.1f}s)")
                self.structured_logger.info({
                    "event": "data_fetch",
                    "token_address": token_address,
                    "data_type": "full_analysis_data",
                    "cache_hit": True,
                    "scan_id": scan_id,
                    "timestamp": int(time.time())
                })
                return self.data_cache[cache_key]['data']
            else:
                self.logger.debug(f"[DATA_MANAGER] Cache expired for {token_address} (age: {cache_age:.1f}s)")
                self.structured_logger.info({
                    "event": "data_fetch",
                    "token_address": token_address,
                    "data_type": "full_analysis_data",
                    "cache_hit": False,
                    "scan_id": scan_id,
                    "timestamp": int(time.time())
                })
        
        self.logger.debug(f"[DATA_MANAGER] Fetching fresh data for {token_address}")
        
        # Initialize result structure
        full_data = {
            'overview': None,
            'price_data': None,
            'trading_data': None,
            'holders': None,
            'top_traders': None,
            'security_data': None,
            'data_freshness': {
                'overview': 'missing',
                'price_data': 'missing',
                'trading_data': 'missing',
                'holders': 'missing',
                'top_traders': 'missing',
                'security_data': 'missing'
            }
        }
        
        # Fetch data concurrently where possible
        try:
            # Core data (always needed)
            self.logger.debug(f"[DATA_MANAGER] Fetching core data (overview + price) for {token_address}")
            overview_task = self.birdeye_api.get_token_overview(token_address)
            price_task = self.birdeye_api.get_historical_price_at_timestamp(token_address, int(time.time()))
            
            overview, price_data = await asyncio.gather(overview_task, price_task, return_exceptions=True)
            
            # Handle overview data
            if isinstance(overview, Exception):
                self.logger.warning(f"[DATA_MANAGER] {token_address} - Overview fetch failed: {overview}")
                full_data['data_freshness']['overview'] = 'failed'
            elif overview:
                full_data['overview'] = overview
                full_data['data_freshness']['overview'] = 'fresh'
                self.logger.debug(f"[DATA_MANAGER] {token_address} - Overview data retrieved: "
                                f"price=${overview.get('price', 'N/A')}, "
                                f"liquidity=${overview.get('liquidity', 'N/A')}, "
                                f"volume_24h=${overview.get('volume', {}).get('h24', 'N/A')}")
            else:
                self.logger.warning(f"[DATA_MANAGER] {token_address} - Overview data is None")
                full_data['data_freshness']['overview'] = 'empty'
            
            # Handle price data
            if isinstance(price_data, Exception):
                self.logger.warning(f"[DATA_MANAGER] {token_address} - Price data fetch failed: {price_data}")
                full_data['data_freshness']['price_data'] = 'failed'
            elif price_data:
                full_data['price_data'] = price_data
                full_data['data_freshness']['price_data'] = 'fresh'
                current_price = price_data.get('current', {}).get('value', 'N/A')
                historical_price = price_data.get('historical_24h', {}).get('price', 'N/A')
                self.logger.debug(f"[DATA_MANAGER] {token_address} - Price data retrieved: "
                                f"current=${current_price}, 24h_ago=${historical_price}")
            else:
                self.logger.warning(f"[DATA_MANAGER] {token_address} - Price data is None")
                full_data['data_freshness']['price_data'] = 'empty'
            
            # Secondary data (fetch if core data is available)
            if full_data['overview']:
                self.logger.debug(f"[DATA_MANAGER] Fetching secondary data for {token_address}")
                
                # Fetch trading data
                try:
                    trading_data = await self.birdeye_api.get_token_trade_metrics(token_address)
                    if trading_data:
                        full_data['trading_data'] = trading_data
                        full_data['data_freshness']['trading_data'] = 'fresh'
                        
                        # Debug: Log trading metrics summary
                        trend_score = trading_data.get('trend_dynamics_score', 0)
                        unique_traders = trading_data.get('unique_trader_count', 0)
                        smart_money = trading_data.get('smart_money_activity', {})
                        
                        self.logger.debug(f"[DATA_MANAGER] {token_address} - Trading data retrieved: "
                                        f"trend_score={trend_score:.3f}, "
                                        f"unique_traders={unique_traders}, "
                                        f"smart_money_detected={any(smart_money.values()) if smart_money else False}")
                    else:
                        full_data['data_freshness']['trading_data'] = 'empty'
                        self.logger.debug(f"[DATA_MANAGER] {token_address} - No trading data available")
                except Exception as e:
                    self.logger.warning(f"[DATA_MANAGER] {token_address} - Trading data fetch failed: {e}")
                    full_data['data_freshness']['trading_data'] = 'failed'
                
                # Fetch holder data
                try:
                    holders = await self.birdeye_api.get_token_holders(token_address, limit=100)
                    if holders:
                        full_data['holders'] = holders
                        full_data['data_freshness']['holders'] = 'fresh'
                        
                        # Debug: Log holder data summary
                        if isinstance(holders, dict):
                            total_holders = holders.get('total', 0)
                            holder_items = holders.get('items', [])
                            self.logger.debug(f"[DATA_MANAGER] {token_address} - Holder data retrieved: "
                                            f"{total_holders} total holders, "
                                            f"{len(holder_items)} detailed records")
                            
                            # Log top holder concentration
                            if holder_items and len(holder_items) > 0:
                                top_holder_pct = holder_items[0].get('percentage', 0) if holder_items[0] else 0
                                self.logger.debug(f"[DATA_MANAGER] {token_address} - Top holder owns {top_holder_pct:.2f}% of supply")
                        elif isinstance(holders, list):
                            self.logger.debug(f"[DATA_MANAGER] {token_address} - Holder data retrieved: {len(holders)} holders (legacy format)")
                    else:
                        full_data['data_freshness']['holders'] = 'empty'
                        self.logger.debug(f"[DATA_MANAGER] {token_address} - No holder data available")
                except Exception as e:
                    self.logger.warning(f"[DATA_MANAGER] {token_address} - Holder data fetch failed: {e}")
                    full_data['data_freshness']['holders'] = 'failed'
                
                # Fetch top traders
                try:
                    top_traders = await self.birdeye_api.get_token_top_traders(token_address, limit=50)
                    if top_traders:
                        full_data['top_traders'] = top_traders
                        full_data['data_freshness']['top_traders'] = 'fresh'
                        self.logger.debug(f"[DATA_MANAGER] {token_address} - Top traders data retrieved: {len(top_traders)} traders")
                        
                        # Debug: Log trading activity summary
                        if top_traders and len(top_traders) > 0:
                            sample_trader = top_traders[0]
                            total_volume = sum(float(trader.get('volume', 0)) for trader in top_traders[:10])
                            self.logger.debug(f"[DATA_MANAGER] {token_address} - Top 10 traders volume: ${total_volume:,.2f}")
                    else:
                        full_data['data_freshness']['top_traders'] = 'empty'
                        self.logger.debug(f"[DATA_MANAGER] {token_address} - No top trader data available")
                except Exception as e:
                    self.logger.warning(f"[DATA_MANAGER] {token_address} - Top trader data fetch failed: {e}")
                    full_data['data_freshness']['top_traders'] = 'failed'
                
                # Fetch security data
                try:
                    security_data = await self.birdeye_api.get_token_security(token_address)
                    if security_data:
                        full_data['security_data'] = security_data
                        full_data['data_freshness']['security_data'] = 'fresh'
                        
                        # Debug: Log security status
                        is_scam = security_data.get('is_scam', False)
                        is_risky = security_data.get('is_risky', False)
                        self.logger.debug(f"[DATA_MANAGER] {token_address} - Security data retrieved: "
                                        f"is_scam={is_scam}, is_risky={is_risky}")
                    else:
                        full_data['data_freshness']['security_data'] = 'empty'
                        self.logger.debug(f"[DATA_MANAGER] {token_address} - No security data available")
                except Exception as e:
                    self.logger.warning(f"[DATA_MANAGER] {token_address} - Security data fetch failed: {e}")
                    full_data['data_freshness']['security_data'] = 'failed'
            else:
                self.logger.warning(f"[DATA_MANAGER] {token_address} - Skipping secondary data fetch due to missing overview")
            
            # Add derived fields from overview to full_data for easier access
            if full_data['overview']:
                overview = full_data['overview']
                
                # Extract key metrics for easy access
                full_data['liquidity'] = overview.get('liquidity', 0)
                full_data['volume'] = overview.get('volume', {})
                full_data['price'] = overview.get('price', 0)
                full_data['priceChange24h'] = overview.get('priceChange24h', 0)
                full_data['marketCap'] = overview.get('marketCap', 0)
                
                self.logger.debug(f"[DATA_MANAGER] {token_address} - Added derived fields for easy access")
            
            # Cache the result
            self.data_cache[cache_key] = {
                'data': full_data,
                'timestamp': time.time()
            }
            
            # Log data completeness summary
            fresh_count = sum(1 for status in full_data['data_freshness'].values() if status == 'fresh')
            total_sources = len(full_data['data_freshness'])
            completeness = fresh_count / total_sources
            
            self.logger.info(f"[DATA_MANAGER] {token_address} - Data retrieval complete:")
            self.logger.info(f"  📊 Data completeness: {fresh_count}/{total_sources} ({completeness:.1%})")
            self.logger.info(f"  🏦 Overview: {full_data['data_freshness']['overview']}")
            self.logger.info(f"  💰 Price Data: {full_data['data_freshness']['price_data']}")
            self.logger.info(f"  📈 Trading Data: {full_data['data_freshness']['trading_data']}")
            self.logger.info(f"  👥 Holders: {full_data['data_freshness']['holders']}")
            self.logger.info(f"  🏪 Top Traders: {full_data['data_freshness']['top_traders']}")
            self.logger.info(f"  🛡️  Security: {full_data['data_freshness']['security_data']}")
            
            self.structured_logger.info({
                "event": "data_fetch",
                "token_address": token_address,
                "data_type": "full_analysis_data",
                "cache_hit": False,
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return full_data
            
        except Exception as e:
            self.logger.error(f"[DATA_MANAGER] Error in full analysis data retrieval for {token_address}: {e}")
            self.structured_logger.error({
                "event": "data_fetch_error",
                "token_address": token_address,
                "data_type": "full_analysis_data",
                "error": str(e),
                "scan_id": scan_id,
                "timestamp": int(time.time())
            })
            return full_data
    
    def _aggregate_ohlcv(self, ohlcv_1m: List[Dict], minutes: int) -> List[Dict]:
        """
        Aggregate 1-minute OHLCV data into larger timeframes to avoid additional API calls.
        
        Args:
            ohlcv_1m: List of 1-minute OHLCV candles
            minutes: Number of minutes for aggregation (5, 15, 60, etc.)
            
        Returns:
            List of aggregated OHLCV candles
        """
        if not ohlcv_1m or minutes <= 1:
            return ohlcv_1m
        
        aggregated = []
        
        # Group candles by time periods
        for i in range(0, len(ohlcv_1m), minutes):
            group = ohlcv_1m[i:i + minutes]
            if not group:
                continue
            
            # Aggregate the group
            aggregated_candle = {
                'unixTime': group[0]['unixTime'],  # Start time of period
                'o': group[0]['o'],                # Open of first candle
                'c': group[-1]['c'],               # Close of last candle
                'h': max(c['h'] for c in group),   # Highest high
                'l': min(c['l'] for c in group),   # Lowest low
                'v': sum(c.get('v', 0) for c in group)  # Sum of volumes
            }
            
            aggregated.append(aggregated_candle)
        
        return aggregated
    
    def get_cached_data_summary(self) -> Dict[str, int]:
        """Get summary of cached data for debugging"""
        summary = {}
        for key in self.data_cache.keys():
            data_type = key.split('_')[0]
            summary[data_type] = summary.get(data_type, 0) + 1
        return summary 

    async def get_token_basic_data(self, token_address: str) -> Dict[str, Any]:
        """
        Get basic token data (overview + price) efficiently.
        This is used for initial screening and quick analysis.
        """
        self.logger.debug(f"[DATA_MANAGER] Fetching basic data for {token_address}")
        
        cache_key = f"basic_data_{token_address}"
        
        # Check cache first
        if cache_key in self.data_cache:
            cache_age = time.time() - self.data_cache[cache_key]['timestamp']
            if cache_age < self.cache_ttl:
                self.logger.debug(f"[DATA_MANAGER] Basic data cache hit for {token_address} (age: {cache_age:.1f}s)")
                return self.data_cache[cache_key]['data']
        
        basic_data = {
            'overview': None,
            'price_data': None,
            'data_quality': 'unknown'
        }
        
        try:
            # Fetch overview and price data concurrently
            self.logger.debug(f"[DATA_MANAGER] Fetching overview and price data for {token_address}")
            overview_task = self.birdeye_api.get_token_overview(token_address)
            price_task = self.birdeye_api.get_historical_price_at_timestamp(token_address, int(time.time()))
            
            overview, price_data = await asyncio.gather(overview_task, price_task, return_exceptions=True)
            
            # Process overview data
            if isinstance(overview, Exception):
                self.logger.warning(f"[DATA_MANAGER] {token_address} - Basic overview fetch failed: {overview}")
                basic_data['data_quality'] = 'failed'
            elif overview:
                basic_data['overview'] = overview
                self.logger.debug(f"[DATA_MANAGER] {token_address} - Basic overview retrieved: "
                                f"price=${overview.get('price', 'N/A')}, "
                                f"liquidity=${overview.get('liquidity', 'N/A'):,.0f}")
            else:
                self.logger.debug(f"[DATA_MANAGER] {token_address} - Basic overview is None")
            
            # Process price data
            if isinstance(price_data, Exception):
                self.logger.warning(f"[DATA_MANAGER] {token_address} - Basic price fetch failed: {price_data}")
            elif price_data:
                basic_data['price_data'] = price_data
                current = price_data.get('current', {}).get('value', 'N/A')
                self.logger.debug(f"[DATA_MANAGER] {token_address} - Basic price data retrieved: current=${current}")
            else:
                self.logger.debug(f"[DATA_MANAGER] {token_address} - Basic price data is None")
            
            # Determine data quality
            if basic_data['overview'] and basic_data['price_data']:
                basic_data['data_quality'] = 'complete'
            elif basic_data['overview']:
                basic_data['data_quality'] = 'partial'
            else:
                basic_data['data_quality'] = 'missing'
            
            # Cache the result
            self.data_cache[cache_key] = {
                'data': basic_data,
                'timestamp': time.time()
            }
            
            self.logger.debug(f"[DATA_MANAGER] {token_address} - Basic data quality: {basic_data['data_quality']}")
            return basic_data
            
        except Exception as e:
            self.logger.error(f"[DATA_MANAGER] Error fetching basic data for {token_address}: {e}")
            basic_data['data_quality'] = 'error'
            return basic_data

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics for monitoring."""
        current_time = time.time()
        cache_stats = {
            'total_keys': len(self.data_cache),
            'fresh_keys': 0,
            'expired_keys': 0,
            'cache_sizes': {},
            'data_types': {},
            'oldest_entry': None,
            'newest_entry': None,
            'memory_usage_estimate': 0
        }
        
        oldest_time = current_time
        newest_time = 0
        
        for cache_key, cache_entry in self.data_cache.items():
            entry_age = current_time - cache_entry['timestamp']
            
            # Track fresh vs expired
            if entry_age < self.cache_ttl:
                cache_stats['fresh_keys'] += 1
            else:
                cache_stats['expired_keys'] += 1
            
            # Track oldest and newest
            if cache_entry['timestamp'] < oldest_time:
                oldest_time = cache_entry['timestamp']
                cache_stats['oldest_entry'] = {'key': cache_key, 'age_seconds': entry_age}
            
            if cache_entry['timestamp'] > newest_time:
                newest_time = cache_entry['timestamp']
                cache_stats['newest_entry'] = {'key': cache_key, 'age_seconds': entry_age}
            
            # Categorize by data type
            if 'full_analysis' in cache_key:
                data_type = 'full_analysis'
            elif 'basic_data' in cache_key:
                data_type = 'basic_data'
            else:
                data_type = 'other'
            
            if data_type not in cache_stats['data_types']:
                cache_stats['data_types'][data_type] = 0
            cache_stats['data_types'][data_type] += 1
            
            # Estimate memory usage (rough calculation)
            try:
                import sys
                entry_size = sys.getsizeof(cache_entry['data'])
                cache_stats['memory_usage_estimate'] += entry_size
                
                if data_type not in cache_stats['cache_sizes']:
                    cache_stats['cache_sizes'][data_type] = 0
                cache_stats['cache_sizes'][data_type] += entry_size
            except:
                pass  # Memory estimation failed, skip
        
        # Calculate hit rate if we're tracking hits
        if hasattr(self, 'cache_hits') and hasattr(self, 'cache_misses'):
            total_requests = self.cache_hits + self.cache_misses
            cache_stats['hit_rate'] = self.cache_hits / total_requests if total_requests > 0 else 0
            cache_stats['total_requests'] = total_requests
            cache_stats['cache_hits'] = self.cache_hits
            cache_stats['cache_misses'] = self.cache_misses
        
        self.logger.debug(f"[DATA_MANAGER] Cache statistics: {cache_stats['fresh_keys']} fresh, "
                        f"{cache_stats['expired_keys']} expired, "
                        f"~{cache_stats['memory_usage_estimate']/1024:.1f}KB total")
        
        return cache_stats

    def reset_cache(self) -> None:
        """Reset the data cache and statistics."""
        cache_size_before = len(self.data_cache)
        self.data_cache.clear()
        
        # Reset hit/miss counters if they exist
        if hasattr(self, 'cache_hits'):
            self.cache_hits = 0
        if hasattr(self, 'cache_misses'):
            self.cache_misses = 0
        
        self.logger.debug(f"[DATA_MANAGER] Cache reset - cleared {cache_size_before} entries")

    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries and return count of removed entries."""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, cache_entry in self.data_cache.items():
            entry_age = current_time - cache_entry['timestamp']
            if entry_age >= self.cache_ttl:
                expired_keys.append(cache_key)
        
        # Remove expired entries
        for key in expired_keys:
            del self.data_cache[key]
        
        if expired_keys:
            self.logger.debug(f"[DATA_MANAGER] Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)

    async def prefetch_data(self, token_addresses: List[str], data_type: str = 'basic') -> Dict[str, str]:
        """
        Prefetch data for multiple tokens to warm the cache.
        
        Args:
            token_addresses: List of token addresses to prefetch
            data_type: Type of data to prefetch ('basic' or 'full')
            
        Returns:
            Dictionary mapping token addresses to prefetch status
        """
        self.logger.debug(f"[DATA_MANAGER] Starting prefetch for {len(token_addresses)} tokens (type: {data_type})")
        
        prefetch_results = {}
        
        # Determine prefetch function
        if data_type == 'full':
            prefetch_func = self.get_full_analysis_data
        else:
            prefetch_func = self.get_token_basic_data
        
        # Create prefetch tasks
        tasks = []
        for address in token_addresses:
            if address:  # Skip empty addresses
                task = asyncio.create_task(prefetch_func(address))
                tasks.append((address, task))
        
        # Execute prefetch tasks with progress tracking
        completed = 0
        for address, task in tasks:
            try:
                await task
                prefetch_results[address] = 'success'
                completed += 1
                
                if completed % 10 == 0:  # Log progress every 10 completions
                    self.logger.debug(f"[DATA_MANAGER] Prefetch progress: {completed}/{len(tasks)} completed")
                    
            except Exception as e:
                prefetch_results[address] = f'failed: {str(e)}'
                self.logger.warning(f"[DATA_MANAGER] Prefetch failed for {address}: {e}")
        
        success_count = sum(1 for status in prefetch_results.values() if status == 'success')
        self.logger.info(f"[DATA_MANAGER] Prefetch completed: {success_count}/{len(token_addresses)} successful")
        
        return prefetch_results 