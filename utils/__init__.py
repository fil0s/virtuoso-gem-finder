#!/usr/bin/env python3
"""
Utility modules for Virtuoso Gem Hunter
"""

from .error_recovery import (
    get_error_recovery_manager,
    with_error_recovery,
    create_recovery_strategy,
    SpecificErrorHandlers
)
from .exceptions import (
    VirtuosoError,
    APIError,
    APIConnectionError,
    APIDataError,
    ConfigurationError,
    DatabaseError
)

__all__ = [
    "get_error_recovery_manager",
    "with_error_recovery", 
    "create_recovery_strategy",
    "SpecificErrorHandlers",
    "VirtuosoError",
    "APIError",
    "APIConnectionError",
    "APIDataError",
    "ConfigurationError",
    "DatabaseError",
]
