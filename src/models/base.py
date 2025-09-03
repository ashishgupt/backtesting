"""
Enhanced Database Manager for Regime Analysis
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.database_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost/backtesting")
        self.engine = create_engine(self.database_url)
    
    def get_connection(self):
        return self.engine
    
    def execute_query(self, query: str, params=None):
        """Execute a query and return results"""
        try:
            with self.engine.connect() as conn:
                if params:
                    # Convert positional parameters to dictionary for SQLAlchemy
                    if isinstance(params, (list, tuple)):
                        # Simple positional parameters - replace %s with named parameters
                        param_dict = {f'param_{i}': params[i] for i in range(len(params))}
                        # Replace %s placeholders with :param_0, :param_1, etc.
                        modified_query = query
                        for i in range(len(params)):
                            modified_query = modified_query.replace('%s', f':param_{i}', 1)
                        result = conn.execute(text(modified_query), param_dict)
                    else:
                        # Dictionary parameters
                        result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                return result.fetchall()
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            return []
    
    def get_historical_data(self):
        """Get historical price data for all assets"""
        query = """
        SELECT 
            date,
            MAX(CASE WHEN symbol = 'VTI' THEN adj_close END) as "VTI",
            MAX(CASE WHEN symbol = 'VTIAX' THEN adj_close END) as "VTIAX", 
            MAX(CASE WHEN symbol = 'BND' THEN adj_close END) as "BND",
            MAX(CASE WHEN symbol = 'VNQ' THEN adj_close END) as "VNQ",
            MAX(CASE WHEN symbol = 'GLD' THEN adj_close END) as "GLD",
            MAX(CASE WHEN symbol = 'VWO' THEN adj_close END) as "VWO",
            MAX(CASE WHEN symbol = 'QQQ' THEN adj_close END) as "QQQ"
        FROM daily_prices 
        WHERE symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
        GROUP BY date
        HAVING COUNT(DISTINCT symbol) = 7
        ORDER BY date
        """
        return pd.read_sql(query, self.engine)
    
    def get_price_data(self, start_date=None, end_date=None, symbols=None):
        """Get price data with flexible filtering"""
        if symbols is None:
            symbols = ['VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ']
        
        # Try the new table structure first, fallback to old structure
        queries = [
            """
            SELECT date, symbol, adjusted_close
            FROM historical_prices 
            WHERE date BETWEEN %(start_date)s AND %(end_date)s
            AND symbol = ANY(%(symbols)s)
            ORDER BY date, symbol
            """,
            """
            SELECT date, symbol, adj_close as adjusted_close
            FROM daily_prices 
            WHERE date BETWEEN %(start_date)s AND %(end_date)s
            AND symbol = ANY(%(symbols)s)
            ORDER BY date, symbol
            """
        ]
        
        for query in queries:
            try:
                df = pd.read_sql(query, self.engine, params={
                    'start_date': start_date,
                    'end_date': end_date,
                    'symbols': symbols
                })
                if not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"Query failed, trying fallback: {str(e)}")
                continue
        
        return pd.DataFrame()
