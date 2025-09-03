#!/usr/bin/env python3
"""
Fair Performance Comparison

Analyze performance using only periods where ALL assets have data,
to get a fair comparison of risk-adjusted returns.
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from src.optimization.portfolio_optimizer import PortfolioOptimizer

def analyze_fair_performance():
    """Analyze performance using common data periods only"""
    
    print("⚖️ FAIR PERFORMANCE COMPARISON")
    print("=" * 50)
    
    optimizer = PortfolioOptimizer()
    
    # Get historical data
    historical_data = optimizer._get_historical_data(20)
    returns_stats = optimizer._calculate_returns_statistics(historical_data)
    daily_returns = returns_stats['returns']
    
    print("Data availability by asset:")
    data_start_dates = {}
    for asset in optimizer.assets:
        if asset in daily_returns.columns:
            asset_returns = daily_returns[asset].dropna()
            if len(asset_returns) > 0:
                start_date = asset_returns.index[0]
                end_date = asset_returns.index[-1]
                data_start_dates[asset] = start_date
                print(f"  {asset:6}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Find the latest start date (when ALL assets have data)
    common_start = max(data_start_dates.values())
    print(f"\n📅 Common data period starts: {common_start.strftime('%Y-%m-%d')}")
    print("(This is when ALL assets have complete data)")
    
    # Analyze performance from common start date
    common_period_returns = daily_returns[daily_returns.index >= common_start]
    
    print(f"\n📊 PERFORMANCE FROM {common_start.strftime('%Y-%m-%d')} (Fair Comparison)")
    print("-" * 60)
    
    performance_results = []
    
    for asset in optimizer.assets:
        if asset in common_period_returns.columns:
            asset_returns = common_period_returns[asset].dropna()
            
            if len(asset_returns) > 252:  # At least 1 year of data
                # Calculate fair performance metrics
                total_return = (1 + asset_returns).prod() - 1
                years = len(asset_returns) / 252
                annualized_return = ((1 + total_return) ** (1/years)) - 1
                volatility = asset_returns.std() * np.sqrt(252)
                sharpe = (annualized_return - 0.03) / volatility if volatility > 0 else 0
                
                # Calculate max drawdown
                cumulative = (1 + asset_returns).cumprod()
                peak = cumulative.expanding().max()
                drawdown = (cumulative / peak - 1)
                max_drawdown = drawdown.min()
                
                performance_results.append({
                    'Asset': asset,
                    'Ann. Return': annualized_return,
                    'Volatility': volatility,
                    'Sharpe Ratio': sharpe,
                    'Max Drawdown': max_drawdown,
                    'Risk-Adj Score': annualized_return / volatility if volatility > 0 else 0
                })
    
    # Sort by risk-adjusted score
    performance_results.sort(key=lambda x: x['Risk-Adj Score'], reverse=True)
    
    print("FAIR PERFORMANCE RANKING (Risk-Adjusted):")
    print(f"{'Rank':<4} {'Asset':<6} {'Ann.Ret':<8} {'Vol':<8} {'Sharpe':<7} {'Max DD':<8} {'Risk/Ret':<8}")
    print("-" * 65)
    
    for i, r in enumerate(performance_results, 1):
        print(f"{i:<4} {r['Asset']:<6} {r['Ann. Return']:>7.1%} {r['Volatility']:>7.1%} "
              f"{r['Sharpe Ratio']:>6.2f} {r['Max Drawdown']:>7.1%} {r['Risk-Adj Score']:>7.2f}")
    
    # Highlight the "problem" assets
    print(f"\n🎯 'Problem' Asset Performance in Fair Comparison:")
    problem_assets = ['VTIAX', 'VWO', 'VNQ']
    
    for i, r in enumerate(performance_results, 1):
        if r['Asset'] in problem_assets:
            rank_desc = "TOP TIER" if i <= 3 else "MIDDLE TIER" if i <= 5 else "LOWER TIER"
            print(f"  {r['Asset']}: Rank #{i} of {len(performance_results)} ({rank_desc})")
    
    # Analyze specific crisis periods within common data range
    print(f"\n🔥 CRISIS PERFORMANCE ANALYSIS (From {common_start.strftime('%Y-%m-%d')})")
    print("-" * 60)
    
    crisis_periods = [
        {
            'name': '2020 COVID Crash',
            'start': '2020-02-19',
            'end': '2020-03-23'
        },
        {
            'name': '2022 Bear Market',
            'start': '2022-01-03', 
            'end': '2022-10-12'
        },
        {
            'name': '2018 Q4 Selloff',
            'start': '2018-10-01',
            'end': '2018-12-24'
        }
    ]
    
    for period in crisis_periods:
        period_start = pd.to_datetime(period['start'])
        period_end = pd.to_datetime(period['end'])
        
        if pd.to_datetime(period_start) >= common_start:  # Only analyze if within our data range
            print(f"\n📉 {period['name']} ({period['start']} to {period['end']})")
            print("-" * 40)
            
            crisis_returns = common_period_returns[
                (common_period_returns.index >= period_start) & 
                (common_period_returns.index <= period_end)
            ]
            
            if len(crisis_returns) > 5:  # Sufficient data
                crisis_performance = []
                
                for asset in optimizer.assets:
                    if asset in crisis_returns.columns:
                        asset_crisis = crisis_returns[asset].dropna()
                        if len(asset_crisis) > 0:
                            total_decline = (1 + asset_crisis).prod() - 1
                            crisis_performance.append({
                                'Asset': asset,
                                'Decline': total_decline
                            })
                
                # Sort by performance (least decline = best performance)
                crisis_performance.sort(key=lambda x: x['Decline'], reverse=True)
                
                print("Crisis Protection Ranking (Best to Worst):")
                for i, r in enumerate(crisis_performance, 1):
                    status = "🛡️ DEFENSIVE" if r['Decline'] > -0.10 else "⚠️ VOLATILE"
                    if r['Asset'] in problem_assets:
                        status += " (PROBLEM ASSET)"
                    print(f"  #{i} {r['Asset']}: {r['Decline']:>+7.1%} {status}")

def analyze_glide_path():
    """Check if our engine adjusts allocation based on time horizon"""
    
    print(f"\n\n🛤️ GLIDE PATH ANALYSIS")
    print("=" * 50)
    
    optimizer = PortfolioOptimizer()
    
    # Get data for optimization
    historical_data = optimizer._get_historical_data(20)
    returns_stats = optimizer._calculate_returns_statistics(historical_data)
    
    from src.optimization.portfolio_optimizer import PortfolioRequest, AccountType
    
    time_horizons = [3, 5, 10, 15, 20]
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
    
    # Check for glide path pattern
    if len(allocations_by_horizon) >= 3:
        print(f"\n📈 GLIDE PATH PATTERN DETECTION:")
        print("-" * 40)
        
        short_term = allocations_by_horizon[min(allocations_by_horizon.keys())]
        long_term = allocations_by_horizon[max(allocations_by_horizon.keys())]
        
        stock_change = long_term['stocks'] - short_term['stocks']
        bond_change = long_term['bonds'] - short_term['bonds']
        
        print(f"Stock allocation change (short → long term): {stock_change:+.1%}")
        print(f"Bond allocation change (short → long term): {bond_change:+.1%}")
        
        if stock_change > 0.05:
            print("✅ GLIDE PATH DETECTED: More stocks for longer horizons")
        elif stock_change < -0.05:
            print("📉 REVERSE GLIDE: Fewer stocks for longer horizons")
        else:
            print("➡️ FLAT PROFILE: Similar allocation regardless of horizon")
            
        if abs(bond_change) > 0.05:
            if bond_change < 0:
                print("✅ BOND GLIDE: Fewer bonds for longer horizons")
            else:
                print("📈 BOND INCREASE: More bonds for longer horizons")

if __name__ == "__main__":
    analyze_fair_performance()
    analyze_glide_path()
