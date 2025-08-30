"""
Analysis Routes for Portfolio Backtesting API

Advanced analytics endpoints including rolling period analysis, crisis stress testing,
recovery analysis, timeline-based risk recommendations, and extended historical analysis.

This is the complete restored version with all Sprint 2 advanced analytics engines.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import logging
import numpy as np

def sanitize_float(value):
    """Sanitize float values for JSON serialization"""
    if value is None:
        return None
    if isinstance(value, (int, bool)):
        return value
    if isinstance(value, float):
        if not np.isfinite(value):
            return 0.0
        return float(value)
    return value

def sanitize_dict(data):
    """Recursively sanitize dictionary for JSON serialization"""
    if isinstance(data, dict):
        return {k: sanitize_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_dict(item) for item in data]
    else:
        return sanitize_float(data)

from ..core.rolling_period_analyzer import (
    RollingPeriodAnalyzer, 
    RollingPeriodResult, 
    RollingPeriodSummary
)
from ..core.crisis_period_analyzer import CrisisPeriodAnalyzer
from ..core.recovery_time_analyzer import RecoveryTimeAnalyzer  
from ..core.timeline_risk_analyzer import TimelineRiskAnalyzer
from ..core.rebalancing_strategy_analyzer import RebalancingStrategyAnalyzer
from ..core.extended_historical_analyzer import ExtendedHistoricalAnalyzer
from ..core.portfolio_engine_optimized import OptimizedPortfolioEngine
from ..models.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyze", tags=["analysis"])

# ========================================================================================
# REQUEST/RESPONSE MODELS
# ========================================================================================

class PortfolioAllocation(BaseModel):
    """Base portfolio allocation model"""
    allocation: Dict[str, float] = Field(
        ...,
        description="Portfolio allocation (symbol -> weight)",
        example={"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1}
    )

    @validator('allocation')
    def validate_allocation(cls, v):
        total = sum(v.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Allocation must sum to 1.0, got {total:.3f}")
        return v

class RollingPeriodAnalysisRequest(PortfolioAllocation):
    """Request model for rolling period analysis"""
    period_years: List[int] = Field(
        ..., 
        description="List of rolling window sizes in years",
        example=[3, 5, 10]
    )
    start_date: Optional[datetime] = Field(None, description="Analysis start date")
    end_date: Optional[datetime] = Field(None, description="Analysis end date")

    @validator('period_years')
    def validate_periods(cls, v):
        if len(v) > 5:
            raise ValueError("Maximum 5 periods allowed")
        if len(v) < 1:
            raise ValueError("At least 1 period required")
        for period in v:
            if period < 1 or period > 20:
                raise ValueError(f"Period years must be between 1 and 20, got {period}")
        return sorted(v)

class StressTestRequest(PortfolioAllocation):
    """Request model for crisis stress testing"""
    crisis_periods: Optional[List[str]] = Field(
        None, 
        description="Specific crisis periods to analyze",
        example=["2008-financial-crisis", "2020-covid-crash", "2022-bear-market"]
    )

class RecoveryAnalysisRequest(PortfolioAllocation):
    """Request model for recovery time analysis"""
    start_date: Optional[datetime] = Field(None, description="Analysis start date")
    end_date: Optional[datetime] = Field(None, description="Analysis end date")
    min_drawdown_pct: float = Field(0.05, ge=0.01, le=0.5, description="Minimum drawdown threshold")

class TimelineRiskRequest(PortfolioAllocation):
    """Request model for timeline-based risk analysis"""
    investment_horizon_years: int = Field(10, ge=1, le=50, description="Investment timeline in years")
    age: Optional[int] = Field(None, ge=18, le=100, description="Investor age")
    risk_tolerance: str = Field("moderate", description="Risk tolerance level")

class ExtendedHistoricalRequest(PortfolioAllocation):
    """Request model for extended historical analysis"""
    start_date: Optional[datetime] = Field(None, description="Analysis start date")
    end_date: Optional[datetime] = Field(None, description="Analysis end date")

class PeriodComparisonRequest(PortfolioAllocation):
    """Request model for period performance comparison"""
    comparison_periods: List[int] = Field([10, 20], description="List of periods in years to compare")

class PortfolioComparisonRequest(BaseModel):
    """Request model for comparing multiple portfolios"""
    portfolios: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Named portfolios to compare",
        example={
            "Conservative": {"VTI": 0.3, "BND": 0.7},
            "Aggressive": {"VTI": 0.8, "VTIAX": 0.2}
        }
    )
    period_years: int = Field(5, ge=1, le=20, description="Rolling period length")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# ========================================================================================
# DEPENDENCY FUNCTIONS
# ========================================================================================

def get_rolling_period_analyzer() -> RollingPeriodAnalyzer:
    """Get configured rolling period analyzer instance"""
    try:
        portfolio_engine = OptimizedPortfolioEngine()
        return RollingPeriodAnalyzer(portfolio_engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize analyzer: {str(e)}")

def get_crisis_period_analyzer() -> CrisisPeriodAnalyzer:
    """Get configured crisis period analyzer instance"""
    try:
        portfolio_engine = OptimizedPortfolioEngine()
        return CrisisPeriodAnalyzer(portfolio_engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize crisis analyzer: {str(e)}")

def get_recovery_analyzer() -> RecoveryTimeAnalyzer:
    """Get configured recovery analyzer instance"""
    try:
        portfolio_engine = OptimizedPortfolioEngine()
        return RecoveryTimeAnalyzer(portfolio_engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize recovery analyzer: {str(e)}")

def get_timeline_analyzer() -> TimelineRiskAnalyzer:
    """Get configured timeline analyzer instance"""
    try:
        portfolio_engine = OptimizedPortfolioEngine()
        return TimelineRiskAnalyzer(portfolio_engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize timeline analyzer: {str(e)}")

def get_extended_analyzer() -> ExtendedHistoricalAnalyzer:
    """Get configured extended historical analyzer instance"""
    try:
        return ExtendedHistoricalAnalyzer()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize extended analyzer: {str(e)}")

# ========================================================================================
# ROLLING PERIOD ANALYSIS ENDPOINTS
# ========================================================================================

@router.post("/rolling-periods")
async def analyze_rolling_periods(
    request: RollingPeriodAnalysisRequest,
    analyzer: RollingPeriodAnalyzer = Depends(get_rolling_period_analyzer)
):
    """
    Unified rolling period analysis endpoint
    
    Analyze portfolio performance across rolling time windows. Supports both single-period
    analysis and multi-period comparison for comprehensive performance consistency evaluation.
    """
    try:
        start_time = datetime.now()
        results = {}
        
        # Analyze each requested period
        for period_years in request.period_years:
            periods, summary = analyzer.analyze_rolling_periods(
                allocation=request.allocation,
                period_years=period_years,
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            # Convert results with proper datetime serialization
            results[period_years] = {
                "summary": {
                    "period_years": summary.period_years,
                    "total_windows": summary.total_windows,
                    "avg_cagr": summary.avg_cagr,
                    "min_cagr": summary.min_cagr,
                    "max_cagr": summary.max_cagr,
                    "cagr_std": summary.cagr_std,
                    "avg_volatility": summary.avg_volatility,
                    "avg_sharpe": summary.avg_sharpe,
                    "avg_max_drawdown": summary.avg_max_drawdown,
                    "consistency_score": summary.consistency_score,
                    "worst_period": {
                        "start_date": summary.worst_period.start_date.isoformat(),
                        "end_date": summary.worst_period.end_date.isoformat(),
                        "cagr": summary.worst_period.cagr,
                        "volatility": summary.worst_period.volatility,
                        "sharpe_ratio": summary.worst_period.sharpe_ratio,
                        "max_drawdown": summary.worst_period.max_drawdown,
                        "total_return": summary.worst_period.total_return
                    },
                    "best_period": {
                        "start_date": summary.best_period.start_date.isoformat(),
                        "end_date": summary.best_period.end_date.isoformat(),
                        "cagr": summary.best_period.cagr,
                        "volatility": summary.best_period.volatility,
                        "sharpe_ratio": summary.best_period.sharpe_ratio,
                        "max_drawdown": summary.best_period.max_drawdown,
                        "total_return": summary.best_period.total_return
                    }
                },
                "periods": [
                    {
                        "start_date": period.start_date.isoformat(),
                        "end_date": period.end_date.isoformat(),
                        "period_years": period.period_years,
                        "cagr": period.cagr,
                        "volatility": period.volatility,
                        "sharpe_ratio": period.sharpe_ratio,
                        "max_drawdown": period.max_drawdown,
                        "total_return": period.total_return
                    }
                    for period in periods
                ]
            }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Generate comparative insights if multiple periods
        comparative_insights = None
        if len(request.period_years) > 1:
            comparative_insights = {
                "period_comparison": {
                    period: {
                        "avg_cagr": results[period]["summary"]["avg_cagr"],
                        "consistency_score": results[period]["summary"]["consistency_score"],
                        "avg_sharpe": results[period]["summary"]["avg_sharpe"],
                        "total_windows": results[period]["summary"]["total_windows"]
                    }
                    for period in request.period_years
                },
                "analysis_type": "multi_period" if len(request.period_years) > 1 else "single_period"
            }
        
        return {
            "results": results,
            "comparative_insights": comparative_insights,
            "execution_time_seconds": execution_time
        }
        
    except Exception as e:
        logger.error(f"Error in rolling periods analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rolling-periods/compare")
async def compare_portfolios_rolling(
    request: PortfolioComparisonRequest,
    analyzer: RollingPeriodAnalyzer = Depends(get_rolling_period_analyzer)
):
    """
    Compare multiple portfolios using rolling period analysis
    
    Analyze and rank different portfolio allocations based on their
    rolling period performance, consistency, and risk-adjusted returns.
    """
    try:
        start_time = datetime.now()
        portfolio_results = {}
        portfolio_scores = {}
        
        # Analyze each portfolio
        for name, allocation in request.portfolios.items():
            periods, summary = analyzer.analyze_rolling_periods(
                allocation=allocation,
                period_years=request.period_years,
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            portfolio_results[name] = {
                "summary": {
                    "period_years": summary.period_years,
                    "total_windows": summary.total_windows,
                    "avg_cagr": summary.avg_cagr,
                    "min_cagr": summary.min_cagr,
                    "max_cagr": summary.max_cagr,
                    "cagr_std": summary.cagr_std,
                    "avg_volatility": summary.avg_volatility,
                    "avg_sharpe": summary.avg_sharpe,
                    "avg_max_drawdown": summary.avg_max_drawdown,
                    "consistency_score": summary.consistency_score
                }
            }
            
            # Calculate ranking score
            rank_score = summary.avg_sharpe * (1 - summary.consistency_score * 0.5)
            portfolio_scores[name] = {
                "rank_score": rank_score,
                "avg_cagr": summary.avg_cagr,
                "avg_sharpe": summary.avg_sharpe,
                "consistency_score": summary.consistency_score,
                "avg_max_drawdown": summary.avg_max_drawdown
            }
        
        # Create ranking
        ranking = []
        for rank, (name, scores) in enumerate(
            sorted(portfolio_scores.items(), key=lambda x: x[1]["rank_score"], reverse=True), 1
        ):
            ranking.append({
                "rank": rank,
                "portfolio_name": name,
                "rank_score": scores["rank_score"],
                "avg_cagr": scores["avg_cagr"],
                "avg_sharpe": scores["avg_sharpe"],
                "consistency_score": scores["consistency_score"],
                "avg_max_drawdown": scores["avg_max_drawdown"]
            })
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "portfolio_results": portfolio_results,
            "ranking": ranking,
            "execution_time_seconds": execution_time
        }
        
    except Exception as e:
        logger.error(f"Error in portfolio comparison: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ========================================================================================
# CRISIS STRESS TESTING ENDPOINTS
# ========================================================================================

@router.post("/stress-test")
async def stress_test_portfolio(
    request: StressTestRequest,
    analyzer: CrisisPeriodAnalyzer = Depends(get_crisis_period_analyzer),
    db = Depends(get_db)
):
    """
    Stress test portfolio performance during major historical crises
    
    Analyzes how the portfolio would have performed during major market downturns
    including the 2008 Financial Crisis, 2020 COVID crash, and 2022 bear market.
    """
    try:
        # Get available crisis periods
        all_crises = analyzer.get_crisis_periods()
        
        # Filter by requested periods if specified
        if request.crisis_periods:
            # Map names to crisis objects
            crisis_map = {crisis.name.lower().replace(' ', '-'): crisis for crisis in all_crises}
            selected_crises = []
            
            for period_name in request.crisis_periods:
                normalized_name = period_name.lower().replace('_', '-')
                if normalized_name in crisis_map:
                    selected_crises.append(crisis_map[normalized_name])
                else:
                    # Try partial matching
                    for key, crisis in crisis_map.items():
                        if period_name.lower().replace('_', '-') in key or key in period_name.lower().replace('_', '-'):
                            selected_crises.append(crisis)
                            break
            
            if not selected_crises:
                raise HTTPException(status_code=400, detail=f"No matching crisis periods found for: {request.crisis_periods}")
                
            crisis_results, summary = analyzer.analyze_crisis_periods(
                allocation=request.allocation,
                crisis_periods=selected_crises
            )
        else:
            # Use all available crisis periods
            crisis_results, summary = analyzer.analyze_crisis_periods(
                allocation=request.allocation
            )
        
        # Convert results to JSON-serializable format
        return {
            "crisis_results": [
                {
                    "crisis_name": result.crisis.name,
                    "crisis_type": result.crisis.crisis_type,
                    "start_date": result.crisis.start_date.isoformat(),
                    "end_date": result.crisis.end_date.isoformat(),
                    "description": result.crisis.description,
                    "portfolio_performance": result.portfolio_performance,
                    "crisis_decline": result.crisis_decline,
                    "recovery_time_days": result.recovery_time_days,
                    "recovery_velocity": result.recovery_velocity,
                    "resilience_score": result.resilience_score
                }
                for result in crisis_results
            ],
            "summary": {
                "crisis_results_count": len(crisis_results),
                "avg_crisis_decline": summary.avg_crisis_decline,
                "worst_crisis_decline": summary.worst_crisis_decline,
                "best_crisis_decline": summary.best_crisis_decline,
                "avg_recovery_time_days": summary.avg_recovery_time_days,
                "overall_resilience_score": summary.overall_resilience_score,
                "crisis_consistency": summary.crisis_consistency
            }
        }
        
    except Exception as e:
        logger.error(f"Error in crisis stress test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/crisis-periods")
async def get_available_crisis_periods(
    analyzer: CrisisPeriodAnalyzer = Depends(get_crisis_period_analyzer)
):
    """
    Get list of available crisis periods for analysis
    
    Returns metadata about major historical market crises that can be
    used for stress testing portfolio performance.
    """
    try:
        return analyzer.get_crisis_periods()
        
    except Exception as e:
        logger.error(f"Error getting crisis periods: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get crisis periods: {str(e)}")

# ========================================================================================
# RECOVERY ANALYSIS ENDPOINTS  
# ========================================================================================

@router.post("/recovery-analysis")
async def analyze_recovery_patterns(
    request: RecoveryAnalysisRequest,
    analyzer: RecoveryTimeAnalyzer = Depends(get_recovery_analyzer),
    db = Depends(get_db)
):
    """
    Analyze how quickly portfolio recovers from major drawdowns
    
    Identifies drawdown periods, recovery velocity, and overall resilience
    to help understand portfolio behavior during market stress.
    """
    try:
        result = analyzer.analyze_recovery_patterns(
            allocation=request.allocation,
            start_date=request.start_date,
            end_date=request.end_date,
            min_drawdown_pct=request.min_drawdown_pct
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in recovery analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# ========================================================================================
# TIMELINE RISK ANALYSIS ENDPOINTS
# ========================================================================================

@router.post("/timeline-risk")
async def analyze_timeline_risk(
    request: TimelineRiskRequest,
    analyzer: TimelineRiskAnalyzer = Depends(get_timeline_analyzer),
    db = Depends(get_db)
):
    """
    Provide timeline-aware portfolio risk analysis and recommendations
    
    Considers investment horizon, age, and risk tolerance to suggest
    appropriate portfolio allocations and risk management strategies.
    """
    try:
        # Create investor profile
        from ..core.timeline_risk_analyzer import InvestorProfile, RiskTolerance, LifeStage
        
        # Determine life stage from age
        age = request.age or 35  # Default age if not provided
        if age < 35:
            life_stage = LifeStage.YOUNG_ACCUMULATOR
        elif age < 50:
            life_stage = LifeStage.MID_CAREER
        elif age < 65:
            life_stage = LifeStage.PRE_RETIREMENT
        else:
            life_stage = LifeStage.RETIREMENT
            
        investor_profile = InvestorProfile(
            age=age,
            investment_horizon_years=request.investment_horizon_years,
            risk_tolerance=RiskTolerance(request.risk_tolerance.lower()),
            life_stage=life_stage
        )
        
        result = analyzer.generate_timeline_recommendation(
            investor_profile=investor_profile,
            current_allocation=request.allocation
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in timeline risk analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# ========================================================================================
# EXTENDED HISTORICAL ANALYSIS ENDPOINTS
# ========================================================================================

@router.post("/extended-historical")
async def analyze_extended_historical(
    request: ExtendedHistoricalRequest,
    analyzer: ExtendedHistoricalAnalyzer = Depends(get_extended_analyzer),
    db = Depends(get_db)
):
    """
    Perform comprehensive 20-year historical analysis
    
    Provides advanced market cycle analysis, correlation evolution tracking,
    regime change detection, and long-term vs short-term performance comparisons.
    """
    try:
        result = analyzer.analyze_extended_historical_performance(
            allocation=request.allocation,
            start_date=request.start_date,
            end_date=request.end_date,
            db_session=db
        )
        
        # Convert dataclass to dictionary with proper datetime serialization
        response_dict = {
            "analysis_period_start": result.analysis_period_start.isoformat(),
            "analysis_period_end": result.analysis_period_end.isoformat(),
            "total_years": result.total_years,
            "full_period_cagr": result.full_period_cagr,
            "first_decade_cagr": result.first_decade_cagr,
            "second_decade_cagr": result.second_decade_cagr,
            "market_regimes": [
                {
                    "start_date": regime.start_date.isoformat(),
                    "end_date": regime.end_date.isoformat(),
                    "regime_type": regime.regime_type,
                    "duration_days": regime.duration_days,
                    "market_return": regime.market_return,
                    "volatility": regime.volatility,
                    "description": regime.description
                } for regime in result.market_regimes
            ],
            "regime_performance": result.regime_performance,
            "correlation_periods": [
                {
                    "start_date": period.start_date.isoformat(),
                    "end_date": period.end_date.isoformat(),
                    "period_years": period.period_years,
                    "correlation_matrix": period.correlation_matrix,
                    "avg_correlation": period.avg_correlation,
                    "diversification_ratio": period.diversification_ratio,
                    "dominant_factor_exposure": period.dominant_factor_exposure
                } for period in result.correlation_periods
            ],
            "correlation_trend": result.correlation_trend,
            "diversification_effectiveness": result.diversification_effectiveness,
            "regime_transition_alpha": result.regime_transition_alpha,
            "adaptation_recommendations": result.adaptation_recommendations,
            "volatility_clustering_periods": [
                {
                    "start_date": period[0].isoformat(),
                    "end_date": period[1].isoformat()
                } for period in result.volatility_clustering_periods
            ],
            "tail_risk_evolution": result.tail_risk_evolution
        }
        
        # Sanitize all float values to prevent JSON serialization errors
        sanitized_response = sanitize_dict(response_dict)
        return sanitized_response
        
    except Exception as e:
        logger.error(f"Error in extended historical analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/period-comparison")
async def compare_period_performance(
    request: PeriodComparisonRequest,
    analyzer: ExtendedHistoricalAnalyzer = Depends(get_extended_analyzer),
    db = Depends(get_db)
):
    """
    Compare portfolio performance across different historical time periods
    
    Analyzes how the portfolio would have performed over different time horizons
    to understand long-term consistency and performance patterns.
    """
    try:
        result = analyzer.compare_period_performance(
            allocation=request.allocation,
            comparison_periods=request.comparison_periods,
            db_session=db
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in period comparison analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# ========================================================================================
# EXAMPLES AND DOCUMENTATION
# ========================================================================================

@router.get("/examples")
async def get_analysis_examples():
    """
    Get example requests for all analysis endpoints
    
    Returns comprehensive examples showing how to use each endpoint
    with realistic portfolio allocations and parameters.
    """
    return {
        "rolling_period_analysis": {
            "single_period": {
                "endpoint": "POST /api/analyze/rolling-periods",
                "description": "Single period rolling analysis",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "period_years": [5],
                    "start_date": "2010-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                }
            },
            "multi_period": {
                "endpoint": "POST /api/analyze/rolling-periods",
                "description": "Multi-period comparison analysis",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "period_years": [3, 5, 10],
                    "start_date": "2010-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                }
            }
        },
        "crisis_stress_test": {
            "endpoint": "POST /api/analyze/stress-test",
            "description": "Crisis period stress testing",
            "example_request": {
                "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                "crisis_periods": ["2008-financial-crisis", "2020-covid-crash", "2022-bear-market"]
            }
        },
        "recovery_analysis": {
            "endpoint": "POST /api/analyze/recovery-analysis",
            "description": "Recovery time analysis from drawdowns",
            "example_request": {
                "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                "min_drawdown_pct": 0.10,
                "start_date": "2010-01-01T00:00:00Z",
                "end_date": "2024-01-01T00:00:00Z"
            }
        },
        "timeline_risk": {
            "endpoint": "POST /api/analyze/timeline-risk",
            "description": "Timeline-based risk recommendations",
            "example_request": {
                "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                "investment_horizon_years": 15,
                "age": 35,
                "risk_tolerance": "moderate"
            }
        },
        "extended_historical": {
            "endpoint": "POST /api/analyze/extended-historical",
            "description": "20-year market cycle analysis",
            "example_request": {
                "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                "start_date": "2004-01-01T00:00:00Z",
                "end_date": "2024-01-01T00:00:00Z"
            }
        },
        "period_comparison": {
            "endpoint": "POST /api/analyze/period-comparison", 
            "description": "Compare different time periods",
            "example_request": {
                "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                "comparison_periods": [10, 20]
            }
        },
        "portfolio_comparison": {
            "endpoint": "POST /api/analyze/rolling-periods/compare",
            "description": "Compare multiple portfolios",
            "example_request": {
                "portfolios": {
                    "Conservative": {"VTI": 0.3, "BND": 0.7},
                    "Balanced": {"VTI": 0.6, "BND": 0.4},
                    "Aggressive": {"VTI": 0.8, "VTIAX": 0.2}
                },
                "period_years": 5
            }
        }
    }
