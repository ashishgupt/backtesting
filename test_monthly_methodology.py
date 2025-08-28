#!/usr/bin/env python3
"""
Test portfolio engine using PortfolioVisualizer methodology
- Monthly returns instead of daily
- Different rebalancing approach
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.database import SessionLocal
from src.core.portfolio_engine import PortfolioEngine
import pandas as pd
import numpy as np

def test_monthly_methodology():
    """Test using monthly data points like PortfolioVisualizer"""
    print("🔍 Testing Monthly Methodology (PortfolioVisualizer Style)")
    print("=" * 70)
    
    db = SessionLocal()
    engine = PortfolioEngine(db)
    
    # Get daily data
    allocation = {'VTI': 0.6, 'VTIAX': 0.3, 'BND': 0.1}
    raw_data = engine.get_portfolio_data(['VTI', 'VTIAX', 'BND'], '2015-01-02', '2024-12-31')
    
    # Convert to monthly data (end-of-month prices)
    print("1️⃣ Converting Daily Data to Monthly...")
    
    # Pivot data
    price_data = raw_data.pivot(index='Date', columns='Symbol', values='AdjClose')
    dividend_data = raw_data.pivot(index='Date', columns='Symbol', values='Dividend')
    
    # Convert index to datetime
    price_data.index = pd.to_datetime(price_data.index)
    dividend_data.index = pd.to_datetime(dividend_data.index)
    
    # Get end-of-month prices
    monthly_prices = price_data.resample('M').last()
    monthly_dividends = dividend_data.resample('M').sum()  # Sum dividends for the month
    
    print(f"   Daily data points: {len(price_data)}")
    print(f"   Monthly data points: {len(monthly_prices)}")
    print(f"   Monthly date range: {monthly_prices.index[0].date()} to {monthly_prices.index[-1].date()}")
    
    # Manual monthly calculation
    print(f"\n2️⃣ Manual Monthly Portfolio Calculation...")
    
    initial_value = 10000
    portfolio_values = [initial_value]
    
    # Initial allocation
    first_prices = monthly_prices.iloc[0]
    shares = {}
    for symbol, weight in allocation.items():
        target_value = initial_value * weight
        shares[symbol] = target_value / first_prices[symbol]
    
    print(f"   Initial shares: {dict(shares)}")
    
    # Monthly portfolio evolution
    for i in range(1, len(monthly_prices)):
        current_prices = monthly_prices.iloc[i]
        current_dividends = monthly_dividends.iloc[i]
        
        # Calculate portfolio value
        portfolio_value = sum(shares[symbol] * current_prices[symbol] for symbol in allocation.keys())
        
        # Add dividend income and reinvest proportionally
        dividend_income = sum(shares[symbol] * current_dividends[symbol] for symbol in allocation.keys())
        
        if dividend_income > 0:
            for symbol, weight in allocation.items():
                dividend_to_reinvest = dividend_income * weight
                additional_shares = dividend_to_reinvest / current_prices[symbol]
                shares[symbol] += additional_shares
        
        # Recalculate after dividend reinvestment
        portfolio_value = sum(shares[symbol] * current_prices[symbol] for symbol in allocation.keys())
        
        # Annual rebalancing (January)
        if monthly_prices.index[i].month == 1:
            print(f"   Rebalancing in {monthly_prices.index[i].strftime('%Y-%m')}")
            total_value = portfolio_value
            for symbol, target_weight in allocation.items():
                target_value = total_value * target_weight
                shares[symbol] = target_value / current_prices[symbol]
        
        portfolio_values.append(portfolio_value)
    
    # Calculate performance metrics
    final_value = portfolio_values[-1]
    total_return = (final_value - initial_value) / initial_value
    years = len(monthly_prices) / 12.0
    cagr = (final_value / initial_value) ** (1/years) - 1
    
    print(f"\n📊 Monthly Methodology Results:")
    print(f"   Initial Value: ${initial_value:,.2f}")
    print(f"   Final Value: ${final_value:,.2f}")
    print(f"   Total Return: {total_return:.2%}")
    print(f"   CAGR: {cagr:.2%}")
    print(f"   Years: {years:.2f}")
    
    # Compare with our daily methodology
    print(f"\n3️⃣ Comparison with Daily Methodology...")
    daily_results = engine.backtest_portfolio(
        allocation=allocation,
        initial_value=10000,
        start_date="2015-01-02",
        end_date="2024-12-31",
        rebalance_frequency="annual"  # Match annual rebalancing
    )
    
    daily_cagr = daily_results['performance_metrics']['cagr']
    print(f"   Daily CAGR: {daily_cagr:.2%}")
    print(f"   Monthly CAGR: {cagr:.2%}")
    print(f"   Difference: {daily_cagr - cagr:.2%}")
    
    # Check individual asset performance
    print(f"\n4️⃣ Individual Asset Analysis...")
    for symbol in ['VTI', 'VTIAX', 'BND']:
        start_price = monthly_prices[symbol].iloc[0]
        end_price = monthly_prices[symbol].iloc[-1]
        asset_return = (end_price / start_price) ** (1/years) - 1
        print(f"   {symbol}: {start_price:.2f} → {end_price:.2f} = {asset_return:.2%} CAGR")
    
    db.close()

if __name__ == "__main__":
    test_monthly_methodology()
