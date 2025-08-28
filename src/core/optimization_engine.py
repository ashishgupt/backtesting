"""
OptimizationEngine - Portfolio optimization using Modern Portfolio Theory
"""
import numpy as np
import pandas as pd
from scipy import optimize
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session

from ..models.database import get_db
from .portfolio_engine import PortfolioEngine
from .data_manager import DataManager

class OptimizationEngine:
    """
    Engine for portfolio optimization using Modern Portfolio Theory
    
    Features:
    - Efficient frontier calculation
    - Constrained optimization (min/max allocations)
    - Risk parity portfolios
    - Maximum Sharpe ratio optimization
    """
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.portfolio_engine = PortfolioEngine(self.db)
        self.data_manager = DataManager(self.db)
        
    def calculate_efficient_frontier(self, 
                                   assets: List[str] = None,
                                   start_date: str = "2015-01-02",
                                   end_date: str = "2024-12-31",
                                   num_portfolios: int = 100,
                                   constraints: Dict[str, Dict[str, float]] = None) -> Dict:
        """
        Calculate efficient frontier for given assets
        
        Args:
            assets: List of asset symbols (defaults to VTI, VTIAX, BND)
            start_date: Historical data start date
            end_date: Historical data end date  
            num_portfolios: Number of portfolios to generate along frontier
            constraints: Dict of {symbol: {min: 0.0, max: 1.0}} constraints
            
        Returns:
            Dict with portfolio weights, expected returns, volatilities, and Sharpe ratios
        """
        if assets is None:
            assets = ['VTI', 'VTIAX', 'BND']
            
        # Get historical data and calculate returns
        returns_data = self._get_returns_matrix(assets, start_date, end_date)
        
        if returns_data is None or returns_data.empty:
            raise ValueError("No historical data available for specified assets and date range")
            
        # Calculate expected returns and covariance matrix
        expected_returns = returns_data.mean() * 252  # Annualized
        cov_matrix = returns_data.cov() * 252  # Annualized
        
        # Set up constraints
        asset_constraints = self._setup_constraints(assets, constraints)
        
        # Generate efficient frontier
        portfolios = []
        target_returns = np.linspace(
            expected_returns.min(), 
            expected_returns.max(), 
            num_portfolios
        )
        
        for target_return in target_returns:
            try:
                result = self._optimize_portfolio(
                    expected_returns.values,
                    cov_matrix.values,
                    target_return,
                    asset_constraints
                )
                
                if result.success:
                    weights = dict(zip(assets, result.x))
                    portfolio_return = np.dot(result.x, expected_returns.values)
                    portfolio_vol = np.sqrt(np.dot(result.x, np.dot(cov_matrix.values, result.x)))
                    sharpe_ratio = (portfolio_return - 0.02) / portfolio_vol  # Assuming 2% risk-free rate
                    
                    portfolios.append({
                        'weights': weights,
                        'expected_return': portfolio_return,
                        'volatility': portfolio_vol,
                        'sharpe_ratio': sharpe_ratio
                    })
                    
            except Exception as e:
                print(f"Optimization failed for target return {target_return:.4f}: {e}")
                continue
                
        return {
            'portfolios': portfolios,
            'num_portfolios': len(portfolios),
            'assets': assets,
            'date_range': {'start': start_date, 'end': end_date},
            'expected_returns': expected_returns.to_dict(),
            'correlation_matrix': returns_data.corr().to_dict()
        }
        
    def find_max_sharpe_portfolio(self,
                                  assets: List[str] = None,
                                  start_date: str = "2015-01-02", 
                                  end_date: str = "2024-12-31",
                                  constraints: Dict[str, Dict[str, float]] = None) -> Dict:
        """
        Find portfolio with maximum Sharpe ratio
        
        Args:
            assets: List of asset symbols
            start_date: Historical data start date
            end_date: Historical data end date
            constraints: Asset allocation constraints
            
        Returns:
            Optimal portfolio weights and metrics
        """
        if assets is None:
            assets = ['VTI', 'VTIAX', 'BND']
            
        # Get returns data
        returns_data = self._get_returns_matrix(assets, start_date, end_date)
        expected_returns = returns_data.mean() * 252
        cov_matrix = returns_data.cov() * 252
        
        # Set up constraints  
        asset_constraints = self._setup_constraints(assets, constraints)
        
        # Objective function: negative Sharpe ratio (for minimization)
        def objective(weights):
            portfolio_return = np.dot(weights, expected_returns.values)
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix.values, weights)))
            sharpe = (portfolio_return - 0.02) / portfolio_vol
            return -sharpe  # Negative because we minimize
            
        # Initial guess: equal weights
        x0 = np.array([1.0/len(assets)] * len(assets))
        
        # Optimize
        result = optimize.minimize(
            objective, 
            x0,
            method='SLSQP',
            bounds=asset_constraints,
            constraints={'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        )
        
        if result.success:
            weights = dict(zip(assets, result.x))
            portfolio_return = np.dot(result.x, expected_returns.values)
            portfolio_vol = np.sqrt(np.dot(result.x, np.dot(cov_matrix.values, result.x)))
            sharpe_ratio = (portfolio_return - 0.02) / portfolio_vol
            
            return {
                'weights': weights,
                'expected_return': portfolio_return,
                'volatility': portfolio_vol,
                'sharpe_ratio': sharpe_ratio,
                'optimization_success': True
            }
        else:
            raise ValueError(f"Optimization failed: {result.message}")
            
    def _get_returns_matrix(self, assets: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Get daily returns matrix for assets"""
        from datetime import datetime
        
        # Convert string dates to date objects
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Get all price data at once
        price_data = self.data_manager.get_price_data(assets, start_date_obj, end_date_obj)
        
        if price_data is None or price_data.empty:
            return None
            
        # Pivot to get one column per asset with adjusted close prices
        # Note: DataManager returns columns: Date, Symbol, AdjClose, Dividend
        price_pivot = price_data.pivot(index='Date', columns='Symbol', values='AdjClose')
        
        # Calculate daily returns for each asset
        returns_data = price_pivot.pct_change().dropna()
        
        return returns_data
        
    def _setup_constraints(self, assets: List[str], constraints: Dict = None) -> List[Tuple[float, float]]:
        """Setup optimization constraints for each asset"""
        if constraints is None:
            # Default: no short selling, max 100% in any asset
            return [(0.0, 1.0) for _ in assets]
            
        asset_bounds = []
        for asset in assets:
            if asset in constraints:
                min_weight = constraints[asset].get('min', 0.0)
                max_weight = constraints[asset].get('max', 1.0)
                asset_bounds.append((min_weight, max_weight))
            else:
                asset_bounds.append((0.0, 1.0))
                
        return asset_bounds
        
    def _optimize_portfolio(self, expected_returns: np.ndarray, cov_matrix: np.ndarray, 
                          target_return: float, bounds: List[Tuple[float, float]]) -> optimize.OptimizeResult:
        """Optimize portfolio for target return with minimum risk"""
        
        # Objective: minimize portfolio variance
        def objective(weights):
            return np.dot(weights, np.dot(cov_matrix, weights))
            
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},  # Weights sum to 1
            {'type': 'eq', 'fun': lambda x: np.dot(x, expected_returns) - target_return}  # Target return
        ]
        
        # Initial guess
        x0 = np.array([1.0/len(expected_returns)] * len(expected_returns))
        
        # Optimize
        result = optimize.minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'ftol': 1e-9, 'disp': False}
        )
        
        return result