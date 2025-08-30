#!/usr/bin/env python3
"""
Simple test to validate rolling periods optimization
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test imports
try:
    print('Testing imports...')
    from models import get_db, Asset, DailyPrice
    print('✅ Database models imported')
    
    # Test database connection
    db = next(get_db())
    asset_count = db.query(Asset).count()
    price_count = db.query(DailyPrice).count()
    print(f'✅ Database connected: {asset_count} assets, {price_count} prices')
    
    # Check specific assets
    symbols = ['BND', 'VTI', 'VTIAX']
    for symbol in symbols:
        asset = db.query(Asset).filter(Asset.symbol == symbol).first()
        if asset:
            price_count = db.query(DailyPrice).filter(DailyPrice.symbol == symbol).count()
            earliest = db.query(DailyPrice.date).filter(DailyPrice.symbol == symbol).order_by(DailyPrice.date.asc()).first()
            latest = db.query(DailyPrice.date).filter(DailyPrice.symbol == symbol).order_by(DailyPrice.date.desc()).first()
            print(f'  {symbol}: {price_count} prices, {earliest.date} to {latest.date}')
        else:
            print(f'  {symbol}: NOT FOUND')
            
    print()
    
    # Now test a simple date range calculation
    from datetime import datetime, timedelta
    
    start_date = datetime(2015, 1, 1)
    end_date = datetime(2023, 12, 31) 
    period_years = 5
    
    print('🔧 TESTING WINDOW CALCULATION:')
    print(f'Start: {start_date.date()}, End: {end_date.date()}, Period: {period_years} years')
    
    # Original logic (30-day steps)
    window_count_30 = 0
    window_start = start_date
    windows_30 = []
    
    while window_count_30 < 10:  # Limit for display
        window_end = window_start + timedelta(days=period_years * 365)
        if window_end > end_date:
            break
        windows_30.append((window_start.date(), window_end.date()))
        window_count_30 += 1
        window_start = window_start + timedelta(days=30)
    
    # Optimized logic (90-day steps) 
    window_count_90 = 0
    window_start = start_date
    windows_90 = []
    
    while window_count_90 < 10:  # Limit for display
        window_end = window_start + timedelta(days=period_years * 365)
        if window_end > end_date:
            break
        windows_90.append((window_start.date(), window_end.date()))
        window_count_90 += 1
        window_start = window_start + timedelta(days=90)
        
    print()
    print(f'Original (30-day steps): First {len(windows_30)} windows:')
    for i, (start, end) in enumerate(windows_30):
        print(f'  {i+1}: {start} to {end}')
        
    print()
    print(f'Optimized (90-day steps): First {len(windows_90)} windows:')
    for i, (start, end) in enumerate(windows_90):
        print(f'  {i+1}: {start} to {end}')
    
    # Calculate full ranges
    total_days = (end_date - start_date).days
    window_days = period_years * 365
    available_range = total_days - window_days
    
    max_windows_30 = max(0, available_range // 30)
    max_windows_90 = max(0, available_range // 90)
    
    print()
    print(f'📊 FULL RANGE ANALYSIS:')
    print(f'Total range: {total_days} days')
    print(f'Window size: {window_days} days')
    print(f'Available range: {available_range} days')
    print(f'Max windows (30-day steps): {max_windows_30}')
    print(f'Max windows (90-day steps): {max_windows_90}')
    print(f'Performance improvement: {max_windows_30 / max_windows_90:.1f}x faster')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
