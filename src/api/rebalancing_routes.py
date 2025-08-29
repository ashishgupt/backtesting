# Rebalancing Strategy Analysis Routes - Standalone Implementation

from fastapi import APIRouter
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os

# Add the project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.rebalancing_strategy_analyzer import (
    RebalancingStrategyAnalyzer,
    RebalancingFrequency,
    AccountType
)
from src.core.portfolio_engine_optimized import OptimizedPortfolioEngine

# Create a separate router for rebalancing routes
rebalancing_router = APIRouter(prefix="/api/analyze", tags=["rebalancing"])

# Request Models
class RebalancingStrategyRequest(BaseModel):
    allocation: Dict[str, float] = Field(
        ...,
        description="Target portfolio allocation (symbol -> weight)",
        example={"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1}
    )
    strategy_type: str = Field(
        ...,
        description="Type of rebalancing strategy",
        pattern="^(threshold|time_based|new_money)$"
    )
    threshold_percentages: Optional[List[float]] = Field(
        None,
        description="Drift thresholds to test (for threshold strategy)",
        example=[5, 10, 15, 20]
    )
    rebalancing_frequencies: Optional[List[str]] = Field(
        None,
        description="Frequencies to test (for time-based strategy)",
        example=["monthly", "quarterly", "annual"]
    )
    monthly_contribution: Optional[float] = Field(
        None,
        description="Monthly contribution amount (for new money strategy)",
        example=1000
    )
    account_type: str = Field(
        "taxable",
        description="Account type for tax calculations",
        pattern="^(taxable|tax_deferred|tax_free)$"
    )
    transaction_cost_pct: Optional[float] = Field(
        0.1,
        description="Transaction cost as percentage",
        ge=0,
        le=5.0
    )
    
    @validator('allocation')
    def validate_allocation(cls, v):
        if not v:
            raise ValueError("Allocation cannot be empty")
        total_weight = sum(v.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Allocation weights must sum to 1.0, got {total_weight}")
        return v

# Response Models
class RebalancingResultModel(BaseModel):
    strategy_name: str
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    total_transaction_costs: float
    total_tax_costs: float
    total_costs: float
    rebalancing_events_count: int
    average_drift: float
    drift_episodes: int
    rebalancing_effectiveness: float
    cost_adjusted_return: float

class RebalancingAnalysisResponse(BaseModel):
    results: List[RebalancingResultModel]
    best_strategy: Optional[str]
    execution_time_seconds: float

# Routes
@rebalancing_router.post("/rebalancing-strategy", response_model=RebalancingAnalysisResponse)
async def analyze_rebalancing_strategy(request: RebalancingStrategyRequest):
    """
    Analyze different portfolio rebalancing strategies
    
    Supports threshold-based, time-based, and new money rebalancing strategies
    with comprehensive cost and performance analysis.
    """
    try:
        start_time = datetime.now()
        
        # Initialize analyzer
        portfolio_engine = OptimizedPortfolioEngine()
        price_data = portfolio_engine._get_asset_prices(list(request.allocation.keys()))
        
        analyzer = RebalancingStrategyAnalyzer(price_data)
        analyzer.set_cost_parameters(transaction_cost=request.transaction_cost_pct / 100)
        
        account_type = AccountType(request.account_type)
        results = []
        
        if request.strategy_type == "threshold":
            thresholds = request.threshold_percentages or [5, 10, 15, 20]
            results = analyzer.analyze_threshold_rebalancing(
                target_allocation=request.allocation,
                threshold_percentages=thresholds,
                account_type=account_type
            )
            
        elif request.strategy_type == "time_based":
            frequencies = []
            for freq_str in (request.rebalancing_frequencies or ["monthly", "quarterly", "annual"]):
                frequencies.append(RebalancingFrequency(freq_str))
                
            results = analyzer.analyze_time_based_rebalancing(
                target_allocation=request.allocation,
                frequencies=frequencies,
                account_type=account_type
            )
            
        elif request.strategy_type == "new_money":
            monthly_contribution = request.monthly_contribution or 1000
            result = analyzer.analyze_new_money_rebalancing(
                target_allocation=request.allocation,
                monthly_contribution=monthly_contribution,
                account_type=account_type
            )
            results = [result]
        
        # Convert to response models
        result_models = []
        for result in results:
            total_costs = result.total_transaction_costs + result.total_tax_costs
            cost_adjusted_return = result.total_return - (total_costs / 100000)
            
            result_model = RebalancingResultModel(
                strategy_name=result.strategy_name,
                total_return=result.total_return,
                annualized_return=result.annualized_return,
                volatility=result.volatility,
                sharpe_ratio=result.sharpe_ratio,
                max_drawdown=result.max_drawdown,
                total_transaction_costs=result.total_transaction_costs,
                total_tax_costs=result.total_tax_costs,
                total_costs=total_costs,
                rebalancing_events_count=len(result.rebalancing_events),
                average_drift=result.average_drift,
                drift_episodes=result.drift_episodes,
                rebalancing_effectiveness=result.rebalancing_effectiveness,
                cost_adjusted_return=cost_adjusted_return
            )
            result_models.append(result_model)
        
        # Determine best strategy
        best_strategy = None
        best_score = float('-inf')
        for result_model in result_models:
            score = result_model.sharpe_ratio * (1 - result_model.total_costs / 10000)
            if score > best_score:
                best_score = score
                best_strategy = result_model.strategy_name
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return RebalancingAnalysisResponse(
            results=result_models,
            best_strategy=best_strategy,
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Rebalancing analysis failed: {str(e)}")

@rebalancing_router.get("/rebalancing-strategy/examples")
async def get_rebalancing_examples():
    """Get example requests for rebalancing strategy analysis"""
    return {
        "threshold_analysis": {
            "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
            "strategy_type": "threshold",
            "threshold_percentages": [5, 10, 15, 20],
            "account_type": "taxable",
            "transaction_cost_pct": 0.1
        },
        "time_based_analysis": {
            "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
            "strategy_type": "time_based",
            "rebalancing_frequencies": ["monthly", "quarterly", "annual"],
            "account_type": "tax_deferred"
        },
        "new_money_analysis": {
            "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
            "strategy_type": "new_money",
            "monthly_contribution": 1000,
            "account_type": "taxable"
        }
    }
