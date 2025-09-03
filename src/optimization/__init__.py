"""
Portfolio Optimization Engine - Sprint 3

This module provides comprehensive portfolio optimization with:
- Three core strategies: Conservative, Balanced, Aggressive  
- Automatic rebalancing strategy recommendations
- New money vs traditional rebalancing analysis
- Target achievement probability analysis
- Integration with existing analytics engines

Author: Sprint 3 Development
Created: August 2025
"""

from .portfolio_optimizer import (
    PortfolioOptimizer, PortfolioRequest, AccountType, StrategyType,
    OptimizedPortfolio, OptimizationResult
)

__all__ = [
    'PortfolioOptimizer',
    'PortfolioRequest', 
    'AccountType',
    'StrategyType',
    'OptimizedPortfolio',
    'OptimizationResult'
]
