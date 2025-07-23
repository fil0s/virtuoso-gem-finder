#!/usr/bin/env python3
"""
Security Manager for Virtuoso Gem Hunter
Handles API key validation, rate limiting, and security monitoring
"""

import os
import hashlib
import time
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    mode: str = "development"
    rate_limit_enabled: bool = True
    debug_mode: bool = False
    api_timeout: int = 30
    max_requests_per_minute: int = 100
    alert_threshold: float = 0.8

class SecurityManager:
    """Manages security aspects of the application"""
    
    def __init__(self):
        self.config = self._load_security_config()
        self.api_usage = {}
        self.rate_limits = {}
        self.logger = logging.getLogger(__name__)
        
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration from environment"""
        return SecurityConfig(
            mode=os.getenv("SECURITY_MODE", "development"),
            rate_limit_enabled=os.getenv("API_RATE_LIMIT_ENABLED", "true").lower() == "true",
            debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
            api_timeout=int(os.getenv("API_TIMEOUT", "30")),
            max_requests_per_minute=int(os.getenv("MAX_REQUESTS_PER_MINUTE", "100"))
        )
    
    def validate_api_key(self, service: str, api_key: str) -> bool:
        """Validate API key format and basic security"""
        if not api_key or api_key.startswith("your_"):
            self.logger.warning(f"Invalid or placeholder API key for {service}")
            return False
            
        # Basic format validation
        if service == "moralis" and not api_key.startswith("eyJ"):
            self.logger.warning(f"Invalid Moralis JWT format for {service}")
            return False
            
        if service == "birdeye" and len(api_key) != 32:
            self.logger.warning(f"Invalid Birdeye key length for {service}")
            return False
            
        if service == "telegram" and ":" not in api_key:
            self.logger.warning(f"Invalid Telegram token format for {service}")
            return False
            
        return True
    
    def check_rate_limit(self, service: str, endpoint: str = "default") -> bool:
        """Check if request is within rate limits"""
        if not self.config.rate_limit_enabled:
            return True
            
        key = f"{service}:{endpoint}"
        current_time = time.time()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = []
            
        # Clean old requests (older than 1 minute)
        self.rate_limits[key] = [
            req_time for req_time in self.rate_limits[key] 
            if current_time - req_time < 60
        ]
        
        # Check if we're within limits
        if len(self.rate_limits[key]) >= self.config.max_requests_per_minute:
            self.logger.warning(f"Rate limit exceeded for {service}:{endpoint}")
            return False
            
        # Add current request
        self.rate_limits[key].append(current_time)
        return True
    
    def log_api_usage(self, service: str, endpoint: str, response_time: float, status: str):
        """Log API usage for monitoring"""
        key = f"{service}:{endpoint}"
        
        if key not in self.api_usage:
            self.api_usage[key] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_response_time": 0.0,
                "last_request": None
            }
            
        self.api_usage[key]["total_requests"] += 1
        self.api_usage[key]["total_response_time"] += response_time
        self.api_usage[key]["last_request"] = datetime.now()
        
        if status == "success":
            self.api_usage[key]["successful_requests"] += 1
            
        # Log security events
        if self.config.debug_mode:
            self.logger.debug(f"API Call: {service}:{endpoint} - {response_time:.2f}s - {status}")
    
    def get_security_metrics(self) -> Dict:
        """Get security and usage metrics"""
        metrics = {
            "security_mode": self.config.mode,
            "rate_limiting_enabled": self.config.rate_limit_enabled,
            "api_usage_summary": {},
            "current_rate_limits": {}
        }
        
        # Calculate usage statistics
        for key, usage in self.api_usage.items():
            if usage["total_requests"] > 0:
                avg_response_time = usage["total_response_time"] / usage["total_requests"]
                success_rate = usage["successful_requests"] / usage["total_requests"]
                
                metrics["api_usage_summary"][key] = {
                    "total_requests": usage["total_requests"],
                    "success_rate": f"{success_rate:.2%}",
                    "avg_response_time": f"{avg_response_time:.2f}s",
                    "last_request": usage["last_request"].isoformat() if usage["last_request"] else None
                }
        
        # Current rate limit status
        current_time = time.time()
        for key, requests in self.rate_limits.items():
            recent_requests = [
                req_time for req_time in requests 
                if current_time - req_time < 60
            ]
            metrics["current_rate_limits"][key] = {
                "requests_last_minute": len(recent_requests),
                "limit": self.config.max_requests_per_minute,
                "utilization": f"{len(recent_requests) / self.config.max_requests_per_minute:.1%}"
            }
            
        return metrics
    
    def mask_sensitive_data(self, data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """Mask sensitive data for logging"""
        if len(data) <= visible_chars * 2:
            return mask_char * len(data)
        
        return data[:visible_chars] + mask_char * (len(data) - visible_chars * 2) + data[-visible_chars:]
    
    def generate_security_report(self) -> str:
        """Generate a security status report"""
        metrics = self.get_security_metrics()
        
        report = [
            "=== SECURITY STATUS REPORT ===",
            f"Security Mode: {metrics['security_mode']}",
            f"Rate Limiting: {'Enabled' if metrics['rate_limiting_enabled'] else 'Disabled'}",
            "",
            "API Usage Summary:"
        ]
        
        for service, stats in metrics["api_usage_summary"].items():
            report.append(f"  {service}:")
            report.append(f"    Total Requests: {stats['total_requests']}")
            report.append(f"    Success Rate: {stats['success_rate']}")
            report.append(f"    Avg Response Time: {stats['avg_response_time']}")
            
        report.append("\nRate Limit Status:")
        for service, limits in metrics["current_rate_limits"].items():
            report.append(f"  {service}: {limits['requests_last_minute']}/{limits['limit']} ({limits['utilization']})")
            
        return "\n".join(report)

# Global security manager instance
security_manager = SecurityManager()

def get_security_manager() -> SecurityManager:
    """Get the global security manager instance"""
    return security_manager