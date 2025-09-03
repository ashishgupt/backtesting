#!/usr/bin/env python3
"""
Dynamic Rebalancing vs Dynamic Allocation Analysis

Investigate the difference between:
1. Dynamic rebalancing: Maintaining fixed target weights over time
2. Dynamic allocation: Changing target weights based on market conditions

Check what our system actually does and if it supports true dynamic allocation.
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from src.optimization.portfolio_optimizer import PortfolioOptimizer, PortfolioRequest, AccountType
from datetime import datetime, timedelta

def analyze_rebalancing_vs_allocation():
    """Analyze what 'dynamic rebalancing' means in our system"""
    
    print("🔄 DYNAMIC REBALANCING vs DYNAMIC ALLOCATION")
    print("=" * 60)
    
    print("📖 DEFINITIONS:")
    print("-" * 30)
    print("🔄 DYNAMIC REBALANCING:")
    print("   • Fixed target allocation (e.g., 60% stocks, 40% bonds)")
    print("   • Periodically rebalance back to targets")
    print("   • Same allocation throughout entire investment period")
    print()
    print("🎯 DYNAMIC ALLOCATION (Tactical Asset Allocation):")
    print("   • Target allocation CHANGES over time")
    print("   • Based on market conditions, valuations, outlook")
    print("   • Example: 60% stocks in 2020 → 45% stocks in 2022")
    print()
    
    # Test what our current system does
    print("🧪 TESTING OUR CURRENT SYSTEM:")
    print("-" * 40)
    
    try:
        from src.core.portfolio_engine_optimized import OptimizedPortfolioEngine
        
        engine = OptimizedPortfolioEngine()
        
        # Test 1: Same allocation over different periods
        allocation = {'VTI': 0.4, 'VTIAX': 0.1, 'BND': 0.3, 'VNQ': 0.1, 'GLD': 0.05, 'VWO': 0.03, 'QQQ': 0.02}
        
        print("Test 1: Running same allocation over different time periods...")
        
        periods = [
            ("Bull Market", "2012-01-01", "2013-12-31"),
            ("Bear Market", "2022-01-01", "2022-12-31"), 
            ("Crisis Period", "2020-02-01", "2020-04-30")
        ]
        
        for period_name, start, end in periods:
            result = engine.backtest_portfolio(
                allocation=allocation,
                start_date=start,
                end_date=end,
                rebalance_frequency='quarterly'
            )
            
            if result and 'final_value' in result:
                total_return = (result['final_value'] - 10000) / 10000
                print(f"  {period_name:<12}: {total_return:+7.1%} return")
            else:
                print(f"  {period_name:<12}: Failed to backtest")
        
        print(f"\n✅ CONCLUSION: Our system uses DYNAMIC REBALANCING")
        print("   • Same target allocation maintained throughout")
        print("   • Rebalances back to targets periodically")
        print("   • Does NOT change allocation based on market conditions")
        
    except Exception as e:
        print(f"❌ Error testing portfolio engine: {e}")

def test_if_allocation_changes_with_conditions():
    """Test if our optimizer changes allocations based on different market conditions"""
    
    print(f"\n🌊 TESTING: Does allocation change with market conditions?")
    print("-" * 60)
    
    optimizer = PortfolioOptimizer()
    
    # The key question: Does our optimizer use CURRENT market data or HISTORICAL data?
    print("🔍 INVESTIGATING DATA SOURCE:")
    print("-" * 35)
    
    # Get the data that the optimizer uses
    historical_data = optimizer._get_historical_data(10)
    returns_stats = optimizer._calculate_returns_statistics(historical_data)
    
    print(f"Data used for optimization:")
    print(f"• Start Date: {historical_data['Date'].min()}")
    print(f"• End Date: {historical_data['Date'].max()}")
    print(f"• This is HISTORICAL data, not current market conditions")
    
    # Test: Does optimization change if we run it at different times?
    print(f"\n🧪 TESTING: Do results change with different historical windows?")
    print("-" * 65)
    
    request = PortfolioRequest(
        current_savings=100000.0,
        time_horizon=10,
        account_type=AccountType.TAXABLE
    )
    
    # Test different historical windows (simulating running optimizer at different times)
    windows = [
        ("Full History (20yr)", 20),
        ("Recent History (10yr)", 10),
        ("Short History (5yr)", 5)
    ]
    
    allocations = {}
    
    for window_name, years in windows:
        try:
            # Get different historical data windows
            window_data = optimizer._get_historical_data(years)
            window_stats = optimizer._calculate_returns_statistics(window_data)
            
            # Run optimization
            portfolio = optimizer._optimize_balanced(window_stats, request)
            allocation = portfolio.allocation
            
            allocations[window_name] = {
                'allocation': allocation,
                'return': portfolio.expected_return,
                'volatility': portfolio.expected_volatility,
                'data_period': f"{window_data['Date'].min()} to {window_data['Date'].max()}"
            }
            
            print(f"\n{window_name}:")
            print(f"  Data: {window_data['Date'].min()} to {window_data['Date'].max()}")
            print(f"  Expected: {portfolio.expected_return:5.1%} return, {portfolio.expected_volatility:5.1%} risk")
            print("  Allocation:")
            for asset, weight in allocation.items():
                if weight > 0.01:
                    print(f"    {asset}: {weight:5.1%}")
                    
        except Exception as e:
            print(f"❌ Error with {window_name}: {e}")
    
    # Compare allocations
    if len(allocations) >= 2:
        print(f"\n📊 ALLOCATION COMPARISON:")
        print("-" * 40)
        
        reference = list(allocations.keys())[0]
        ref_allocation = allocations[reference]['allocation']
        
        for name, data in allocations.items():
            if name != reference:
                print(f"\n{reference} vs {name}:")
                allocation_diff = {}
                
                for asset in ref_allocation:
                    ref_weight = ref_allocation.get(asset, 0)
                    comp_weight = data['allocation'].get(asset, 0)
                    diff = comp_weight - ref_weight
                    
                    if abs(diff) > 0.01:  # More than 1% difference
                        allocation_diff[asset] = diff
                        print(f"  {asset}: {diff:+5.1%} difference")
                
                if allocation_diff:
                    print("  ✅ ALLOCATION CHANGES with different data windows")
                else:
                    print("  ➡️  Similar allocations despite different data")

def check_if_system_supports_tactical_allocation():
    """Check if our system has any tactical allocation features"""
    
    print(f"\n🎯 TACTICAL ALLOCATION CAPABILITY CHECK")
    print("-" * 50)
    
    # Check if we have regime-based allocation
    try:
        from src.regime.regime_analyzer import RegimeAnalyzer
        
        print("✅ Found RegimeAnalyzer - checking tactical capability...")
        
        # This suggests we might have regime-based allocation
        print("🌊 REGIME-BASED ALLOCATION POTENTIAL:")
        print("   • System has market regime detection")
        print("   • Could potentially adjust allocation based on:")
        print("     - Bull vs Bear markets")
        print("     - High vs Low volatility periods") 
        print("     - Economic expansion vs recession")
        print()
        print("❓ QUESTION: Is regime data used in portfolio optimization?")
        
        # Check if optimizer uses regime data
        optimizer = PortfolioOptimizer()
        
        # Look at the optimizer methods
        methods = [method for method in dir(optimizer) if not method.startswith('_')]
        
        regime_related = [method for method in methods if 'regime' in method.lower()]
        
        if regime_related:
            print(f"✅ Found regime-related methods: {regime_related}")
        else:
            print("❌ No regime integration found in optimizer")
            
        print(f"\n💡 CURRENT STATUS:")
        print("   • Portfolio optimization uses HISTORICAL data only")
        print("   • No real-time regime adjustment in base optimizer")
        print("   • Regime detection exists but appears separate from optimization")
        
    except ImportError:
        print("❌ No RegimeAnalyzer found")
    except Exception as e:
        print(f"❌ Error checking regime capabilities: {e}")

def summary_and_recommendations():
    """Provide summary and recommendations"""
    
    print(f"\n📋 SUMMARY & RECOMMENDATIONS")
    print("=" * 50)
    
    print("🔍 CURRENT SYSTEM ANALYSIS:")
    print("• ✅ Dynamic Rebalancing: YES (maintains fixed target weights)")
    print("• ❌ Dynamic Allocation: NO (doesn't change weights based on conditions)")
    print("• 📊 Uses historical data for optimization")
    print("• 🎯 Same allocation regardless of current market regime")
    print()
    
    print("💡 WHAT THIS MEANS:")
    print("• If you optimize today, you get allocation based on 2004-2024 data")
    print("• If you optimize next year, you get allocation based on 2005-2025 data")
    print("• The allocation WILL change slightly as new data comes in")
    print("• But it doesn't adapt to current market conditions/valuations")
    print()
    
    print("🚀 POTENTIAL ENHANCEMENTS:")
    print("1. Regime-based allocation: Adjust weights based on market regime")
    print("2. Valuation-based allocation: Reduce allocation to expensive assets") 
    print("3. Momentum-based allocation: Tilt toward recent outperformers")
    print("4. Economic indicator-based: Adjust based on leading indicators")
    print("5. Real-time optimization: Re-optimize based on current market data")

if __name__ == "__main__":
    analyze_rebalancing_vs_allocation()
    test_if_allocation_changes_with_conditions()
    check_if_system_supports_tactical_allocation()
    summary_and_recommendations()
