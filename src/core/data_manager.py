"""
DataManager - Handle data fetching and storage for portfolio backtesting
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from ..models.database import get_db
from ..models.schemas import Asset, DailyPrice

class DataManager:
    """Manages historical price data fetching and storage"""
    
    # Target assets for backtesting
    DEFAULT_ASSETS = {
        'VTI': {'name': 'Vanguard Total Stock Market ETF', 'asset_class': 'US_EQUITY'},
        'VTIAX': {'name': 'Vanguard Total International Stock Index Admiral', 'asset_class': 'INTL_EQUITY'},
        'BND': {'name': 'Vanguard Total Bond Market ETF', 'asset_class': 'US_BONDS'}
    }
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        
    def ensure_assets_exist(self) -> None:
        """Ensure our target assets exist in the database"""
        existing_symbols = {asset.symbol for asset in self.db.query(Asset).all()}
        
        for symbol, info in self.DEFAULT_ASSETS.items():
            if symbol not in existing_symbols:
                asset = Asset(
                    symbol=symbol,
                    name=info['name'],
                    asset_class=info['asset_class']
                )
                self.db.add(asset)
        
        self.db.commit()
        print(f"Assets ensured in database: {list(self.DEFAULT_ASSETS.keys())}")
    
    def fetch_historical_data(self, symbol: str, start_date: str = "2015-01-01", 
                             end_date: str = "2025-01-01") -> pd.DataFrame:
        """
        Fetch historical data from Yahoo Finance
        
        Args:
            symbol: Stock symbol (e.g., 'VTI')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with historical price data
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data with dividends and splits
            hist = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            
            if hist.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            # Add dividend and split information
            dividends = ticker.dividends
            splits = ticker.splits
            
            # Merge dividend data
            hist['Dividend'] = 0.0
            if not dividends.empty:
                # Match dividends to dates in our data
                for div_date, div_amount in dividends.items():
                    div_date = div_date.date()
                    if div_date in hist.index.date:
                        hist.loc[hist.index.date == div_date, 'Dividend'] = div_amount
            
            # Add split factor
            hist['Split_Factor'] = 1.0
            if not splits.empty:
                for split_date, split_factor in splits.items():
                    split_date = split_date.date()
                    if split_date in hist.index.date:
                        hist.loc[hist.index.date == split_date, 'Split_Factor'] = split_factor
            
            print(f"Fetched {len(hist)} days of data for {symbol}")
            return hist
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            raise
    
    def store_price_data(self, symbol: str, price_data: pd.DataFrame) -> int:
        """
        Store price data in the database
        
        Args:
            symbol: Stock symbol
            price_data: DataFrame from fetch_historical_data
            
        Returns:
            Number of records stored
        """
        records_stored = 0
        
        try:
            # Check existing data to avoid duplicates
            existing_dates = {
                row[0] for row in 
                self.db.query(DailyPrice.date).filter(DailyPrice.symbol == symbol).all()
            }
            
            for date_idx, row in price_data.iterrows():
                price_date = date_idx.date()
                
                # Skip if already exists
                if price_date in existing_dates:
                    continue
                
                price_record = DailyPrice(
                    date=price_date,
                    symbol=symbol,
                    open_price=float(row['Open']),
                    high_price=float(row['High']),
                    low_price=float(row['Low']),
                    close_price=float(row['Close']),
                    adj_close=float(row['Adj Close']),
                    volume=int(row['Volume']) if pd.notna(row['Volume']) else None,
                    dividend=float(row['Dividend']) if pd.notna(row['Dividend']) else 0,
                    split_factor=float(row['Split_Factor']) if pd.notna(row['Split_Factor']) else 1
                )
                
                self.db.add(price_record)
                records_stored += 1
            
            self.db.commit()
            print(f"Stored {records_stored} new price records for {symbol}")
            return records_stored
            
        except Exception as e:
            self.db.rollback()
            print(f"Error storing data for {symbol}: {e}")
            raise
    
    def refresh_all_data(self) -> Dict[str, int]:
        """
        Refresh historical data for all target assets
        
        Returns:
            Dictionary mapping symbol to number of new records
        """
        self.ensure_assets_exist()
        results = {}
        
        for symbol in self.DEFAULT_ASSETS.keys():
            try:
                print(f"Refreshing data for {symbol}...")
                price_data = self.fetch_historical_data(symbol)
                records_stored = self.store_price_data(symbol, price_data)
                results[symbol] = records_stored
                
            except Exception as e:
                print(f"Failed to refresh {symbol}: {e}")
                results[symbol] = 0
        
        return results
    
    def get_price_data(self, symbols: List[str], start_date: date = None, 
                      end_date: date = None) -> pd.DataFrame:
        """
        Retrieve price data from database as DataFrame
        
        Args:
            symbols: List of symbols to fetch
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            DataFrame with columns: Date, Symbol, AdjClose, Dividend
        """
        query = select(
            DailyPrice.date,
            DailyPrice.symbol, 
            DailyPrice.adj_close,
            DailyPrice.dividend
        ).filter(DailyPrice.symbol.in_(symbols))
        
        if start_date:
            query = query.filter(DailyPrice.date >= start_date)
        if end_date:
            query = query.filter(DailyPrice.date <= end_date)
            
        query = query.order_by(DailyPrice.date, DailyPrice.symbol)
        
        # Execute query and convert to DataFrame
        result = self.db.execute(query).fetchall()
        
        if not result:
            return pd.DataFrame()
        
        df = pd.DataFrame(result, columns=['Date', 'Symbol', 'AdjClose', 'Dividend'])
        
        # Convert Decimal to float for calculations
        df['AdjClose'] = df['AdjClose'].astype(float)
        df['Dividend'] = df['Dividend'].astype(float)
        
        return df
    
    def validate_data_integrity(self, symbol: str) -> Dict[str, Any]:
        """
        Validate data integrity for a symbol
        
        Returns:
            Dictionary with validation results
        """
        query = select(
            DailyPrice.date,
            DailyPrice.adj_close,
            DailyPrice.dividend
        ).filter(DailyPrice.symbol == symbol).order_by(DailyPrice.date)
        
        result = self.db.execute(query).fetchall()
        
        if not result:
            return {'valid': False, 'error': 'No data found'}
        
        df = pd.DataFrame(result, columns=['Date', 'AdjClose', 'Dividend'])
        
        validation = {
            'valid': True,
            'symbol': symbol,
            'total_records': len(df),
            'date_range': {
                'start': df['Date'].min(),
                'end': df['Date'].max()
            },
            'missing_dates': 0,  # Could implement business day gap detection
            'negative_prices': (df['AdjClose'] <= 0).sum(),
            'avg_daily_return': df['AdjClose'].pct_change().mean(),
            'total_dividends': df['Dividend'].sum()
        }
        
        return validation
