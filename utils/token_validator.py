#!/usr/bin/env python3
"""
Enhanced Token Validation Layer
Comprehensive token validation to prevent unnecessary API calls and reduce costs.
"""

import re
import logging
from typing import List, Dict, Set, Tuple, Optional, Any
import time
from dataclasses import dataclass
from enum import Enum

class TokenValidationResult(Enum):
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    EXCLUDED_TOKEN = "excluded_token"
    DUPLICATE = "duplicate"
    RATE_LIMITED = "rate_limited"

@dataclass
class ValidationStats:
    """Track validation statistics for optimization"""
    total_tokens: int = 0
    valid_tokens: int = 0
    invalid_format: int = 0
    excluded_tokens: int = 0
    duplicates_filtered: int = 0
    rate_limited: int = 0
    validation_time_ms: float = 0

class EnhancedTokenValidator:
    """
    Enhanced Token Validation Layer
    
    Features:
    - Comprehensive format validation for Solana addresses
    - Token exclusion rules (major tokens, stablecoins, etc.)
    - Duplicate detection and filtering
    - Rate limiting protection
    - Validation statistics tracking
    - Cache-aware validation
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Solana address validation patterns
        self.solana_address_pattern = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
        self.ethereum_address_pattern = re.compile(r'^0x[a-fA-F0-9]{40}$')
        
        # Token exclusion sets
        # Only exclude the most major tokens - be less aggressive for gem hunting
        self.major_tokens = {
            # Major cryptocurrencies that we definitely don't want to analyze as "gems"
            'So11111111111111111111111111111111111111112',  # WSOL
            '7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs',  # Ether
            '9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E',  # BTC
        }
        
        self.stablecoins = {
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
            'Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr',  # USDC (old)
            'BXXkv6z8ykpG1yuvUDPgh732wzVHB69RnB9YgSYh3itW'   # USDC.e
        }
        
        self.excluded_tokens = self.major_tokens | self.stablecoins
        
        # Validation tracking
        self.recently_validated = set()  # Cache of recently validated tokens
        self.validation_cache_ttl = 300  # 5 minutes
        self.last_cache_clear = time.time()
        
        # Statistics tracking
        self.stats = ValidationStats()
        self.session_start = time.time()
        
    def validate_token_batch(self, token_addresses: List[str], 
                           enable_format_check: bool = True,
                           enable_exclusion_check: bool = True,
                           enable_duplicate_check: bool = True) -> Tuple[List[str], Dict[str, Any]]:
        """
        Validate a batch of token addresses with comprehensive filtering
        
        Args:
            token_addresses: List of token addresses to validate
            enable_format_check: Check address format validity
            enable_exclusion_check: Check against exclusion lists
            enable_duplicate_check: Remove duplicates
            
        Returns:
            Tuple of (valid_addresses, validation_report)
        """
        start_time = time.time()
        
        if not token_addresses:
            return [], {"error": "No token addresses provided"}
            
        self.logger.info(f"🔍 Validating batch of {len(token_addresses)} token addresses")
        
        valid_addresses = []
        validation_report = {
            "total_input": len(token_addresses),
            "valid_count": 0,
            "filtered_count": 0,
            "invalid_format": [],
            "excluded_tokens": [],
            "duplicates_removed": [],
            "validation_time_ms": 0,
            "filters_applied": []
        }
        
        # Track what filters are being applied
        filters_applied = []
        if enable_format_check:
            filters_applied.append("format_validation")
        if enable_exclusion_check:
            filters_applied.append("exclusion_filtering")
        if enable_duplicate_check:
            filters_applied.append("duplicate_removal")
        validation_report["filters_applied"] = filters_applied
        
        # Step 1: Remove duplicates if enabled
        unique_addresses = token_addresses
        if enable_duplicate_check:
            original_count = len(token_addresses)
            unique_addresses = list(dict.fromkeys(token_addresses))  # Preserve order
            duplicates_removed = original_count - len(unique_addresses)
            if duplicates_removed > 0:
                validation_report["duplicates_removed"] = duplicates_removed
                self.logger.debug(f"🔄 Removed {duplicates_removed} duplicate addresses")
        
        # Step 2: Validate each unique address
        for address in unique_addresses:
            validation_result = self._validate_single_token(
                address, 
                enable_format_check=enable_format_check,
                enable_exclusion_check=enable_exclusion_check
            )
            
            if validation_result == TokenValidationResult.VALID:
                valid_addresses.append(address)
            elif validation_result == TokenValidationResult.INVALID_FORMAT:
                validation_report["invalid_format"].append(address)
            elif validation_result == TokenValidationResult.EXCLUDED_TOKEN:
                validation_report["excluded_tokens"].append(address)
        
        # Update statistics
        validation_time = (time.time() - start_time) * 1000
        validation_report["validation_time_ms"] = round(validation_time, 2)
        validation_report["valid_count"] = len(valid_addresses)
        validation_report["filtered_count"] = len(unique_addresses) - len(valid_addresses)
        
        self._update_stats(validation_report)
        
            # Log results with enhanced structured logging
            success_rate = len(valid_addresses) / len(unique_addresses) if unique_addresses else 0
            
            self.enhanced_logger.info("Batch validation completed",
                                    total_processed=len(unique_addresses),
                                    valid_tokens=len(valid_addresses),
                                    success_rate=f"{success_rate:.2%}",
                                    validation_time_ms=validation_time,
                                    tokens_per_second=len(unique_addresses) / max(validation_time / 1000, 0.001))
            
            if self.debug_mode:
                validation_breakdown = {
                    "invalid_format_count": len(validation_report["invalid_format"]),
                    "excluded_tokens_count": len(validation_report["excluded_tokens"]),
                    "duplicates_removed_count": len(validation_report["duplicates_removed"])
                }
                self.enhanced_logger.debug("Validation breakdown", **validation_breakdown)
            
            # Traditional logging for backward compatibility
            if validation_report["filtered_count"] > 0:
                self.logger.info(f"✅ Validation complete: {len(valid_addresses)}/{len(unique_addresses)} valid "
                               f"({validation_report['filtered_count']} filtered) in {validation_time:.1f}ms")
            else:
                self.logger.info(f"✅ All {len(valid_addresses)} addresses valid in {validation_time:.1f}ms")
                
            return valid_addresses, validation_report
    
    def _validate_single_token(self, address: str, 
                             enable_format_check: bool = True,
                             enable_exclusion_check: bool = True) -> TokenValidationResult:
        """Validate a single token address"""
        
        if not address or not isinstance(address, str):
            return TokenValidationResult.INVALID_FORMAT
            
        address = address.strip()
        
        # Format validation
        if enable_format_check:
            if not self._is_valid_solana_address(address):
                return TokenValidationResult.INVALID_FORMAT
        
        # Exclusion check
        if enable_exclusion_check:
            if self._is_excluded_token(address):
                return TokenValidationResult.EXCLUDED_TOKEN
                
        return TokenValidationResult.VALID
    
    def _is_valid_solana_address(self, address: str) -> bool:
        """Check if address is a valid Solana address format"""
        
        # Basic length and character validation
        if not self.solana_address_pattern.match(address):
            return False
            
        # Check if it's not an Ethereum address
        if self.ethereum_address_pattern.match(address):
            return False
            
        # Length validation (Solana addresses are typically 32-44 characters)
        if len(address) < 32 or len(address) > 44:
            return False
            
        return True
    
    def _is_excluded_token(self, address: str) -> bool:
        """Check if token is in exclusion list"""
        return address in self.excluded_tokens
    
    def _update_stats(self, validation_report: Dict[str, Any]):
        """Update validation statistics"""
        self.stats.total_tokens += validation_report["total_input"]
        self.stats.valid_tokens += validation_report["valid_count"]
        self.stats.invalid_format += len(validation_report["invalid_format"])
        self.stats.excluded_tokens += len(validation_report["excluded_tokens"])
        self.stats.duplicates_filtered += validation_report.get("duplicates_removed", 0)
        self.stats.validation_time_ms += validation_report["validation_time_ms"]
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics"""
        session_duration = time.time() - self.session_start
        
        return {
            "session_stats": {
                "total_tokens_processed": self.stats.total_tokens,
                "valid_tokens": self.stats.valid_tokens,
                "invalid_format": self.stats.invalid_format,
                "excluded_tokens": self.stats.excluded_tokens,
                "duplicates_filtered": self.stats.duplicates_filtered,
                "validation_success_rate": round(self.stats.valid_tokens / max(self.stats.total_tokens, 1) * 100, 2),
                "total_validation_time_ms": round(self.stats.validation_time_ms, 2),
                "average_validation_time_ms": round(self.stats.validation_time_ms / max(self.stats.total_tokens, 1), 2),
                "session_duration_minutes": round(session_duration / 60, 2)
            },
            "exclusion_rules": {
                "major_tokens_count": len(self.major_tokens),
                "stablecoins_count": len(self.stablecoins),
                "total_excluded": len(self.excluded_tokens)
            },
            "performance_metrics": {
                "tokens_per_second": round(self.stats.total_tokens / max(session_duration, 1), 2),
                "api_calls_saved": self.stats.invalid_format + self.stats.excluded_tokens + self.stats.duplicates_filtered
            }
        }
    
    def add_exclusion_token(self, token_address: str, reason: str = "manual"):
        """Add a token to the exclusion list"""
        self.excluded_tokens.add(token_address)
        self.logger.info(f"🚫 Added token {token_address} to exclusion list (reason: {reason})")
    
    def remove_exclusion_token(self, token_address: str):
        """Remove a token from the exclusion list"""
        if token_address in self.excluded_tokens:
            self.excluded_tokens.remove(token_address)
            self.logger.info(f"✅ Removed token {token_address} from exclusion list")
        else:
            self.logger.warning(f"⚠️  Token {token_address} not found in exclusion list")
    
    def is_likely_spam_token(self, metadata: Dict[str, Any]) -> bool:
        """
        Detect likely spam/scam tokens based on metadata patterns
        
        Args:
            metadata: Token metadata from API
            
        Returns:
            True if token appears to be spam/scam
        """
        if not metadata:
            return False
            
        # Check for suspicious patterns
        name = metadata.get('name', '').lower()
        symbol = metadata.get('symbol', '').lower()
        
        spam_indicators = [
            # Common spam patterns
            'test', 'fake', 'scam', 'rug', 'pump', 'moon',
            # Impersonation attempts
            'bitcoin', 'ethereum', 'solana', 'usdc', 'usdt',
            # Obvious spam
            '🚀', '💎', 'xxx', 'sex', 'porn'
        ]
        
        for indicator in spam_indicators:
            if indicator in name or indicator in symbol:
                return True
                
        # Check for suspicious total supply (too high or too low)
        total_supply = metadata.get('total_supply', 0)
        if total_supply > 1e15 or (total_supply > 0 and total_supply < 1000):
            return True
            
        return False
    
    def get_pre_validation_report(self, token_addresses: List[str]) -> Dict[str, Any]:
        """
        Generate a pre-validation report to show what would be filtered
        without actually filtering tokens
        """
        if not token_addresses:
            return {"error": "No token addresses provided"}
            
        report = {
            "input_analysis": {
                "total_addresses": len(token_addresses),
                "unique_addresses": len(set(token_addresses)),
                "duplicates": len(token_addresses) - len(set(token_addresses))
            },
            "format_analysis": {
                "valid_solana_format": 0,
                "invalid_format": 0,
                "ethereum_addresses": 0
            },
            "exclusion_analysis": {
                "major_tokens": 0,
                "stablecoins": 0,
                "total_excluded": 0
            },
            "estimated_api_calls_saved": 0
        }
        
        unique_addresses = set(token_addresses)
        
        for address in unique_addresses:
            # Format analysis
            if self._is_valid_solana_address(address):
                report["format_analysis"]["valid_solana_format"] += 1
            else:
                report["format_analysis"]["invalid_format"] += 1
                if self.ethereum_address_pattern.match(address):
                    report["format_analysis"]["ethereum_addresses"] += 1
            
            # Exclusion analysis
            if address in self.major_tokens:
                report["exclusion_analysis"]["major_tokens"] += 1
            elif address in self.stablecoins:
                report["exclusion_analysis"]["stablecoins"] += 1
            
            if address in self.excluded_tokens:
                report["exclusion_analysis"]["total_excluded"] += 1
        
        # Calculate potential API call savings
        calls_saved = (report["input_analysis"]["duplicates"] + 
                      report["format_analysis"]["invalid_format"] + 
                      report["exclusion_analysis"]["total_excluded"])
        report["estimated_api_calls_saved"] = calls_saved
        
        return report

# Factory function for easy initialization
def create_token_validator(logger: Optional[logging.Logger] = None) -> EnhancedTokenValidator:
    """Create and return a configured token validator instance"""
    return EnhancedTokenValidator(logger=logger)