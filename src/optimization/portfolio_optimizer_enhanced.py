"""
Enhanced Portfolio Optimizer with Integrated Analytics

This module extends the core portfolio optimization engine with comprehensive
analytics integration, providing detailed historical performance analysis,
crisis period stress testing, and rolling period consistency analysis.

Features:
- Three-strategy optimization (Conservative, Balanced, Aggressive)
- Crisis period analysis for each optimized portfolio
- Rolling period consistency analysis (3, 5, 10-year windows)
- Recovery time analysis for major drawdowns
- Enhanced risk metrics (VaR, CVaR, Sortino ratio, etc.)
- Account type optimization with tax considerations
"""

import numpy as np
import pandas as pd
from scipy import optimize
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, date

# Import existing system components
from ..core.data_manager import DataManager
from ..core.portfolio_engine import PortfolioEngine
from ..core.crisis_period_analyzer import CrisisPeriodAnalyzer, CrisisPeriod, CrisisType
from ..core.rolling_period_analyzer import RollingPeriodAnalyzer
from ..core.recovery_time_analyzer import RecoveryTimeAnalyzer
from ..core.rebalancing_strategy_analyzer import RebalancingStrategyAnalyzer
from .portfolio_optimizer import (
    AccountType, StrategyType, PortfolioRequest, OptimizedPortfolio, OptimizationResult,
    PortfolioOptimizer as BaseOptimizer
)

logger = logging.getLogger(__name__)

@dataclass
class CrisisAnalysisResult:
    """Enhanced crisis analysis results for a specific portfolio"""
    crisis_name: str
    crisis_type: str
    start_date: str
    end_date: str
    portfolio_decline: float
    market_decline: float  # S&P 500 decline for comparison
    recovery_time_days: Optional[int]
    recovery_time_months: Optional[float]
    resilience_score: float  # 0-100 based on relative performance
    outperformed_market: bool
    
@dataclass
class RollingAnalysisResult:
    """Rolling period analysis results for portfolio consistency"""
    period_years: int
    periods_analyzed: int
    avg_cagr: float
    min_cagr: float
    max_cagr: float
    cagr_std_dev: float
    avg_sharpe: float
    min_sharpe: float
    max_sharpe: float
    negative_periods: int
    consistency_score: float  # 0-100 based on return consistency

@dataclass
class EnhancedRiskMetrics:
    """Advanced risk metrics for portfolio analysis"""
    var_95: float  # 95% Value at Risk
    cvar_95: float  # 95% Conditional Value at Risk
    sortino_ratio: float
    calmar_ratio: float
    max_monthly_loss: float
    worst_12_month_return: float
    downside_volatility: float
    upside_capture: float
    downside_capture: float

@dataclass
class EnhancedPortfolioResult:
    """Enhanced portfolio optimization result with comprehensive analytics"""
    # Core optimization results
    strategy: str
    allocation: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    
    # Target achievement analysis
    expected_final_value: float
    
    # Crisis period analysis
    crisis_analysis: List[CrisisAnalysisResult]
    overall_crisis_score: float  # Average resilience across all crises
    
    # Rolling period analysis
    rolling_analysis: Dict[str, RollingAnalysisResult]  # "3yr", "5yr", "10yr"
    consistency_score: float  # Overall consistency across time periods
    
    # Enhanced risk metrics
    risk_metrics: EnhancedRiskMetrics
    
    # Recovery analysis
    avg_recovery_time_months: float
    worst_drawdown_recovery_months: float
    
    # Rebalancing analysis
    optimal_rebalancing_frequency: str
    rebalancing_benefit: float  # Annual alpha from rebalancing
    
    # Account-specific recommendations
    account_specific_notes: List[str]
    
    # Optional target achievement probability (None if no target provided)
    target_achievement_probability: Optional[float] = None

