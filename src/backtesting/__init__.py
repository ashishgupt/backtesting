"""
Backtesting Module for Portfolio Optimization

This module provides comprehensive backtesting capabilities including:
- Walk-forward validation
- Out-of-sample testing
- Performance degradation analysis
- Strategy comparison and ranking
"""

from .walk_forward_validator import (
    WalkForwardValidator,
    ValidationWindow,
    ValidationResult
)

__all__ = [
    'WalkForwardValidator',
    'ValidationWindow', 
    'ValidationResult'
]
