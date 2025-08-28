#!/usr/bin/env python3
"""
Debug backtesting calculations by comparing with known benchmarks
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.database import SessionLocal
from src.core.portfolio_engine import PortfolioEngine
from src.core.data_manager import DataManager
import pandas as pd

def debug_calculation_issues():
    """Investigate potential calculation errors"""
    print("🔍 DEBUGGING Portfolio Calculation Issues")
    print("=" * 60)
    
    db = SessionLocal()
    engine = PortfolioEngine(db)
    dm = DataManager(db)
    
    # Test 1: Check raw data integrity
    print("1️⃣ Checking Raw Data Integrity...")
    raw_data = engine.get_portfolio_data(['VTI', 'VTIAX', 'BND'], '2015-01-02', '2024-12-31')
    print(f"   Total records: {len(raw_data)}")
    print(f"   Date range: {raw_data['Date'].min()} to {raw_data['Date'].max()}")
    
    # Check price evolution for VTI
    vti_data = raw_data[raw_data['Symbol'] == 'VTI'].copy()
    vti_data = vti_data.sort_values('Date')
    print(f"   VTI first price: ${vti_data['AdjClose'].iloc[0]:.2f}")
    print(f"   VTI last price: ${vti_data['AdjClose'].iloc[-1]:.2f}")
    print(f"   VTI raw return: {(vti_data['AdjClose'].iloc[-1] / vti_data['AdjClose'].iloc[0] - 1):.2%}")
    
    # Test 2: Simple buy-and-hold VTI calculation
    print(f"\n2️⃣ Simple Buy-and-Hold Test (100% VTI)...")
    simple_allocation = {'VTI': 1.0, 'VTIAX': 0.0, 'BND': 0.0}
    
    simple_results = engine.backtest_portfolio(
        allocation=simple_allocation,
        initial_value=10000,
        start_date="2015-01-02",
        end_date="2024-12-31",
        rebalance_frequency="annual"  # No rebalancing needed
    )
    
    print(f"   100% VTI Final Value: ${simple_results['final_value']:,.2f}")
    print(f"   100% VTI CAGR: {simple_results['performance_metrics']['cagr']:.2%}")
    print(f"   Expected vs Actual: Should roughly match VTI raw return")
    
    # Test 3: Check dividend handling
    print(f"\n3️⃣ Dividend Analysis...")
    total_dividends = vti_data['Dividend'].sum()
    print(f"   Total VTI dividends: ${total_dividends:.2f}")
    
    # Test 4: Check for data issues
    print(f"\n4️⃣ Data Quality Checks...")
    
    # Check for missing dates
    all_dates = pd.date_range(start='2015-01-02', end='2024-12-31', freq='D')
    trading_days_expected = len([d for d in all_dates if d.weekday() < 5])  # Mon-Fri
    actual_trading_days = len(vti_data)
    print(f"   Expected trading days: ~{trading_days_expected}")
    print(f"   Actual trading days: {actual_trading_days}")
    
    # Check for unusual price jumps
    vti_data['daily_return'] = vti_data['AdjClose'].pct_change()
    extreme_days = vti_data[abs(vti_data['daily_return']) > 0.15]  # >15% moves
    print(f"   Extreme daily moves (>15%): {len(extreme_days)}")
    if len(extreme_days) > 0:
        print(f"   Dates with extreme moves: {extreme_days['Date'].tolist()}")
    
    # Test 5: Manual calculation verification
    print(f"\n5️⃣ Manual Calculation Check...")
    start_price = vti_data['AdjClose'].iloc[0]
    end_price = vti_data['AdjClose'].iloc[-1]
    years = 10
    manual_cagr = (end_price / start_price) ** (1/years) - 1
    print(f"   Manual VTI CAGR (price only): {manual_cagr:.2%}")
    
    db.close()

if __name__ == "__main__":
    debug_calculation_issues()
