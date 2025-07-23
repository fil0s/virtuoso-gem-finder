import asyncio
import logging
import time
import aiohttp
import json
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError, retry_if_exception_type
from dataclasses import dataclass

from core.cache_manager import CacheManager
from services.rate_limiter_service import RateLimiterService
from utils.exceptions import APIConnectionError, APIDataError, APIError
from utils.structured_logger import get_structured_logger

# Define namespace constant locally
BIRDEYE_API_NAMESPACE = "birdeye"

class BirdeyeAPI:
    API_DOMAIN = "birdeye" 

    def __init__(self, 
                 config: Dict[str, Any], 
                 logger: logging.Logger, 
                 cache_manager: CacheManager, 
                 rate_limiter: RateLimiterService):
        
        self.config = config
        self.logger = logger
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter
        
        self.api_key = self.config.get('api_key')
        self.base_url = self.config.get('base_url', 'https://public-api.birdeye.so')

        # Enhanced API key validation
        self._validate_api_key()
        
        self.headers = {"X-API-KEY": self.api_key if self.api_key else ""}
        
        self.default_ttl = self.config.get('cache_ttl_default_seconds', 300) 
        self.error_ttl = self.config.get('cache_ttl_error_seconds', 60)
        
        # Maximum retry attempts for critical functions
        self.max_retries = self.config.get('max_retries', 3)
        self.backoff_factor = self.config.get('backoff_factor', 2)
        
        # Resource management
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_timeout = aiohttp.ClientTimeout(
            total=self.config.get('request_timeout_seconds', 20),
            connect=10
        )
        self._closed = False
        
        # Rate limiting - Conservative settings for BirdEye starter plan (15 RPS = 900 RPM)
        self.rate_limit = self.config.get('rate_limit', 800)  # requests per minute (conservative)
        self.request_interval = 60.0 / self.rate_limit
        self.last_request_time = 0
        
        # Log initialization info after rate limit is set
        self.logger.info(f"🚀 BirdeyeAPI initialized successfully!")
        self.logger.info(f"  📡 Base URL: {self.base_url}")
        self.logger.info(f"  🔐 API Key Status: {'✅ Loaded' if self.api_key else '❌ Not Set'}")
        self.logger.info(f"  ⚡ Rate Limit: {self.rate_limit} requests/minute")
        self.logger.info(f"  🕒 Request Timeout: {self.config.get('request_timeout_seconds', 20)}s")
        
        # Performance metrics for monitoring
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'rate_limit_hits': 0,
            'average_response_time': 0.0,
            'response_times': [],
            'last_reset': time.time()
        }
        
        # Enhanced API call tracking
        self.api_call_tracker = {
            'total_api_calls': 0,
            'successful_api_calls': 0,
            'failed_api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'calls_by_endpoint': {},
            'calls_by_status_code': {},
            'total_response_time_ms': 0,
            'session_start_time': time.time(),
            'last_reset_time': time.time()
        }
        
        # Initialize BirdEye cost calculator for accurate cost tracking
        try:
            from api.birdeye_cost_calculator import BirdEyeCostCalculator
            self.cost_calculator = BirdEyeCostCalculator(self.logger)
            self.logger.info("🧮 BirdEye cost calculator initialized - tracking compute units")
        except ImportError as e:
            self.logger.warning(f"BirdEye cost calculator not available: {e}")
            self.cost_calculator = None
        
        # Initialize batch manager for intelligent API optimization
        self.batch_manager = None
        self._init_batch_manager()
        
        self.structured_logger = get_structured_logger('BirdeyeAPI')
        
        # Initialize token exclusion system
        self._init_token_exclusion()
    
    def _init_token_exclusion(self) -> None:
        """Initialize the token exclusion system to prevent API calls for excluded tokens"""
        try:
            from services.early_token_detection import is_major_token, MAJOR_TOKENS_TO_EXCLUDE
            self.is_major_token = is_major_token
            self.excluded_tokens = MAJOR_TOKENS_TO_EXCLUDE
            self.logger.info(f"🚫 Token exclusion initialized - {len(self.excluded_tokens)} tokens excluded from API calls")
        except ImportError as e:
            self.logger.warning(f"Token exclusion system not available: {e}")
            self.is_major_token = lambda x: False
            self.excluded_tokens = set()
    
    def _should_skip_token(self, token_address: str) -> bool:
        """Check if a token should be skipped due to exclusion rules"""
        if not token_address:
            return True
            
        if self.is_major_token(token_address):
            self.logger.debug(f"🚫 Skipping excluded token: {token_address}")
            return True
            
        return False
    
    def _validate_api_key(self) -> None:
        """Enhanced API key validation with detailed feedback"""
        if not self.api_key:
            self.logger.error("❌ CRITICAL: BirdEye API key is not set!")
            self.logger.error("   Please check your configuration file or environment variables.")
            self.logger.error("   Expected: BIRDEYE_API_KEY environment variable or api_key in config")
            return
            
        # Basic format validation
        if len(self.api_key) < 20:
            self.logger.warning("⚠️  API key appears too short - this may cause authentication failures")
            
        # Check for common issues
        if self.api_key.startswith('sk-') or self.api_key.startswith('pk-'):
            self.logger.warning("⚠️  API key format may be incorrect for BirdEye (starts with sk-/pk-)")
            
        # Security: Mask API key in logs
        if len(self.api_key) > 16:
            masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"
        else:
            masked_key = "***MASKED***"
        self.logger.info(f"🔑 BirdEye API key loaded: {masked_key}")
        
    async def _handle_authentication_error(self, endpoint: str, response_status: int, response_text: str) -> None:
        """Handle 401 authentication errors with detailed diagnostics"""
        self.logger.error(f"🚫 AUTHENTICATION FAILED for {endpoint}")
        self.logger.error(f"   Status Code: {response_status}")
        self.logger.error(f"   Response: {response_text[:200]}")
        
        # Provide specific troubleshooting guidance
        if not self.api_key:
            self.logger.error("   ❌ No API key configured!")
            self.logger.error("   🔧 Fix: Set BIRDEYE_API_KEY environment variable")
        else:
            masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}" if len(self.api_key) > 16 else "***MASKED***"
            self.logger.error(f"   🔑 API Key: {masked_key}")
            self.logger.error("   🔧 Possible fixes:")
            self.logger.error("      - Check if API key is valid and not expired")
            self.logger.error("      - Verify API key has correct permissions")
            self.logger.error("      - Check if rate limits have been exceeded")
            self.logger.error("      - Ensure API key format is correct for BirdEye")
            
        # Log headers being sent (without sensitive data)
        safe_headers = {}
        for key, value in self.headers.items():
            if key.upper() in ['X-API-KEY', 'AUTHORIZATION']:
                if value:
                    safe_headers[key] = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***MASKED***"
                else:
                    safe_headers[key] = "***NOT_SET***"
            else:
                safe_headers[key] = value
        self.logger.error(f"   📋 Headers sent: {safe_headers}")

    def _get_rate_limit_domain(self, endpoint: str) -> str:
        """
        Get the appropriate rate limiting domain based on the endpoint.
        
        Wallet API endpoints have special rate limits (30 RPM) according to BirdEye docs:
        https://docs.birdeye.so/docs/rate-limiting
        """
        wallet_endpoints = [
            '/v1/wallet/tx-list',
            '/v1/wallet/token-list', 
            '/v1/wallet/token_list',
            '/v1/wallet/multichain-token-list',
            '/v1/wallet/token-balance',
            '/v1/wallet/multichain-tx-list',
            '/v1/wallet/simulate'
        ]
        
        if any(endpoint.startswith(wallet_ep) for wallet_ep in wallet_endpoints):
            return "birdeye_wallet"
        else:
            return self.API_DOMAIN
        
    def _init_batch_manager(self):
        """Initialize the batch manager for intelligent API batching"""
        try:
            from api.batch_api_manager import BatchAPIManager
            self.batch_manager = BatchAPIManager(self, self.logger)
            self.logger.info("🚀 BatchAPIManager initialized - intelligent batching enabled")
        except ImportError as e:
            self.logger.warning(f"BatchAPIManager not available: {e}")
            self.batch_manager = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper resource management"""
        if self._closed:
            raise RuntimeError("BirdeyeAPI has been closed")
            
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,  # Increase maximum number of connections
                limit_per_host=20,  # Increase connections per host for better throughput
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=60,  # Increase keepalive for better connection reuse
                enable_cleanup_closed=True  # Clean up closed connections
            )
            
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=self._session_timeout,
                connector=connector,
                raise_for_status=False  # We'll handle status codes manually
            )
            self.logger.debug("Created new aiohttp session for BirdeyeAPI")
            
        return self._session

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), 
           stop=stop_after_attempt(3), 
           retry=retry_if_exception_type((APIConnectionError, aiohttp.ClientError)),
           reraise=True)
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, custom_headers: Optional[Dict[str, str]] = None, scan_id: Optional[str] = None) -> Any:
        """Make HTTP request using aiohttp with proper error handling and resource management"""
        if self._closed:
            raise RuntimeError("BirdeyeAPI has been closed")
            
        if not self.base_url:
            raise APIConnectionError(api_name=self.API_DOMAIN, message="Base URL not configured")

        url = f"{self.base_url}{endpoint}"
        
        # Apply rate limiting - use special domain for wallet endpoints
        rate_limit_domain = self._get_rate_limit_domain(endpoint)
        await self.rate_limiter.wait_for_slot(rate_limit_domain)
        
        session = await self._get_session()
        request_headers = dict(self.headers)
        if custom_headers:
            request_headers.update(custom_headers)
        
        try:
            self.logger.debug(f"Making BirdEye request to: {url} with params: {params}")
            
            # Track performance metrics
            request_start_time = time.time()
            # SECURITY FIX: Mask API key in logs to prevent exposure
            safe_headers = {}
            for key, value in request_headers.items():
                if key.upper() in ['X-API-KEY', 'API-KEY', 'AUTHORIZATION']:
                    if value:
                        safe_headers[key] = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***MASKED***"
                    else:
                        safe_headers[key] = "***NOT_SET***"
                else:
                    safe_headers[key] = value
            
            # Enhanced request logging with masked sensitive data
            self.logger.info(f"🔗 API Request: {endpoint}")
            self.logger.info(f"  📋 Headers: {safe_headers}")
            if params:
                self.logger.info(f"  📊 Params: {params}")
            
            async with session.get(url, params=params, headers=request_headers) as response:
                response_time_ms = int((time.time() - request_start_time) * 1000)
                
                # Track API call metrics (default to 1 token for individual calls)
                self._track_api_call(endpoint, response.status, response_time_ms, num_tokens=1, is_batch=False)
                
                log_data = {
                    "event": "api_call",
                    "endpoint": endpoint,
                    "params": params,
                    "scan_id": scan_id,
                    "status_code": response.status,
                    "response_time_ms": response_time_ms
                }
                if response.status == 200:
                    self.structured_logger.info({**log_data, "result": "success"})
                else:
                    self.structured_logger.warning({**log_data, "result": "error"})
                
                # Log response headers that might be useful (without sensitive data)
                useful_headers = {}
                for header_name in ['content-type', 'x-ratelimit-remaining', 'x-ratelimit-reset', 'server']:
                    if header_name in response.headers:
                        useful_headers[header_name] = response.headers[header_name]
                
                if useful_headers:
                    self.logger.debug(f"  📋 Response headers: {useful_headers}")
                
                # Handle different status codes
                if response.status == 200:
                    try:
                        response_data = await response.json()
                        
                        # Enhanced success logging with comprehensive data summary
                        data_summary = ""
                        
                        # 🔍 ENHANCED DEBUG LOGGING - DISABLED FOR PRODUCTION
                        # self.logger.info(f"🔍 ENHANCED DEBUG - Detailed API Response Analysis for {endpoint}:")
                        
                        if isinstance(response_data, dict):
                            # Only basic logging for production
                            # self.logger.info(f"  📦 Response Type: Dictionary with {len(response_data)} top-level keys")
                            # self.logger.info(f"  🔑 Top-level Keys: {list(response_data.keys())}")
                            
                            # Special handling for common response structures
                            if 'data' in response_data:
                                data = response_data['data']
                                if isinstance(data, list):
                                    data_summary = f"data array with {len(data)} items"
                                elif isinstance(data, dict):
                                    data_summary = f"data object with keys: {list(data.keys())[:5]}"
                                else:
                                    data_summary = f"data {type(data).__name__}"
                            elif 'tokens' in response_data:
                                tokens = response_data['tokens']
                                if isinstance(tokens, list):
                                    data_summary = f"tokens array with {len(tokens)} items"
                            else:
                                data_summary = f"object with keys: {list(response_data.keys())[:5]}"
                                
                        elif isinstance(response_data, list):
                            data_summary = f"array with {len(response_data)} items"
                        else:
                            data_summary = f"{type(response_data).__name__}"
                        
                        self.logger.info(f"✅ Success: {endpoint} - {data_summary}")
                        
                        # Log first 100 chars for debugging (without sensitive data)
                        preview = str(response_data)[:100]
                        # Remove any potential sensitive data from preview
                        preview = re.sub(r'["\']?(?:api[_-]?key|authorization|secret)["\']?\s*:\s*["\'][^"\']{8,}["\']', 
                                       '"***MASKED***"', preview, flags=re.IGNORECASE)
                        self.logger.debug(f"  📊 Response preview: {preview}...")
                        
                        return response_data
                    except aiohttp.ContentTypeError as e:
                        text_content = await response.text()
                        self.logger.error(f"❌ Invalid JSON response from {endpoint}: {text_content[:500]}")
                        raise APIDataError(api_name=self.API_DOMAIN, message=f"Invalid JSON response: {e}")
                        
                elif response.status == 401:
                    # Authentication error - provide detailed diagnostics
                    text_content = await response.text()
                    await self._handle_authentication_error(endpoint, response.status, text_content)
                    raise APIDataError(
                        api_name=self.API_DOMAIN,
                        message=f"Authentication failed: {text_content[:200]}",
                        status_code=401
                    )
                    
                elif response.status in [400, 404, 555]:
                    # Suppress these common API errors but provide more context
                    text_content = await response.text()
                    self.logger.info(f"⚠️  API Error {response.status} for {endpoint}: {text_content[:200]}")
                    return None
                    
                elif response.status == 429:
                    # Rate limit hit - provide actionable information
                    text_content = await response.text()
                    reset_time = response.headers.get('x-ratelimit-reset', 'unknown')
                    remaining = response.headers.get('x-ratelimit-remaining', 'unknown')
                    
                    self.logger.warning(f"🚫 Rate limit hit (429) for {endpoint}")
                    self.logger.warning(f"  ⏰ Reset time: {reset_time}")
                    self.logger.warning(f"  📊 Remaining: {remaining}")
                    
                    raise APIConnectionError(
                        api_name=self.API_DOMAIN, 
                        message=f"Rate limit hit: reset={reset_time}, remaining={remaining}", 
                        status_code=429
                    )
                    
                elif response.status in [500, 502, 503, 504]:
                    # Server errors - retry with enhanced logging
                    text_content = await response.text()
                    self.logger.warning(f"🔴 Server error {response.status} for {endpoint}: {text_content[:200]}")
                    raise APIConnectionError(
                        api_name=self.API_DOMAIN,
                        message=f"Server error {response.status}: {text_content[:200]}",
                        status_code=response.status
                    )
                    
                else:
                    # Other errors with enhanced context
                    text_content = await response.text()
                    self.logger.error(f"💥 HTTP {response.status} for {endpoint}: {text_content[:200]}")
                    raise APIDataError(
                        api_name=self.API_DOMAIN,
                        message=f"HTTP {response.status}: {text_content[:200]}",
                        status_code=response.status
                    )
                    
        except Exception as e:
            self.structured_logger.error({"event": "api_call_exception", "endpoint": endpoint, "params": params, "scan_id": scan_id, "error": str(e)})
            self.logger.error(f"🔌 Client error for BirdEye {endpoint}: {e}")
            raise APIConnectionError(api_name=self.API_DOMAIN, message=f"Client error: {e}")
        except asyncio.TimeoutError as e:
            self.logger.error(f"⏰ Timeout error for BirdEye {endpoint}: {e}")
            raise APIConnectionError(api_name=self.API_DOMAIN, message=f"Request timeout: {e}")

    def _track_api_call(self, endpoint: str, status_code: int, response_time_ms: int, num_tokens: int = 1, is_batch: bool = False) -> None:
        """
        Track API call metrics for comprehensive monitoring including compute unit costs.
        
        Args:
            endpoint: The API endpoint called
            status_code: HTTP status code returned
            response_time_ms: Response time in milliseconds
            num_tokens: Number of tokens processed (for cost calculation)
            is_batch: Whether this was a batch call
        """
        # Update total counters
        self.api_call_tracker['total_api_calls'] += 1
        self.api_call_tracker['total_response_time_ms'] += response_time_ms
        
        # Track compute unit costs if calculator is available
        if self.cost_calculator and status_code == 200:
            compute_units = self.cost_calculator.track_api_call(endpoint, num_tokens, is_batch)
            self.logger.debug(f"💰 Cost tracking: {endpoint} with {num_tokens} tokens = {compute_units} CUs")
        
        # Track success/failure
        if status_code == 200:
            self.api_call_tracker['successful_api_calls'] += 1
        else:
            self.api_call_tracker['failed_api_calls'] += 1
        
        # Create endpoint key that includes batch information for better tracking
        endpoint_key = endpoint
        if is_batch and num_tokens > 1:
            endpoint_key = f"{endpoint} [BATCH-{num_tokens}]"
        
        # Track by endpoint (including batch info)
        if endpoint_key not in self.api_call_tracker['calls_by_endpoint']:
            self.api_call_tracker['calls_by_endpoint'][endpoint_key] = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'avg_response_time_ms': 0,
                'total_response_time_ms': 0,
                'is_batch': is_batch,
                'tokens_processed': 0
            }
        
        endpoint_stats = self.api_call_tracker['calls_by_endpoint'][endpoint_key]
        endpoint_stats['total'] += 1
        endpoint_stats['tokens_processed'] += num_tokens
        endpoint_stats['total_response_time_ms'] += response_time_ms
        endpoint_stats['avg_response_time_ms'] = endpoint_stats['total_response_time_ms'] / endpoint_stats['total']
        
        if status_code == 200:
            endpoint_stats['successful'] += 1
        else:
            endpoint_stats['failed'] += 1
        
        # Also track the base endpoint without batch info for compatibility
        if endpoint not in self.api_call_tracker['calls_by_endpoint']:
            self.api_call_tracker['calls_by_endpoint'][endpoint] = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'avg_response_time_ms': 0,
                'total_response_time_ms': 0,
                'is_batch': False,
                'tokens_processed': 0
            }
        
        base_endpoint_stats = self.api_call_tracker['calls_by_endpoint'][endpoint]
        base_endpoint_stats['total'] += 1
        base_endpoint_stats['tokens_processed'] += num_tokens
        base_endpoint_stats['total_response_time_ms'] += response_time_ms
        base_endpoint_stats['avg_response_time_ms'] = base_endpoint_stats['total_response_time_ms'] / base_endpoint_stats['total']
        
        if status_code == 200:
            base_endpoint_stats['successful'] += 1
        else:
            base_endpoint_stats['failed'] += 1
        
        # Track by status code
        if status_code not in self.api_call_tracker['calls_by_status_code']:
            self.api_call_tracker['calls_by_status_code'][status_code] = 0
        self.api_call_tracker['calls_by_status_code'][status_code] += 1
        
        # Update legacy performance metrics for backward compatibility
        self.performance_metrics['total_requests'] += 1
        if status_code == 200:
            self.performance_metrics['successful_requests'] += 1
        else:
            self.performance_metrics['failed_requests'] += 1
        
        # Update response times
        response_time_seconds = response_time_ms / 1000.0
        self.performance_metrics['response_times'].append(response_time_seconds)
        if len(self.performance_metrics['response_times']) > 100:
            self.performance_metrics['response_times'] = self.performance_metrics['response_times'][-100:]
        
        # Calculate average response time
        if self.performance_metrics['response_times']:
            self.performance_metrics['average_response_time'] = sum(self.performance_metrics['response_times']) / len(self.performance_metrics['response_times'])

    def _track_cache_hit(self, cache_key: str) -> None:
        """Track cache hit for API call metrics."""
        self.api_call_tracker['cache_hits'] += 1
        self.performance_metrics['cache_hits'] += 1
        self.logger.debug(f"📋 Cache hit tracked: {cache_key}")

    def _track_cache_miss(self, cache_key: str) -> None:
        """Track cache miss for API call metrics."""
        self.api_call_tracker['cache_misses'] += 1
        self.logger.debug(f"📋 Cache miss tracked: {cache_key}")

    async def close_session(self) -> None:
        """Properly close the aiohttp session and clean up resources"""
        if self._closed:
            self.logger.debug("BirdeyeAPI already closed")
            return
            
        self._closed = True
        
        if self._session and not self._session.closed:
            try:
                # Set a shorter timeout for closing to prevent hanging
                timeout = aiohttp.ClientTimeout(total=5.0)  # 5 second timeout for cleanup
                
                # Close the session with timeout
                await asyncio.wait_for(self._session.close(), timeout=5.0)
                
                # Wait for underlying connections to close with timeout
                await asyncio.wait_for(asyncio.sleep(0.25), timeout=1.0)
                
                self.logger.info("BirdeyeAPI session closed and resources cleaned up")
            except asyncio.TimeoutError:
                self.logger.warning("Session close timed out - forcing cleanup")
                # Force close without waiting
                if not self._session.closed:
                    try:
                        self._session._connector.close()
                    except Exception as e:
                        self.logger.debug(f"Error during force close: {e}")
            except Exception as e:
                self.logger.error(f"Error closing BirdeyeAPI session: {e}")
                # Try to force close the connector
                try:
                    if hasattr(self._session, '_connector') and self._session._connector:
                        self._session._connector.close()
                except Exception as force_error:
                    self.logger.debug(f"Error during force connector close: {force_error}")
        else:
            self.logger.debug("No active session to close")
            
        # Clear the session reference
        self._session = None

    async def close(self) -> None:
        """Public close method for external cleanup calls"""
        await self.close_session()

    def __del__(self):
        """Cleanup in destructor as safety net"""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            self.logger.warning("BirdeyeAPI session not properly closed - cleaning up in destructor")
            # Note: Can't use await in __del__, so we just log the warning

    async def _make_request_with_retry(self, endpoint: str, params: Optional[Dict[str, Any]] = None, custom_headers: Optional[Dict[str, str]] = None, max_retries: int = None) -> Any:
        """Enhanced request method with customizable retry logic"""
        if max_retries is None:
            max_retries = self.max_retries
            
        last_error = None
        for attempt in range(max_retries):
            try:
                return await self._make_request(endpoint, params, custom_headers)
            except (APIConnectionError, APIDataError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    self.logger.warning(f"Retry {attempt+1}/{max_retries} for {endpoint} after {wait_time}s. Error: {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"All {max_retries} retries failed for {endpoint}. Last error: {str(e)}")
        
        # If all retries failed
        if last_error:
            raise last_error
        return None

    async def _make_request_batch_aware(self, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                                      num_tokens: int = 1, custom_headers: Optional[Dict[str, str]] = None) -> Any:
        """
        Make HTTP request with batch-aware cost tracking.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            num_tokens: Number of tokens in the request (for cost calculation)
            custom_headers: Optional custom headers
            
        Returns:
            API response data
        """
        if self._closed:
            raise RuntimeError("BirdeyeAPI has been closed")
            
        if not self.base_url:
            raise APIConnectionError(api_name=self.API_DOMAIN, message="Base URL not configured")

        url = f"{self.base_url}{endpoint}"
        is_batch = num_tokens > 1
        
        # Apply rate limiting - use special domain for wallet endpoints
        rate_limit_domain = self._get_rate_limit_domain(endpoint)
        await self.rate_limiter.wait_for_slot(rate_limit_domain)
        
        session = await self._get_session()
        request_headers = dict(self.headers)
        if custom_headers:
            request_headers.update(custom_headers)
        
        try:
            self.logger.debug(f"Making batch-aware BirdEye request to: {url} with params: {params}")
            
            # Track performance metrics
            request_start_time = time.time()
            
            # Enhanced request logging with masked sensitive data
            safe_headers = {}
            for key, value in request_headers.items():
                if key.upper() in ['X-API-KEY', 'API-KEY', 'AUTHORIZATION']:
                    if value:
                        safe_headers[key] = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***MASKED***"
                    else:
                        safe_headers[key] = "***NOT_SET***"
                else:
                    safe_headers[key] = value
            
            batch_info = f" [BATCH: {num_tokens} tokens]" if is_batch else " [INDIVIDUAL]"
            self.logger.info(f"🔗 API Request: {endpoint}{batch_info}")
            self.logger.debug(f"  📋 Headers: {safe_headers}")
            if params:
                self.logger.debug(f"  📊 Params: {params}")
            
            async with session.get(url, params=params, headers=request_headers) as response:
                response_time_ms = int((time.time() - request_start_time) * 1000)
                
                # Track API call metrics with proper batch information
                self._track_api_call(endpoint, response.status, response_time_ms, num_tokens=num_tokens, is_batch=is_batch)
                
                # Handle different status codes
                if response.status == 200:
                    try:
                        response_data = await response.json()
                        
                        # Enhanced success logging
                        data_summary = ""
                        if isinstance(response_data, dict):
                            if 'data' in response_data:
                                data = response_data['data']
                                if isinstance(data, list):
                                    data_summary = f"data array with {len(data)} items"
                                elif isinstance(data, dict):
                                    data_summary = f"data object with {len(data)} keys"
                                else:
                                    data_summary = f"data {type(data).__name__}"
                            else:
                                data_summary = f"object with {len(response_data)} keys"
                        elif isinstance(response_data, list):
                            data_summary = f"array with {len(response_data)} items"
                        else:
                            data_summary = f"{type(response_data).__name__}"
                        
                        batch_info = f" [BATCH: {num_tokens} tokens]" if is_batch else ""
                        self.logger.info(f"✅ Success: {endpoint}{batch_info} - {data_summary}")
                        
                        return response_data
                        
                    except aiohttp.ContentTypeError as e:
                        text_content = await response.text()
                        self.logger.error(f"❌ Invalid JSON response from {endpoint}: {text_content[:500]}")
                        raise APIDataError(api_name=self.API_DOMAIN, message=f"Invalid JSON response: {e}")
                        
                elif response.status == 401:
                    # Authentication error
                    text_content = await response.text()
                    await self._handle_authentication_error(endpoint, response.status, text_content)
                    raise APIDataError(
                        api_name=self.API_DOMAIN,
                        message=f"Authentication failed: {text_content[:200]}",
                        status_code=401
                    )
                    
                elif response.status in [400, 404, 555]:
                    # Common API errors
                    text_content = await response.text()
                    self.logger.info(f"⚠️  API Error {response.status} for {endpoint}: {text_content[:200]}")
                    return None
                    
                elif response.status == 429:
                    # Rate limit hit
                    text_content = await response.text()
                    reset_time = response.headers.get('x-ratelimit-reset', 'unknown')
                    remaining = response.headers.get('x-ratelimit-remaining', 'unknown')
                    
                    self.logger.warning(f"🚫 Rate limit hit (429) for {endpoint}")
                    self.logger.warning(f"  ⏰ Reset time: {reset_time}")
                    self.logger.warning(f"  📊 Remaining: {remaining}")
                    
                    raise APIConnectionError(
                        api_name=self.API_DOMAIN, 
                        message=f"Rate limit hit: reset={reset_time}, remaining={remaining}", 
                        status_code=429
                    )
                    
                else:
                    # Other errors
                    text_content = await response.text()
                    self.logger.error(f"💥 HTTP {response.status} for {endpoint}: {text_content[:200]}")
                    raise APIDataError(
                        api_name=self.API_DOMAIN,
                        message=f"HTTP {response.status}: {text_content[:200]}",
                        status_code=response.status
                    )
                    
        except Exception as e:
            self.logger.error(f"🔌 Client error for BirdEye {endpoint}: {e}")
            raise APIConnectionError(api_name=self.API_DOMAIN, message=f"Client error: {e}")
        except asyncio.TimeoutError as e:
            self.logger.error(f"⏰ Timeout error for BirdEye {endpoint}: {e}")
            raise APIConnectionError(api_name=self.API_DOMAIN, message=f"Request timeout: {e}")

    async def get_token_overview(self, token_address: str) -> Optional[Dict[str, Any]]:
        # Check if token should be excluded
        if self._should_skip_token(token_address):
            return None
            
        cache_key = f"{BIRDEYE_API_NAMESPACE}_overview_{token_address}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self._track_cache_hit(cache_key)
            self.logger.debug(f"Cache hit for Birdeye token_overview: {cache_key}")
            return cached_data
            
        # Track cache miss
        self._track_cache_miss(cache_key)
        self.logger.debug(f"[API] Fetching Birdeye token overview for {token_address}")
        endpoint = "/defi/token_overview" 
        params = {"address": token_address}
        
        try:
            response_data = await self._make_request_with_retry(endpoint, params=params)
            
            # Debug: Log raw response sample
            self.logger.debug(f"[API] Token overview raw response sample for {token_address}: "
                            f"{str(response_data)[:500]}...")
            
            if response_data and isinstance(response_data, dict):
                # Check if the response has 'data' directly or if it has 'success' and then 'data'
                if 'data' in response_data:
                    actual_overview = response_data.get('data')
                elif response_data.get('success') and 'data' in response_data:
                    actual_overview = response_data.get('data')
                else:
                    actual_overview = response_data  # Some endpoints might return data directly
                
                if isinstance(actual_overview, dict):
                    # Debug: Log key data points
                    self.logger.debug(f"[API] {token_address} overview data extracted:")
                    self.logger.debug(f"  - Price: {actual_overview.get('price', 'N/A')}")
                    self.logger.debug(f"  - Market Cap: {actual_overview.get('marketCap', 'N/A')}")
                    self.logger.debug(f"  - Liquidity: {actual_overview.get('liquidity', 'N/A')}")
                    self.logger.debug(f"  - Volume 24h: {actual_overview.get('volume', {}).get('h24', 'N/A')}")
                    self.logger.debug(f"  - Price Change 24h: {actual_overview.get('priceChange24h', 'N/A')}")
                    
                    # Check if volume data is missing or zero
                    volume_data = actual_overview.get('volume', {})
                    if not volume_data or (isinstance(volume_data, dict) and volume_data.get('h24', 0) == 0):
                        self.logger.debug(f"[API] {token_address} has missing or zero volume, calculating from transactions")
                        
                        # Calculate volume from transaction data
                        try:
                            tx_volume = await self.get_token_transaction_volume(token_address)
                            
                            # Update the volume data in the overview
                            if tx_volume > 0:
                                if not volume_data or not isinstance(volume_data, dict):
                                    volume_data = {}
                                    
                                volume_data['h24'] = tx_volume
                                actual_overview['volume'] = volume_data
                                self.logger.debug(f"[API] Updated volume data for {token_address} from transactions: ${tx_volume:.2f}")
                        except Exception as e:
                            self.logger.warning(f"[API] Error calculating transaction volume for {token_address}: {e}")
                    
                    self.cache_manager.set(cache_key, actual_overview, ttl=self.default_ttl)
                    return actual_overview
                    
                # If actual_overview is not a dict, or if the initial check failed
                self.logger.warning(f"[API] Token overview for {token_address} data field issue. Data type: {type(actual_overview)}, Response: {str(response_data)[:300]}")
                self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
                return None
                
            # Handles cases where response_data is None, not a dict, or success is false
            self.logger.warning(f"[API] Failed to get valid token overview for {token_address}. Response: {str(response_data)[:300]}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
            
        except APIError as e:
            self.logger.error(f"[API] APIError in get_token_overview for {token_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except RetryError as e_retry:
            self.logger.error(f"[API] Retries exhausted for Birdeye get_token_overview for {token_address}: {e_retry.last_attempt.exception()}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None

    async def get_token_creation_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Fetches creation information for a given token address.
        Corrected Endpoint: /defi/token_creation_info
        """
        # Check if token should be excluded
        if self._should_skip_token(token_address):
            return None
            
        cache_key = f"{BIRDEYE_API_NAMESPACE}_token_creation_info_{token_address}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye token_creation_info: {cache_key}")
            return cached_data

        self.logger.debug(f"Fetching Birdeye token creation info for {token_address}")        
        endpoint = "/defi/token_creation_info" # Corrected endpoint
        params = {"address": token_address}
        
        try:
            response_data = await self._make_request_with_retry(endpoint, params=params)
            # Assuming the response structure is {"success": true, "data": {<creation_info_fields>}}
            if response_data and isinstance(response_data, dict) and response_data.get('success'):
                creation_data = response_data.get('data')
                if isinstance(creation_data, dict):
                    self.logger.debug(f"Successfully fetched token creation info for {token_address}")
                    self.cache_manager.set(cache_key, creation_data, ttl=self.default_ttl)
                    return creation_data
                else:
                    self.logger.warning(f"Birdeye token_creation_info for {token_address} 'data' field is not a dict or is missing. Data: {str(creation_data)[:200]}")
                    self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
                    return None
            else:
                message = response_data.get('message', 'Unknown error or success=false') if isinstance(response_data, dict) else 'Invalid response format'
                self.logger.warning(f"Birdeye token_creation_info call not successful for {token_address}: {message}. Response: {str(response_data)[:300]}")
                self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except APIError as e:
            self.logger.error(f"APIError in get_token_creation_info for {token_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except RetryError as e_retry:
            self.logger.error(f"Retries exhausted for Birdeye get_token_creation_info for {token_address}: {e_retry.last_attempt.exception()}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None

    async def get_token_price(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        STARTER PLAN COMPATIBLE: Fetch individual token price using /defi/price endpoint.
        This method is optimized for Starter Plan which doesn't have batch price endpoints.
        """
        # Check if token should be excluded
        if self._should_skip_token(token_address):
            return None
            
        cache_key = f"{BIRDEYE_API_NAMESPACE}_price_{token_address}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self._track_cache_hit(cache_key)
            self.logger.debug(f"Cache hit for Birdeye token_price: {cache_key}")
            return cached_data
            
        # Track cache miss
        self._track_cache_miss(cache_key)
        
        self.logger.debug(f"Fetching Birdeye token price for {token_address}")
        endpoint = "/defi/price"
        params = {"address": token_address}
        
        try:
            response_data = await self._make_request_with_retry(endpoint, params=params)
            if response_data and isinstance(response_data, dict) and response_data.get('success'):
                price_data = response_data.get('data')
                if isinstance(price_data, dict):
                    self.logger.debug(f"Successfully fetched token price for {token_address}")
                    # Cache for shorter time since price data is volatile
                    self.cache_manager.set(cache_key, price_data, ttl=30)  # 30 seconds for price data
                    return price_data
                else:
                    self.logger.warning(f"Birdeye token_price for {token_address} 'data' field is not a dict or is missing")
                    self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
                    return None
            else:
                message = response_data.get('message', 'Unknown error') if isinstance(response_data, dict) else 'Invalid response'
                self.logger.warning(f"Birdeye token_price call not successful for {token_address}: {message}")
                self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except APIError as e:
            self.logger.error(f"APIError in get_token_price for {token_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except RetryError as e_retry:
            self.logger.error(f"Retries exhausted for Birdeye get_token_price for {token_address}: {e_retry.last_attempt.exception()}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None

    async def get_token_metadata_single(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        STARTER PLAN COMPATIBLE: Fetch individual token metadata using /defi/v3/token/meta-data/single endpoint.
        This method is optimized for Starter Plan which doesn't have batch metadata endpoints.
        """
        # Check if token should be excluded
        if self._should_skip_token(token_address):
            return None
            
        cache_key = f"{BIRDEYE_API_NAMESPACE}_metadata_single_{token_address}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self._track_cache_hit(cache_key)
            self.logger.debug(f"Cache hit for Birdeye token_metadata_single: {cache_key}")
            return cached_data
            
        # Track cache miss
        self._track_cache_miss(cache_key)
        
        self.logger.debug(f"Fetching Birdeye token metadata for {token_address}")
        endpoint = "/defi/v3/token/meta-data/single"
        params = {"address": token_address}
        
        try:
            response_data = await self._make_request_with_retry(endpoint, params=params)
            if response_data and isinstance(response_data, dict) and response_data.get('success'):
                metadata = response_data.get('data')
                if isinstance(metadata, dict):
                    self.logger.debug(f"Successfully fetched token metadata for {token_address}")
                    # Cache for longer time since metadata is more stable
                    self.cache_manager.set(cache_key, metadata, ttl=300)  # 5 minutes for metadata
                    return metadata
                else:
                    self.logger.warning(f"Birdeye token_metadata_single for {token_address} 'data' field is not a dict or is missing")
                    self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
                    return None
            else:
                message = response_data.get('message', 'Unknown error') if isinstance(response_data, dict) else 'Invalid response'
                self.logger.warning(f"Birdeye token_metadata_single call not successful for {token_address}: {message}")
                self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except APIError as e:
            self.logger.error(f"APIError in get_token_metadata_single for {token_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except RetryError as e_retry:
            self.logger.error(f"Retries exhausted for Birdeye get_token_metadata_single for {token_address}: {e_retry.last_attempt.exception()}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None

    async def get_historical_price_at_timestamp(self, token_address: str, unix_timestamp: int) -> Optional[Dict[str, Any]]:
        """Fetches historical token price at a specific UNIX timestamp with fallback mechanisms."""
        # Check if token should be excluded
        if self._should_skip_token(token_address):
            return None
            
        cache_key = f"{BIRDEYE_API_NAMESPACE}_hist_price_{token_address}_{unix_timestamp}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye historical_price_at_timestamp: {cache_key}")
            return cached_data

        self.logger.debug(f"Fetching Birdeye historical price for {token_address} at {unix_timestamp}")
        
        # Try primary endpoint first - updated to use the correct endpoint
        endpoint = "/defi/historical_price_unix"  # Changed from "/defi/price-historical-by-unix-time"
        
        # ALWAYS USE unixtime=10000000000 as requested
        params = {"address": token_address, "unixtime": 10000000000}  # Always use 10000000000 regardless of unix_timestamp parameter
        
        try:
            response_data = await self._make_request_with_retry(endpoint, params=params)
            self.logger.debug(f"[DEBUG] Birdeye historical price API raw response for {token_address} at {unix_timestamp}: {response_data}")
            
            if response_data and isinstance(response_data, dict):
                # Extract price data from the new endpoint format
                if response_data.get('success', False) and 'data' in response_data:
                    price_data = response_data.get('data', {})
                    
                    # New endpoint returns the structure {"data":{"value":0.004178,"updateUnixTime":1747969771},"success":true}
                    if isinstance(price_data, dict) and "value" in price_data:
                        price_info = {
                            "timestamp": price_data.get("updateUnixTime", unix_timestamp), 
                            "price": price_data["value"]
                        }
                        self.logger.debug(f"Successfully fetched price for {token_address} at {unix_timestamp}: {price_info['price']}")
                        self.cache_manager.set(cache_key, price_info, ttl=self.default_ttl) 
                        return price_info
            
            # If primary endpoint failed, try backup method: multi_price API
            self.logger.info(f"Primary historical price endpoint failed for {token_address}, trying multi_price API as fallback")
            multi_price_data = await self.get_multi_price([token_address])
            
            if multi_price_data and token_address in multi_price_data:
                token_price_data = multi_price_data[token_address]
                price_info = {
                    "timestamp": token_price_data.get("updateUnixTime", unix_timestamp),
                    "price": token_price_data.get("value")
                }
                if price_info["price"] is not None:
                    self.logger.info(f"Successfully fetched price via multi_price fallback for {token_address}: {price_info['price']}")
                    self.cache_manager.set(cache_key, price_info, ttl=self.default_ttl)
                    return price_info
            
            # If all attempts fail, check token overview as final fallback
            self.logger.info(f"Both historical price and multi_price failed for {token_address}, trying token_overview as final fallback")
            overview_data = await self.get_token_overview(token_address)
            
            if overview_data and "price" in overview_data:
                price_info = {
                    "timestamp": unix_timestamp,  # We don't know exactly when this price was recorded
                    "price": overview_data["price"]
                }
                self.logger.info(f"Successfully fetched price via token_overview fallback for {token_address}: {price_info['price']}")
                self.cache_manager.set(cache_key, price_info, ttl=self.default_ttl)
                return price_info
                
            # If all methods fail
            self.logger.warning(f"All price fetch methods failed for {token_address} at {unix_timestamp}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
            
        except Exception as e:
            self.logger.error(f"Error in get_historical_price_at_timestamp for {token_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None

    async def get_token_holders(self, token_address: str, offset: int = 0, limit: int = 100) -> Optional[Dict[str, Any]]:
        cache_key = f"{BIRDEYE_API_NAMESPACE}_holders_{token_address}_{offset}_{limit}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye token_holders: {cache_key}")
            return cached_data
        self.logger.debug(f"Fetching Birdeye token_holders for {token_address}, offset {offset}, limit {limit}")
        endpoint = "/defi/v3/token/holder" # Updated to correct v3 endpoint
        params = {"address": token_address, "offset": offset, "limit": limit}
        try:
            response_data = await self._make_request_with_retry(endpoint, params=params)
            if response_data and isinstance(response_data, dict) and response_data.get('success'):
                # Updated structure based on working example: {success: true, data: {items: [...], total: 123, ...}}
                holders_data_container = response_data.get('data', {}) 
                
                if isinstance(holders_data_container, dict):
                    holders_items = holders_data_container.get('items', [])
                    total_holders = holders_data_container.get('total', 0)
                    
                    # Return both items and total count
                    full_response = {
                        'items': holders_items,
                        'total': total_holders,
                        'offset': offset,
                        'limit': limit
                    }
                    
                    if isinstance(holders_items, list):
                        self.cache_manager.set(cache_key, full_response, ttl=self.default_ttl)
                        return full_response
                    else:
                        self.logger.warning(f"Birdeye token_holders for {token_address} 'items' is not a list: {type(holders_items)}")
                        self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
                else:
                    self.logger.warning(f"Birdeye token_holders for {token_address} data container is not a dict: {type(holders_data_container)}")
                    self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            else:
                self.logger.warning(f"Failed to get valid token_holders for {token_address} from BirdEye. Response: {str(response_data)[:300]}")
                self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None # Return None if any success condition above fails
        except APIError as e: 
            self.logger.error(f"APIError in get_token_holders for {token_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl_seconds=self.error_ttl)
            return None

    async def batch_get_token_overviews(self, addresses: List[str], scan_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Fetch token overviews using true batch API to reduce costs by 90%.
        Uses /defi/v3/token/meta-data/multiple (5 base CU + N^0.8) instead of 
        individual /defi/token_overview calls (30 CU each).
        
        Args:
            addresses: List of token addresses
            scan_id: Optional scan identifier for tracking
        
        Returns:
            Dictionary mapping addresses to their overview data
        """
        if not addresses:
            return {}
            
        # Filter out excluded tokens first to avoid wasted API calls
        filtered_addresses = [addr for addr in addresses if not self._should_skip_token(addr)]
        if not filtered_addresses:
            self.logger.debug("All tokens in batch were excluded from API calls")
            return {}
            
        results = {}
        unique_addresses = list(dict.fromkeys(filtered_addresses))
        
        # Process in batches of 50 (max for metadata endpoint)
        for i in range(0, len(unique_addresses), 50):
            batch = unique_addresses[i:i+50]
            batch_key = f"{BIRDEYE_API_NAMESPACE}_batch_overview_{'-'.join(batch)}"
            
            # Check cache first for entire batch
            cached_batch = self.cache_manager.get(batch_key)
            if cached_batch is not None:
                self._track_cache_hit(batch_key)
                self.logger.debug(f"Cache hit for batch overview: {len(batch)} tokens")
                results.update(cached_batch)
                continue
                
            self._track_cache_miss(batch_key)
            
            # Check individual cache entries
            batch_results = {}
            uncached_tokens = []
            
            for address in batch:
                cache_key = f"{BIRDEYE_API_NAMESPACE}_overview_{address}"
                cached_data = self.cache_manager.get(cache_key)
                if cached_data is not None:
                    batch_results[address] = cached_data
                    self._track_cache_hit(cache_key)
                else:
                    uncached_tokens.append(address)
                    self._track_cache_miss(cache_key)
            
            # Only make API call for uncached tokens
            if uncached_tokens:
                try:
                    # Use the efficient batch metadata endpoint
                    batch_data = await self.get_token_metadata_multiple(uncached_tokens, scan_id)
                    
                    if batch_data:
                        # Cache individual results with longer TTL (30 minutes for metadata)
                        for address, data in batch_data.items():
                            if data:
                                batch_results[address] = data
                                # Cache individual entries with 30-minute TTL since metadata is relatively stable
                                self.cache_manager.set(f"{BIRDEYE_API_NAMESPACE}_overview_{address}", data, ttl=1800)
                        
                        self.logger.info(f"✅ Batch API success: {len(batch_data)}/{len(uncached_tokens)} tokens fetched via batch endpoint")
                    else:
                        self.logger.warning(f"⚠️ Batch metadata call returned no data for {len(uncached_tokens)} tokens")
                        
                except Exception as e:
                    self.logger.error(f"❌ Batch metadata call failed: {e}")
                    # Fallback to individual calls only if absolutely necessary
                    self.logger.warning("Falling back to individual calls for this batch")
                    
                    # Use semaphore to limit concurrent individual calls
                    semaphore = asyncio.Semaphore(3)
                    
                    async def fetch_individual(address: str) -> tuple[str, Optional[Dict]]:
                        async with semaphore:
                            try:
                                data = await self.get_token_overview(address)
                                return address, data
                            except Exception as e:
                                self.logger.warning(f"Individual fallback failed for {address}: {e}")
                                return address, None
                    
                    # Execute fallback individual calls
                    tasks = [fetch_individual(addr) for addr in uncached_tokens]
                    fallback_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in fallback_results:
                        if isinstance(result, Exception):
                            continue
                        address, data = result
                        if data:
                            batch_results[address] = data
            
            # Cache the entire batch result
            if batch_results:
                self.cache_manager.set(batch_key, batch_results, ttl=1800)  # 30 minutes
            
            results.update(batch_results)
            
            # Rate limiting between batches
            if i + 50 < len(unique_addresses):
                await asyncio.sleep(0.2)
        
        self.logger.info(f"📊 Batch overview completed: {len(results)}/{len(unique_addresses)} tokens retrieved")
        return results

    def _prepare_token_overview_request(self, address: str) -> Dict[str, Any]:
        """Prepare a token overview request for concurrent execution"""
        return {
            'method': 'GET',
            'url': f"{self.base_url}/defi/token_overview",
            'headers': self.headers,
            'params': {'address': address},
            'address': address  # Store address for reference
        }
    
    def _extract_address_from_request(self, request: Dict[str, Any]) -> str:
        """Extract the token address from a request object"""
        if 'address' in request:
            return request['address']
        if 'params' in request and 'address' in request['params']:
            return request['params']['address']
        return ""

    async def _execute_concurrent_requests(self, requests: List[Dict[str, Any]]) -> List[Any]:
        """Execute multiple requests concurrently"""
        results = []
        
        # Use asyncio/aiohttp since it's already imported
        session = await self._get_session()
        
        async def _async_fetch(req):
            try:
                # Apply rate limiting
                await self.rate_limiter.wait_for_slot(self.API_DOMAIN)
                
                async with session.request(
                    req['method'], 
                    req['url'], 
                    headers=req['headers'], 
                    params=req.get('params')
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Handle different response structures
                        if isinstance(data, dict):
                            if 'data' in data:
                                return data.get('data')
                            return data
                    return None
            except Exception as e:
                self.logger.error(f"API request failed: {str(e)}")
                return None
        
        # Execute all requests concurrently
        tasks = [_async_fetch(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to None
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Request failed: {result}")
                results[i] = None
        
        return results

    async def get_wallet_transaction_history(self, wallet_address: str, chain: str = "solana", offset: int = 0, limit: int = 50, sort_by: Optional[str] = None, sort_type: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches the transaction history for a given wallet address.
        Corrected Endpoint: /v1/wallet/tx-list (Beta)
        Requires x-chain header, e.g., "solana".
        Parameters from docs (B4 Wallet - Transaction List - Selected Chain) are minimal.
        Other params like offset, limit, sort_by, sort_type are kept for potential compatibility
        but may not be supported by this specific beta endpoint.
        """
        cache_key_parts = [BIRDEYE_API_NAMESPACE, "wallet_tx_list", chain, wallet_address, str(offset), str(limit)]
        if sort_by:
            cache_key_parts.append(sort_by)
        if sort_type:
            cache_key_parts.append(sort_type)
        cache_key = "_".join(cache_key_parts)
        
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye wallet_transaction_history: {cache_key}")
            return cached_data

        self.logger.debug(f"Fetching Birdeye wallet transaction history for {wallet_address} on chain {chain}")
        endpoint = "/v1/wallet/tx-list" # Beta endpoint
        params = {"wallet": wallet_address} # Address key for this endpoint
        
        # Adding optional parameters if they exist (may not be supported by the beta endpoint but safe to include)
        if offset:
            params["offset"] = offset
        if limit:
            params["limit"] = limit
        if sort_by:
            params["sort_by"] = sort_by
        if sort_type:
            params["sort_type"] = sort_type

        # The x-chain header requirement
        custom_headers = {"x-chain": chain}

        # Debug log for request details
        self.logger.debug(f"[BirdeyeAPI] Requesting {self.base_url+endpoint} with headers={custom_headers} params={params} chain={chain} address={wallet_address}")

        try:
            response_data = await self._make_request_with_retry(endpoint, params=params, custom_headers=custom_headers)
            
            if response_data and isinstance(response_data, dict) and response_data.get('success'):
                data_field = response_data.get('data')
                items = []
                if isinstance(data_field, dict):
                    items = data_field.get('items', [])
                elif isinstance(data_field, list):
                    items = data_field
                if isinstance(items, list):
                    self.logger.debug(f"Successfully fetched {len(items)} transactions for wallet {wallet_address}")
                    if not items:
                        self.logger.warning(f"No transactions found for wallet {wallet_address} (empty tx list). Params: {params}")
                    else:
                        # Check for all failed or only airdrop txs if possible
                        all_failed = all(not tx.get('status', True) for tx in items)
                        only_airdrops = all(tx.get('mainAction') == 'airdrop' for tx in items if 'mainAction' in tx)
                        if all_failed:
                            self.logger.warning(f"All transactions failed for wallet {wallet_address}. Params: {params}")
                        if only_airdrops and items:
                            self.logger.info(f"Only airdrop transactions found for wallet {wallet_address}. Params: {params}")
                    self.cache_manager.set(cache_key, items, ttl=self.default_ttl)
                    return items
                else:
                    self.logger.warning(f"Birdeye wallet_transaction_history for {wallet_address} 'items' or 'data' is not a list. Data: {str(data_field)[:200]}")
                    self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
                    return None
            else:
                message = response_data.get('message', 'Unknown error or success=false') if isinstance(response_data, dict) else 'Invalid response format'
                self.logger.warning(f"Birdeye wallet_transaction_history call not successful for {wallet_address}: {message}. Response: {str(response_data)[:300]}")
                self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except (APIConnectionError, APIDataError) as e:
            self.logger.error(f"API error for wallet transaction history {wallet_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error for wallet transaction history {wallet_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None

    async def get_wallet_portfolio(self, wallet_address: str, chain: str = "solana") -> Optional[Dict[str, Any]]:
        """
        Fetches the token portfolio for a given wallet address.
        Endpoint: /v1/wallet/token_list
        Requires x-chain header.
        Parameters:
            wallet_address (str): The address of the wallet.
            chain (str): The chain name, e.g., "solana".
        """
        cache_key = f"{BIRDEYE_API_NAMESPACE}_wallet_portfolio_{chain}_{wallet_address}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye wallet_portfolio: {cache_key}")
            return cached_data

        self.logger.debug(f"Fetching Birdeye wallet portfolio for {wallet_address} on chain {chain}")
        endpoint = "/v1/wallet/token_list" # Corrected endpoint
        params = {"wallet": wallet_address} # Corrected parameter name
        
        # The x-chain header needs to be handled. 
        custom_headers = {"x-chain": chain}

        try:
            response_data = await self._make_request_with_retry(endpoint, params=params, custom_headers=custom_headers)
            
            if response_data and isinstance(response_data, dict) and response_data.get('success'):
                portfolio_data = response_data.get('data')
                if portfolio_data is not None:
                    self.logger.debug(f"Successfully fetched portfolio data for wallet {wallet_address}. Type: {type(portfolio_data)}")
                    self.cache_manager.set(cache_key, portfolio_data, ttl=self.default_ttl)
                    return portfolio_data
                else:
                    self.logger.warning(f"Birdeye wallet_portfolio for {wallet_address} 'data' field is missing or null.")
                    self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
                    return None
            else:
                message = response_data.get('message', 'Unknown error or success=false') if isinstance(response_data, dict) else 'Invalid response format'
                self.logger.warning(f"Birdeye wallet_portfolio call not successful for {wallet_address}: {message}. Response: {str(response_data)[:300]}")
                self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except (APIConnectionError, APIDataError) as e:
            self.logger.error(f"API error for wallet portfolio {wallet_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error for wallet portfolio {wallet_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None

    async def get_trader_gainers_losers(self, timeframe: str = "24h", sort_by: str = "pnl", limit: int = 10, offset: int = 0, chain: str = "solana") -> Optional[List[Dict[str, Any]]]:
        """
        Fetches a list of top gainers or losers among traders for a given timeframe.
        Corrected Endpoint: /trader/gainers-losers
        Requires x-chain header.
        Parameters:
            timeframe (str): e.g., "6h", "24h", "7d". API docs mention this as part of endpoint 26.
            sort_by (str): Field to sort by, e.g., "pnl" (profit and loss), "volume".
            limit (int): Number of results to return (1-10 based on API error message).
            offset (int): Offset for pagination.
            chain (str): The chain name, e.g., "solana".
        """
        cache_key = f"{BIRDEYE_API_NAMESPACE}_trader_gainers_losers_{chain}_{timeframe}_{sort_by}_{limit}_{offset}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye trader_gainers_losers: {cache_key}")
            return cached_data

        self.logger.debug(f"Fetching Birdeye trader gainers/losers for chain {chain}, timeframe {timeframe}, sort {sort_by}, limit {limit}")
        endpoint = "/trader/gainers-losers" # Corrected endpoint
        
        # Ensure limit is within API constraints (1-10)
        api_limit = max(1, min(10, limit))
        
        params = {
            "timeFrame": timeframe, 
            "sortBy": sort_by,    
            "limit": api_limit,  # Use constrained limit
            "offset": offset
            # chain is passed via header
        }

        custom_headers = {"x-chain": chain}
        
        try:
            response_data = await self._make_request_with_retry(endpoint, params=params, custom_headers=custom_headers)

            if response_data and isinstance(response_data, dict) and response_data.get('success'):
                data_field = response_data.get('data')
                items = []
                if isinstance(data_field, dict):
                    items = data_field.get('items', [])
                elif isinstance(data_field, list):
                    items = data_field

                if isinstance(items, list):
                    self.logger.debug(f"Successfully fetched {len(items)} trader rankings for {timeframe} on {chain}.")
                    self.cache_manager.set(cache_key, items, ttl=self.default_ttl)
                    return items
                else:
                    self.logger.warning(f"Birdeye trader_gainers_losers for {timeframe} on {chain} 'items' or 'data' is not a list. Data: {str(data_field)[:200]}")
                    self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
                    return None
            else:
                message = response_data.get('message', 'Unknown error or success=false') if isinstance(response_data, dict) else 'Invalid response format'
                self.logger.warning(f"Birdeye trader_gainers_losers call not successful for {timeframe} on {chain}: {message}. Response: {str(response_data)[:300]}")
                self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except (APIConnectionError, APIDataError) as e:
            self.logger.error(f"API error for trader gainers/losers {timeframe} on {chain}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except Exception as e: 
            self.logger.error(f"Unexpected error in get_trader_gainers_losers for {timeframe} on {chain}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None

    async def get_token_security(self, token_address: str) -> Optional[Dict[str, Any]]:
        cache_key = f"{BIRDEYE_API_NAMESPACE}_security_{token_address}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self._track_cache_hit(cache_key)
            self.logger.debug(f"Cache hit for Birdeye token_security: {cache_key}")
            return cached_data
        
        # Track cache miss
        self._track_cache_miss(cache_key)
        self.logger.debug(f"Fetching Birdeye token security for {token_address}")
        endpoint = "/defi/token_security"
        params = {"address": token_address}
        try:
            response_data = await self._make_request_with_retry(endpoint, params=params)
            if response_data and isinstance(response_data, dict) and response_data.get('success'):
                security_data = response_data.get('data')
                if isinstance(security_data, dict):
                    self.cache_manager.set(cache_key, security_data, ttl=self.default_ttl)
                    return security_data
                self.logger.warning(f"Birdeye token_security for {token_address} data field issue. Data: {str(security_data)[:300]}")
                self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
                return None
            self.logger.warning(f"Failed to get valid token security for {token_address} from Birdeye. Response: {str(response_data)[:300]}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None
        except Exception as e:
            self.logger.error(f"Error fetching token security for {token_address}: {e}")
            self.cache_manager.set(cache_key, None, ttl=self.error_ttl)
            return None

    async def get_token_age(self, token_address: str) -> Tuple[float, str]:
        """
        Determine token age in days from creation timestamp and corresponding age category.
        
        Args:
            token_address: The token address to analyze
            
        Returns:
            Tuple of (age_in_days, age_category)
            age_category is one of: 'ultra_new', 'new', 'very_recent', 'recent', 'developing', 'established', 'mature'
        """
        # Check cache first - use longer TTL for this since creation time doesn't change
        cache_key = f"{BIRDEYE_API_NAMESPACE}_token_age_{token_address}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for token age data: {cache_key}")
            return cached_data
            
        self.logger.debug(f"Fetching token age data for {token_address}")
        
        # Default age if we can't determine
        default_age_days = 30
        default_category = 'established'
        
        try:
            # First try token creation info endpoint - most reliable source
            creation_data = await self.get_token_creation_info(token_address)
            if creation_data and 'createdTime' in creation_data:
                creation_timestamp = int(creation_data['createdTime'])
                self.logger.info(f"Found creation timestamp from creation info: {creation_timestamp}")
            else:
                # Try token security data which often contains creation date
                security_data = await self.get_token_security(token_address)
                if security_data and 'createdTime' in security_data:
                    creation_timestamp = int(security_data['createdTime'])
                    self.logger.info(f"Found creation timestamp from security data: {creation_timestamp}")
                else:
                    # Fall back to searching transactions for earliest activity
                    try:
                        earliest_tx = await self._get_earliest_transaction(token_address)
                        if earliest_tx and 'time' in earliest_tx:
                            creation_timestamp = int(earliest_tx['time'])
                            self.logger.info(f"Found earliest transaction timestamp: {creation_timestamp}")
                        else:
                            self.logger.warning(f"Could not determine creation time for {token_address}, using default age")
                            result = (default_age_days, default_category)
                            self.cache_manager.set(cache_key, result, ttl=3600)  # Cache for 1 hour
                            return result
                    except Exception as e:
                        self.logger.error(f"Error finding earliest transaction for {token_address}: {e}")
                        result = (default_age_days, default_category)
                        self.cache_manager.set(cache_key, result, ttl=3600)
                        return result
            
            # Calculate age in days
            now = int(time.time())
            age_seconds = now - creation_timestamp
            age_days = age_seconds / (60 * 60 * 24)
            
            # Determine age category with more granularity
            if age_days < 0.25:  # Less than 6 hours
                age_category = 'new'
            elif age_days < 1:  # 6-24 hours
                age_category = 'very_recent'
            elif age_days < 3:  # 1-3 days
                age_category = 'recent'
            elif age_days < 7:  # 3-7 days
                age_category = 'developing'
            elif age_days < 30:  # 7-30 days
                age_category = 'established'
            else:  # More than 30 days
                age_category = 'mature'
            
            self.logger.info(f"Token {token_address} age: {age_days:.1f} days, category: {age_category}")
            
            # Cache the result for a day (creation time doesn't change)
            result = (age_days, age_category)
            self.cache_manager.set(cache_key, result, ttl=86400)  # Cache for 24 hours
            return result
                
        except Exception as e:
            self.logger.error(f"Error determining token age for {token_address}: {e}")
            result = (default_age_days, default_category)
            self.cache_manager.set(cache_key, result, ttl=3600)  # Cache errors for shorter time
            return result

    async def get_trending_tokens(self) -> Optional[List[str]]:
        """Fetch the list of trending token addresses from Birdeye."""
        cache_key = f"{BIRDEYE_API_NAMESPACE}_trending_tokens"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye trending tokens: {cache_key}")
            return cached_data
        self.logger.debug("Fetching Birdeye trending tokens")
        
        # Try multiple endpoints with different parameters to handle API changes
        endpoints = [
            "/defi/token_trending",   # Original endpoint
            "/defi/tokens/trending",  # Alternative endpoint format 
            "/defi/v2/tokens/trending", # V2 format
            "/defi/token_list"        # Fallback to general token list
        ]
        
        for endpoint in endpoints:
            try:
                params = None
                
                # Add special parameters for token_list endpoint to sort by volume
                if endpoint == "/defi/token_list":
                    params = {
                        "sort_by": "volume_24h_usd",
                        "sort_type": "desc",
                        "limit": 20
                    }
                
                response_data = await self._make_request_with_retry(endpoint, params=params)
                
                # Check if we have a valid response
                if response_data and isinstance(response_data, dict) and response_data.get('success'):
                    trending_data = response_data.get('data', {})
                    trending_tokens = []
                    
                    # Handle different data structures
                    if isinstance(trending_data, dict):
                        if 'tokens' in trending_data:
                            trending_tokens = trending_data.get('tokens', [])
                        elif 'items' in trending_data:
                            trending_tokens = trending_data.get('items', [])
                    elif isinstance(trending_data, list):
                        trending_tokens = trending_data
                    
                    # Extract addresses from tokens
                    if trending_tokens:
                        if isinstance(trending_tokens[0], dict):
                            trending_addresses = [t.get('address') for t in trending_tokens if isinstance(t, dict) and 'address' in t]
                        elif isinstance(trending_tokens[0], str):
                            trending_addresses = trending_tokens  # Direct list of addresses
                        else:
                            trending_addresses = []
                            
                        if trending_addresses:
                            self.logger.info(f"Successfully fetched {len(trending_addresses)} trending tokens using {endpoint}")
                            self.cache_manager.set(cache_key, trending_addresses, ttl=self.default_ttl)
                            return trending_addresses
                
                self.logger.debug(f"No valid data from {endpoint}, trying next endpoint")
            except Exception as e:
                self.logger.warning(f"Error with trending endpoint {endpoint}: {e}")
                continue
        
        # If all endpoints fail, use a fallback solution by getting top volume tokens
        try:
            self.logger.warning("All trending token endpoints failed, using top volume tokens as fallback")
            top_tokens = await self.get_token_list(
                sort_by="volume_24h_usd",
                sort_type="desc",
                limit=20,
                min_liquidity=500000  # Lower threshold for fallback
            )
            
            if top_tokens and isinstance(top_tokens, dict) and 'data' in top_tokens:
                token_items = []
                
                # Check different data structures
                data_field = top_tokens.get('data', {})
                if isinstance(data_field, dict) and 'items' in data_field:
                    token_items = data_field.get('items', [])
                elif isinstance(data_field, dict) and 'tokens' in data_field:
                    token_items = data_field.get('tokens', [])
                elif isinstance(data_field, list):
                    token_items = data_field
                
                # Extract addresses
                if token_items:
                    trending_addresses = [t.get('address') for t in token_items if isinstance(t, dict) and 'address' in t]
                    if trending_addresses:
                        self.logger.info(f"Using fallback method: found {len(trending_addresses)} high-volume tokens")
                        self.cache_manager.set(cache_key, trending_addresses, ttl=self.error_ttl)
                        return trending_addresses
        except Exception as e:
            self.logger.error(f"Fallback method for trending tokens also failed: {e}")
        
        # If all methods fail, return empty list with short cache time
        self.logger.warning("Unable to fetch trending tokens through any method")
        self.cache_manager.set(cache_key, [], ttl_seconds=60)  # Cache empty list for 1 minute only
        return []

    async def get_top_traders(self, token_address: str) -> Optional[List[Dict]]:
        """Fetch top active wallets for a token from Birdeye with updated endpoints."""
        cache_key = f"{BIRDEYE_API_NAMESPACE}_top_traders_{token_address}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye top_traders: {cache_key}")
            return cached_data
        self.logger.debug(f"Fetching Birdeye top traders for {token_address}")
        
        # Try multiple endpoints and methods
        endpoints = [
            "/defi/v2/tokens/top_traders",   # Try v2 first (more stable)
            "/defi/v3/tokens/top_traders",   # Then v3
            "/defi/tokens/top_traders",      # Alternative format
            "/defi/token/top_traders"        # Another alternative
        ]
        
        for endpoint in endpoints:
            try:
                params = {"address": token_address}
                response_data = await self._make_request_with_retry(endpoint, params=params)
                if response_data and isinstance(response_data, dict) and response_data.get('success'):
                    # Handle different response structures
                    data_field = response_data.get('data', {})
                    traders = []
                    
                    if isinstance(data_field, dict):
                        # Check for various possible array fields
                        traders = (data_field.get('traders', []) or 
                                 data_field.get('items', []) or 
                                 data_field.get('top_traders', []))
                    elif isinstance(data_field, list):
                        traders = data_field
                    
                    if traders and isinstance(traders, list):  # Only cache and return if we have data
                        self.logger.debug(f"Successfully fetched top traders using {endpoint}")
                        self.cache_manager.set(cache_key, traders, ttl=self.default_ttl)
                        return traders
                        
                self.logger.debug(f"No traders data from {endpoint}")
            except Exception as e:
                self.logger.warning(f"Error with top traders endpoint {endpoint}: {e}")
                continue
        
        # If dedicated endpoints fail, try using get_token_top_traders as fallback
        try:
            self.logger.debug(f"Trying get_token_top_traders as fallback for {token_address}")
            top_traders_from_txs = await self.get_token_top_traders(token_address, limit=20)
            if top_traders_from_txs and isinstance(top_traders_from_txs, list):
                self.logger.info(f"Using transaction-based top traders fallback: {len(top_traders_from_txs)} traders")
                self.cache_manager.set(cache_key, top_traders_from_txs, ttl=self.error_ttl)
                return top_traders_from_txs
        except Exception as e:
            self.logger.warning(f"Transaction-based fallback also failed: {e}")
        
        self.logger.warning(f"Failed to get top traders for {token_address} from all endpoints and fallbacks")
        self.cache_manager.set(cache_key, [], ttl=self.error_ttl)
        return []

    async def get_top_traders_optimized(self, token_address: str, time_frame: str = "24h", 
                                      sort_by: str = "volume", sort_type: str = "desc", 
                                      limit: int = 10, offset: int = 0) -> Optional[List[Dict]]:
        """
        Fetch top traders with optimized query parameters for enhanced analysis.
        
        Args:
            token_address: Token contract address
            time_frame: Time window for analysis (30m, 1h, 2h, 4h, 6h, 8h, 12h, 24h)
            sort_by: Sort field (volume, trade) 
            sort_type: Sort order (desc, asc)
            limit: Number of traders to return (1-10, API limitation)
            offset: Pagination offset (0-10000)
            
        Returns:
            List of trader dictionaries with enhanced data
        """
        # Create cache key that includes all parameters for proper caching
        cache_key = f"{BIRDEYE_API_NAMESPACE}_top_traders_opt_{token_address}_{time_frame}_{sort_by}_{sort_type}_{limit}_{offset}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self._track_cache_hit(cache_key)
            self.logger.debug(f"Cache hit for optimized top traders: {time_frame}_{sort_by}")
            return cached_data
        
        self._track_cache_miss(cache_key)
        self.logger.debug(f"Fetching optimized top traders for {token_address} ({time_frame}, sort_by={sort_by})")
        
        # Validate parameters according to API constraints
        valid_timeframes = ["30m", "1h", "2h", "4h", "6h", "8h", "12h", "24h"]
        valid_sort_by = ["volume", "trade"]
        valid_sort_types = ["desc", "asc"]
        
        if time_frame not in valid_timeframes:
            self.logger.warning(f"Invalid time_frame '{time_frame}', using default '24h'")
            time_frame = "24h"
        
        if sort_by not in valid_sort_by:
            self.logger.warning(f"Invalid sort_by '{sort_by}', using default 'volume'")
            sort_by = "volume"
            
        if sort_type not in valid_sort_types:
            self.logger.warning(f"Invalid sort_type '{sort_type}', using default 'desc'")
            sort_type = "desc"
        
        # Clamp limit and offset to API constraints
        limit = max(1, min(10, limit))  # API allows 1-10
        offset = max(0, min(10000, offset))  # API allows 0-10000
        
        # Build optimized parameters
        params = {
            "address": token_address,
            "time_frame": time_frame,
            "sort_by": sort_by,
            "sort_type": sort_type,
            "limit": limit,
            "offset": offset
        }
        
        # Try multiple endpoints with optimized parameters
        endpoints = [
            "/defi/v2/tokens/top_traders",   # Primary v2 endpoint
            "/defi/v3/tokens/top_traders",   # Alternative v3 endpoint
            "/defi/tokens/top_traders"       # Legacy endpoint
        ]
        
        for endpoint in endpoints:
            try:
                self.logger.debug(f"Trying {endpoint} with params: {params}")
                response_data = await self._make_request_with_retry(endpoint, params=params)
                
                if response_data and isinstance(response_data, dict) and response_data.get('success'):
                    # Handle different response structures
                    data_field = response_data.get('data', {})
                    traders = []
                    
                    if isinstance(data_field, dict):
                        # Check for various possible array fields
                        traders = (data_field.get('items', []) or 
                                 data_field.get('traders', []) or 
                                 data_field.get('top_traders', []))
                    elif isinstance(data_field, list):
                        traders = data_field
                    
                    if traders and isinstance(traders, list):
                        # Enhance trader data with query context
                        enhanced_traders = []
                        for trader in traders:
                            enhanced_trader = {
                                **trader,
                                "query_timeframe": time_frame,
                                "query_sort_by": sort_by,
                                "query_sort_type": sort_type,
                                "api_endpoint": endpoint
                            }
                            enhanced_traders.append(enhanced_trader)
                        
                        # Cache successful results
                        cache_ttl = self._get_optimized_cache_ttl(time_frame)
                        self.cache_manager.set(cache_key, enhanced_traders, ttl=cache_ttl)
                        
                        self.logger.info(f"✅ Fetched {len(enhanced_traders)} traders using {endpoint} "
                                       f"({time_frame}, {sort_by}, limit={limit})")
                        return enhanced_traders
                        
                self.logger.debug(f"No traders data from {endpoint} with optimized params")
                
            except Exception as e:
                self.logger.warning(f"Error with optimized endpoint {endpoint}: {e}")
                continue
        
        # If optimized endpoints fail, try fallback with basic parameters
        try:
            self.logger.debug(f"Trying basic fallback for {token_address}")
            basic_result = await self.get_top_traders(token_address)
            
            if basic_result and isinstance(basic_result, list):
                # Add query context to fallback data
                enhanced_fallback = []
                for trader in basic_result[:limit]:  # Respect limit
                    enhanced_trader = {
                        **trader,
                        "query_timeframe": time_frame,
                        "query_sort_by": sort_by,
                        "query_sort_type": sort_type,
                        "api_endpoint": "fallback",
                        "is_fallback": True
                    }
                    enhanced_fallback.append(enhanced_trader)
                
                # Cache fallback results with shorter TTL
                self.cache_manager.set(cache_key, enhanced_fallback, ttl=self.error_ttl)
                
                self.logger.info(f"Using fallback traders for {token_address}: {len(enhanced_fallback)} traders")
                return enhanced_fallback
                
        except Exception as e:
            self.logger.warning(f"Fallback also failed for {token_address}: {e}")
        
        # If everything fails, return empty list
        self.logger.warning(f"Failed to get optimized top traders for {token_address} with all methods")
        self.cache_manager.set(cache_key, [], ttl=self.error_ttl)
        return []
    
    def _get_optimized_cache_ttl(self, time_frame: str) -> int:
        """
        Get optimized cache TTL based on timeframe.
        
        Args:
            time_frame: Query timeframe
            
        Returns:
            Cache TTL in seconds
        """
        # Shorter timeframes need more frequent updates
        timeframe_ttl_map = {
            "30m": 300,   # 5 minutes
            "1h": 600,    # 10 minutes  
            "2h": 900,    # 15 minutes
            "4h": 1200,   # 20 minutes
            "6h": 1800,   # 30 minutes
            "8h": 2400,   # 40 minutes
            "12h": 3600,  # 1 hour
            "24h": 7200   # 2 hours
        }
        
        return timeframe_ttl_map.get(time_frame, self.default_ttl)

    async def get_new_listings(self) -> Optional[List[Dict]]:
        """Fetch newly listed tokens from Birdeye with updated endpoints."""
        cache_key = f"{BIRDEYE_API_NAMESPACE}_new_listings"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye new listings: {cache_key}")
            return cached_data
        self.logger.debug("Fetching Birdeye new listings")
        
        # Try multiple endpoints including discovery alternatives
        endpoints = [
            "/defi/v2/tokens/new_listing",   # Try v2 first (more stable)
            "/defi/v3/tokens/new_listing",   # Then v3
            "/defi/token_list",              # Alternative: general token list with filters
            "/defi/tokens/new"               # Alternative: newer endpoint format
        ]
        
        for endpoint in endpoints:
            try:
                # Add parameters for token list endpoint to filter new tokens
                if "token_list" in endpoint:
                    params = {
                        "sort_by": "listing_time", 
                        "sort_type": "desc",
                        "limit": 20  # Changed from 50 to 20 to comply with API limits
                    }
                elif endpoint == "/defi/v2/tokens/new_listing":
                    # New listings endpoint has a strict limit of 1-20
                    params = {"limit": 20}
                else:
                    params = None
                    
                response_data = await self._make_request_with_retry(endpoint, params=params)
                if response_data and isinstance(response_data, dict) and response_data.get('success'):
                    # Handle different response structures
                    data_field = response_data.get('data', {})
                    listings = []
                    
                    if isinstance(data_field, dict):
                        # Check for various possible array fields
                        listings = (data_field.get('items', []) or 
                                  data_field.get('tokens', []) or 
                                  data_field.get('new_listings', []))
                    elif isinstance(data_field, list):
                        listings = data_field
                    
                    if listings and isinstance(listings, list):  # Only cache and return if we have data
                        self.logger.debug(f"Successfully fetched new listings using {endpoint}")
                        self.cache_manager.set(cache_key, listings, ttl=self.default_ttl)
                        return listings
                    
                self.logger.debug(f"No listings data from {endpoint}")
            except Exception as e:
                self.logger.warning(f"Error with new listings endpoint {endpoint}: {e}")
                continue
        
        # If all dedicated endpoints fail, try using trending tokens as fallback
        try:
            self.logger.debug("Trying trending tokens as fallback for new listings")
            trending = await self.get_trending_tokens()
            if trending and isinstance(trending, list):
                # Return subset of trending tokens as new listings fallback
                fallback_listings = [{"address": addr} for addr in trending[:20]]
                self.logger.info(f"Using trending tokens fallback for new listings: {len(fallback_listings)} tokens")
                self.cache_manager.set(cache_key, fallback_listings, ttl=self.error_ttl)
                return fallback_listings
        except Exception as e:
            self.logger.warning(f"Trending tokens fallback also failed: {e}")
        
        self.logger.warning("Failed to get new listings from all endpoints and fallbacks")
        self.cache_manager.set(cache_key, [], ttl=self.error_ttl)
        return []

    async def get_gainers_losers(self, timeframe: str = "24h") -> Optional[List[Dict]]:
        """Fetch top traders by PnL, volume, trade count from Birdeye."""
        cache_key = f"{BIRDEYE_API_NAMESPACE}_gainers_losers_{timeframe}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye gainers/losers: {cache_key}")
            return cached_data
        self.logger.debug(f"Fetching Birdeye gainers/losers for {timeframe}")
        endpoint = "/trader/gainers-losers"
        params = {"timeframe": timeframe}
        try:
            response_data = await self._make_request_with_retry(endpoint, params=params)
            if response_data and isinstance(response_data, dict) and response_data.get('success'):
                # Handle the correct response structure: {"data": {"items": [...]}}
                data_field = response_data.get('data')
                traders = []
                
                if isinstance(data_field, dict) and 'items' in data_field:
                    # Extract items array from data dict
                    traders = data_field['items']
                    if isinstance(traders, list):
                        self.cache_manager.set(cache_key, traders, ttl=self.default_ttl)
                        return traders
                    else:
                        self.logger.warning(f"Items field is not a list: {type(traders)}")
                elif isinstance(data_field, list):
                    # If data is directly a list (fallback)
                    traders = data_field
                    self.cache_manager.set(cache_key, traders, ttl=self.default_ttl)
                    return traders
                else:
                    self.logger.warning(f"Unexpected data structure in gainers/losers response: {type(data_field)}")
                
                # If no valid traders found, return empty list
                self.logger.warning(f"No valid traders data in gainers/losers response for {timeframe}")
                self.cache_manager.set(cache_key, [], ttl=self.error_ttl)
                return []
            
            self.logger.warning(f"Failed to get gainers/losers from Birdeye. Response: {str(response_data)[:300]}")
            self.cache_manager.set(cache_key, [], ttl=self.error_ttl)
            return []
        except Exception as e:
            self.logger.error(f"Error fetching gainers/losers: {e}")
            self.cache_manager.set(cache_key, [], ttl=self.error_ttl)
            return []


    
    def _filter_solana_addresses(self, addresses: List[str]) -> Tuple[List[str], List[str]]:
        """
        Enhanced address filtering to handle edge cases that cause 'list_address is invalid format' errors.
        
        Args:
            addresses: List of addresses to filter
            
        Returns:
            Tuple of (valid_solana_addresses, filtered_out_addresses)
        """
        valid_addresses = []
        filtered_addresses = []
        
        for addr in addresses:
            # Skip None or empty addresses
            if not addr:
                filtered_addresses.append(f"<empty:{type(addr).__name__}>")
                continue
            
            # Convert to string and strip whitespace
            addr_str = str(addr).strip()
            
            # Skip empty strings after stripping
            if not addr_str:
                filtered_addresses.append("<empty_after_strip>")
                continue
            
            # Enhanced validation for Solana addresses
            if self._is_valid_solana_address(addr_str):
                valid_addresses.append(addr_str)
            else:
                filtered_addresses.append(addr_str)
        
        return valid_addresses, filtered_addresses

    def _is_valid_solana_address(self, address: str) -> bool:
        """
        Enhanced Solana address validation to prevent API format errors.
        
        Args:
            address: Address string to validate
            
        Returns:
            True if valid Solana address format
        """
        if not address or not isinstance(address, str):
            return False
        
        # Strip whitespace
        address = address.strip()
        
        # Check basic length (Solana addresses are typically 32-44 characters)
        if len(address) < 32 or len(address) > 44:
            return False
        
        # Solana addresses should not start with 0x (Ethereum format)
        if address.startswith('0x') or address.startswith('0X'):
            return False
        
        # Solana addresses use Base58 encoding
        # Valid characters: 123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz
        # (excludes 0, O, I, l to avoid confusion)
        valid_base58_chars = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
        
        # Check if all characters are valid Base58
        if not all(c in valid_base58_chars for c in address):
            return False
        
        # Additional checks for common invalid patterns
        if address.count(',') > 0:  # Should not contain commas
            return False
        
        if address.count(' ') > 0:  # Should not contain spaces
            return False
        
        # Check for suspicious patterns
        if address.startswith('http') or address.startswith('www'):
            return False
            
        if '.' in address and len(address.split('.')) > 1:  # Looks like URL or filename
            return False
        
        return True

    async def get_multi_price(self, addresses: list, include_liquidity: bool = True, scan_id: Optional[str] = None) -> Optional[dict]:
        """
        Enhanced version of multi_price with improved error handling and cost tracking.
        Now includes address validation to filter out non-Solana addresses.
        """
        if not addresses:
            return {}
        
        # Validate and clean addresses - ENHANCED with Solana address filtering
        if isinstance(addresses, list):
            # Filter out empty/invalid addresses and non-Solana addresses
            valid_addresses, filtered_addresses = self._filter_solana_addresses(addresses)
            
            if filtered_addresses:
                # Log filtered addresses for debugging
                self.logger.info(f"🔍 Filtered out {len(filtered_addresses)} non-Solana addresses from multi_price request")
                for addr in filtered_addresses[:5]:  # Show first 5 for debugging
                    addr_type = "Ethereum" if addr.startswith('0x') else "Unknown format"
                    self.logger.debug(f"  ❌ Filtered: {addr[:20]}... ({addr_type})")
                if len(filtered_addresses) > 5:
                    self.logger.debug(f"  ... and {len(filtered_addresses) - 5} more")
            
            if not valid_addresses:
                self.logger.warning("No valid Solana addresses provided to get_multi_price after filtering")
                return {}
            
            # Limit to maximum 100 tokens as per API documentation
            if len(valid_addresses) > 100:
                self.logger.warning(f"Too many addresses ({len(valid_addresses)}), limiting to 100")
                valid_addresses = valid_addresses[:100]
            
            address_param = ','.join(valid_addresses)
            num_tokens = len(valid_addresses)
            
            self.logger.debug(f"📊 Multi-price request: {num_tokens} valid Solana addresses (filtered out {len(filtered_addresses)} invalid)")
        else:
            # Handle string input (legacy support)
            address_param = addresses
            num_tokens = len(addresses.split(',')) if isinstance(addresses, str) else 1
            
        cache_key = f"{BIRDEYE_API_NAMESPACE}_multi_price_{address_param}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self._track_cache_hit(cache_key)
            self.logger.debug(f"Cache hit for Birdeye multi_price")
            return cached_data
            
        self._track_cache_miss(cache_key)
        endpoint = "/defi/multi_price"
        params = {
            "list_address": address_param,
            "include_liquidity": "true" if include_liquidity else "false"
        }
        
        try:
            # Use custom request method to track batch costs with Solana chain header
            response_data = await self._make_request_batch_aware(
                endpoint, 
                params, 
                num_tokens, 
                custom_headers={"x-chain": "solana"}
            )
            
            if response_data and isinstance(response_data, dict):
                # Handle different response formats
                if 'data' in response_data:
                    price_data = response_data['data']
                else:
                    price_data = response_data  # Some API versions return data directly
                    
                if isinstance(price_data, dict):
                    self.cache_manager.set(cache_key, price_data, ttl=self.default_ttl)
                    self.logger.debug(f"✅ Multi-price success: {len(price_data)} tokens with price data")
                    return price_data
                    
            self.logger.warning(f"Failed to get valid multi_price data. Response: {str(response_data)[:300]}")
            self.cache_manager.set(cache_key, {}, ttl=self.error_ttl)
            return {}
            
        except Exception as e:
            self.logger.error(f"Error in get_multi_price: {e}")
            self.cache_manager.set(cache_key, {}, ttl=self.error_ttl)
            return {}

    async def get_ohlcv_data(self, token_address: str, time_frame: str = '1m', limit: int = 60) -> Optional[List[Dict[str, Any]]]:
        """
        Get OHLCV (Open, High, Low, Close, Volume) data for a token using the working v3 endpoint.
        Enhanced with proper headers, time range parameters, and token-age awareness.
        
        Args:
            token_address: The token address to fetch OHLCV data for
            time_frame: Requested timeframe ('1s', '15s', '30s', '1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w') or 'auto'
            limit: Number of candles to fetch (not used in v3, controlled by time range)
            
        Returns:
            List of OHLCV candles or empty list if no data available
        """
        # Check if token should be excluded
        if self._should_skip_token(token_address):
            return []
            
        # Quick data availability check to avoid expensive calls
        try:
            from services.adaptive_rate_limiter import DataAvailabilityChecker
            availability_checker = DataAvailabilityChecker(self, self.cache_manager)
            availability_info = await availability_checker.check_data_availability(token_address)
            
            if availability_info.get("skip_ohlcv", True):
                reason = availability_info.get("reason", "no_trading_data")
                self.logger.debug(f"⏭️ Skipping OHLCV for {token_address}: {reason}")
                return []
        except ImportError:
            # Fallback if availability checker not available
            pass
            
        # Normalize time_frame format for v3 endpoint
        normalized_time_frame = time_frame
        
        # Define all available timeframes in order from shortest to longest
        all_timeframes = ['1s', '15s', '30s', '1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w']
        
        # If the client code requested 'auto' timeframe,
        # determine the appropriate timeframe based on token age
        if time_frame == 'auto':
            try:
                # Get token age and category
                age_days, age_category = await self.get_token_age(token_address)
                
                # Select appropriate timeframes based on age category
                # More granular selection based on precise age ranges
                if age_days < 0.01:  # < 15 minutes
                    age_appropriate_timeframe = '1s'  # Use finest granularity for extremely new tokens
                    fallback_timeframes = ['15s', '30s', '1m']
                elif age_days < 0.04:  # 15 min - 1 hour
                    age_appropriate_timeframe = '15s'  # Very fine granularity for very new tokens
                    fallback_timeframes = ['30s', '1m', '5m']
                elif age_days < 0.25:  # 1-6 hours
                    age_appropriate_timeframe = '30s'  # Fine granularity for very new tokens
                    fallback_timeframes = ['1m', '5m', '15m']
                elif age_days < 1:  # 6-24 hours
                    age_appropriate_timeframe = '1m'  # Fine granularity for new tokens
                    fallback_timeframes = ['5m', '15m', '30m']
                elif age_days < 3:  # 1-3 days
                    age_appropriate_timeframe = '5m'  # Medium-fine granularity
                    fallback_timeframes = ['15m', '30m', '1h']
                elif age_days < 7:  # 3-7 days
                    age_appropriate_timeframe = '15m'  # Medium granularity
                    fallback_timeframes = ['30m', '1h', '2h']
                elif age_days < 14:  # 7-14 days
                    age_appropriate_timeframe = '30m'  # Medium-coarse granularity
                    fallback_timeframes = ['1h', '2h', '4h']
                elif age_days < 30:  # 14-30 days
                    age_appropriate_timeframe = '1h'  # Medium-coarse granularity
                    fallback_timeframes = ['2h', '4h', '6h']
                elif age_days < 90:  # 1-3 months
                    age_appropriate_timeframe = '2h'  # Coarse granularity for established tokens
                    fallback_timeframes = ['4h', '6h', '12h']
                elif age_days < 180:  # 3-6 months
                    age_appropriate_timeframe = '4h'  # Coarse granularity for established tokens
                    fallback_timeframes = ['6h', '12h', '1d']
                else:  # > 6 months
                    age_appropriate_timeframe = '6h'  # Coarse granularity for mature tokens
                    fallback_timeframes = ['12h', '1d', '3d']
                
                self.logger.info(f"Token age category: {age_category} ({age_days:.2f} days), selected timeframe: {age_appropriate_timeframe}")
                normalized_time_frame = age_appropriate_timeframe
            except Exception as e:
                self.logger.error(f"Error determining age-appropriate timeframe: {e}, falling back to 1h")
                normalized_time_frame = '1h'  # Default fallback if age detection fails
                fallback_timeframes = ['2h', '4h', '1d']
        
        # Construct cache key with normalized timeframe
        cache_key = f"{BIRDEYE_API_NAMESPACE}_ohlcv_{token_address}_{normalized_time_frame}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for Birdeye OHLCV data: {cache_key}")
            return cached_data
            
        self.logger.debug(f"Fetching Birdeye OHLCV data for {token_address} with time_frame={normalized_time_frame}")
        
        # Calculate time range for the last 24 hours (v3 endpoint requires time_from and time_to)
        current_time = int(time.time())
        time_from = current_time - 86400  # 24 hours ago
        time_to = current_time
        
        # For very new tokens with sub-minute timeframes, use shorter time range
        if normalized_time_frame in ['1s', '15s', '30s']:
            time_from = current_time - 3600  # 1 hour ago for sub-minute data
        elif normalized_time_frame in ['1m', '5m']:
            time_from = current_time - 7200  # 2 hours ago for minute data
        
        # Primary v3 endpoint configuration (this is the working one!)
        v3_endpoint_config = {
            "url": "/defi/v3/ohlcv",
            "params": {
                "address": token_address,
                "type": self._normalize_timeframe_for_endpoint(normalized_time_frame, "v3"),
                "time_from": time_from,
                "time_to": time_to
            },
            "headers": {"x-chain": "solana"}  # Required header for v3 endpoint
        }
        
        # Try primary v3 endpoint first
        success = False
        ohlcv_data = []
        
        try:
            self.logger.debug(f"Trying v3 OHLCV endpoint with timeframe {normalized_time_frame}, time_from={time_from}, time_to={time_to}")
            
            response_data = await self._make_request_with_retry(
                v3_endpoint_config["url"], 
                params=v3_endpoint_config["params"], 
                custom_headers=v3_endpoint_config["headers"]
            )
            
            if response_data and isinstance(response_data, dict) and 'data' in response_data:
                data_content = response_data['data']
                if isinstance(data_content, dict) and 'items' in data_content:
                    ohlcv_data = data_content['items']
                    if isinstance(ohlcv_data, list) and len(ohlcv_data) > 0:
                        self.logger.info(f"✅ Successfully fetched {len(ohlcv_data)} OHLCV candles using v3 endpoint with {normalized_time_frame}")
                        success = True
                    else:
                        self.logger.debug(f"v3 endpoint returned empty items array for {token_address} with {normalized_time_frame}")
                else:
                    self.logger.debug(f"v3 endpoint returned unexpected data structure: {type(data_content)}")
            else:
                self.logger.debug(f"v3 endpoint returned invalid response format for {token_address}")
                
        except Exception as e:
            self.logger.warning(f"Error with v3 OHLCV endpoint for {token_address} with {normalized_time_frame}: {e}")
        
        # If primary timeframe failed and we're in auto mode, try fallback timeframes
        if not success and time_frame == 'auto' and 'fallback_timeframes' in locals():
            self.logger.info(f"Primary timeframe {normalized_time_frame} failed for {token_address}, trying fallback timeframes: {fallback_timeframes}")
            
            for fallback_tf in fallback_timeframes:
                self.logger.debug(f"Trying fallback timeframe {fallback_tf} for {token_address}")
                
                try:
                    # Adjust time range for fallback timeframe
                    if fallback_tf in ['1s', '15s', '30s']:
                        fallback_time_from = current_time - 3600  # 1 hour
                    elif fallback_tf in ['1m', '5m']:
                        fallback_time_from = current_time - 7200  # 2 hours
                    else:
                        fallback_time_from = current_time - 86400  # 24 hours
                    
                    fallback_params = {
                        "address": token_address,
                        "type": self._normalize_timeframe_for_endpoint(fallback_tf, "v3"),
                        "time_from": fallback_time_from,
                        "time_to": current_time
                    }
                    
                    response_data = await self._make_request_with_retry(
                        "/defi/v3/ohlcv", 
                        params=fallback_params, 
                        custom_headers={"x-chain": "solana"}
                    )
                    
                    if response_data and isinstance(response_data, dict) and 'data' in response_data:
                        data_content = response_data['data']
                        if isinstance(data_content, dict) and 'items' in data_content:
                            ohlcv_data = data_content['items']
                            if isinstance(ohlcv_data, list) and len(ohlcv_data) > 0:
                                self.logger.info(f"✅ Successfully fetched {len(ohlcv_data)} OHLCV candles using fallback timeframe {fallback_tf}")
                                success = True
                                break
                
                except Exception as e:
                    self.logger.debug(f"Fallback timeframe {fallback_tf} also failed: {e}")
                    continue
        
        # If v3 endpoint failed completely, try legacy base_quote endpoint as final fallback
        if not success:
            try:
                self.logger.debug("Trying legacy base_quote OHLCV endpoint as final fallback")
                usdc_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
                # Convert to uppercase format for base_quote endpoint (e.g., "4h" -> "4H")
                upper_time_frame = normalized_time_frame.upper() if normalized_time_frame.endswith('h') else normalized_time_frame
                
                legacy_response = await self._make_request("/defi/ohlcv/base_quote", params={
                    "base_address": token_address,
                    "quote_address": usdc_address,
                    "type": upper_time_frame
                })
                
                if legacy_response and isinstance(legacy_response, dict) and 'data' in legacy_response:
                    data_content = legacy_response['data']
                    if isinstance(data_content, dict) and 'items' in data_content:
                        ohlcv_data = data_content['items']
                        if isinstance(ohlcv_data, list) and len(ohlcv_data) > 0:
                            self.logger.info(f"✅ Successfully fetched {len(ohlcv_data)} OHLCV candles using legacy base_quote endpoint")
                            success = True
            except Exception as e:
                self.logger.warning(f"Legacy base_quote endpoint also failed for {token_address}: {e}")
        
        # Cache results (even if empty) to avoid repeated failed calls
        self.cache_manager.set(cache_key, ohlcv_data, ttl=self.default_ttl)
        
        if success and ohlcv_data:
            self.logger.info(f"🎯 OHLCV data fetched successfully for {token_address}: {len(ohlcv_data)} candles")
        else:
            self.logger.warning(f"⚠️ No OHLCV data available for {token_address} with timeframe {normalized_time_frame}")
        
        # Return data (empty list if no data found)
        return ohlcv_data if ohlcv_data else []

    async def get_token_transaction_volume(self, token_address: str, limit: int = 50, max_pages: int = 3) -> float:
        """
        Calculate the 24h trading volume for a token by aggregating transaction data.
        This is more accurate than the volume reported in token overview for some tokens.
        
        Args:
            token_address: The token address to analyze
            limit: Maximum number of transactions per page (max 50 for the API)
            max_pages: Maximum number of pages to fetch (for pagination)
            
        Returns:
            Total volume in USD equivalent
        """
        cache_key = f"{BIRDEYE_API_NAMESPACE}_tx_volume_{token_address}_{limit}_pages_{max_pages}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for transaction volume: {cache_key}")
            return cached_data
            
        self.logger.debug(f"Calculating transaction volume for {token_address} from up to {limit * max_pages} trades")
        
        # Fetch latest transactions with pagination
        txs = await self.get_token_transactions(token_address, limit=limit, max_pages=max_pages)
        
        # Calculate total volume in USD
        total_volume_usd = 0.0
        
        if txs:
            for tx in txs:
                volume_usd = self._extract_trade_volume_usd(tx)
                total_volume_usd += volume_usd
        
        self.logger.debug(f"Calculated transaction volume for {token_address}: ${total_volume_usd:.2f} from {len(txs)} transactions")
        self.cache_manager.set(cache_key, total_volume_usd, ttl=300)  # Cache for 5 minutes
        return total_volume_usd

    async def get_token_transactions(self, token_address: str, limit: int = 50, sort_type: str = "desc", max_pages: int = 1) -> List[Dict[str, Any]]:
        """
        Fetch token transactions from the Birdeye API with pagination support.
        
        Args:
            token_address: The token address to fetch transactions for
            limit: Maximum number of transactions per page (max 50 for the API)
            sort_type: Sort order - "desc" for newest first, "asc" for oldest first
            max_pages: Maximum number of pages to fetch for pagination
            
        Returns:
            List of transaction dictionaries
        """
        # Check if token should be excluded
        if self._should_skip_token(token_address):
            return []
            
        cache_key = f"{BIRDEYE_API_NAMESPACE}_transactions_{token_address}_{limit}_{sort_type}_{max_pages}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for token transactions: {cache_key}")
            return cached_data
        
        self.logger.debug(f"Fetching token transactions for {token_address} (limit={limit}, sort={sort_type}, max_pages={max_pages})")
        
        all_transactions = []
        
        # Ensure limit is within API constraints (1-50 for /defi/txs/token endpoint)
        api_limit = min(50, max(1, limit))
        
        for page in range(max_pages):
            offset = page * api_limit
        
            # Use the /defi/txs/token endpoint with Solana chain header
            params = {
                "address": token_address, 
                "offset": offset,
                "limit": api_limit,
                "tx_type": "swap",  # Focus on swap transactions for trading analysis
                "sort_type": sort_type
            }
            
            try:
                response_data = await self._make_request_with_retry(
                    "/defi/txs/token", 
                    params=params, 
                    custom_headers={"x-chain": "solana"}
                )
                
                transactions = []
                
                if response_data and isinstance(response_data, dict):
                    if "data" in response_data:
                        data_content = response_data["data"]
                        if isinstance(data_content, dict) and "items" in data_content:
                            transactions = data_content["items"]
                        elif isinstance(data_content, list):
                            transactions = data_content
                    elif "items" in response_data:
                        transactions = response_data["items"]
                    else:
                        # Some endpoints might return transactions directly
                        if isinstance(response_data, list):
                            transactions = response_data
                
                if not transactions:
                    # No more transactions available, stop pagination
                    self.logger.debug(f"No more transactions found for {token_address} at page {page + 1}")
                    break
                        
                # Normalize transaction format
                normalized_transactions = []
                for tx in transactions:
                    # Ensure required fields exist
                    if 'blockUnixTime' in tx and 'time' not in tx:
                        tx['time'] = tx['blockUnixTime']
                    
                    # Determine transaction side if not present
                    if 'side' not in tx and 'from' in tx and 'to' in tx:
                        if token_address == tx.get('from', {}).get('address'):
                            tx['side'] = 'sell'
                        elif token_address == tx.get('to', {}).get('address'):
                            tx['side'] = 'buy'
                            
                    normalized_transactions.append(tx)
                        
                all_transactions.extend(normalized_transactions)
                self.logger.debug(f"Fetched {len(normalized_transactions)} transactions for {token_address} (page {page + 1})")
                        
                # If we got fewer transactions than requested, there are no more pages
                if len(transactions) < api_limit:
                    break
            
            except Exception as e:
                self.logger.warning(f"Error fetching transactions for {token_address} (page {page + 1}): {e}")
                # Try fallback endpoint if primary fails
                if page == 0:  # Only try fallback on first page failure
                    try:
                        self.logger.debug(f"Trying fallback endpoint for {token_address} transactions")
                        fallback_response = await self._make_request("/defi/v3/token-activity", params={
                            "address": token_address,
                            "offset": offset,
                            "limit": api_limit
                        })
                        
                        if fallback_response and isinstance(fallback_response, dict) and "data" in fallback_response:
                            fallback_data = fallback_response["data"]
                            if isinstance(fallback_data, dict) and "items" in fallback_data:
                                fallback_transactions = fallback_data["items"]
                                all_transactions.extend(fallback_transactions)
                                self.logger.debug(f"Fetched {len(fallback_transactions)} transactions using fallback endpoint")
                    except Exception as fallback_error:
                        self.logger.warning(f"Fallback endpoint also failed for {token_address}: {fallback_error}")
                break
        
        self.logger.debug(f"Total transactions fetched for {token_address}: {len(all_transactions)}")
        
        # Cache results for 5 minutes (shorter TTL since transaction data changes frequently)
        self.cache_manager.set(cache_key, all_transactions, ttl=300)
        return all_transactions

    def _extract_trade_volume_usd(self, transaction: Dict[str, Any]) -> float:
        """
        Extract USD volume from a transaction object.
        
        Args:
            transaction: Transaction dictionary from Birdeye API
            
        Returns:
            Volume in USD as float
        """
        try:
            # Debug log the transaction structure on first few calls
            if not hasattr(self, '_logged_tx_structure'):
                self.logger.debug(f"🔍 Transaction structure sample: {list(transaction.keys())}")
                if 'quote' in transaction:
                    self.logger.debug(f"🔍 Quote structure: {list(transaction['quote'].keys()) if isinstance(transaction['quote'], dict) else type(transaction['quote'])}")
                if 'base' in transaction:
                    self.logger.debug(f"🔍 Base structure: {list(transaction['base'].keys()) if isinstance(transaction['base'], dict) else type(transaction['base'])}")
                self._logged_tx_structure = True
            
            # Try different possible volume fields in the transaction
            volume_usd = 0.0
            
            # Method 1: Direct volume_usd field
            if 'volume_usd' in transaction:
                volume_usd = float(transaction['volume_usd'])
                self.logger.debug(f"📊 Volume from volume_usd: ${volume_usd:.2f}")
            
            # Method 2: volumeInUsd field
            elif 'volumeInUsd' in transaction:
                volume_usd = float(transaction['volumeInUsd'])
                self.logger.debug(f"📊 Volume from volumeInUsd: ${volume_usd:.2f}")
            
            # Method 3: Check for quote (SOL) side volume - most reliable for Solana
            elif 'quote' in transaction:
                quote_data = transaction['quote']
                if isinstance(quote_data, dict):
                    # Try quote amount * quote price (uiAmountString version)
                    if 'uiAmountString' in quote_data and 'priceInUsd' in quote_data:
                        amount = float(quote_data['uiAmountString'])
                        price = float(quote_data['priceInUsd'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from quote (uiAmountString * priceInUsd): {amount} * ${price} = ${volume_usd:.2f}")
                    # Try quote amount * quote price (uiAmount version)
                    elif 'uiAmount' in quote_data and 'priceInUsd' in quote_data:
                        amount = float(quote_data['uiAmount'])
                        price = float(quote_data['priceInUsd'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from quote (uiAmount * priceInUsd): {amount} * ${price} = ${volume_usd:.2f}")
                    # Try quote amount * quote price (using 'price' field - common in Birdeye)
                    elif 'uiAmount' in quote_data and 'price' in quote_data:
                        amount = float(quote_data['uiAmount'])
                        price = float(quote_data['price'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from quote (uiAmount * price): {amount} * ${price} = ${volume_usd:.2f}")
                    # Try uiAmountString with 'price' field
                    elif 'uiAmountString' in quote_data and 'price' in quote_data:
                        amount = float(quote_data['uiAmountString'])
                        price = float(quote_data['price'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from quote (uiAmountString * price): {amount} * ${price} = ${volume_usd:.2f}")
                    # Try direct quote value
                    elif 'valueInUsd' in quote_data:
                        volume_usd = float(quote_data['valueInUsd'])
                        self.logger.debug(f"📊 Volume from quote valueInUsd: ${volume_usd:.2f}")
            
            # Method 4: Check for base token side volume
            elif 'base' in transaction:
                base_data = transaction['base']
                if isinstance(base_data, dict):
                    if 'uiAmountString' in base_data and 'priceInUsd' in base_data:
                        amount = float(base_data['uiAmountString'])
                        price = float(base_data['priceInUsd'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from base (uiAmountString * priceInUsd): {amount} * ${price} = ${volume_usd:.2f}")
                    elif 'uiAmount' in base_data and 'priceInUsd' in base_data:
                        amount = float(base_data['uiAmount'])
                        price = float(base_data['priceInUsd'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from base (uiAmount * priceInUsd): {amount} * ${price} = ${volume_usd:.2f}")
                    # Try base amount * base price (using 'price' field - common in Birdeye)
                    elif 'uiAmount' in base_data and 'price' in base_data:
                        amount = float(base_data['uiAmount'])
                        price = float(base_data['price'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from base (uiAmount * price): {amount} * ${price} = ${volume_usd:.2f}")
                    # Try uiAmountString with 'price' field
                    elif 'uiAmountString' in base_data and 'price' in base_data:
                        amount = float(base_data['uiAmountString'])
                        price = float(base_data['price'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from base (uiAmountString * price): {amount} * ${price} = ${volume_usd:.2f}")
                    elif 'valueInUsd' in base_data:
                        volume_usd = float(base_data['valueInUsd'])
                        self.logger.debug(f"📊 Volume from base valueInUsd: ${volume_usd:.2f}")
            
            # Method 5: Calculate from token amounts and prices (legacy)
            elif 'from' in transaction and 'to' in transaction:
                from_data = transaction['from']
                to_data = transaction['to']
                
                # Try to get USD value from either side of the trade
                if isinstance(from_data, dict):
                    if 'uiAmountString' in from_data and 'priceInUsd' in from_data:
                        amount = float(from_data['uiAmountString'])
                        price = float(from_data['priceInUsd'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from 'from' side (uiAmountString * priceInUsd): {amount} * ${price} = ${volume_usd:.2f}")
                    elif 'uiAmount' in from_data and 'priceInUsd' in from_data:
                        amount = float(from_data['uiAmount'])
                        price = float(from_data['priceInUsd'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from 'from' side (uiAmount * priceInUsd): {amount} * ${price} = ${volume_usd:.2f}")
                    elif 'uiAmount' in from_data and 'price' in from_data:
                        amount = float(from_data['uiAmount'])
                        price = float(from_data['price'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from 'from' side (uiAmount * price): {amount} * ${price} = ${volume_usd:.2f}")
                    elif 'uiAmountString' in from_data and 'price' in from_data:
                        amount = float(from_data['uiAmountString'])
                        price = float(from_data['price'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from 'from' side (uiAmountString * price): {amount} * ${price} = ${volume_usd:.2f}")
                
                if volume_usd == 0.0 and isinstance(to_data, dict):
                    if 'uiAmountString' in to_data and 'priceInUsd' in to_data:
                        amount = float(to_data['uiAmountString'])
                        price = float(to_data['priceInUsd'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from 'to' side (uiAmountString * priceInUsd): {amount} * ${price} = ${volume_usd:.2f}")
                    elif 'uiAmount' in to_data and 'priceInUsd' in to_data:
                        amount = float(to_data['uiAmount'])
                        price = float(to_data['priceInUsd'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from 'to' side (uiAmount * priceInUsd): {amount} * ${price} = ${volume_usd:.2f}")
                    elif 'uiAmount' in to_data and 'price' in to_data:
                        amount = float(to_data['uiAmount'])
                        price = float(to_data['price'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from 'to' side (uiAmount * price): {amount} * ${price} = ${volume_usd:.2f}")
                    elif 'uiAmountString' in to_data and 'price' in to_data:
                        amount = float(to_data['uiAmountString'])
                        price = float(to_data['price'])
                        volume_usd = amount * price
                        self.logger.debug(f"📊 Volume from 'to' side (uiAmountString * price): {amount} * ${price} = ${volume_usd:.2f}")
            
            # Method 6: Look for other common volume fields
            elif 'value' in transaction:
                volume_usd = float(transaction['value'])
                self.logger.debug(f"📊 Volume from 'value': ${volume_usd:.2f}")
            elif 'amount_usd' in transaction:
                volume_usd = float(transaction['amount_usd'])
                self.logger.debug(f"📊 Volume from 'amount_usd': ${volume_usd:.2f}")
            elif 'usd_amount' in transaction:
                volume_usd = float(transaction['usd_amount'])
                self.logger.debug(f"📊 Volume from 'usd_amount': ${volume_usd:.2f}")
            elif 'valueInUsd' in transaction:
                volume_usd = float(transaction['valueInUsd'])
                self.logger.debug(f"📊 Volume from 'valueInUsd': ${volume_usd:.2f}")
            
            if volume_usd == 0.0:
                # Log a sample transaction structure for debugging
                if not hasattr(self, '_logged_failed_extraction'):
                    self.logger.debug(f"🔍 Failed to extract volume from transaction: {transaction}")
                    self._logged_failed_extraction = True
            
            return max(0.0, volume_usd)  # Ensure non-negative
            
        except (ValueError, TypeError, KeyError) as e:
            self.logger.debug(f"Error extracting volume from transaction: {e}")
            return 0.0

    async def get_historical_trade_data(self, token_address: str, time_intervals: List[int], limit: int = 50, max_pages: int = 1) -> Dict[str, List[Dict]]:
        """
        Fetch historical trade data for multiple time intervals to analyze trend dynamics.
        
        Args:
            token_address: The address of the token to analyze
            time_intervals: List of time intervals in seconds (e.g., [60, 300, 3600, 86400] for 1min, 5min, 1hr, 1day)
            limit: Maximum number of trades to fetch per page (max 50 for /defi/txs/token endpoint)
            max_pages: Maximum number of pages to fetch per interval
            
        Returns:
            Dictionary mapping interval -> list of trades
        """
        cache_key = f"{BIRDEYE_API_NAMESPACE}_historical_trades_{token_address}_{'-'.join(map(str, time_intervals))}_pages_{max_pages}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for historical trade data: {cache_key}")
            return cached_data
            
        self.logger.debug(f"Fetching historical trade data for {token_address} across {len(time_intervals)} intervals with up to {max_pages} pages each")
        
        now = int(time.time())
        result = {}
        
        # Ensure limit is within allowed range for /defi/txs/token endpoint (1-50)
        txs_token_limit = min(50, limit)
        
        for interval in time_intervals:
            time_from = now - interval
            result[interval] = []
            
            # Paginated fetching for each interval
            for page in range(max_pages):
                offset = page * txs_token_limit
                
                # First try the new txs/token endpoint with time parameters
                params = {
                    "address": token_address,
                    "offset": offset,
                    "limit": txs_token_limit,  # Use restricted limit for this endpoint
                    "tx_type": "swap",
                    "sort_type": "desc",
                    "from_time": time_from,
                    "to_time": now
                }
                
                try:
                    # Try the new endpoint with x-chain header
                    data = await self._make_request("/defi/txs/token", params=params, custom_headers={"x-chain": "solana"})
                    trades = []
                    
                    if data and isinstance(data, dict) and "data" in data:
                        if isinstance(data["data"], dict) and "items" in data["data"]:
                            trades = data["data"]["items"]
                        elif isinstance(data["data"], list):
                            trades = data["data"]
                        
                        # If no trades in this page, stop pagination for this interval
                        if not trades:
                            break
                    
                    # Normalize trades format for consistency if trades were found
                    normalized_trades = []
                    for trade in trades:
                        # Ensure side is set based on token address
                        if 'side' not in trade and 'from' in trade and 'to' in trade:
                            if token_address == trade.get('from', {}).get('address'):
                                trade['side'] = 'sell'
                            elif token_address == trade.get('to', {}).get('address'):
                                trade['side'] = 'buy'
                        
                        # Ensure timestamp field exists
                        if 'blockUnixTime' in trade and 'time' not in trade:
                            trade['time'] = trade['blockUnixTime']
                            
                        normalized_trades.append(trade)
                    
                    self.logger.debug(f"Successfully fetched {len(normalized_trades)} trades from /defi/txs/token for {token_address} in {interval}s interval (page {page+1})")
                    result[interval].extend(normalized_trades)
                    
                    # If we got fewer trades than the limit, there are no more to fetch
                    if len(trades) < txs_token_limit:
                        break
                except Exception as e:
                    self.logger.error(f"Error fetching historical trades for {token_address} in {interval}s interval (page {page+1}): {e}")
                    break
            
            # If we got no data from the primary endpoint, try fallbacks
            if not result[interval]:
                self.logger.warning(f"No trades found for {token_address} in {interval}s interval using primary endpoint, trying fallbacks")
                
                try:
                    # Fall back to v3/token-activity
                    params = {
                        "address": token_address,
                        "offset": 0,
                        "limit": limit,
                        "fromTime": time_from,
                        "toTime": now
                    }
                    
                    data = await self._make_request("/defi/v3/token-activity", params=params)
                    trades = []
                    
                    if data and isinstance(data, dict) and "data" in data:
                        if isinstance(data["data"], dict) and "items" in data["data"]:
                            trades = data["data"]["items"]
                        elif isinstance(data["data"], list):
                            trades = data["data"]
                        
                        if trades:
                            result[interval] = trades
                            self.logger.debug(f"Fetched {len(trades)} trades from fallback endpoint for {token_address} in {interval}s interval")
                
                except Exception as e:
                    self.logger.error(f"Error fetching fallback trades for {token_address} in {interval}s interval: {e}")
        
        self.cache_manager.set(cache_key, result, ttl=self.default_ttl)
        return result

    # List of known smart money wallets for Solana - regularly updated
    # This is just a starting point and should be expanded with more wallets over time
    SMART_MONEY_WALLETS = {
        # Solana Foundation
        "5yb3D1KBy13czATSYGLUbZrYJvRvFQiH9XYkAeG2nDzH": "Solana Foundation",
        "HrwRZw4ZpEGgkzgDY1LrU8rgJZeYCNwRaf9LNkWJHRjH": "Solana Foundation",
        
        # Major funds and VCs
        "65CmecDnuFAYJv8D8Ax3m3eNEGe4NQvrJV2GJPFMtATH": "Jump Capital",
        "9iDWyYZ5VHBCxxmWZogoY3Z6FSbKsX7xKTLSrMJRYmb": "Multicoin Capital",
        "CXWNm8HKVGA2jX8tfZEfW9NjJdmfrmQUgLyYCcNnPrAL": "Three Arrows Capital",
        
        # Well-known traders
        "AySc5J6asYDPLCgk9Lzn3ebPfEtWYGDWYTzNxJyf5dan": "Top Trader 1",
        "HHvNuiQF21eSYo1o9KN5QFpqwGf7dDM2EbCkZ5CJ9ihD": "Top Trader 2",
        "E9bQjuJxF5xiZwBFKjgFC4P4kfMv3aJKJaXw3EPxLKVw": "Top Trader 3",
        
        # Major DEXes and protocols
        "DEX1CZAcuP3vfiGP7BmSbZY5AAv81TzjX4JR6Tmy2rZ": "Orca Protocol",
        "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1": "Raydium Protocol"
    }
    
    def _is_smart_money_wallet(self, wallet_address: str) -> bool:
        """
        Check if a wallet address belongs to a known smart money entity.
        
        Args:
            wallet_address: The wallet address to check
            
        Returns:
            True if the wallet is a known smart money wallet, False otherwise
        """
        return wallet_address in self.SMART_MONEY_WALLETS
    
    async def detect_smart_money_activity(self, token_address: str, max_pages: int = 3) -> Dict[str, Any]:
        """
        Detect if any smart money wallets have interacted with a token.
        
        Args:
            token_address: The token address to analyze
            max_pages: Number of transaction pages to analyze
            
        Returns:
            Dictionary with smart money activity metrics
        """
        cache_key = f"{BIRDEYE_API_NAMESPACE}_smart_money_{token_address}_pages_{max_pages}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"Cache hit for smart money detection: {cache_key}")
            return cached_data
            
        self.logger.debug(f"Analyzing smart money activity for {token_address}")
        
        # Get recent transactions with pagination
        txs = await self.get_token_transactions(token_address, limit=50, max_pages=max_pages)
        
        result = {
            "has_smart_money": False,
            "smart_money_wallets": [],
            "smart_money_buy_count": 0,
            "smart_money_sell_count": 0,
            "total_smart_money_volume_usd": 0.0,
            "percent_of_transactions": 0.0
        }
        
        if not txs:
            self.logger.debug(f"No transactions found for {token_address}, cannot detect smart money activity")
            self.cache_manager.set(cache_key, result, ttl=300)
            return result
            
        # Analyze transactions for smart money involvement
        smart_money_wallets = set()
        smart_money_txs = []
        
        for tx in txs:
            owner = tx.get("owner")
            if owner and self._is_smart_money_wallet(owner):
                smart_money_wallets.add(owner)
                smart_money_txs.append(tx)
                
                # Track buy/sell activity
                if tx.get("side") == "buy":
                    result["smart_money_buy_count"] += 1
                elif tx.get("side") == "sell":
                    result["smart_money_sell_count"] += 1
                    
                # Calculate volume
                volume_usd = self._extract_trade_volume_usd(tx)
                result["total_smart_money_volume_usd"] += volume_usd
        
        # Update results
        result["has_smart_money"] = len(smart_money_wallets) > 0
        result["smart_money_wallets"] = list(smart_money_wallets)
        result["percent_of_transactions"] = (len(smart_money_txs) / len(txs)) * 100 if txs else 0
        
        self.logger.debug(f"Smart money analysis for {token_address}: {result['has_smart_money']}, wallets: {len(result['smart_money_wallets'])}")
        self.cache_manager.set(cache_key, result, ttl=300)
        return result

    async def get_token_list(self, sort_by: str = "volume_24h_usd", sort_type: str = "desc", 
                           min_liquidity: float = 1000000, min_volume_24h_usd: float = 100000,
                           limit: int = 20, offset: int = 0, min_holder: int = None, 
                           min_trade_24h_count: int = None) -> Optional[Dict]:
        """
        Get token list with automatic fallback to V1 endpoint if V3 access is restricted.
        
        Args:
            sort_by: Sort field (volume_24h_usd, trade_24h_count, etc.)
            sort_type: Sort direction (desc, asc)
            min_liquidity: Minimum liquidity filter
            min_volume_24h_usd: Minimum 24h volume filter
            limit: Number of tokens to return
            offset: Pagination offset
            min_holder: Minimum holder count
            min_trade_24h_count: Minimum 24h trade count
            
        Returns:
            Dict with token list data in standardized format
        """
        # Build parameters for V3 endpoint
        params = {
            "sort_by": sort_by,
            "sort_type": sort_type,
            "limit": min(limit, 100),  # V3 endpoint max is 100
            "offset": offset
        }
        
        # Add optional filters
        if min_liquidity is not None:
            params["min_liquidity"] = min_liquidity
        if min_volume_24h_usd is not None:
            params["min_volume_24h_usd"] = min_volume_24h_usd
        if min_holder is not None:
            params["min_holder"] = min_holder
        if min_trade_24h_count is not None:
            params["min_trade_24h_count"] = min_trade_24h_count
        
        try:
            # Try V3 endpoint first
            response = await self._make_request("/defi/v3/token/list", params=params)
            if response and response.get("success"):
                # V3 endpoint success - standardize the response format
                return self._standardize_token_list_response(response, "v3")
                
        except Exception as e:
            if "401" in str(e) or "permission" in str(e).lower():
                self.logger.warning(f"V3 endpoint access restricted, falling back to V1: {e}")
                # Fall back to V1 endpoint
                return await self._get_token_list_v1_fallback(sort_by, sort_type, min_liquidity, 
                                                            min_volume_24h_usd, limit, offset, 
                                                            min_holder, min_trade_24h_count)
            else:
                self.logger.error(f"Token list request failed: {e}")
                raise e
        
        # If V3 failed without 401, try V1 fallback
        self.logger.warning("V3 endpoint returned no data, trying V1 fallback")
        return await self._get_token_list_v1_fallback(sort_by, sort_type, min_liquidity, 
                                                    min_volume_24h_usd, limit, offset, 
                                                    min_holder, min_trade_24h_count)
    
    async def _get_token_list_v1_fallback(self, sort_by: str, sort_type: str, 
                                        min_liquidity: float, min_volume_24h_usd: float,
                                        limit: int, offset: int, min_holder: int, 
                                        min_trade_24h_count: int) -> Optional[Dict]:
        """
        Fallback to V1 tokenlist endpoint when V3 access is restricted.
        
        Maps V3 parameters to V1 format and standardizes the response.
        """
        # Map V3 sort parameters to V1 format
        v1_sort_mapping = {
            "volume_24h_usd": "v24hUSD",
            "trade_24h_count": "trade24h",
            "liquidity": "liquidity",
            "market_cap": "mc"
        }
        
        v1_sort_by = v1_sort_mapping.get(sort_by, "v24hUSD")
        
        # Build V1 parameters
        v1_params = {
            "sort_by": v1_sort_by,
            "sort_type": sort_type,
            "limit": limit,
            "offset": offset
        }
        
        # Add filters (V1 uses different parameter names)
        if min_liquidity is not None:
            v1_params["min_liquidity"] = min_liquidity
        if min_volume_24h_usd is not None:
            v1_params["min_volume_24h_usd"] = min_volume_24h_usd
        if min_holder is not None:
            v1_params["min_holder"] = min_holder
        if min_trade_24h_count is not None:
            v1_params["min_trade_24h_count"] = min_trade_24h_count
        
        try:
            response = await self._make_request("/defi/tokenlist", params=v1_params)
            if response and response.get("success"):
                return self._standardize_token_list_response(response, "v1")
            else:
                self.logger.error(f"V1 fallback also failed: {response}")
                return None
                
        except Exception as e:
            self.logger.error(f"V1 fallback request failed: {e}")
            return None
    
    def _standardize_token_list_response(self, response: Dict, endpoint_version: str) -> Dict:
        """
        Standardize token list response format from different API versions.
        
        Args:
            response: Raw API response
            endpoint_version: "v1" or "v3"
            
        Returns:
            Standardized response in the format expected by strategies
        """
        try:
            if endpoint_version == "v3":
                # V3 format: {"success": true, "data": {"items": [...]}}
                data = response.get("data", {})
                if "items" in data:
                    tokens = data["items"]
                elif "tokens" in data:
                    # Handle nested tokens structure
                    token_data = data["tokens"]
                    if isinstance(token_data, list) and len(token_data) > 0:
                        # Extract tokens from nested structure
                        tokens = []
                        for item in token_data:
                            if isinstance(item, dict) and "items" in item:
                                tokens.extend(item["items"])
                            else:
                                tokens.append(item)
                    else:
                        tokens = token_data
                else:
                    tokens = []
                    
            elif endpoint_version == "v1":
                # V1 format: {"success": true, "data": {"tokens": [...]}}
                data = response.get("data", {})
                tokens = data.get("tokens", [])
            else:
                self.logger.error(f"Unknown endpoint version: {endpoint_version}")
                return {"success": False, "data": {"tokens": []}}
            
            # Return in standardized format
            standardized = {
                "success": True,
                "data": {
                    "tokens": tokens,
                    "total": len(tokens),
                    "endpoint_used": endpoint_version
                }
            }
            
            self.logger.info(f"Standardized {endpoint_version} response: {len(tokens)} tokens")
            return standardized
            
        except Exception as e:
            self.logger.error(f"Error standardizing response: {e}")
            return {"success": False, "data": {"tokens": []}}

    async def make_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, custom_headers: Optional[Dict[str, str]] = None) -> Any:
        """
        Public wrapper for _make_request to maintain compatibility with TraderPerformanceAnalyzer
        
        Args:
            method: HTTP method (GET, POST, etc.) - kept for compatibility but not used as API is GET-only
            endpoint: API endpoint path
            params: Query parameters
            custom_headers: Additional headers
            
        Returns:
            API response data or None
        """
        # BirdeyeAPI only supports GET requests, so we ignore the method parameter
        return await self._make_request(endpoint, params, custom_headers)

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance and monitoring statistics.
        
        Returns:
            Dictionary with detailed performance metrics and health indicators
        """
        total_requests = self.performance_metrics['total_requests']
        successful_requests = self.performance_metrics['successful_requests']
        failed_requests = self.performance_metrics['failed_requests']
        
        # Calculate success rate
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Get cache statistics
        cache_stats = self.cache_manager.get_cache_stats() if hasattr(self.cache_manager, 'get_cache_stats') else {}
        
        # Calculate uptime
        uptime_seconds = time.time() - self.performance_metrics['last_reset']
        uptime_hours = uptime_seconds / 3600
        
        # Calculate requests per hour
        requests_per_hour = total_requests / uptime_hours if uptime_hours > 0 else 0
        
        # Health status
        health_status = "Healthy"
        if success_rate < 80:
            health_status = "Degraded"
        elif success_rate < 50:
            health_status = "Unhealthy"
        elif self.performance_metrics['rate_limit_hits'] > total_requests * 0.1:
            health_status = "Rate Limited"
        
        return {
            # Overall health
            'health_status': health_status,
            'success_rate_percent': round(success_rate, 2),
            'uptime_hours': round(uptime_hours, 2),
            
            # Request metrics
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'rate_limit_hits': self.performance_metrics['rate_limit_hits'],
            'requests_per_hour': round(requests_per_hour, 2),
            
            # Performance metrics
            'average_response_time_ms': round(self.performance_metrics['average_response_time'] * 1000, 2),
            'recent_response_times': [round(t * 1000, 2) for t in self.performance_metrics['response_times'][-10:]],
            
            # Cache metrics
            'cache_statistics': cache_stats,
            
            # Configuration
            'rate_limit_per_minute': self.rate_limit,
            'timeout_seconds': self.config.get('request_timeout_seconds', 20),
            'max_retries': self.max_retries,
            
            # Last reset
            'stats_reset_time': self.performance_metrics['last_reset'],
        }

    def reset_performance_stats(self) -> None:
        """Reset performance statistics for a new monitoring period"""
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'rate_limit_hits': 0,
            'average_response_time': 0.0,
            'response_times': [],
            'last_reset': time.time()
        }
        self.logger.info("📊 Performance statistics reset")

    def log_performance_summary(self) -> None:
        """Log a comprehensive performance summary"""
        stats = self.get_performance_stats()
        
        self.logger.info("📊 API PERFORMANCE SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"🏥 Health Status: {stats['health_status']}")
        self.logger.info(f"✅ Success Rate: {stats['success_rate_percent']}%")
        self.logger.info(f"⏱️  Average Response Time: {stats['average_response_time_ms']}ms")
        self.logger.info(f"📞 Total Requests: {stats['total_requests']}")
        self.logger.info(f"🚀 Requests/Hour: {stats['requests_per_hour']}")
        
        if stats['rate_limit_hits'] > 0:
            self.logger.warning(f"🚫 Rate Limit Hits: {stats['rate_limit_hits']}")
        
        if stats['failed_requests'] > 0:
            failure_rate = (stats['failed_requests'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
            self.logger.warning(f"❌ Failed Requests: {stats['failed_requests']} ({failure_rate:.1f}%)")
        
        self.logger.info(f"🕒 Uptime: {stats['uptime_hours']:.1f} hours")
        self.logger.info("=" * 50)

    def get_api_call_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive API call statistics with detailed breakdown.
        
        Returns:
            Dictionary with detailed API call metrics, cache performance, and endpoint analysis
        """
        total_calls = self.api_call_tracker['total_api_calls']
        successful_calls = self.api_call_tracker['successful_api_calls']
        failed_calls = self.api_call_tracker['failed_api_calls']
        cache_hits = self.api_call_tracker['cache_hits']
        cache_misses = self.api_call_tracker['cache_misses']
        
        # Calculate rates and percentages
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        failure_rate = (failed_calls / total_calls * 100) if total_calls > 0 else 0
        cache_hit_rate = (cache_hits / (cache_hits + cache_misses) * 100) if (cache_hits + cache_misses) > 0 else 0
        
        # Calculate session duration and call rates
        session_duration_seconds = time.time() - self.api_call_tracker['session_start_time']
        session_duration_minutes = session_duration_seconds / 60
        calls_per_minute = total_calls / session_duration_minutes if session_duration_minutes > 0 else 0
        
        # Calculate average response time
        avg_response_time_ms = (self.api_call_tracker['total_response_time_ms'] / total_calls) if total_calls > 0 else 0
        
        # Get top endpoints by usage
        top_endpoints = sorted(
            self.api_call_tracker['calls_by_endpoint'].items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )[:10]  # Top 10 endpoints
        
        return {
            # Overall API call metrics
            'total_api_calls': total_calls,
            'successful_api_calls': successful_calls,
            'failed_api_calls': failed_calls,
            'success_rate_percent': round(success_rate, 2),
            'failure_rate_percent': round(failure_rate, 2),
            
            # Cache performance
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'total_cache_requests': cache_hits + cache_misses,
            
            # Performance metrics
            'average_response_time_ms': round(avg_response_time_ms, 2),
            'total_response_time_ms': self.api_call_tracker['total_response_time_ms'],
            
            # Session metrics
            'session_duration_minutes': round(session_duration_minutes, 2),
            'calls_per_minute': round(calls_per_minute, 2),
            'session_start_time': self.api_call_tracker['session_start_time'],
            
            # Detailed breakdowns
            'calls_by_status_code': dict(self.api_call_tracker['calls_by_status_code']),
            'calls_by_endpoint': dict(self.api_call_tracker['calls_by_endpoint']),
            'top_endpoints': [
                {
                    'endpoint': endpoint,
                    'total_calls': stats['total'],
                    'successful_calls': stats['successful'],
                    'failed_calls': stats['failed'],
                    'success_rate_percent': round((stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0, 2),
                    'avg_response_time_ms': round(stats['avg_response_time_ms'], 2)
                }
                for endpoint, stats in top_endpoints
            ],
            
            # API efficiency metrics
            'api_calls_vs_cache_ratio': round(total_calls / (cache_hits + total_calls), 2) if (cache_hits + total_calls) > 0 else 0,
            'cache_efficiency_score': round(cache_hit_rate / 100, 2),  # 0-1 score
            
            # Cost tracking (if available)
            'cost_tracking': self.cost_calculator.get_session_summary() if self.cost_calculator else {},
            
            # Health indicators
            'health_status': self._get_api_health_status(),
            'last_reset_time': self.api_call_tracker['last_reset_time']
        }

    def _get_api_health_status(self) -> str:
        """Determine API health status based on metrics."""
        total_calls = self.api_call_tracker['total_api_calls']
        if total_calls == 0:
            return "No Activity"
        
        success_rate = (self.api_call_tracker['successful_api_calls'] / total_calls * 100)
        avg_response_time_ms = (self.api_call_tracker['total_response_time_ms'] / total_calls)
        
        if success_rate >= 95 and avg_response_time_ms < 1000:
            return "Excellent"
        elif success_rate >= 90 and avg_response_time_ms < 2000:
            return "Good"
        elif success_rate >= 80 and avg_response_time_ms < 5000:
            return "Fair"
        elif success_rate >= 60:
            return "Poor"
        else:
            return "Critical"

    def log_api_call_summary(self) -> None:
        """Log a comprehensive API call summary with detailed metrics."""
        stats = self.get_api_call_statistics()
        
        self.logger.info("📊 COMPREHENSIVE API CALL SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"🏥 API Health Status: {stats['health_status']}")
        self.logger.info(f"📞 Total API Calls: {stats['total_api_calls']}")
        self.logger.info(f"✅ Successful Calls: {stats['successful_api_calls']} ({stats['success_rate_percent']}%)")
        self.logger.info(f"❌ Failed Calls: {stats['failed_api_calls']} ({stats['failure_rate_percent']}%)")
        self.logger.info(f"⚡ Calls/Minute: {stats['calls_per_minute']:.1f}")
        self.logger.info(f"⏱️  Avg Response Time: {stats['average_response_time_ms']:.0f}ms")
        
        self.logger.info(f"📋 Cache Performance:")
        self.logger.info(f"  • Cache Hits: {stats['cache_hits']}")
        self.logger.info(f"  • Cache Misses: {stats['cache_misses']}")
        self.logger.info(f"  • Cache Hit Rate: {stats['cache_hit_rate_percent']:.1f}%")
        
        if stats['top_endpoints']:
            self.logger.info(f"🔗 Top API Endpoints:")
            for i, endpoint_data in enumerate(stats['top_endpoints'][:5], 1):
                self.logger.info(f"  {i}. {endpoint_data['endpoint']}: {endpoint_data['total_calls']} calls ({endpoint_data['success_rate_percent']:.1f}% success)")
        
        if stats['calls_by_status_code']:
            self.logger.info(f"📊 Status Code Breakdown: {stats['calls_by_status_code']}")
        
        self.logger.info(f"🕒 Session Duration: {stats['session_duration_minutes']:.1f} minutes")
        self.logger.info("=" * 60)

    def reset_api_call_statistics(self) -> None:
        """Reset API call statistics for a new monitoring period."""
        self.api_call_tracker = {
            'total_api_calls': 0,
            'successful_api_calls': 0,
            'failed_api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'calls_by_endpoint': {},
            'calls_by_status_code': {},
            'total_response_time_ms': 0,
            'session_start_time': time.time(),
            'last_reset_time': time.time()
        }
        
        # Also reset legacy performance metrics
        self.reset_performance_stats()
        self.logger.info("📊 API call statistics reset")

    async def _get_earliest_transaction(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Find the earliest transaction for a token to determine creation time.
        
        Args:
            token_address: The token address to analyze
            
        Returns:
            The earliest transaction data with 'time' field or None if not found
        """
        try:
            # Fetch transactions sorted by oldest first (ascending time)
            txs = await self.get_token_transactions(token_address, limit=1, sort_type="asc")
            
            if txs and len(txs) > 0:
                earliest_tx = txs[0]
                
                # Ensure the time field exists (normalize different time field names)
                if 'blockUnixTime' in earliest_tx and 'time' not in earliest_tx:
                    earliest_tx['time'] = earliest_tx['blockUnixTime']
                elif 'time' not in earliest_tx and 'timestamp' in earliest_tx:
                    earliest_tx['time'] = earliest_tx['timestamp']
                
                # Return the transaction if it has a valid time field
                if 'time' in earliest_tx and earliest_tx['time']:
                    return earliest_tx
            
            # If no valid transaction found with the initial query,
            # try fetching more transactions to find the earliest one
            more_txs = await self.get_token_transactions(token_address, limit=10, sort_type="asc")
            
            if more_txs:
                # Find the transaction with the earliest timestamp
                earliest_time = int(time.time())  # Current time as initial value
                earliest_tx = None
                
                for tx in more_txs:
                    # Get timestamp from various possible field names
                    tx_time = tx.get('time', tx.get('blockUnixTime', tx.get('timestamp')))
                    
                    # If this tx has a valid timestamp and it's earlier than current earliest
                    if tx_time and tx_time < earliest_time:
                        earliest_time = tx_time
                        earliest_tx = tx
                
                # If we found a valid earliest transaction, ensure it has the time field
                if earliest_tx:
                    if 'time' not in earliest_tx:
                        earliest_tx['time'] = earliest_time
                    return earliest_tx
            
            self.logger.warning(f"Could not find earliest transaction for {token_address}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding earliest transaction for {token_address}: {e}")
            return None

    def _normalize_timeframe_for_endpoint(self, timeframe: str, endpoint_type: str) -> str:
        """
        Normalize timeframe format based on the specific endpoint requirements.
        The v3 endpoint requires uppercase H for hours (e.g., "1H", "4H") based on our testing.
        
        Args:
            timeframe: The requested timeframe (e.g., '1h', '4h', '1d')
            endpoint_type: The endpoint type ('v3', 'legacy', 'base_quote')
            
        Returns:
            Properly formatted timeframe for the endpoint
        """
        # Map common timeframes to what each endpoint expects
        timeframe_mappings = {
            "v3": {
                # v3 endpoint requires uppercase H for hours (confirmed working format)
                "1s": "1s", "15s": "15s", "30s": "30s",
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1H", "2h": "2H", "4h": "4H", "6h": "6H", "8h": "8H", "12h": "12H",
                "1d": "1D", "3d": "3D", "1w": "1W"
            },
            "legacy": {
                # Legacy endpoint format requirements
                "1s": "1s", "15s": "15s", "30s": "30s",
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1H", "2h": "2H", "4h": "4H", "6h": "6H", "8h": "8H", "12h": "12H",
                "1d": "1D", "3d": "3D", "1w": "1W"
            },
            "base_quote": {
                # Base quote endpoint format requirements
                "1s": "1s", "15s": "15s", "30s": "30s",
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1H", "2h": "2H", "4h": "4H", "6h": "6H", "8h": "8H", "12h": "12H",
                "1d": "1D", "3d": "3D", "1w": "1W"
            }
        }
        
        if endpoint_type not in timeframe_mappings:
            self.logger.warning(f"Unknown endpoint type: {endpoint_type}, using default format")
            return timeframe
        
        mapping = timeframe_mappings[endpoint_type]
        normalized = mapping.get(timeframe.lower(), timeframe)
        
        self.logger.debug(f"Normalized timeframe '{timeframe}' to '{normalized}' for {endpoint_type} endpoint")
        return normalized

    async def get_price_volume_multi(self, addresses: List[str], time_range: str = "24h", scan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch price and volume data for multiple tokens using batch API.
        Implements the /defi/price_volume/multi endpoint for efficient batch operations.
        
        Args:
            addresses: List of token addresses (max 50)
            time_range: Time range for volume data ('1h', '6h', '24h', '7d', '30d')
            scan_id: Optional scan identifier for tracking
            
        Returns:
            Dictionary mapping token addresses to price/volume data
        """
        if not addresses:
            return {}
            
        # Filter out excluded tokens first
        filtered_addresses = [addr for addr in addresses if not self._should_skip_token(addr)]
        if not filtered_addresses:
            self.logger.debug("All tokens in price_volume_multi batch were excluded from API calls")
            return {}
            
        # Limit to API maximum
        unique_addresses = list(dict.fromkeys(filtered_addresses))[:50]
        num_tokens = len(unique_addresses)
        
        cache_key = f"{BIRDEYE_API_NAMESPACE}_price_volume_multi_{'-'.join(unique_addresses)}_{time_range}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self._track_cache_hit(cache_key)
            self.logger.debug(f"Cache hit for price_volume_multi: {len(unique_addresses)} tokens")
            return cached_data
            
        self._track_cache_miss(cache_key)
        endpoint = "/defi/price_volume/multi"
        params = {
            "list_address": ','.join(unique_addresses),
            "time_range": time_range
        }
        
        try:
            # Use batch-aware request to track costs properly
            response_data = await self._make_request_batch_aware(endpoint, params, num_tokens)
            
            if response_data and isinstance(response_data, dict):
                if 'data' in response_data:
                    batch_data = response_data['data']
                elif 'success' in response_data and response_data['success']:
                    batch_data = response_data
                else:
                    batch_data = response_data
                    
                if isinstance(batch_data, dict):
                    self.logger.debug(f"Successfully fetched price/volume data for {len(batch_data)} tokens")
                    self.cache_manager.set(cache_key, batch_data, ttl=self.default_ttl)
                    return batch_data
                    
            self.logger.warning(f"Failed to get valid price_volume_multi data. Response: {str(response_data)[:300]}")
            self.cache_manager.set(cache_key, {}, ttl=self.error_ttl)
            return {}
            
        except Exception as e:
            self.logger.error(f"Error in get_price_volume_multi: {e}")
            self.cache_manager.set(cache_key, {}, ttl=self.error_ttl)
            return {}

    async def get_token_metadata_multiple(self, addresses: List[str], scan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for multiple tokens using batch API.
        Implements the /defi/v3/token/meta-data/multiple endpoint.
        
        Args:
            addresses: List of token addresses (max 50)
            scan_id: Optional scan identifier for tracking
            
        Returns:
            Dictionary mapping token addresses to metadata
        """
        if not addresses:
            return {}
            
        # Filter out excluded tokens first
        filtered_addresses = [addr for addr in addresses if not self._should_skip_token(addr)]
        if not filtered_addresses:
            self.logger.debug("All tokens in token_metadata_multiple batch were excluded from API calls")
            return {}
            
        # Limit to API maximum
        unique_addresses = list(dict.fromkeys(filtered_addresses))[:50]
        num_tokens = len(unique_addresses)
        
        cache_key = f"{BIRDEYE_API_NAMESPACE}_metadata_multiple_{'-'.join(unique_addresses)}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self._track_cache_hit(cache_key)
            self.logger.debug(f"Cache hit for token_metadata_multiple: {len(unique_addresses)} tokens")
            return cached_data
            
        self._track_cache_miss(cache_key)
        endpoint = "/defi/v3/token/meta-data/multiple"
        params = {
            "list_address": ','.join(unique_addresses)
        }
        
        try:
            # Use batch-aware request to track costs properly
            response_data = await self._make_request_batch_aware(endpoint, params, num_tokens)
            
            if response_data and isinstance(response_data, dict):
                if 'data' in response_data:
                    batch_data = response_data['data']
                elif 'success' in response_data and response_data['success']:
                    batch_data = response_data
                else:
                    batch_data = response_data
                    
                if isinstance(batch_data, dict):
                    self.logger.debug(f"Successfully fetched metadata for {len(batch_data)} tokens")
                    self.cache_manager.set(cache_key, batch_data, ttl=self.default_ttl)
                    return batch_data
                    
            self.logger.warning(f"Failed to get valid token_metadata_multiple data. Response: {str(response_data)[:300]}")
            self.cache_manager.set(cache_key, {}, ttl=self.error_ttl)
            return {}
            
        except Exception as e:
            self.logger.error(f"Error in get_token_metadata_multiple: {e}")
            self.cache_manager.set(cache_key, {}, ttl=self.error_ttl)
            return {}

    async def get_token_trade_data_multiple(self, addresses: List[str], time_frame: str = "24h", scan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Starter package compatible version of trade data multiple.
        Uses token overview data which includes trading metrics.
        Available in Starter package and provides trading volume, price change, etc.
        
        Args:
            addresses: List of token addresses
            time_frame: Time frame for data ('24h' recommended)
            scan_id: Optional scan identifier for tracking
            
        Returns:
            Dictionary mapping token addresses to trading overview data
        """
        if not addresses:
            return {}
            
        unique_addresses = list(dict.fromkeys(addresses))[:15]  # Starter package friendly limit
        
        trade_overview_data = {}
        
        try:
            semaphore = asyncio.Semaphore(5)  # Conservative for Starter package
            
            async def fetch_token_overview(address: str) -> Tuple[str, Optional[Dict[str, Any]]]:
                async with semaphore:
                    try:
                        # Use token overview endpoint (available in Starter)
                        endpoint = "/defi/token_overview"
                        params = {"address": address}
                        
                        response_data = await self._make_request(endpoint, params)
                        
                        if response_data and isinstance(response_data, dict):
                            if 'data' in response_data:
                                overview_data = response_data['data']
                            else:
                                overview_data = response_data
                            
                            # Extract trading-relevant data from overview
                            trading_data = {
                                'volume_24h_usd': overview_data.get('volume24h', 0) or overview_data.get('volume24hUsd', 0),
                                'price_change_24h': overview_data.get('priceChange24h', 0),
                                'price_change_24h_percent': overview_data.get('priceChange24hPercent', 0),
                                'market_cap': overview_data.get('marketCap', 0) or overview_data.get('mc', 0),
                                'liquidity': overview_data.get('liquidity', 0) or overview_data.get('liquidityUsd', 0),
                                'price': overview_data.get('price', 0),
                                'symbol': overview_data.get('symbol', ''),
                                'name': overview_data.get('name', ''),
                                # Add derived trading metrics
                                'volume_to_mcap_ratio': 0,
                                'trading_activity_score': 0
                            }
                            
                            # Calculate derived metrics
                            if trading_data['market_cap'] > 0:
                                trading_data['volume_to_mcap_ratio'] = trading_data['volume_24h_usd'] / trading_data['market_cap']
                            
                            # Trading activity score (0-100)
                            volume_score = min(100, (trading_data['volume_24h_usd'] / 10000) * 20)  # $10k = 20 points
                            price_momentum_score = abs(trading_data['price_change_24h_percent']) * 2  # 2 points per %
                            trading_data['trading_activity_score'] = min(100, volume_score + price_momentum_score)
                            
                            return address, trading_data
                        
                        return address, None
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch overview for {address}: {e}")
                        return address, None
                    
                    await asyncio.sleep(0.1)  # Rate limiting
            
            # Execute requests
            tasks = [fetch_token_overview(addr) for addr in unique_addresses]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_count = 0
            for result in results:
                if isinstance(result, Exception):
                    continue
                    
                address, data = result
                if data:
                    trade_overview_data[address] = data
                    successful_count += 1
            
            self.logger.info(f"Starter package trade data fetch: {successful_count}/{len(unique_addresses)} successful")
            return trade_overview_data
            
        except Exception as e:
            self.logger.error(f"Error in get_token_trade_data_multiple: {e}")
            return {}

    async def get_token_market_data_multiple(self, addresses: List[str], time_frame: str = "24h", scan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Starter package compatible version of market data multiple.
        Uses individual calls to /defi/v3/token/market-data endpoint.
        
        Args:
            addresses: List of token addresses (max 15 for Starter package)
            time_frame: Time frame for market data ('1h', '4h', '24h', '7d', '30d')
            scan_id: Optional scan identifier for tracking
            
        Returns:
            Dictionary mapping token addresses to market data
        """
        if not addresses:
            return {}
            
        # Limit to Starter package friendly size
        unique_addresses = list(dict.fromkeys(addresses))[:15]
        
        market_data = {}
        
        try:
            # Use semaphore to respect rate limits (Starter: 15 RPS)
            semaphore = asyncio.Semaphore(5)  # Conservative rate limiting
            
            async def fetch_single_market_data(address: str) -> Tuple[str, Optional[Dict[str, Any]]]:
                async with semaphore:
                    try:
                        # Use single token market data endpoint (available in Starter)
                        endpoint = "/defi/v3/token/market-data"
                        params = {
                            "address": address,
                            "time_frame": time_frame
                        }
                        
                        response_data = await self._make_request(endpoint, params)
                        
                        if response_data and isinstance(response_data, dict):
                            if 'data' in response_data:
                                return address, response_data['data']
                            elif 'success' in response_data and response_data['success']:
                                return address, response_data
                            else:
                                return address, response_data
                        
                        return address, None
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch market data for {address}: {e}")
                        return address, None
                    
                    # Rate limiting delay
                    await asyncio.sleep(0.1)  # 100ms between calls
            
            # Execute all requests concurrently with rate limiting
            tasks = [fetch_single_market_data(addr) for addr in unique_addresses]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_count = 0
            for result in results:
                if isinstance(result, Exception):
                    self.logger.warning(f"Market data fetch exception: {result}")
                    continue
                    
                address, data = result
                if data:
                    market_data[address] = data
                    successful_count += 1
            
            self.logger.info(f"Starter package market data fetch: {successful_count}/{len(unique_addresses)} successful")
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error in get_token_market_data_multiple: {e}")
            return {}

    async def get_pair_overview_multiple(self, pair_addresses: List[str], scan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch overview data for multiple pairs using batch API.
        Implements the /defi/v3/pair/overview/multiple endpoint.
        
        Args:
            pair_addresses: List of pair addresses (max 20)
            scan_id: Optional scan identifier for tracking
            
        Returns:
            Dictionary mapping pair addresses to overview data
        """
        if not pair_addresses:
            return {}
            
        # Limit to API maximum
        unique_addresses = list(dict.fromkeys(pair_addresses))[:20]
        num_pairs = len(unique_addresses)
        
        cache_key = f"{BIRDEYE_API_NAMESPACE}_pair_overview_multiple_{'-'.join(unique_addresses)}"
        cached_data = self.cache_manager.get(cache_key)
        if cached_data is not None:
            self._track_cache_hit(cache_key)
            self.logger.debug(f"Cache hit for pair_overview_multiple: {len(unique_addresses)} pairs")
            return cached_data
            
        self._track_cache_miss(cache_key)
        endpoint = "/defi/v3/pair/overview/multiple"
        params = {
            "list_address": ','.join(unique_addresses)
        }
        
        try:
            # Use batch-aware request to track costs properly
            response_data = await self._make_request_batch_aware(endpoint, params, num_pairs)
            
            if response_data and isinstance(response_data, dict):
                if 'data' in response_data:
                    batch_data = response_data['data']
                elif 'success' in response_data and response_data['success']:
                    batch_data = response_data
                else:
                    batch_data = response_data
                    
                if isinstance(batch_data, dict):
                    self.logger.debug(f"Successfully fetched pair overview data for {len(batch_data)} pairs")
                    self.cache_manager.set(cache_key, batch_data, ttl=self.default_ttl)
                    return batch_data
                    
            self.logger.warning(f"Failed to get valid pair_overview_multiple data. Response: {str(response_data)[:300]}")
            self.cache_manager.set(cache_key, {}, ttl=self.error_ttl)
            return {}
            
        except Exception as e:
            self.logger.error(f"Error in get_pair_overview_multiple: {e}")
            self.cache_manager.set(cache_key, {}, ttl=self.error_ttl)
            return {}

    async def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive cost summary from the cost calculator.
        
        Returns:
            Dictionary with cost statistics and session summary
        """
        if not self.cost_calculator:
            return {
                'error': 'Cost calculator not available',
                'total_compute_units': 0,
                'total_http_requests': 0
            }
            
        summary = self.cost_calculator.get_session_summary()
        
        # Add API call statistics for comprehensive view
        api_stats = self.get_api_call_statistics()
        
        return {
            **summary,
            'api_call_statistics': api_stats,
            'recommendations': self._get_cost_optimization_recommendations(summary)
        }
    
    def _get_cost_optimization_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate cost optimization recommendations based on usage patterns."""
        recommendations = []
        
        # Check batch efficiency
        if summary.get('batch_efficiency_percent', 0) < 50:
            recommendations.append("Consider using more batch API calls to improve efficiency")
            
        # Check endpoint usage patterns
        top_endpoints = summary.get('top_cost_endpoints', [])
        for endpoint_data in top_endpoints:
            endpoint = endpoint_data['endpoint']
            avg_cost = endpoint_data['avg_cus_per_call']
            
            # Suggest batch alternatives for high-cost individual calls
            if avg_cost > 50 and endpoint in ['/defi/token_overview', '/defi/token_security']:
                if endpoint == '/defi/token_overview':
                    recommendations.append("Consider using /defi/v3/token/meta-data/multiple for token overviews")
                elif endpoint == '/defi/token_security':
                    recommendations.append("Batch security checks when possible to reduce individual call costs")
                    
        # Check total usage
        total_cus = summary.get('total_compute_units', 0)
        if total_cus > 100000:  # High usage threshold
            recommendations.append("High compute unit usage detected - review caching strategy")
            
        return recommendations[:5]  # Limit to top 5 recommendations
    
    # =============================================
    # TRUE BATCH API METHODS
    # =============================================
    
    async def get_multi_token_price(self, token_addresses: List[str]) -> Optional[Dict[str, Any]]:
        """
        Fetch multiple token prices using batch endpoint (if available)
        
        Args:
            token_addresses: List of token addresses
            
        Returns:
            Dictionary mapping token address to price data or None if not available
        """
        try:
            # Validate addresses first
            valid_addresses, filtered = self._filter_solana_addresses(token_addresses)
            if not valid_addresses:
                return {}
            
            # Try the multi-price endpoint (available in higher-tier plans)
            addresses_param = ",".join(valid_addresses[:50])  # Limit to 50 addresses
            endpoint = "/defi/multi_price"
            params = {"list_address": addresses_param, "include_liquidity": "false"}
            
            response = await self._make_request(endpoint, params)
            
            if response and "data" in response:
                # Convert list response to dictionary
                result = {}
                for price_data in response["data"]:
                    if "address" in price_data:
                        result[price_data["address"]] = price_data
                return result
            
            return None
            
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                # Endpoint not available in current plan
                self.logger.debug("Multi-price endpoint not available in current API plan")
                return None
            else:
                self.logger.error(f"Error in batch price fetch: {e}")
                return None
    
    async def get_batch_token_metadata(self, token_addresses: List[str]) -> Optional[Dict[str, Any]]:
        """
        Fetch multiple token metadata using batch endpoint (if available)
        
        Args:
            token_addresses: List of token addresses
            
        Returns:
            Dictionary mapping token address to metadata or None if not available
        """
        try:
            # Validate addresses first
            valid_addresses, filtered = self._filter_solana_addresses(token_addresses)
            if not valid_addresses:
                return {}
            
            # Try batch metadata endpoint (may not be available in Starter Plan)
            endpoint = "/defi/v3/token/meta-data/multiple"
            addresses_param = ",".join(valid_addresses[:50])  # Limit batch size
            params = {"list_address": addresses_param}
            
            response = await self._make_request(endpoint, params)
            
            if response and "data" in response:
                # Convert to address-keyed dictionary
                result = {}
                data = response["data"]
                if isinstance(data, list):
                    for metadata in data:
                        if "address" in metadata:
                            result[metadata["address"]] = metadata
                elif isinstance(data, dict):
                    # Some APIs return direct address-keyed data
                    result = data
                return result
            
            return None
            
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                self.logger.debug("Batch metadata endpoint not available in current API plan")
                return None
            else:
                self.logger.error(f"Error in batch metadata fetch: {e}")
                return None

