#!/usr/bin/env python3
"""
HTTP Client Manager
Provides standardized HTTP client interface across all services
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, Union
from contextlib import asynccontextmanager
import json
from utils.api_config_manager import get_api_config


class StandardHTTPClient:
    """
    Standardized HTTP client that wraps aiohttp with consistent interface
    
    Features:
    - Automatic timeout configuration per service
    - Consistent error handling
    - Request/response logging
    - Rate limiting integration ready
    - Retry mechanism with exponential backoff
    """
    
    def __init__(self, service_name: str, session: Optional[aiohttp.ClientSession] = None):
        """
        Initialize HTTP client for a specific service
        
        Args:
            service_name: Name of the service (for config lookup)
            session: Optional existing aiohttp session to reuse
        """
        self.service_name = service_name
        self.logger = logging.getLogger(f'HTTPClient-{service_name}')
        self._session = session
        self._owned_session = session is None
        
        # Get service configuration
        self.config = get_api_config()
        self.service_config = self.config.get_service_config(service_name)
        
        # Configure timeouts
        self.default_timeout = self.config.get_timeout(service_name)
        
        # Configure retry settings
        self.max_retries = self.service_config.get('max_retries', 3)
        self.backoff_factor = self.service_config.get('backoff_factor', 1.5)
        
        self.logger.debug(f"📡 HTTP Client initialized for {service_name}")
        self.logger.debug(f"   ⏱️ Default timeout: {self.default_timeout}s")
        self.logger.debug(f"   🔄 Max retries: {self.max_retries}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None:
            # Create new session with optimized settings
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Max connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=self.default_timeout)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                json_serialize=json.dumps
            )
            
            self.logger.debug(f"✅ Created new HTTP session for {self.service_name}")
        
        return self._session
    
    async def get(self, 
                  url: str,
                  params: Optional[Dict] = None,
                  headers: Optional[Dict] = None,
                  timeout: Optional[float] = None,
                  **kwargs) -> Dict[str, Any]:
        """
        Perform GET request with standardized handling
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Request headers
            timeout: Override default timeout
            **kwargs: Additional aiohttp parameters
            
        Returns:
            JSON response as dictionary
        """
        return await self._request('GET', url, params=params, headers=headers, 
                                 timeout=timeout, **kwargs)
    
    async def post(self,
                   url: str,
                   data: Optional[Union[Dict, str]] = None,
                   json: Optional[Dict] = None,
                   headers: Optional[Dict] = None,
                   timeout: Optional[float] = None,
                   **kwargs) -> Dict[str, Any]:
        """
        Perform POST request with standardized handling
        
        Args:
            url: Request URL
            data: Form data or raw data
            json: JSON data
            headers: Request headers
            timeout: Override default timeout
            **kwargs: Additional aiohttp parameters
            
        Returns:
            JSON response as dictionary
        """
        return await self._request('POST', url, data=data, json=json, 
                                 headers=headers, timeout=timeout, **kwargs)
    
    async def _request(self,
                      method: str,
                      url: str,
                      timeout: Optional[float] = None,
                      **kwargs) -> Dict[str, Any]:
        """
        Internal request method with retry logic and error handling
        
        Args:
            method: HTTP method
            url: Request URL
            timeout: Override default timeout
            **kwargs: Additional aiohttp parameters
            
        Returns:
            JSON response as dictionary
        """
        session = await self._get_session()
        
        # Use provided timeout or service default
        request_timeout = timeout or self.default_timeout
        
        # Prepare request
        if timeout:
            kwargs['timeout'] = aiohttp.ClientTimeout(total=request_timeout)
        
        # Retry logic
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"🔄 {method} {url} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                async with session.request(method, url, **kwargs) as response:
                    # Log response status
                    if response.status == 200:
                        self.logger.debug(f"✅ {method} {url} -> {response.status}")
                    else:
                        self.logger.warning(f"⚠️ {method} {url} -> {response.status}")
                    
                    # Handle different response types
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        
                        if 'application/json' in content_type:
                            return await response.json()
                        else:
                            # Try to parse as JSON anyway, fallback to text
                            try:
                                return await response.json()
                            except json.JSONDecodeError:
                                text = await response.text()
                                return {'text': text, 'status': response.status}
                    
                    elif response.status == 404:
                        return {'error': 'Not Found', 'status': 404}
                    
                    elif response.status == 429:
                        # Rate limited - implement backoff
                        if attempt < self.max_retries:
                            backoff_time = self.backoff_factor ** attempt
                            self.logger.warning(f"⏰ Rate limited, backing off {backoff_time:.1f}s")
                            await asyncio.sleep(backoff_time)
                            continue
                        else:
                            return {'error': 'Rate Limited', 'status': 429}
                    
                    elif response.status >= 500:
                        # Server error - retry with backoff
                        if attempt < self.max_retries:
                            backoff_time = self.backoff_factor ** attempt
                            self.logger.warning(f"🔄 Server error {response.status}, retrying in {backoff_time:.1f}s")
                            await asyncio.sleep(backoff_time)
                            continue
                        else:
                            return {'error': f'Server Error {response.status}', 'status': response.status}
                    
                    else:
                        # Other client errors - don't retry
                        return {'error': f'HTTP {response.status}', 'status': response.status}
            
            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < self.max_retries:
                    backoff_time = self.backoff_factor ** attempt
                    self.logger.warning(f"⏰ Timeout, retrying in {backoff_time:.1f}s")
                    await asyncio.sleep(backoff_time)
                    continue
                else:
                    self.logger.error(f"❌ Final timeout for {method} {url}")
                    return {'error': 'Timeout', 'timeout': request_timeout}
            
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    backoff_time = self.backoff_factor ** attempt
                    self.logger.warning(f"❌ Request error: {e}, retrying in {backoff_time:.1f}s")
                    await asyncio.sleep(backoff_time)
                    continue
                else:
                    self.logger.error(f"❌ Final error for {method} {url}: {e}")
                    return {'error': str(e), 'exception_type': type(e).__name__}
        
        # Should not reach here, but handle gracefully
        return {'error': f'Max retries exceeded: {last_exception}'}
    
    async def close(self):
        """Close HTTP session if owned by this client"""
        if self._owned_session and self._session:
            await self._session.close()
            self._session = None
            self.logger.debug(f"🔒 Closed HTTP session for {self.service_name}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


class HTTPClientFactory:
    """
    Factory for creating standardized HTTP clients for different services
    """
    
    _clients: Dict[str, StandardHTTPClient] = {}
    _shared_session: Optional[aiohttp.ClientSession] = None
    
    @classmethod
    async def get_client(cls, service_name: str, shared_session: bool = True) -> StandardHTTPClient:
        """
        Get or create HTTP client for a service
        
        Args:
            service_name: Name of the service
            shared_session: Whether to use shared session across clients
            
        Returns:
            StandardHTTPClient instance
        """
        if service_name not in cls._clients:
            session = None
            
            if shared_session:
                if cls._shared_session is None:
                    cls._shared_session = await cls._create_shared_session()
                session = cls._shared_session
            
            cls._clients[service_name] = StandardHTTPClient(service_name, session)
        
        return cls._clients[service_name]
    
    @classmethod
    async def _create_shared_session(cls) -> aiohttp.ClientSession:
        """Create optimized shared session"""
        connector = aiohttp.TCPConnector(
            limit=200,  # Higher limit for shared session
            limit_per_host=50,
            ttl_dns_cache=600,  # Longer DNS cache
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        
        return aiohttp.ClientSession(
            connector=connector,
            json_serialize=json.dumps
        )
    
    @classmethod
    async def close_all(cls):
        """Close all clients and shared session"""
        # Close individual clients
        for client in cls._clients.values():
            await client.close()
        cls._clients.clear()
        
        # Close shared session
        if cls._shared_session:
            await cls._shared_session.close()
            cls._shared_session = None


# Convenience functions for common usage patterns
async def get_json(service_name: str, url: str, **kwargs) -> Dict[str, Any]:
    """
    Simple GET request for JSON data
    
    Args:
        service_name: Service name for configuration lookup
        url: Request URL
        **kwargs: Additional request parameters
        
    Returns:
        JSON response
    """
    async with StandardHTTPClient(service_name) as client:
        return await client.get(url, **kwargs)


async def post_json(service_name: str, url: str, **kwargs) -> Dict[str, Any]:
    """
    Simple POST request for JSON data
    
    Args:
        service_name: Service name for configuration lookup
        url: Request URL
        **kwargs: Additional request parameters
        
    Returns:
        JSON response
    """
    async with StandardHTTPClient(service_name) as client:
        return await client.post(url, **kwargs)


@asynccontextmanager
async def http_client_pool():
    """
    Context manager for managing a pool of HTTP clients
    
    Usage:
        async with http_client_pool() as pool:
            dex_client = await pool.get_client('dexscreener')
            pump_client = await pool.get_client('pump_fun')
            # ... use clients
    """
    try:
        yield HTTPClientFactory
    finally:
        await HTTPClientFactory.close_all()


# Example usage and testing
if __name__ == "__main__":
    async def demo():
        print("🌐 HTTP Client Manager Demo")
        print("=" * 40)
        
        # Test individual client
        print("\n📡 Testing individual client:")
        async with StandardHTTPClient('dexscreener') as client:
            # Test with a real endpoint
            config = get_api_config()
            base_url = config.get_base_url('dexscreener')
            
            if base_url:
                # Test search endpoint
                search_url = f"{base_url}/latest/dex/search"
                params = {'q': 'solana'}
                
                result = await client.get(search_url, params=params)
                print(f"   Status: {'success' if 'pairs' in result else 'error'}")
                print(f"   Response keys: {list(result.keys())}")
        
        # Test client factory
        print("\n🏭 Testing client factory:")
        async with http_client_pool() as pool:
            dex_client = await pool.get_client('dexscreener')
            pump_client = await pool.get_client('pump_fun')
            
            print(f"   DexScreener client: {type(dex_client).__name__}")
            print(f"   Pump.fun client: {type(pump_client).__name__}")
        
        # Test convenience functions
        print("\n⚡ Testing convenience functions:")
        try:
            config = get_api_config()
            base_url = config.get_base_url('dexscreener')
            
            if base_url:
                result = await get_json('dexscreener', f"{base_url}/latest/dex/search", 
                                      params={'q': 'sol'})
                print(f"   Convenience function result: {'success' if isinstance(result, dict) else 'error'}")
        except Exception as e:
            print(f"   Convenience function error: {e}")
        
        print("\n✅ HTTP Client Manager demo complete!")
    
    asyncio.run(demo())