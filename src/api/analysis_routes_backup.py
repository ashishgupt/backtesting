"""
Analysis Routes for Portfolio Backtesting API

Advanced analytics endpoints including rolling period analysis, 
stress testing, and risk assessment capabilities.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

from ..core.rolling_period_analyzer import (
    RollingPeriodAnalyzer, 
    RollingPeriodResult, 
    RollingPeriodSummary
)
from ..core.portfolio_engine_optimized import OptimizedPortfolioEngine


# Request/Response Models
class RollingPeriodAnalysisRequest(BaseModel):
    """Request model for rolling period analysis"""
    allocation: Dict[str, float] = Field(
        ...,
        description="Portfolio allocation (symbol -> weight)",
        example={"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1}
    )
    period_years: int = Field(
        ..., 
        ge=1, 
        le=20, 
        description="Rolling window size in years"
    )
    start_date: Optional[datetime] = Field(
        None, 
        description="Analysis start date (ISO format)"
    )
    end_date: Optional[datetime] = Field(
        None, 
        description="Analysis end date (ISO format)"
    )
    
    @validator('allocation')
    def validate_allocation(cls, v):
        """Validate portfolio allocation"""
        if not v:
            raise ValueError("Allocation cannot be empty")
            
        total_weight = sum(v.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Allocation weights must sum to 1.0, got {total_weight}")
            
        for symbol, weight in v.items():
            if weight < 0:
                raise ValueError(f"Negative weight not allowed: {symbol} = {weight}")
                
        return v


class MultiPeriodAnalysisRequest(BaseModel):
    """Request model for multiple rolling period analysis"""
    allocation: Dict[str, float] = Field(
        ...,
        description="Portfolio allocation (symbol -> weight)",
        example={"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1}
    )
    period_years_list: List[int] = Field(
        ...,
        description="List of rolling window sizes in years",
        example=[3, 5, 10]
    )
    start_date: Optional[datetime] = Field(None)
    end_date: Optional[datetime] = Field(None)
    
    @validator('allocation')
    def validate_allocation(cls, v):
        """Validate portfolio allocation"""
        if not v:
            raise ValueError("Allocation cannot be empty")
            
        total_weight = sum(v.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Allocation weights must sum to 1.0, got {total_weight}")
            
        return v
        
    @validator('period_years_list')
    def validate_periods(cls, v):
        """Validate period years list"""
        if not v:
            raise ValueError("Period years list cannot be empty")
            
        for period in v:
            if period < 1 or period > 20:
                raise ValueError(f"Period years must be between 1 and 20, got {period}")
                
        return sorted(v)  # Sort for consistent results


class PortfolioComparisonRequest(BaseModel):
    """Request model for comparing multiple portfolios with rolling analysis"""
    portfolios: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Named portfolios to compare",
        example={
            "Conservative": {"VTI": 0.3, "BND": 0.7},
            "Aggressive": {"VTI": 0.8, "VTIAX": 0.2}
        }
    )
    period_years: int = Field(..., ge=1, le=20)
    start_date: Optional[datetime] = Field(None)
    end_date: Optional[datetime] = Field(None)
    
    @validator('portfolios')
    def validate_portfolios(cls, v):
        """Validate all portfolio allocations"""
        if not v:
            raise ValueError("Portfolios dictionary cannot be empty")
            
        for name, allocation in v.items():
            if not allocation:
                raise ValueError(f"Portfolio '{name}' allocation cannot be empty")
                
            total_weight = sum(allocation.values())
            if abs(total_weight - 1.0) > 0.001:
                raise ValueError(f"Portfolio '{name}' weights must sum to 1.0, got {total_weight}")
                
        return v


# Response Models
class RollingPeriodResultModel(BaseModel):
    """Rolling period result model for API responses"""
    start_date: datetime
    end_date: datetime
    period_years: int
    cagr: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    total_return: float


class RollingPeriodSummaryModel(BaseModel):
    """Rolling period summary model for API responses"""
    period_years: int
    total_windows: int
    avg_cagr: float
    min_cagr: float
    max_cagr: float
    cagr_std: float
    avg_volatility: float
    avg_sharpe: float
    avg_max_drawdown: float
    worst_period: RollingPeriodResultModel
    best_period: RollingPeriodResultModel
    consistency_score: float


class RollingPeriodAnalysisResponse(BaseModel):
    """Response model for rolling period analysis"""
    summary: RollingPeriodSummaryModel
    periods: List[RollingPeriodResultModel]
    insights: Dict[str, Any]
    execution_time_seconds: float


class MultiPeriodAnalysisResponse(BaseModel):
    """Response model for multiple period analysis"""
    results: Dict[int, RollingPeriodAnalysisResponse]
    comparative_insights: Dict[str, Any]
    execution_time_seconds: float


class PortfolioComparisonResponse(BaseModel):
    """Response model for portfolio comparison"""
    portfolio_results: Dict[str, RollingPeriodAnalysisResponse]
    ranking: List[Dict[str, Any]]
    execution_time_seconds: float


# Dependency to get rolling period analyzer
def get_rolling_period_analyzer() -> RollingPeriodAnalyzer:
    """Get configured rolling period analyzer instance"""
    try:
        portfolio_engine = OptimizedPortfolioEngine()  # Uses default db session
        return RollingPeriodAnalyzer(portfolio_engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize analyzer: {str(e)}")


# Router configuration
router = APIRouter(prefix="/api/analyze", tags=["analysis"])


@router.post("/rolling-periods", response_model=RollingPeriodAnalysisResponse)
async def analyze_rolling_periods(
    request: RollingPeriodAnalysisRequest,
    analyzer: RollingPeriodAnalyzer = Depends(get_rolling_period_analyzer)
):
    """
    Analyze portfolio performance across rolling time windows
    
    This endpoint provides detailed analysis of how a portfolio performs
    across different time periods, helping investors understand performance
    consistency and identify best/worst performing periods.
    
    Returns summary statistics, individual period results, and actionable insights.
    """
    try:
        start_time = datetime.now()
        
        # Perform rolling period analysis
        periods, summary = analyzer.analyze_rolling_periods(
            allocation=request.allocation,
            period_years=request.period_years,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Generate insights
        insights = analyzer.generate_rolling_insights(
            summaries={request.period_years: summary},
            allocation=request.allocation
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Convert to response models
        summary_model = RollingPeriodSummaryModel(
            period_years=summary.period_years,
            total_windows=summary.total_windows,
            avg_cagr=summary.avg_cagr,
            min_cagr=summary.min_cagr,
            max_cagr=summary.max_cagr,
            cagr_std=summary.cagr_std,
            avg_volatility=summary.avg_volatility,
            avg_sharpe=summary.avg_sharpe,
            avg_max_drawdown=summary.avg_max_drawdown,
            worst_period=RollingPeriodResultModel(**summary.worst_period.__dict__),
            best_period=RollingPeriodResultModel(**summary.best_period.__dict__),
            consistency_score=summary.consistency_score
        )
        
        periods_models = [
            RollingPeriodResultModel(**period.__dict__) for period in periods
        ]
        
        return RollingPeriodAnalysisResponse(
            summary=summary_model,
            periods=periods_models,
            insights=insights,
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rolling-periods/multi", response_model=MultiPeriodAnalysisResponse)
async def analyze_multiple_rolling_periods(
    request: MultiPeriodAnalysisRequest,
    analyzer: RollingPeriodAnalyzer = Depends(get_rolling_period_analyzer)
):
    """
    Analyze portfolio across multiple rolling period lengths
    
    Compare portfolio performance consistency across different time horizons
    (e.g., 3-year vs 5-year vs 10-year rolling windows).
    
    Provides comparative analysis to help understand how portfolio behavior
    changes with different investment timeframes.
    """
    try:
        start_time = datetime.now()
        
        # Perform multi-period analysis
        multi_results = analyzer.analyze_multiple_periods(
            allocation=request.allocation,
            period_years_list=request.period_years_list,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Build response structure
        results = {}
        summaries = {}
        
        for period_years, (periods, summary) in multi_results.items():
            # Generate insights for this period
            insights = analyzer.generate_rolling_insights(
                summaries={period_years: summary},
                allocation=request.allocation
            )
            
            # Convert to response models
            summary_model = RollingPeriodSummaryModel(
                period_years=summary.period_years,
                total_windows=summary.total_windows,
                avg_cagr=summary.avg_cagr,
                min_cagr=summary.min_cagr,
                max_cagr=summary.max_cagr,
                cagr_std=summary.cagr_std,
                avg_volatility=summary.avg_volatility,
                avg_sharpe=summary.avg_sharpe,
                avg_max_drawdown=summary.avg_max_drawdown,
                worst_period=RollingPeriodResultModel(**summary.worst_period.__dict__),
                best_period=RollingPeriodResultModel(**summary.best_period.__dict__),
                consistency_score=summary.consistency_score
            )
            
            periods_models = [
                RollingPeriodResultModel(**period.__dict__) for period in periods
            ]
            
            results[period_years] = RollingPeriodAnalysisResponse(
                summary=summary_model,
                periods=periods_models,
                insights=insights,
                execution_time_seconds=0  # Will be set at the end
            )
            
            summaries[period_years] = summary
            
        # Generate comparative insights
        comparative_insights = analyzer.generate_rolling_insights(
            summaries=summaries,
            allocation=request.allocation
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Update individual execution times (approximation)
        for period_analysis in results.values():
            period_analysis.execution_time_seconds = execution_time / len(results)
        
        return MultiPeriodAnalysisResponse(
            results=results,
            comparative_insights=comparative_insights,
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rolling-periods/compare", response_model=PortfolioComparisonResponse)
async def compare_portfolios_rolling(
    request: PortfolioComparisonRequest,
    analyzer: RollingPeriodAnalyzer = Depends(get_rolling_period_analyzer)
):
    """
    Compare multiple portfolios using rolling period analysis
    
    Analyze and rank different portfolio allocations based on their
    rolling period performance, consistency, and risk-adjusted returns.
    
    Helps investors choose between different allocation strategies by
    understanding their historical performance patterns.
    """
    try:
        start_time = datetime.now()
        
        # Perform portfolio comparison
        comparison_results = analyzer.compare_portfolios_rolling(
            allocations=request.portfolios,
            period_years=request.period_years,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Build response structure
        portfolio_results = {}
        summaries_for_ranking = {}
        
        for portfolio_name, (periods, summary) in comparison_results.items():
            # Generate insights for this portfolio
            insights = analyzer.generate_rolling_insights(
                summaries={request.period_years: summary},
                allocation=request.portfolios[portfolio_name]
            )
            
            # Convert to response models  
            summary_model = RollingPeriodSummaryModel(
                period_years=summary.period_years,
                total_windows=summary.total_windows,
                avg_cagr=summary.avg_cagr,
                min_cagr=summary.min_cagr,
                max_cagr=summary.max_cagr,
                cagr_std=summary.cagr_std,
                avg_volatility=summary.avg_volatility,
                avg_sharpe=summary.avg_sharpe,
                avg_max_drawdown=summary.avg_max_drawdown,
                worst_period=RollingPeriodResultModel(**summary.worst_period.__dict__),
                best_period=RollingPeriodResultModel(**summary.best_period.__dict__),
                consistency_score=summary.consistency_score
            )
            
            periods_models = [
                RollingPeriodResultModel(**period.__dict__) for period in periods
            ]
            
            portfolio_results[portfolio_name] = RollingPeriodAnalysisResponse(
                summary=summary_model,
                periods=periods_models,
                insights=insights,
                execution_time_seconds=0  # Will be set at the end
            )
            
            summaries_for_ranking[portfolio_name] = summary
        
        # Generate ranking based on risk-adjusted returns and consistency
        ranking = []
        for name, summary in summaries_for_ranking.items():
            score = summary.avg_sharpe * (1 - summary.consistency_score * 0.5)  # Reward consistency
            ranking.append({
                "portfolio_name": name,
                "rank_score": round(score, 4),
                "avg_cagr": round(summary.avg_cagr * 100, 2),
                "avg_sharpe": round(summary.avg_sharpe, 3),
                "consistency_score": round(summary.consistency_score, 3),
                "allocation": request.portfolios[name]
            })
            
        # Sort by score (higher is better)
        ranking.sort(key=lambda x: x["rank_score"], reverse=True)
        
        # Add rank position
        for i, item in enumerate(ranking):
            item["rank"] = i + 1
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Update individual execution times
        for portfolio_analysis in portfolio_results.values():
            portfolio_analysis.execution_time_seconds = execution_time / len(portfolio_results)
        
        return PortfolioComparisonResponse(
            portfolio_results=portfolio_results,
            ranking=ranking,
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rolling-periods/examples")
async def get_rolling_period_examples():
    """
    Get example requests for rolling period analysis endpoints
    
    Returns sample payloads that can be used to test the various
    rolling period analysis endpoints.
    """
    return {
        "single_period_analysis": {
            "endpoint": "POST /api/analyze/rolling-periods",
            "example_request": {
                "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                "period_years": 5,
                "start_date": "2010-01-01T00:00:00Z",
                "end_date": "2024-01-01T00:00:00Z"
            }
        },
        "multi_period_analysis": {
            "endpoint": "POST /api/analyze/rolling-periods/multi", 
            "example_request": {
                "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                "period_years_list": [3, 5, 10],
                "start_date": "2010-01-01T00:00:00Z",
                "end_date": "2024-01-01T00:00:00Z"
            }
        },
        "portfolio_comparison": {
            "endpoint": "POST /api/analyze/rolling-periods/compare",
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


# Additional imports for crisis period analysis
from ..core.crisis_period_analyzer import (
    CrisisPeriodAnalyzer, 
    CrisisAnalysisResult, 
    StressTestSummary,
    CrisisPeriod,
    CrisisType
)
from datetime import datetime


# Additional Request/Response Models for Crisis Analysis
class CrisisPeriodAnalysisRequest(BaseModel):
    """Request model for crisis period stress testing"""
    allocation: Dict[str, float] = Field(
        ...,
        description="Portfolio allocation (symbol -> weight)",
        example={"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1}
    )
    crisis_periods: Optional[List[str]] = Field(
        None,
        description="Specific crisis periods to analyze (defaults to all major crises)",
        example=["2008 Financial Crisis", "2020 COVID-19 Crash"]
    )
    
    @validator('allocation')
    def validate_allocation(cls, v):
        """Validate portfolio allocation"""
        if not v:
            raise ValueError("Allocation cannot be empty")
            
        total_weight = sum(v.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Allocation weights must sum to 1.0, got {total_weight}")
            
        for symbol, weight in v.items():
            if weight < 0:
                raise ValueError(f"Negative weight not allowed: {symbol} = {weight}")
                
        return v


class CustomCrisisAnalysisRequest(BaseModel):
    """Request model for custom crisis period analysis"""
    allocation: Dict[str, float] = Field(
        ...,
        description="Portfolio allocation (symbol -> weight)"
    )
    start_date: datetime = Field(
        ...,
        description="Crisis period start date"
    )
    end_date: datetime = Field(
        ..., 
        description="Crisis period end date"
    )
    crisis_name: str = Field(
        "Custom Crisis",
        description="Name for the crisis period"
    )
    crisis_type: str = Field(
        "bear_market",
        description="Type of crisis (financial_crisis, pandemic, bear_market, etc.)"
    )
    
    @validator('allocation')
    def validate_allocation(cls, v):
        if not v:
            raise ValueError("Allocation cannot be empty")
        total_weight = sum(v.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Allocation weights must sum to 1.0, got {total_weight}")
        return v
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v


# Crisis Period Analysis Endpoints
@router.post("/stress-test", 
                     summary="Crisis Period Stress Testing",
                     description="Analyze portfolio performance during major market crisis periods")
async def analyze_crisis_periods(request: CrisisPeriodAnalysisRequest):
    """
    Perform comprehensive stress testing across major market crisis periods
    
    Analyzes portfolio performance during:
    - 2008 Financial Crisis (Sept 2008 - Mar 2009)
    - 2020 COVID-19 Crash (Feb - Mar 2020)
    - 2022 Bear Market (Jan - Oct 2022)
    
    Returns detailed crisis analysis with resilience scoring and recovery metrics.
    """
    try:
        # Initialize analyzers
        portfolio_engine = OptimizedPortfolioEngine()
        crisis_analyzer = CrisisPeriodAnalyzer(portfolio_engine)
        
        # Filter crisis periods if specified
        available_crises = crisis_analyzer.get_crisis_periods()
        crisis_periods_to_analyze = available_crises
        
        if request.crisis_periods:
            crisis_periods_to_analyze = [
                crisis for crisis in available_crises 
                if crisis.name in request.crisis_periods
            ]
            
            if not crisis_periods_to_analyze:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No valid crisis periods found. Available: {[c.name for c in available_crises]}"
                )
        
        # Perform crisis analysis
        crisis_results, summary = crisis_analyzer.analyze_crisis_periods(
            allocation=request.allocation,
            crisis_periods=crisis_periods_to_analyze
        )
        
        # Format results for JSON response
        formatted_results = []
        for result in crisis_results:
            formatted_result = {
                "crisis_name": result.crisis.name,
                "crisis_type": result.crisis.crisis_type.value,
                "period": {
                    "start_date": result.crisis.start_date.isoformat(),
                    "end_date": result.crisis.end_date.isoformat()
                },
                "description": result.crisis.description,
                "portfolio_performance": result.portfolio_performance,
                "crisis_decline": result.crisis_decline,
                "recovery_time_days": result.recovery_time_days,
                "recovery_velocity": result.recovery_velocity,
                "resilience_score": result.resilience_score
            }
            formatted_results.append(formatted_result)
        
        formatted_summary = {
            "total_crises_analyzed": len(crisis_results),
            "avg_crisis_decline": summary.avg_crisis_decline,
            "worst_crisis_decline": summary.worst_crisis_decline,
            "best_crisis_decline": summary.best_crisis_decline,
            "avg_recovery_time_days": summary.avg_recovery_time_days,
            "overall_resilience_score": summary.overall_resilience_score,
            "crisis_consistency": summary.crisis_consistency
        }
        
        return {
            "crisis_analysis": formatted_results,
            "stress_test_summary": formatted_summary,
            "analysis_metadata": {
                "portfolio_allocation": request.allocation,
                "analysis_date": datetime.now().isoformat(),
                "crisis_periods_analyzed": [c.name for c in crisis_periods_to_analyze]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crisis analysis failed: {str(e)}")


@router.post("/stress-test/custom",
                     summary="Custom Crisis Period Analysis", 
                     description="Analyze portfolio performance during a custom crisis period")
async def analyze_custom_crisis(request: CustomCrisisAnalysisRequest):
    """
    Analyze portfolio performance during a user-defined crisis period
    
    Allows analysis of any custom time period to understand portfolio
    behavior during specific market events or periods of interest.
    """
    try:
        # Initialize analyzers
        portfolio_engine = OptimizedPortfolioEngine()
        crisis_analyzer = CrisisPeriodAnalyzer(portfolio_engine)
        
        # Perform custom crisis analysis
        result = crisis_analyzer.analyze_custom_crisis(
            allocation=request.allocation,
            start_date=request.start_date,
            end_date=request.end_date,
            crisis_name=request.crisis_name,
            crisis_type=CrisisType(request.crisis_type)
        )
        
        # Format result for JSON response
        formatted_result = {
            "crisis_name": result.crisis.name,
            "crisis_type": result.crisis.crisis_type.value,
            "period": {
                "start_date": result.crisis.start_date.isoformat(),
                "end_date": result.crisis.end_date.isoformat()
            },
            "description": result.crisis.description,
            "portfolio_performance": result.portfolio_performance,
            "crisis_decline": result.crisis_decline,
            "recovery_time_days": result.recovery_time_days,
            "recovery_velocity": result.recovery_velocity,
            "resilience_score": result.resilience_score,
            "analysis_metadata": {
                "portfolio_allocation": request.allocation,
                "analysis_date": datetime.now().isoformat()
            }
        }
        
        return formatted_result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Custom crisis analysis failed: {str(e)}")


@router.get("/crisis-periods",
                    summary="Available Crisis Periods",
                    description="Get list of available crisis periods for stress testing")
async def get_available_crisis_periods():
    """
    Get list of available crisis periods for stress testing
    
    Returns details about major market crisis periods that can be
    used for portfolio stress testing analysis.
    """
    try:
        portfolio_engine = OptimizedPortfolioEngine()
        crisis_analyzer = CrisisPeriodAnalyzer(portfolio_engine)
        
        crisis_periods = crisis_analyzer.get_crisis_periods()
        
        formatted_periods = []
        for crisis in crisis_periods:
            formatted_period = {
                "name": crisis.name,
                "type": crisis.crisis_type.value,
                "start_date": crisis.start_date.isoformat(),
                "end_date": crisis.end_date.isoformat(),
                "description": crisis.description,
                "duration_days": (crisis.end_date - crisis.start_date).days,
                "market_decline_pct": crisis.market_decline_pct
            }
            formatted_periods.append(formatted_period)
        
        return {
            "available_crisis_periods": formatted_periods,
            "total_periods": len(formatted_periods),
            "supported_crisis_types": [ct.value for ct in CrisisType]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get crisis periods: {str(e)}")


# Update the examples endpoint to include crisis analysis
@router.get("/examples",
                    summary="Analysis Examples", 
                    description="Get example requests for all analysis endpoints")
async def get_analysis_examples():
    """
    Get example requests for analysis endpoints
    
    Returns sample payloads that can be used to test the various
    analysis endpoints including rolling periods and crisis analysis.
    """
    return {
        "rolling_period_analysis": {
            "single_period": {
                "endpoint": "POST /api/analyze/rolling-periods",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "period_years": 5,
                    "start_date": "2010-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                }
            },
            "multi_period": {
                "endpoint": "POST /api/analyze/rolling-periods/multi", 
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "period_years_list": [3, 5, 10],
                    "start_date": "2010-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                }
            },
            "portfolio_comparison": {
                "endpoint": "POST /api/analyze/rolling-periods/compare",
                "example_request": {
                    "portfolios": {
                        "Conservative": {"VTI": 0.3, "BND": 0.7},
                        "Balanced": {"VTI": 0.6, "BND": 0.4},
                        "Aggressive": {"VTI": 0.8, "VTIAX": 0.2}
                    },
                    "period_years": 5
                }
            }
        },
        "crisis_period_analysis": {
            "stress_test": {
                "endpoint": "POST /api/analyze/stress-test",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "crisis_periods": ["2008 Financial Crisis", "2020 COVID-19 Crash"]
                }
            },
            "custom_crisis": {
                "endpoint": "POST /api/analyze/stress-test/custom",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "start_date": "2018-10-01T00:00:00Z",
                    "end_date": "2018-12-31T00:00:00Z",
                    "crisis_name": "Q4 2018 Selloff",
                    "crisis_type": "bear_market"
                }
            },
            "available_periods": {
                "endpoint": "GET /api/analyze/crisis-periods",
                "description": "Get list of available crisis periods for analysis"
            }
        },
        "multi_period": {
                "endpoint": "POST /api/analyze/rolling-periods/multi", 
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "period_years_list": [3, 5, 10],
                    "start_date": "2010-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                }
            },
            "portfolio_comparison": {
                "endpoint": "POST /api/analyze/rolling-periods/compare",
                "example_request": {
                    "portfolios": {
                        "Conservative": {"VTI": 0.3, "BND": 0.7},
                        "Balanced": {"VTI": 0.6, "BND": 0.4},
                        "Aggressive": {"VTI": 0.8, "VTIAX": 0.2}
                    },
                    "period_years": 5
                }
            }
        },
        "crisis_period_analysis": {
            "stress_test": {
                "endpoint": "POST /api/analyze/stress-test",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "crisis_periods": ["2008 Financial Crisis", "2020 COVID-19 Crash"]
                }
            },
            "custom_crisis": {
                "endpoint": "POST /api/analyze/stress-test/custom",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "start_date": "2018-10-01T00:00:00Z",
                    "end_date": "2018-12-31T00:00:00Z",
                    "crisis_name": "Q4 2018 Selloff",
                    "crisis_type": "bear_market"
                }
            },
            "available_periods": {
                "endpoint": "GET /api/analyze/crisis-periods",
                "description": "Get list of available crisis periods for analysis"
            }
        },
        "recovery_time_analysis": {
            "recovery_patterns": {
                "endpoint": "POST /api/analyze/recovery-analysis",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "start_date": "2010-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z",
                    "min_drawdown_pct": 0.10
                }
            },
            "recovery_comparison": {
                "endpoint": "POST /api/analyze/recovery-analysis/compare",
                "example_request": {
                    "portfolios": {
                        "Conservative": {"VTI": 0.3, "BND": 0.7},
                        "Balanced": {"VTI": 0.6, "BND": 0.4}, 
                        "Aggressive": {"VTI": 0.8, "VTIAX": 0.2}
                    },
                    "min_drawdown_pct": 0.10
                }
            }
        }
    }


# Additional imports for timeline risk analysis
from ..core.timeline_risk_analyzer import (
    TimelineRiskAnalyzer,
    InvestorProfile,
    TimelineAnalysisResult,
    RiskTolerance,
    LifeStage
)


# Additional Request/Response Models for Timeline Analysis
class InvestorProfileRequest(BaseModel):
    """Request model for investor profile"""
    age: int = Field(..., ge=18, le=100, description="Investor age")
    investment_horizon_years: int = Field(..., ge=1, le=50, description="Years until retirement or goal")
    risk_tolerance: str = Field(..., description="Risk tolerance level", 
                               regex="^(conservative|moderate|aggressive|very_aggressive)$")
    account_type: str = Field("taxable", description="Account type", 
                             regex="^(taxable|401k|ira|roth_ira)$")
    current_portfolio_value: Optional[float] = Field(None, ge=0, description="Current portfolio value")
    monthly_contribution: Optional[float] = Field(None, ge=0, description="Monthly contribution amount")
    retirement_target_value: Optional[float] = Field(None, ge=0, description="Target retirement value")


class TimelineRecommendationRequest(BaseModel):
    """Request model for timeline-aware recommendations"""
    investor_profile: InvestorProfileRequest = Field(..., description="Investor profile")
    current_allocation: Optional[Dict[str, float]] = Field(
        None, description="Current portfolio allocation (optional)"
    )
    
    @validator('current_allocation')
    def validate_current_allocation(cls, v):
        if v is not None:
            if not v:
                raise ValueError("Current allocation cannot be empty if provided")
            total_weight = sum(v.values())
            if abs(total_weight - 1.0) > 0.001:
                raise ValueError(f"Current allocation weights must sum to 1.0, got {total_weight}")
        return v


# Timeline Risk Analysis Endpoints
@router.post("/timeline-recommendation",
                     summary="Timeline-Aware Portfolio Recommendations",
                     description="Generate portfolio recommendations based on age, timeline, and risk tolerance")
async def generate_timeline_recommendation(request: TimelineRecommendationRequest):
    """
    Generate comprehensive timeline-aware portfolio recommendations
    
    Analyzes investor profile including:
    - Age and life stage
    - Investment horizon
    - Risk tolerance
    - Current allocation (if provided)
    
    Returns personalized allocation recommendations with scenario analysis.
    """
    try:
        # Initialize analyzers
        portfolio_engine = OptimizedPortfolioEngine()
        timeline_analyzer = TimelineRiskAnalyzer(portfolio_engine)
        
        # Create investor profile
        profile_data = request.investor_profile
        
        # Determine life stage based on age
        if profile_data.age < 40:
            life_stage = LifeStage.YOUNG_ACCUMULATOR
        elif profile_data.age < 55:
            life_stage = LifeStage.MID_CAREER
        elif profile_data.age < 65:
            life_stage = LifeStage.PRE_RETIREMENT
        else:
            life_stage = LifeStage.RETIREMENT
        
        investor_profile = InvestorProfile(
            age=profile_data.age,
            investment_horizon_years=profile_data.investment_horizon_years,
            risk_tolerance=RiskTolerance(profile_data.risk_tolerance),
            life_stage=life_stage,
            account_type=profile_data.account_type,
            current_portfolio_value=profile_data.current_portfolio_value,
            monthly_contribution=profile_data.monthly_contribution,
            retirement_target_value=profile_data.retirement_target_value
        )
        
        # Generate timeline recommendations
        result = timeline_analyzer.generate_timeline_recommendation(
            investor_profile=investor_profile,
            current_allocation=request.current_allocation
        )
        
        # Format recommended allocation for JSON response
        recommended_allocation = {
            "allocation": result.recommended_allocation.recommended_allocation,
            "rationale": result.recommended_allocation.allocation_rationale,
            "risk_level": result.recommended_allocation.risk_level,
            "expected_annual_return": result.recommended_allocation.expected_annual_return,
            "expected_volatility": result.recommended_allocation.expected_volatility,
            "max_drawdown_expectation": result.recommended_allocation.max_drawdown_expectation,
            "recovery_time_expectation_days": result.recommended_allocation.recovery_time_expectation,
            "rebalancing_frequency": result.recommended_allocation.rebalancing_frequency,
            "key_risks": result.recommended_allocation.key_risks,
            "timeline_specific_notes": result.recommended_allocation.timeline_specific_notes,
            "confidence_score": result.recommended_allocation.confidence_score
        }
        
        # Format current allocation analysis if provided
        current_analysis = None
        if result.current_allocation_analysis:
            current_analysis = result.current_allocation_analysis
        
        # Format milestone projections
        formatted_projections = []
        for projection in result.milestone_projections:
            formatted_projection = {
                "years_from_now": projection["years_from_now"],
                "age_at_milestone": projection["age_at_milestone"], 
                "projected_value": projection["projected_value"],
                "total_contributions": projection["total_contributions"],
                "growth_from_returns": projection["growth_from_returns"],
                "purchasing_power_2024_dollars": projection["purchasing_power"],
                "milestone_notes": projection["milestone_notes"]
            }
            formatted_projections.append(formatted_projection)
        
        return {
            "timeline_recommendation": {
                "investor_profile": {
                    "age": investor_profile.age,
                    "life_stage": investor_profile.life_stage.value,
                    "investment_horizon_years": investor_profile.investment_horizon_years,
                    "risk_tolerance": investor_profile.risk_tolerance.value,
                    "account_type": investor_profile.account_type
                },
                "recommended_allocation": recommended_allocation,
                "current_allocation_analysis": current_analysis,
                "scenario_analysis": result.scenario_analysis,
                "milestone_projections": formatted_projections,
                "adjustment_triggers": result.adjustment_triggers
            },
            "analysis_metadata": {
                "analysis_date": datetime.now().isoformat(),
                "recommendation_basis": "Historical performance analysis with timeline optimization"
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline recommendation failed: {str(e)}")


@router.get("/risk-profiles",
                    summary="Available Risk Profiles and Life Stages", 
                    description="Get information about available risk tolerance levels and life stages")
async def get_risk_profiles():
    """
    Get available risk tolerance levels and life stage categories
    
    Returns detailed information about risk profiles and life stages
    used for timeline-aware recommendations.
    """
    return {
        "risk_tolerance_levels": {
            "conservative": {
                "description": "Focus on capital preservation with minimal volatility",
                "typical_volatility": "8-12%",
                "max_drawdown_tolerance": "10-15%",
                "suitable_for": ["Near retirement", "Risk-averse investors", "Short time horizons"]
            },
            "moderate": {
                "description": "Balanced approach between growth and stability",
                "typical_volatility": "12-16%", 
                "max_drawdown_tolerance": "15-25%",
                "suitable_for": ["Mid-career professionals", "Balanced investors", "Medium time horizons"]
            },
            "aggressive": {
                "description": "Growth-focused with higher volatility tolerance",
                "typical_volatility": "16-20%",
                "max_drawdown_tolerance": "25-35%",
                "suitable_for": ["Young investors", "Long time horizons", "Growth-oriented"]
            },
            "very_aggressive": {
                "description": "Maximum growth potential with high risk tolerance", 
                "typical_volatility": "20%+",
                "max_drawdown_tolerance": "35%+",
                "suitable_for": ["Very long horizons", "High risk tolerance", "Experienced investors"]
            }
        },
        "life_stages": {
            "young_accumulator": {
                "age_range": "20s-30s",
                "description": "Building wealth, long investment horizon",
                "typical_stock_allocation": "70-95%",
                "key_considerations": ["Tax-advantaged savings", "Aggressive growth", "Time to recover from losses"]
            },
            "mid_career": {
                "age_range": "40s-50s",
                "description": "Peak earning years, moderate horizon",
                "typical_stock_allocation": "50-80%",
                "key_considerations": ["Balanced approach", "Gradual risk reduction", "Estate planning"]
            },
            "pre_retirement": {
                "age_range": "55-65",
                "description": "Preparing for retirement, shorter horizon",
                "typical_stock_allocation": "30-60%", 
                "key_considerations": ["Capital preservation", "Income planning", "Sequence risk"]
            },
            "retirement": {
                "age_range": "65+",
                "description": "In retirement, income focus",
                "typical_stock_allocation": "20-50%",
                "key_considerations": ["Income generation", "Inflation protection", "Legacy planning"]
            }
        },
        "account_types": {
            "taxable": {
                "description": "Regular brokerage account",
                "tax_considerations": ["Capital gains tax", "Dividend tax", "Tax-loss harvesting"],
                "rebalancing_notes": "Consider tax implications when rebalancing"
            },
            "401k": {
                "description": "Employer-sponsored retirement account",
                "tax_considerations": ["Tax-deferred growth", "Required minimum distributions"],
                "rebalancing_notes": "Tax-free rebalancing within account"
            },
            "ira": {
                "description": "Individual Retirement Account",
                "tax_considerations": ["Tax-deferred growth", "Early withdrawal penalties"],
                "rebalancing_notes": "Tax-free rebalancing within account"
            },
            "roth_ira": {
                "description": "Roth Individual Retirement Account", 
                "tax_considerations": ["Tax-free growth", "No required distributions"],
                "rebalancing_notes": "Tax-free rebalancing and withdrawals in retirement"
            }
        }
    }


# Update the main examples endpoint to include timeline analysis
@router.get("/examples",
                    summary="Analysis Examples",
                    description="Get example requests for all analysis endpoints")
async def get_analysis_examples():
    """
    Get example requests for analysis endpoints
    
    Returns sample payloads for all analysis endpoints including 
    rolling periods, crisis analysis, recovery patterns, and timeline recommendations.
    """
    return {
        "rolling_period_analysis": {
            "single_period": {
                "endpoint": "POST /api/analyze/rolling-periods",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "period_years": 5,
                    "start_date": "2010-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                }
            },
            "multi_period": {
                "endpoint": "POST /api/analyze/rolling-periods/multi",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "period_years_list": [3, 5, 10],
                    "start_date": "2010-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z"
                }
            },
            "portfolio_comparison": {
                "endpoint": "POST /api/analyze/rolling-periods/compare",
                "example_request": {
                    "portfolios": {
                        "Conservative": {"VTI": 0.3, "BND": 0.7},
                        "Balanced": {"VTI": 0.6, "BND": 0.4},
                        "Aggressive": {"VTI": 0.8, "VTIAX": 0.2}
                    },
                    "period_years": 5
                }
            }
        },
        "crisis_period_analysis": {
            "stress_test": {
                "endpoint": "POST /api/analyze/stress-test",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "crisis_periods": ["2008 Financial Crisis", "2020 COVID-19 Crash"]
                }
            },
            "custom_crisis": {
                "endpoint": "POST /api/analyze/stress-test/custom",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "start_date": "2018-10-01T00:00:00Z",
                    "end_date": "2018-12-31T00:00:00Z",
                    "crisis_name": "Q4 2018 Selloff",
                    "crisis_type": "bear_market"
                }
            },
            "available_periods": {
                "endpoint": "GET /api/analyze/crisis-periods",
                "description": "Get list of available crisis periods for analysis"
            }
        },
        "recovery_time_analysis": {
            "recovery_patterns": {
                "endpoint": "POST /api/analyze/recovery-analysis",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "start_date": "2010-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z",
                    "min_drawdown_pct": 0.10
                }
            },
            "recovery_comparison": {
                "endpoint": "POST /api/analyze/recovery-analysis/compare",
                "example_request": {
                    "portfolios": {
                        "Conservative": {"VTI": 0.3, "BND": 0.7},
                        "Balanced": {"VTI": 0.6, "BND": 0.4},
                        "Aggressive": {"VTI": 0.8, "VTIAX": 0.2}
                    },
                    "min_drawdown_pct": 0.10
                }
            }
        },
        "timeline_risk_analysis": {
            "timeline_recommendation": {
                "endpoint": "POST /api/analyze/timeline-recommendation",
                "example_request": {
                    "investor_profile": {
                        "age": 35,
                        "investment_horizon_years": 30,
                        "risk_tolerance": "aggressive",
                        "account_type": "401k",
                        "current_portfolio_value": 50000,
                        "monthly_contribution": 1000,
                        "retirement_target_value": 1500000
                    },
                    "current_allocation": {
                        "VTI": 0.7,
                        "BND": 0.3
                    }
                }
            },
            "risk_profiles": {
                "endpoint": "GET /api/analyze/risk-profiles", 
                "description": "Get information about risk tolerance levels and life stages"
            }
        }
        },
        "rebalancing_strategy_analysis": {
            "threshold_analysis": {
                "endpoint": "POST /api/analyze/rebalancing-strategy",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "strategy_type": "threshold",
                    "threshold_percentages": [5, 10, 15, 20],
                    "account_type": "taxable",
                    "transaction_cost_pct": 0.1
                }
            },
            "time_based_analysis": {
                "endpoint": "POST /api/analyze/rebalancing-strategy", 
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "strategy_type": "time_based",
                    "rebalancing_frequencies": ["monthly", "quarterly", "annual"],
                    "account_type": "tax_deferred"
                }
            },
            "new_money_analysis": {
                "endpoint": "POST /api/analyze/rebalancing-strategy",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "strategy_type": "new_money",
                    "monthly_contribution": 1000,
                    "account_type": "taxable"
                }
            },
            "strategy_comparison": {
                "endpoint": "POST /api/analyze/rebalancing-strategy/compare",
                "example_request": {
                    "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
                    "strategies_to_compare": ["threshold", "time_based", "new_money"],
                    "account_type": "taxable"
                }
            }
        }
    }
