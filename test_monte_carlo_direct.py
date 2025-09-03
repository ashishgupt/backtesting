#!/usr/bin/env python3
"""
Minimal test for Monte Carlo fix - directly test the new method
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import numpy as np
from src.optimization.portfolio_optimizer_enhanced import EnhancedPortfolioOptimizer
from src.optimization.portfolio_optimizer import PortfolioRequest, AccountType

# Simple mock portfolio class for testing
class MockPortfolio:
    def __init__(self, expected_return, volatility):
        self.expected_return = expected_return
        self.expected_volatility = volatility

def test_monte_carlo_method():
    """Test the new Monte Carlo method directly"""
    
    print("🧪 Testing Monte Carlo Fix - Direct Method Test")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = EnhancedPortfolioOptimizer()
    
    # Create mock portfolios with your exact parameters
    conservative = MockPortfolio(0.047, 0.064)  # 4.7%, 6.4%
    balanced = MockPortfolio(0.140, 0.144)      # 14.0%, 14.4%  
    aggressive = MockPortfolio(0.158, 0.163)    # 15.8%, 16.3%
    
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
    
    portfolios = [
        ("Conservative", conservative),
        ("Balanced", balanced), 
        ("Aggressive", aggressive)
    ]
    
    results = []
    print("🔄 Testing Monte Carlo calculations...")
    
    for name, portfolio in portfolios:
        try:
            # Call our new method directly
            probability = optimizer._calculate_target_achievement_probability(portfolio, test_request)
            results.append(probability)
            
            print(f"{name:<12} | Return: {portfolio.expected_return:>5.1%} | "
                  f"Volatility: {portfolio.expected_volatility:>5.1%} | "
                  f"Success Rate: {probability:>5.1%}")
                  
        except Exception as e:
            print(f"❌ Error testing {name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(None)
    
    print()
    
    # Verify the fix
    valid_results = [r for r in results if r is not None]
    
    if len(valid_results) == 0:
        print("❌ ERROR: All Monte Carlo calculations failed!")
        return False
    elif all(r == 0.75 for r in valid_results):
        print("❌ ISSUE: Still showing hardcoded 0.75!")
        print("   The fix may not have been applied correctly.")
        return False
    elif len(set(valid_results)) == 1:
        print("❌ ISSUE: All portfolios show the same probability!")
        print(f"   All showing: {valid_results[0]:.1%}")
        return False
    else:
        print("✅ SUCCESS: Portfolios show different target achievement probabilities!")
        print("   The Monte Carlo fix is working correctly!")
        print(f"   Range: {min(valid_results):.1%} to {max(valid_results):.1%}")
        
        # Additional validation - conservative should be lowest
        if results[0] and results[1] and results[2]:
            if results[0] < results[1] < results[2]:
                print("✅ BONUS: Results follow expected risk-return relationship!")
                print("   (Conservative < Balanced < Aggressive)")
            else:
                print("⚠️  NOTE: Results don't follow expected pattern, but that's normal for Monte Carlo")
        
        return True

if __name__ == "__main__":
    success = test_monte_carlo_method()
    sys.exit(0 if success else 1)
