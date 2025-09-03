#!/usr/bin/env python3
"""
🔬 DYNAMIC ASSET ALLOCATION STUDY - SPRINT 8 RESEARCH

Mathematical research experiment comparing:
1. Static Allocation: Fixed allocation optimized once using full historical data
2. Rolling Window Optimization: Re-optimize allocation yearly using rolling historical windows

EXPERIMENT DESIGN:
- Year 1 (2014): Optimize using 2004-2013 data → Get allocation A₁
- Year 2 (2015): Optimize using 2005-2014 data → Get allocation A₂  
- Year 3 (2016): Optimize using 2006-2015 data → Get allocation A₃
- Continue through 2024 with yearly rolling optimization
- Compare Performance: Rolling allocation vs current static approach

PERFORMANCE METRICS:
- Total Return (Rolling vs Static)
- Risk-Adjusted Returns (Sharpe, Sortino ratios)
- Maximum Drawdowns
- Portfolio Volatility
- Transaction Costs (turnover from allocation changes)

Expected Academic Literature Outcomes:
- Rolling optimization: Potential 0.5-1.0% annual alpha improvement
- Higher turnover: More frequent allocation changes = higher costs  
- Regime adaptation: Natural adjustment to market conditions over time
"""

import sys
import os
sys.path.append('/Users/ashish/Claude/backtesting')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import our optimization system
from src.optimization.portfolio_optimizer import PortfolioOptimizer, PortfolioRequest, AccountType

@dataclass
class AllocationResult:
    """Container for allocation optimization results"""
    year: int
    allocation: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    optimization_window: str
    data_start: str
    data_end: str

@dataclass
class PerformanceResult:
    """Container for backtest performance results"""
    strategy_name: str
    total_return: float
    annual_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    turnover: float
    num_rebalances: int

