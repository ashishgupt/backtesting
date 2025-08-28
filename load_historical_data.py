#!/usr/bin/env python3
"""
Load full historical data for backtesting (2015-2025)
This script loads 10 years of data for VTI, VTIAX, BND
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.database import SessionLocal
from src.core.data_manager import DataManager
from datetime import datetime

def main():
    print("📈 Loading Full Historical Data (2015-2025)")
    print("=" * 60)
    
    # Create DataManager instance
    db = SessionLocal()
    dm = DataManager(db)
    
    try:
        # Load full dataset for all assets
        print("Loading 10 years of data for VTI, VTIAX, BND...")
        print("This may take a few minutes...")
        
        results = dm.refresh_all_data()
        
        print(f"\n📊 Data Loading Results:")
        total_records = 0
        for symbol, count in results.items():
            print(f"  {symbol}: {count} new records")
            total_records += count
        
        print(f"\nTotal new records loaded: {total_records}")
        
        # Validate data integrity
        print(f"\n🔍 Data Validation:")
        for symbol in dm.DEFAULT_ASSETS.keys():
            validation = dm.validate_data_integrity(symbol)
            print(f"\n{symbol} Validation:")
            print(f"  Records: {validation['total_records']}")
            print(f"  Date Range: {validation['date_range']['start']} to {validation['date_range']['end']}")
            print(f"  Total Dividends: ${validation['total_dividends']:.2f}")
            print(f"  Avg Daily Return: {validation['avg_daily_return']:.4f}")
            
        print(f"\n✅ Historical data loading complete!")
        
    except Exception as e:
        print(f"❌ Error loading historical data: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
