#!/usr/bin/env python3
"""
Enhanced Telegram Alerter with Retry Logic and Delivery Confirmation

Improvements:
- Retry logic for temporary failures
- Alert delivery confirmation tracking
- Health monitoring and statistics
- Better HTML entity parsing
- Exponential backoff for rate limiting
"""

import requests
import logging
import time
import json
import html
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import threading
from datetime import datetime, timedelta

from services.logger_setup import LoggerSetup
from utils.structured_logger import get_structured_logger

@dataclass
class AlertAttempt:
    """Track individual alert attempts"""
    timestamp: float
    success: bool
    error_message: str = ""
    response_data: Dict = field(default_factory=dict)
    attempt_number: int = 1

@dataclass
class AlertStats:
    """Track alerting statistics"""
    total_attempts: int = 0
    successful_sends: int = 0
    failed_sends: int = 0
    retry_attempts: int = 0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    html_parse_errors: int = 0
    rate_limit_hits: int = 0

class EnhancedTelegramAlerter:
    """Enhanced Telegram alerter with retry logic and monitoring"""
    
    def __init__(self, bot_token: str, chat_id: str, config: Optional[Dict] = None, logger_setup: Optional[LoggerSetup] = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.config = config if config is not None else {}
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Retry configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 2.0)  # seconds
        self.backoff_multiplier = self.config.get('backoff_multiplier', 2.0)
        self.timeout = self.config.get('timeout', 15)
        
        # Setup logging
        if logger_setup:
            self.logger = logger_setup.logger
        else:
            self.logger = logging.getLogger('EnhancedTelegramAlerter')
        
        self.structured_logger = get_structured_logger('EnhancedAlertingService')
        
        # Alert tracking
        self.stats = AlertStats()
        self.recent_attempts: List[AlertAttempt] = []
        self.failed_alerts_log = Path("data/failed_alerts.json")
        self.stats_lock = threading.Lock()
        
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        self.logger.info("✅ Enhanced Telegram Alerter initialized")
    
    def send_gem_alert(self, metrics, score: float, score_breakdown: Optional[dict] = None, 
                      enhanced_data: Optional[dict] = None, pair_address: Optional[str] = None, 
                      scan_id: Optional[str] = None) -> bool:
        """Send gem alert with retry logic and delivery confirmation"""
        
        alert_id = f"{scan_id or 'unknown'}_{metrics.address[:8]}_{int(time.time())}"
        
        try:
            # Build message
            message = self._build_enhanced_message(metrics, score, enhanced_data)
            
            # Send with retry logic
            success, attempts = self._send_with_retry(message, alert_id, max_retries=self.max_retries)
            
            # Update statistics
            self._update_stats(success, attempts)
            
            # Log result
            if success:
                self.structured_logger.info({
                    "event": "alert_send_success",
                    "alert_id": alert_id,
                    "token": metrics.address,
                    "attempts": len(attempts),
                    "timestamp": int(time.time())
                })
                self.logger.info(f"✅ Successfully sent gem alert for {metrics.symbol} after {len(attempts)} attempts")
            else:
                self._log_failed_alert(alert_id, metrics, attempts)
                self.logger.error(f"❌ Failed to send gem alert for {metrics.symbol} after {len(attempts)} attempts")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Exception in send_gem_alert: {e}")
            return False
    
    def _send_with_retry(self, message: str, alert_id: str, max_retries: int = 3) -> Tuple[bool, List[AlertAttempt]]:
        """Send message with exponential backoff retry logic"""
        
        attempts = []
        delay = self.retry_delay
        
        for attempt_num in range(1, max_retries + 1):
            attempt_start = time.time()
            
            try:
                # Send the message
                success, response_data, error_msg = self._send_message_attempt(message)
                
                attempt = AlertAttempt(
                    timestamp=attempt_start,
                    success=success,
                    error_message=error_msg,
                    response_data=response_data,
                    attempt_number=attempt_num
                )
                attempts.append(attempt)
                
                if success:
                    self.logger.debug(f"✅ Alert sent successfully on attempt {attempt_num}")
                    return True, attempts
                
                # Check if we should retry
                if not self._should_retry(error_msg, response_data):
                    self.logger.warning(f"⏹️ Not retrying due to permanent error: {error_msg}")
                    break
                
                # Wait before retry (except on last attempt)
                if attempt_num < max_retries:
                    self.logger.info(f"🔄 Retrying in {delay:.1f}s (attempt {attempt_num + 1}/{max_retries})")
                    time.sleep(delay)
                    delay *= self.backoff_multiplier
                    
            except Exception as e:
                attempt = AlertAttempt(
                    timestamp=attempt_start,
                    success=False,
                    error_message=f"Exception: {str(e)}",
                    attempt_number=attempt_num
                )
                attempts.append(attempt)
                
                if attempt_num < max_retries:
                    time.sleep(delay)
                    delay *= self.backoff_multiplier
        
        return False, attempts
    
    def _send_message_attempt(self, message: str) -> Tuple[bool, Dict, str]:
        """Single attempt to send message to Telegram"""
        
        if not message or not message.strip():
            return False, {}, "Empty message"
        
        # Truncate if too long
        if len(message) > 4096:
            message = message[:4093] + "..."
            self.logger.warning("📏 Message truncated to fit Telegram limit")
        
        url = f"{self.base_url}/sendMessage"
        
        # Try HTML parsing first
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('ok'):
                return True, response_data, ""
            
            # Handle specific errors
            error_description = response_data.get('description', 'Unknown error')
            
            # If HTML parsing failed, try plain text
            if 'parse entities' in error_description.lower():
                self.stats.html_parse_errors += 1
                self.logger.warning("🔧 HTML parsing failed, trying plain text")
                return self._send_plain_text_fallback(message)
            
            # Handle rate limiting
            if response.status_code == 429:
                self.stats.rate_limit_hits += 1
                retry_after = response_data.get('parameters', {}).get('retry_after', 30)
                return False, response_data, f"Rate limited (retry after {retry_after}s)"
            
            return False, response_data, error_description
            
        except requests.exceptions.Timeout:
            return False, {}, f"Request timeout after {self.timeout}s"
        except requests.exceptions.RequestException as e:
            return False, {}, f"Request error: {str(e)}"
        except Exception as e:
            return False, {}, f"Unexpected error: {str(e)}"
    
    def _send_plain_text_fallback(self, message: str) -> Tuple[bool, Dict, str]:
        """Send message as plain text (fallback for HTML parsing errors)"""
        
        # Strip HTML tags for plain text
        import re
        plain_message = re.sub(r'<[^>]+>', '', message)
        plain_message = html.unescape(plain_message)
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': plain_message,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('ok'):
                return True, response_data, ""
            else:
                error_description = response_data.get('description', 'Unknown error')
                return False, response_data, f"Plain text fallback failed: {error_description}"
                
        except Exception as e:
            return False, {}, f"Plain text fallback error: {str(e)}"
    
    def _should_retry(self, error_msg: str, response_data: Dict) -> bool:
        """Determine if an error is retryable"""
        
        # Don't retry permanent errors
        permanent_errors = [
            'bot was blocked',
            'user not found',
            'chat not found',
            'forbidden',
            'unauthorized'
        ]
        
        error_lower = error_msg.lower()
        for permanent in permanent_errors:
            if permanent in error_lower:
                return False
        
        # Don't retry bad request unless it's a parsing issue
        if 'bad request' in error_lower and 'parse entities' not in error_lower:
            return False
        
        # Retry temporary errors
        return True
    
    def _build_enhanced_message(self, metrics, score: float, enhanced_data: Optional[dict]) -> str:
        """Build enhanced alert message with better HTML escaping"""
        
        # Safe HTML escaping
        symbol = html.escape(str(metrics.symbol))
        name = html.escape(str(metrics.name))
        address = str(metrics.address)
        
        # Score-based styling
        if score >= 80:
            emoji = "🚀🔥💎"
            status = "PREMIUM GEM"
        elif score >= 60:
            emoji = "🚀💎"
            status = "HIGH POTENTIAL"
        elif score >= 40:
            emoji = "📈💎"
            status = "SOLID OPPORTUNITY"
        else:
            emoji = "📊"
            status = "HIGH CONVICTION"
        
        # Build message sections
        sections = []
        
        # Header
        header = f"{emoji} <b>VIRTUOSO GEM DETECTED</b> {emoji}\\n"
        header += f"<b>{status}</b>\\n"
        header += f"<b>Token:</b> {name} ({symbol})\\n"
        header += f"<b>Score:</b> {score:.1f}/100"
        sections.append(header)
        
        # Core metrics
        metrics_section = "💎 <b>CORE METRICS</b>\\n"
        
        # Safe price formatting
        try:
            price = float(metrics.price) if metrics.price else 0
            if price < 0.000001:
                price_str = f"${price:.8f}"
            elif price < 0.01:
                price_str = f"${price:.6f}"
            else:
                price_str = f"${price:.4f}"
            metrics_section += f"💰 <b>Price:</b> {price_str}\\n"
        except:
            metrics_section += f"💰 <b>Price:</b> N/A\\n"
        
        # Safe market cap formatting
        try:
            market_cap = float(metrics.market_cap) if hasattr(metrics, 'market_cap') and metrics.market_cap else 0
            if market_cap > 0:
                metrics_section += f"📊 <b>Market Cap:</b> ${market_cap:,.0f}\\n"
        except:
            pass
        
        # Safe liquidity formatting
        try:
            liquidity = float(metrics.liquidity) if metrics.liquidity else 0
            if liquidity > 0:
                metrics_section += f"🌊 <b>Liquidity:</b> ${liquidity:,.0f}\\n"
        except:
            pass
        
        sections.append(metrics_section.rstrip('\\n'))
        
        # Quick actions
        actions = "🔗 <b>QUICK ACTIONS</b>\\n"
        actions += f"📊 <a href=\\"https://dexscreener.com/solana/{address}\\">DexScreener</a> | "
        actions += f"🔍 <a href=\\"https://rugcheck.xyz/tokens/{address}\\">RugCheck</a> | "
        actions += f"📈 <a href=\\"https://birdeye.so/token/{address}\\">Birdeye</a>"
        sections.append(actions)
        
        return "\\n\\n".join(sections)
    
    def _update_stats(self, success: bool, attempts: List[AlertAttempt]):
        """Update alerting statistics"""
        with self.stats_lock:
            self.stats.total_attempts += 1
            self.stats.retry_attempts += len(attempts) - 1
            
            if success:
                self.stats.successful_sends += 1
                self.stats.last_success = time.time()
            else:
                self.stats.failed_sends += 1
                self.stats.last_failure = time.time()
            
            # Keep recent attempts (last 100)
            self.recent_attempts.extend(attempts)
            self.recent_attempts = self.recent_attempts[-100:]
    
    def _log_failed_alert(self, alert_id: str, metrics, attempts: List[AlertAttempt]):
        """Log failed alert for debugging"""
        failed_alert = {
            "alert_id": alert_id,
            "timestamp": time.time(),
            "token_address": metrics.address,
            "token_symbol": metrics.symbol,
            "attempts": [
                {
                    "attempt_number": attempt.attempt_number,
                    "timestamp": attempt.timestamp,
                    "error": attempt.error_message,
                    "response": attempt.response_data
                } for attempt in attempts
            ]
        }
        
        # Append to failed alerts log
        try:
            if self.failed_alerts_log.exists():
                with open(self.failed_alerts_log, 'r') as f:
                    failed_alerts = json.load(f)
            else:
                failed_alerts = []
            
            failed_alerts.append(failed_alert)
            
            # Keep only last 50 failed alerts
            failed_alerts = failed_alerts[-50:]
            
            with open(self.failed_alerts_log, 'w') as f:
                json.dump(failed_alerts, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to log failed alert: {e}")
    
    def get_health_status(self) -> Dict:
        """Get alerting system health status"""
        with self.stats_lock:
            if self.stats.total_attempts == 0:
                success_rate = 0.0
            else:
                success_rate = (self.stats.successful_sends / self.stats.total_attempts) * 100
            
            # Recent success rate (last 24 hours)
            recent_cutoff = time.time() - (24 * 60 * 60)
            recent_attempts = [a for a in self.recent_attempts if a.timestamp > recent_cutoff]
            recent_successes = len([a for a in recent_attempts if a.success])
            recent_success_rate = (recent_successes / len(recent_attempts)) * 100 if recent_attempts else 0.0
            
            return {
                "total_attempts": self.stats.total_attempts,
                "successful_sends": self.stats.successful_sends,
                "failed_sends": self.stats.failed_sends,
                "success_rate_percent": round(success_rate, 1),
                "recent_success_rate_percent": round(recent_success_rate, 1),
                "retry_attempts": self.stats.retry_attempts,
                "html_parse_errors": self.stats.html_parse_errors,
                "rate_limit_hits": self.stats.rate_limit_hits,
                "last_success": datetime.fromtimestamp(self.stats.last_success).isoformat() if self.stats.last_success else None,
                "last_failure": datetime.fromtimestamp(self.stats.last_failure).isoformat() if self.stats.last_failure else None,
                "health_status": "good" if recent_success_rate >= 90 else "warning" if recent_success_rate >= 70 else "poor"
            }
    
    def send_test_message(self, message: str = "🎤 Test message from Enhanced Telegram Alerter") -> bool:
        """Send a test message to verify connectivity"""
        success, attempts = self._send_with_retry(message, f"test_{int(time.time())}")
        return success