"""
Rolling Period Analysis Engine for Portfolio Backtesting

This module provides comprehensive rolling window analysis for portfolio performance,
enabling users to understand performance consistency across different market regimes.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session

from .portfolio_engine_optimized import OptimizedPortfolioEngine
from ..models import get_db, Asset, DailyPrice


@dataclass
class RollingPeriodResult:
    """Results from a single rolling period analysis"""
    start_date: datetime
    end_date: datetime
    period_years: int
    cagr: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    total_return: float


@dataclass
class RollingPeriodSummary:
    """Summary statistics for rolling period analysis"""
    period_years: int
    total_windows: int
    avg_cagr: float
    min_cagr: float
    max_cagr: float
    cagr_std: float
    avg_volatility: float
    avg_sharpe: float
    avg_max_drawdown: float
    worst_period: RollingPeriodResult
    best_period: RollingPeriodResult
    consistency_score: float  # Lower std dev relative to mean = higher consistency


class RollingPeriodAnalyzer:
    """
    Analyzes portfolio performance across rolling time windows
    
    Provides insights into:
    - Performance consistency across market cycles
    - Best/worst performing periods
    - Risk-adjusted return stability
    - Portfolio behavior across different market regimes
    """
    
    def __init__(self, portfolio_engine: OptimizedPortfolioEngine):
        """
        Initialize with optimized portfolio engine
        
        Args:
            portfolio_engine: OptimizedPortfolioEngine instance for backtesting
        """
        self.portfolio_engine = portfolio_engine
        
    def analyze_rolling_periods(
        self,
        allocation: Dict[str, float],
        period_years: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[RollingPeriodResult], RollingPeriodSummary]:
        """
        Perform rolling period analysis for given portfolio allocation
        
        Args:
            allocation: Portfolio allocation dictionary (symbol -> weight)
            period_years: Rolling window size in years (e.g., 3 for 3-year windows)
            start_date: Analysis start date (defaults to earliest available data)
            end_date: Analysis end date (defaults to latest available data)
            
        Returns:
            Tuple of (individual period results, summary statistics)
        """
        # Get available data range
        if start_date is None or end_date is None:
            data_range = self._get_data_range(list(allocation.keys()))
            start_date = start_date or data_range[0]
            end_date = end_date or data_range[1]
            
        # Calculate rolling windows
        period_results = []
        window_start = start_date
        
        print(f"DEBUG: Starting rolling analysis from {start_date} to {end_date}, period: {period_years} years")
        
        window_count = 0
        while True:
            window_end = window_start + timedelta(days=period_years * 365)
            
            # Stop if window extends beyond available data
            if window_end > end_date:
                print(f"DEBUG: Stopping - window end {window_end} > analysis end {end_date}")
                break
                
            window_count += 1
            print(f"DEBUG: Processing window {window_count}: {window_start} to {window_end}")
                
            # Perform backtest for this window
            try:
                backtest_result = self.portfolio_engine.backtest_portfolio(
                    allocation=allocation,
                    start_date=window_start.strftime("%Y-%m-%d"),
                    end_date=window_end.strftime("%Y-%m-%d")
                )
                
                # Create rolling period result with safe float conversion
                metrics = backtest_result['performance_metrics']
                
                def safe_float(value):
                    """Convert to safe float that can be JSON serialized"""
                    if value is None or np.isnan(value) or np.isinf(value):
                        return 0.0
                    return float(value)
                
                period_result = RollingPeriodResult(
                    start_date=window_start,
                    end_date=window_end,
                    period_years=period_years,
                    cagr=safe_float(metrics['cagr']),
                    volatility=safe_float(metrics['volatility']),
                    sharpe_ratio=safe_float(metrics['sharpe_ratio']),
                    max_drawdown=safe_float(metrics['max_drawdown']),
                    total_return=safe_float(metrics['total_return'])
                )
                
                period_results.append(period_result)
                print(f"DEBUG: Window {window_count} successful, CAGR: {period_result.cagr:.2%}")
                
            except Exception as e:
                # Log but don't fail entire analysis for one window
                print(f"DEBUG Warning: Failed to analyze window {window_start} to {window_end}: {e}")
                
            # Move window forward by 3 months (quarterly) for optimized performance
            # Reduces windows from 74 to 25 (3x performance improvement)
            window_start = window_start + timedelta(days=90)
            
            # Safety break to prevent infinite loops
            if window_count > 50:
                print("DEBUG: Safety break - too many windows")
                break
            
        print(f"DEBUG: Analysis complete. Generated {len(period_results)} period results")
        
        # Generate summary statistics
        summary = self._calculate_summary_statistics(period_results, period_years)
        
        return period_results, summary
        
    def analyze_multiple_periods(
        self,
        allocation: Dict[str, float],
        period_years_list: List[int],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[int, Tuple[List[RollingPeriodResult], RollingPeriodSummary]]:
        """
        Analyze multiple rolling period lengths for comparison
        
        Args:
            allocation: Portfolio allocation dictionary
            period_years_list: List of period lengths to analyze (e.g., [3, 5, 10])
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Dictionary mapping period length to (results, summary) tuple
        """
        results = {}
        
        for period_years in period_years_list:
            try:
                period_results, summary = self.analyze_rolling_periods(
                    allocation=allocation,
                    period_years=period_years,
                    start_date=start_date,
                    end_date=end_date
                )
                results[period_years] = (period_results, summary)
            except Exception as e:
                print(f"Warning: Failed to analyze {period_years}-year rolling periods: {e}")
                
        return results
        
    def compare_portfolios_rolling(
        self,
        allocations: Dict[str, Dict[str, float]],
        period_years: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Tuple[List[RollingPeriodResult], RollingPeriodSummary]]:
        """
        Compare multiple portfolio allocations using rolling period analysis
        
        Args:
            allocations: Dictionary mapping portfolio name to allocation
            period_years: Rolling window size in years
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            Dictionary mapping portfolio name to (results, summary) tuple
        """
        comparison_results = {}
        
        for portfolio_name, allocation in allocations.items():
            try:
                results, summary = self.analyze_rolling_periods(
                    allocation=allocation,
                    period_years=period_years,
                    start_date=start_date,
                    end_date=end_date
                )
                comparison_results[portfolio_name] = (results, summary)
            except Exception as e:
                print(f"Warning: Failed to analyze portfolio '{portfolio_name}': {e}")
                
        return comparison_results
        
    def _get_data_range(self, symbols: List[str]) -> Tuple[datetime, datetime]:
        """Get available data range for given symbols"""
        try:
            db = next(get_db())
            
            # Find common date range across all symbols
            min_start = None
            max_end = None
            
            for symbol in symbols:
                # Check if asset exists
                asset = db.query(Asset).filter(Asset.symbol == symbol).first()
                if not asset:
                    continue
                    
                earliest = db.query(DailyPrice.date).filter(
                    DailyPrice.symbol == symbol
                ).order_by(DailyPrice.date.asc()).first()
                
                latest = db.query(DailyPrice.date).filter(
                    DailyPrice.symbol == symbol
                ).order_by(DailyPrice.date.desc()).first()
                
                if earliest and latest:
                    if min_start is None or earliest.date > min_start:
                        min_start = earliest.date
                    if max_end is None or latest.date < max_end:
                        max_end = latest.date
                        
            return min_start, max_end
            
        except Exception as e:
            # Fallback to reasonable defaults
            return (
                datetime(2004, 1, 1),
                datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            )
            
    def _calculate_summary_statistics(
        self, 
        results: List[RollingPeriodResult], 
        period_years: int
    ) -> RollingPeriodSummary:
        """Calculate summary statistics from individual period results"""
        print(f"DEBUG: _calculate_summary_statistics called with {len(results)} results")
        
        if not results:
            print(f"DEBUG: ERROR - No results provided to summary calculation!")
            raise ValueError("No rolling period results to summarize")
            
        # Filter out any NaN or infinite values from results
        cagrs = [r.cagr for r in results if not (np.isnan(r.cagr) or np.isinf(r.cagr))]
        volatilities = [r.volatility for r in results if not (np.isnan(r.volatility) or np.isinf(r.volatility))]
        sharpes = [r.sharpe_ratio for r in results if not (np.isnan(r.sharpe_ratio) or np.isinf(r.sharpe_ratio))]
        drawdowns = [r.max_drawdown for r in results if not (np.isnan(r.max_drawdown) or np.isinf(r.max_drawdown))]
        
        # Check if we have valid data after filtering
        if not cagrs:
            raise ValueError("No valid CAGR values found in rolling period results")
        
        # Find best and worst periods based on valid CAGR values
        valid_results = [r for r in results if not (np.isnan(r.cagr) or np.isinf(r.cagr))]
        if not valid_results:
            raise ValueError("No valid results found for best/worst period calculation")
            
        best_period = max(valid_results, key=lambda r: r.cagr)
        worst_period = min(valid_results, key=lambda r: r.cagr)
        
        # Calculate consistency score (lower is more consistent)
        # Coefficient of variation: std_dev / mean
        avg_cagr = np.mean(cagrs)
        cagr_std = np.std(cagrs)
        
        # Handle edge cases for consistency score
        if avg_cagr == 0:
            consistency_score = 1.0  # Neutral score instead of infinity
        else:
            consistency_score = cagr_std / abs(avg_cagr)
            # Cap extremely high consistency scores
            if consistency_score > 10.0:
                consistency_score = 10.0
        
        # Calculate averages with safe defaults
        avg_volatility = np.mean(volatilities) if volatilities else 0.0
        avg_sharpe = np.mean(sharpes) if sharpes else 0.0
        avg_max_drawdown = np.mean(drawdowns) if drawdowns else 0.0
        
        # Ensure all values are JSON-serializable floats
        def safe_float(value):
            """Convert to safe float that can be JSON serialized"""
            if np.isnan(value) or np.isinf(value):
                return 0.0
            return float(value)
        
        return RollingPeriodSummary(
            period_years=period_years,
            total_windows=len(results),
            avg_cagr=safe_float(avg_cagr),
            min_cagr=safe_float(min(cagrs)),
            max_cagr=safe_float(max(cagrs)),
            cagr_std=safe_float(cagr_std),
            avg_volatility=safe_float(avg_volatility),
            avg_sharpe=safe_float(avg_sharpe),
            avg_max_drawdown=safe_float(avg_max_drawdown),
            worst_period=worst_period,
            best_period=best_period,
            consistency_score=safe_float(consistency_score)
        )
        
    def generate_rolling_insights(
        self,
        summaries: Dict[int, RollingPeriodSummary],
        allocation: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generate actionable insights from rolling period analysis
        
        Args:
            summaries: Dictionary mapping period years to summary statistics
            allocation: Portfolio allocation being analyzed
            
        Returns:
            Dictionary with key insights and recommendations
        """
        insights = {
            "consistency_analysis": {},
            "risk_profile": {},
            "recommendations": [],
            "key_findings": []
        }
        
        # Analyze consistency across different time horizons
        for period_years, summary in summaries.items():
            insights["consistency_analysis"][f"{period_years}_year"] = {
                "consistency_score": round(summary.consistency_score, 3),
                "cagr_range": {
                    "min": round(summary.min_cagr * 100, 1),
                    "max": round(summary.max_cagr * 100, 1),
                    "avg": round(summary.avg_cagr * 100, 1),
                    "std": round(summary.cagr_std * 100, 1)
                },
                "worst_period": {
                    "start": summary.worst_period.start_date.strftime("%Y-%m-%d"),
                    "end": summary.worst_period.end_date.strftime("%Y-%m-%d"),
                    "cagr": round(summary.worst_period.cagr * 100, 1)
                },
                "best_period": {
                    "start": summary.best_period.start_date.strftime("%Y-%m-%d"),
                    "end": summary.best_period.end_date.strftime("%Y-%m-%d"),
                    "cagr": round(summary.best_period.cagr * 100, 1)
                }
            }
            
        # Generate key insights
        if len(summaries) >= 2:
            period_keys = sorted(summaries.keys())
            short_term = summaries[period_keys[0]]
            long_term = summaries[period_keys[-1]]
            
            if short_term.consistency_score > long_term.consistency_score:
                insights["key_findings"].append(
                    f"Portfolio becomes more consistent over longer time horizons "
                    f"({period_keys[0]}-year consistency: {short_term.consistency_score:.2f} vs "
                    f"{period_keys[-1]}-year: {long_term.consistency_score:.2f})"
                )
                
        return insights
