#!/usr/bin/env python3
"""
Historical Performance Analysis - Crisis Period Investigation

This script analyzes the performance of VTIAX, VWO, and VNQ during specific periods,
particularly the 2004-2009 timeframe and other crisis periods to understand if
these assets provide crisis protection benefits that justify inclusion.
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from src.optimization.portfolio_optimizer import PortfolioOptimizer
from datetime import datetime, date

def analyze_crisis_performance():
    """Analyze performance during specific crisis periods"""
    
    print("📊 CRISIS PERIOD PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    # Initialize optimizer to get data access
    optimizer = PortfolioOptimizer()
    
    # Get full historical data
    print("Loading historical data...")
    historical_data = optimizer._get_historical_data(20)  # Full 20 years
    returns_stats = optimizer._calculate_returns_statistics(historical_data)
    
    # Get daily returns for analysis
    daily_returns = returns_stats['returns']
    
    print(f"Data Range: {daily_returns.index.min()} to {daily_returns.index.max()}")
    print(f"Assets: {list(daily_returns.columns)}")
    print()
    
    # Define crisis periods
    crisis_periods = [
        {
            'name': '2004-2009 (Including Financial Crisis)',
            'start': datetime(2004, 1, 1),
            'end': datetime(2009, 12, 31),
            'description': 'Full period including build-up and financial crisis'
        },
        {
            'name': '2007-2009 Financial Crisis',
            'start': datetime(2007, 10, 1),  # Market peak
            'end': datetime(2009, 3, 31),    # Market bottom + recovery start
            'description': 'Peak-to-trough financial crisis period'
        },
        {
            'name': '2008 Crisis Year',
            'start': datetime(2008, 1, 1),
            'end': datetime(2008, 12, 31),
            'description': 'Worst year of financial crisis'
        },
        {
            'name': '2020 COVID Pandemic',
            'start': datetime(2020, 2, 19),
            'end': datetime(2020, 3, 23),
            'description': 'COVID market crash'
        },
        {
            'name': '2022 Bear Market',
            'start': datetime(2022, 1, 3),
            'end': datetime(2022, 10, 12),
            'description': 'Inflation/rate hike bear market'
        }
    ]
    
    # Analyze each crisis period
    for period in crisis_periods:
        print(f"\n🔍 {period['name']}")
        print("-" * 50)
        print(f"Period: {period['start'].strftime('%Y-%m-%d')} to {period['end'].strftime('%Y-%m-%d')}")
        print(f"Description: {period['description']}")
        print()
        
        # Filter data for this period
        period_start = pd.Timestamp(period['start'])
        period_end = pd.Timestamp(period['end'])
        
        period_returns = daily_returns[
            (daily_returns.index >= period_start) & 
            (daily_returns.index <= period_end)
        ]
        
        if len(period_returns) < 10:  # Skip if insufficient data
            print("❌ Insufficient data for this period")
            continue
            
        # Calculate performance metrics for each asset
        results = []
        
        for asset in optimizer.assets:
            if asset in period_returns.columns:
                asset_returns = period_returns[asset].dropna()
                
                if len(asset_returns) > 0:
                    # Calculate metrics
                    total_return = (1 + asset_returns).prod() - 1
                    annualized_return = ((1 + total_return) ** (252 / len(asset_returns))) - 1
                    volatility = asset_returns.std() * np.sqrt(252)
                    
                    # Calculate maximum drawdown
                    cumulative = (1 + asset_returns).cumprod()
                    peak = cumulative.expanding().max()
                    drawdown = (cumulative / peak - 1)
                    max_drawdown = drawdown.min()
                    
                    # Sharpe ratio (using 0% risk-free rate for crisis periods)
                    sharpe = annualized_return / volatility if volatility > 0 else 0
                    
                    results.append({
                        'Asset': asset,
                        'Total Return': total_return,
                        'Annualized Return': annualized_return,
                        'Volatility': volatility,
                        'Max Drawdown': max_drawdown,
                        'Sharpe Ratio': sharpe
                    })
        
        # Sort by total return (best to worst)
        results.sort(key=lambda x: x['Total Return'], reverse=True)
        
        print("Performance Ranking (Best to Worst):")
        print(f"{'Asset':<6} {'Total Ret':<10} {'Ann. Ret':<10} {'Volatility':<10} {'Max DD':<10} {'Sharpe':<8}")
        print("-" * 65)
        
        for r in results:
            print(f"{r['Asset']:<6} {r['Total Return']:>8.1%} {r['Annualized Return']:>8.1%} "
                  f"{r['Volatility']:>8.1%} {r['Max Drawdown']:>8.1%} {r['Sharpe Ratio']:>6.2f}")
        
        # Highlight our "problem" assets
        problem_assets = ['VTIAX', 'VWO', 'VNQ']
        problem_ranks = {}
        
        for i, r in enumerate(results):
            if r['Asset'] in problem_assets:
                problem_ranks[r['Asset']] = i + 1
                
        print(f"\n📍 Problem Asset Rankings (out of {len(results)}):")
        for asset in problem_assets:
            if asset in problem_ranks:
                rank = problem_ranks[asset]
                if rank <= 3:
                    status = "✅ TOP PERFORMER"
                elif rank <= len(results) // 2:
                    status = "🟡 ABOVE AVERAGE"
                else:
                    status = "❌ BELOW AVERAGE"
                print(f"  {asset}: #{rank} - {status}")
            else:
                print(f"  {asset}: No data")

def analyze_glide_path_capability():
    """Analyze if our engine handles dynamic allocation based on timeline"""
    
    print("\n\n🛤️ GLIDE PATH CAPABILITY ANALYSIS")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = PortfolioOptimizer()
    
    # Test different time horizons
    time_horizons = [3, 5, 10, 15, 20, 30]
    
    from src.optimization.portfolio_optimizer import PortfolioRequest, AccountType
    
    print("Testing allocation changes based on time horizon:")
    print()
    
    # Get historical data once
    historical_data = optimizer._get_historical_data(20)
    returns_stats = optimizer._calculate_returns_statistics(historical_data)
    
    results_by_horizon = {}
    
    for horizon in time_horizons:
        print(f"📅 Time Horizon: {horizon} years")
        print("-" * 30)
        
        # Create request for this horizon
        request = PortfolioRequest(
            current_savings=100000.0,
            target_amount=500000.0,
            time_horizon=horizon,
            account_type=AccountType.TAXABLE
        )
        
        try:
            # Test balanced strategy (most representative)
            balanced_portfolio = optimizer._optimize_balanced(returns_stats, request)
            
            allocation = balanced_portfolio.allocation
            
            # Store key metrics
            results_by_horizon[horizon] = {
                'stocks_total': allocation.get('VTI', 0) + allocation.get('QQQ', 0) + 
                              allocation.get('VTIAX', 0) + allocation.get('VWO', 0),
                'bonds': allocation.get('BND', 0),
                'alternatives': allocation.get('GLD', 0) + allocation.get('VNQ', 0),
                'expected_return': balanced_portfolio.expected_return,
                'volatility': balanced_portfolio.expected_volatility,
                'allocation': allocation
            }
            
            # Print allocation
            for asset, weight in allocation.items():
                print(f"  {asset:6}: {weight:6.1%}")
            
            print(f"  Stocks:  {results_by_horizon[horizon]['stocks_total']:6.1%}")
            print(f"  Bonds:   {results_by_horizon[horizon]['bonds']:6.1%}")
            print(f"  Alts:    {results_by_horizon[horizon]['alternatives']:6.1%}")
            print(f"  Return:  {balanced_portfolio.expected_return:6.1%}")
            print(f"  Risk:    {balanced_portfolio.expected_volatility:6.1%}")
            print()
            
        except Exception as e:
            print(f"❌ Error for {horizon} years: {e}")
    
    # Analyze if there's a glide path pattern
    print("🔍 GLIDE PATH PATTERN ANALYSIS:")
    print("-" * 40)
    
    if len(results_by_horizon) >= 3:
        print("Time Horizon vs Asset Allocation:")
        print(f"{'Years':<6} {'Stocks':<8} {'Bonds':<8} {'Alts':<8} {'Return':<8} {'Risk':<8}")
        print("-" * 50)
        
        for horizon in sorted(results_by_horizon.keys()):
            r = results_by_horizon[horizon]
            print(f"{horizon:<6} {r['stocks_total']:<7.1%} {r['bonds']:<7.1%} "
                  f"{r['alternatives']:<7.1%} {r['expected_return']:<7.1%} {r['volatility']:<7.1%}")
        
        # Check for glide path behavior
        short_term = results_by_horizon[min(results_by_horizon.keys())]
        long_term = results_by_horizon[max(results_by_horizon.keys())]
        
        print(f"\n📊 Glide Path Evidence:")
        
        stock_diff = long_term['stocks_total'] - short_term['stocks_total']
        bond_diff = long_term['bonds'] - short_term['bonds']
        
        if stock_diff > 0.05:  # More than 5% more stocks for long-term
            print(f"✅ STOCKS: Higher allocation for longer horizons (+{stock_diff:.1%})")
        else:
            print(f"❌ STOCKS: No clear glide path pattern ({stock_diff:+.1%})")
            
        if bond_diff < -0.05:  # More than 5% fewer bonds for long-term
            print(f"✅ BONDS: Lower allocation for longer horizons ({bond_diff:+.1%})")
        else:
            print(f"❌ BONDS: No clear glide path pattern ({bond_diff:+.1%})")
    
    else:
        print("❌ Insufficient data to analyze glide path patterns")

if __name__ == "__main__":
    analyze_crisis_performance()
    analyze_glide_path_capability()
