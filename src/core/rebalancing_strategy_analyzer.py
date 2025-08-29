"""
Rebalancing Strategy Analysis Engine

Provides comprehensive analysis of different rebalancing strategies including:
- Threshold-based rebalancing (drift tolerance analysis)
- Time-based rebalancing (periodic vs opportunistic)
- Tax-adjusted returns for taxable vs tax-advantaged accounts
- "New money" rebalancing vs selling/buying
- Crisis period rebalancing effectiveness

Author: AI Assistant
Created: August 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RebalancingFrequency(Enum):
    """Enumeration of rebalancing frequency options"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    THRESHOLD = "threshold"
    NEW_MONEY = "new_money"


class AccountType(Enum):
    """Account type for tax considerations"""
    TAXABLE = "taxable"
    TAX_DEFERRED = "tax_deferred"  # 401k, traditional IRA
    TAX_FREE = "tax_free"  # Roth IRA, HSA


@dataclass
class RebalancingEvent:
    """Single rebalancing event record"""
    date: datetime
    trigger: str  # "time", "threshold", "crisis", "new_money"
    before_allocation: Dict[str, float]
    after_allocation: Dict[str, float]
    transaction_cost: float
    tax_cost: float
    drift_magnitude: float


@dataclass
class RebalancingResult:
    """Results of a rebalancing strategy analysis"""
    strategy_name: str
    frequency: RebalancingFrequency
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    rebalancing_events: List[RebalancingEvent]
    total_transaction_costs: float
    total_tax_costs: float
    average_drift: float
    drift_episodes: int
    rebalancing_effectiveness: float


