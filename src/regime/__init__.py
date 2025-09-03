"""
Market Regime Awareness Module

This module provides comprehensive market regime detection and analysis capabilities
for the portfolio backtesting system. It identifies different market environments
and helps optimize portfolio strategies based on prevailing conditions.

Components:
- Market Regime Detection Engine
- Regime-Aware Strategy Recommendations
- Historical Regime Analysis
- Performance Attribution by Market Regime
"""

from .regime_detector import MarketRegimeDetector
from .regime_analyzer import RegimeAwareAnalyzer
from .regime_indicators import RegimeIndicatorCalculator

__all__ = [
    'MarketRegimeDetector',
    'RegimeAwareAnalyzer', 
    'RegimeIndicatorCalculator'
]