class DynamicAllocationStudy:
    """
    Comprehensive study of dynamic asset allocation vs static allocation
    """
    
    def __init__(self):
        self.optimizer = PortfolioOptimizer()
        self.assets = ['VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ']
        self.study_period_start = "2014-01-01"
        self.study_period_end = "2024-12-31"
        self.optimization_window_years = 10
        self.initial_portfolio_value = 100000.0
        
        # Results storage
        self.rolling_allocations: List[AllocationResult] = []
        self.static_allocation: Optional[AllocationResult] = None
        self.performance_results: Dict[str, PerformanceResult] = {}
        
        print("🔬 DYNAMIC ASSET ALLOCATION STUDY INITIALIZED")
        print("=" * 60)
        print(f"Study Period: {self.study_period_start} to {self.study_period_end}")
        print(f"Assets: {', '.join(self.assets)}")
        print(f"Optimization Window: {self.optimization_window_years} years")
        print(f"Initial Portfolio Value: ${self.initial_portfolio_value:,.0f}")
        print()

    def generate_static_allocation(self) -> AllocationResult:
        """
        Generate static allocation using full historical data (current system approach)
        """
        print("🎯 GENERATING STATIC ALLOCATION (CURRENT SYSTEM)")
        print("-" * 50)
        
        try:
            # Use full historical data available (similar to current system)
            historical_data = self.optimizer._get_historical_data(20)  # Full history
            
            data_start = historical_data['Date'].min().strftime('%Y-%m-%d')
            data_end = historical_data['Date'].max().strftime('%Y-%m-%d')
            
            print(f"Optimization Data Window: {data_start} to {data_end}")
            
            # Create optimization request
            request = PortfolioRequest(
                current_savings=self.initial_portfolio_value,
                time_horizon=10,
                account_type=AccountType.TAXABLE
            )
            
            # Run optimization
            returns_stats = self.optimizer._calculate_returns_statistics(historical_data)
            portfolio = self.optimizer._optimize_balanced(returns_stats, request)
            
            static_result = AllocationResult(
                year=2024,  # Current year
                allocation=portfolio.allocation,
                expected_return=portfolio.expected_return,
                expected_volatility=portfolio.expected_volatility,
                sharpe_ratio=portfolio.expected_return / portfolio.expected_volatility if portfolio.expected_volatility > 0 else 0,
                optimization_window=f"{self.optimization_window_years}+ years",
                data_start=data_start,
                data_end=data_end
            )
            
            print("✅ Static Allocation Generated:")
            print(f"   Expected Return: {static_result.expected_return:.2%}")
            print(f"   Expected Volatility: {static_result.expected_volatility:.2%}")
            print(f"   Expected Sharpe: {static_result.sharpe_ratio:.3f}")
            print("   Allocation:")
            for asset, weight in static_result.allocation.items():
                if weight > 0.01:
                    print(f"     {asset}: {weight:.1%}")
            
            self.static_allocation = static_result
            return static_result
            
        except Exception as e:
            print(f"❌ Error generating static allocation: {e}")
            return None

    def generate_rolling_allocations(self) -> List[AllocationResult]:
        """
        Generate rolling window allocations for each year 2014-2024
        """
        print("\n🔄 GENERATING ROLLING WINDOW ALLOCATIONS")
        print("-" * 50)
        
        rolling_results = []
        
        # Generate allocations for each year
        for year in range(2014, 2025):  # 2014 through 2024
            try:
                print(f"\n📅 Year {year} Optimization:")
                
                # Calculate optimization window: use previous 10 years
                optimization_end_year = year - 1
                optimization_start_year = optimization_end_year - self.optimization_window_years + 1
                
                optimization_start = f"{optimization_start_year}-01-01"
                optimization_end = f"{optimization_end_year}-12-31"
                
                print(f"   Using data: {optimization_start} to {optimization_end}")
                
                # Get historical data for this window
                # Note: We'll simulate this since our _get_historical_data doesn't take date ranges
                # In a real implementation, we'd modify the function to accept date ranges
                
                # For now, we'll use the approach of getting data and filtering
                # This is a simulation of what rolling window optimization would look like
                historical_data = self._get_rolling_historical_data(
                    start_date=optimization_start,
                    end_date=optimization_end
                )
                
                if historical_data is None or len(historical_data) < 250:  # Need at least 1 year of data
                    print(f"   ⚠️  Insufficient data for {year}, skipping...")
                    continue
                
                # Create optimization request
                request = PortfolioRequest(
                    current_savings=self.initial_portfolio_value,
                    time_horizon=10,
                    account_type=AccountType.TAXABLE
                )
                
                # Run optimization on this window
                returns_stats = self.optimizer._calculate_returns_statistics(historical_data)
                portfolio = self.optimizer._optimize_balanced(returns_stats, request)
                
                rolling_result = AllocationResult(
                    year=year,
                    allocation=portfolio.allocation,
                    expected_return=portfolio.expected_return,
                    expected_volatility=portfolio.expected_volatility,
                    sharpe_ratio=portfolio.expected_return / portfolio.expected_volatility if portfolio.expected_volatility > 0 else 0,
                    optimization_window=f"{optimization_start} to {optimization_end}",
                    data_start=optimization_start,
                    data_end=optimization_end
                )
                
                rolling_results.append(rolling_result)
                
                print(f"   ✅ Expected Return: {rolling_result.expected_return:.2%}")
                print(f"   ✅ Expected Volatility: {rolling_result.expected_volatility:.2%}")
                print(f"   ✅ Expected Sharpe: {rolling_result.sharpe_ratio:.3f}")
                
                # Show top 3 allocations
                top_allocations = sorted(rolling_result.allocation.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"   📊 Top allocations: {', '.join([f'{asset}:{weight:.1%}' for asset, weight in top_allocations])}")
                
            except Exception as e:
                print(f"   ❌ Error optimizing for year {year}: {e}")
                continue
        
        print(f"\n✅ Generated {len(rolling_results)} rolling allocations")
        self.rolling_allocations = rolling_results
        return rolling_results

    def _get_rolling_historical_data(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        Get historical data for a specific date range and pivot to wide format for analysis
        """
        try:
            # Get full historical data (in long format)
            full_data = self.optimizer._get_historical_data(20)
            
            # Filter to date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            # Filter data by date range - keep in original long format
            filtered_data = full_data[
                (pd.to_datetime(full_data['Date']) >= start_dt) & 
                (pd.to_datetime(full_data['Date']) <= end_dt)
            ].copy()
            
            return filtered_data if len(filtered_data) > 0 else None
            
        except Exception as e:
            print(f"   ❌ Error filtering data for {start_date} to {end_date}: {e}")
            return None

    def _convert_to_wide_format(self, long_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Convert long format data (Date, Symbol, AdjClose, Dividend) to wide format for simulation
        """
        try:
            # Pivot to wide format for easier analysis
            wide_data = long_data.pivot_table(
                index='Date',
                columns='Symbol', 
                values='AdjClose',
                aggfunc='first'
            ).reset_index()
            
            # Fill any missing data forward
            wide_data = wide_data.fillna(method='ffill')
            
            return wide_data if len(wide_data) > 0 else None
            
        except Exception as e:
            print(f"   ❌ Error converting to wide format: {e}")
            return None

    def simulate_performance(self, allocation_strategy: str = "static") -> PerformanceResult:
        """
        Simulate portfolio performance using either static or rolling allocations
        """
        print(f"\n📊 SIMULATING {allocation_strategy.upper()} STRATEGY PERFORMANCE")
        print("-" * 60)
        
        try:
            # Get historical data for simulation period in long format
            simulation_data_long = self._get_rolling_historical_data(
                self.study_period_start, 
                self.study_period_end
            )
            
            if simulation_data_long is None or len(simulation_data_long) == 0:
                print("❌ No data available for simulation period")
                return None
            
            # Convert to wide format for simulation
            simulation_data = self._convert_to_wide_format(simulation_data_long)
            
            if simulation_data is None or len(simulation_data) == 0:
                print("❌ Failed to convert data to wide format")
                return None
            
            print(f"📊 Simulation data: {len(simulation_data)} days from {simulation_data['Date'].min()} to {simulation_data['Date'].max()}")
            
            # Ensure all required assets are present
            available_assets = [col for col in simulation_data.columns if col != 'Date']
            missing_assets = [asset for asset in self.assets if asset not in available_assets]
            if missing_assets:
                print(f"⚠️  Missing assets in data: {missing_assets}")
            
            # Calculate returns for each available asset
            returns_data = {}
            for asset in self.assets:
                if asset in simulation_data.columns:
                    prices = simulation_data[asset].dropna()
                    if len(prices) > 1:
                        returns = prices.pct_change().dropna()
                        returns_data[asset] = returns
                        print(f"   ✅ {asset}: {len(returns)} return observations")
                    else:
                        print(f"   ❌ {asset}: Insufficient price data")
                else:
                    print(f"   ❌ {asset}: Not found in data")
            
            if not returns_data:
                print("❌ No return data available for simulation")
                return None
            
            # Simulate portfolio performance
            portfolio_values = [self.initial_portfolio_value]
            portfolio_returns = []
            allocation_changes = 0
            current_allocation = None
            
            # Get dates for simulation
            simulation_dates = pd.to_datetime(simulation_data['Date'])
            
            print(f"🔄 Simulating performance over {len(simulation_dates)} days...")
            
            for i in range(1, len(simulation_dates)):  # Start from 1 for returns calculation
                date = simulation_dates.iloc[i]
                year = date.year
                
                # Determine allocation for this year
                if allocation_strategy == "static" and self.static_allocation:
                    allocation = self.static_allocation.allocation
                    
                elif allocation_strategy == "rolling":
                    # Find allocation for this year
                    year_allocation = None
                    for ra in self.rolling_allocations:
                        if ra.year == year:
                            year_allocation = ra.allocation
                            break
                    
                    if year_allocation is None:
                        # Use previous year's allocation or fallback to static
                        if current_allocation:
                            allocation = current_allocation
                        elif self.static_allocation:
                            allocation = self.static_allocation.allocation
                        else:
                            continue
                    else:
                        allocation = year_allocation
                        
                        # Count allocation changes (only at beginning of new year)
                        if (current_allocation and allocation != current_allocation and 
                            date.dayofyear <= 5):  # Only count changes in first few days of year
                            allocation_changes += 1
                        current_allocation = allocation
                else:
                    continue
                
                # Calculate portfolio return for this day
                day_return = 0.0
                total_weight = 0.0
                
                for asset, weight in allocation.items():
                    if asset in returns_data and i-1 < len(returns_data[asset]):
                        try:
                            asset_return = returns_data[asset].iloc[i-1]
                            if not pd.isna(asset_return):
                                day_return += weight * asset_return
                                total_weight += weight
                        except (IndexError, KeyError):
                            continue
                
                # Normalize if weights don't sum to 1 (handle any rounding issues)
                if total_weight > 0 and abs(total_weight - 1.0) > 0.01:
                    day_return = day_return / total_weight
                
                portfolio_returns.append(day_return)
                current_value = portfolio_values[-1] * (1 + day_return)
                portfolio_values.append(current_value)
            
            # Calculate performance metrics
            if len(portfolio_returns) == 0:
                print("❌ No portfolio returns calculated")
                return None
            
            portfolio_returns = np.array(portfolio_returns)
            final_value = portfolio_values[-1]
            
            print(f"✅ Calculated {len(portfolio_returns)} portfolio returns")
            print(f"   Portfolio grew from ${self.initial_portfolio_value:,.0f} to ${final_value:,.0f}")
            
            # Basic metrics
            total_return = (final_value - self.initial_portfolio_value) / self.initial_portfolio_value
            years = len(portfolio_returns) / 252  # Assuming daily data
            annual_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
            
            volatility = np.std(portfolio_returns) * np.sqrt(252) if len(portfolio_returns) > 1 else 0
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
            
            # Downside deviation for Sortino ratio
            downside_returns = portfolio_returns[portfolio_returns < 0]
            downside_deviation = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
            sortino_ratio = annual_return / downside_deviation if downside_deviation > 0 else sharpe_ratio
            
            # Maximum drawdown
            cumulative_values = np.array(portfolio_values)
            running_max = np.maximum.accumulate(cumulative_values)
            drawdown = (cumulative_values - running_max) / running_max
            max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
            
            # Calmar ratio
            calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
            
            # Turnover approximation
            turnover = allocation_changes / years if years > 0 else 0
            
            result = PerformanceResult(
                strategy_name=allocation_strategy,
                total_return=total_return,
                annual_return=annual_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                calmar_ratio=calmar_ratio,
                turnover=turnover,
                num_rebalances=allocation_changes
            )
            
            print(f"✅ {allocation_strategy.upper()} STRATEGY RESULTS:")
            print(f"   Total Return: {result.total_return:.2%}")
            print(f"   Annual Return: {result.annual_return:.2%}")
            print(f"   Volatility: {result.volatility:.2%}")
            print(f"   Sharpe Ratio: {result.sharpe_ratio:.3f}")
            print(f"   Sortino Ratio: {result.sortino_ratio:.3f}")
            print(f"   Max Drawdown: {result.max_drawdown:.2%}")
            print(f"   Calmar Ratio: {result.calmar_ratio:.3f}")
            print(f"   Allocation Changes: {result.num_rebalances}")
            print(f"   Turnover: {result.turnover:.1f}/year")
            
            return result
            
        except Exception as e:
            print(f"❌ Error simulating {allocation_strategy} performance: {e}")
            import traceback
            traceback.print_exc()
            return None

    def compare_strategies(self) -> None:
        """
        Compare static vs rolling allocation strategies
        """
        print("\n🏆 STRATEGY COMPARISON")
        print("=" * 60)
        
        if not self.performance_results:
            print("❌ No performance results to compare. Run simulations first.")
            return
        
        static = self.performance_results.get('static')
        rolling = self.performance_results.get('rolling')
        
        if not static or not rolling:
            print("❌ Need both static and rolling results for comparison")
            return
        
        print(f"{'METRIC':<20} {'STATIC':<12} {'ROLLING':<12} {'DIFFERENCE':<12}")
        print("-" * 60)
        
        metrics = [
            ('Total Return', 'total_return', '.2%'),
            ('Annual Return', 'annual_return', '.2%'),
            ('Volatility', 'volatility', '.2%'),
            ('Sharpe Ratio', 'sharpe_ratio', '.3f'),
            ('Sortino Ratio', 'sortino_ratio', '.3f'),
            ('Max Drawdown', 'max_drawdown', '.2%'),
            ('Calmar Ratio', 'calmar_ratio', '.3f'),
            ('Rebalances', 'num_rebalances', 'd'),
            ('Turnover/Year', 'turnover', '.1f')
        ]
        
        for metric_name, metric_attr, fmt in metrics:
            static_val = getattr(static, metric_attr)
            rolling_val = getattr(rolling, metric_attr)
            
            if 'd' in fmt:
                diff = rolling_val - static_val
                print(f"{metric_name:<20} {static_val:<12{fmt}} {rolling_val:<12{fmt}} {diff:<12}")
            else:
                diff = rolling_val - static_val
                print(f"{metric_name:<20} {static_val:<12{fmt}} {rolling_val:<12{fmt}} {diff:<12.3f}")
        
        # Analysis
        print(f"\n📈 PERFORMANCE ANALYSIS:")
        print("-" * 30)
        
        return_advantage = rolling.annual_return - static.annual_return
        risk_difference = rolling.volatility - static.volatility
        sharpe_advantage = rolling.sharpe_ratio - static.sharpe_ratio
        
        if return_advantage > 0:
            print(f"✅ Rolling allocation outperforms by {return_advantage:.2%} annually")
        else:
            print(f"❌ Rolling allocation underperforms by {abs(return_advantage):.2%} annually")
        
        if risk_difference > 0:
            print(f"⚠️  Rolling allocation has {risk_difference:.2%} higher volatility")
        else:
            print(f"✅ Rolling allocation has {abs(risk_difference):.2%} lower volatility")
        
        if sharpe_advantage > 0:
            print(f"✅ Rolling allocation has better risk-adjusted returns (+{sharpe_advantage:.3f} Sharpe)")
        else:
            print(f"❌ Rolling allocation has worse risk-adjusted returns ({sharpe_advantage:.3f} Sharpe)")
        
        print(f"💸 Rolling strategy requires {rolling.num_rebalances} allocation changes")
        
        # Business conclusions
        print(f"\n🎯 BUSINESS CONCLUSIONS:")
        print("-" * 25)
        
        if sharpe_advantage > 0.1:  # Meaningful improvement
            print("✅ RECOMMENDATION: Implement dynamic allocation")
            print("   • Significant risk-adjusted return improvement")
            print(f"   • Additional alpha: {return_advantage:.2%} annually")
            print("   • Worth the additional complexity")
        elif sharpe_advantage > 0.05:  # Modest improvement
            print("⚠️  RECOMMENDATION: Consider dynamic allocation")
            print("   • Modest improvement in risk-adjusted returns")
            print("   • Evaluate if complexity is worth the benefit")
        else:
            print("❌ RECOMMENDATION: Keep current static approach")
            print("   • No meaningful improvement from dynamic allocation")
            print("   • Static approach is simpler and more reliable")

    def run_complete_study(self) -> Dict:
        """
        Run the complete dynamic allocation study
        """
        print("🚀 STARTING DYNAMIC ASSET ALLOCATION STUDY")
        print("=" * 80)
        
        results = {}
        
        try:
            # Step 1: Generate static allocation (current approach)
            static_allocation = self.generate_static_allocation()
            if not static_allocation:
                print("❌ Failed to generate static allocation")
                return results
            results['static_allocation'] = static_allocation
            
            # Step 2: Generate rolling allocations
            rolling_allocations = self.generate_rolling_allocations()
            if not rolling_allocations:
                print("❌ Failed to generate rolling allocations")
                return results
            results['rolling_allocations'] = rolling_allocations
            
            # Step 3: Simulate static strategy performance
            static_performance = self.simulate_performance("static")
            if static_performance:
                self.performance_results['static'] = static_performance
                results['static_performance'] = static_performance
            
            # Step 4: Simulate rolling strategy performance
            rolling_performance = self.simulate_performance("rolling")
            if rolling_performance:
                self.performance_results['rolling'] = rolling_performance
                results['rolling_performance'] = rolling_performance
            
            # Step 5: Compare strategies
            self.compare_strategies()
            
            return results
            
        except Exception as e:
            print(f"❌ Study failed: {e}")
            import traceback
            traceback.print_exc()
            return results

def main():
    """Run the dynamic allocation study"""
    study = DynamicAllocationStudy()
    results = study.run_complete_study()
    
    if results:
        print(f"\n🎉 STUDY COMPLETED SUCCESSFULLY")
        print(f"✅ Generated static allocation")
        print(f"✅ Generated {len(results.get('rolling_allocations', []))} rolling allocations")
        print(f"✅ Compared strategy performance")
        print(f"✅ Results ready for analysis")
    else:
        print(f"\n❌ STUDY INCOMPLETE")
        print(f"Check logs above for specific issues")

if __name__ == "__main__":
    main()
