#!/usr/bin/env python3
"""
Simple test script to verify the Monte Carlo target achievement fix
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

from src.optimization.portfolio_optimizer_enhanced import EnhancedPortfolioOptimizer
from src.optimization.portfolio_optimizer import PortfolioRequest, AccountType, OptimizedPortfolio, StrategyType

def test_monte_carlo_directly():
    """Test the Monte Carlo calculation directly"""
    
    print("🧪 Testing Monte Carlo Target Achievement Fix")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = EnhancedPortfolioOptimizer()
    
    # Create test portfolios with the parameters from your image
    conservative = OptimizedPortfolio(
        strategy=StrategyType.CONSERVATIVE,
        allocation={'VTI': 0.6, 'BND': 0.4},  # Simple allocation
        expected_return=0.047,  # 4.7%
        expected_volatility=0.064,  # 6.4%
        sharpe_ratio=0.27,
        max_drawdown=0.1,
        optimal_rebalancing='annual'
    )
    
    balanced = OptimizedPortfolio(
        strategy=StrategyType.BALANCED,
        allocation={'VTI': 0.7, 'VTIAX': 0.3},
        expected_return=0.140,  # 14.0%
        expected_volatility=0.144,  # 14.4%
        sharpe_ratio=0.77,
        max_drawdown=0.2,
        optimal_rebalancing='annual'
    )
    
    aggressive = OptimizedPortfolio(
        strategy=StrategyType.AGGRESSIVE,
        allocation={'VTI': 0.8, 'VNQ': 0.2},
        expected_return=0.158,  # 15.8%
        expected_volatility=0.163,  # 16.3%
        sharpe_ratio=0.79,
        max_drawdown=0.3,
        optimal_rebalancing='annual'
    )
    
    # Test request
    test_request = PortfolioRequest(
        current_savings=100000,  # $100k starting
        target_amount=500000,    # $500k target  
        time_horizon=20,         # 20 years
        account_type=AccountType.TAX_DEFERRED
    )
    
    print(f"📊 Test Scenario:")
    print(f"   Current Savings: ${test_request.current_savings:,}")
    print(f"   Target Amount: ${test_request.target_amount:,}")
    print(f"   Time Horizon: {test_request.time_horizon} years")
    print()
    
    portfolios = [conservative, balanced, aggressive]
    results = []
    
    print("🔄 Testing Monte Carlo calculations...")
    
    for portfolio in portfolios:
        try:
            probability = optimizer._calculate_target_achievement_probability(portfolio, test_request)
            results.append(probability)
            
            print(f"{portfolio.strategy.value.upper():<12} | Return: {portfolio.expected_return:>5.1%} | "
                  f"Volatility: {portfolio.expected_volatility:>5.1%} | "
                  f"Success Rate: {probability:>5.1%}")
                  
        except Exception as e:
            print(f"❌ Error testing {portfolio.strategy.value}: {str(e)}")
            results.append(None)
    
    print()
    
    # Check if the fix worked
    valid_results = [r for r in results if r is not None]
    
    if len(valid_results) == 0:
        print("❌ ERROR: All Monte Carlo calculations failed!")
        return False
    elif len(set(valid_results)) == 1:
        print("❌ ISSUE: All portfolios still show the same probability!")
        print(f"   All showing: {valid_results[0]:.1%}")
        print("   This suggests the hardcoded 0.75 is still being used somehow.")
        return False
    else:
        print("✅ SUCCESS: Portfolios show different target achievement probabilities!")
        print("   The Monte Carlo fix is working correctly.")
        print(f"   Range: {min(valid_results):.1%} to {max(valid_results):.1%}")
        return True

if __name__ == "__main__":
    success = test_monte_carlo_directly()
    sys.exit(0 if success else 1)
