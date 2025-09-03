"""
Rebalancing Strategy API Routes - Sprint 5 Phase 7

RESTful API endpoints for enhanced rebalancing strategy analysis:
- Compare different rebalancing approaches
- Analyze tax-aware rebalancing strategies  
- Get strategy recommendations based on account type
- Historical walk-forward performance analysis

Part of the intellectual honesty approach - showing real costs and trade-offs.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from enum import Enum
import logging
import pandas as pd

from ..models.base import DatabaseManager
from ..backtesting.rebalancing_analyzer import (
    RebalancingAnalyzer, RebalancingMethod, AccountType, 
    RebalancingAnalysis
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rebalancing", tags=["rebalancing"])

# Request/Response Models
class RebalancingMethodEnum(str, Enum):
    """API enum for rebalancing methods"""
    THRESHOLD_5_PERCENT = "5_percent_threshold"
    THRESHOLD_10_PERCENT = "10_percent_threshold" 
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    NEW_MONEY_ONLY = "new_money_only"

class AccountTypeEnum(str, Enum):
    """API enum for account types"""
    TAXABLE = "taxable"
    TAX_DEFERRED = "tax_deferred"
    TAX_FREE = "tax_free"

class RebalancingAnalysisRequest(BaseModel):
    """Request for single rebalancing strategy analysis"""
    target_allocation: Dict[str, float] = Field(
        ..., 
        description="Target portfolio allocation",
        example={
            "VTI": 0.30,
            "VTIAX": 0.20, 
            "BND": 0.25,
            "VNQ": 0.10,
            "GLD": 0.05,
            "VWO": 0.05,
            "QQQ": 0.05
        }
    )
    method: RebalancingMethodEnum = Field(..., description="Rebalancing method to analyze")
    account_type: AccountTypeEnum = Field(..., description="Account type for tax calculations")
    start_date: str = Field("2014-01-01", description="Analysis start date (YYYY-MM-DD)")
    end_date: str = Field("2024-01-01", description="Analysis end date (YYYY-MM-DD)")
    initial_value: float = Field(100000.0, description="Starting portfolio value", gt=1000)
    annual_contribution: float = Field(0.0, description="Annual new money contribution", ge=0)
    
    @validator('target_allocation')
    def validate_allocation_weights(cls, v):
        """Ensure allocation weights sum to approximately 1.0"""
        total = sum(v.values())
        if not (0.95 <= total <= 1.05):
            raise ValueError(f"Allocation weights must sum to 1.0, got {total:.3f}")
        return v
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        """Ensure dates are valid format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Dates must be in YYYY-MM-DD format")
        return v

class RebalancingComparisonRequest(BaseModel):
    """Request for comparing multiple rebalancing strategies"""
    target_allocation: Dict[str, float] = Field(
        ..., 
        description="Target portfolio allocation"
    )
    account_type: AccountTypeEnum = Field(..., description="Account type for tax calculations")
    start_date: str = Field("2014-01-01", description="Analysis start date")
    end_date: str = Field("2024-01-01", description="Analysis end date")
    initial_value: float = Field(100000.0, description="Starting portfolio value", gt=1000)
    annual_contribution: float = Field(0.0, description="Annual new money contribution", ge=0)
    methods: Optional[List[RebalancingMethodEnum]] = Field(
        None, 
        description="Methods to compare (defaults to all)"
    )
    
    @validator('target_allocation')
    def validate_allocation_weights(cls, v):
        total = sum(v.values())
        if not (0.95 <= total <= 1.05):
            raise ValueError(f"Allocation weights must sum to 1.0, got {total:.3f}")
        return v

class RebalancingEventResponse(BaseModel):
    """Single rebalancing event"""
    date: date
    method: str
    trigger_reason: str
    transaction_cost: float
    tax_impact: float
    total_drag: float

