"""
Enhanced Optimization API Routes with Integrated Analytics

Provides comprehensive portfolio optimization with crisis analysis,
rolling period consistency, and advanced risk metrics.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from ..optimization.portfolio_optimizer_enhanced import (
    EnhancedPortfolioOptimizer, 
    EnhancedPortfolioResult,
    AccountType,
    PortfolioRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/enhanced", tags=["Enhanced Portfolio Optimization"])

# Initialize the enhanced optimizer
enhanced_optimizer = EnhancedPortfolioOptimizer()

# Pydantic models for API
class EnhancedOptimizationRequest(BaseModel):
    """Enhanced portfolio optimization request"""
    current_savings: float = Field(default=10000.0, ge=1000, le=10000000, 
                                 description="Current savings amount")
    target_amount: Optional[float] = Field(default=None, ge=10000, le=50000000,
                                         description="Target amount (optional)")
    time_horizon: int = Field(default=10, ge=1, le=50, 
                            description="Investment time horizon in years")
    account_type: str = Field(default="tax_free", 
                            description="Account type: taxable, tax_deferred, tax_free")
    new_money_available: bool = Field(default=False,
                                    description="Whether new money contributions are available")
    max_annual_contribution: Optional[float] = Field(default=None, ge=0, le=100000,
                                                   description="Maximum annual contribution")

class CrisisAnalysisResponse(BaseModel):
    """Crisis analysis results for API response"""
    crisis_name: str
    crisis_type: str
    start_date: str
    end_date: str
    portfolio_decline: float
    market_decline: float
    recovery_time_days: Optional[int]
    recovery_time_months: Optional[float]
    resilience_score: float
    outperformed_market: bool

class RollingAnalysisResponse(BaseModel):
    """Rolling period analysis results for API response"""
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
    consistency_score: float

class EnhancedRiskMetricsResponse(BaseModel):
    """Enhanced risk metrics for API response"""
    var_95: float
    cvar_95: float
    sortino_ratio: float
    calmar_ratio: float
    max_monthly_loss: float
    worst_12_month_return: float
    downside_volatility: float
    upside_capture: float
    downside_capture: float

class EnhancedPortfolioResponse(BaseModel):
    """Enhanced portfolio optimization response"""
    strategy: str
    allocation: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    target_achievement_probability: Optional[float] = None
    expected_final_value: float
    
    # Enhanced analytics
    crisis_analysis: List[CrisisAnalysisResponse]
    overall_crisis_score: float
    rolling_analysis: Dict[str, RollingAnalysisResponse]
    consistency_score: float
    risk_metrics: EnhancedRiskMetricsResponse
    avg_recovery_time_months: float
    worst_drawdown_recovery_months: float
    optimal_rebalancing_frequency: str
    rebalancing_benefit: float
    account_specific_notes: List[str]

@router.post("/portfolio/optimize", response_model=List[EnhancedPortfolioResponse])
async def optimize_enhanced_portfolio(request: EnhancedOptimizationRequest):
    """
    Generate optimized portfolios with comprehensive analytics
    
    Returns three portfolios (Conservative, Balanced, Aggressive) with:
    - Crisis period stress testing
    - Rolling period consistency analysis  
    - Advanced risk metrics
    - Recovery time analysis
    - Account-specific recommendations
    """
    try:
        logger.info(f"Processing enhanced optimization request: {request.dict()}")
        
        # Convert API request to internal format
        portfolio_request = PortfolioRequest(
            current_savings=request.current_savings,
            target_amount=request.target_amount,
            time_horizon=request.time_horizon,
            account_type=AccountType(request.account_type),
            new_money_available=request.new_money_available,
            max_annual_contribution=request.max_annual_contribution
        )
        
        # Get enhanced optimization results
        results = enhanced_optimizer.optimize_enhanced_portfolio(portfolio_request)
        
        # Convert internal results to API response format
        api_results = []
        for result in results:
            # Convert crisis analysis
            crisis_analysis = [
                CrisisAnalysisResponse(**crisis.__dict__)
                for crisis in result.crisis_analysis
            ]
            
            # Convert rolling analysis
            rolling_analysis = {
                period: RollingAnalysisResponse(**analysis.__dict__)
                for period, analysis in result.rolling_analysis.items()
            }
            
            # Convert risk metrics
            risk_metrics = EnhancedRiskMetricsResponse(**result.risk_metrics.__dict__)
            
            api_result = EnhancedPortfolioResponse(
                strategy=result.strategy,
                allocation=result.allocation,
                expected_return=result.expected_return,
                volatility=result.volatility,
                sharpe_ratio=result.sharpe_ratio,
                target_achievement_probability=result.target_achievement_probability,
                expected_final_value=result.expected_final_value,
                crisis_analysis=crisis_analysis,
                overall_crisis_score=result.overall_crisis_score,
                rolling_analysis=rolling_analysis,
                consistency_score=result.consistency_score,
                risk_metrics=risk_metrics,
                avg_recovery_time_months=result.avg_recovery_time_months,
                worst_drawdown_recovery_months=result.worst_drawdown_recovery_months,
                optimal_rebalancing_frequency=result.optimal_rebalancing_frequency,
                rebalancing_benefit=result.rebalancing_benefit,
                account_specific_notes=result.account_specific_notes
            )
            
            api_results.append(api_result)
        
        logger.info(f"Successfully generated {len(api_results)} enhanced portfolios")
        return api_results
        
    except ValueError as e:
        logger.error(f"Validation error in enhanced optimization: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in enhanced portfolio optimization: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during optimization")

@router.get("/portfolio/analytics-info")
async def get_analytics_info():
    """
    Get information about available analytics and crisis periods
    """
    return {
        "crisis_periods": [
            {
                "name": "2008 Financial Crisis",
                "type": "financial_crisis",
                "start_date": "2007-10-09",
                "end_date": "2009-03-09",
                "market_decline": -56.8,
                "description": "Global financial crisis and recession"
            },
            {
                "name": "2020 COVID Pandemic", 
                "type": "pandemic",
                "start_date": "2020-02-19",
                "end_date": "2020-03-23",
                "market_decline": -33.9,
                "description": "COVID-19 pandemic market crash"
            },
            {
                "name": "2022 Bear Market",
                "type": "bear_market", 
                "start_date": "2022-01-03",
                "end_date": "2022-10-12",
                "market_decline": -25.4,
                "description": "Inflation and rate hike bear market"
            }
        ],
        "rolling_periods": ["3yr", "5yr", "10yr"],
        "risk_metrics": [
            "Value at Risk (95%)",
            "Conditional Value at Risk (95%)",
            "Sortino Ratio",
            "Calmar Ratio", 
            "Maximum Monthly Loss",
            "Worst 12-Month Return",
            "Downside Volatility",
            "Upside/Downside Capture"
        ],
        "account_types": ["taxable", "tax_deferred", "tax_free"]
    }

@router.get("/portfolio/asset-universe")
async def get_asset_universe():
    """
    Get information about the 7-asset universe used for optimization
    """
    return {
        "assets": [
            {"symbol": "VTI", "name": "Total Stock Market", "category": "US Equity"},
            {"symbol": "VTIAX", "name": "Total International Stock", "category": "International Equity"},
            {"symbol": "BND", "name": "Total Bond Market", "category": "Bonds"},
            {"symbol": "VNQ", "name": "Real Estate", "category": "REITs"},
            {"symbol": "GLD", "name": "Gold", "category": "Commodities"},
            {"symbol": "VWO", "name": "Emerging Markets", "category": "Emerging Markets"},
            {"symbol": "QQQ", "name": "Technology Growth", "category": "Technology"}
        ],
        "data_range": {
            "start_date": "2004-01-01",
            "end_date": "2024-12-31",
            "total_records": "33,725+"
        },
        "optimization_features": [
            "Three-strategy optimization (Conservative/Balanced/Aggressive)",
            "Crisis period stress testing",
            "Rolling period consistency analysis",
            "Advanced risk metrics (VaR, CVaR, Sortino, etc.)",
            "Recovery time analysis",
            "Account type optimization",
            "Monte Carlo projections"
        ]
    }
