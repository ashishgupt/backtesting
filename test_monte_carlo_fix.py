#!/usr/bin/env python3
"""
Test script to verify the Monte Carlo target achievement fix
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

from src.optimization.portfolio_optimizer_enhanced import EnhancedPortfolioOptimizer
from src.optimization.portfolio_optimizer import PortfolioRequest, AccountType

def test_monte_carlo_fix():
    """Test that the three portfolios now show different target achievement probabilities"""
    
    print("🧪 Testing Monte Carlo Target Achievement Fix")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = EnhancedPortfolioOptimizer()
    
    # Create test request that should show clear differences between strategies
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
    print(f"   Account Type: {test_request.account_type.value}")
    print()
    
    try:
        # Run enhanced optimization
        print("🔄 Running enhanced portfolio optimization...")
        result = optimizer.optimize_enhanced_portfolio(test_request)
        
        print("✅ Optimization completed successfully!")
        print()
        
        # Display results
        print("📈 TARGET ACHIEVEMENT RESULTS:")
        print("-" * 40)
        
        for portfolio in result.portfolios:
            strategy = portfolio.strategy
            expected_return = portfolio.expected_return
            volatility = portfolio.volatility
            target_prob = portfolio.target_achievement_probability
            
            print(f"{strategy.upper():<12} | Return: {expected_return:>5.1%} | "
                  f"Volatility: {volatility:>5.1%} | "
                  f"Success Rate: {target_prob:>5.1%}" if target_prob else "Success Rate: None")
        
        print()
        
        # Verify the fix worked
        probabilities = [p.target_achievement_probability for p in result.portfolios if p.target_achievement_probability is not None]
        
        if len(set(probabilities)) == 1:
            print("❌ ISSUE: All portfolios still show the same probability!")
            print(f"   All showing: {probabilities[0]:.1%}")
            return False
        else:
            print("✅ SUCCESS: Portfolios show different target achievement probabilities!")
            print("   The Monte Carlo fix is working correctly.")
            return True
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_monte_carlo_fix()
    sys.exit(0 if success else 1)
