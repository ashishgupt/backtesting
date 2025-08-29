"""
Crisis Period Stress Testing Engine for Portfolio Backtesting

This module provides comprehensive crisis period analysis for portfolio performance,
enabling users to understand portfolio resilience during major market downturns.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .portfolio_engine_optimized import OptimizedPortfolioEngine


class CrisisType(str, Enum):
    """Types of market crises for analysis"""
    FINANCIAL_CRISIS = "financial_crisis"
    PANDEMIC = "pandemic"
    BEAR_MARKET = "bear_market"
    INTEREST_RATE_SHOCK = "interest_rate_shock"
    GEOPOLITICAL = "geopolitical"


@dataclass
class CrisisPeriod:
    """Definition of a market crisis period"""
    name: str
    crisis_type: CrisisType
    start_date: datetime
    end_date: datetime
    description: str
    peak_to_trough_dates: Optional[Tuple[datetime, datetime]] = None
    market_decline_pct: Optional[float] = None


@dataclass 
class CrisisAnalysisResult:
    """Results from crisis period analysis"""
    crisis: CrisisPeriod
    portfolio_performance: Dict[str, float]
    crisis_decline: float  # Portfolio decline during crisis period
    recovery_time_days: Optional[int] = None  # Days to recover to pre-crisis level
    recovery_velocity: Optional[float] = None  # % recovery per month
    resilience_score: float = 0.0  # 0-100 score based on decline and recovery
    

@dataclass
class StressTestSummary:
    """Summary of stress testing across multiple crisis periods"""
    crisis_results: List[CrisisAnalysisResult]
    avg_crisis_decline: float
    worst_crisis_decline: float
    best_crisis_decline: float
    avg_recovery_time_days: Optional[float]
    overall_resilience_score: float
    crisis_consistency: float  # How consistent performance is across crises


class CrisisPeriodAnalyzer:
    """
    Analyzes portfolio performance during major market crisis periods
    
    Provides insights into:
    - Portfolio behavior during market stress
    - Recovery time from major drawdowns
    - Resilience scoring for different allocations
    - Crisis-specific risk assessment
    """
    
    # Define major crisis periods for analysis
    CRISIS_PERIODS = [
        CrisisPeriod(
            name="2008 Financial Crisis",
            crisis_type=CrisisType.FINANCIAL_CRISIS,
            start_date=datetime(2008, 9, 1),
            end_date=datetime(2009, 3, 31),
            description="Global financial crisis triggered by subprime mortgage collapse",
            peak_to_trough_dates=(datetime(2007, 10, 9), datetime(2009, 3, 9)),
            market_decline_pct=-56.8  # S&P 500 peak to trough
        ),
        CrisisPeriod(
            name="2020 COVID-19 Crash",
            crisis_type=CrisisType.PANDEMIC,
            start_date=datetime(2020, 2, 19),
            end_date=datetime(2020, 3, 23),
            description="Pandemic-driven market crash with rapid recovery",
            peak_to_trough_dates=(datetime(2020, 2, 19), datetime(2020, 3, 23)),
            market_decline_pct=-33.9  # S&P 500 decline in 33 days
        ),
        CrisisPeriod(
            name="2022 Bear Market",
            crisis_type=CrisisType.INTEREST_RATE_SHOCK,
            start_date=datetime(2022, 1, 3),
            end_date=datetime(2022, 10, 12),
            description="Bear market driven by inflation and interest rate hikes",
            peak_to_trough_dates=(datetime(2022, 1, 3), datetime(2022, 10, 12)),
            market_decline_pct=-25.4  # S&P 500 decline
        )
    ]
    
    def __init__(self, portfolio_engine: OptimizedPortfolioEngine):
        """
        Initialize with optimized portfolio engine
        
        Args:
            portfolio_engine: OptimizedPortfolioEngine instance for backtesting
        """
        self.portfolio_engine = portfolio_engine
        
    def analyze_crisis_periods(
        self,
        allocation: Dict[str, float],
        crisis_periods: Optional[List[CrisisPeriod]] = None
    ) -> Tuple[List[CrisisAnalysisResult], StressTestSummary]:
        """
        Analyze portfolio performance across major crisis periods
        
        Args:
            allocation: Portfolio allocation dictionary (symbol -> weight)
            crisis_periods: List of crisis periods to analyze (defaults to all major crises)
            
        Returns:
            Tuple of (individual crisis results, stress test summary)
        """
        if crisis_periods is None:
            crisis_periods = self.CRISIS_PERIODS
            
        crisis_results = []
        
        for crisis in crisis_periods:
            try:
                result = self._analyze_single_crisis(allocation, crisis)
                crisis_results.append(result)
            except Exception as e:
                print(f"Warning: Failed to analyze crisis {crisis.name}: {e}")
                continue
                
        # Generate summary statistics
        summary = self._calculate_stress_test_summary(crisis_results)
        
        return crisis_results, summary
        
    def _analyze_single_crisis(
        self,
        allocation: Dict[str, float],
        crisis: CrisisPeriod
    ) -> CrisisAnalysisResult:
        """Analyze portfolio performance during a single crisis period"""
        
        # Filter allocation to only include assets that existed during the crisis period
        # VTIAX started in 2010, so skip 2008 crisis analysis if it's in allocation
        filtered_allocation = allocation.copy()
        
        if crisis.name == "2008 Financial Crisis" and "VTIAX" in allocation:
            # For 2008 crisis, redistribute VTIAX allocation to VTI
            vtiax_weight = filtered_allocation.pop("VTIAX", 0)
            if "VTI" in filtered_allocation:
                filtered_allocation["VTI"] += vtiax_weight
            else:
                filtered_allocation["VTI"] = vtiax_weight
        
        # Normalize allocation to ensure it sums to 1.0
        total_weight = sum(filtered_allocation.values())
        if total_weight > 0:
            filtered_allocation = {k: v/total_weight for k, v in filtered_allocation.items()}
        
        # Backtest during crisis period
        crisis_result = self.portfolio_engine.backtest_portfolio(
            allocation=filtered_allocation,
            start_date=crisis.start_date.strftime("%Y-%m-%d"),
            end_date=crisis.end_date.strftime("%Y-%m-%d")
        )
        
        # Calculate crisis-specific metrics
        crisis_decline = self._safe_float(crisis_result['performance_metrics']['total_return'])
        
        # Calculate recovery time if we have post-crisis data
        recovery_time_days = None
        recovery_velocity = None
        
        try:
            # Use simplified recovery estimation to avoid date range issues
            # This is a basic estimate - full recovery analysis should use RecoveryTimeAnalyzer
            if abs(crisis_decline) > 0.10:  # Only for significant declines
                # Estimate recovery time based on historical patterns
                # Conservative estimate: 12-18 months for major declines
                estimated_months = abs(crisis_decline) * 24  # 24 months per 100% decline
                recovery_time_days = int(estimated_months * 30.44)  # Convert to days
                recovery_velocity = abs(crisis_decline) / estimated_months if estimated_months > 0 else None
        except Exception as e:
            # Recovery calculation is optional, don't fail the entire analysis
            pass
            
        # Calculate resilience score (0-100)
        resilience_score = self._calculate_resilience_score(
            crisis_decline, recovery_time_days, crisis.market_decline_pct
        )
        
        return CrisisAnalysisResult(
            crisis=crisis,
            portfolio_performance=crisis_result['performance_metrics'],
            crisis_decline=crisis_decline,
            recovery_time_days=recovery_time_days,
            recovery_velocity=recovery_velocity,
            resilience_score=resilience_score
        )
        
    def _calculate_resilience_score(
        self,
        portfolio_decline: float,
        recovery_time_days: Optional[int],
        market_decline: Optional[float]
    ) -> float:
        """
        Calculate portfolio resilience score (0-100)
        
        Scoring factors:
        - Relative performance vs market during crisis (40% weight)
        - Absolute decline magnitude (30% weight)  
        - Recovery speed (30% weight, if available)
        """
        score = 0.0
        
        # Factor 1: Relative performance vs market (40% weight)
        if market_decline is not None and market_decline != 0:
            relative_performance = portfolio_decline / market_decline
            if relative_performance < 1.0:  # Portfolio declined less than market
                relative_score = min(40.0, 40.0 * (1.0 - relative_performance))
            else:
                relative_score = max(0.0, 40.0 * (2.0 - relative_performance))
            score += relative_score
        else:
            # Default score if no market comparison available
            score += 20.0
            
        # Factor 2: Absolute decline magnitude (30% weight)
        abs_decline = abs(portfolio_decline)
        if abs_decline <= 0.05:  # <= 5% decline
            decline_score = 30.0
        elif abs_decline <= 0.15:  # <= 15% decline
            decline_score = 30.0 * (1.0 - (abs_decline - 0.05) / 0.10)
        elif abs_decline <= 0.35:  # <= 35% decline
            decline_score = 15.0 * (1.0 - (abs_decline - 0.15) / 0.20)
        else:
            decline_score = 0.0
        score += decline_score
        
        # Factor 3: Recovery speed (30% weight)
        if recovery_time_days is not None:
            if recovery_time_days <= 90:  # Quick recovery (3 months)
                recovery_score = 30.0
            elif recovery_time_days <= 365:  # Recovery within 1 year
                recovery_score = 30.0 * (1.0 - (recovery_time_days - 90) / 275)
            elif recovery_time_days <= 730:  # Recovery within 2 years  
                recovery_score = 10.0 * (1.0 - (recovery_time_days - 365) / 365)
            else:
                recovery_score = 0.0
            score += recovery_score
        else:
            # Default recovery score if data not available
            score += 15.0
            
        return max(0.0, min(100.0, score))
        
    def _calculate_stress_test_summary(
        self,
        crisis_results: List[CrisisAnalysisResult]
    ) -> StressTestSummary:
        """Calculate summary statistics across all crisis periods"""
        
        if not crisis_results:
            return StressTestSummary(
                crisis_results=[],
                avg_crisis_decline=0.0,
                worst_crisis_decline=0.0, 
                best_crisis_decline=0.0,
                avg_recovery_time_days=None,
                overall_resilience_score=0.0,
                crisis_consistency=0.0
            )
            
        # Extract metrics
        declines = [result.crisis_decline for result in crisis_results]
        recovery_times = [
            result.recovery_time_days for result in crisis_results 
            if result.recovery_time_days is not None
        ]
        resilience_scores = [result.resilience_score for result in crisis_results]
        
        # Calculate summary statistics
        avg_crisis_decline = self._safe_float(np.mean(declines))
        worst_crisis_decline = self._safe_float(np.min(declines))  # Most negative
        best_crisis_decline = self._safe_float(np.max(declines))   # Least negative
        
        avg_recovery_time = None
        if recovery_times:
            avg_recovery_time = self._safe_float(np.mean(recovery_times))
            
        overall_resilience = self._safe_float(np.mean(resilience_scores))
        
        # Crisis consistency (inverse of coefficient of variation)
        if len(declines) > 1 and np.std(declines) > 0:
            cv = np.std(declines) / abs(np.mean(declines)) if np.mean(declines) != 0 else 0
            crisis_consistency = self._safe_float(max(0.0, 1.0 - cv))
        else:
            crisis_consistency = 1.0
            
        return StressTestSummary(
            crisis_results=crisis_results,
            avg_crisis_decline=avg_crisis_decline,
            worst_crisis_decline=worst_crisis_decline,
            best_crisis_decline=best_crisis_decline,
            avg_recovery_time_days=avg_recovery_time,
            overall_resilience_score=overall_resilience,
            crisis_consistency=crisis_consistency
        )
        
    def _safe_float(self, value) -> float:
        """Convert to safe float that can be JSON serialized"""
        if value is None or np.isnan(value) or np.isinf(value):
            return 0.0
        return float(value)
        
    def get_crisis_periods(self) -> List[CrisisPeriod]:
        """Get list of available crisis periods for analysis"""
        return self.CRISIS_PERIODS.copy()
        
    def analyze_custom_crisis(
        self,
        allocation: Dict[str, float],
        start_date: datetime,
        end_date: datetime,
        crisis_name: str = "Custom Crisis",
        crisis_type: CrisisType = CrisisType.BEAR_MARKET
    ) -> CrisisAnalysisResult:
        """
        Analyze portfolio performance during a custom crisis period
        
        Args:
            allocation: Portfolio allocation dictionary
            start_date: Crisis start date
            end_date: Crisis end date  
            crisis_name: Name for the crisis period
            crisis_type: Type of crisis
            
        Returns:
            CrisisAnalysisResult for the custom period
        """
        custom_crisis = CrisisPeriod(
            name=crisis_name,
            crisis_type=crisis_type,
            start_date=start_date,
            end_date=end_date,
            description=f"Custom crisis period from {start_date.date()} to {end_date.date()}"
        )
        
        return self._analyze_single_crisis(allocation, custom_crisis)
