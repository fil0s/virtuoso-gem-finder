#!/usr/bin/env python3
"""
Example migration showing how to replace hardcoded URLs with centralized configuration

This demonstrates the before/after of migrating from hardcoded URLs to the 
centralized API configuration system.
"""

import aiohttp
import asyncio
from utils.api_config_manager import get_api_config, get_service_url, get_service_timeout


# =============================================================================
# BEFORE: Hardcoded URLs (Example of what we're replacing)
# =============================================================================

class OldStyleAPIClient:
    """Example of old style with hardcoded URLs"""
    
    def __init__(self):
        # ❌ PROBLEM: Hardcoded URLs scattered throughout code
        self.dexscreener_base = "https://api.dexscreener.com"
        self.pump_fun_base = "https://frontend-api.pump.fun"
        self.jupiter_tokens = "https://token.jup.ag/all"
        self.jupiter_price = "https://lite-api.jup.ag/price/v2"
        self.raydium_pools = "https://api.raydium.io/v2/main/pairs"
        
        # ❌ PROBLEM: Hardcoded timeouts
        self.timeout = 30
        
    async def get_dexscreener_data(self, token_address: str):
        """Example method with hardcoded URL"""
        # ❌ PROBLEM: URL construction scattered everywhere
        url = f"{self.dexscreener_base}/latest/dex/tokens/{token_address}"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.get(url) as response:
                return await response.json()


# =============================================================================
# AFTER: Centralized Configuration (Improved approach)
# =============================================================================

class NewStyleAPIClient:
    """Example of new style with centralized configuration"""
    
    def __init__(self, environment: str = None):
        # ✅ SOLUTION: Get configuration manager
        self.config = get_api_config(environment)
        
        # ✅ SOLUTION: All URLs come from centralized config
        self.logger = self.config.logger
        
    async def get_dexscreener_data(self, token_address: str):
        """Example method using centralized configuration"""
        # ✅ SOLUTION: Get URL from config
        base_url = self.config.get_base_url('dexscreener')
        url = f"{base_url}/latest/dex/tokens/{token_address}"
        
        # ✅ SOLUTION: Get timeout from config
        timeout = self.config.get_timeout('dexscreener')
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url) as response:
                return await response.json()
    
    async def get_pump_fun_latest(self, limit: int = 20):
        """Example using endpoint-specific configuration"""
        # ✅ SOLUTION: Get complete endpoint URL
        url = self.config.get_endpoint_url('pump_fun', 'latest')
        params = {'limit': limit}
        
        # ✅ SOLUTION: Service-specific timeout
        timeout = self.config.get_timeout('pump_fun')
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, params=params) as response:
                return await response.json()
    
    def get_trading_links(self, token_address: str) -> dict:
        """Example using reference URLs"""
        return {
            'birdeye': self.config.get_reference_url('birdeye_token', address=token_address),
            'dexscreener': self.config.get_reference_url('dexscreener_token', address=token_address),
            'raydium': self.config.get_reference_url('raydium_swap', address=token_address),
            'solscan': self.config.get_reference_url('solscan_token', address=token_address)
        }


# =============================================================================
# CONVENIENCE FUNCTIONS: Even simpler usage
# =============================================================================

class SuperSimpleAPIClient:
    """Example using convenience functions for maximum simplicity"""
    
    async def get_token_data(self, token_address: str):
        """Ultra-simple example using convenience functions"""
        # ✅ SOLUTION: One-liner to get service URL
        url = get_service_url('dexscreener', 'tokens')
        full_url = f"{url.rstrip('/')}/{token_address}"
        
        # ✅ SOLUTION: One-liner to get timeout
        timeout = get_service_timeout('dexscreener')
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(full_url) as response:
                return await response.json()


# =============================================================================
# MIGRATION STRATEGIES
# =============================================================================

def migration_strategy_1_gradual():
    """
    Strategy 1: Gradual Migration
    
    Migrate service by service, maintaining backward compatibility
    """
    print("🔄 Strategy 1: Gradual Migration")
    print("1. Add config manager to existing class __init__")
    print("2. Replace hardcoded URLs one method at a time")
    print("3. Keep old constants as fallbacks initially")
    print("4. Remove old constants once all methods migrated")
    
    # Example gradual migration
    class PartiallyMigratedService:
        def __init__(self):
            # New: Add config manager
            self.config = get_api_config()
            
            # Old: Keep existing hardcoded values as fallbacks
            self.old_base_url = "https://api.example.com"
            
        def new_method(self, token_address: str):
            """New method using config"""
            url = self.config.get_base_url('example_service')
            return f"{url}/tokens/{token_address}"
            
        def old_method(self, token_address: str):
            """Old method still using hardcoded URL"""
            return f"{self.old_base_url}/tokens/{token_address}"