class RebalancingAnalysisResponse(BaseModel):
    """Response for rebalancing strategy analysis"""
    method: str
    account_type: str
    analysis_period: Dict[str, str]
    
    # Performance metrics
    performance: Dict[str, float] = Field(
        ..., 
        description="Performance metrics",
        example={
            "total_return": 0.142,
            "annualized_return": 0.086,
            "volatility": 0.156,
            "sharpe_ratio": 0.423,
            "max_drawdown": -0.089
        }
    )
    
    # Rebalancing metrics
    rebalancing_stats: Dict[str, Any] = Field(
        ...,
        description="Rebalancing statistics",
        example={
            "num_rebalances": 12,
            "avg_transaction_cost": 125.50,
            "total_transaction_costs": 1506.00,
            "total_tax_drag": 450.25,
            "total_drag": 1956.25
        }
    )
    
    # Risk metrics
    risk_metrics: Dict[str, float] = Field(
        ...,
        description="Risk-adjusted metrics",
        example={
            "tracking_error": 0.012,
            "active_return": 0.008,
            "drag_adjusted_sharpe": 0.415,
            "cost_efficiency_ratio": 4.08
        }
    )
    
    # Event history (limited to last 10 for API response)
    recent_rebalancing_events: List[RebalancingEventResponse]
    
    # Summary insights
    insights: Dict[str, str] = Field(
        ...,
        description="Key insights and takeaways"
    )

class RebalancingComparisonResponse(BaseModel):
    """Response for comparing multiple rebalancing strategies"""
    account_type: str
    analysis_period: Dict[str, str]
    comparison_results: Dict[str, RebalancingAnalysisResponse]
    recommendation: Dict[str, str] = Field(
        ...,
        description="Recommended strategy with explanation"
    )
    summary_comparison: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Side-by-side metric comparison"
    )

class RebalancingInfoResponse(BaseModel):
    """Information about available rebalancing methods and features"""
    available_methods: Dict[str, Dict[str, str]]
    account_types: Dict[str, Dict[str, str]]
    supported_assets: List[str]
    analysis_capabilities: List[str]

# Global analyzer instance (will be initialized)
_analyzer: Optional[RebalancingAnalyzer] = None

def get_analyzer() -> RebalancingAnalyzer:
    """Get initialized rebalancing analyzer"""
    global _analyzer
    if _analyzer is None:
        # Load historical data
        db = DatabaseManager()
        df = db.get_historical_data()
        _analyzer = RebalancingAnalyzer(df)
        logger.info("✅ Rebalancing analyzer initialized")
    return _analyzer

