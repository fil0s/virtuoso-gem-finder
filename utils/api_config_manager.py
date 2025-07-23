#!/usr/bin/env python3
"""
API Configuration Manager
Centralizes API endpoint configuration and provides environment-aware URL management
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class APIConfigManager:
    """
    Centralized API configuration manager that provides:
    - Environment-aware endpoint URLs
    - Timeout and retry configurations
    - Easy switching between mainnet/testnet/development
    - Fallback mechanisms for missing configurations
    """
    
    def __init__(self, environment: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize API configuration manager
        
        Args:
            environment: Target environment (production, testnet, development)
            config_path: Path to configuration file (defaults to config/api_endpoints.yaml)
        """
        self.logger = logging.getLogger('APIConfigManager')
        
        # Determine config file path
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to config/api_endpoints.yaml relative to project root
            project_root = Path(__file__).parent.parent
            self.config_path = project_root / "config" / "api_endpoints.yaml"
            
        # Load configuration
        self.config = self._load_config()
        
        # Determine environment
        self.environment = (
            environment or 
            os.getenv('API_ENVIRONMENT', 'production') or
            self.config.get('default_environment', 'production')
        )
        
        # Get environment-specific config
        self.env_config = self.config.get('environments', {}).get(self.environment, {})
        
        self.logger.info(f"🔧 API Config Manager initialized")
        self.logger.info(f"   📍 Environment: {self.environment}")
        self.logger.info(f"   📁 Config file: {self.config_path}")
        self.logger.info(f"   ✅ Loaded {len(self.env_config)} service configurations")
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                self.logger.warning(f"⚠️ Config file not found: {self.config_path}")
                return self._get_fallback_config()
                
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            self.logger.info(f"✅ Loaded API configuration from {self.config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load API config: {e}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Provide fallback configuration if config file is missing"""
        return {
            'default_environment': 'production',
            'environments': {
                'production': {
                    'birdeye': {'base_url': 'https://public-api.birdeye.so'},
                    'moralis': {'base_url': 'https://deep-index.moralis.io/api/v2.2'},
                    'dexscreener': {'base_url': 'https://api.dexscreener.com'},
                    'pump_fun': {'base_url': 'https://frontend-api.pump.fun'},
                    'solana': {'rpc': 'https://api.mainnet-beta.solana.com'}
                }
            }
        }
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Get complete configuration for a service
        
        Args:
            service_name: Name of the service (e.g., 'birdeye', 'dexscreener')
            
        Returns:
            Dictionary containing service configuration
        """
        service_config = self.env_config.get(service_name, {})
        
        if not service_config:
            self.logger.warning(f"⚠️ No configuration found for service: {service_name}")
            
        return service_config
    
    def get_base_url(self, service_name: str) -> str:
        """
        Get base URL for a service
        
        Args:
            service_name: Name of the service
            
        Returns:
            Base URL string
        """
        service_config = self.get_service_config(service_name)
        base_url = service_config.get('base_url', '')
        
        if not base_url:
            self.logger.warning(f"⚠️ No base_url found for service: {service_name}")
            
        return base_url
    
    def get_endpoint_url(self, service_name: str, endpoint_name: str) -> str:
        """
        Get complete URL for a specific endpoint
        
        Args:
            service_name: Name of the service
            endpoint_name: Name of the endpoint
            
        Returns:
            Complete URL string
        """
        service_config = self.get_service_config(service_name)
        base_url = service_config.get('base_url', '')
        endpoints = service_config.get('endpoints', {})
        endpoint_path = endpoints.get(endpoint_name, '')
        
        if not base_url:
            self.logger.warning(f"⚠️ No base_url for {service_name}")
            return ''
            
        if not endpoint_path:
            self.logger.warning(f"⚠️ No endpoint '{endpoint_name}' for {service_name}")
            return base_url
            
        # Ensure proper URL joining
        if not base_url.endswith('/') and not endpoint_path.startswith('/'):
            return f"{base_url}/{endpoint_path}"
        elif base_url.endswith('/') and endpoint_path.startswith('/'):
            return f"{base_url[:-1]}{endpoint_path}"
        else:
            return f"{base_url}{endpoint_path}"
    
    def get_timeout(self, service_name: str, operation: str = 'default') -> int:
        """
        Get timeout configuration for a service
        
        Args:
            service_name: Name of the service
            operation: Type of operation (default, fast, slow)
            
        Returns:
            Timeout in seconds
        """
        # Service-specific timeout
        service_config = self.get_service_config(service_name)
        service_timeout = service_config.get('timeout')
        
        if service_timeout:
            return service_timeout
            
        # Global timeout fallback
        global_timeouts = self.config.get('global_timeouts', {})
        return global_timeouts.get(operation, 30)
    
    def get_reference_url(self, url_type: str, **kwargs) -> str:
        """
        Get reference URL with parameter substitution
        
        Args:
            url_type: Type of reference URL (e.g., 'birdeye_token')
            **kwargs: Parameters for URL formatting (e.g., address='ABC123')
            
        Returns:
            Formatted reference URL
        """
        reference_urls = self.env_config.get('reference_urls', {})
        url_template = reference_urls.get(url_type, '')
        
        if not url_template:
            self.logger.warning(f"⚠️ No reference URL found for: {url_type}")
            return ''
            
        try:
            return url_template.format(**kwargs)
        except KeyError as e:
            self.logger.error(f"❌ Missing parameter {e} for URL template: {url_template}")
            return url_template
    
    def get_rate_limit(self, service_name: str, api_type: str = 'free_apis') -> Dict[str, int]:
        """
        Get rate limiting configuration
        
        Args:
            service_name: Name of the service
            api_type: Type of API (free_apis, paid_apis)
            
        Returns:
            Dictionary with rate limit settings
        """
        # Service-specific rate limit
        service_config = self.get_service_config(service_name)
        service_rate_limit = service_config.get('rate_limit')
        
        if service_rate_limit:
            return {'rpm': service_rate_limit, 'burst_size': 10}
            
        # Global rate limit fallback
        rate_limits = self.config.get('rate_limits', {})
        api_config = rate_limits.get(api_type, {})
        
        return {
            'rpm': api_config.get('default_rpm', 60),
            'burst_size': api_config.get('burst_size', 10)
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate current configuration and return status report
        
        Returns:
            Dictionary with validation results
        """
        validation_report = {
            'environment': self.environment,
            'config_file_exists': self.config_path.exists(),
            'services_configured': len(self.env_config),
            'missing_services': [],
            'invalid_urls': [],
            'warnings': []
        }
        
        # Check for common services
        expected_services = [
            'birdeye', 'moralis', 'dexscreener', 'pump_fun', 
            'jupiter', 'raydium', 'orca', 'solana'
        ]
        
        for service in expected_services:
            if service not in self.env_config:
                validation_report['missing_services'].append(service)
            else:
                # Validate base URL
                base_url = self.get_base_url(service)
                if not base_url or not base_url.startswith(('http://', 'https://')):
                    validation_report['invalid_urls'].append(f"{service}: {base_url}")
        
        # Add warnings
        if validation_report['missing_services']:
            validation_report['warnings'].append(
                f"Missing configurations for: {', '.join(validation_report['missing_services'])}"
            )
            
        if validation_report['invalid_urls']:
            validation_report['warnings'].append(
                f"Invalid URLs found: {', '.join(validation_report['invalid_urls'])}"
            )
            
        return validation_report
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        self.logger.info("🔄 Reloading API configuration...")
        self.config = self._load_config()
        self.env_config = self.config.get('environments', {}).get(self.environment, {})
        self.logger.info("✅ Configuration reloaded successfully")


# Global singleton instance
_config_manager = None

def get_api_config(environment: Optional[str] = None) -> APIConfigManager:
    """
    Get global API configuration manager instance
    
    Args:
        environment: Override environment (optional)
        
    Returns:
        APIConfigManager instance
    """
    global _config_manager
    
    if _config_manager is None or environment:
        _config_manager = APIConfigManager(environment=environment)
        
    return _config_manager


# Convenience functions for common operations
def get_service_url(service_name: str, endpoint_name: str = None) -> str:
    """Get service URL (base URL or specific endpoint)"""
    config = get_api_config()
    
    if endpoint_name:
        return config.get_endpoint_url(service_name, endpoint_name)
    else:
        return config.get_base_url(service_name)


def get_service_timeout(service_name: str) -> int:
    """Get service timeout"""
    config = get_api_config()
    return config.get_timeout(service_name)


def get_trading_url(platform: str, token_address: str) -> str:
    """Get trading URL for a token on specific platform"""
    config = get_api_config()
    url_type = f"{platform}_token"
    return config.get_reference_url(url_type, address=token_address)


# Example usage and testing
if __name__ == "__main__":
    # Demo usage
    print("🔧 API Configuration Manager Demo")
    print("=" * 50)
    
    # Initialize manager
    config = get_api_config()
    
    # Test various endpoints
    services_to_test = ['birdeye', 'dexscreener', 'pump_fun', 'solana']
    
    for service in services_to_test:
        base_url = config.get_base_url(service)
        timeout = config.get_timeout(service)
        print(f"📍 {service.upper()}:")
        print(f"   Base URL: {base_url}")
        print(f"   Timeout: {timeout}s")
        
    # Test specific endpoints
    print(f"\n🔗 DexScreener search: {config.get_endpoint_url('dexscreener', 'search')}")
    print(f"🔗 Pump.fun latest: {config.get_endpoint_url('pump_fun', 'latest')}")
    
    # Test reference URLs
    test_address = "So11111111111111111111111111111111111111112"
    print(f"\n🌐 Reference URLs for {test_address[:12]}...:")
    print(f"   Birdeye: {config.get_reference_url('birdeye_token', address=test_address)}")
    print(f"   DexScreener: {config.get_reference_url('dexscreener_token', address=test_address)}")
    
    # Validation report
    print(f"\n✅ Configuration Validation:")
    report = config.validate_configuration()
    print(f"   Environment: {report['environment']}")
    print(f"   Services configured: {report['services_configured']}")
    if report['warnings']:
        for warning in report['warnings']:
            print(f"   ⚠️ {warning}")
    else:
        print("   🎉 No warnings found!")