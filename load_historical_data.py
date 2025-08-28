#!/usr/bin/env python3
"""
Load full historical data for backtesting (2004-2024)
This script loads 20 years of data for all 7 assets:
VTI, VTIAX, BND, VNQ, GLD, VWO, QQQ
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.database import SessionLocal
from src.core.data_manager import DataManager
from datetime import datetime

def main():
    print("📈 Loading Full Historical Data (2004-2024) - 7 Asset Universe")
    print("=" * 70)
    
    # Create DataManager instance
    db = SessionLocal()
    dm = DataManager(db)
    
    try:
        # Load full dataset for all 7 assets over 20 years
        print("Loading 20 years of data for 7-asset portfolio...")
        print("Assets: VTI, VTIAX, BND, VNQ, GLD, VWO, QQQ")
        print("Period: 2004-01-01 to 2024-12-31")
        print("Expected: ~51,100 records (20 years × 7 assets × ~365 days)")
        print("This may take several minutes...")
        
        start_time = datetime.now()
        results = dm.refresh_all_data()
        end_time = datetime.now()
        
        print(f"\n📊 Data Loading Results:")
        total_records = 0
        for symbol, count in results.items():
            print(f"  {symbol}: {count:,} new records")
            total_records += count
        
        print(f"\nTotal new records loaded: {total_records:,}")
        print(f"Loading time: {(end_time - start_time).total_seconds():.1f} seconds")
        
        # Validate data integrity for all assets
        print(f"\n🔍 Data Validation:")
        for symbol in dm.DEFAULT_ASSETS.keys():
            validation = dm.validate_data_integrity(symbol)
            print(f"\n{symbol} Validation:")
            print(f"  Records: {validation['total_records']:,}")
            print(f"  Date Range: {validation['date_range']['start']} to {validation['date_range']['end']}")
            print(f"  Total Dividends: ${validation['total_dividends']:.2f}")
            print(f"  Avg Daily Return: {validation['avg_daily_return']:.4f}")
            
        print(f"\n✅ 7-asset historical data loading complete!")
        print(f"🎯 Ready for expanded portfolio backtesting and optimization")
        
    except Exception as e:
        print(f"❌ Error loading historical data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
