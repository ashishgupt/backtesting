"""
Enhanced Rebalancing Strategy Analyzer - Sprint 5 Phase 7

Compares rebalancing approaches with honest performance attribution:
- Four rebalancing methods: 5% threshold, 10% threshold, quarterly, annual
- Tax-aware rebalancing for different account types
- Walk-forward analysis of historical performance 2014-2024
- Transaction cost and tax drag calculations
- Strategy recommendation engine

This is part of our intellectual honesty approach - showing users the real
impact of different rebalancing strategies rather than theoretical perfection.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class RebalancingMethod(Enum):
    """Available rebalancing approaches"""
    THRESHOLD_5_PERCENT = "5_percent_threshold"
    THRESHOLD_10_PERCENT = "10_percent_threshold" 
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    NEW_MONEY_ONLY = "new_money_only"  # Tax-aware approach

class AccountType(Enum):
    """Account types with different tax implications"""
    TAXABLE = "taxable"
    TAX_DEFERRED = "tax_deferred"  # 401k, Traditional IRA
    TAX_FREE = "tax_free"  # Roth IRA, Roth 401k

@dataclass
class RebalancingEvent:
    """Single rebalancing transaction"""
    date: datetime
    method: RebalancingMethod
    trigger_reason: str  # "threshold_breach", "quarterly", "annual", "new_money"
    old_allocation: Dict[str, float]
    new_allocation: Dict[str, float]
    transaction_cost: float  # Estimated cost in basis points
    tax_impact: float  # Tax drag in basis points (for taxable accounts)
    total_drag: float  # Combined transaction + tax cost

@dataclass
class RebalancingAnalysis:
    """Complete rebalancing strategy analysis"""
    method: RebalancingMethod
    account_type: AccountType
    start_date: datetime
    end_date: datetime
    
    # Performance metrics
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    
    # Rebalancing specific metrics
    num_rebalances: int
    avg_transaction_cost: float
    total_transaction_costs: float
    total_tax_drag: float
    total_drag: float
    
    # Tracking error vs buy-and-hold
    tracking_error: float
    active_return: float  # Return difference vs buy-and-hold
    
    # Events and timeline
    rebalancing_events: List[RebalancingEvent]
    performance_timeline: pd.DataFrame
    
    # Risk-adjusted metrics
    drag_adjusted_sharpe: float  # Sharpe ratio after costs
    cost_efficiency_ratio: float  # Active return / Total costs
    
class RebalancingAnalyzer:
    """
    Enhanced Rebalancing Strategy Analyzer
    
    Performs honest walk-forward analysis of different rebalancing approaches,
    accounting for transaction costs, tax implications, and real-world constraints.
    """
    
    def __init__(self, historical_data: pd.DataFrame):
        """
        Initialize with historical price data
        
        Args:
            historical_data: DataFrame with columns [date, VTI, VTIAX, BND, VNQ, GLD, VWO, QQQ]
        """
        self.historical_data = historical_data.copy()
        self.historical_data['date'] = pd.to_datetime(self.historical_data['date'])
        self.historical_data = self.historical_data.sort_values('date').reset_index(drop=True)
        
        # Rebalancing cost assumptions (basis points)
        self.transaction_costs = {
            AccountType.TAXABLE: 5.0,  # ETF trading costs
            AccountType.TAX_DEFERRED: 3.0,  # Lower costs in retirement accounts
            AccountType.TAX_FREE: 3.0
        }
        
        # Tax drag assumptions for rebalancing (basis points per trade)
        # Based on typical capital gains rates and average holding periods
        self.tax_drag_rates = {
            "short_term": 25.0,  # <1 year holding, taxed as ordinary income
            "long_term": 15.0,   # >1 year holding, capital gains rate
            "tax_exempt": 0.0    # No tax drag in retirement accounts
        }
        
    def analyze_rebalancing_strategy(
        self, 
        target_allocation: Dict[str, float],
        method: RebalancingMethod,
        account_type: AccountType,
        start_date: str = "2014-01-01",
        end_date: str = "2024-01-01",
        initial_value: float = 100000.0,
        annual_contribution: float = 0.0
    ) -> RebalancingAnalysis:
        """
        Analyze a specific rebalancing strategy with walk-forward simulation
        
        Args:
            target_allocation: Target portfolio weights {symbol: weight}
            method: Rebalancing method to analyze
            account_type: Account type for tax calculations
            start_date: Analysis start date
            end_date: Analysis end date  
            initial_value: Starting portfolio value
            annual_contribution: Annual new money (for new_money_only method)
            
        Returns:
            RebalancingAnalysis with comprehensive results
        """
        logger.info(f"Analyzing {method.value} strategy for {account_type.value} account")
        
        # Filter data to analysis period
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        period_data = self.historical_data[
            (self.historical_data['date'] >= start_dt) & 
            (self.historical_data['date'] <= end_dt)
        ].copy().reset_index(drop=True)
        
        if len(period_data) < 252:  # Need at least 1 year of data
            raise ValueError(f"Insufficient data for analysis period: {len(period_data)} days")
        
        # Initialize portfolio simulation
        portfolio_value = initial_value
        current_allocation = target_allocation.copy()
        rebalancing_events = []
        performance_timeline = []
        
        # Track costs and performance
        total_transaction_costs = 0.0
        total_tax_drag = 0.0
        last_rebalance_date = start_dt
        
        # Process each trading day
        for i, row in period_data.iterrows():
            current_date = row['date']
            
            # Calculate daily returns for each asset
            if i == 0:
                # First day - initialize positions
                asset_values = {symbol: portfolio_value * weight 
                               for symbol, weight in current_allocation.items()}
            else:
                # Update asset values based on returns
                prev_row = period_data.iloc[i-1]
                for symbol in current_allocation.keys():
                    if symbol in row and symbol in prev_row:
                        daily_return = (row[symbol] - prev_row[symbol]) / prev_row[symbol]
                        asset_values[symbol] *= (1 + daily_return)
            
            # Calculate current portfolio value and weights
            portfolio_value = sum(asset_values.values())
            current_weights = {symbol: value / portfolio_value 
                              for symbol, value in asset_values.items()}
            
            # Add annual contribution if applicable (monthly installments)
            if annual_contribution > 0 and current_date.day == 1:  # First of month
                monthly_contribution = annual_contribution / 12
                portfolio_value += monthly_contribution
                
                # For new_money_only, use contributions to rebalance
                if method == RebalancingMethod.NEW_MONEY_ONLY:
                    # Allocate new money to restore target allocation
                    # Calculate how much each asset needs to reach target
                    current_portfolio_value = portfolio_value - monthly_contribution
                    shortfalls = {}
                    total_shortfall = 0
                    
                    for symbol, target_weight in target_allocation.items():
                        current_weight = asset_values[symbol] / current_portfolio_value if current_portfolio_value > 0 else 0
                        weight_diff = target_weight - current_weight
                        if weight_diff > 0:  # Asset is underweight
                            shortfalls[symbol] = weight_diff
                            total_shortfall += weight_diff
                    
                    # Allocate new money proportionally to shortfalls
                    if total_shortfall > 0:
                        for symbol, shortfall in shortfalls.items():
                            contribution_to_asset = monthly_contribution * (shortfall / total_shortfall)
                            asset_values[symbol] += contribution_to_asset
                    else:
                        # If no shortfalls, allocate proportionally to target
                        for symbol in current_allocation:
                            asset_values[symbol] += monthly_contribution * target_allocation[symbol]
                else:
                    # Proportional allocation of new money
                    for symbol in current_allocation:
                        asset_values[symbol] += monthly_contribution * target_allocation[symbol]
            
            # Check if rebalancing is needed
            should_rebalance, trigger_reason = self._should_rebalance(
                current_weights, target_allocation, method, 
                current_date, last_rebalance_date
            )
            
            if should_rebalance and method != RebalancingMethod.NEW_MONEY_ONLY:
                # Execute rebalancing
                rebalance_event = self._execute_rebalancing(
                    current_date, method, trigger_reason,
                    current_weights, target_allocation, 
                    portfolio_value, account_type, last_rebalance_date
                )
                
                rebalancing_events.append(rebalance_event)
                total_transaction_costs += rebalance_event.transaction_cost
                total_tax_drag += rebalance_event.tax_impact
                last_rebalance_date = current_date
                
                # Reset asset values to target allocation
                asset_values = {symbol: portfolio_value * weight 
                               for symbol, weight in target_allocation.items()}
                current_weights = target_allocation.copy()
            
            # Record daily performance
            performance_timeline.append({
                'date': current_date,
                'portfolio_value': portfolio_value,
                'total_costs': total_transaction_costs + total_tax_drag,
                'net_value': portfolio_value - (total_transaction_costs + total_tax_drag),
                **current_weights
            })
        
        # Convert to DataFrame
        performance_df = pd.DataFrame(performance_timeline)
        
        # Calculate final metrics
        return self._calculate_final_metrics(
            method, account_type, start_dt, end_dt,
            performance_df, rebalancing_events,
            total_transaction_costs, total_tax_drag
        )
    
    def _should_rebalance(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float], 
        method: RebalancingMethod,
        current_date: datetime,
        last_rebalance_date: datetime
    ) -> Tuple[bool, str]:
        """
        Determine if rebalancing is needed based on method
        
        Returns:
            Tuple of (should_rebalance, trigger_reason)
        """
        if method == RebalancingMethod.NEW_MONEY_ONLY:
            return False, ""  # Never rebalance, only use new money
        
        elif method == RebalancingMethod.THRESHOLD_5_PERCENT:
            # Check if any asset is >5% away from target
            for symbol, target_weight in target_weights.items():
                current_weight = current_weights.get(symbol, 0.0)
                if abs(current_weight - target_weight) > 0.05:
                    return True, f"5% threshold breach: {symbol}"
            return False, ""
        
        elif method == RebalancingMethod.THRESHOLD_10_PERCENT:
            # Check if any asset is >10% away from target
            for symbol, target_weight in target_weights.items():
                current_weight = current_weights.get(symbol, 0.0)
                if abs(current_weight - target_weight) > 0.10:
                    return True, f"10% threshold breach: {symbol}"
            return False, ""
        
        elif method == RebalancingMethod.QUARTERLY:
            # Rebalance every 3 months
            months_since_last = (current_date - last_rebalance_date).days / 30.44
            if months_since_last >= 3:
                return True, "quarterly_schedule"
            return False, ""
        
        elif method == RebalancingMethod.ANNUAL:
            # Rebalance every 12 months
            months_since_last = (current_date - last_rebalance_date).days / 30.44
            if months_since_last >= 12:
                return True, "annual_schedule" 
            return False, ""
        
        return False, ""
    
    def _execute_rebalancing(
        self,
        date: datetime,
        method: RebalancingMethod,
        trigger_reason: str,
        old_allocation: Dict[str, float],
        new_allocation: Dict[str, float],
        portfolio_value: float,
        account_type: AccountType,
        last_rebalance_date: datetime
    ) -> RebalancingEvent:
        """Execute a rebalancing transaction with cost calculations"""
        
        # Calculate transaction volume (sum of absolute allocation changes)
        total_turnover = sum(abs(new_allocation[symbol] - old_allocation.get(symbol, 0)) 
                           for symbol in new_allocation)
        
        # Transaction costs (basis points of portfolio value)
        transaction_cost_bps = self.transaction_costs[account_type]
        transaction_cost = (transaction_cost_bps / 10000) * portfolio_value * (total_turnover / 2)
        
        # Tax implications for taxable accounts
        tax_impact = 0.0
        if account_type == AccountType.TAXABLE:
            # Estimate tax drag based on holding period and gains
            holding_period_days = (date - last_rebalance_date).days
            
            if holding_period_days < 365:
                # Short-term gains - higher tax rate
                tax_rate_bps = self.tax_drag_rates["short_term"]
            else:
                # Long-term gains - lower tax rate  
                tax_rate_bps = self.tax_drag_rates["long_term"]
            
            # Apply tax drag only to assets being sold (reduced allocations)
            for symbol, new_weight in new_allocation.items():
                old_weight = old_allocation.get(symbol, 0)
                if new_weight < old_weight:  # Selling this asset
                    reduction = old_weight - new_weight
                    tax_impact += (tax_rate_bps / 10000) * portfolio_value * reduction
        
        return RebalancingEvent(
            date=date,
            method=method,
            trigger_reason=trigger_reason,
            old_allocation=old_allocation.copy(),
            new_allocation=new_allocation.copy(),
            transaction_cost=transaction_cost,
            tax_impact=tax_impact,
            total_drag=transaction_cost + tax_impact
        )
    
    def _calculate_final_metrics(
        self,
        method: RebalancingMethod,
        account_type: AccountType,
        start_date: datetime,
        end_date: datetime,
        performance_df: pd.DataFrame,
        rebalancing_events: List[RebalancingEvent],
        total_transaction_costs: float,
        total_tax_drag: float
    ) -> RebalancingAnalysis:
        """Calculate final analysis metrics"""
        
        # Basic performance metrics
        initial_value = performance_df.iloc[0]['portfolio_value']
        final_value = performance_df.iloc[-1]['net_value']
        
        total_return = (final_value - initial_value) / initial_value
        years = (end_date - start_date).days / 365.25
        annualized_return = (1 + total_return) ** (1/years) - 1
        
        # Calculate volatility from daily returns
        performance_df['daily_return'] = performance_df['net_value'].pct_change()
        volatility = performance_df['daily_return'].std() * np.sqrt(252)  # Annualized
        
        # Sharpe ratio (assume 2% risk-free rate)
        sharpe_ratio = (annualized_return - 0.02) / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        running_max = performance_df['net_value'].expanding().max()
        drawdown = (performance_df['net_value'] - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Cost analysis
        total_drag = total_transaction_costs + total_tax_drag
        avg_transaction_cost = (total_transaction_costs / len(rebalancing_events) 
                               if rebalancing_events else 0)
        
        # Calculate buy-and-hold comparison for tracking error
        # This would need the same portfolio tracked without rebalancing
        # For now, use simplified tracking error estimate
        tracking_error = volatility * 0.1  # Simplified estimate
        
        # Cost efficiency
        gross_return = total_return + (total_drag / initial_value)
        active_return = total_return  # vs buy-and-hold (simplified)
        cost_efficiency_ratio = (abs(active_return) / (total_drag / initial_value) 
                                if total_drag > 0 else 999.99)  # Cap at 999.99 instead of infinity
        
        # Drag-adjusted metrics
        drag_adjusted_sharpe = sharpe_ratio  # Already calculated on net returns
        
        return RebalancingAnalysis(
            method=method,
            account_type=account_type,
            start_date=start_date,
            end_date=end_date,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            num_rebalances=len(rebalancing_events),
            avg_transaction_cost=avg_transaction_cost,
            total_transaction_costs=total_transaction_costs,
            total_tax_drag=total_tax_drag,
            total_drag=total_drag,
            tracking_error=tracking_error,
            active_return=active_return,
            rebalancing_events=rebalancing_events,
            performance_timeline=performance_df,
            drag_adjusted_sharpe=drag_adjusted_sharpe,
            cost_efficiency_ratio=cost_efficiency_ratio
        )
    
    def compare_rebalancing_strategies(
        self,
        target_allocation: Dict[str, float],
        account_type: AccountType,
        start_date: str = "2014-01-01", 
        end_date: str = "2024-01-01",
        initial_value: float = 100000.0,
        annual_contribution: float = 0.0
    ) -> Dict[RebalancingMethod, RebalancingAnalysis]:
        """
        Compare all rebalancing methods for a given portfolio and account type
        
        Returns:
            Dictionary mapping each method to its analysis results
        """
        logger.info(f"Comparing all rebalancing strategies for {account_type.value} account")
        
        results = {}
        methods_to_test = list(RebalancingMethod)
        
        for method in methods_to_test:
            try:
                analysis = self.analyze_rebalancing_strategy(
                    target_allocation=target_allocation,
                    method=method,
                    account_type=account_type,
                    start_date=start_date,
                    end_date=end_date,
                    initial_value=initial_value,
                    annual_contribution=annual_contribution
                )
                results[method] = analysis
                logger.info(f"✅ Completed analysis for {method.value}")
                
            except Exception as e:
                logger.error(f"❌ Failed to analyze {method.value}: {str(e)}")
                
        return results
    
    def recommend_rebalancing_strategy(
        self,
        comparison_results: Dict[RebalancingMethod, RebalancingAnalysis],
        account_type: AccountType
    ) -> Tuple[RebalancingMethod, str]:
        """
        Recommend the best rebalancing strategy based on analysis results
        
        Returns:
            Tuple of (recommended_method, explanation)
        """
        if not comparison_results:
            return RebalancingMethod.ANNUAL, "No analysis results available - defaulting to annual rebalancing"
        
        # Score each method based on multiple criteria
        scores = {}
        
        for method, analysis in comparison_results.items():
            score = 0.0
            
            # Reward higher risk-adjusted returns (40% weight)
            if analysis.drag_adjusted_sharpe > 0:
                score += analysis.drag_adjusted_sharpe * 0.4
            
            # Reward cost efficiency (30% weight)  
            if analysis.cost_efficiency_ratio > 0:
                score += min(analysis.cost_efficiency_ratio * 0.1, 0.3)  # Cap at 0.3
            
            # Penalize high total costs (20% weight)
            cost_penalty = (analysis.total_drag / analysis.performance_timeline.iloc[0]['portfolio_value']) * 100
            score -= min(cost_penalty * 0.02, 0.2)  # Max penalty 0.2
            
            # Reward lower volatility for Conservative accounts (10% weight)
            vol_bonus = max(0, (0.15 - analysis.volatility)) * 0.1
            score += vol_bonus
            
            scores[method] = score
        
        # Find best method
        best_method = max(scores.keys(), key=lambda m: scores[m])
        best_analysis = comparison_results[best_method]
        
        # Generate explanation
        explanation = self._generate_recommendation_explanation(
            best_method, best_analysis, account_type, scores
        )
        
        return best_method, explanation
    
    def _generate_recommendation_explanation(
        self,
        method: RebalancingMethod,
        analysis: RebalancingAnalysis,
        account_type: AccountType,
        all_scores: Dict[RebalancingMethod, float]
    ) -> str:
        """Generate human-readable explanation for recommendation"""
        
        explanations = {
            RebalancingMethod.THRESHOLD_5_PERCENT: 
                f"5% threshold rebalancing provided the best balance of return ({analysis.annualized_return:.1%}) "
                f"and cost control ({analysis.num_rebalances} rebalances over the period). "
                f"This approach responds quickly to market moves while avoiding excessive trading costs.",
            
            RebalancingMethod.THRESHOLD_10_PERCENT:
                f"10% threshold rebalancing offered optimal cost efficiency with {analysis.num_rebalances} rebalances "
                f"generating {analysis.annualized_return:.1%} annual returns. The wider bands reduced trading costs "
                f"while still maintaining reasonable portfolio discipline.",
            
            RebalancingMethod.QUARTERLY:
                f"Quarterly rebalancing provided consistent portfolio maintenance with predictable costs. "
                f"With {analysis.num_rebalances} rebalances, it delivered {analysis.annualized_return:.1%} returns "
                f"while maintaining systematic risk control.",
            
            RebalancingMethod.ANNUAL:
                f"Annual rebalancing minimized costs with only {analysis.num_rebalances} rebalances while "
                f"still achieving {analysis.annualized_return:.1%} returns. This approach works well for "
                f"patient investors focused on long-term cost minimization.",
            
            RebalancingMethod.NEW_MONEY_ONLY:
                f"New money rebalancing eliminated transaction costs and tax drag while achieving "
                f"{analysis.annualized_return:.1%} returns. This tax-efficient approach uses regular contributions "
                f"to naturally rebalance the portfolio over time."
        }
        
        base_explanation = explanations.get(method, f"{method.value} was the optimal choice.")
        
        # Add account-specific context
        if account_type == AccountType.TAXABLE:
            if method == RebalancingMethod.NEW_MONEY_ONLY:
                base_explanation += " This is especially valuable in taxable accounts where it avoids capital gains taxes."
            else:
                base_explanation += f" Tax impact: ${analysis.total_tax_drag:,.0f} over the period."
        else:
            base_explanation += " In tax-advantaged accounts, transaction costs are the primary concern."
            
        return base_explanation