def migration_strategy_2_factory_pattern():
    """
    Strategy 2: Factory Pattern
    
    Create factory that provides pre-configured clients
    """
    print("🏭 Strategy 2: Factory Pattern")
    
    class APIClientFactory:
        @staticmethod
        def create_dexscreener_client():
            config = get_api_config()
            base_url = config.get_base_url('dexscreener')
            timeout = config.get_timeout('dexscreener')
            return {'base_url': base_url, 'timeout': timeout}
        
        @staticmethod  
        def create_pump_fun_client():
            config = get_api_config()
            return {
                'base_url': config.get_base_url('pump_fun'),
                'endpoints': config.get_service_config('pump_fun').get('endpoints', {}),
                'timeout': config.get_timeout('pump_fun')
            }


def migration_strategy_3_dependency_injection():
    """
    Strategy 3: Dependency Injection
    
    Inject configuration into existing services
    """
    print("💉 Strategy 3: Dependency Injection")
    
    class ExistingService:
        def __init__(self, base_url: str, timeout: int = 30):
            self.base_url = base_url
            self.timeout = timeout
            
        def fetch_data(self, endpoint: str):
            return f"{self.base_url}/{endpoint}"
    
    # Inject configured values
    config = get_api_config()
    service = ExistingService(
        base_url=config.get_base_url('dexscreener'),
        timeout=config.get_timeout('dexscreener')
    )


# =============================================================================
# ENVIRONMENT SWITCHING EXAMPLES
# =============================================================================

async def environment_switching_demo():
    """Demonstrate environment switching capabilities"""
    print("🌍 Environment Switching Demo")
    
    # Production environment
    prod_config = get_api_config('production')
    prod_url = prod_config.get_base_url('solana')
    print(f"Production Solana RPC: {prod_url}")
    
    # Development environment  
    dev_config = get_api_config('development')
    dev_url = dev_config.get_base_url('solana')
    print(f"Development Solana RPC: {dev_url}")
    
    # Testnet environment
    test_config = get_api_config('testnet')
    test_url = test_config.get_base_url('solana')
    print(f"Testnet Solana RPC: {test_url}")


# =============================================================================
# TESTING AND VALIDATION
# =============================================================================

async def validate_migration():
    """Validate that migration was successful"""
    print("✅ Validating Migration")
    
    config = get_api_config()
    
    # Test configuration loading
    validation_report = config.validate_configuration()
    print(f"Environment: {validation_report['environment']}")
    print(f"Services configured: {validation_report['services_configured']}")
    
    if validation_report['warnings']:
        print("⚠️ Warnings found:")
        for warning in validation_report['warnings']:
            print(f"  - {warning}")
    else:
        print("🎉 No configuration warnings!")
    
    # Test URL generation
    services_to_test = ['dexscreener', 'pump_fun', 'birdeye', 'moralis']
    print(f"\n🔗 Testing URL generation:")
    
    for service in services_to_test:
        try:
            base_url = config.get_base_url(service)
            timeout = config.get_timeout(service)
            print(f"  ✅ {service}: {base_url} (timeout: {timeout}s)")
        except Exception as e:
            print(f"  ❌ {service}: Error - {e}")


# =============================================================================
# MAIN DEMO
# =============================================================================

async def main():
    """Run complete migration demonstration"""
    print("🚀 API Configuration Migration Demo")
    print("=" * 60)
    
    # Show old vs new approach
    print("\n📊 Comparing Old vs New Approach:")
    
    old_client = OldStyleAPIClient()
    new_client = NewStyleAPIClient()
    
    # Demonstrate URL differences
    test_token = "So11111111111111111111111111111111111111112"
    
    print(f"\n🔍 Token: {test_token[:12]}...")
    print(f"Old style hardcoded: {old_client.dexscreener_base}/latest/dex/tokens/{test_token}")
    
    config = get_api_config()
    new_url = f"{config.get_base_url('dexscreener')}/latest/dex/tokens/{test_token}"
    print(f"New style configured: {new_url}")
    
    # Show trading links
    print(f"\n🌐 Trading Links:")
    trading_links = new_client.get_trading_links(test_token)
    for platform, url in trading_links.items():
        print(f"  {platform.capitalize()}: {url}")
    
    # Migration strategies
    print(f"\n🔄 Migration Strategies:")
    migration_strategy_1_gradual()
    migration_strategy_2_factory_pattern()
    migration_strategy_3_dependency_injection()
    
    # Environment switching
    print(f"\n🌍 Environment Examples:")
    await environment_switching_demo()
    
    # Validation
    print(f"\n✅ Configuration Validation:")
    await validate_migration()
    
    print(f"\n🎯 Migration Benefits:")
    print("  ✅ Centralized URL management")
    print("  ✅ Environment-aware configuration")
    print("  ✅ Easy maintenance and updates")
    print("  ✅ Consistent timeout handling")
    print("  ✅ Better testing with mock environments")
    print("  ✅ No more scattered hardcoded URLs")


if __name__ == "__main__":
    asyncio.run(main())