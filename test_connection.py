#!/usr/bin/env python3
"""
Test script to validate database connection and DataManager functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.database import engine, SessionLocal
from src.models.schemas import Asset, DailyPrice
from src.core.data_manager import DataManager

def test_database_connection():
    """Test basic database connectivity"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test")).fetchone()
            print(f"✅ Database connection successful: {result}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_data_manager():
    """Test DataManager functionality"""
    try:
        # Create DataManager instance
        db = SessionLocal()
        dm = DataManager(db)
        
        # Test 1: Ensure assets exist
        print("\n📊 Testing asset creation...")
        dm.ensure_assets_exist()
        
        # Verify assets were created
        assets = db.query(Asset).all()
        print(f"Assets in database: {[a.symbol for a in assets]}")
        
        # Test 2: Fetch small sample of data (just 1 week)
        print("\n📈 Testing data fetch (sample)...")
        sample_data = dm.fetch_historical_data('VTI', '2024-01-01', '2024-01-08')
        print(f"Sample data shape: {sample_data.shape}")
        print(f"Sample data columns: {list(sample_data.columns)}")
        
        # Test 3: Data validation
        if len(sample_data) > 0:
            print(f"Sample price range: ${sample_data['Adj Close'].min():.2f} - ${sample_data['Adj Close'].max():.2f}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ DataManager test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Portfolio Backtesting - Connection Test")
    print("=" * 50)
    
    # Test database connection
    db_ok = test_database_connection()
    
    if db_ok:
        # Test DataManager
        dm_ok = test_data_manager()
        
        if dm_ok:
            print("\n✅ All tests passed! Ready for backtesting development.")
        else:
            print("\n❌ DataManager tests failed.")
    else:
        print("\n❌ Database connection failed. Check .env file and PostgreSQL.")