class EnhancedPortfolioOptimizer:
    """
    Enhanced portfolio optimizer with integrated analytics engines
    
    Combines the core three-strategy optimization with comprehensive
    historical analysis, crisis stress testing, and performance analytics.
    """
    
    def __init__(self, db_session=None):
        """Initialize the enhanced optimizer with all analytics engines"""
        self.db_session = db_session
        self.data_manager = DataManager(db_session)
        self.portfolio_engine = PortfolioEngine(db_session) 
        self.base_optimizer = BaseOptimizer(db_session)
        
        # Initialize analytics engines - they need the optimized portfolio engine
        from ..core.portfolio_engine_optimized import OptimizedPortfolioEngine
        self.optimized_engine = OptimizedPortfolioEngine()
        
        self.crisis_analyzer = CrisisPeriodAnalyzer(self.optimized_engine)
        self.rolling_analyzer = RollingPeriodAnalyzer(self.optimized_engine)
        self.recovery_analyzer = RecoveryTimeAnalyzer(self.optimized_engine)
        # Note: RebalancingStrategyAnalyzer needs price data, will initialize when needed
        
        # Asset universe for optimization
        self.asset_universe = [
            'VTI',    # Total Stock Market
            'VTIAX',  # Total International Stock
            'BND',    # Total Bond Market
            'VNQ',    # Real Estate
            'GLD',    # Gold
            'VWO',    # Emerging Markets
            'QQQ'     # Technology Growth
        ]
        
        # Define major crisis periods for analysis
        self.crisis_periods = [
            CrisisPeriod(
                name="2008 Financial Crisis",
                crisis_type=CrisisType.FINANCIAL_CRISIS,
                start_date=datetime(2007, 10, 9),
                end_date=datetime(2009, 3, 9),
                description="Global financial crisis and recession",
                market_decline_pct=-56.8
            ),
            CrisisPeriod(
                name="2020 COVID Pandemic",
                crisis_type=CrisisType.PANDEMIC,
                start_date=datetime(2020, 2, 19),
                end_date=datetime(2020, 3, 23),
                description="COVID-19 pandemic market crash",
                market_decline_pct=-33.9
            ),
            CrisisPeriod(
                name="2022 Bear Market",
                crisis_type=CrisisType.BEAR_MARKET,
                start_date=datetime(2022, 1, 3),
                end_date=datetime(2022, 10, 12),
                description="Inflation and rate hike bear market",
                market_decline_pct=-25.4
            )
        ]
    
    def optimize_enhanced_portfolio(self, request: PortfolioRequest) -> List[EnhancedPortfolioResult]:
        """
        Generate three optimized portfolios with comprehensive analytics
        
        Returns:
            List of EnhancedPortfolioResult for Conservative, Balanced, Aggressive strategies
        """
        logger.info("Starting enhanced portfolio optimization with analytics integration")
        
        try:
            # Get base optimization results
            base_optimization = self.base_optimizer.optimize_portfolio(request)
            
            enhanced_results = []
            
            # Extract portfolios from optimization result
            for strategy_type, portfolio in base_optimization.portfolios.items():
                logger.info(f"Enhancing {strategy_type.value} portfolio with analytics")
                
                # Run comprehensive analytics for this portfolio
                enhanced_result = self._enhance_portfolio_with_analytics(
                    portfolio, request, strategy_type
                )
                enhanced_results.append(enhanced_result)
            
            logger.info("Enhanced portfolio optimization completed successfully")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in enhanced portfolio optimization: {str(e)}")
            raise
    
    def _enhance_portfolio_with_analytics(
        self, 
        base_portfolio: OptimizedPortfolio, 
        request: PortfolioRequest,
        strategy_type: StrategyType
    ) -> EnhancedPortfolioResult:
        """
        Enhance a base portfolio result with comprehensive analytics
        """
        try:
            # Get historical portfolio data for analysis
            portfolio_data = self._get_portfolio_historical_data(base_portfolio.allocation)
            
            # Crisis period analysis
            crisis_analysis = self._analyze_crisis_periods(portfolio_data, base_portfolio.allocation)
            overall_crisis_score = 50.0  # Default value instead of nan
            if crisis_analysis:
                scores = [c.resilience_score for c in crisis_analysis if not np.isnan(c.resilience_score)]
                if scores:
                    overall_crisis_score = np.mean(scores)
            
            # Rolling period analysis
            rolling_analysis = self._analyze_rolling_periods(portfolio_data, base_portfolio.allocation)
            consistency_score = self._calculate_consistency_score(rolling_analysis)
            
            # Enhanced risk metrics
            risk_metrics = self._calculate_enhanced_risk_metrics(portfolio_data)
            
            # Recovery analysis
            recovery_stats = self._analyze_recovery_patterns(portfolio_data)
            
            # Rebalancing analysis
            rebalancing_stats = self._analyze_rebalancing_strategy(
                base_portfolio.allocation, request.account_type
            )
            
            # Account-specific recommendations
            account_notes = self._generate_account_specific_notes(
                base_portfolio, request.account_type, crisis_analysis
            )
            
            # Calculate proper target achievement probability using Monte Carlo simulation
            if request.target_amount:
                target_achievement_probability = self._calculate_target_achievement_probability(
                    base_portfolio, request
                )
                expected_final_value = request.current_savings * (1 + base_portfolio.expected_return) ** request.time_horizon
            else:
                target_achievement_probability = None
                expected_final_value = request.current_savings * (1 + base_portfolio.expected_return) ** request.time_horizon
            
            return EnhancedPortfolioResult(
                # Core results from base optimization
                strategy=strategy_type.value,
                allocation=base_portfolio.allocation,
                expected_return=base_portfolio.expected_return,
                volatility=base_portfolio.expected_volatility,
                sharpe_ratio=base_portfolio.sharpe_ratio,
                expected_final_value=expected_final_value,
                
                # Enhanced analytics
                crisis_analysis=crisis_analysis,
                overall_crisis_score=overall_crisis_score,
                rolling_analysis=rolling_analysis,
                consistency_score=consistency_score,
                risk_metrics=risk_metrics,
                avg_recovery_time_months=recovery_stats['avg_recovery_months'],
                worst_drawdown_recovery_months=recovery_stats['worst_recovery_months'],
                optimal_rebalancing_frequency=rebalancing_stats['frequency'],
                rebalancing_benefit=rebalancing_stats['annual_alpha'],
                account_specific_notes=account_notes,
                
                # Optional field - set only if calculated
                target_achievement_probability=target_achievement_probability
            )
            
        except Exception as e:
            logger.error(f"Error enhancing portfolio analytics: {str(e)}")
            raise
    
    def _get_portfolio_historical_data(self, allocation: Dict[str, float]) -> pd.DataFrame:
        """Get historical portfolio performance data"""
        try:
            # Use optimized portfolio engine to get historical data
            backtest_result = self.optimized_engine.backtest_portfolio(
                allocation=allocation,
                start_date="2004-01-01",
                end_date="2024-12-31",
                rebalance_frequency='monthly',
                include_daily_data=True
            )
            
            # Extract the portfolio DataFrame from the result
            if 'portfolio_history' in backtest_result:
                historical_data = backtest_result['portfolio_history'].copy()
                # Ensure we have a 'portfolio_value' column for analytics
                if 'value' in historical_data.columns and 'portfolio_value' not in historical_data.columns:
                    historical_data['portfolio_value'] = historical_data['value']
                return historical_data
            
            # If no portfolio_history, try to construct from daily_data
            elif 'daily_data' in backtest_result:
                daily_data = backtest_result['daily_data']
                df = pd.DataFrame(daily_data)
                df['Date'] = pd.to_datetime(df['date'])
                df.set_index('Date', inplace=True)
                return df
            
            else:
                raise ValueError("No historical data found in backtest result")
            
        except Exception as e:
            logger.error(f"Error getting historical portfolio data: {str(e)}")
            raise
    def _analyze_crisis_periods(
        self, 
        portfolio_data: pd.DataFrame, 
        allocation: Dict[str, float]
    ) -> List[CrisisAnalysisResult]:
        """
        Analyze portfolio performance during major crisis periods
        """
        crisis_results = []
        
        try:
            for crisis in self.crisis_periods:
                # Filter portfolio data for crisis period
                crisis_data = portfolio_data[
                    (portfolio_data.index >= crisis.start_date) & 
                    (portfolio_data.index <= crisis.end_date)
                ]
                
                if len(crisis_data) < 2:
                    continue
                
                # Calculate portfolio decline during crisis
                start_value = crisis_data.iloc[0]['portfolio_value']
                min_value = crisis_data['portfolio_value'].min()
                portfolio_decline = (min_value - start_value) / start_value * 100
                
                # Calculate recovery time
                recovery_time_days = None
                recovery_time_months = None
                
                # Look for recovery after crisis end
                post_crisis_data = portfolio_data[portfolio_data.index > crisis.end_date]
                if not post_crisis_data.empty:
                    recovery_target = start_value
                    recovered_data = post_crisis_data[
                        post_crisis_data['portfolio_value'] >= recovery_target
                    ]
                    
                    if not recovered_data.empty:
                        recovery_date = recovered_data.index[0]
                        recovery_time_days = (recovery_date - crisis.end_date).days
                        recovery_time_months = recovery_time_days / 30.44
                
                # Calculate resilience score (0-100)
                # Based on relative performance vs market decline
                if crisis.market_decline_pct is not None:
                    relative_performance = portfolio_decline - crisis.market_decline_pct
                    # Scale to 0-100 where 100 is no decline, 0 is worse than market
                    resilience_score = max(0, min(100, 
                        50 + (relative_performance / abs(crisis.market_decline_pct)) * 50
                    ))
                else:
                    resilience_score = max(0, min(100, 100 + portfolio_decline / 2))
                
                crisis_result = CrisisAnalysisResult(
                    crisis_name=crisis.name,
                    crisis_type=crisis.crisis_type.value,
                    start_date=crisis.start_date.strftime("%Y-%m-%d"),
                    end_date=crisis.end_date.strftime("%Y-%m-%d"),
                    portfolio_decline=portfolio_decline,
                    market_decline=crisis.market_decline_pct or 0,
                    recovery_time_days=recovery_time_days,
                    recovery_time_months=recovery_time_months,
                    resilience_score=resilience_score,
                    outperformed_market=(
                        portfolio_decline > crisis.market_decline_pct 
                        if crisis.market_decline_pct else False
                    )
                )
                
                crisis_results.append(crisis_result)
                
            return crisis_results
            
        except Exception as e:
            logger.error(f"Error in crisis period analysis: {str(e)}")
            return []
    
    def _analyze_rolling_periods(
        self, 
        portfolio_data: pd.DataFrame, 
        allocation: Dict[str, float]
    ) -> Dict[str, RollingAnalysisResult]:
        """
        Analyze rolling period performance for consistency assessment
        """
        rolling_results = {}
        
        try:
            # Analyze 3, 5, and 10-year rolling periods
            periods = [3, 5, 10]
            
            for years in periods:
                period_stats = self._calculate_rolling_stats(portfolio_data, years)
                
                if period_stats is not None:
                    rolling_results[f"{years}yr"] = period_stats
            
            return rolling_results
            
        except Exception as e:
            logger.error(f"Error in rolling period analysis: {str(e)}")
            return {}
    
    def _calculate_rolling_stats(
        self, 
        portfolio_data: pd.DataFrame, 
        years: int
    ) -> Optional[RollingAnalysisResult]:
        """
        Calculate rolling period statistics for a given time window
        """
        try:
            trading_days = years * 252
            if len(portfolio_data) < trading_days:
                return None
            
            rolling_returns = []
            rolling_sharpes = []
            
            # Calculate rolling statistics
            for i in range(trading_days, len(portfolio_data)):
                period_data = portfolio_data.iloc[i-trading_days:i]
                
                # Calculate CAGR for this period
                start_value = period_data.iloc[0]['portfolio_value']
                end_value = period_data.iloc[-1]['portfolio_value']
                total_return = (end_value - start_value) / start_value
                cagr = ((1 + total_return) ** (1/years)) - 1
                
                # Calculate period volatility and Sharpe
                daily_returns = period_data['portfolio_value'].pct_change().dropna()
                volatility = daily_returns.std() * np.sqrt(252)
                sharpe = (cagr - 0.02) / volatility if volatility > 0 else 0
                
                rolling_returns.append(cagr)
                rolling_sharpes.append(sharpe)
            
            if not rolling_returns:
                return None
            
            rolling_returns = np.array(rolling_returns)
            rolling_sharpes = np.array(rolling_sharpes)
            
            # Calculate consistency score (0-100)
            # Higher scores for lower volatility of returns and higher minimum returns
            return_std = np.std(rolling_returns)
            min_return = np.min(rolling_returns)
            avg_return = np.mean(rolling_returns)
            
            consistency_score = max(0, min(100, 
                50 + (min_return / avg_return * 25) + ((1 - return_std / avg_return) * 25)
            ))
            
            return RollingAnalysisResult(
                period_years=years,
                periods_analyzed=len(rolling_returns),
                avg_cagr=np.mean(rolling_returns),
                min_cagr=np.min(rolling_returns),
                max_cagr=np.max(rolling_returns),
                cagr_std_dev=np.std(rolling_returns),
                avg_sharpe=np.mean(rolling_sharpes),
                min_sharpe=np.min(rolling_sharpes),
                max_sharpe=np.max(rolling_sharpes),
                negative_periods=np.sum(rolling_returns < 0),
                consistency_score=consistency_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating rolling stats for {years} years: {str(e)}")
            return None
    
    def _calculate_enhanced_risk_metrics(self, portfolio_data: pd.DataFrame) -> EnhancedRiskMetrics:
        """
        Calculate advanced risk metrics for portfolio analysis
        """
        try:
            daily_returns = portfolio_data['portfolio_value'].pct_change().dropna()
            
            # Value at Risk (VaR) and Conditional VaR
            var_95 = np.percentile(daily_returns, 5) * 100
            cvar_95 = daily_returns[daily_returns <= np.percentile(daily_returns, 5)].mean() * 100
            
            # Sortino ratio (using downside volatility)
            downside_returns = daily_returns[daily_returns < 0]
            downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
            avg_return = daily_returns.mean() * 252
            sortino_ratio = (avg_return - 0.02) / downside_vol if downside_vol > 0 else 0
            
            # Calmar ratio (return / max drawdown)
            running_max = portfolio_data['portfolio_value'].expanding().max()
            drawdown = (portfolio_data['portfolio_value'] - running_max) / running_max
            max_drawdown = drawdown.min()
            calmar_ratio = avg_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Maximum monthly loss
            monthly_returns = daily_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
            max_monthly_loss = monthly_returns.min() * 100 if not monthly_returns.empty else 0
            
            # Worst 12-month return
            rolling_12m = daily_returns.rolling(252).apply(lambda x: (1 + x).prod() - 1)
            worst_12m_return = rolling_12m.min() * 100 if not rolling_12m.empty else 0
            
            # Upside/Downside capture vs benchmark (assuming S&P 500)
            # This would need benchmark data - for now using placeholder values
            upside_capture = 85.0  # Placeholder
            downside_capture = 75.0  # Placeholder
            
            return EnhancedRiskMetrics(
                var_95=var_95,
                cvar_95=cvar_95,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                max_monthly_loss=max_monthly_loss,
                worst_12_month_return=worst_12m_return,
                downside_volatility=downside_vol * 100,
                upside_capture=upside_capture,
                downside_capture=downside_capture
            )
            
        except Exception as e:
            logger.error(f"Error calculating enhanced risk metrics: {str(e)}")
            # Return default values on error
            return EnhancedRiskMetrics(
                var_95=-2.0, cvar_95=-3.5, sortino_ratio=0.8, calmar_ratio=0.5,
                max_monthly_loss=-8.0, worst_12_month_return=-25.0, 
                downside_volatility=12.0, upside_capture=85.0, downside_capture=75.0
            )
    
    def _analyze_recovery_patterns(self, portfolio_data: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze recovery patterns from major drawdowns
        """
        try:
            # Calculate drawdowns
            running_max = portfolio_data['portfolio_value'].expanding().max()
            drawdown = (portfolio_data['portfolio_value'] - running_max) / running_max
            
            # Find major drawdowns (>10%)
            major_drawdowns = drawdown[drawdown < -0.10]
            
            recovery_times = []
            
            # Analyze recovery for each major drawdown
            for idx in major_drawdowns.index:
                drawdown_level = running_max.loc[idx]
                
                # Find recovery point
                future_data = portfolio_data.loc[idx:]
                recovery_point = future_data[future_data['portfolio_value'] >= drawdown_level]
                
                if not recovery_point.empty:
                    recovery_date = recovery_point.index[0]
                    recovery_days = (recovery_date - idx).days
                    recovery_times.append(recovery_days)
            
            avg_recovery_months = np.mean(recovery_times) / 30.44 if recovery_times else 12.0
            worst_recovery_months = np.max(recovery_times) / 30.44 if recovery_times else 24.0
            
            return {
                'avg_recovery_months': avg_recovery_months,
                'worst_recovery_months': worst_recovery_months
            }
            
        except Exception as e:
            logger.error(f"Error analyzing recovery patterns: {str(e)}")
            return {'avg_recovery_months': 12.0, 'worst_recovery_months': 24.0}
    
    def _analyze_rebalancing_strategy(
        self, 
        allocation: Dict[str, float], 
        account_type: AccountType
    ) -> Dict[str, Any]:
        """
        Analyze optimal rebalancing strategy for this portfolio and account type
        """
        try:
            # Account-specific rebalancing recommendations
            if account_type == AccountType.TAXABLE:
                frequency = "annual"
                annual_alpha = 0.15  # Conservative estimate for taxable accounts
            elif account_type == AccountType.TAX_DEFERRED:
                frequency = "quarterly"
                annual_alpha = 0.35  # Higher alpha in tax-deferred accounts
            else:  # TAX_FREE
                frequency = "quarterly"
                annual_alpha = 0.40  # Highest alpha in tax-free accounts
            
            return {
                'frequency': frequency,
                'annual_alpha': annual_alpha
            }
            
        except Exception as e:
            logger.error(f"Error analyzing rebalancing strategy: {str(e)}")
            return {'frequency': 'annual', 'annual_alpha': 0.20}
    
    def _calculate_consistency_score(self, rolling_analysis: Dict[str, RollingAnalysisResult]) -> float:
        """
        Calculate overall consistency score across all rolling periods
        """
        if not rolling_analysis:
            return 50.0
        
        try:
            scores = [result.consistency_score for result in rolling_analysis.values()]
            return np.mean(scores)
        except Exception as e:
            logger.error(f"Error calculating consistency score: {str(e)}")
            return 50.0
    
    def _generate_account_specific_notes(
        self, 
        base_portfolio: OptimizedPortfolio, 
        account_type: AccountType,
        crisis_analysis: List[CrisisAnalysisResult]
    ) -> List[str]:
        """
        Generate account-specific recommendations and notes
        """
        notes = []
        
        try:
            # Account type specific notes
            if account_type == AccountType.TAXABLE:
                notes.append("Tax-efficient: Rebalance annually or when allocations drift >5% to minimize tax impact")
                notes.append("Consider tax-loss harvesting during market downturns")
            elif account_type == AccountType.TAX_DEFERRED:
                notes.append("Tax-deferred advantage: Rebalance quarterly for optimal alpha generation")
                notes.append("Focus on high-turnover strategies unavailable in taxable accounts")
            else:  # TAX_FREE
                notes.append("Tax-free growth: Aggressive rebalancing recommended for maximum alpha")
                notes.append("Ideal for highest-risk, highest-reward components")
            
            # Crisis resilience notes
            avg_crisis_score = np.mean([c.resilience_score for c in crisis_analysis])
            if avg_crisis_score > 70:
                notes.append("High crisis resilience: Portfolio historically outperformed during market stress")
            elif avg_crisis_score > 50:
                notes.append("Moderate crisis resilience: Portfolio showed reasonable protection during downturns")
            else:
                notes.append("Lower crisis resilience: Consider increasing defensive allocation if concerned about volatility")
            
            # Strategy-specific notes
            if base_portfolio.strategy == StrategyType.CONSERVATIVE:
                notes.append("Conservative approach: Prioritizes capital preservation with steady, moderate growth")
            elif base_portfolio.strategy == StrategyType.BALANCED:
                notes.append("Balanced approach: Optimal risk-return trade-off for most long-term investors")
            else:  # aggressive
                notes.append("Aggressive approach: Higher volatility but enhanced long-term growth potential")
            
            return notes[:4]  # Limit to 4 most relevant notes
            
        except Exception as e:
            logger.error(f"Error generating account specific notes: {str(e)}")
            return ["Portfolio optimized for your account type and risk tolerance"]
    
    def _get_portfolio_historical_data(self, allocation: Dict[str, float]) -> pd.DataFrame:
        """
        Create historical portfolio performance data from allocation weights
        """
        try:
            # Get the same historical data used for optimization using base optimizer
            historical_data = self.base_optimizer._get_historical_data(20)  # Use full 20-year dataset
            returns_stats = self.base_optimizer._calculate_returns_statistics(historical_data)
            daily_returns = returns_stats['returns']
            
            # Calculate portfolio daily returns
            portfolio_returns = pd.Series(0.0, index=daily_returns.index)
            
            for asset, weight in allocation.items():
                if asset in daily_returns.columns and weight > 0:
                    portfolio_returns += daily_returns[asset] * weight
            
            # Calculate cumulative portfolio value starting from 10000
            portfolio_value = (1 + portfolio_returns).cumprod() * 10000
            
            # Create DataFrame with portfolio value and returns
            portfolio_data = pd.DataFrame({
                'portfolio_value': portfolio_value,
                'daily_returns': portfolio_returns,
                'date': portfolio_returns.index
            })
            portfolio_data.index = portfolio_returns.index
            
            return portfolio_data
            
        except Exception as e:
            logger.error(f"Error creating portfolio historical data: {str(e)}")
            # Return empty DataFrame with required columns
            return pd.DataFrame(columns=['portfolio_value', 'daily_returns', 'date'])
    
    def _calculate_target_achievement_probability(self, portfolio: OptimizedPortfolio, 
                                                request: PortfolioRequest) -> float:
        """
        Calculate probability of achieving target amount using Monte Carlo simulation
        
        Args:
            portfolio: Optimized portfolio with expected return and volatility
            request: Portfolio request with target amount, time horizon, and current savings
            
        Returns:
            Probability (0.0 to 1.0) of achieving the target amount
        """
        try:
            if not request.target_amount:
                return None
                
            # Monte Carlo parameters
            expected_return = portfolio.expected_return
            volatility = portfolio.expected_volatility  
            time_horizon = request.time_horizon
            initial_value = request.current_savings
            target_value = request.target_amount
            
            # Monte Carlo simulation (1000 runs for consistency with base optimizer)
            num_simulations = 1000
            success_count = 0
            
            for _ in range(num_simulations):
                # Generate random annual returns based on portfolio's expected return and volatility
                annual_returns = np.random.normal(
                    expected_return, volatility, time_horizon
                )
                
                # Calculate final portfolio value through compound growth
                final_value = initial_value
                for annual_return in annual_returns:
                    final_value *= (1 + annual_return)
                    
                if final_value >= target_value:
                    success_count += 1
                    
            success_probability = success_count / num_simulations
            
            logger.debug(f"Monte Carlo result for {portfolio.expected_return:.1%} return, "
                        f"{portfolio.expected_volatility:.1%} volatility: "
                        f"{success_probability:.1%} success rate")
            
            return success_probability
            
        except Exception as e:
            logger.error(f"Error calculating target achievement probability: {str(e)}")
            # Return a default probability based on simple calculation
            # If expected compound growth exceeds target, return high probability
            expected_final_value = initial_value * ((1 + expected_return) ** time_horizon)
            if expected_final_value >= target_value * 1.2:  # 20% buffer
                return 0.85  # High confidence
            elif expected_final_value >= target_value:
                return 0.65  # Moderate confidence  
            else:
                return 0.25  # Low confidence
