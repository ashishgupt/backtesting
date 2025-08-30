"""
Extended Historical Analysis Engine for Portfolio Backtesting

This module provides comprehensive 20-year historical analysis including:
- Market cycle identification and analysis across different economic regimes
- Correlation evolution tracking over extended periods  
- Regime change detection and strategy adaptation alerts
- Long-term vs short-term performance comparisons
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session
from scipy import stats
from scipy.signal import find_peaks
import warnings

from .portfolio_engine_optimized import OptimizedPortfolioEngine
from ..models import get_db, Asset, DailyPrice


@dataclass
class MarketRegime:
    """Information about a detected market regime"""
    start_date: datetime
    end_date: datetime
    regime_type: str  # 'bull', 'bear', 'sideways', 'crisis', 'recovery'
    duration_days: int
    market_return: float
    volatility: float
    description: str


@dataclass
class CorrelationPeriod:
    """Correlation analysis for a specific time period"""
    start_date: datetime
    end_date: datetime
    period_years: int
    correlation_matrix: Dict[str, Dict[str, float]]
    avg_correlation: float
    diversification_ratio: float  # Measure of diversification benefit
    dominant_factor_exposure: float  # How much is driven by single factor


@dataclass  
class ExtendedHistoricalSummary:
    """Comprehensive summary of extended historical analysis"""
    analysis_period_start: datetime
    analysis_period_end: datetime
    total_years: int
    
    # Performance across different periods
    full_period_cagr: float
    first_decade_cagr: float
    second_decade_cagr: float
    
    # Market regime analysis
    market_regimes: List[MarketRegime]
    regime_performance: Dict[str, Dict[str, float]]  # Performance in each regime type
    
    # Correlation evolution
    correlation_periods: List[CorrelationPeriod] 
    correlation_trend: str  # 'increasing', 'decreasing', 'stable'
    diversification_effectiveness: float  # 0-1 score
    
    # Regime change impact
    regime_transition_alpha: float  # Excess return during transitions
    adaptation_recommendations: List[str]
    
    # Risk metrics evolution  
    volatility_clustering_periods: List[Tuple[datetime, datetime]]
    tail_risk_evolution: Dict[str, float]  # VaR evolution over time


class ExtendedHistoricalAnalyzer:
    """
    Advanced 20-year historical analysis engine
    
    Provides comprehensive market cycle analysis, correlation tracking,
    and regime change detection for long-term investment strategy optimization.
    """
    
    def __init__(self):
        self.portfolio_engine = OptimizedPortfolioEngine()
        
    def analyze_extended_historical_performance(
        self,
        allocation: Dict[str, float],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db_session: Session = None
    ) -> ExtendedHistoricalSummary:
        """
        Perform comprehensive 20-year historical analysis
        
        Args:
            allocation: Portfolio allocation weights
            start_date: Analysis start date (defaults to 20 years ago)
            end_date: Analysis end date (defaults to present)
            db_session: Database session
            
        Returns:
            ExtendedHistoricalSummary: Comprehensive analysis results
        """
        try:
            # Set default date range for 20-year analysis
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=20*365)
                
            # Get portfolio data for full period using backtest method
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            backtest_result = self.portfolio_engine.backtest_portfolio(
                allocation=allocation,
                initial_value=10000,
                start_date=start_date_str,
                end_date=end_date_str,
                rebalance_frequency="monthly",
                include_daily_data=True
            )
            
            # Extract daily portfolio values
            portfolio_data = pd.DataFrame(backtest_result['daily_data'])
            portfolio_data['date'] = pd.to_datetime(portfolio_data['date'])
            portfolio_data.set_index('date', inplace=True)
            
            if portfolio_data is None or len(portfolio_data) < 252*10:  # Need at least 10 years
                raise ValueError("Insufficient historical data for extended analysis")
                
            # Perform market regime analysis
            market_regimes = self._detect_market_regimes(portfolio_data)
            regime_performance = self._analyze_regime_performance(portfolio_data, market_regimes, allocation)
            
            # Perform correlation evolution analysis
            correlation_periods = self._analyze_correlation_evolution(allocation, start_date, end_date, db_session)
            correlation_trend, diversification_effectiveness = self._assess_correlation_trends(correlation_periods)
            
            # Analyze regime transitions and adaptation opportunities
            regime_transition_alpha = self._calculate_regime_transition_alpha(portfolio_data, market_regimes)
            adaptation_recommendations = self._generate_adaptation_recommendations(
                market_regimes, correlation_periods, regime_performance
            )
            
            # Calculate performance metrics for different periods
            full_period_cagr = self._calculate_period_cagr(portfolio_data, 0, len(portfolio_data)-1)
            
            # Split into decades for comparison
            mid_point = len(portfolio_data) // 2
            first_decade_cagr = self._calculate_period_cagr(portfolio_data, 0, mid_point)
            second_decade_cagr = self._calculate_period_cagr(portfolio_data, mid_point, len(portfolio_data)-1)
            
            # Analyze volatility clustering and tail risks
            volatility_clustering_periods = self._detect_volatility_clustering(portfolio_data)
            tail_risk_evolution = self._analyze_tail_risk_evolution(portfolio_data)
            
            return ExtendedHistoricalSummary(
                analysis_period_start=start_date,
                analysis_period_end=end_date,
                total_years=round((end_date - start_date).days / 365.25, 1),
                full_period_cagr=full_period_cagr,
                first_decade_cagr=first_decade_cagr,
                second_decade_cagr=second_decade_cagr,
                market_regimes=market_regimes,
                regime_performance=regime_performance,
                correlation_periods=correlation_periods,
                correlation_trend=correlation_trend,
                diversification_effectiveness=diversification_effectiveness,
                regime_transition_alpha=regime_transition_alpha,
                adaptation_recommendations=adaptation_recommendations,
                volatility_clustering_periods=volatility_clustering_periods,
                tail_risk_evolution=tail_risk_evolution
            )
            
        except Exception as e:
            raise Exception(f"Extended historical analysis failed: {str(e)}")
    
    def _detect_market_regimes(self, portfolio_data: pd.DataFrame) -> List[MarketRegime]:
        """
        Detect market regimes using multiple indicators
        
        Uses volatility, drawdowns, and trend analysis to identify:
        - Bull markets (sustained uptrends, low volatility)
        - Bear markets (sustained downtrends, high volatility) 
        - Crisis periods (sharp drawdowns, extreme volatility)
        - Recovery periods (strong rebounds from lows)
        - Sideways markets (low trend, moderate volatility)
        """
        regimes = []
        
        # Calculate rolling metrics for regime detection
        returns = portfolio_data['portfolio_value'].pct_change().fillna(0)
        
        # 252-day (1 year) rolling metrics
        rolling_return = returns.rolling(252).mean() * 252  # Annualized
        rolling_vol = returns.rolling(252).std() * np.sqrt(252)  # Annualized
        rolling_drawdown = self._calculate_rolling_drawdown(portfolio_data['portfolio_value'])
        
        # Define regime thresholds
        BULL_RETURN_THRESHOLD = 0.08  # 8% annual return
        BEAR_RETURN_THRESHOLD = -0.05  # -5% annual return
        HIGH_VOL_THRESHOLD = 0.25  # 25% volatility
        CRISIS_DRAWDOWN_THRESHOLD = 0.20  # 20% drawdown
        
        current_regime = None
        regime_start = None
        
        for i, date in enumerate(portfolio_data.index):
            if i < 252:  # Need full year of data
                continue
                
            annual_return = rolling_return.iloc[i]
            volatility = rolling_vol.iloc[i]
            drawdown = rolling_drawdown.iloc[i]
            
            # Determine regime based on conditions
            if drawdown > CRISIS_DRAWDOWN_THRESHOLD and volatility > HIGH_VOL_THRESHOLD:
                regime_type = 'crisis'
            elif annual_return > BULL_RETURN_THRESHOLD and volatility < HIGH_VOL_THRESHOLD:
                regime_type = 'bull'
            elif annual_return < BEAR_RETURN_THRESHOLD:
                regime_type = 'bear'  
            elif drawdown < 0.05 and annual_return > 0.05:  # Recovery from low drawdown
                regime_type = 'recovery'
            else:
                regime_type = 'sideways'
                
            # Check for regime change
            if regime_type != current_regime:
                # End previous regime
                if current_regime is not None and regime_start is not None:
                    regime_end = date
                    regime_duration = (regime_end - regime_start).days
                    
                    # Calculate regime performance
                    regime_data = portfolio_data.loc[regime_start:regime_end]
                    regime_return = ((regime_data['portfolio_value'].iloc[-1] / 
                                    regime_data['portfolio_value'].iloc[0]) - 1) * 100
                    regime_volatility = (regime_data['portfolio_value'].pct_change()
                                       .std() * np.sqrt(252)) * 100
                    
                    regimes.append(MarketRegime(
                        start_date=regime_start,
                        end_date=regime_end,
                        regime_type=current_regime,
                        duration_days=regime_duration,
                        market_return=regime_return,
                        volatility=regime_volatility,
                        description=self._get_regime_description(current_regime, regime_return, regime_volatility)
                    ))
                
                # Start new regime
                current_regime = regime_type
                regime_start = date
        
        # Handle final regime
        if current_regime is not None and regime_start is not None:
            regime_end = portfolio_data.index[-1]
            regime_duration = (regime_end - regime_start).days
            
            regime_data = portfolio_data.loc[regime_start:regime_end]
            regime_return = ((regime_data['portfolio_value'].iloc[-1] / 
                            regime_data['portfolio_value'].iloc[0]) - 1) * 100
            regime_volatility = (regime_data['portfolio_value'].pct_change()
                               .std() * np.sqrt(252)) * 100
            
            regimes.append(MarketRegime(
                start_date=regime_start,
                end_date=regime_end,
                regime_type=current_regime,
                duration_days=regime_duration,
                market_return=regime_return,
                volatility=regime_volatility,
                description=self._get_regime_description(current_regime, regime_return, regime_volatility)
            ))
        
        return regimes
    
    def _calculate_rolling_drawdown(self, price_series: pd.Series) -> pd.Series:
        """Calculate rolling maximum drawdown"""
        rolling_max = price_series.rolling(252).max()
        drawdown = (price_series - rolling_max) / rolling_max * -1
        return drawdown
    
    def _get_regime_description(self, regime_type: str, return_pct: float, volatility_pct: float) -> str:
        """Generate human-readable regime description"""
        descriptions = {
            'bull': f"Bull Market: {return_pct:.1f}% return with {volatility_pct:.1f}% volatility",
            'bear': f"Bear Market: {return_pct:.1f}% return with {volatility_pct:.1f}% volatility", 
            'crisis': f"Crisis Period: {return_pct:.1f}% return with {volatility_pct:.1f}% volatility",
            'recovery': f"Recovery Period: {return_pct:.1f}% return with {volatility_pct:.1f}% volatility",
            'sideways': f"Sideways Market: {return_pct:.1f}% return with {volatility_pct:.1f}% volatility"
        }
        return descriptions.get(regime_type, f"Unknown regime: {return_pct:.1f}% return")
    
    def _analyze_regime_performance(
        self, 
        portfolio_data: pd.DataFrame, 
        regimes: List[MarketRegime],
        allocation: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """Analyze portfolio performance within each regime type"""
        regime_performance = {}
        
        # Group regimes by type
        regime_types = {}
        for regime in regimes:
            if regime.regime_type not in regime_types:
                regime_types[regime.regime_type] = []
            regime_types[regime.regime_type].append(regime)
        
        # Calculate performance metrics for each regime type
        for regime_type, regime_list in regime_types.items():
            returns = []
            volatilities = []
            durations = []
            
            for regime in regime_list:
                returns.append(regime.market_return)
                volatilities.append(regime.volatility)
                durations.append(regime.duration_days)
            
            regime_performance[regime_type] = {
                'avg_return': np.mean(returns),
                'avg_volatility': np.mean(volatilities),
                'avg_duration_days': np.mean(durations),
                'total_occurrences': len(regime_list),
                'best_return': np.max(returns),
                'worst_return': np.min(returns)
            }
        
        return regime_performance
    
    def _analyze_correlation_evolution(
        self,
        allocation: Dict[str, float],
        start_date: datetime,
        end_date: datetime,
        db_session: Session
    ) -> List[CorrelationPeriod]:
        """
        Analyze how asset correlations evolve over time
        
        Tracks correlation changes across 5-year rolling windows to identify
        diversification effectiveness and regime-dependent correlation patterns.
        """
        correlation_periods = []
        
        # Get individual asset data
        asset_data = {}
        for symbol in allocation.keys():
            query = db_session.query(DailyPrice).join(Asset).filter(
                Asset.symbol == symbol,
                DailyPrice.date >= start_date,
                DailyPrice.date <= end_date
            ).order_by(DailyPrice.date)
            
            prices = pd.DataFrame([(p.date, p.adj_close) for p in query.all()],
                                columns=['date', symbol])
            prices.set_index('date', inplace=True)
            asset_data[symbol] = prices[symbol]
        
        # Combine into single DataFrame
        combined_data = pd.DataFrame(asset_data)
        combined_data = combined_data.dropna()
        
        # Calculate correlations over 5-year rolling windows
        window_years = 5
        window_days = window_years * 252
        
        for i in range(window_days, len(combined_data), 252):  # Annual steps
            window_start = combined_data.index[i - window_days]
            window_end = combined_data.index[i]
            
            # Get window data and calculate returns
            window_data = combined_data.loc[window_start:window_end]
            returns = window_data.pct_change().dropna()
            
            # Calculate correlation matrix
            corr_matrix = returns.corr()
            
            # Convert to dictionary format
            corr_dict = {}
            for asset1 in corr_matrix.columns:
                corr_dict[asset1] = {}
                for asset2 in corr_matrix.columns:
                    corr_dict[asset1][asset2] = float(corr_matrix.loc[asset1, asset2])
            
            # Calculate average correlation (excluding self-correlations)
            correlations = []
            for i_asset in corr_matrix.columns:
                for j_asset in corr_matrix.columns:
                    if i_asset != j_asset:
                        correlations.append(abs(corr_matrix.loc[i_asset, j_asset]))
            
            avg_correlation = np.mean(correlations)
            
            # Calculate diversification ratio (lower correlation = better diversification)
            diversification_ratio = 1 - avg_correlation
            
            # Estimate dominant factor exposure (how much driven by single factor)
            eigenvalues = np.linalg.eigvals(corr_matrix.values)
            eigensum = np.sum(eigenvalues)
            
            # Handle edge cases to prevent invalid float values
            if np.isfinite(eigensum) and eigensum != 0 and len(eigenvalues) > 0:
                dominant_factor_exposure = max(0.0, min(1.0, eigenvalues[0] / eigensum))
            else:
                dominant_factor_exposure = 0.5  # Default fallback
            
            correlation_periods.append(CorrelationPeriod(
                start_date=window_start,
                end_date=window_end,
                period_years=window_years,
                correlation_matrix=corr_dict,
                avg_correlation=avg_correlation,
                diversification_ratio=diversification_ratio,
                dominant_factor_exposure=dominant_factor_exposure
            ))
        
        return correlation_periods
    
    def _assess_correlation_trends(
        self, 
        correlation_periods: List[CorrelationPeriod]
    ) -> Tuple[str, float]:
        """
        Assess the trend in correlations and overall diversification effectiveness
        
        Returns:
            Tuple of (trend_direction, diversification_effectiveness_score)
        """
        if len(correlation_periods) < 3:
            return 'insufficient_data', 0.5
        
        # Extract correlation values over time
        correlations = [period.avg_correlation for period in correlation_periods]
        diversification_ratios = [period.diversification_ratio for period in correlation_periods]
        
        # Calculate trend using linear regression
        x = np.arange(len(correlations))
        slope_corr, _, _, p_value, _ = stats.linregress(x, correlations)
        
        # Determine trend direction
        if p_value < 0.05:  # Statistically significant trend
            if slope_corr > 0.01:
                trend = 'increasing'  # Correlations increasing (worse for diversification)
            elif slope_corr < -0.01:
                trend = 'decreasing'  # Correlations decreasing (better for diversification)
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        # Calculate overall diversification effectiveness (0-1, higher is better)
        avg_diversification_ratio = np.mean(diversification_ratios)
        diversification_effectiveness = min(1.0, max(0.0, avg_diversification_ratio))
        
        return trend, diversification_effectiveness
    
    def _calculate_regime_transition_alpha(
        self,
        portfolio_data: pd.DataFrame,
        regimes: List[MarketRegime]
    ) -> float:
        """
        Calculate excess returns during regime transitions
        
        Measures if the portfolio generates alpha during regime changes,
        which could indicate good adaptive characteristics.
        """
        if len(regimes) < 2:
            return 0.0
        
        transition_returns = []
        
        for i in range(1, len(regimes)):
            # Define transition period (30 days around regime change)
            transition_start = regimes[i].start_date - timedelta(days=15)
            transition_end = regimes[i].start_date + timedelta(days=15)
            
            # Get portfolio data for transition period
            transition_data = portfolio_data[
                (portfolio_data.index >= transition_start) & 
                (portfolio_data.index <= transition_end)
            ]
            
            if len(transition_data) >= 20:  # Need sufficient data
                # Calculate return during transition
                transition_return = (
                    (transition_data['portfolio_value'].iloc[-1] / 
                     transition_data['portfolio_value'].iloc[0]) - 1
                ) * 100
                transition_returns.append(transition_return)
        
        if not transition_returns:
            return 0.0
        
        # Calculate average excess return during transitions
        # Assume market benchmark return of 0.5% per month (6% annual)
        benchmark_monthly_return = 0.5
        avg_transition_return = np.mean(transition_returns)
        
        # Alpha is excess return above benchmark
        regime_transition_alpha = avg_transition_return - benchmark_monthly_return
        
        return regime_transition_alpha
    
    def _generate_adaptation_recommendations(
        self,
        regimes: List[MarketRegime],
        correlation_periods: List[CorrelationPeriod],
        regime_performance: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """
        Generate strategic recommendations based on regime and correlation analysis
        """
        recommendations = []
        
        # Analyze regime patterns
        if 'crisis' in regime_performance:
            crisis_perf = regime_performance['crisis']
            if crisis_perf['avg_return'] > -15:  # Portfolio held up well in crises
                recommendations.append(
                    "Portfolio shows good crisis resilience. Consider maintaining current allocation during market stress."
                )
            else:
                recommendations.append(
                    "Portfolio vulnerable during crisis periods. Consider increasing defensive assets (bonds, gold)."
                )
        
        # Correlation-based recommendations
        if correlation_periods:
            recent_diversification = correlation_periods[-1].diversification_ratio
            if recent_diversification < 0.3:
                recommendations.append(
                    "Low diversification detected. Consider adding uncorrelated assets (REITs, commodities)."
                )
            elif recent_diversification > 0.7:
                recommendations.append(
                    "Excellent diversification maintained. Portfolio structure is well-balanced."
                )
        
        # Regime duration analysis
        regime_durations = [regime.duration_days for regime in regimes]
        avg_regime_duration = np.mean(regime_durations) if regime_durations else 365
        
        if avg_regime_duration < 180:  # Short regimes suggest high volatility environment
            recommendations.append(
                "Market regimes changing rapidly. Consider tactical rebalancing with shorter review periods."
            )
        elif avg_regime_duration > 1000:  # Long regimes suggest stable environment
            recommendations.append(
                "Stable market regimes detected. Strategic buy-and-hold approach likely effective."
            )
        
        # Performance consistency across regimes
        if len(regime_performance) >= 3:
            returns_by_regime = [perf['avg_return'] for perf in regime_performance.values()]
            return_consistency = 1 / (np.std(returns_by_regime) + 0.1)  # Higher = more consistent
            
            if return_consistency > 2:
                recommendations.append(
                    "Portfolio performs consistently across market regimes. Well-suited for long-term investing."
                )
            else:
                recommendations.append(
                    "Portfolio performance varies significantly by market regime. Consider regime-aware rebalancing."
                )
        
        return recommendations if recommendations else ["Portfolio analysis complete. Consider periodic review."]
    
    def _detect_volatility_clustering(self, portfolio_data: pd.DataFrame) -> List[Tuple[datetime, datetime]]:
        """
        Detect periods of high volatility clustering using GARCH-like analysis
        
        Identifies periods where high volatility tends to be followed by more high volatility,
        which can help in risk management and position sizing decisions.
        """
        returns = portfolio_data['portfolio_value'].pct_change().fillna(0)
        
        # Calculate rolling volatility (30-day window)
        rolling_vol = returns.rolling(30).std() * np.sqrt(252)
        
        # Define high volatility threshold (top quartile)
        high_vol_threshold = rolling_vol.quantile(0.75)
        
        # Find periods of sustained high volatility (>= 10 consecutive days)
        high_vol_periods = rolling_vol > high_vol_threshold
        clustering_periods = []
        
        in_cluster = False
        cluster_start = None
        
        for date, is_high_vol in high_vol_periods.items():
            if is_high_vol and not in_cluster:
                # Start new cluster
                cluster_start = date
                in_cluster = True
            elif not is_high_vol and in_cluster:
                # End current cluster
                if cluster_start and (date - cluster_start).days >= 10:
                    clustering_periods.append((cluster_start, date))
                in_cluster = False
                cluster_start = None
        
        # Handle final cluster
        if in_cluster and cluster_start:
            final_date = portfolio_data.index[-1]
            if (final_date - cluster_start).days >= 10:
                clustering_periods.append((cluster_start, final_date))
        
        return clustering_periods
    
    def _analyze_tail_risk_evolution(self, portfolio_data: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze how tail risks (extreme losses) evolve over the analysis period
        
        Calculates Value-at-Risk (VaR) metrics for different periods to understand
        if the portfolio's extreme risk profile is changing over time.
        """
        returns = portfolio_data['portfolio_value'].pct_change().fillna(0)
        
        # Calculate VaR for different confidence levels
        var_95 = np.percentile(returns, 5) * 100  # 5th percentile (95% VaR)
        var_99 = np.percentile(returns, 1) * 100  # 1st percentile (99% VaR)
        
        # Split into first and second half for comparison
        mid_point = len(returns) // 2
        first_half_returns = returns.iloc[:mid_point]
        second_half_returns = returns.iloc[mid_point:]
        
        first_half_var95 = np.percentile(first_half_returns, 5) * 100
        second_half_var95 = np.percentile(second_half_returns, 5) * 100
        
        # Calculate tail risk change
        tail_risk_change = second_half_var95 - first_half_var95
        
        return {
            'var_95_full_period': var_95,
            'var_99_full_period': var_99,
            'var_95_first_half': first_half_var95,
            'var_95_second_half': second_half_var95,
            'tail_risk_change_pct': tail_risk_change,
            'tail_risk_trend': 'increasing' if tail_risk_change < -0.5 else 'stable' if abs(tail_risk_change) <= 0.5 else 'decreasing'
        }
    
    def _calculate_period_cagr(self, portfolio_data: pd.DataFrame, start_idx: int, end_idx: int) -> float:
        """Calculate CAGR for a specific period within the data"""
        if start_idx >= end_idx or end_idx >= len(portfolio_data):
            return 0.0
        
        start_value = portfolio_data['portfolio_value'].iloc[start_idx]
        end_value = portfolio_data['portfolio_value'].iloc[end_idx]
        days = (portfolio_data.index[end_idx] - portfolio_data.index[start_idx]).days
        years = days / 365.25
        
        if years <= 0 or start_value <= 0:
            return 0.0
        
        cagr = (end_value / start_value) ** (1/years) - 1
        return cagr * 100  # Convert to percentage
    
    def compare_period_performance(
        self,
        allocation: Dict[str, float],
        comparison_periods: List[int] = [10, 20],
        db_session: Session = None
    ) -> Dict[str, Any]:
        """
        Compare performance across different historical periods
        
        Args:
            allocation: Portfolio allocation
            comparison_periods: List of periods in years to compare
            db_session: Database session
            
        Returns:
            Dictionary with performance comparison across periods
        """
        end_date = datetime.now()
        results = {}
        
        for years in comparison_periods:
            start_date = end_date - timedelta(days=years*365)
            
            try:
                # Get portfolio data using backtest method
                start_date_str = start_date.strftime("%Y-%m-%d")
                end_date_str = end_date.strftime("%Y-%m-%d")
                
                backtest_result = self.portfolio_engine.backtest_portfolio(
                    allocation=allocation,
                    initial_value=10000,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    rebalance_frequency="monthly",
                    include_daily_data=True
                )
                
                # Extract daily portfolio values
                portfolio_data = pd.DataFrame(backtest_result['daily_data'])
                portfolio_data['date'] = pd.to_datetime(portfolio_data['date'])
                portfolio_data.set_index('date', inplace=True)
                
                if portfolio_data is None or len(portfolio_data) < 252:
                    continue
                
                # Calculate performance metrics
                cagr = self._calculate_period_cagr(portfolio_data, 0, len(portfolio_data)-1)
                
                returns = portfolio_data['portfolio_value'].pct_change().fillna(0)
                volatility = returns.std() * np.sqrt(252) * 100
                
                # Calculate Sharpe ratio (assuming 2% risk-free rate)
                excess_return = cagr - 2.0
                sharpe_ratio = excess_return / volatility if volatility > 0 else 0
                
                # Calculate max drawdown
                rolling_max = portfolio_data['portfolio_value'].expanding().max()
                drawdown = (portfolio_data['portfolio_value'] - rolling_max) / rolling_max
                max_drawdown = abs(drawdown.min()) * 100
                
                results[f"{years}_year"] = {
                    'period_years': years,
                    'cagr': cagr,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
                
            except Exception as e:
                results[f"{years}_year"] = {'error': str(e)}
        
        return results