@router.post("/analyze-strategy", response_model=RebalancingAnalysisResponse)
async def analyze_rebalancing_strategy(request: RebalancingAnalysisRequest):
    """
    Analyze a single rebalancing strategy with walk-forward simulation
    
    Performs honest analysis including:
    - Transaction costs and tax implications
    - Historical performance metrics
    - Risk-adjusted returns
    - Rebalancing event timeline
    """
    try:
        logger.info(f"Analyzing {request.method} strategy for {request.account_type} account")
        
        analyzer = get_analyzer()
        
        # Convert enums to internal types
        method = RebalancingMethod(request.method.value)
        account_type = AccountType(request.account_type.value)
        
        # Run analysis
        analysis = analyzer.analyze_rebalancing_strategy(
            target_allocation=request.target_allocation,
            method=method,
            account_type=account_type,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_value=request.initial_value,
            annual_contribution=request.annual_contribution
        )
        
        # Convert to response format
        return _convert_analysis_to_response(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing rebalancing strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/compare-strategies", response_model=RebalancingComparisonResponse)  
async def compare_rebalancing_strategies(request: RebalancingComparisonRequest):
    """
    Compare multiple rebalancing strategies and get recommendation
    
    Analyzes all requested methods (or all available methods) and provides:
    - Performance comparison across all methods
    - Cost analysis and efficiency metrics
    - Recommended strategy with explanation
    - Side-by-side comparison table
    """
    try:
        logger.info(f"Comparing rebalancing strategies for {request.account_type} account")
        
        analyzer = get_analyzer()
        account_type = AccountType(request.account_type.value)
        
        # Use all methods if none specified
        methods_to_compare = (
            [RebalancingMethod(m.value) for m in request.methods] 
            if request.methods 
            else list(RebalancingMethod)
        )
        
        # Run comparison analysis
        results = {}
        for method in methods_to_compare:
            try:
                analysis = analyzer.analyze_rebalancing_strategy(
                    target_allocation=request.target_allocation,
                    method=method,
                    account_type=account_type,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    initial_value=request.initial_value,
                    annual_contribution=request.annual_contribution
                )
                results[method] = analysis
            except Exception as e:
                logger.warning(f"Failed to analyze {method.value}: {str(e)}")
        
        if not results:
            raise HTTPException(status_code=500, detail="No successful strategy analyses")
        
        # Get recommendation
        best_method, explanation = analyzer.recommend_rebalancing_strategy(
            results, account_type
        )
        
        # Convert to response format
        return _convert_comparison_to_response(
            results, best_method, explanation, account_type, 
            request.start_date, request.end_date
        )
        
    except Exception as e:
        logger.error(f"Error comparing rebalancing strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/info", response_model=RebalancingInfoResponse)
async def get_rebalancing_info():
    """
    Get information about available rebalancing methods and capabilities
    """
    return RebalancingInfoResponse(
        available_methods={
            "5_percent_threshold": {
                "name": "5% Threshold Rebalancing",
                "description": "Rebalance when any asset drifts >5% from target allocation",
                "typical_frequency": "Monthly to Quarterly",
                "best_for": "Active investors comfortable with moderate trading costs"
            },
            "10_percent_threshold": {
                "name": "10% Threshold Rebalancing", 
                "description": "Rebalance when any asset drifts >10% from target allocation",
                "typical_frequency": "Quarterly to Semi-annual",
                "best_for": "Balanced approach between control and cost efficiency"
            },
            "quarterly": {
                "name": "Quarterly Rebalancing",
                "description": "Rebalance every 3 months regardless of drift",
                "typical_frequency": "Quarterly",
                "best_for": "Systematic investors who prefer predictable schedules"
            },
            "annual": {
                "name": "Annual Rebalancing",
                "description": "Rebalance once per year regardless of drift",
                "typical_frequency": "Annually", 
                "best_for": "Cost-conscious long-term investors"
            },
            "new_money_only": {
                "name": "New Money Rebalancing",
                "description": "Use new contributions to rebalance, never sell existing holdings",
                "typical_frequency": "With each contribution",
                "best_for": "Tax-conscious investors in taxable accounts"
            }
        },
        account_types={
            "taxable": {
                "name": "Taxable Investment Account",
                "tax_implications": "Capital gains taxes on rebalancing trades",
                "recommended_approach": "New money rebalancing or wider thresholds"
            },
            "tax_deferred": {
                "name": "Tax-Deferred Account (401k, Traditional IRA)",
                "tax_implications": "No immediate tax impact from trading",
                "recommended_approach": "More active rebalancing strategies acceptable"
            },
            "tax_free": {
                "name": "Tax-Free Account (Roth IRA, Roth 401k)",  
                "tax_implications": "No tax impact from trading",
                "recommended_approach": "Optimal for active rebalancing strategies"
            }
        },
        supported_assets=[
            "VTI", "VTIAX", "BND", "VNQ", "GLD", "VWO", "QQQ"
        ],
        analysis_capabilities=[
            "Walk-forward historical simulation (2014-2024)",
            "Transaction cost modeling",
            "Tax impact estimation for taxable accounts", 
            "Risk-adjusted performance metrics",
            "Cost efficiency analysis",
            "Strategy recommendation engine",
            "Rebalancing event timeline tracking"
        ]
    )

# Helper functions
def _convert_analysis_to_response(analysis: RebalancingAnalysis) -> RebalancingAnalysisResponse:
    """Convert internal analysis result to API response"""
    
    # Recent events (last 10)
    recent_events = [
        RebalancingEventResponse(
            date=event.date.date(),
            method=event.method.value,
            trigger_reason=event.trigger_reason,
            transaction_cost=event.transaction_cost,
            tax_impact=event.tax_impact,
            total_drag=event.total_drag
        )
        for event in analysis.rebalancing_events[-10:]
    ]
    
    # Generate insights
    insights = _generate_analysis_insights(analysis)
    
    return RebalancingAnalysisResponse(
        method=analysis.method.value,
        account_type=analysis.account_type.value,
        analysis_period={
            "start": analysis.start_date.strftime("%Y-%m-%d"),
            "end": analysis.end_date.strftime("%Y-%m-%d")
        },
        performance={
            "total_return": round(analysis.total_return, 4),
            "annualized_return": round(analysis.annualized_return, 4),
            "volatility": round(analysis.volatility, 4),
            "sharpe_ratio": round(analysis.sharpe_ratio, 4),
            "max_drawdown": round(analysis.max_drawdown, 4)
        },
        rebalancing_stats={
            "num_rebalances": analysis.num_rebalances,
            "avg_transaction_cost": round(analysis.avg_transaction_cost, 2),
            "total_transaction_costs": round(analysis.total_transaction_costs, 2),
            "total_tax_drag": round(analysis.total_tax_drag, 2),
            "total_drag": round(analysis.total_drag, 2)
        },
        risk_metrics={
            "tracking_error": round(analysis.tracking_error, 4),
            "active_return": round(analysis.active_return, 4),
            "drag_adjusted_sharpe": round(analysis.drag_adjusted_sharpe, 4),
            "cost_efficiency_ratio": round(analysis.cost_efficiency_ratio, 2)
        },
        recent_rebalancing_events=recent_events,
        insights=insights
    )

def _convert_comparison_to_response(
    results: Dict[RebalancingMethod, RebalancingAnalysis],
    best_method: RebalancingMethod,
    explanation: str,
    account_type: AccountType,
    start_date: str,
    end_date: str
) -> RebalancingComparisonResponse:
    """Convert comparison results to API response"""
    
    # Convert each analysis
    comparison_results = {
        method.value: _convert_analysis_to_response(analysis)
        for method, analysis in results.items()
    }
    
    # Create summary comparison table
    summary_comparison = {}
    for method, analysis in results.items():
        summary_comparison[method.value] = {
            "annualized_return": round(analysis.annualized_return, 4),
            "volatility": round(analysis.volatility, 4),
            "sharpe_ratio": round(analysis.sharpe_ratio, 4),
            "num_rebalances": analysis.num_rebalances,
            "total_costs": round(analysis.total_drag, 2),
            "cost_efficiency": round(analysis.cost_efficiency_ratio, 2)
        }
    
    return RebalancingComparisonResponse(
        account_type=account_type.value,
        analysis_period={
            "start": start_date,
            "end": end_date
        },
        comparison_results=comparison_results,
        recommendation={
            "method": best_method.value,
            "explanation": explanation
        },
        summary_comparison=summary_comparison
    )

def _generate_analysis_insights(analysis: RebalancingAnalysis) -> Dict[str, str]:
    """Generate key insights from analysis results"""
    
    insights = {}
    
    # Cost efficiency insight
    if analysis.total_drag > 0:
        cost_pct = (analysis.total_drag / analysis.performance_timeline.iloc[0]['portfolio_value']) * 100
        insights["cost_impact"] = f"Total rebalancing costs were {cost_pct:.2f}% of initial portfolio value"
    
    # Rebalancing frequency insight
    years = (analysis.end_date - analysis.start_date).days / 365.25
    rebalances_per_year = analysis.num_rebalances / years
    insights["frequency"] = f"Averaged {rebalances_per_year:.1f} rebalances per year"
    
    # Performance insight
    if analysis.sharpe_ratio > 0.5:
        insights["performance"] = f"Strong risk-adjusted returns with Sharpe ratio of {analysis.sharpe_ratio:.2f}"
    elif analysis.sharpe_ratio > 0.2:
        insights["performance"] = f"Reasonable risk-adjusted returns with Sharpe ratio of {analysis.sharpe_ratio:.2f}" 
    else:
        insights["performance"] = f"Below-average risk-adjusted returns with Sharpe ratio of {analysis.sharpe_ratio:.2f}"
    
    # Account-specific insight
    if analysis.account_type == AccountType.TAXABLE and analysis.total_tax_drag > 0:
        insights["tax_impact"] = f"Tax drag of ${analysis.total_tax_drag:,.0f} emphasizes importance of tax-aware strategies"
    
    return insights
