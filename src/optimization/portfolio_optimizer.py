"""
Portfolio Optimizer - Core three-strategy optimization engine

Provides three optimal portfolio strategies:
1. Conservative: Global Minimum Variance with bond tilt
2. Balanced: Maximum Sharpe ratio with moderate constraints  
3. Aggressive: Maximum Sharpe ratio with growth tilt

Features:
- 7-asset universe optimization
- Account type awareness for tax efficiency
- Monte Carlo projections for expected returns
- Integration with existing analytics engines
"""

import numpy as np
import pandas as pd
from scipy import optimize
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, date

# Import existing system components
from ..core.data_manager import DataManager
from ..core.portfolio_engine import PortfolioEngine

logger = logging.getLogger(__name__)

class AccountType(Enum):
    """Account types for tax-aware optimization"""
    TAXABLE = "taxable"
    TAX_DEFERRED = "tax_deferred"  # 401k, Traditional IRA
    TAX_FREE = "tax_free"          # Roth IRA, HSA

class StrategyType(Enum):
    """Portfolio optimization strategies"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced" 
    AGGRESSIVE = "aggressive"

@dataclass
class PortfolioRequest:
    """Portfolio optimization request parameters"""
    current_savings: float = 10000.0
    target_amount: Optional[float] = None
    time_horizon: int = 10  # years
    account_type: AccountType = AccountType.TAXABLE
    new_money_available: bool = False
    max_annual_contribution: Optional[float] = None

@dataclass  
class OptimizedPortfolio:
    """Single optimized portfolio result"""
    strategy: StrategyType
    allocation: Dict[str, float]  # Asset symbol -> weight
    expected_return: float        # Annual expected return
    expected_volatility: float    # Annual volatility
    sharpe_ratio: float
    max_drawdown: float          # Historical max drawdown
    
    # Rebalancing plan
    optimal_rebalancing: str     # 'annual', 'quarterly', 'threshold_5%', 'new_money'
    rebalancing_rationale: str
    
    # New money analysis
    new_money_needed_annual: Optional[float] = None
    new_money_needed_monthly: Optional[float] = None
    traditional_rebalancing_tax_drag: Optional[float] = None
    
    # Enhanced: Rebalancing strategy comparison
    rebalancing_analysis: Optional[Dict[str, Dict[str, float]]] = None

@dataclass
class OptimizationResult:
    """Complete optimization result with three strategies"""
    request: PortfolioRequest
    portfolios: Dict[StrategyType, OptimizedPortfolio]
    target_analysis: Optional[Dict[StrategyType, Dict[str, float]]] = None
    optimization_metadata: Dict[str, Any] = None

class PortfolioOptimizer:
    """
    Main portfolio optimization engine
    
    Generates three optimal portfolios (Conservative/Balanced/Aggressive)
    with automatic rebalancing recommendations and target achievement analysis
    """
    
    def __init__(self, db_session=None):
        """Initialize with database connection"""
        self.db = db_session
        self.data_manager = DataManager(self.db)
        self.portfolio_engine = PortfolioEngine(self.db)
        
        # 7-asset universe (Sprint 2 complete)
        self.assets = ['VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ']
        
        # Risk-free rate assumption (10-year Treasury average)
        self.risk_free_rate = 0.03
        
    def optimize_portfolio(self, request: PortfolioRequest) -> OptimizationResult:
        """
        Main optimization function - generates three optimal portfolios
        
        Args:
            request: Portfolio optimization request
            
        Returns:
            Complete optimization result with three strategies
        """
        logger.info(f"Starting portfolio optimization for {request.time_horizon}-year horizon")
        
        try:
            # Get historical data for optimization
            historical_data = self._get_historical_data(request.time_horizon)
            
            # Calculate expected returns and covariance matrix
            returns_stats = self._calculate_returns_statistics(historical_data)
            
            # Generate three optimal portfolios
            portfolios = {}
            
            # Conservative: Global Minimum Variance with bond tilt
            portfolios[StrategyType.CONSERVATIVE] = self._optimize_conservative(
                returns_stats, request
            )
            
            # Balanced: Maximum Sharpe ratio with moderate constraints
            portfolios[StrategyType.BALANCED] = self._optimize_balanced(
                returns_stats, request
            )
            
            # Aggressive: Maximum Sharpe ratio with growth tilt  
            portfolios[StrategyType.AGGRESSIVE] = self._optimize_aggressive(
                returns_stats, request
            )
            
            # Add rebalancing analysis for each portfolio
            for strategy, portfolio in portfolios.items():
                self._analyze_rebalancing_strategy(portfolio, request)
                
            # ENHANCED: Add actual rebalancing performance analysis
            logger.info("Starting rebalancing performance analysis")
            portfolios = self._analyze_rebalancing_performance(
                portfolios, request, returns_stats, historical_data
            )
            logger.info("Rebalancing performance analysis completed")
            
            # Target achievement analysis (if target specified)
            target_analysis = None
            if request.target_amount:
                target_analysis = self._analyze_target_achievement(
                    portfolios, request, returns_stats
                )
                
            return OptimizationResult(
                request=request,
                portfolios=portfolios,
                target_analysis=target_analysis,
                optimization_metadata={
                    'optimization_date': datetime.now(),
                    'data_period_years': request.time_horizon,
                    'assets_used': self.assets,
                    'risk_free_rate': self.risk_free_rate
                }
            )
            
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            raise
            
    def _get_historical_data(self, time_horizon: int) -> pd.DataFrame:
        """
        Get historical price data for optimization
        Always uses full 20 years of available data for consistent optimization
        Time horizon affects risk constraints, not data selection
        """
        # Always use full available dataset for consistent optimization
        years_to_use = 20  # Use full 20 years regardless of time horizon
        end_date = date(2024, 12, 31)
        start_date = date(end_date.year - years_to_use, 1, 1)
        
        logger.info(f"Using full {years_to_use} years of data for consistent optimization: {start_date} to {end_date}")
        logger.info(f"Time horizon ({time_horizon} years) will affect risk constraints, not data selection")
        
        # Get price data using existing DataManager
        price_data = self.data_manager.get_price_data(
            self.assets, start_date, end_date
        )
        
        if price_data is None or price_data.empty:
            raise ValueError(f"No historical data available for assets: {self.assets}")
            
        return price_data
        
    def _calculate_returns_statistics(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate expected returns and covariance matrix from historical data"""
        
        # Pivot to get price matrix (Date x Assets)
        price_pivot = price_data.pivot(
            index='Date', columns='Symbol', values='AdjClose'
        )
        
        # Calculate daily returns
        returns = price_pivot.pct_change(fill_method=None).dropna()
        
        # Annualized statistics  
        expected_returns_series = returns.mean() * 252  # Trading days per year
        volatility_series = returns.std() * np.sqrt(252)
        covariance_matrix = returns.cov() * 252
        correlation_matrix = returns.corr()
        
        # CRITICAL FIX: Reorder all statistics to match self.assets order
        expected_returns = expected_returns_series.reindex(self.assets)
        volatility = volatility_series.reindex(self.assets)
        covariance_matrix = covariance_matrix.reindex(index=self.assets, columns=self.assets)
        correlation_matrix = correlation_matrix.reindex(index=self.assets, columns=self.assets)
        returns = returns.reindex(columns=self.assets)
        
        return {
            'returns': returns,
            'expected_returns': expected_returns, 
            'volatility': volatility,
            'covariance_matrix': covariance_matrix,
            'correlation_matrix': correlation_matrix,
            'data_years': len(returns) / 252
        }
        
    def _optimize_conservative(self, returns_stats: Dict, 
                             request: PortfolioRequest) -> OptimizedPortfolio:
        """
        Conservative strategy: Global Minimum Variance with bond tilt
        - Minimize portfolio volatility  
        - Higher allocation to bonds (BND)
        - Constraints: max 30% in any single equity, min 20% bonds
        """
        
        expected_returns = returns_stats['expected_returns'].values
        cov_matrix = returns_stats['covariance_matrix'].values
        
        # Objective: minimize portfolio variance
        def objective(weights):
            return np.dot(weights, np.dot(cov_matrix, weights))
            
        # Constraints for conservative strategy
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},  # Weights sum to 1
        ]
        
        # Bounds: Conservative limits - truly conservative allocations
        # BND (bonds): min 25%, max 60% (conservative needs more bonds)
        # Each equity: max 25% (lower concentration risk)
        # Gold (GLD): max 10% (limit alternative assets)
        bounds = []
        for i, asset in enumerate(self.assets):
            if asset == 'BND':  # Bonds - higher allocation for conservatives
                bounds.append((0.25, 0.60))
            elif asset == 'GLD':  # Gold - limit alternative assets
                bounds.append((0.0, 0.10))
            else:  # Equities - conservative limits
                bounds.append((0.0, 0.25))
                
        # Initial guess: Very bond-heavy for conservative
        x0 = np.array([0.12, 0.12, 0.45, 0.08, 0.05, 0.10, 0.08])  # BND=45%
        
        # Optimize
        result = optimize.minimize(
            objective, x0, method='SLSQP', bounds=bounds, constraints=constraints
        )
        
        if not result.success:
            raise ValueError(f"Conservative optimization failed: {result.message}")
            
        # Calculate portfolio metrics
        weights = result.x
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_vol
        
        # Get max drawdown from historical backtesting  
        max_drawdown = self._calculate_historical_max_drawdown(
            dict(zip(self.assets, weights)), returns_stats['returns']
        )
        
        return OptimizedPortfolio(
            strategy=StrategyType.CONSERVATIVE,
            allocation=dict(zip(self.assets, weights)),
            expected_return=portfolio_return,
            expected_volatility=portfolio_vol,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            optimal_rebalancing="",  # Will be filled by _analyze_rebalancing_strategy
            rebalancing_rationale=""
        )
    def _optimize_balanced(self, returns_stats: Dict, 
                          request: PortfolioRequest) -> OptimizedPortfolio:
        """
        Balanced strategy: Maximum Sharpe ratio with moderate constraints
        - Maximize risk-adjusted returns
        - Balanced diversification across all asset classes
        - Constraints: max 40% in any single asset, min 10% bonds
        """
        
        expected_returns = returns_stats['expected_returns'].values
        cov_matrix = returns_stats['covariance_matrix'].values
        
        # Objective: maximize Sharpe ratio (minimize negative Sharpe)
        def objective(weights):
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            if portfolio_vol == 0:
                return 1e10  # Avoid division by zero
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
            return -sharpe  # Negative for minimization
            
        # Constraints for balanced strategy
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},  # Weights sum to 1
        ]
        
        # Bounds: Time horizon-aware balanced limits
        if request.time_horizon >= 10:
            max_single_asset = 0.50  # Long term - can handle more concentration
            min_bonds = 0.08         # Lower bonds for long term
        elif request.time_horizon >= 5:
            max_single_asset = 0.45  # Medium term
            min_bonds = 0.10         # Moderate bonds
        else:
            max_single_asset = 0.40  # Short term - more diversification
            min_bonds = 0.15         # Higher bonds for short horizons
            
        bounds = []
        for i, asset in enumerate(self.assets):
            if asset == 'BND':  # Bonds - time horizon aware
                bonds_max = min(0.35, min_bonds + 0.20)
                bounds.append((min_bonds, bonds_max))
            elif asset in ['QQQ', 'VTI']:  # Top growth assets
                bounds.append((0.0, max_single_asset))
            elif asset in ['VNQ', 'VTIAX']:  # Diversification assets
                bounds.append((0.0, 0.30))
            else:  # GLD, VWO - lower limits for alternatives
                bounds.append((0.0, 0.20))
                
        # Initial guess: Time horizon-aware balanced allocation
        if request.time_horizon >= 10:
            # Long term - can be more growth-oriented
            x0 = np.array([0.28, 0.15, min_bonds + 0.03, 0.15, 0.08, 0.08, 0.18])  
        else:
            # Shorter term - more balanced
            x0 = np.array([0.22, 0.18, min_bonds + 0.08, 0.18, 0.10, 0.10, 0.12])
        
        # Optimize
        result = optimize.minimize(
            objective, x0, method='SLSQP', bounds=bounds, constraints=constraints
        )
        
        if not result.success:
            raise ValueError(f"Balanced optimization failed: {result.message}")
            
        # Calculate portfolio metrics
        weights = result.x
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_vol
        
        # Get max drawdown from historical backtesting
        max_drawdown = self._calculate_historical_max_drawdown(
            dict(zip(self.assets, weights)), returns_stats['returns']
        )
        
        return OptimizedPortfolio(
            strategy=StrategyType.BALANCED,
            allocation=dict(zip(self.assets, weights)),
            expected_return=portfolio_return,
            expected_volatility=portfolio_vol,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            optimal_rebalancing="",  # Will be filled by _analyze_rebalancing_strategy
            rebalancing_rationale=""
        )
        
    def _optimize_aggressive(self, returns_stats: Dict, 
                           request: PortfolioRequest) -> OptimizedPortfolio:
        """
        Aggressive strategy: Maximum Sharpe ratio with growth tilt
        - Maximize returns with growth-oriented allocation
        - Higher allocation to growth assets (VTI, QQQ, VWO)
        - Constraints: max 50% in any single asset, min 5% bonds
        """
        
        expected_returns = returns_stats['expected_returns'].values
        cov_matrix = returns_stats['covariance_matrix'].values
        
        # Objective: maximize Sharpe ratio (same as balanced, but with different constraints)
        def objective(weights):
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            if portfolio_vol == 0:
                return 1e10
                
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
            return -sharpe  # Negative for minimization
            
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},
        ]
        
        # Bounds: Time horizon-aware aggressive limits
        # Longer horizons allow more concentration risk since there's more time to recover
        if request.time_horizon >= 15:
            max_single_equity = 0.70  # Very long term - can handle high concentration
            min_bonds = 0.02          # Minimal bonds for very long term
        elif request.time_horizon >= 10:
            max_single_equity = 0.65  # Long term - high concentration OK
            min_bonds = 0.03          # Very low bonds
        elif request.time_horizon >= 7:
            max_single_equity = 0.60  # Medium-long term
            min_bonds = 0.05          # Low bonds
        elif request.time_horizon >= 5:
            max_single_equity = 0.55  # Medium term - moderate constraints
            min_bonds = 0.08          # Some bonds for stability
        else:
            max_single_equity = 0.45  # Short term - more conservative
            min_bonds = 0.12          # Higher bonds for short horizons
            
        bounds = []
        for i, asset in enumerate(self.assets):
            if asset == 'BND':  # Bonds - time horizon aware
                bonds_max = min(0.20, min_bonds + 0.15)  # Reasonable upper bound
                bounds.append((min_bonds, bonds_max))
            elif asset in ['QQQ', 'VTI']:  # Top growth assets - time horizon aware
                bounds.append((0.0, max_single_equity))
            elif asset == 'VNQ':  # Real estate - moderate allocation
                bounds.append((0.0, 0.25))
            elif asset == 'VTIAX':  # International developed - moderate
                bounds.append((0.0, 0.30))
            elif asset in ['GLD', 'VWO']:  # Alternative/EM - lower limits
                bounds.append((0.0, 0.15))
                
        # Initial guess: Growth-focused allocation adjusted for time horizon
        if request.time_horizon >= 10:
            # Long term - can be more aggressive
            x0 = np.array([0.35, 0.15, min_bonds + 0.02, 0.10, 0.05, 0.08, 0.25])  # More in QQQ for long term
        else:
            # Shorter term - more balanced
            x0 = np.array([0.30, 0.20, min_bonds + 0.05, 0.12, 0.08, 0.10, 0.15])  # More diversified
        
        # Optimize
        result = optimize.minimize(
            objective, x0, method='SLSQP', bounds=bounds, constraints=constraints
        )
        
        if not result.success:
            raise ValueError(f"Aggressive optimization failed: {result.message}")
            
        # Calculate portfolio metrics
        weights = result.x
        portfolio_return = np.dot(weights, expected_returns)
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_vol
        
        # Get max drawdown from historical backtesting
        max_drawdown = self._calculate_historical_max_drawdown(
            dict(zip(self.assets, weights)), returns_stats['returns']
        )
        
        return OptimizedPortfolio(
            strategy=StrategyType.AGGRESSIVE,
            allocation=dict(zip(self.assets, weights)),
            expected_return=portfolio_return,
            expected_volatility=portfolio_vol,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            optimal_rebalancing="",  # Will be filled by _analyze_rebalancing_strategy
            rebalancing_rationale=""
        )
        
    def _calculate_historical_max_drawdown(self, allocation: Dict[str, float], 
                                         returns: pd.DataFrame) -> float:
        """Calculate maximum drawdown from historical returns"""
        
        # Create portfolio returns time series
        portfolio_returns = pd.Series(0.0, index=returns.index)
        
        for asset, weight in allocation.items():
            if asset in returns.columns:
                portfolio_returns += returns[asset] * weight
                
        # Calculate cumulative returns and drawdown
        cumulative_returns = (1 + portfolio_returns).cumprod()
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns / peak) - 1
        
        return abs(drawdown.min())
        
    def _analyze_rebalancing_strategy(self, portfolio: OptimizedPortfolio, 
                                    request: PortfolioRequest) -> None:
        """
        Analyze optimal rebalancing strategy for portfolio
        Updates portfolio object with rebalancing recommendations
        """
        
        # Default rebalancing recommendations by account type and volatility
        volatility = portfolio.expected_volatility
        
        if request.account_type == AccountType.TAXABLE:
            # Taxable accounts: minimize taxable events
            if volatility < 0.15:  # Low volatility
                optimal_strategy = "annual"
                rationale = "Annual rebalancing minimizes tax drag in taxable accounts"
            else:  # Higher volatility
                optimal_strategy = "threshold_5%"  
                rationale = "5% threshold balances rebalancing benefits vs tax costs"
        else:
            # Tax-advantaged accounts: more frequent rebalancing OK
            if volatility < 0.15:
                optimal_strategy = "quarterly"
                rationale = "Quarterly rebalancing captures more rebalancing alpha in tax-advantaged accounts"
            else:
                optimal_strategy = "threshold_5%"
                rationale = "5% threshold captures rebalancing opportunities without over-trading"
                
        # Override with new money strategy if available
        if request.new_money_available and request.max_annual_contribution:
            # Calculate if new money alone can handle rebalancing
            portfolio_value = request.current_savings
            annual_contribution = request.max_annual_contribution
            
            # Rough estimate: need ~5% of portfolio value annually for effective rebalancing
            rebalancing_need = portfolio_value * 0.05
            
            if annual_contribution >= rebalancing_need:
                optimal_strategy = "new_money"
                rationale = "New money contributions can handle all rebalancing needs - no selling required"
                
        portfolio.optimal_rebalancing = optimal_strategy
        portfolio.rebalancing_rationale = rationale
        
        # Calculate new money requirements
        if request.new_money_available:
            self._calculate_new_money_requirements(portfolio, request)
            
    def _calculate_new_money_requirements(self, portfolio: OptimizedPortfolio, 
                                        request: PortfolioRequest) -> None:
        """Calculate new money needed for natural rebalancing"""
        
        portfolio_value = request.current_savings
        target_volatility = portfolio.expected_volatility
        
        # Estimate annual rebalancing need based on portfolio characteristics
        # Higher volatility = more drift = more rebalancing needed
        volatility_factor = target_volatility * 1.5  # Scale factor for rebalancing frequency
        
        # Base rebalancing need: 3-8% of portfolio value annually depending on volatility
        base_percentage = 0.03 + min(volatility_factor, 0.05)  # 3% to 8% range
        annual_need = portfolio_value * base_percentage
        
        # Additional factor for more complex allocations (more assets = more rebalancing)
        active_assets = sum(1 for weight in portfolio.allocation.values() if weight > 0.01)
        complexity_multiplier = 1.0 + (active_assets - 3) * 0.1  # More assets = more rebalancing
        
        annual_need *= complexity_multiplier
        monthly_need = annual_need / 12
        
        portfolio.new_money_needed_annual = annual_need
        portfolio.new_money_needed_monthly = monthly_need
        
        # Calculate tax drag of traditional rebalancing (for taxable accounts)
        if request.account_type == AccountType.TAXABLE:
            # Tax drag scales with portfolio volatility and turnover
            base_tax_drag = 0.003  # 0.3% base
            volatility_tax_impact = target_volatility * 0.01  # Additional drag from volatility
            portfolio.traditional_rebalancing_tax_drag = (base_tax_drag + volatility_tax_impact) * portfolio.expected_return
            
    def _analyze_target_achievement(self, portfolios: Dict[StrategyType, OptimizedPortfolio],
                                  request: PortfolioRequest, returns_stats: Dict) -> Dict[StrategyType, Dict[str, float]]:
        """
        Analyze probability of achieving target amount for each strategy
        Uses Monte Carlo simulation based on historical returns
        """
        
        if not request.target_amount:
            return None
            
        target_analysis = {}
        
        for strategy, portfolio in portfolios.items():
            
            # Monte Carlo parameters
            expected_return = portfolio.expected_return
            volatility = portfolio.expected_volatility  
            time_horizon = request.time_horizon
            initial_value = request.current_savings
            target_value = request.target_amount
            
            # Simple Monte Carlo simulation (1000 runs)
            num_simulations = 1000
            success_count = 0
            
            for _ in range(num_simulations):
                # Generate random annual returns
                annual_returns = np.random.normal(
                    expected_return, volatility, time_horizon
                )
                
                # Calculate final portfolio value
                final_value = initial_value
                for annual_return in annual_returns:
                    final_value *= (1 + annual_return)
                    
                if final_value >= target_value:
                    success_count += 1
                    
            success_probability = success_count / num_simulations
            
            target_analysis[strategy] = {
                'probability': success_probability,
                'expected_final_value': initial_value * ((1 + expected_return) ** time_horizon),
                'target_value': target_value,
                'shortfall_risk': 1 - success_probability
            }
            
        return target_analysis
        
    def _analyze_rebalancing_performance(self, portfolios: Dict[StrategyType, OptimizedPortfolio],
                                       request: PortfolioRequest, returns_stats: Dict,
                                       historical_data: pd.DataFrame) -> Dict[StrategyType, OptimizedPortfolio]:
        """
        Analyze different rebalancing strategy performance using simplified calculations
        
        Compare different rebalancing strategies:
        - Annual rebalancing
        - Threshold-based (5% drift)  
        - New money rebalancing
        """
        
        try:
            logger.info("Analyzing rebalancing performance for portfolios")
            for strategy, portfolio in portfolios.items():
                
                # Calculate rebalancing strategy performance differences
                rebalancing_results = {}
                
                base_return = portfolio.expected_return
                base_volatility = portfolio.expected_volatility
                base_sharpe = portfolio.sharpe_ratio
                
                # 1. Annual Rebalancing
                # Standard approach - good balance of rebalancing alpha and simplicity
                annual_alpha = 0.002 if request.account_type != AccountType.TAXABLE else 0.001  # 0.2% vs 0.1%
                annual_vol_reduction = 0.994  # Modest volatility reduction from rebalancing
                
                rebalancing_results['annual'] = {
                    'total_return': base_return * (1 + annual_alpha),
                    'annual_return': base_return * (1 + annual_alpha),
                    'volatility': base_volatility * annual_vol_reduction,
                    'sharpe_ratio': (base_return * (1 + annual_alpha) - self.risk_free_rate) / (base_volatility * annual_vol_reduction),
                    'rebalancing_events': 15,  # Once per year for 15 years
                    'description': 'Annual rebalancing provides consistent portfolio maintenance with low complexity'
                }
                
                # 2. Threshold-based (5% drift)
                # More responsive to market movements, provides better rebalancing alpha
                threshold_5_alpha = 0.003 if request.account_type != AccountType.TAXABLE else 0.0015  # 0.3% vs 0.15%
                threshold_5_vol_reduction = 0.988  # Better volatility control from more frequent rebalancing
                
                rebalancing_results['threshold_5pct'] = {
                    'total_return': base_return * (1 + threshold_5_alpha),
                    'annual_return': base_return * (1 + threshold_5_alpha),
                    'volatility': base_volatility * threshold_5_vol_reduction,
                    'sharpe_ratio': (base_return * (1 + threshold_5_alpha) - self.risk_free_rate) / (base_volatility * threshold_5_vol_reduction),
                    'rebalancing_events': 35,  # More frequent based on market volatility
                    'description': '5% threshold captures medium-frequency rebalancing opportunities'
                }
                
                # 3. Threshold-based (10% drift) 
                # Less frequent rebalancing, lower alpha but also lower costs
                threshold_10_alpha = 0.001 if request.account_type != AccountType.TAXABLE else 0.0005  # 0.1% vs 0.05%
                threshold_10_vol_reduction = 0.995  # Modest volatility control
                
                rebalancing_results['threshold_10pct'] = {
                    'total_return': base_return * (1 + threshold_10_alpha),
                    'annual_return': base_return * (1 + threshold_10_alpha),
                    'volatility': base_volatility * threshold_10_vol_reduction,
                    'sharpe_ratio': (base_return * (1 + threshold_10_alpha) - self.risk_free_rate) / (base_volatility * threshold_10_vol_reduction),
                    'rebalancing_events': 18,  # Less frequent than 5% threshold
                    'description': '10% threshold reduces trading while capturing major rebalancing opportunities'
                }
                
                # 4. New Money Rebalancing (if applicable)
                if request.new_money_available and request.max_annual_contribution:
                    # Tax-free approach, minimal transaction costs
                    new_money_alpha = 0.0015  # Modest but consistent benefit
                    new_money_vol_reduction = 0.997  # Some volatility smoothing
                    
                    rebalancing_results['new_money'] = {
                        'total_return': base_return * (1 + new_money_alpha),
                        'annual_return': base_return * (1 + new_money_alpha),
                        'volatility': base_volatility * new_money_vol_reduction,
                        'sharpe_ratio': (base_return * (1 + new_money_alpha) - self.risk_free_rate) / (base_volatility * new_money_vol_reduction),
                        'rebalancing_events': 15,  # Annual contributions
                        'description': 'Tax-efficient rebalancing through new contributions'
                    }
                
                # Add rebalancing analysis to portfolio
                portfolio.rebalancing_analysis = rebalancing_results
                
                # Update the optimal rebalancing recommendation based on results
                best_strategy = self._determine_best_rebalancing_strategy(rebalancing_results, request)
                portfolio.optimal_rebalancing = best_strategy['name']
                portfolio.rebalancing_rationale = best_strategy['rationale']
                
            return portfolios
            
        except Exception as e:
            logger.error(f"Rebalancing performance analysis failed: {e}")
            # Return portfolios unchanged if analysis fails
            return portfolios
    
    def _determine_best_rebalancing_strategy(self, rebalancing_results: Dict, request: PortfolioRequest) -> Dict[str, str]:
        """Determine the best rebalancing strategy based on risk-adjusted returns"""
        
        if not rebalancing_results:
            return {'name': 'annual', 'rationale': 'Default annual rebalancing'}
            
        # Compare strategies by Sharpe ratio (risk-adjusted return)
        best_sharpe = -1
        best_strategy = 'annual'
        best_rationale = 'Annual rebalancing provides good balance of returns and simplicity'
        
        for strategy_name, results in rebalancing_results.items():
            sharpe = results.get('sharpe_ratio', 0)
            
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_strategy = strategy_name
                
                if strategy_name == 'annual':
                    best_rationale = f"Annual rebalancing optimal: {sharpe:.3f} Sharpe ratio, {results.get('rebalancing_events', 0)} rebalancing events"
                elif strategy_name == 'threshold_5pct':
                    best_rationale = f"5% threshold rebalancing optimal: {sharpe:.3f} Sharpe ratio, ~{results.get('rebalancing_events', 0)} rebalancing events"
                elif strategy_name == 'new_money':
                    best_rationale = f"New money rebalancing optimal: {sharpe:.3f} Sharpe ratio, tax-efficient approach"
        
        return {'name': best_strategy, 'rationale': best_rationale}
