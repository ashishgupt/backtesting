#!/usr/bin/env python3
"""
Correlation-Based Portfolio Analysis

1. Test if our optimizer actually considers correlation benefits
2. Check if we're using fixed vs changing portfolios in the app
3. Test correlation-based optimization vs pure return optimization
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from scipy import optimize
from src.optimization.portfolio_optimizer import PortfolioOptimizer, PortfolioRequest, AccountType

def analyze_correlation_benefits():
    """Test if correlation benefits are being captured in optimization"""
    
    print("🔗 CORRELATION-BASED PORTFOLIO ANALYSIS")
    print("=" * 60)
    
    optimizer = PortfolioOptimizer()
    
    # Get historical data and correlation matrix
    historical_data = optimizer._get_historical_data(20)
    returns_stats = optimizer._calculate_returns_statistics(historical_data)
    
    corr_matrix = returns_stats['correlation_matrix']
    expected_returns = returns_stats['expected_returns']
    volatility = returns_stats['volatility']
    cov_matrix = returns_stats['covariance_matrix']
    
    print("📊 CORRELATION MATRIX:")
    print("-" * 40)
    print(corr_matrix.round(3))
    
    print(f"\n📈 INDIVIDUAL ASSET PERFORMANCE:")
    print("-" * 50)
    print(f"{'Asset':<6} {'Return':<8} {'Vol':<8} {'Sharpe':<7} {'Avg Corr':<8}")
    print("-" * 42)
    
    # Calculate average correlation for each asset
    for asset in optimizer.assets:
        if asset in corr_matrix.index:
            avg_corr = corr_matrix.loc[asset].drop(asset).mean()  # Exclude self-correlation
            ret = expected_returns[asset]
            vol = volatility[asset] 
            sharpe = (ret - 0.03) / vol
            print(f"{asset:<6} {ret:>7.1%} {vol:>7.1%} {sharpe:>6.2f} {avg_corr:>7.2f}")
    
    # Test different optimization approaches
    print(f"\n🧪 OPTIMIZATION APPROACH COMPARISON:")
    print("-" * 50)
    
    request = PortfolioRequest(
        current_savings=100000.0,
        time_horizon=10,
        account_type=AccountType.TAXABLE
    )
    
    # 1. Current optimizer (uses covariance matrix)
    print("1️⃣ CURRENT OPTIMIZER (Covariance-based):")
    current_portfolio = optimizer._optimize_balanced(returns_stats, request)
    print_portfolio_analysis(current_portfolio.allocation, returns_stats, "Current")
    
    # 2. Pure return optimization (ignoring correlations)
    print("\n2️⃣ PURE RETURN OPTIMIZER (Ignoring Correlations):")
    pure_return_allocation = optimize_pure_returns(returns_stats, optimizer.assets)
    print_portfolio_analysis(pure_return_allocation, returns_stats, "Pure Return")
    
    # 3. Low-correlation portfolio (force diversification)
    print("\n3️⃣ CORRELATION-DIVERSIFIED PORTFOLIO:")
    corr_diversified_allocation = optimize_low_correlation(returns_stats, optimizer.assets)
    print_portfolio_analysis(corr_diversified_allocation, returns_stats, "Low Correlation")
    
    # 4. Equal-weight portfolio (benchmark)
    print("\n4️⃣ EQUAL-WEIGHT PORTFOLIO (Benchmark):")
    equal_weight = {asset: 1/len(optimizer.assets) for asset in optimizer.assets}
    print_portfolio_analysis(equal_weight, returns_stats, "Equal Weight")
    
    # Compare portfolio correlations
    print(f"\n🔍 CORRELATION ANALYSIS:")
    print("-" * 40)
    
    portfolios = {
        "Current Optimizer": current_portfolio.allocation,
        "Pure Return": pure_return_allocation, 
        "Low Correlation": corr_diversified_allocation,
        "Equal Weight": equal_weight
    }
    
    for name, allocation in portfolios.items():
        avg_corr = calculate_portfolio_avg_correlation(allocation, corr_matrix)
        diversification_ratio = calculate_diversification_ratio(allocation, returns_stats)
        print(f"{name:<18}: Avg Correlation {avg_corr:5.2f} | Diversification Ratio {diversification_ratio:5.2f}")

def optimize_pure_returns(returns_stats, assets):
    """Optimize based purely on returns, ignoring correlations"""
    
    expected_returns = returns_stats['expected_returns'].values
    
    # Simply allocate to highest return assets
    # Sort by returns and allocate proportionally
    returns_series = returns_stats['expected_returns']
    sorted_assets = returns_series.sort_values(ascending=False)
    
    # Top 3 assets get allocation
    allocation = {}
    top_assets = sorted_assets.head(3)
    total_return = top_assets.sum()
    
    for asset in assets:
        if asset in top_assets.index:
            allocation[asset] = top_assets[asset] / total_return
        else:
            allocation[asset] = 0.0
    
    # Normalize to sum to 1
    total = sum(allocation.values())
    if total > 0:
        allocation = {k: v/total for k, v in allocation.items()}
    
    return allocation

def optimize_low_correlation(returns_stats, assets):
    """Optimize for low correlation while maintaining reasonable returns"""
    
    expected_returns = returns_stats['expected_returns'].values
    cov_matrix = returns_stats['covariance_matrix'].values
    corr_matrix = returns_stats['correlation_matrix'].values
    
    def objective(weights):
        # Minimize portfolio variance but penalize high correlations
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        
        # Add correlation penalty
        weighted_corr = 0
        for i in range(len(weights)):
            for j in range(i+1, len(weights)):
                weighted_corr += weights[i] * weights[j] * abs(corr_matrix[i,j])
        
        return portfolio_variance + 0.5 * weighted_corr  # Correlation penalty
    
    # Constraints: weights sum to 1, minimum 5% in each asset for diversification
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}]
    bounds = [(0.05, 0.25) for _ in assets]  # Force diversification
    
    # Initial guess: equal weights
    x0 = np.array([1/len(assets)] * len(assets))
    
    result = optimize.minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
    
    if result.success:
        return dict(zip(assets, result.x))
    else:
        return {asset: 1/len(assets) for asset in assets}  # Fallback to equal weight

def print_portfolio_analysis(allocation, returns_stats, name):
    """Print detailed portfolio analysis"""
    
    # Calculate portfolio metrics
    weights = np.array([allocation.get(asset, 0) for asset in returns_stats['expected_returns'].index])
    expected_returns = returns_stats['expected_returns'].values
    cov_matrix = returns_stats['covariance_matrix'].values
    
    portfolio_return = np.dot(weights, expected_returns)
    portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
    sharpe = (portfolio_return - 0.03) / portfolio_vol if portfolio_vol > 0 else 0
    
    print(f"  Return: {portfolio_return:6.1%} | Volatility: {portfolio_vol:6.1%} | Sharpe: {sharpe:5.2f}")
    print("  Allocation:")
    for asset, weight in allocation.items():
        if weight > 0.001:  # Only show meaningful allocations
            print(f"    {asset}: {weight:6.1%}")

def calculate_portfolio_avg_correlation(allocation, corr_matrix):
    """Calculate weighted average correlation of portfolio"""
    
    total_weighted_corr = 0
    total_weight_pairs = 0
    
    for asset1, weight1 in allocation.items():
        for asset2, weight2 in allocation.items():
            if asset1 != asset2 and weight1 > 0 and weight2 > 0:
                if asset1 in corr_matrix.index and asset2 in corr_matrix.columns:
                    corr = corr_matrix.loc[asset1, asset2]
                    total_weighted_corr += weight1 * weight2 * corr
                    total_weight_pairs += weight1 * weight2
    
    return total_weighted_corr / total_weight_pairs if total_weight_pairs > 0 else 0

def calculate_diversification_ratio(allocation, returns_stats):
    """Calculate diversification ratio (weighted avg vol / portfolio vol)"""
    
    weights = np.array([allocation.get(asset, 0) for asset in returns_stats['volatility'].index])
    individual_vols = returns_stats['volatility'].values
    cov_matrix = returns_stats['covariance_matrix'].values
    
    weighted_avg_vol = np.dot(weights, individual_vols)
    portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
    
    return weighted_avg_vol / portfolio_vol if portfolio_vol > 0 else 1

def check_app_portfolio_behavior():
    """Check if the app uses fixed or rebalanced portfolios"""
    
    print(f"\n\n📱 APP PORTFOLIO BEHAVIOR ANALYSIS")
    print("=" * 60)
    
    print("Checking how portfolios are implemented in the application...")
    
    # Check if we have rebalancing functionality
    try:
        # Look for portfolio engine and backtest functionality
        from src.core.portfolio_engine_optimized import OptimizedPortfolioEngine
        
        engine = OptimizedPortfolioEngine()
        
        print("✅ Found OptimizedPortfolioEngine - supports dynamic rebalancing")
        
        # Test a sample allocation
        sample_allocation = {'VTI': 0.4, 'VTIAX': 0.2, 'BND': 0.2, 'VNQ': 0.1, 'GLD': 0.05, 'VWO': 0.03, 'QQQ': 0.02}
        
        print(f"\n🧪 Testing Portfolio Engine Capabilities:")
        print("-" * 45)
        
        # Test different rebalancing frequencies
        frequencies = ['monthly', 'quarterly', 'annual']
        
        for freq in frequencies:
            try:
                result = engine.backtest_portfolio(
                    allocation=sample_allocation,
                    start_date="2020-01-01",
                    end_date="2021-12-31", 
                    rebalance_frequency=freq
                )
                
                if result and 'final_value' in result:
                    print(f"  {freq:<10} rebalancing: ✅ Supported (Final value: ${result['final_value']:,.0f})")
                else:
                    print(f"  {freq:<10} rebalancing: ❌ Failed")
                    
            except Exception as e:
                print(f"  {freq:<10} rebalancing: ❌ Error - {str(e)[:50]}...")
                
        # Check what the guided dashboard actually uses
        print(f"\n📊 GUIDED DASHBOARD IMPLEMENTATION:")
        print("-" * 45)
        print("The guided dashboard optimization results show:")
        print("• Expected returns and volatility based on historical backtesting")
        print("• These likely assume periodic rebalancing to maintain target allocation")
        print("• But we need to verify the actual implementation...")
        
    except ImportError:
        print("❌ OptimizedPortfolioEngine not available")
    except Exception as e:
        print(f"❌ Error testing portfolio engine: {e}")

if __name__ == "__main__":
    analyze_correlation_benefits()
    check_app_portfolio_behavior()
