"""
PortfolioEngine - OPTIMIZED Core backtesting logic for portfolio performance analysis

SPRINT 2, Phase 1, Week 3: Portfolio Engine Optimization
Target: <0.5s for 7-asset backtesting (currently 0.6-0.8s)

Key Optimizations:
1. Vectorized calculations with NumPy instead of Python loops
2. Pre-computed symbol indices to avoid dictionary lookups
3. Optimized dividend reinvestment using array operations
4. Exact rebalancing logic match with original engine for accuracy
5. Reduced DataFrame operations in tight loops
"""
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session

from ..models.database import get_db
from .data_manager import DataManager

class OptimizedPortfolioEngine:
    """Optimized core engine for portfolio backtesting and performance analysis"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.data_manager = DataManager(self.db)
        
    def get_portfolio_data(self, symbols: List[str], start_date: str = "2015-01-01", 
                          end_date: str = "2024-12-31") -> pd.DataFrame:
        """Get historical data for portfolio backtesting"""
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        return self.data_manager.get_price_data(symbols, start, end)
    
    def backtest_portfolio(self, allocation: Dict[str, float], 
                          initial_value: float = 10000, 
                          start_date: str = "2015-01-01",
                          end_date: str = "2024-12-31", 
                          rebalance_frequency: str = "monthly",
                          include_daily_data: bool = False) -> Dict:
        """OPTIMIZED backtest a portfolio allocation over time"""
        
        # Validate allocation
        total_weight = sum(allocation.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Portfolio allocation must sum to 1.0, got {total_weight}")
        
        # Get historical data
        symbols = list(allocation.keys())
        raw_data = self.get_portfolio_data(symbols, start_date, end_date)
        
        if raw_data.empty:
            raise ValueError("No historical data found for the specified period")
        
        # Pivot data for easier manipulation
        price_data = raw_data.pivot(index='Date', columns='Symbol', values='AdjClose')
        dividend_data = raw_data.pivot(index='Date', columns='Symbol', values='Dividend')
        
        # Fill any missing data with forward fill
        price_data = price_data.ffill().dropna()
        dividend_data = dividend_data.fillna(0)
        
        print(f"Optimized backtesting portfolio with {len(price_data)} trading days")
        print(f"Assets: {symbols}")
        print(f"Allocation: {allocation}")
        
        # Calculate portfolio performance using vectorized operations
        portfolio_results = self._calculate_portfolio_performance_vectorized(
            price_data, dividend_data, allocation, initial_value, rebalance_frequency, include_daily_data
        )
        
        return portfolio_results
    
    def _calculate_portfolio_performance_vectorized(self, price_data: pd.DataFrame, 
                                                   dividend_data: pd.DataFrame,
                                                   allocation: Dict[str, float], 
                                                   initial_value: float,
                                                   rebalance_freq: str,
                                                   include_daily_data: bool = False) -> Dict:
        """VECTORIZED portfolio performance calculation with exact original logic match"""
        
        # Convert to numpy arrays for vectorized operations
        dates = price_data.index
        if not isinstance(dates, pd.DatetimeIndex):
            dates = pd.to_datetime(dates)
        
        symbols = list(allocation.keys())
        n_days, n_assets = price_data.shape
        
        # Pre-compute allocation arrays
        weights = np.array([allocation[symbol] for symbol in symbols])
        
        # Convert data to numpy arrays for speed
        prices = price_data[symbols].values
        dividends = dividend_data[symbols].values
        
        # Get rebalancing dates using EXACT original logic
        rebalance_dates = self._get_rebalance_dates_exact(dates, rebalance_freq)
        rebalance_date_set = set(rebalance_dates)
        
        # Initialize tracking arrays
        portfolio_values = np.zeros(n_days)
        shares = np.zeros(n_assets)
        
        # Calculate initial share positions
        first_prices = prices[0]
        target_values = initial_value * weights
        shares = target_values / first_prices
        
        print(f"Initial shares (exact): {dict(zip(symbols, shares))}")
        
        # VECTORIZED DAILY CALCULATION with exact original logic
        for i in range(n_days):
            daily_prices = prices[i]
            daily_dividends = dividends[i]
            
            # Calculate portfolio value (vectorized)
            portfolio_value = np.sum(shares * daily_prices)
            
            # Calculate and reinvest dividend income (vectorized)
            dividend_income = np.sum(shares * daily_dividends)
            
            if dividend_income > 0:
                # Reinvest dividends proportionally (vectorized)
                dividends_to_reinvest = dividend_income * weights
                additional_shares = dividends_to_reinvest / daily_prices
                shares += additional_shares
                
                # Recalculate portfolio value after dividend reinvestment
                portfolio_value = np.sum(shares * daily_prices)
            
            portfolio_values[i] = portfolio_value
            
            # Rebalance if needed using EXACT original logic
            if i > 0 and dates[i].date() in rebalance_date_set:
                target_values = portfolio_value * weights
                shares = target_values / daily_prices
        
        # Calculate daily returns (vectorized)
        daily_returns = np.concatenate([[0], np.diff(portfolio_values) / portfolio_values[:-1]])
        
        # Create results DataFrame
        portfolio_df = pd.DataFrame({
            'Date': dates,
            'Portfolio_Value': portfolio_values,
            'Daily_Return': daily_returns
        })
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics(portfolio_df, initial_value)
        
        result = {
            'portfolio_history': portfolio_df,
            'performance_metrics': metrics,
            'final_value': portfolio_values[-1],
            'total_return': (portfolio_values[-1] - initial_value) / initial_value,
            'rebalance_dates': rebalance_dates
        }
        
        # Add daily data if requested (for recovery analysis)
        if include_daily_data:
            daily_data = []
            for i, date in enumerate(dates):
                cumulative_return = (portfolio_values[i] - initial_value) / initial_value
                daily_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'portfolio_value': portfolio_values[i],
                    'daily_return': daily_returns[i],
                    'cumulative_return': cumulative_return
                })
            result['daily_data'] = daily_data
            
        return result
    
    def _get_rebalance_dates_exact(self, dates: pd.DatetimeIndex, frequency: str) -> List[date]:
        """Get list of rebalancing dates (EXACT original logic)"""
        rebalance_dates = []
        
        if frequency == 'monthly':
            for year in range(dates.min().year, dates.max().year + 1):
                for month in range(1, 13):
                    month_dates = dates[(dates.year == year) & (dates.month == month)]
                    if len(month_dates) > 0:
                        rebalance_dates.append(month_dates[0].date())
        
        elif frequency == 'quarterly':
            for year in range(dates.min().year, dates.max().year + 1):
                for quarter_month in [1, 4, 7, 10]:
                    quarter_dates = dates[(dates.year == year) & (dates.month == quarter_month)]
                    if len(quarter_dates) > 0:
                        rebalance_dates.append(quarter_dates[0].date())
        
        elif frequency == 'annual':
            for year in range(dates.min().year, dates.max().year + 1):
                year_dates = dates[dates.year == year]
                if len(year_dates) > 0:
                    rebalance_dates.append(year_dates[0].date())
        
        return rebalance_dates[1:]  # Skip first date - EXACT original behavior
    
    def _calculate_performance_metrics(self, portfolio_df: pd.DataFrame, 
                                     initial_value: float) -> Dict[str, float]:
        """Calculate performance metrics (optimized with vectorized operations)"""
        
        # Use numpy arrays for vectorized calculations
        daily_returns = portfolio_df['Daily_Return'].values[1:]  # Skip first day
        portfolio_values = portfolio_df['Portfolio_Value'].values
        
        # Time period
        start_date = portfolio_df['Date'].iloc[0]
        end_date = portfolio_df['Date'].iloc[-1]
        years = (end_date - start_date).days / 365.25
        
        # Ensure we have valid data
        if years <= 0:
            raise ValueError(f"Invalid time period: {years} years")
        
        # Helper function to safely convert values that might be NaN/inf
        def safe_float(value, default=0.0):
            """Convert to safe float that can be JSON serialized"""
            if value is None or np.isnan(value) or np.isinf(value):
                return default
            return float(value)
        
        # Total return
        total_return = (portfolio_values[-1] - initial_value) / initial_value
        
        # CAGR
        cagr = (portfolio_values[-1] / initial_value) ** (1 / years) - 1
        
        # Volatility (annualized) - vectorized
        volatility = np.std(daily_returns, ddof=1) * np.sqrt(252)
        
        # Sharpe Ratio
        risk_free_rate = 0.02
        excess_return = cagr - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Maximum Drawdown - vectorized
        peak_values = np.maximum.accumulate(portfolio_values)
        drawdowns = (portfolio_values - peak_values) / peak_values
        max_drawdown = np.min(drawdowns)
        
        # Sortino Ratio - vectorized
        downside_returns = daily_returns[daily_returns < 0]
        downside_volatility = np.std(downside_returns, ddof=1) * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0
        
        # Win rate - vectorized
        win_rate = np.mean(daily_returns > 0) if len(daily_returns) > 0 else 0
        
        # Average gain/loss - vectorized
        positive_returns = daily_returns[daily_returns > 0]
        negative_returns = daily_returns[daily_returns < 0]
        
        avg_gain = np.mean(positive_returns) if len(positive_returns) > 0 else 0
        avg_loss = np.mean(negative_returns) if len(negative_returns) > 0 else 0
        
        return {
            'cagr': round(safe_float(cagr), 4),
            'total_return': round(safe_float(total_return), 4),
            'volatility': round(safe_float(volatility), 4),
            'sharpe_ratio': round(safe_float(sharpe_ratio), 4),
            'max_drawdown': round(safe_float(max_drawdown), 4),
            'sortino_ratio': round(safe_float(sortino_ratio), 4),
            'win_rate': round(safe_float(win_rate), 4),
            'avg_daily_gain': round(safe_float(avg_gain), 6),
            'avg_daily_loss': round(safe_float(avg_loss), 6),
            'years': round(safe_float(years), 2),
            'total_trading_days': len(portfolio_values)
        }
    
    def generate_allocation_hash(self, allocation: Dict[str, float]) -> str:
        """Generate unique hash for portfolio allocation for caching"""
        import hashlib
        
        sorted_allocation = {k: v for k, v in sorted(allocation.items())}
        allocation_str = str(sorted_allocation)
        
        return hashlib.sha256(allocation_str.encode()).hexdigest()
    
    def get_cached_portfolio_snapshot(self, allocation: Dict[str, float]) -> Optional:
        """Retrieve cached portfolio snapshot by allocation (compatibility method)"""
        # For now, return None to disable caching and use fresh calculations
        # The optimized engine is fast enough that caching is less critical
        return None
    
    def save_portfolio_snapshot(self, allocation: Dict[str, float], 
                               performance_metrics: Dict[str, float]) -> bool:
        """Save portfolio snapshot (compatibility method)"""
        # For now, don't save snapshots since the optimized engine is fast enough
        return True
