#!/usr/bin/env python3
"""
Quick Data Range Check

Check what historical data we actually have available.
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from src.optimization.portfolio_optimizer import PortfolioOptimizer

def check_data_availability():
    """Check what historical data is actually available"""
    
    print("📊 DATA AVAILABILITY CHECK")
    print("=" * 40)
    
    optimizer = PortfolioOptimizer()
    
    # Get historical data
    historical_data = optimizer._get_historical_data(20)
    
    print("Overall Data Summary:")
    print(f"Total records: {len(historical_data)}")
    print(f"Date range: {historical_data['Date'].min()} to {historical_data['Date'].max()}")
    print(f"Assets: {sorted(historical_data['Symbol'].unique())}")
    print()
    
    print("Data availability by asset:")
    for asset in optimizer.assets:
        asset_data = historical_data[historical_data['Symbol'] == asset]
        if len(asset_data) > 0:
            start_date = asset_data['Date'].min()
            end_date = asset_data['Date'].max()
            print(f"  {asset:6}: {start_date} to {end_date} ({len(asset_data)} records)")
        else:
            print(f"  {asset:6}: NO DATA")
    
    # Check if we have 2004-2009 data
    print(f"\n🔍 2004-2009 Data Check:")
    crisis_start = pd.to_datetime('2004-01-01')
    crisis_end = pd.to_datetime('2009-12-31')
    
    crisis_data = historical_data[
        (historical_data['Date'] >= crisis_start) & 
        (historical_data['Date'] <= crisis_end)
    ]
    
    if len(crisis_data) > 0:
        print(f"✅ Have {len(crisis_data)} records for 2004-2009")
        print("Assets available for 2004-2009:")
        for asset in crisis_data['Symbol'].unique():
            asset_crisis = crisis_data[crisis_data['Symbol'] == asset]
            print(f"  {asset}: {len(asset_crisis)} records")
    else:
        print("❌ NO data available for 2004-2009 period")
        
    # Check 2007-2009 financial crisis
    print(f"\n🔍 2007-2009 Financial Crisis Data Check:")
    fin_crisis_start = pd.to_datetime('2007-10-01')
    fin_crisis_end = pd.to_datetime('2009-03-31')
    
    fin_crisis_data = historical_data[
        (historical_data['Date'] >= fin_crisis_start) & 
        (historical_data['Date'] <= fin_crisis_end)
    ]
    
    if len(fin_crisis_data) > 0:
        print(f"✅ Have {len(fin_crisis_data)} records for 2007-2009 crisis")
    else:
        print("❌ NO data for 2007-2009 financial crisis")

if __name__ == "__main__":
    check_data_availability()