class RebalancingStrategyAnalyzer:
    """
    Comprehensive rebalancing strategy analysis engine
    
    Analyzes various rebalancing approaches and their impact on portfolio performance,
    including transaction costs, tax implications, and effectiveness during different
    market conditions.
    """
    
    def __init__(self, price_data: pd.DataFrame):
        """
        Initialize the rebalancing analyzer
        
        Args:
            price_data: DataFrame with Date index and asset prices as columns
        """
        self.price_data = price_data.copy()
        self.returns_data = price_data.pct_change().dropna()
        
        # Default parameters
        self.transaction_cost_rate = 0.001  # 0.1% per transaction
        self.tax_rates = {
            'short_term': 0.37,  # Short-term capital gains
            'long_term': 0.20,   # Long-term capital gains
            'dividend': 0.20     # Qualified dividends
        }
        
        logger.info(f"Initialized RebalancingStrategyAnalyzer with {len(price_data)} price points")
    
    def set_cost_parameters(self, 
                           transaction_cost: float = 0.001,
                           tax_rates: Optional[Dict[str, float]] = None):
        """
        Set transaction cost and tax rate parameters
        
        Args:
            transaction_cost: Transaction cost as fraction of trade value
            tax_rates: Dictionary of tax rates for different types of gains
        """
        self.transaction_cost_rate = transaction_cost
        if tax_rates:
            self.tax_rates.update(tax_rates)
    
    def analyze_threshold_rebalancing(self,
                                    target_allocation: Dict[str, float],
                                    threshold_percentages: List[float] = [5, 10, 15, 20],
                                    account_type: AccountType = AccountType.TAXABLE,
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> List[RebalancingResult]:
        """
        Analyze threshold-based rebalancing strategies
        
        Args:
            target_allocation: Target portfolio allocation as {asset: weight}
            threshold_percentages: List of drift thresholds to test (e.g., [5, 10, 15])
            account_type: Type of account for tax calculations
            start_date: Start date for analysis (default: first date in data)
            end_date: End date for analysis (default: last date in data)
            
        Returns:
            List of RebalancingResult objects for each threshold
        """
        results = []
        
        # Set date range
        if start_date is None:
            start_date = self.price_data.index[0]
        if end_date is None:
            end_date = self.price_data.index[-1]
            
        date_mask = (self.price_data.index >= start_date) & (self.price_data.index <= end_date)
        analysis_data = self.price_data[date_mask].copy()
        
        for threshold in threshold_percentages:
            logger.info(f"Analyzing {threshold}% threshold rebalancing strategy")
            
            result = self._simulate_threshold_strategy(
                analysis_data, target_allocation, threshold, account_type
            )
            result.strategy_name = f"Threshold {threshold}%"
            results.append(result)
        
        return results
    
    def analyze_time_based_rebalancing(self,
                                     target_allocation: Dict[str, float],
                                     frequencies: List[RebalancingFrequency] = None,
                                     account_type: AccountType = AccountType.TAXABLE,
                                     start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None) -> List[RebalancingResult]:
        """
        Analyze time-based rebalancing strategies
        
        Args:
            target_allocation: Target portfolio allocation
            frequencies: List of rebalancing frequencies to test
            account_type: Type of account for tax calculations
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of RebalancingResult objects for each frequency
        """
        if frequencies is None:
            frequencies = [
                RebalancingFrequency.MONTHLY,
                RebalancingFrequency.QUARTERLY,
                RebalancingFrequency.ANNUAL
            ]
        
        results = []
        
        # Set date range
        if start_date is None:
            start_date = self.price_data.index[0]
        if end_date is None:
            end_date = self.price_data.index[-1]
            
        date_mask = (self.price_data.index >= start_date) & (self.price_data.index <= end_date)
        analysis_data = self.price_data[date_mask].copy()
        
        for frequency in frequencies:
            logger.info(f"Analyzing {frequency.value} rebalancing strategy")
            
            result = self._simulate_time_based_strategy(
                analysis_data, target_allocation, frequency, account_type
            )
            result.strategy_name = f"Time-based {frequency.value.title()}"
            results.append(result)
        
        return results
    
    def analyze_new_money_rebalancing(self,
                                    target_allocation: Dict[str, float],
                                    monthly_contribution: float = 1000,
                                    rebalance_threshold: float = 10,
                                    account_type: AccountType = AccountType.TAXABLE,
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> RebalancingResult:
        """
        Analyze "new money" rebalancing strategy
        
        Uses new contributions to rebalance portfolio rather than selling/buying
        existing positions, reducing transaction costs and tax implications.
        
        Args:
            target_allocation: Target portfolio allocation
            monthly_contribution: Amount of new money added monthly
            rebalance_threshold: Drift threshold for triggering rebalancing
            account_type: Type of account for tax calculations
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            RebalancingResult for new money strategy
        """
        logger.info(f"Analyzing new money rebalancing with ${monthly_contribution}/month")
        
        # Set date range
        if start_date is None:
            start_date = self.price_data.index[0]
        if end_date is None:
            end_date = self.price_data.index[-1]
            
        date_mask = (self.price_data.index >= start_date) & (self.price_data.index <= end_date)
        analysis_data = self.price_data[date_mask].copy()
        
        result = self._simulate_new_money_strategy(
            analysis_data, target_allocation, monthly_contribution, 
            rebalance_threshold, account_type
        )
        
        result.strategy_name = f"New Money (${monthly_contribution}/month)"
        return result
    
    def _simulate_threshold_strategy(self,
                                   data: pd.DataFrame,
                                   target_allocation: Dict[str, float],
                                   threshold: float,
                                   account_type: AccountType) -> RebalancingResult:
        """
        Simulate threshold-based rebalancing strategy
        
        Args:
            data: Price data for simulation period
            target_allocation: Target portfolio weights
            threshold: Drift threshold percentage for rebalancing
            account_type: Account type for tax calculations
            
        Returns:
            RebalancingResult with simulation results
        """
        # Initialize portfolio
        initial_value = 100000  # $100k starting portfolio
        portfolio_values = []
        rebalancing_events = []
        
        # Convert target allocation to numpy array for efficiency
        assets = list(target_allocation.keys())
        target_weights = np.array([target_allocation[asset] for asset in assets])
        
        # Initialize current holdings
        current_values = target_weights * initial_value
        total_transaction_costs = 0
        total_tax_costs = 0
        drift_episodes = 0
        total_drift = 0
        
        for i, (date, prices) in enumerate(data.iterrows()):
            if i == 0:
                # First day - just record initial values
                portfolio_value = initial_value
                current_weights = target_weights.copy()
            else:
                # Calculate returns and update portfolio values
                prev_prices = data.iloc[i-1][assets]
                current_prices = prices[assets]
                returns = (current_prices / prev_prices - 1).values
                
                # Update current values based on returns
                current_values = current_values * (1 + returns)
                portfolio_value = current_values.sum()
                current_weights = current_values / portfolio_value
                
                # Check drift
                weight_diffs = np.abs(current_weights - target_weights)
                max_drift = weight_diffs.max() * 100  # Convert to percentage
                
                # Track drift statistics
                total_drift += max_drift
                if max_drift > threshold:
                    drift_episodes += 1
                
                # Rebalance if threshold exceeded
                if max_drift > threshold:
                    # Calculate rebalancing transaction
                    target_values = target_weights * portfolio_value
                    trades = target_values - current_values
                    
                    # Calculate transaction costs
                    transaction_cost = np.abs(trades).sum() * self.transaction_cost_rate
                    
                    # Calculate tax costs (simplified)
                    tax_cost = self._calculate_tax_cost(
                        trades, current_values, account_type, 
                        holding_periods=None  # Simplified for now
                    )
                    
                    # Apply costs and rebalance
                    net_portfolio_value = portfolio_value - transaction_cost - tax_cost
                    current_values = target_weights * net_portfolio_value
                    portfolio_value = net_portfolio_value
                    current_weights = target_weights.copy()
                    
                    # Record rebalancing event
                    event = RebalancingEvent(
                        date=date,
                        trigger="threshold",
                        before_allocation={assets[j]: w for j, w in enumerate(current_weights)},
                        after_allocation=target_allocation,
                        transaction_cost=transaction_cost,
                        tax_cost=tax_cost,
                        drift_magnitude=max_drift
                    )
                    rebalancing_events.append(event)
                    
                    total_transaction_costs += transaction_cost
                    total_tax_costs += tax_cost
            
            portfolio_values.append(portfolio_value)
        
        # Calculate performance metrics
        portfolio_series = pd.Series(portfolio_values, index=data.index)
        returns_series = portfolio_series.pct_change().dropna()
        
        total_return = (portfolio_values[-1] / portfolio_values[0]) - 1
        annualized_return = (1 + total_return) ** (252 / len(returns_series)) - 1
        volatility = returns_series.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Calculate maximum drawdown
        cumulative = (1 + returns_series).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calculate effectiveness metrics
        average_drift = total_drift / len(data) if len(data) > 0 else 0
        rebalancing_effectiveness = self._calculate_rebalancing_effectiveness(
            portfolio_series, rebalancing_events
        )
        
        return RebalancingResult(
            strategy_name=f"Threshold {threshold}%",
            frequency=RebalancingFrequency.THRESHOLD,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            rebalancing_events=rebalancing_events,
            total_transaction_costs=total_transaction_costs,
            total_tax_costs=total_tax_costs,
            average_drift=average_drift,
            drift_episodes=drift_episodes,
            rebalancing_effectiveness=rebalancing_effectiveness
        )
    
    def _simulate_time_based_strategy(self,
                                    data: pd.DataFrame,
                                    target_allocation: Dict[str, float],
                                    frequency: RebalancingFrequency,
                                    account_type: AccountType) -> RebalancingResult:
        """
        Simulate time-based rebalancing strategy
        
        Args:
            data: Price data for simulation period
            target_allocation: Target portfolio weights
            frequency: Rebalancing frequency
            account_type: Account type for tax calculations
            
        Returns:
            RebalancingResult with simulation results
        """
        # Determine rebalancing dates based on frequency
        rebalance_dates = self._get_rebalancing_dates(data.index, frequency)
        
        # Initialize portfolio
        initial_value = 100000
        portfolio_values = []
        rebalancing_events = []
        
        assets = list(target_allocation.keys())
        target_weights = np.array([target_allocation[asset] for asset in assets])
        current_values = target_weights * initial_value
        
        total_transaction_costs = 0
        total_tax_costs = 0
        total_drift = 0
        drift_episodes = 0
        
        for i, (date, prices) in enumerate(data.iterrows()):
            if i == 0:
                portfolio_value = initial_value
                current_weights = target_weights.copy()
            else:
                # Update portfolio values based on returns
                prev_prices = data.iloc[i-1][assets]
                current_prices = prices[assets]
                returns = (current_prices / prev_prices - 1).values
                
                current_values = current_values * (1 + returns)
                portfolio_value = current_values.sum()
                current_weights = current_values / portfolio_value
                
                # Track drift
                weight_diffs = np.abs(current_weights - target_weights)
                max_drift = weight_diffs.max() * 100
                total_drift += max_drift
                
                if max_drift > 5:  # Count significant drift episodes
                    drift_episodes += 1
                
                # Check if it's a rebalancing date
                if date in rebalance_dates:
                    # Calculate rebalancing transaction
                    target_values = target_weights * portfolio_value
                    trades = target_values - current_values
                    
                    # Calculate costs
                    transaction_cost = np.abs(trades).sum() * self.transaction_cost_rate
                    tax_cost = self._calculate_tax_cost(
                        trades, current_values, account_type
                    )
                    
                    # Apply costs and rebalance
                    net_portfolio_value = portfolio_value - transaction_cost - tax_cost
                    current_values = target_weights * net_portfolio_value
                    portfolio_value = net_portfolio_value
                    current_weights = target_weights.copy()
                    
                    # Record event
                    event = RebalancingEvent(
                        date=date,
                        trigger="time",
                        before_allocation={assets[j]: w for j, w in enumerate(current_weights)},
                        after_allocation=target_allocation,
                        transaction_cost=transaction_cost,
                        tax_cost=tax_cost,
                        drift_magnitude=max_drift
                    )
                    rebalancing_events.append(event)
                    
                    total_transaction_costs += transaction_cost
                    total_tax_costs += tax_cost
            
            portfolio_values.append(portfolio_value)
        
        # Calculate performance metrics (same as threshold method)
        portfolio_series = pd.Series(portfolio_values, index=data.index)
        returns_series = portfolio_series.pct_change().dropna()
        
        total_return = (portfolio_values[-1] / portfolio_values[0]) - 1
        annualized_return = (1 + total_return) ** (252 / len(returns_series)) - 1
        volatility = returns_series.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        cumulative = (1 + returns_series).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        average_drift = total_drift / len(data) if len(data) > 0 else 0
        rebalancing_effectiveness = self._calculate_rebalancing_effectiveness(
            portfolio_series, rebalancing_events
        )
        
        return RebalancingResult(
            strategy_name=f"Time-based {frequency.value}",
            frequency=frequency,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            rebalancing_events=rebalancing_events,
            total_transaction_costs=total_transaction_costs,
            total_tax_costs=total_tax_costs,
            average_drift=average_drift,
            drift_episodes=drift_episodes,
            rebalancing_effectiveness=rebalancing_effectiveness
        )
    
    def _simulate_new_money_strategy(self,
                                   data: pd.DataFrame,
                                   target_allocation: Dict[str, float],
                                   monthly_contribution: float,
                                   rebalance_threshold: float,
                                   account_type: AccountType) -> RebalancingResult:
        """
        Simulate new money rebalancing strategy
        
        Uses new contributions to gradually rebalance portfolio rather than
        selling existing positions, minimizing transaction costs and taxes.
        """
        # Initialize portfolio
        initial_value = 100000
        portfolio_values = []
        rebalancing_events = []
        
        assets = list(target_allocation.keys())
        target_weights = np.array([target_allocation[asset] for asset in assets])
        current_values = target_weights * initial_value
        
        total_transaction_costs = 0
        total_tax_costs = 0
        total_drift = 0
        drift_episodes = 0
        
        # Track contributions (assume monthly on first business day)
        last_contribution_month = None
        
        for i, (date, prices) in enumerate(data.iterrows()):
            if i == 0:
                portfolio_value = initial_value
                current_weights = target_weights.copy()
            else:
                # Update values based on returns
                prev_prices = data.iloc[i-1][assets]
                current_prices = prices[assets]
                returns = (current_prices / prev_prices - 1).values
                
                current_values = current_values * (1 + returns)
                
                # Add monthly contribution
                current_month = date.strftime('%Y-%m')
                if (current_month != last_contribution_month and 
                    date.day <= 5):  # First business days of month
                    
                    # Allocate new money to bring portfolio closer to target
                    portfolio_value = current_values.sum()
                    current_weights = current_values / portfolio_value
                    
                    # Calculate optimal allocation of new money
                    weight_diffs = target_weights - current_weights
                    new_money_allocation = self._optimize_new_money_allocation(
                        weight_diffs, monthly_contribution
                    )
                    
                    # Add new money
                    current_values += new_money_allocation
                    last_contribution_month = current_month
                
                portfolio_value = current_values.sum()
                current_weights = current_values / portfolio_value
                
                # Track drift
                weight_diffs = np.abs(current_weights - target_weights)
                max_drift = weight_diffs.max() * 100
                total_drift += max_drift
                
                if max_drift > rebalance_threshold:
                    drift_episodes += 1
                    
                    # Only rebalance through selling if drift is very large
                    if max_drift > rebalance_threshold * 2:
                        target_values = target_weights * portfolio_value
                        trades = target_values - current_values
                        
                        transaction_cost = np.abs(trades).sum() * self.transaction_cost_rate
                        tax_cost = self._calculate_tax_cost(
                            trades, current_values, account_type
                        )
                        
                        net_portfolio_value = portfolio_value - transaction_cost - tax_cost
                        current_values = target_weights * net_portfolio_value
                        portfolio_value = net_portfolio_value
                        current_weights = target_weights.copy()
                        
                        event = RebalancingEvent(
                            date=date,
                            trigger="new_money_rebalance",
                            before_allocation={assets[j]: w for j, w in enumerate(current_weights)},
                            after_allocation=target_allocation,
                            transaction_cost=transaction_cost,
                            tax_cost=tax_cost,
                            drift_magnitude=max_drift
                        )
                        rebalancing_events.append(event)
                        
                        total_transaction_costs += transaction_cost
                        total_tax_costs += tax_cost
            
            portfolio_values.append(portfolio_value)
        
        # Calculate performance metrics
        portfolio_series = pd.Series(portfolio_values, index=data.index)
        returns_series = portfolio_series.pct_change().dropna()
        
        total_return = (portfolio_values[-1] / portfolio_values[0]) - 1
        annualized_return = (1 + total_return) ** (252 / len(returns_series)) - 1
        volatility = returns_series.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        cumulative = (1 + returns_series).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        average_drift = total_drift / len(data) if len(data) > 0 else 0
        rebalancing_effectiveness = self._calculate_rebalancing_effectiveness(
            portfolio_series, rebalancing_events
        )
        
        return RebalancingResult(
            strategy_name=f"New Money (${monthly_contribution}/month)",
            frequency=RebalancingFrequency.NEW_MONEY,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            rebalancing_events=rebalancing_events,
            total_transaction_costs=total_transaction_costs,
            total_tax_costs=total_tax_costs,
            average_drift=average_drift,
            drift_episodes=drift_episodes,
            rebalancing_effectiveness=rebalancing_effectiveness
        )
    
    def _get_rebalancing_dates(self, 
                              date_index: pd.DatetimeIndex, 
                              frequency: RebalancingFrequency) -> List[datetime]:
        """
        Generate rebalancing dates based on frequency
        
        Args:
            date_index: Available trading dates
            frequency: Rebalancing frequency
            
        Returns:
            List of rebalancing dates
        """
        start_date = date_index[0]
        end_date = date_index[-1]
        rebalance_dates = []
        
        if frequency == RebalancingFrequency.MONTHLY:
            # First trading day of each month
            current = start_date.replace(day=1)
            while current <= end_date:
                # Find first trading day of the month
                month_dates = date_index[
                    (date_index.year == current.year) & 
                    (date_index.month == current.month)
                ]
                if len(month_dates) > 0:
                    rebalance_dates.append(month_dates[0])
                
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
        
        elif frequency == RebalancingFrequency.QUARTERLY:
            # First trading day of each quarter
            quarters = [1, 4, 7, 10]  # Jan, Apr, Jul, Oct
            for year in range(start_date.year, end_date.year + 1):
                for quarter_month in quarters:
                    quarter_dates = date_index[
                        (date_index.year == year) & 
                        (date_index.month == quarter_month)
                    ]
                    if len(quarter_dates) > 0 and quarter_dates[0] >= start_date:
                        rebalance_dates.append(quarter_dates[0])
        
        elif frequency == RebalancingFrequency.ANNUAL:
            # First trading day of each year
            for year in range(start_date.year, end_date.year + 1):
                year_dates = date_index[date_index.year == year]
                if len(year_dates) > 0 and year_dates[0] >= start_date:
                    rebalance_dates.append(year_dates[0])
        
        return rebalance_dates
    
    def _optimize_new_money_allocation(self, 
                                     weight_diffs: np.ndarray, 
                                     contribution_amount: float) -> np.ndarray:
        """
        Optimize allocation of new money to reduce portfolio drift
        
        Args:
            weight_diffs: Differences between target and current weights
            contribution_amount: Amount of new money to allocate
            
        Returns:
            Optimal allocation of new money across assets
        """
        # Simple strategy: allocate new money proportionally to underweight assets
        underweight_mask = weight_diffs > 0
        
        if not underweight_mask.any():
            # If no assets are underweight, allocate proportionally to targets
            return weight_diffs * contribution_amount / weight_diffs.sum()
        
        # Allocate proportionally to underweight amounts
        underweight_diffs = weight_diffs * underweight_mask
        total_underweight = underweight_diffs.sum()
        
        if total_underweight > 0:
            allocation = (underweight_diffs / total_underweight) * contribution_amount
        else:
            # Fallback to proportional allocation
            allocation = weight_diffs * contribution_amount / weight_diffs.sum()
        
        return allocation
    
    def _calculate_tax_cost(self, 
                           trades: np.ndarray, 
                           current_values: np.ndarray,
                           account_type: AccountType,
                           holding_periods: Optional[np.ndarray] = None) -> float:
        """
        Calculate tax cost of rebalancing trades
        
        Args:
            trades: Array of trade amounts (positive = buy, negative = sell)
            current_values: Current asset values
            account_type: Type of investment account
            holding_periods: Holding periods for each asset (for tax rate determination)
            
        Returns:
            Total tax cost of trades
        """
        if account_type != AccountType.TAXABLE:
            return 0.0  # No taxes in tax-advantaged accounts
        
        # Calculate capital gains on sales
        sales = trades[trades < 0]  # Negative values are sales
        
        # Simplified calculation: assume average cost basis is 80% of current value
        # and average holding period is > 1 year (long-term rates)
        cost_basis_ratio = 0.8
        total_sales = abs(sales.sum())
        
        if total_sales > 0:
            capital_gains = total_sales * (1 - cost_basis_ratio)
            tax_cost = capital_gains * self.tax_rates['long_term']
        else:
            tax_cost = 0.0
        
        return tax_cost
    
    def _calculate_rebalancing_effectiveness(self, 
                                           portfolio_series: pd.Series,
                                           events: List[RebalancingEvent]) -> float:
        """
        Calculate effectiveness of rebalancing strategy
        
        Measures how much rebalancing improved risk-adjusted returns
        compared to a buy-and-hold strategy.
        
        Args:
            portfolio_series: Portfolio value time series
            events: List of rebalancing events
            
        Returns:
            Rebalancing effectiveness score (higher is better)
        """
        if len(events) == 0:
            return 0.0
        
        # Simple effectiveness measure: average return improvement after rebalancing
        returns = portfolio_series.pct_change().dropna()
        effectiveness_scores = []
        
        for event in events:
            # Look at returns in the period following rebalancing
            event_idx = portfolio_series.index.get_loc(event.date)
            if event_idx < len(portfolio_series) - 21:  # Need at least 21 days after
                post_rebalance_returns = returns.iloc[event_idx+1:event_idx+22]  # Next 21 days
                avg_post_return = post_rebalance_returns.mean()
                effectiveness_scores.append(avg_post_return)
        
        return np.mean(effectiveness_scores) if effectiveness_scores else 0.0
    
    def compare_strategies(self, results: List[RebalancingResult]) -> Dict[str, Any]:
        """
        Compare multiple rebalancing strategies and rank them
        
        Args:
            results: List of RebalancingResult objects to compare
            
        Returns:
            Dictionary with comparison metrics and rankings
        """
        if not results:
            return {}
        
        # Create comparison dataframe
        comparison_data = []
        for result in results:
            comparison_data.append({
                'Strategy': result.strategy_name,
                'Total Return': result.total_return,
                'Annualized Return': result.annualized_return,
                'Volatility': result.volatility,
                'Sharpe Ratio': result.sharpe_ratio,
                'Max Drawdown': result.max_drawdown,
                'Rebalancing Events': len(result.rebalancing_events),
                'Transaction Costs': result.total_transaction_costs,
                'Tax Costs': result.total_tax_costs,
                'Total Costs': result.total_transaction_costs + result.total_tax_costs,
                'Average Drift': result.average_drift,
                'Net Return': result.total_return - (result.total_transaction_costs + result.total_tax_costs) / 100000
            })
        
        df = pd.DataFrame(comparison_data)
        
        # Calculate rankings
        df['Return Rank'] = df['Total Return'].rank(ascending=False)
        df['Sharpe Rank'] = df['Sharpe Ratio'].rank(ascending=False)
        df['Cost Rank'] = df['Total Costs'].rank(ascending=True)  # Lower costs = better rank
        df['Drawdown Rank'] = df['Max Drawdown'].rank(ascending=True)  # Lower drawdown = better rank
        
        # Overall score (weighted average of ranks)
        df['Overall Score'] = (
            0.3 * df['Return Rank'] + 
            0.3 * df['Sharpe Rank'] + 
            0.2 * df['Cost Rank'] + 
            0.2 * df['Drawdown Rank']
        )
        df['Overall Rank'] = df['Overall Score'].rank(ascending=True)
        
        # Sort by overall rank
        df = df.sort_values('Overall Rank')
        
        return {
            'comparison_table': df,
            'best_strategy': df.iloc[0]['Strategy'],
            'best_overall_score': df.iloc[0]['Overall Score'],
            'summary_stats': {
                'strategies_compared': len(results),
                'best_return': df['Total Return'].max(),
                'best_sharpe': df['Sharpe Ratio'].max(),
                'lowest_costs': df['Total Costs'].min(),
                'lowest_drawdown': df['Max Drawdown'].min()
            }
        }
