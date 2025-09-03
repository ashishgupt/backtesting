#!/usr/bin/env python3
"""
Debug Asset Allocation Issue

This script investigates why VTIAX, VWO, and VNQ are getting near-zero allocations
in the optimization results.
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from src.optimization.portfolio_optimizer import (
    PortfolioOptimizer, PortfolioRequest, AccountType
)

def debug_allocation_issue():
    """Debug the asset allocation imbalance issue"""
    
    print("🔍 DEBUG: Asset Allocation Issue Investigation")
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
    
    print(f"Request Details:")
    print(f"- Current Savings: ${request.current_savings:,.0f}")
    print(f"- Target Amount: ${request.target_amount:,.0f}")
    print(f"- Time Horizon: {request.time_horizon} years")
    print(f"- Account Type: {request.account_type.value}")
    print()
    
    # Get historical data and statistics
    print("📊 STEP 1: Analyzing Historical Data")
    print("-" * 40)
    
    try:
        historical_data = optimizer._get_historical_data(request.time_horizon)
        print(f"Historical data loaded: {len(historical_data)} records")
        print(f"Date range: {historical_data['Date'].min()} to {historical_data['Date'].max()}")
        print(f"Assets included: {sorted(historical_data['Symbol'].unique())}")
        print()
        
        # Calculate returns statistics
        returns_stats = optimizer._calculate_returns_statistics(historical_data)
        
        print("Expected Annual Returns:")
        for asset in optimizer.assets:
            if asset in returns_stats['expected_returns'].index:
                ret = returns_stats['expected_returns'][asset]
                vol = returns_stats['volatility'][asset] 
                print(f"  {asset:6}: {ret:7.2%} return, {vol:7.2%} volatility")
            else:
                print(f"  {asset:6}: MISSING DATA")
        print()
        
        print("Correlation Matrix:")
        corr_matrix = returns_stats['correlation_matrix']
        print(corr_matrix.round(3))
        print()
        
    except Exception as e:
        print(f"❌ ERROR loading historical data: {e}")
        return
    
    # Test each optimization strategy
    print("🎯 STEP 2: Testing Optimization Strategies")
    print("-" * 40)
    
    strategies = ['conservative', 'balanced', 'aggressive']
    
    for strategy_name in strategies:
        print(f"\n{strategy_name.upper()} STRATEGY:")
        print("-" * 30)
        
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
            
            for asset, weight in portfolio.allocation.items():
                total_allocation += weight
                print(f"  {asset:6}: {weight:7.2%}")
                
                # Flag problem assets (near zero allocation)
                if weight < 0.01:  # Less than 1%
                    problem_assets.append(asset)
            
            print(f"\nTotal Allocation: {total_allocation:7.2%}")
            
            if problem_assets:
                print(f"⚠️  PROBLEM ASSETS (< 1%): {', '.join(problem_assets)}")
            else:
                print("✅ All assets have meaningful allocations")
                
        except Exception as e:
            print(f"❌ ERROR optimizing {strategy_name}: {e}")
    
    # Analyze constraints and bounds
    print("\n🔧 STEP 3: Analyzing Optimization Constraints")
    print("-" * 40)
    
    print("Asset Universe and Bounds Analysis:")
    print("(Based on current optimization code)")
    print()
    
    # Conservative bounds
    print("CONSERVATIVE Strategy Bounds:")
    assets_info = [
        ("VTI", "0.0% - 25.0%", "US Total Market"),
        ("VTIAX", "0.0% - 25.0%", "International Developed"), 
        ("BND", "25.0% - 60.0%", "US Bonds (Required minimum)"),
        ("VNQ", "0.0% - 25.0%", "US Real Estate"),
        ("GLD", "0.0% - 10.0%", "Gold (Limited alternative)"),
        ("VWO", "0.0% - 25.0%", "Emerging Markets"),
        ("QQQ", "0.0% - 25.0%", "Technology Growth")
    ]
    
    for asset, bounds, description in assets_info:
        print(f"  {asset:6}: {bounds:12} ({description})")
    print()
    
    # Balanced bounds  
    print("BALANCED Strategy Bounds (10+ year horizon):")
    balanced_info = [
        ("VTI", "0.0% - 50.0%", "US Total Market"),
        ("VTIAX", "0.0% - 30.0%", "International Developed"),
        ("BND", "8.0% - 28.0%", "US Bonds"),
        ("VNQ", "0.0% - 30.0%", "US Real Estate"), 
        ("GLD", "0.0% - 20.0%", "Gold"),
        ("VWO", "0.0% - 20.0%", "Emerging Markets"),
        ("QQQ", "0.0% - 50.0%", "Technology Growth")
    ]
    
    for asset, bounds, description in balanced_info:
        print(f"  {asset:6}: {bounds:12} ({description})")
    print()
    
    print("💡 ANALYSIS SUMMARY:")
    print("-" * 40)
    print("Potential Issues Identified:")
    print("1. No minimum allocation constraints for diversification assets")
    print("2. VWO (Emerging Markets) capped at 20% vs 25% for other equities")
    print("3. VTIAX (International) capped at 30% vs 50% for domestic")
    print("4. VNQ bounds vary by strategy but no minimum floor")
    print("5. Optimization may favor domestic assets due to higher expected returns")
    print()
    print("Recommendations:")
    print("1. Add minimum allocation constraints (e.g., 2-5% each)")
    print("2. Review if international/EM assets have poor risk-adjusted returns")
    print("3. Consider correlation benefits in objective function")
    print("4. Test with equal bounds across similar asset classes")

if __name__ == "__main__":
    debug_allocation_issue()
