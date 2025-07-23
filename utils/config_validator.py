#!/usr/bin/env python3
"""
Configuration Validator

Validates configuration files at runtime to catch issues early.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

class ConfigValidator:
    """Validate configuration files and environment variables"""
    
    def __init__(self):
        self.logger = logging.getLogger('ConfigValidator')
        self.errors = []
        self.warnings = []
        
    def validate_config(self, config: Dict) -> Tuple[bool, List[str], List[str]]:
        """Validate entire configuration dictionary"""
        
        self.errors = []
        self.warnings = []
        
        # Validate core sections
        self._validate_analysis_config(config.get('ANALYSIS', {}))
        self._validate_telegram_config(config.get('TELEGRAM', {}))
        self._validate_birdeye_config(config.get('BIRDEYE_API', {}))
        self._validate_environment_variables()
        self._validate_file_paths()
        
        # Check for conflicts
        self._validate_threshold_consistency(config)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_analysis_config(self, analysis_config: Dict):
        """Validate ANALYSIS section"""
        
        # Check alert score threshold
        alert_threshold = analysis_config.get('alert_score_threshold')
        if alert_threshold is None:
            self.errors.append("ANALYSIS.alert_score_threshold is missing")
        elif not isinstance(alert_threshold, (int, float)):
            self.errors.append("ANALYSIS.alert_score_threshold must be a number")
        elif alert_threshold < 0 or alert_threshold > 100:
            self.errors.append("ANALYSIS.alert_score_threshold must be between 0 and 100")
        elif alert_threshold < 20:
            self.warnings.append("ANALYSIS.alert_score_threshold is very low (<20) - may generate too many alerts")
        elif alert_threshold > 80:
            self.warnings.append("ANALYSIS.alert_score_threshold is very high (>80) - may miss opportunities")
        
        # Check scoring configuration
        scoring = analysis_config.get('scoring', {})
        cross_platform = scoring.get('cross_platform', {})
        
        high_conviction = cross_platform.get('high_conviction_threshold')
        if high_conviction is None:
            self.errors.append("ANALYSIS.scoring.cross_platform.high_conviction_threshold is missing")
        elif not isinstance(high_conviction, (int, float)):
            self.errors.append("ANALYSIS.scoring.cross_platform.high_conviction_threshold must be a number")
        elif high_conviction < 0 or high_conviction > 100:
            self.errors.append("ANALYSIS.scoring.cross_platform.high_conviction_threshold must be between 0 and 100")
        
        # Check scoring weights
        weights = analysis_config.get('scoring_weights', {})
        if weights:
            weight_sum = sum(weights.values())
            if abs(weight_sum - 1.0) > 0.01:  # Allow small floating point errors
                self.warnings.append(f"ANALYSIS.scoring_weights sum to {weight_sum:.2f}, should be 1.0")
            
            required_weights = ['age', 'concentration', 'liquidity', 'price_change', 'volume']
            missing_weights = [w for w in required_weights if w not in weights]
            if missing_weights:
                self.warnings.append(f"Missing scoring weights: {', '.join(missing_weights)}")
    
    def _validate_telegram_config(self, telegram_config: Dict):
        """Validate TELEGRAM section"""
        
        if not telegram_config.get('enabled', False):
            self.warnings.append("TELEGRAM.enabled is false - alerts will not be sent")
            return
        
        # Check required fields
        if 'bot_token' not in telegram_config:
            self.errors.append("TELEGRAM.bot_token is missing")
        
        if 'chat_id' not in telegram_config:
            self.errors.append("TELEGRAM.chat_id is missing")
        
        # Check alert limits
        max_alerts = telegram_config.get('max_alerts_per_hour')
        if max_alerts is not None:
            if not isinstance(max_alerts, int) or max_alerts < 1:
                self.errors.append("TELEGRAM.max_alerts_per_hour must be a positive integer")
            elif max_alerts > 60:
                self.warnings.append("TELEGRAM.max_alerts_per_hour is very high (>60) - may hit rate limits")
        
        # Check cooldown
        cooldown = telegram_config.get('cooldown_minutes')
        if cooldown is not None:
            if not isinstance(cooldown, (int, float)) or cooldown < 0:
                self.errors.append("TELEGRAM.cooldown_minutes must be a non-negative number")
            elif cooldown > 1440:  # 24 hours
                self.warnings.append("TELEGRAM.cooldown_minutes is very long (>24h)")
    
    def _validate_birdeye_config(self, birdeye_config: Dict):
        """Validate BIRDEYE_API section"""
        
        if not birdeye_config.get('api_key'):
            self.errors.append("BIRDEYE_API.api_key is missing")
        
        if not birdeye_config.get('base_url'):
            self.errors.append("BIRDEYE_API.base_url is missing")
        elif not birdeye_config['base_url'].startswith('https://'):
            self.warnings.append("BIRDEYE_API.base_url should use HTTPS")
        
        # Check rate limiting
        rate_limit = birdeye_config.get('rate_limit_requests_per_second')
        if rate_limit is not None:
            if not isinstance(rate_limit, (int, float)) or rate_limit <= 0:
                self.errors.append("BIRDEYE_API.rate_limit_requests_per_second must be positive")
            elif rate_limit > 100:
                self.warnings.append("BIRDEYE_API.rate_limit_requests_per_second is very high - may exceed API limits")
        
        # Check timeout
        timeout = birdeye_config.get('request_timeout_seconds')
        if timeout is not None:
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                self.errors.append("BIRDEYE_API.request_timeout_seconds must be positive")
            elif timeout > 60:
                self.warnings.append("BIRDEYE_API.request_timeout_seconds is very high (>60s)")
    
    def _validate_environment_variables(self):
        """Validate required environment variables"""
        
        required_env_vars = [
            ('BIRDEYE_API_KEY', 'Birdeye API functionality will not work'),
            ('TELEGRAM_BOT_TOKEN', 'Telegram alerts will not work'),
            ('TELEGRAM_CHAT_ID', 'Telegram alerts will not work')
        ]
        
        for env_var, consequence in required_env_vars:
            if not os.getenv(env_var):
                self.warnings.append(f"Environment variable {env_var} is missing - {consequence}")
        
        # Validate format of specific variables
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if chat_id and not chat_id.isdigit() and not chat_id.startswith('-'):
            self.warnings.append("TELEGRAM_CHAT_ID should be a number (user ID or negative for groups)")
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if bot_token and ':' not in bot_token:
            self.errors.append("TELEGRAM_BOT_TOKEN format appears invalid (should contain ':')")
    
    def _validate_file_paths(self):
        """Validate file paths and directories"""
        
        # Check data directory
        data_dir = Path("data")
        if not data_dir.exists():
            self.warnings.append("data/ directory does not exist - will be created at runtime")
        
        # Check logs directory
        logs_dir = Path("logs")
        if not logs_dir.exists():
            self.warnings.append("logs/ directory does not exist - will be created at runtime")
        
        # Check config directory
        config_dir = Path("config")
        if not config_dir.exists():
            self.errors.append("config/ directory does not exist")
        
        # Check main config file
        main_config = Path("config/config.yaml")
        if not main_config.exists():
            self.errors.append("config/config.yaml does not exist")
    
    def _validate_threshold_consistency(self, config: Dict):
        """Validate threshold consistency across configuration"""
        
        analysis_config = config.get('ANALYSIS', {})
        
        alert_threshold = analysis_config.get('alert_score_threshold', 0)
        high_conviction = analysis_config.get('scoring', {}).get('cross_platform', {}).get('high_conviction_threshold', 0)
        final_alert_threshold = analysis_config.get('scoring', {}).get('final_scoring', {}).get('alert_threshold', 0)
        
        # Check logical consistency
        if high_conviction > 0 and alert_threshold > 0:
            if high_conviction < alert_threshold:
                self.warnings.append(f"high_conviction_threshold ({high_conviction}) is lower than alert_score_threshold ({alert_threshold})")
        
        if final_alert_threshold > 0 and alert_threshold > 0:
            if abs(final_alert_threshold - alert_threshold) > 10:
                self.warnings.append(f"final_scoring.alert_threshold ({final_alert_threshold}) differs significantly from main alert_score_threshold ({alert_threshold})")
        
        # Check Telegram config consistency
        telegram_config = config.get('TELEGRAM', {})
        telegram_threshold = telegram_config.get('alert_threshold')
        if telegram_threshold and alert_threshold:
            if abs(telegram_threshold - alert_threshold) > 5:
                self.warnings.append(f"TELEGRAM.alert_threshold ({telegram_threshold}) differs from ANALYSIS.alert_score_threshold ({alert_threshold})")
    
    def validate_at_runtime(self, config: Dict, strict: bool = False) -> bool:
        """Validate configuration at runtime with logging"""
        
        is_valid, errors, warnings = self.validate_config(config)
        
        # Log results
        if errors:
            self.logger.error("Configuration validation failed:")
            for error in errors:
                self.logger.error(f"  ❌ {error}")
        
        if warnings:
            self.logger.warning("Configuration warnings:")
            for warning in warnings:
                self.logger.warning(f"  ⚠️ {warning}")
        
        if is_valid and not warnings:
            self.logger.info("✅ Configuration validation passed")
        elif is_valid:
            self.logger.info(f"✅ Configuration validation passed with {len(warnings)} warnings")
        
        # In strict mode, warnings are treated as errors
        if strict and warnings:
            self.logger.error("Strict mode: Treating warnings as errors")
            return False
        
        return is_valid
    
    def get_validation_summary(self) -> Dict:
        """Get a summary of validation results"""
        return {
            "is_valid": len(self.errors) == 0,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings
        }

def validate_config_file(config_path: str = "config/config.yaml") -> bool:
    """Standalone function to validate a config file"""
    
    import yaml
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        validator = ConfigValidator()
        is_valid, errors, warnings = validator.validate_config(config)
        
        print(f"🔍 Validating {config_path}")
        print("-" * 40)
        
        if errors:
            print("❌ ERRORS:")
            for error in errors:
                print(f"  • {error}")
        
        if warnings:
            print("⚠️ WARNINGS:")
            for warning in warnings:
                print(f"  • {warning}")
        
        if is_valid and not warnings:
            print("✅ Configuration is valid")
        elif is_valid:
            print(f"✅ Configuration is valid with {len(warnings)} warnings")
        else:
            print(f"❌ Configuration is invalid ({len(errors)} errors)")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Failed to load config file: {e}")
        return False

if __name__ == "__main__":
    import sys
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
    success = validate_config_file(config_file)
    sys.exit(0 if success else 1)