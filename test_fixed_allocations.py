#!/usr/bin/env python3
"""
Test Fixed Asset Allocation

This script tests the fixed optimization algorithm to verify that VTIAX, VWO, 
and VNQ now receive meaningful allocations.
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from src.optimization.portfolio_optimizer import (
    PortfolioOptimizer, PortfolioRequest, AccountType
)

def test_fixed_allocations():
    """Test the fixed asset allocation constraints"""
    
    print("🔧 TESTING: Fixed Asset Allocation Constraints")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = PortfolioOptimizer()
    
    # Create test request
    request = PortfolioRequest(
        current_savings=100000.0,
        target_amount=500000.0,
        time_horizon=10,
        account_type=AccountType.TAXABLE
    )
    
    print(f"Test Request:")
    print(f"- Current Savings: ${request.current_savings:,.0f}")
    print(f"- Target Amount: ${request.target_amount:,.0f}")
    print(f"- Time Horizon: {request.time_horizon} years")
    print(f"- Account Type: {request.account_type.value}")
    print()
    
    # Test minimum allocation constraints
    print("📊 STEP 1: Testing Minimum Allocation Constraints")
    print("-" * 50)
    
    from src.optimization.portfolio_optimizer import StrategyType
    
    strategies = [StrategyType.CONSERVATIVE, StrategyType.BALANCED, StrategyType.AGGRESSIVE]
    
    for strategy in strategies:
        min_allocations = optimizer._get_minimum_allocations(strategy, request)
        print(f"\n{strategy.value.upper()} Minimum Allocations:")
        for asset, min_pct in min_allocations.items():
            print(f"  {asset:6}: {min_pct:5.1%}")
    
    print()
    
    # Test optimized portfolios with fixes
    print("🎯 STEP 2: Testing Fixed Optimization Results")
    print("-" * 50)
    
    try:
        # Get historical data
        historical_data = optimizer._get_historical_data(request.time_horizon)
        returns_stats = optimizer._calculate_returns_statistics(historical_data)
        
        # Test each strategy
        for strategy_name in ['conservative', 'balanced', 'aggressive']:
            print(f"\n{strategy_name.upper()} STRATEGY (FIXED):")
            print("-" * 35)
            
            try:
                if strategy_name == 'conservative':
                    portfolio = optimizer._optimize_conservative(returns_stats, request)
                elif strategy_name == 'balanced':
                    portfolio = optimizer._optimize_balanced(returns_stats, request)
                else:
                    portfolio = optimizer._optimize_aggressive(returns_stats, request)
                
                print(f"Expected Return: {portfolio.expected_return:7.2%}")
                print(f"Volatility:      {portfolio.expected_volatility:7.2%}")
                print(f"Sharpe Ratio:    {portfolio.sharpe_ratio:7.2f}")
                print()
                
                print("Asset Allocations:")
                total_allocation = 0
                problem_assets = []
                fixed_assets = []
                
                for asset, weight in portfolio.allocation.items():
                    total_allocation += weight
                    print(f"  {asset:6}: {weight:7.2%}")
                    
                    # Flag problem assets (still near zero)
                    if weight < 0.01:  # Less than 1%
                        problem_assets.append(asset)
                    elif weight >= 0.02:  # 2% or more - good diversification
                        fixed_assets.append(asset)
                
                print(f"\nTotal Allocation: {total_allocation:7.2%}")
                
                if problem_assets:
                    print(f"⚠️  STILL PROBLEMATIC (< 1%): {', '.join(problem_assets)}")
                else:
                    print("✅ All assets have meaningful allocations")
                
                if fixed_assets:
                    print(f"✅ DIVERSIFIED ASSETS (≥ 2%): {', '.join(fixed_assets)}")
                    
            except Exception as e:
                print(f"❌ ERROR optimizing {strategy_name}: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"❌ ERROR in optimization testing: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n💡 COMPARISON SUMMARY:")
    print("-" * 40)
    print("Expected Improvements:")
    print("• VTIAX: Should be ≥ 3-8% (was 0%)")
    print("• VWO: Should be ≥ 2-3% (was 0%)")  
    print("• VNQ: Should be ≥ 3-5% (was 0%)")
    print("• All assets should have meaningful allocation")
    print("• Diversification across asset classes preserved")
    print("• Return/risk metrics should remain competitive")

if __name__ == "__main__":
    test_fixed_allocations()
