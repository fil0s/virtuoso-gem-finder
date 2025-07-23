"""
Moralis API Connector for Solana Token Analysis
Comprehensive connector to test Moralis as alternative to Birdeye/other APIs
"""

import aiohttp
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class MoralisAPI:
    """
    🔍 MORALIS API CONNECTOR - Solana Token Analysis
    
    Comprehensive connector to test Moralis capabilities for:
    ✅ Token discovery and metadata (Solana-specific endpoints)
    ✅ Price and market data
    ✅ Trading analytics and volume
    ✅ Holder analysis and distribution
    ✅ Liquidity and DEX data
    ✅ Performance vs existing APIs
    """
    
    def __init__(self, api_key: str, logger: Optional[logging.Logger] = None):
        """Initialize Moralis API connector"""
        self.api_key = api_key
        self.base_url = "https://deep-index.moralis.io/api/v2.2"  # Regular API
        self.solana_gateway_url = "https://solana-gateway.moralis.io"  # Solana Gateway
        self.logger = logger or self._setup_logger()
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0,
            'rate_limit_hits': 0,
            'last_request_time': 0
        }
        
        # Rate limiting for 40,000 CU/day limit
        self.daily_cu_limit = 40000
        self.cu_usage = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'used_cu': 0,
            'requests_today': 0,
            'bonding_requests': 0,
            'graduated_requests': 0
        }
        
        # Session for connection pooling - Create immediately to avoid NoneType errors
        self.session = None
        self._session_headers = {
            'X-API-Key': self.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        self.logger.info("🔍 Moralis API connector initialized (Solana-focused)")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for Moralis connector"""
        logger = logging.getLogger('MoralisAPI')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - 🔍 MORALIS - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def _ensure_session(self):
        """Ensure session is created when needed"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers=self._session_headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def close(self):
        """Close the session manually"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def _check_rate_limit(self, estimated_cu: int = 1) -> bool:
        """Check if request would exceed daily CU limit"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Reset counter if new day
        if self.cu_usage['date'] != today:
            self.cu_usage = {
                'date': today,
                'used_cu': 0,
                'requests_today': 0,
                'bonding_requests': 0,
                'graduated_requests': 0
            }
            self.logger.info(f"🔄 Daily CU usage reset for {today}")
        
        # Check if adding this request would exceed limit
        if self.cu_usage['used_cu'] + estimated_cu > self.daily_cu_limit:
            remaining = self.daily_cu_limit - self.cu_usage['used_cu']
            self.logger.warning(f"🚨 Rate limit check failed: Need {estimated_cu} CU, only {remaining} remaining")
            return False
        
        return True
    
    def _update_cu_usage(self, cu_used: int, endpoint_type: str = 'general'):
        """Update CU usage tracking"""
        self.cu_usage['used_cu'] += cu_used
        self.cu_usage['requests_today'] += 1
        
        if endpoint_type == 'bonding':
            self.cu_usage['bonding_requests'] += 1
        elif endpoint_type == 'graduated':
            self.cu_usage['graduated_requests'] += 1
        
        # Log usage milestones
        usage_pct = (self.cu_usage['used_cu'] / self.daily_cu_limit) * 100
        if usage_pct >= 90:
            self.logger.warning(f"🚨 CU usage at {usage_pct:.1f}% ({self.cu_usage['used_cu']}/{self.daily_cu_limit})")
        elif usage_pct >= 75:
            self.logger.warning(f"⚠️ CU usage at {usage_pct:.1f}% ({self.cu_usage['used_cu']}/{self.daily_cu_limit})")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None, use_solana_gateway: bool = False, estimated_cu: int = 1) -> Optional[Dict]:
        """Make authenticated request to Moralis API with performance tracking and rate limiting"""
        
        # Check rate limit before making request
        if not self._check_rate_limit(estimated_cu):
            self.logger.error(f"❌ Request blocked: Daily CU limit would be exceeded")
            return None

        # Ensure session is created before use - FIX for NoneType error
        await self._ensure_session()
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            if use_solana_gateway:
                url = f"{self.solana_gateway_url}{endpoint}"
            else:
                url = f"{self.base_url}{endpoint}"
            
            self.logger.debug(f"🔍 Moralis request: {url} (Est. {estimated_cu} CU)")
            
            async with self.session.get(url, params=params) as response:
                response_time = time.time() - start_time
                self.stats['total_response_time'] += response_time
                self.stats['last_request_time'] = response_time
                
                if response.status == 200:
                    self.stats['successful_requests'] += 1
                    data = await response.json()
                    
                    # Update CU usage for successful requests
                    endpoint_type = 'bonding' if 'bonding' in endpoint else ('graduated' if 'graduated' in endpoint else 'general')
                    self._update_cu_usage(estimated_cu, endpoint_type)
                    
                    self.logger.debug(f"✅ Moralis success: {url} ({response_time:.2f}s, {estimated_cu} CU)")
                    return data
                elif response.status == 429:
                    self.stats['rate_limit_hits'] += 1
                    self.logger.warning(f"⚠️ Rate limit hit: {url}")
                    return None
                else:
                    self.stats['failed_requests'] += 1
                    error_text = await response.text()
                    self.logger.error(f"❌ Moralis error {response.status}: {url} - {error_text}")
                    return None
                    
        except Exception as e:
            self.stats['failed_requests'] += 1
            self.logger.error(f"❌ Request failed: {endpoint} - {e}")
            return None
    
    # ================================
    # SOLANA TOKEN ENDPOINTS (CORRECT)
    # ================================
    
    async def get_bonding_tokens_by_exchange(self, exchange: str = "pumpfun", limit: int = 100, network: str = "mainnet") -> Optional[List[Dict]]:
        """Get bonding tokens by exchange - Updated with correct endpoint format"""
        try:
            # Based on Moralis documentation, there might not be a direct bonding endpoint
            # Try alternative approaches for pre-graduation tokens
            
            # First try: direct bonding endpoint (if it exists)
            endpoint = f"/token/{network}/exchange/{exchange}/bonding"
            params = {'limit': limit}
            
            result = await self._make_request(endpoint, params, use_solana_gateway=True, estimated_cu=2)
            
            # If bonding endpoint doesn't exist, try alternative endpoints
            if not result:
                self.logger.debug(f"🔍 Direct bonding endpoint not available, trying alternatives...")
                
                # Alternative 1: Try pump.fun specific endpoint variations
                alternative_endpoints = [
                    f"/token/{network}/exchange/{exchange}/tokens",  # General tokens
                    f"/token/{network}/tokens",  # All tokens
                    f"/tokens/{network}/exchange/{exchange}",  # Alternative format
                ]
                
                for alt_endpoint in alternative_endpoints:
                    self.logger.debug(f"🔄 Trying alternative endpoint: {alt_endpoint}")
                    result = await self._make_request(alt_endpoint, params, use_solana_gateway=True, estimated_cu=2)
                    if result:
                        break
            
            # Process result if found
            if result:
                if isinstance(result, list):
                    return self._normalize_bonding_tokens(result)
                elif result.get('result'):
                    return self._normalize_bonding_tokens(result['result'])
            
            # If no direct bonding endpoint works, log and return empty (not an error)
            self.logger.debug(f"📝 No bonding tokens endpoint available for {exchange} on {network}")
            return []
            
        except Exception as e:
            self.logger.error(f"Bonding tokens by exchange failed: {e}")
            return []
    
    async def get_graduated_tokens_by_exchange(self, exchange: str = "pumpfun", limit: int = 100, network: str = "mainnet") -> Optional[List[Dict]]:
        """🎓 Get graduated tokens by exchange - Updated with correct documented format"""
        try:
            # Use the documented endpoint format from Moralis API docs
            # URL: https://docs.moralis.com/web3-data-api/solana/reference/get-graduated-tokens-by-exchange
            endpoint = f"/token/{network}/exchange/{exchange}/graduated"
            params = {
                'exchange': exchange,  # As query parameter per documentation
                'limit': limit
            }
            
            self.logger.debug(f"🎓 Fetching graduated tokens from: {exchange}, limit: {limit}")
            
            result = await self._make_request(endpoint, params, use_solana_gateway=True, estimated_cu=2)
            
            if result:
                if isinstance(result, list):
                    tokens = self._normalize_graduated_tokens(result)
                    self.logger.debug(f"✅ Found {len(tokens)} graduated tokens")
                    return tokens
                elif result.get('result'):
                    tokens = self._normalize_graduated_tokens(result['result'])
                    self.logger.debug(f"✅ Found {len(tokens)} graduated tokens from result")
                    return tokens
            
            self.logger.debug(f"📝 No graduated tokens found for {exchange} on {network}")
            return []
            
        except Exception as e:
            self.logger.error(f"Graduated tokens by exchange failed: {e}")
            return []
    
    async def get_solana_token_metadata(self, token_address: str, network: str = "mainnet") -> Optional[Dict]:
        """Get Solana token metadata using correct endpoint"""
        try:
            # Try individual token metadata if available
            endpoint = f"/solana/token/{token_address}/metadata"
            params = {'network': network}
            
            result = await self._make_request(endpoint, params)
            if result:
                return self._normalize_solana_token_metadata(result)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Solana token metadata failed: {e}")
            return None
    
    async def get_solana_token_price(self, token_address: str, network: str = "mainnet") -> Optional[Dict]:
        """Get Solana token price"""
        try:
            endpoint = f"/solana/token/{token_address}/price"
            params = {'network': network}
            
            result = await self._make_request(endpoint, params)
            if result:
                return self._normalize_solana_price_data(result)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Solana token price failed: {e}")
            return None
    
    async def get_solana_trending_tokens(self, network: str = "mainnet", limit: int = 50) -> Optional[List[Dict]]:
        """Get trending Solana tokens if available"""
        try:
            # Multiple endpoints to try for discovery
            endpoints_to_try = [
                f"/solana/tokens/trending",
                f"/solana/tokens/bonding/pumpfun",
                f"/solana/tokens/top-gainers"
            ]
            
            for endpoint in endpoints_to_try:
                params = {
                    'network': network,
                    'limit': limit
                }
                
                result = await self._make_request(endpoint, params)
                if result and result.get('result'):
                    return self._normalize_trending_tokens(result['result'])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Trending tokens failed: {e}")
            return None
    
    async def get_solana_token_balance(self, wallet_address: str, token_address: str, network: str = "mainnet") -> Optional[Dict]:
        """Get Solana token balance for wallet"""
        try:
            endpoint = f"/solana/account/{wallet_address}/tokens"
            params = {'network': network}
            
            result = await self._make_request(endpoint, params)
            if result and isinstance(result, list):
                # Find specific token in balance list
                for token_balance in result:
                    if token_balance.get('mint') == token_address:
                        return self._normalize_solana_token_balance(token_balance)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Solana token balance failed: {e}")
            return None
    
    async def get_solana_token_transfers(self, token_address: str, network: str = "mainnet", limit: int = 100) -> Optional[List[Dict]]:
        """Get Solana token transfers"""
        try:
            endpoint = f"/solana/token/{token_address}/transfers"
            params = {
                'network': network,
                'limit': limit
            }
            
            result = await self._make_request(endpoint, params)
            if result:
                return self._normalize_solana_transfers(result)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Solana token transfers failed: {e}")
            return None
    
    async def get_solana_wallet_tokens(self, wallet_address: str, network: str = "mainnet") -> Optional[List[Dict]]:
        """Get all tokens in a Solana wallet"""
        try:
            endpoint = f"/solana/account/{wallet_address}/tokens"
            params = {'network': network}
            
            result = await self._make_request(endpoint, params)
            if result:
                return self._normalize_solana_wallet_tokens(result)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Solana wallet tokens failed: {e}")
            return None
    
    async def get_solana_account_info(self, account_address: str, network: str = "mainnet") -> Optional[Dict]:
        """Get Solana account information"""
        try:
            endpoint = f"/solana/account/{account_address}/balance"
            params = {'network': network}
            
            result = await self._make_request(endpoint, params)
            if result:
                return self._normalize_solana_account_info(result)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Solana account info failed: {e}")
            return None
    
    # ================================
    # DATA NORMALIZATION METHODS
    # ================================
    
    def _normalize_solana_token_metadata(self, data: Dict) -> Dict:
        """Normalize Solana token metadata to standard format"""
        return {
            'address': data.get('account', data.get('address', '')),
            'name': data.get('name', ''),
            'symbol': data.get('symbol', ''),
            'decimals': data.get('decimals', 9),
            'supply': data.get('supply', 0),
            'metadata_uri': data.get('metadata_uri', ''),
            'update_authority': data.get('update_authority', ''),
            'mint_authority': data.get('mint_authority', ''),
            'freeze_authority': data.get('freeze_authority', ''),
            'is_mutable': data.get('is_mutable', False),
            'source': 'moralis_solana_metadata'
        }
    
    def _normalize_solana_price_data(self, data: Dict) -> Dict:
        """Normalize Solana price data to standard format"""
        return {
            'price_usd': float(data.get('usdPrice', 0)),
            'price_sol': float(data.get('solPrice', 0)),
            'market_cap': float(data.get('marketCap', 0)),
            'volume_24h': float(data.get('volume24h', 0)),
            'price_change_24h': float(data.get('priceChange24h', 0)),
            'timestamp': data.get('timestamp', ''),
            'source': 'moralis_solana_price'
        }
    
    def _normalize_solana_token_balance(self, data: Dict) -> Dict:
        """Normalize Solana token balance"""
        return {
            'token_address': data.get('mint', ''),
            'balance': float(data.get('amount', 0)),
            'decimals': data.get('decimals', 9),
            'owner': data.get('owner', ''),
            'source': 'moralis_solana_balance'
        }
    
    def _normalize_solana_transfers(self, data: List[Dict]) -> List[Dict]:
        """Normalize Solana transfer data"""
        normalized = []
        transfers = data if isinstance(data, list) else data.get('result', [])
        
        for transfer in transfers:
            normalized.append({
                'signature': transfer.get('signature', ''),
                'slot': transfer.get('slot', 0),
                'block_time': transfer.get('blockTime', 0),
                'fee': transfer.get('fee', 0),
                'status': transfer.get('status', ''),
                'account_keys': transfer.get('accountKeys', []),
                'source': 'moralis_solana_transfers'
            })
        
        return normalized
    
    def _normalize_solana_wallet_tokens(self, data: List[Dict]) -> List[Dict]:
        """Normalize Solana wallet token data"""
        normalized = []
        tokens = data if isinstance(data, list) else data.get('result', [])
        
        for token in tokens:
            normalized.append({
                'mint': token.get('mint', ''),
                'amount': float(token.get('amount', 0)),
                'decimals': token.get('decimals', 9),
                'owner': token.get('owner', ''),
                'name': token.get('name', ''),
                'symbol': token.get('symbol', ''),
                'source': 'moralis_solana_wallet_tokens'
            })
        
        return normalized
    
    def _normalize_solana_account_info(self, data: Dict) -> Dict:
        """Normalize Solana account information"""
        return {
            'address': data.get('address', ''),
            'lamports': data.get('lamports', 0),
            'owner': data.get('owner', ''),
            'executable': data.get('executable', False),
            'rent_epoch': data.get('rentEpoch', 0),
            'data': data.get('data', {}),
            'source': 'moralis_solana_account'
        }
    
    def _normalize_bonding_tokens(self, tokens: List[Dict]) -> List[Dict]:
        """Normalize bonding tokens data (pump.fun, etc.)"""
        normalized = []
        
        for token in tokens:
            normalized.append({
                'token_address': token.get('tokenAddress', ''),
                'name': token.get('name', ''),
                'symbol': token.get('symbol', ''),
                'logo': token.get('logo', ''),
                'decimals': int(token.get('decimals') or 6),  # Handle None values
                'price_native': float(token.get('priceNative') or 0),
                'price_usd': float(token.get('priceUsd') or 0),
                'liquidity': float(token.get('liquidity') or 0),
                'fully_diluted_valuation': float(token.get('fullyDilutedValuation') or 0),
                'bonding_curve_progress': float(token.get('bondingCurveProgress') or 0),
                'market_cap': float(token.get('fullyDilutedValuation') or 0),  # Alias
                'source': 'moralis_bonding_tokens'
            })
        
        return normalized
    
    def _normalize_trending_tokens(self, tokens: List[Dict]) -> List[Dict]:
        """Normalize trending tokens data"""
        return self._normalize_bonding_tokens(tokens)  # Same structure
    
    def _normalize_graduated_tokens(self, tokens: List[Dict]) -> List[Dict]:
        """🎓 Normalize graduated tokens data structure"""
        normalized = []
        
        for token in tokens:
            normalized_token = {
                'token_address': token.get('tokenAddress', ''),
                'name': token.get('name', ''),
                'symbol': token.get('symbol', ''),
                'logo': token.get('logo', ''),
                'decimals': int(token.get('decimals') or 6),  # Handle None values
                'price_native': float(token.get('priceNative') or 0),
                'price_usd': float(token.get('priceUsd') or 0),
                'liquidity': float(token.get('liquidity') or 0),
                'fully_diluted_valuation': float(token.get('fullyDilutedValuation') or 0),
                'bonding_curve_progress': float(token.get('bondingCurveProgress') or 100),  # Should be 100% for graduated
                'graduated_at': token.get('graduatedAt'),  # 🎓 CRITICAL FIELD
                'graduation_timestamp': token.get('graduatedAt'),
                'market_cap': float(token.get('fullyDilutedValuation') or 0),  # Alias
                'stage': 'graduated',
                'source': 'moralis_graduated_tokens'
            }
            
            # Calculate graduation age in hours
            if normalized_token['graduated_at']:
                try:
                    from datetime import datetime
                    grad_time = datetime.fromisoformat(normalized_token['graduated_at'].replace('Z', '+00:00'))
                    now = datetime.now(grad_time.tzinfo)
                    hours_since_graduation = (now - grad_time).total_seconds() / 3600
                    normalized_token['hours_since_graduation'] = hours_since_graduation
                    normalized_token['is_fresh_graduate'] = hours_since_graduation <= 1  # Fresh if < 1 hour
                    normalized_token['is_recent_graduate'] = hours_since_graduation <= 24  # Recent if < 24 hours
                except Exception as e:
                    normalized_token['hours_since_graduation'] = 999
                    normalized_token['is_fresh_graduate'] = False
                    normalized_token['is_recent_graduate'] = False
            else:
                normalized_token['hours_since_graduation'] = 999
                normalized_token['is_fresh_graduate'] = False
                normalized_token['is_recent_graduate'] = False
            
            normalized.append(normalized_token)
        
        return normalized
    
    def get_performance_stats(self) -> Dict:
        """Get API performance statistics"""
        total_requests = self.stats['total_requests']
        
        return {
            'total_requests': total_requests,
            'successful_requests': self.stats['successful_requests'],
            'failed_requests': self.stats['failed_requests'],
            'success_rate': (self.stats['successful_requests'] / total_requests * 100) if total_requests > 0 else 0,
            'average_response_time': (self.stats['total_response_time'] / total_requests) if total_requests > 0 else 0,
            'rate_limit_hits': self.stats['rate_limit_hits'],
            'last_request_time': self.stats['last_request_time']
        }
    
    def get_cu_usage_stats(self) -> Dict:
        """Get CU (Compute Units) usage statistics for rate limiting"""
        usage_pct = (self.cu_usage['used_cu'] / self.daily_cu_limit) * 100
        remaining_cu = self.daily_cu_limit - self.cu_usage['used_cu']
        
        return {
            'date': self.cu_usage['date'],
            'used_cu': self.cu_usage['used_cu'],
            'daily_limit': self.daily_cu_limit,
            'remaining_cu': remaining_cu,
            'usage_percentage': usage_pct,
            'requests_today': self.cu_usage['requests_today'],
            'bonding_requests': self.cu_usage['bonding_requests'],
            'graduated_requests': self.cu_usage['graduated_requests'],
            'rate_limit_status': 'CRITICAL' if usage_pct >= 90 else ('WARNING' if usage_pct >= 75 else 'OK')
        }
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0,
            'rate_limit_hits': 0,
            'last_request_time': 0
        }
    
    async def test_api_connectivity(self) -> Dict:
        """Test basic API connectivity and capabilities"""
        self.logger.info("🔍 Testing Moralis API connectivity...")
        
        test_results = {
            'api_version': None,
            'authentication_valid': False,
            'solana_support': False,
            'endpoint_availability': {},
            'performance_metrics': {}
        }
        
        try:
            # Test API version endpoint
            version_result = await self._make_request("/web3/version")
            if version_result:
                test_results['api_version'] = version_result
                test_results['authentication_valid'] = True
                self.logger.info("✅ Authentication valid")
            
            # Test key endpoints for early gem detection
            test_endpoints = {
                'token_metadata': '/solana/account/metadata',
                'token_price': '/solana/account/price',
                'trending_tokens': '/market-data/erc20s/top-gainers',
                'endpoint_weights': '/info/endpointWeights'
            }
            
            for name, endpoint in test_endpoints.items():
                try:
                    result = await self._make_request(endpoint)
                    test_results['endpoint_availability'][name] = bool(result)
                    if result:
                        self.logger.info(f"✅ {name} endpoint available")
                    else:
                        self.logger.warning(f"⚠️ {name} endpoint not available")
                except:
                    test_results['endpoint_availability'][name] = False
                    self.logger.warning(f"❌ {name} endpoint failed")
            
            # Get performance metrics
            test_results['performance_metrics'] = self.get_performance_stats()
            
            return test_results
            
        except Exception as e:
            self.logger.error(f"API connectivity test failed: {e}")
            test_results['error'] = str(e)
            return test_results 