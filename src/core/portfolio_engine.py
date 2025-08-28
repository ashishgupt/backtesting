"""
PortfolioEngine - Core backtesting logic for portfolio performance analysis
"""
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.database import get_db
from ..models.schemas import DailyPrice, PortfolioSnapshot
from .data_manager import DataManager

class PortfolioEngine:
    """Core engine for portfolio backtesting and performance analysis"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.data_manager = DataManager(self.db)
        
    def get_portfolio_data(self, symbols: List[str], start_date: str = "2015-01-01", 
                          end_date: str = "2024-12-31") -> pd.DataFrame:
        """
        Get historical data for portfolio backtesting
        
        Returns DataFrame with columns: Date, Symbol, AdjClose, Dividend
        """
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        return self.data_manager.get_price_data(symbols, start, end)
    
    def backtest_portfolio(self, allocation: Dict[str, float], 
                          initial_value: float = 10000, 
                          start_date: str = "2015-01-01",
                          end_date: str = "2024-12-31", 
                          rebalance_frequency: str = "monthly") -> Dict:
        """
        Backtest a portfolio allocation over time
        
        Args:
            allocation: Dict of {symbol: weight} e.g. {'VTI': 0.6, 'VTIAX': 0.3, 'BND': 0.1}
            initial_value: Starting portfolio value in dollars
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)  
            rebalance_frequency: 'monthly', 'quarterly', or 'annual'
            
        Returns:
            Dictionary with backtest results and performance metrics
        """
        
        # Validate allocation sums to 1.0
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
        
        print(f"Backtesting portfolio with {len(price_data)} trading days")
        print(f"Assets: {symbols}")
        print(f"Allocation: {allocation}")
        
        # Calculate daily portfolio performance
        portfolio_results = self._calculate_portfolio_performance(
            price_data, dividend_data, allocation, initial_value, rebalance_frequency
        )
        
        return portfolio_results
    
    def _calculate_portfolio_performance(self, price_data: pd.DataFrame, 
                                       dividend_data: pd.DataFrame,
                                       allocation: Dict[str, float], 
                                       initial_value: float,
                                       rebalance_freq: str) -> Dict:
        """
        Calculate detailed portfolio performance with rebalancing
        
        This is the core calculation engine that handles:
        - Daily portfolio value calculation
        - Periodic rebalancing 
        - Dividend reinvestment
        - Performance metrics calculation
        """
        
        # Initialize portfolio tracking
        dates = price_data.index
        # Convert to DatetimeIndex if needed
        if not isinstance(dates, pd.DatetimeIndex):
            dates = pd.to_datetime(dates)
        
        portfolio_values = []
        daily_returns = []
        
        # Get rebalancing dates
        rebalance_dates = self._get_rebalance_dates(dates, rebalance_freq)
        
        # Initialize positions (shares held)
        current_value = initial_value
        shares = {}
        
        # Calculate initial share positions
        first_prices = price_data.iloc[0]
        for symbol, weight in allocation.items():
            target_value = current_value * weight
            shares[symbol] = target_value / first_prices[symbol]
        
        print(f"Initial shares: {shares}")
        
        # Daily portfolio calculation loop
        for i, date in enumerate(dates):
            daily_prices = price_data.iloc[i]
            daily_dividends = dividend_data.iloc[i]
            
            # Calculate portfolio value
            portfolio_value = sum(shares[symbol] * daily_prices[symbol] for symbol in allocation.keys())
            
            # Add dividend income (reinvested)
            dividend_income = sum(shares[symbol] * daily_dividends[symbol] for symbol in allocation.keys())
            
            # Reinvest dividends proportionally  
            if dividend_income > 0:
                for symbol, weight in allocation.items():
                    dividend_to_reinvest = dividend_income * weight
                    additional_shares = dividend_to_reinvest / daily_prices[symbol]
                    shares[symbol] += additional_shares
            
            # Recalculate value after dividend reinvestment
            portfolio_value = sum(shares[symbol] * daily_prices[symbol] for symbol in allocation.keys())
            
            # Store daily results
            portfolio_values.append(portfolio_value)
            
            # Calculate daily return
            if i > 0:
                daily_return = (portfolio_value - portfolio_values[i-1]) / portfolio_values[i-1]
                daily_returns.append(daily_return)
            
            # Rebalance if needed
            if date in rebalance_dates and i > 0:
                shares = self._rebalance_portfolio(shares, daily_prices, allocation, portfolio_value)
        
        # Create results DataFrame
        portfolio_df = pd.DataFrame({
            'Date': dates,
            'Portfolio_Value': portfolio_values,
            'Daily_Return': [0] + daily_returns  # First day has no return
        })
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics(portfolio_df, initial_value)
        
        return {
            'portfolio_history': portfolio_df,
            'performance_metrics': metrics,
            'final_value': portfolio_values[-1],
            'total_return': (portfolio_values[-1] - initial_value) / initial_value,
            'rebalance_dates': rebalance_dates
        }
    
    def _get_rebalance_dates(self, dates: pd.DatetimeIndex, frequency: str) -> List[date]:
        """Get list of dates when portfolio should be rebalanced"""
        rebalance_dates = []
        
        if frequency == 'monthly':
            # First trading day of each month
            for year in range(dates.min().year, dates.max().year + 1):
                for month in range(1, 13):
                    month_dates = dates[(dates.year == year) & (dates.month == month)]
                    if len(month_dates) > 0:
                        rebalance_dates.append(month_dates[0].date())
        
        elif frequency == 'quarterly':
            # First trading day of each quarter
            for year in range(dates.min().year, dates.max().year + 1):
                for quarter_month in [1, 4, 7, 10]:  # Jan, Apr, Jul, Oct
                    quarter_dates = dates[(dates.year == year) & (dates.month == quarter_month)]
                    if len(quarter_dates) > 0:
                        rebalance_dates.append(quarter_dates[0].date())
        
        elif frequency == 'annual':
            # First trading day of each year
            for year in range(dates.min().year, dates.max().year + 1):
                year_dates = dates[dates.year == year]
                if len(year_dates) > 0:
                    rebalance_dates.append(year_dates[0].date())
        
        return rebalance_dates[1:]  # Skip first date (initial allocation)
    
    def _rebalance_portfolio(self, current_shares: Dict[str, float], 
                           current_prices: pd.Series,
                           target_allocation: Dict[str, float], 
                           total_value: float) -> Dict[str, float]:
        """
        Rebalance portfolio to target allocation
        
        Args:
            current_shares: Current share holdings
            current_prices: Current prices for all assets
            target_allocation: Target allocation weights
            total_value: Current total portfolio value
            
        Returns:
            New share holdings after rebalancing
        """
        new_shares = {}
        
        for symbol, target_weight in target_allocation.items():
            target_value = total_value * target_weight
            new_shares[symbol] = target_value / current_prices[symbol]
        
        return new_shares
    
    def _calculate_performance_metrics(self, portfolio_df: pd.DataFrame, 
                                     initial_value: float) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics
        
        Returns dictionary with:
        - CAGR (Compound Annual Growth Rate)
        - Total Return
        - Volatility (annualized)
        - Sharpe Ratio
        - Maximum Drawdown
        - Sortino Ratio
        """
        
        # Calculate returns
        daily_returns = portfolio_df['Daily_Return'].dropna()
        portfolio_values = portfolio_df['Portfolio_Value']
        
        # Time period
        start_date = portfolio_df['Date'].iloc[0]
        end_date = portfolio_df['Date'].iloc[-1]
        years = (end_date - start_date).days / 365.25
        
        # Total return
        total_return = (portfolio_values.iloc[-1] - initial_value) / initial_value
        
        # CAGR - Compound Annual Growth Rate
        cagr = (portfolio_values.iloc[-1] / initial_value) ** (1 / years) - 1
        
        # Volatility (annualized)
        volatility = daily_returns.std() * np.sqrt(252)  # 252 trading days per year
        
        # Sharpe Ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        excess_return = cagr - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Maximum Drawdown
        peak = portfolio_values.cummax()
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = drawdown.min()
        
        # Sortino Ratio (downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252)
        sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0
        
        # Win rate
        positive_days = len(daily_returns[daily_returns > 0])
        total_days = len(daily_returns)
        win_rate = positive_days / total_days if total_days > 0 else 0
        
        # Average gain/loss
        avg_gain = daily_returns[daily_returns > 0].mean() if len(daily_returns[daily_returns > 0]) > 0 else 0
        avg_loss = daily_returns[daily_returns < 0].mean() if len(daily_returns[daily_returns < 0]) > 0 else 0
        
        return {
            'cagr': round(cagr, 4),
            'total_return': round(total_return, 4),
            'volatility': round(volatility, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'max_drawdown': round(max_drawdown, 4),
            'sortino_ratio': round(sortino_ratio, 4),
            'win_rate': round(win_rate, 4),
            'avg_daily_gain': round(avg_gain, 6),
            'avg_daily_loss': round(avg_loss, 6),
            'years': round(years, 2),
            'total_trading_days': len(portfolio_values)
        }
    
    def generate_allocation_hash(self, allocation: Dict[str, float]) -> str:
        """Generate unique hash for portfolio allocation for caching"""
        import hashlib
        
        # Sort allocation for consistent hashing
        sorted_allocation = {k: v for k, v in sorted(allocation.items())}
        allocation_str = str(sorted_allocation)
        
        return hashlib.sha256(allocation_str.encode()).hexdigest()
    
    def save_portfolio_snapshot(self, allocation: Dict[str, float], 
                               performance_metrics: Dict[str, float]) -> bool:
        """Save portfolio backtest results to cache for faster future access"""
        try:
            allocation_hash = self.generate_allocation_hash(allocation)
            
            # Check if already exists
            existing = self.db.query(PortfolioSnapshot).filter(
                PortfolioSnapshot.allocation_hash == allocation_hash
            ).first()
            
            if existing:
                print(f"Portfolio snapshot already exists for allocation {allocation}")
                return False
            
            # Create new snapshot
            snapshot = PortfolioSnapshot(
                allocation_hash=allocation_hash,
                vti_weight=allocation.get('VTI', 0),
                vtiax_weight=allocation.get('VTIAX', 0),
                bnd_weight=allocation.get('BND', 0),
                total_return=float(performance_metrics.get('total_return')),
                cagr=float(performance_metrics.get('cagr')),
                volatility=float(performance_metrics.get('volatility')),
                max_drawdown=float(performance_metrics.get('max_drawdown')),
                sharpe_ratio=float(performance_metrics.get('sharpe_ratio'))
            )
            
            self.db.add(snapshot)
            self.db.commit()
            
            print(f"Saved portfolio snapshot: {allocation}")
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error saving portfolio snapshot: {e}")
            return False
    
    def get_cached_portfolio_snapshot(self, allocation: Dict[str, float]) -> Optional[PortfolioSnapshot]:
        """
        Retrieve cached portfolio snapshot by allocation
        
        Args:
            allocation: Portfolio allocation dictionary
            
        Returns:
            PortfolioSnapshot if found, None otherwise
        """
        try:
            allocation_hash = self._generate_allocation_hash(allocation)
            
            snapshot = self.db.query(PortfolioSnapshot).filter(
                PortfolioSnapshot.allocation_hash == allocation_hash
            ).first()
            
            return snapshot
            
        except Exception as e:
            print(f"Error retrieving cached portfolio snapshot: {e}")
            return None