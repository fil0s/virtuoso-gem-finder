#!/usr/bin/env python3
"""
Virtuoso Gem Hunter - High-performance token detection system for Solana

A sophisticated gem hunting system that reduces API calls by 75-85% while maintaining
or improving analysis quality through advanced optimization techniques.
"""

__version__ = "1.0.0"
__author__ = "Virtuoso Trading Systems"
__email__ = "dev@virtuoso-trading.com"

# Available modules
from .detectors.early_gem_detector import EarlyGemDetector
from .scoring.early_gem_focused_scoring import EarlyGemFocusedScoring

__all__ = [
    "EarlyGemDetector",
    "EarlyGemFocusedScoring",
    "__version__",
]
