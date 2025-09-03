"""
Portfolio Optimization API Routes - Sprint 3

Enhanced portfolio optimization endpoints providing:
- Three-strategy optimization (Conservative/Balanced/Aggressive)
- Target achievement analysis  
- Rebalancing strategy recommendations
- New money vs traditional rebalancing comparison
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import logging

from ..models.database import get_db
from ..optimization.portfolio_optimizer import (
    PortfolioOptimizer, PortfolioRequest, AccountType, StrategyType
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/portfolio", tags=["Portfolio Optimization V2"])

# Pydantic models for API
class OptimizationRequestAPI(BaseModel):
    """API model for portfolio optimization requests"""
    current_savings: float = Field(10000.0, gt=0, description="Current portfolio value")
    target_amount: Optional[float] = Field(None, gt=0, description="Target portfolio value (optional)")
    time_horizon: int = Field(10, ge=1, le=50, description="Investment time horizon in years")
    account_type: str = Field("taxable", description="Account type: taxable, tax_deferred, or tax_free")
    new_money_available: bool = Field(False, description="Can you add new money regularly?")
    max_annual_contribution: Optional[float] = Field(None, ge=0, description="Maximum annual contribution if new money available")
    
    @validator('account_type')
    def validate_account_type(cls, v):
        valid_types = ['taxable', 'tax_deferred', 'tax_free']
        if v not in valid_types:
            raise ValueError(f"Account type must be one of: {valid_types}")
        return v

class PortfolioAllocationAPI(BaseModel):
    """API model for portfolio allocation"""
    VTI: float
    VTIAX: float  
    BND: float
    VNQ: float
    GLD: float
    VWO: float
    QQQ: float

class OptimizedPortfolioAPI(BaseModel):
    """API model for single optimized portfolio"""
    strategy: str
    allocation: PortfolioAllocationAPI
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    optimal_rebalancing: str
    rebalancing_rationale: str
    new_money_needed_annual: Optional[float]
    new_money_needed_monthly: Optional[float]
    traditional_rebalancing_tax_drag: Optional[float]
    rebalancing_analysis: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Comparison of different rebalancing strategies")

class TargetAnalysisAPI(BaseModel):
    """API model for target achievement analysis"""
    probability: float = Field(..., ge=0, le=1, description="Probability of achieving target")
    expected_final_value: float
    target_value: float
    shortfall_risk: float

class OptimizationResultAPI(BaseModel):
    """API model for complete optimization result"""
    request_summary: Dict[str, Any]
    portfolios: Dict[str, OptimizedPortfolioAPI]
    target_analysis: Optional[Dict[str, TargetAnalysisAPI]]
    optimization_metadata: Dict[str, Any]

@router.post("/optimize", response_model=OptimizationResultAPI)
async def optimize_portfolio(
    request: OptimizationRequestAPI,
    db: Session = Depends(get_db)
):
    """
    Optimize portfolio allocation using three strategies
    
    Returns optimized portfolios for Conservative, Balanced, and Aggressive strategies
    with comprehensive analytics and rebalancing recommendations.
    """
    
    try:
        logger.info(f"Portfolio optimization request: {request.time_horizon}yr horizon, ${request.current_savings:,.0f}")
        
        # Convert API request to internal format
        internal_request = PortfolioRequest(
            current_savings=request.current_savings,
            target_amount=request.target_amount,
            time_horizon=request.time_horizon,
            account_type=AccountType(request.account_type),
            new_money_available=request.new_money_available,
            max_annual_contribution=request.max_annual_contribution
        )
        
        # Initialize optimizer and run optimization
        optimizer = PortfolioOptimizer(db)
        result = optimizer.optimize_portfolio(internal_request)
        
        # Convert internal result to API format
        api_portfolios = {}
        for strategy, portfolio in result.portfolios.items():
            api_portfolios[strategy.value] = OptimizedPortfolioAPI(
                strategy=portfolio.strategy.value,
                allocation=PortfolioAllocationAPI(**portfolio.allocation),
                expected_return=round(portfolio.expected_return, 4),
                expected_volatility=round(portfolio.expected_volatility, 4),
                sharpe_ratio=round(portfolio.sharpe_ratio, 2),
                max_drawdown=round(portfolio.max_drawdown, 4),
                optimal_rebalancing=portfolio.optimal_rebalancing,
                rebalancing_rationale=portfolio.rebalancing_rationale,
                new_money_needed_annual=portfolio.new_money_needed_annual,
                new_money_needed_monthly=portfolio.new_money_needed_monthly,
                traditional_rebalancing_tax_drag=portfolio.traditional_rebalancing_tax_drag,
                rebalancing_analysis=portfolio.rebalancing_analysis
            )
            
        # Convert target analysis if present
        api_target_analysis = None
        if result.target_analysis:
            api_target_analysis = {}
            for strategy, analysis in result.target_analysis.items():
                api_target_analysis[strategy.value] = TargetAnalysisAPI(**analysis)
        
        # Prepare response
        response = OptimizationResultAPI(
            request_summary={
                "current_savings": request.current_savings,
                "target_amount": request.target_amount,
                "time_horizon": request.time_horizon,
                "account_type": request.account_type,
                "new_money_available": request.new_money_available
            },
            portfolios=api_portfolios,
            target_analysis=api_target_analysis,
            optimization_metadata=result.optimization_metadata
        )
        
        logger.info(f"Optimization completed successfully - 3 strategies generated")
        return response
        
    except Exception as e:
        logger.error(f"Portfolio optimization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio optimization failed: {str(e)}"
        )

@router.get("/strategies")  
async def get_available_strategies():
    """Get list of available optimization strategies"""
    return {
        "strategies": [
            {
                "name": "conservative",
                "description": "Global Minimum Variance with bond tilt - lowest risk",
                "typical_volatility": "8-12%",
                "typical_return": "6-8%"
            },
            {
                "name": "balanced", 
                "description": "Maximum Sharpe ratio with moderate constraints",
                "typical_volatility": "12-16%",
                "typical_return": "8-10%"
            },
            {
                "name": "aggressive",
                "description": "Maximum Sharpe ratio with growth tilt - higher returns",
                "typical_volatility": "16-22%", 
                "typical_return": "10-12%"
            }
        ],
        "account_types": [
            {
                "type": "taxable",
                "description": "Regular brokerage account - subject to capital gains tax"
            },
            {
                "type": "tax_deferred", 
                "description": "401k, Traditional IRA - tax-deferred growth"
            },
            {
                "type": "tax_free",
                "description": "Roth IRA, HSA - tax-free growth and withdrawals"
            }
        ]
    }

@router.post("/compare-rebalancing")
async def compare_rebalancing_strategies(
    allocation: PortfolioAllocationAPI,
    account_type: str = Query(..., description="Account type"),
    new_money_available: bool = Query(False, description="New money available?"),
    max_annual_contribution: Optional[float] = Query(None, description="Max annual contribution"),
    db: Session = Depends(get_db)
):
    """
    Compare new money vs traditional rebalancing strategies
    
    Shows both rebalancing approaches with tax implications and costs
    """
    
    try:
        # This will be implemented in Week 2 - connecting to RebalancingStrategyAnalyzer
        # For now, return placeholder structure
        
        return {
            "traditional_rebalancing": {
                "method": "sell_and_buy",
                "frequency": "quarterly",
                "estimated_tax_drag": 0.5,  # 0.5% annually
                "transaction_costs": 0.0,    # $0 for ETFs
                "pros": ["Precise rebalancing", "Works with any amount"],
                "cons": ["Tax implications", "Realized gains/losses"]
            },
            "new_money_rebalancing": {
                "method": "contribute_to_underweight",  
                "annual_contribution_needed": 5000,
                "monthly_contribution_needed": 417,
                "estimated_tax_drag": 0.0,
                "transaction_costs": 0.0,
                "pros": ["No selling required", "No tax events", "Dollar cost averaging"],
                "cons": ["Requires regular contributions", "Less precise rebalancing"]
            },
            "recommendation": "new_money" if new_money_available else "traditional",
            "rationale": "New money rebalancing avoids all tax implications" if new_money_available else "Traditional rebalancing required without new contributions"
        }
        
    except Exception as e:
        logger.error(f"Rebalancing comparison failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Rebalancing comparison failed: {str(e)}"
        )

@router.get("/asset-universe")
async def get_asset_universe():
    """Get information about the 7-asset universe"""
    return {
        "assets": [
            {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "class": "US Total Market"},
            {"symbol": "VTIAX", "name": "Vanguard Total International Stock Index", "class": "International Developed"},  
            {"symbol": "BND", "name": "Vanguard Total Bond Market ETF", "class": "US Bonds"},
            {"symbol": "VNQ", "name": "Vanguard Real Estate ETF", "class": "REITs"},
            {"symbol": "GLD", "name": "SPDR Gold Trust", "class": "Gold/Commodities"},
            {"symbol": "VWO", "name": "Vanguard Emerging Markets ETF", "class": "Emerging Markets"},
            {"symbol": "QQQ", "name": "Invesco QQQ Trust", "class": "Technology/Growth"}
        ],
        "data_availability": {
            "start_date": "2004-01-01",
            "end_date": "2024-12-31", 
            "total_years": 20,
            "total_records": 33725
        },
        "optimization_features": [
            "20-year historical performance analysis",
            "Crisis period stress testing (2008, 2020, 2022)",
            "Rolling period consistency analysis",
            "Correlation evolution over time",
            "Rebalancing strategy optimization"
        ]
    }
