"""
Recovery Time Analysis Engine for Portfolio Backtesting

This module provides comprehensive recovery time analysis for portfolio performance,
enabling users to understand how quickly portfolios recover from drawdowns.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .portfolio_engine_optimized import OptimizedPortfolioEngine


@dataclass
class DrawdownPeriod:
    """A period of portfolio drawdown"""
    start_date: datetime
    end_date: datetime  # Peak to trough
    peak_value: float
    trough_value: float
    drawdown_pct: float
    duration_days: int


@dataclass
class RecoveryPeriod:
    """A period of portfolio recovery"""
    trough_date: datetime
    recovery_date: Optional[datetime]  # None if not yet recovered
    trough_value: float
    target_value: float
    recovery_pct: float  # Percentage of drawdown recovered
    recovery_duration_days: Optional[int]
    recovery_velocity: Optional[float]  # % recovery per month
    full_recovery: bool  # Whether portfolio fully recovered to pre-drawdown level


@dataclass
class RecoveryAnalysisResult:
    """Complete recovery analysis for a portfolio"""
    analysis_period: Tuple[datetime, datetime]
    major_drawdowns: List[DrawdownPeriod]  # Drawdowns > 10%
    recovery_periods: List[RecoveryPeriod]
    avg_recovery_time_days: Optional[float]
    avg_recovery_velocity: Optional[float]
    recovery_success_rate: float  # % of drawdowns that fully recovered
    max_recovery_time_days: Optional[int]
    current_drawdown: Optional[DrawdownPeriod]  # If currently in drawdown
    resilience_metrics: Dict[str, float]


class RecoveryTimeAnalyzer:
    """
    Analyzes portfolio recovery patterns from drawdowns
    
    Provides insights into:
    - Time required to recover from major drawdowns
    - Recovery velocity (speed of recovery)
    - Success rate of full recoveries
    - Current drawdown status
    - Historical resilience patterns
    """
    
    def __init__(self, portfolio_engine: OptimizedPortfolioEngine):
        """
        Initialize with optimized portfolio engine
        
        Args:
            portfolio_engine: OptimizedPortfolioEngine instance for backtesting
        """
        self.portfolio_engine = portfolio_engine
        
    def analyze_recovery_patterns(
        self,
        allocation: Dict[str, float],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_drawdown_pct: float = 0.10  # Minimum 10% drawdown to analyze
    ) -> RecoveryAnalysisResult:
        """
        Analyze recovery patterns for a portfolio across a given time period
        
        Args:
            allocation: Portfolio allocation dictionary (symbol -> weight)
            start_date: Analysis start date (defaults to earliest available)
            end_date: Analysis end date (defaults to latest available) 
            min_drawdown_pct: Minimum drawdown percentage to include in analysis
            
        Returns:
            RecoveryAnalysisResult with complete recovery analysis
        """
        # Get portfolio performance data
        backtest_result = self.portfolio_engine.backtest_portfolio(
            allocation=allocation,
            start_date=start_date.strftime("%Y-%m-%d") if start_date else None,
            end_date=end_date.strftime("%Y-%m-%d") if end_date else None,
            include_daily_data=True  # Request daily data for recovery analysis
        )
        
        if 'daily_data' not in backtest_result:
            raise ValueError("Daily data required for recovery analysis")
            
        # Convert to DataFrame for easier analysis
        daily_data = pd.DataFrame(backtest_result['daily_data'])
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        daily_data['portfolio_value'] = daily_data['cumulative_return'] + 1.0
        
        # Find drawdown periods
        drawdown_periods = self._identify_drawdown_periods(
            daily_data, min_drawdown_pct
        )
        
        # Analyze recovery for each drawdown
        recovery_periods = []
        for drawdown in drawdown_periods:
            recovery = self._analyze_recovery_from_drawdown(
                daily_data, drawdown
            )
            recovery_periods.append(recovery)
            
        # Calculate summary metrics
        analysis_start = daily_data['date'].iloc[0]
        analysis_end = daily_data['date'].iloc[-1]
        
        # Current drawdown check
        current_drawdown = self._check_current_drawdown(
            daily_data, min_drawdown_pct
        )
        
        # Calculate resilience metrics
        resilience_metrics = self._calculate_resilience_metrics(
            drawdown_periods, recovery_periods
        )
        
        # Calculate summary statistics
        recovery_times = [
            r.recovery_duration_days for r in recovery_periods 
            if r.recovery_duration_days is not None
        ]
        
        recovery_velocities = [
            r.recovery_velocity for r in recovery_periods
            if r.recovery_velocity is not None
        ]
        
        avg_recovery_time = np.mean(recovery_times) if recovery_times else None
        avg_recovery_velocity = np.mean(recovery_velocities) if recovery_velocities else None
        max_recovery_time = max(recovery_times) if recovery_times else None
        
        # Recovery success rate
        full_recoveries = sum(1 for r in recovery_periods if r.full_recovery)
        recovery_success_rate = full_recoveries / len(recovery_periods) if recovery_periods else 0.0
        
        return RecoveryAnalysisResult(
            analysis_period=(analysis_start, analysis_end),
            major_drawdowns=drawdown_periods,
            recovery_periods=recovery_periods,
            avg_recovery_time_days=avg_recovery_time,
            avg_recovery_velocity=avg_recovery_velocity,
            recovery_success_rate=recovery_success_rate,
            max_recovery_time_days=max_recovery_time,
            current_drawdown=current_drawdown,
            resilience_metrics=resilience_metrics
        )
        
    def _identify_drawdown_periods(
        self,
        daily_data: pd.DataFrame,
        min_drawdown_pct: float
    ) -> List[DrawdownPeriod]:
        """Identify major drawdown periods in the data"""
        
        drawdowns = []
        
        # Calculate running maximum (peak values)
        daily_data['peak_value'] = daily_data['portfolio_value'].expanding().max()
        
        # Calculate drawdown from peak
        daily_data['drawdown'] = (
            daily_data['portfolio_value'] / daily_data['peak_value']
        ) - 1.0
        
        # Find periods where drawdown exceeds minimum threshold
        in_drawdown = daily_data['drawdown'] <= -min_drawdown_pct
        
        # Find drawdown start/end points
        drawdown_starts = []
        drawdown_ends = []
        
        was_in_drawdown = False
        for i, currently_in_drawdown in enumerate(in_drawdown):
            if currently_in_drawdown and not was_in_drawdown:
                # Start of drawdown
                drawdown_starts.append(i)
            elif not currently_in_drawdown and was_in_drawdown:
                # End of drawdown  
                drawdown_ends.append(i - 1)
            was_in_drawdown = currently_in_drawdown
            
        # Handle case where drawdown continues to end of data
        if was_in_drawdown:
            drawdown_ends.append(len(daily_data) - 1)
            
        # Create DrawdownPeriod objects
        for start_idx, end_idx in zip(drawdown_starts, drawdown_ends):
            start_row = daily_data.iloc[start_idx]
            end_row = daily_data.iloc[end_idx]
            
            # Find the actual trough (minimum value) during drawdown period
            drawdown_slice = daily_data.iloc[start_idx:end_idx+1]
            trough_idx = drawdown_slice['portfolio_value'].idxmin()
            trough_row = daily_data.loc[trough_idx]
            
            drawdown = DrawdownPeriod(
                start_date=start_row['date'],
                end_date=trough_row['date'],
                peak_value=start_row['peak_value'],
                trough_value=trough_row['portfolio_value'],
                drawdown_pct=trough_row['drawdown'],
                duration_days=(trough_row['date'] - start_row['date']).days
            )
            drawdowns.append(drawdown)
            
        return drawdowns
        
    def _analyze_recovery_from_drawdown(
        self,
        daily_data: pd.DataFrame,
        drawdown: DrawdownPeriod
    ) -> RecoveryPeriod:
        """Analyze recovery from a specific drawdown period"""
        
        # Find data starting from trough date
        trough_date = drawdown.end_date
        recovery_data = daily_data[daily_data['date'] >= trough_date].copy()
        
        if recovery_data.empty:
            return RecoveryPeriod(
                trough_date=trough_date,
                recovery_date=None,
                trough_value=drawdown.trough_value,
                target_value=drawdown.peak_value,
                recovery_pct=0.0,
                recovery_duration_days=None,
                recovery_velocity=None,
                full_recovery=False
            )
        
        # Target is to recover to pre-drawdown peak
        target_value = drawdown.peak_value
        trough_value = drawdown.trough_value
        
        # Find if/when full recovery occurred
        recovery_achieved = recovery_data['portfolio_value'] >= target_value
        
        recovery_date = None
        recovery_duration_days = None
        full_recovery = False
        
        if recovery_achieved.any():
            # Find first date of full recovery
            recovery_idx = recovery_achieved.idxmax()
            recovery_date = recovery_data.loc[recovery_idx, 'date']
            recovery_duration_days = (recovery_date - trough_date).days
            full_recovery = True
            
        # Calculate current recovery percentage
        latest_value = recovery_data['portfolio_value'].iloc[-1]
        recovery_pct = min(1.0, max(0.0, 
            (latest_value - trough_value) / (target_value - trough_value)
        ))
        
        # Calculate recovery velocity (% per month)
        recovery_velocity = None
        if recovery_duration_days and recovery_duration_days > 0:
            months = recovery_duration_days / 30.44  # Average days per month
            total_recovery_needed = abs(drawdown.drawdown_pct)
            recovery_velocity = total_recovery_needed / months
            
        return RecoveryPeriod(
            trough_date=trough_date,
            recovery_date=recovery_date,
            trough_value=trough_value,
            target_value=target_value,
            recovery_pct=recovery_pct,
            recovery_duration_days=recovery_duration_days,
            recovery_velocity=recovery_velocity,
            full_recovery=full_recovery
        )
        
    def _check_current_drawdown(
        self,
        daily_data: pd.DataFrame,
        min_drawdown_pct: float
    ) -> Optional[DrawdownPeriod]:
        """Check if portfolio is currently in a significant drawdown"""
        
        if daily_data.empty:
            return None
            
        # Get current status
        latest_row = daily_data.iloc[-1]
        current_value = latest_row['portfolio_value']
        
        # Find recent peak (within last 2 years)
        recent_data = daily_data[
            daily_data['date'] >= (latest_row['date'] - timedelta(days=730))
        ]
        
        if recent_data.empty:
            return None
            
        peak_value = recent_data['portfolio_value'].max()
        peak_date_idx = recent_data['portfolio_value'].idxmax()
        peak_date = recent_data.loc[peak_date_idx, 'date']
        
        # Calculate current drawdown
        current_drawdown_pct = (current_value / peak_value) - 1.0
        
        # Check if significant drawdown
        if current_drawdown_pct <= -min_drawdown_pct:
            return DrawdownPeriod(
                start_date=peak_date,
                end_date=latest_row['date'],
                peak_value=peak_value,
                trough_value=current_value,
                drawdown_pct=current_drawdown_pct,
                duration_days=(latest_row['date'] - peak_date).days
            )
            
        return None
        
    def _calculate_resilience_metrics(
        self,
        drawdown_periods: List[DrawdownPeriod],
        recovery_periods: List[RecoveryPeriod]
    ) -> Dict[str, float]:
        """Calculate portfolio resilience metrics"""
        
        if not drawdown_periods:
            return {
                "drawdown_frequency": 0.0,
                "avg_drawdown_magnitude": 0.0,
                "max_drawdown_magnitude": 0.0,
                "recovery_efficiency": 100.0,
                "resilience_score": 100.0
            }
        
        # Drawdown frequency (per year - approximate)
        total_days = sum(dd.duration_days for dd in drawdown_periods)
        avg_days_between = total_days / len(drawdown_periods) if drawdown_periods else 365
        drawdown_frequency = 365.0 / max(1, avg_days_between)
        
        # Drawdown magnitudes
        drawdown_magnitudes = [abs(dd.drawdown_pct) for dd in drawdown_periods]
        avg_drawdown_magnitude = np.mean(drawdown_magnitudes)
        max_drawdown_magnitude = max(drawdown_magnitudes)
        
        # Recovery efficiency
        full_recoveries = sum(1 for r in recovery_periods if r.full_recovery)
        recovery_efficiency = (full_recoveries / len(recovery_periods)) * 100 if recovery_periods else 100.0
        
        # Overall resilience score (0-100)
        # Factors: lower drawdown magnitude (40%), higher recovery rate (30%), faster recovery (30%)
        magnitude_score = max(0, 100 - (avg_drawdown_magnitude * 400))  # 25% drawdown = 0 points
        recovery_score = recovery_efficiency * 0.3
        
        # Speed score based on average recovery time
        recovery_times = [r.recovery_duration_days for r in recovery_periods if r.recovery_duration_days]
        if recovery_times:
            avg_recovery_days = np.mean(recovery_times)
            # 90 days = 100 points, 365 days = 50 points, 730+ days = 0 points
            speed_score = max(0, min(30, 30 * (1 - (avg_recovery_days - 90) / 640)))
        else:
            speed_score = 15  # Neutral score if no recovery data
            
        resilience_score = magnitude_score * 0.4 + recovery_score + speed_score
        
        return {
            "drawdown_frequency": self._safe_float(drawdown_frequency),
            "avg_drawdown_magnitude": self._safe_float(avg_drawdown_magnitude),
            "max_drawdown_magnitude": self._safe_float(max_drawdown_magnitude),
            "recovery_efficiency": self._safe_float(recovery_efficiency),
            "resilience_score": self._safe_float(resilience_score)
        }
        
    def _safe_float(self, value) -> float:
        """Convert to safe float that can be JSON serialized"""
        if value is None or np.isnan(value) or np.isinf(value):
            return 0.0
        return float(value)
        
    def compare_recovery_patterns(
        self,
        portfolios: Dict[str, Dict[str, float]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_drawdown_pct: float = 0.10
    ) -> Dict[str, RecoveryAnalysisResult]:
        """
        Compare recovery patterns across multiple portfolios
        
        Args:
            portfolios: Dictionary of portfolio name -> allocation
            start_date: Analysis start date
            end_date: Analysis end date  
            min_drawdown_pct: Minimum drawdown percentage to analyze
            
        Returns:
            Dictionary of portfolio name -> RecoveryAnalysisResult
        """
        results = {}
        
        for portfolio_name, allocation in portfolios.items():
            try:
                # Use default date range if not specified
                analysis_start = start_date or datetime(2015, 1, 1)
                analysis_end = end_date or datetime(2024, 1, 1)
                
                result = self.analyze_recovery_patterns(
                    allocation=allocation,
                    start_date=analysis_start,
                    end_date=analysis_end,
                    min_drawdown_pct=min_drawdown_pct
                )
                results[portfolio_name] = result
            except Exception as e:
                print(f"Warning: Failed to analyze recovery for {portfolio_name}: {e}")
                continue
                
        return results
