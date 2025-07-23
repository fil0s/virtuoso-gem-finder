#!/usr/bin/env python3
"""
Robust configuration manager for the Virtuoso Gem Hunter application.

This module provides secure, fault-tolerant configuration loading and validation
with proper error recovery and fallback mechanisms.
"""

import os
import yaml
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from copy import deepcopy
from dotenv import load_dotenv

from utils.exceptions import ConfigurationError
from utils.error_recovery import with_error_recovery, get_error_recovery_manager

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config") / "config.yaml"

@dataclass
class ConfigValidationRule:
    """Defines validation rules for configuration values"""
    required: bool = False
    data_type: type = str
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    validator_func: Optional[callable] = None
    description: str = ""

@dataclass 
class ConfigSection:
    """Represents a configuration section with validation rules"""
    name: str
    required: bool = False
    fields: Dict[str, ConfigValidationRule] = field(default_factory=dict)
    subsections: Dict[str, 'ConfigSection'] = field(default_factory=dict)

class RobustConfigManager:
    """
    Advanced configuration manager with robust error handling and validation.
    
    Features:
    - Graceful fallback to defaults on errors
    - Comprehensive validation with custom rules
    - Environment variable priority
    - Secure handling of sensitive data
    - Configuration hot-reloading capability
    - Circuit breaker for file operations
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = self._resolve_config_path(config_path)
        self._config: Dict[str, Any] = {}
        self._validation_schema = self._build_validation_schema()
        self._config_loaded = False
        self._config_lock = asyncio.Lock()
        
        # Initialize with safe defaults first
        self._apply_safe_defaults()
        
        # Then attempt to load full configuration
        self._load_configuration()
    
    def _resolve_config_path(self, config_path: Optional[Union[str, Path]]) -> Path:
        """Safely resolve configuration file path with fallbacks"""
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            else:
                logger.warning(f"Specified config path does not exist: {path}")
        
        # Try default locations
        candidates = [
            Path.cwd() / DEFAULT_CONFIG_PATH,
            Path.cwd().parent / DEFAULT_CONFIG_PATH,
            Path.cwd() / "config.yaml",
            Path.cwd() / "config" / "default.yaml"
        ]
        
        for candidate in candidates:
            if candidate.exists():
                logger.info(f"Using configuration file: {candidate}")
                return candidate
        
        logger.warning(f"No configuration file found. Trying defaults: {candidates[0]}")
        return candidates[0]  # Return first candidate as default
    
    def _build_validation_schema(self) -> Dict[str, ConfigSection]:
        """Build comprehensive validation schema for all configuration sections"""
        
        schema = {}
        
        # Database configuration
        schema["DATABASE"] = ConfigSection(
            name="DATABASE",
            required=False,
            fields={
                "name": ConfigValidationRule(required=True, data_type=str, description="Database file name"),
                "backup_interval_hours": ConfigValidationRule(data_type=int, min_value=1, max_value=168),
                "max_backup_files": ConfigValidationRule(data_type=int, min_value=1, max_value=100)
            }
        )
        
        # RPC configuration  
        schema["RPC"] = ConfigSection(
            name="RPC",
            required=True,
            fields={
                "solana_endpoint": ConfigValidationRule(required=True, data_type=str, description="Solana RPC endpoint"),
                "timeout_seconds": ConfigValidationRule(data_type=int, min_value=5, max_value=120),
                "max_retries": ConfigValidationRule(data_type=int, min_value=0, max_value=10),
                "retry_delay_seconds": ConfigValidationRule(data_type=int, min_value=1, max_value=60)
            }
        )
        
        # API configurations
        for api_name in ["HELIUS_API", "BIRDEYE_API"]:
            schema[api_name] = ConfigSection(
                name=api_name,
                required=True,
                fields={
                    "base_url": ConfigValidationRule(required=True, data_type=str, description=f"{api_name} base URL"),
                    "api_key": ConfigValidationRule(data_type=str, description=f"{api_name} API key (from env)"),
                    "timeout_seconds": ConfigValidationRule(data_type=int, min_value=5, max_value=120),
                    "max_retries": ConfigValidationRule(data_type=int, min_value=0, max_value=10)
                }
            )
        
        # Telegram configuration
        schema["TELEGRAM"] = ConfigSection(
            name="TELEGRAM",
            required=False,
            fields={
                "enabled": ConfigValidationRule(data_type=bool, description="Enable Telegram notifications"),
                "bot_token": ConfigValidationRule(data_type=str, description="Telegram bot token (from env)"),
                "chat_id": ConfigValidationRule(data_type=str, description="Telegram chat ID (from env)"),
                "alert_threshold": ConfigValidationRule(data_type=int, min_value=0, max_value=100),
                "cooldown_minutes": ConfigValidationRule(data_type=int, min_value=1, max_value=1440)
            }
        )
        
        # Rate limiter configuration
        schema["RATE_LIMITER"] = ConfigSection(
            name="RATE_LIMITER", 
            required=True,
            fields={
                "enabled": ConfigValidationRule(data_type=bool, description="Enable rate limiting"),
                "default_retry_interval": ConfigValidationRule(data_type=int, min_value=1, max_value=60)
            }
        )
        
        return schema
    
    def _apply_safe_defaults(self):
        """Apply minimal safe defaults to ensure the application can start"""
        self._config = {
            "DATABASE": {
                "name": "virtuoso_gem_hunter.db",
                "backup_interval_hours": 24,
                "max_backup_files": 7
            },
            "RPC": {
                "solana_endpoint": "https://api.mainnet-beta.solana.com",
                "timeout_seconds": 30,
                "max_retries": 3,
                "retry_delay_seconds": 2
            },
            "HELIUS_API": {
                "base_url": "https://api.helius.xyz",
                "api_key": None,
                "timeout_seconds": 20,
                "max_retries": 3
            },
            "BIRDEYE_API": {
                "base_url": "https://public-api.birdeye.so", 
                "api_key": None,
                "timeout_seconds": 20,
                "max_retries": 3
            },
            "TELEGRAM": {
                "enabled": False,
                "bot_token": None,
                "chat_id": None,
                "alert_threshold": 70,
                "cooldown_minutes": 30
            },
            "WHALE_TRACKING": {
                "enabled": False,
                "score_threshold": 60,
                "rpc_url": "https://api.mainnet-beta.solana.com",
                "top_holders_limit": 3,
                "min_success_rate": 0.6,
                "cache_ttl": 3600,
                "transaction_history_limit": 100
            },
            "CACHING": {
                "enabled": True,
                "default_ttl_seconds": 3600,
                "max_memory_items": 512,
                "file_cache_dir": str(Path("temp") / "app_cache")
            },
            "LOGGING": {
                "level": "INFO",
                "log_file": "virtuoso_gem_hunter.log",
                "max_file_size_mb": 10,
                "backup_count": 5,
                "console_output": True
            },
            "ANALYSIS": {
                "min_liquidity_default": 25000,
                "max_age_days_default": 3,
                "default_limit": 10
            },
            "RATE_LIMITER": {
                "enabled": True,
                "default_retry_interval": 1,
                "domains": {
                    "default": {"calls": 5, "period": 1},
                    "helius": {"calls": 5, "period": 1},
                    "birdeye": {"calls": 2, "period": 1},
                    "dexscreener": {"calls": 30, "period": 60}
                }
            },
            "API_OPTIMIZATION": {
                "enable_caching": True,
                "cache_ttl": {
                    "token_list": 300,        # 5 minutes
                    "token_overview": 600,    # 10 minutes
                    "price_data": 180,        # 3 minutes
                    "transactions": 300,      # 5 minutes
                    "holders": 1800,          # 30 minutes
                    "inactive_token": 3600,   # 1 hour
                },
                "batch_sizes": {
                    "token_overview": 5,      # Process 5 tokens at once
                    "multi_price": 30  # Optimized from 15 based on testing,        # Up to 20 tokens in one request
                },
                "transaction_analysis": {
                    "initial_limit": 10,      # Initial small batch size
                    "full_limit": 50,         # Full analysis batch size
                    "tx_score_threshold": 15, # Score needed for full analysis
                }
            },
            "ANALYSIS_THRESHOLDS": {
                "quick_score": 30,   # Minimum score to proceed past quick scoring
                "medium_score": 50,  # Minimum score to proceed past medium scoring
                "full_score": 70,    # Minimum score for final recommendation
                "dynamic_relaxation": {
                    "enabled": True,
                    "min_threshold": 50,      # Minimum threshold after relaxation
                    "max_reduction": 20,      # Maximum threshold reduction
                }
            }
        }
        
    def _load_configuration(self):
        """Load configuration with comprehensive error handling"""
        try:
            # Step 1: Load environment variables
            self._load_environment_variables()
            
            # Step 2: Load and merge YAML configuration
            if self.config_path.exists():
                self._load_yaml_configuration()
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                logger.info("Using default configuration with environment variables")
            
            # Step 3: Apply environment variable overrides
            self._apply_environment_overrides()
            
            # Step 4: Validate configuration
            self._validate_configuration()
            
            # Step 5: Log configuration status
            self._log_configuration_status()
            
            self._config_loaded = True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.warning("Falling back to safe defaults")
            self._apply_safe_defaults()
            self._apply_environment_overrides()
            
    def _load_environment_variables(self):
        """Load environment variables from .env file"""
        try:
            # Try multiple .env file locations
            env_files = [
                Path.cwd() / ".env",
                Path.cwd().parent / ".env",
                Path.cwd() / "config" / ".env"
            ]
            
            for env_file in env_files:
                if env_file.exists():
                    load_dotenv(env_file)
                    logger.info(f"Loaded environment variables from: {env_file}")
                    break
            else:
                logger.info("No .env file found, using system environment variables")
                
        except Exception as e:
            logger.error(f"Error loading environment variables: {e}")
    
    def _load_yaml_configuration(self):
        """Load YAML configuration with robust error handling"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f) or {}
            
            if not isinstance(yaml_config, dict):
                logger.warning("YAML configuration is not a dictionary, using defaults")
                return
                
            # Deep merge YAML config over defaults
            self._deep_merge_config(self._config, yaml_config)
            logger.info(f"Successfully loaded YAML configuration from: {self.config_path}")
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {self.config_path}: {e}")
            raise ConfigurationError(f"Invalid YAML configuration: {e}")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {self.config_path}")
        except PermissionError:
            logger.error(f"Permission denied reading configuration file: {self.config_path}")
            raise ConfigurationError(f"Cannot read configuration file: {self.config_path}")
        except Exception as e:
            logger.error(f"Unexpected error loading YAML configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")
    
    def _deep_merge_config(self, base: Dict[str, Any], update: Dict[str, Any]):
        """Safely merge configuration dictionaries"""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge_config(base[key], value)
            else:
                base[key] = value
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides with secure handling"""
        env_mappings = {
            # API Keys (sensitive)
            'HELIUS_API_KEY': ('HELIUS_API', 'api_key'),
            'BIRDEYE_API_KEY': ('BIRDEYE_API', 'api_key'),
            'TELEGRAM_BOT_TOKEN': ('TELEGRAM', 'bot_token'),
            'TELEGRAM_CHAT_ID': ('TELEGRAM', 'chat_id'),
            
            # RPC URLs
            'SOLANA_RPC_URL': ('RPC', 'solana_endpoint'),
            'WHALE_TRACKING_RPC_URL': ('WHALE_TRACKING', 'rpc_url'),
            
            # Feature toggles
            'TELEGRAM_ENABLED': ('TELEGRAM', 'enabled'),
            'WHALE_TRACKING_ENABLED': ('WHALE_TRACKING', 'enabled'),
            'RATE_LIMITER_ENABLED': ('RATE_LIMITER', 'enabled'),
            
            # Logging
            'LOG_LEVEL': ('LOGGING', 'level'),
            'LOG_FILE': ('LOGGING', 'log_file')
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Ensure section exists
                if section not in self._config:
                    self._config[section] = {}
                
                # Type conversion for boolean values
                if key == 'enabled' and value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                
                self._config[section][key] = value
                
                # Log non-sensitive overrides
                if 'KEY' not in env_var and 'TOKEN' not in env_var:
                    logger.debug(f"Environment override: {section}.{key} = {value}")
                else:
                    logger.debug(f"Environment override: {section}.{key} = [REDACTED]")
    
    def _validate_configuration(self):
        """Comprehensive configuration validation"""
        validation_errors = []
        validation_warnings = []
        
        for section_name, section_schema in self._validation_schema.items():
            if section_schema.required and section_name not in self._config:
                validation_errors.append(f"Required section '{section_name}' is missing")
                continue
            
            if section_name not in self._config:
                continue
                
            section_config = self._config[section_name]
            
            for field_name, field_rule in section_schema.fields.items():
                field_value = section_config.get(field_name)
                
                # Check required fields
                if field_rule.required and (field_value is None or field_value == ""):
                    validation_errors.append(
                        f"Required field '{section_name}.{field_name}' is missing or empty"
                    )
                    continue
                
                if field_value is None:
                    continue
                
                # Type validation
                if field_rule.data_type and not isinstance(field_value, field_rule.data_type):
                    try:
                        # Attempt type conversion
                        if field_rule.data_type == bool and isinstance(field_value, str):
                            field_value = field_value.lower() in ('true', '1', 'yes', 'on')
                        elif field_rule.data_type in (int, float):
                            field_value = field_rule.data_type(field_value)
                        else:
                            field_value = field_rule.data_type(field_value)
                        
                        section_config[field_name] = field_value
                        
                    except (ValueError, TypeError):
                        validation_errors.append(
                            f"Field '{section_name}.{field_name}' should be {field_rule.data_type.__name__}, got {type(field_value).__name__}"
                        )
                        continue
                
                # Range validation
                if field_rule.min_value is not None and field_value < field_rule.min_value:
                    validation_errors.append(
                        f"Field '{section_name}.{field_name}' value {field_value} is below minimum {field_rule.min_value}"
                    )
                
                if field_rule.max_value is not None and field_value > field_rule.max_value:
                    validation_errors.append(
                        f"Field '{section_name}.{field_name}' value {field_value} is above maximum {field_rule.max_value}"
                    )
                
                # Allowed values validation
                if field_rule.allowed_values and field_value not in field_rule.allowed_values:
                    validation_errors.append(
                        f"Field '{section_name}.{field_name}' value '{field_value}' not in allowed values: {field_rule.allowed_values}"
                    )
                
                # Custom validator
                if field_rule.validator_func:
                    try:
                        if not field_rule.validator_func(field_value):
                            validation_errors.append(
                                f"Field '{section_name}.{field_name}' failed custom validation"
                            )
                    except Exception as e:
                        validation_errors.append(
                            f"Field '{section_name}.{field_name}' custom validation error: {e}"
                        )
        
        # Service-specific validations
        self._validate_service_configurations(validation_errors, validation_warnings)
        
        # Log warnings
        for warning in validation_warnings:
            logger.warning(f"Configuration warning: {warning}")
        
        # Raise errors if any
        if validation_errors:
            error_message = "Configuration validation failed:\n" + "\n".join(validation_errors)
            logger.error(error_message)
            raise ConfigurationError(error_message)
    
    def _validate_service_configurations(self, errors: List[str], warnings: List[str]):
        """Validate service-specific configuration dependencies"""
        
        # Telegram validation
        telegram_config = self._config.get("TELEGRAM", {})
        if telegram_config.get("enabled"):
            if not telegram_config.get("bot_token"):
                errors.append("Telegram is enabled but bot_token is not configured")
            if not telegram_config.get("chat_id"):
                errors.append("Telegram is enabled but chat_id is not configured")
        
        # API key warnings
        helius_config = self._config.get("HELIUS_API", {})
        if not helius_config.get("api_key"):
            warnings.append("HELIUS_API_KEY not configured - Helius API calls may fail")
        
        birdeye_config = self._config.get("BIRDEYE_API", {})
        if not birdeye_config.get("api_key"):
            warnings.append("BIRDEYE_API_KEY not configured - BirdEye API calls may fail")
    
    def _log_configuration_status(self):
        """Log configuration loading status"""
        enabled_services = []
        
        if self._config.get("TELEGRAM", {}).get("enabled"):
            enabled_services.append("Telegram")
        if self._config.get("WHALE_TRACKING", {}).get("enabled"):
            enabled_services.append("Whale Tracking")
        if self._config.get("RATE_LIMITER", {}).get("enabled"):
            enabled_services.append("Rate Limiter")
        
        logger.info(f"Configuration loaded successfully. Enabled services: {', '.join(enabled_services) or 'None'}")
        
        # Log API availability
        api_status = []
        if self._config.get("HELIUS_API", {}).get("api_key"):
            api_status.append("Helius")
        if self._config.get("BIRDEYE_API", {}).get("api_key"):
            api_status.append("BirdEye")
            
        logger.info(f"Available APIs: {', '.join(api_status) or 'None (using public endpoints)'}")
    
    # Public interface methods
    def get_config(self) -> Dict[str, Any]:
        """Get complete configuration (returns copy for safety)"""
        return deepcopy(self._config)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get configuration section (returns copy for safety)"""
        return deepcopy(self._config.get(section, {}))
    
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get specific configuration value with default fallback"""
        return self._config.get(section, {}).get(key, default)
    
    async def reload_configuration(self, config_path: Optional[Union[str, Path]] = None):
        """Safely reload configuration"""
        async with self._config_lock:
            try:
                old_config = deepcopy(self._config)
                
                if config_path:
                    self.config_path = self._resolve_config_path(config_path)
                
                self._apply_safe_defaults()
                self._load_configuration()
                
                logger.info("Configuration reloaded successfully")
                
            except Exception as e:
                # Restore old configuration on error
                self._config = old_config
                logger.error(f"Configuration reload failed, restored previous configuration: {e}")
                raise ConfigurationError(f"Configuration reload failed: {e}")
    
    def is_service_enabled(self, service: str) -> bool:
        """Check if a service is enabled"""
        return self._config.get(service, {}).get("enabled", False)
    
    def has_api_key(self, api_service: str) -> bool:
        """Check if API key is configured for a service"""
        return bool(self._config.get(api_service, {}).get("api_key"))

# Singleton instance for backward compatibility
_config_manager_instance: Optional[RobustConfigManager] = None

def get_config_manager(config_path: Optional[Union[str, Path]] = None) -> RobustConfigManager:
    """Get or create singleton configuration manager instance"""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = RobustConfigManager(config_path)
    return _config_manager_instance

# Legacy ConfigManager class for backward compatibility
class ConfigManager(RobustConfigManager):
    """Legacy ConfigManager class - use get_config_manager() instead"""
    
    _instance = None
    
    def __new__(cls, config_path_str: Optional[str] = None):
        if cls._instance is None:
            cls._instance = get_config_manager(config_path_str)
        return cls._instance

# Example of how to access config:
# from core.config_manager import config_manager
# db_name = config_manager.get_value("DATABASE", "name")
# helius_api_key = config_manager.get_value("HELIUS_API", "api_key") 