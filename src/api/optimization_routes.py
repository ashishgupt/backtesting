"""
Portfolio optimization API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from typing import List, Dict, Optional

from src.models.database import get_db
from src.core.optimization_engine import OptimizationEngine
from src.api.models import AssetInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/optimize", tags=["optimization"])

# Pydantic models for optimization endpoints
from pydantic import BaseModel, Field, validator

class OptimizationConstraints(BaseModel):
    """Asset allocation constraints"""
    min_weight: float = Field(0.0, ge=0.0, le=1.0, description="Minimum allocation weight")
    max_weight: float = Field(1.0, ge=0.0, le=1.0, description="Maximum allocation weight")
    
    @validator('max_weight')
    def max_must_be_greater_than_min(cls, v, values):
        if 'min_weight' in values and v < values['min_weight']:
            raise ValueError('max_weight must be greater than or equal to min_weight')
        return v

class EfficientFrontierRequest(BaseModel):
    """Request for efficient frontier calculation"""
    assets: Optional[List[str]] = Field(
        default=None, 
        description="Asset symbols (defaults to VTI, VTIAX, BND)"
    )
    start_date: str = Field("2015-01-02", description="Start date for historical data")
    end_date: str = Field("2024-12-31", description="End date for historical data") 
    num_portfolios: int = Field(100, ge=10, le=500, description="Number of portfolios to generate")
    constraints: Optional[Dict[str, OptimizationConstraints]] = Field(
        default=None,
        description="Asset allocation constraints"
    )

class PortfolioPoint(BaseModel):
    """Single portfolio point on efficient frontier"""
    weights: Dict[str, float] = Field(..., description="Asset allocation weights")
    expected_return: float = Field(..., description="Expected annual return")
    volatility: float = Field(..., description="Expected annual volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")

class EfficientFrontierResponse(BaseModel):
    """Response for efficient frontier calculation"""
    success: bool = Field(True, description="Whether optimization completed successfully")
    portfolios: List[PortfolioPoint] = Field(..., description="Efficient frontier portfolios")
    num_portfolios: int = Field(..., description="Number of portfolios generated")
    assets: List[str] = Field(..., description="Assets used in optimization")
    date_range: Dict[str, str] = Field(..., description="Date range for historical data")
    expected_returns: Dict[str, float] = Field(..., description="Expected returns by asset")
    correlation_matrix: Dict[str, Dict[str, float]] = Field(..., description="Asset correlation matrix")
    calculation_time_seconds: Optional[float] = Field(None, description="Time taken to calculate")

class MaxSharpeRequest(BaseModel):
    """Request for maximum Sharpe ratio portfolio"""
    assets: Optional[List[str]] = Field(
        default=None,
        description="Asset symbols (defaults to VTI, VTIAX, BND)"
    )
    start_date: str = Field("2015-01-02", description="Start date for historical data")
    end_date: str = Field("2024-12-31", description="End date for historical data")
    constraints: Optional[Dict[str, OptimizationConstraints]] = Field(
        default=None,
        description="Asset allocation constraints"
    )

class MaxSharpeResponse(BaseModel):
    """Response for maximum Sharpe ratio portfolio"""
    success: bool = Field(True, description="Whether optimization completed successfully")
    weights: Dict[str, float] = Field(..., description="Optimal asset weights")
    expected_return: float = Field(..., description="Expected annual return")
    volatility: float = Field(..., description="Expected annual volatility") 
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    optimization_success: bool = Field(..., description="Whether scipy optimization converged")
    calculation_time_seconds: Optional[float] = Field(None, description="Time taken to calculate")

@router.post("/efficient-frontier", response_model=EfficientFrontierResponse)
async def calculate_efficient_frontier(
    request: EfficientFrontierRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate efficient frontier for portfolio optimization
    
    Returns a set of optimal portfolios along the risk-return spectrum,
    allowing users to choose their preferred risk/return tradeoff.
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Calculating efficient frontier for assets: {request.assets}")
        
        engine = OptimizationEngine(db)
        
        # Convert constraints format
        constraints_dict = None
        if request.constraints:
            constraints_dict = {
                asset: {'min': constraint.min_weight, 'max': constraint.max_weight}
                for asset, constraint in request.constraints.items()
            }
        
        # Calculate efficient frontier
        result = engine.calculate_efficient_frontier(
            assets=request.assets,
            start_date=request.start_date,
            end_date=request.end_date,
            num_portfolios=request.num_portfolios,
            constraints=constraints_dict
        )
        
        # Convert to response format
        portfolio_points = []
        for portfolio in result['portfolios']:
            # Convert numpy types to Python types
            weights = {k: float(v) for k, v in portfolio['weights'].items()}
            portfolio_points.append(PortfolioPoint(
                weights=weights,
                expected_return=float(portfolio['expected_return']),
                volatility=float(portfolio['volatility']),
                sharpe_ratio=float(portfolio['sharpe_ratio'])
            ))
        
        # Convert expected returns and correlation matrix
        expected_returns = {k: float(v) for k, v in result['expected_returns'].items()}
        correlation_matrix = {
            k: {k2: float(v2) for k2, v2 in v.items()}
            for k, v in result['correlation_matrix'].items()
        }
        
        calculation_time = time.time() - start_time
        logger.info(f"Efficient frontier calculated in {calculation_time:.2f} seconds")
        
        return EfficientFrontierResponse(
            success=True,
            portfolios=portfolio_points,
            num_portfolios=result['num_portfolios'],
            assets=result['assets'],
            date_range=result['date_range'],
            expected_returns=expected_returns,
            correlation_matrix=correlation_matrix,
            calculation_time_seconds=calculation_time
        )
        
    except ValueError as e:
        logger.error(f"Validation error in efficient frontier calculation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in efficient frontier calculation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during optimization"
        )

@router.post("/max-sharpe", response_model=MaxSharpeResponse)
async def find_max_sharpe_portfolio(
    request: MaxSharpeRequest,
    db: Session = Depends(get_db)
):
    """
    Find portfolio with maximum Sharpe ratio
    
    Returns the single portfolio that provides the best risk-adjusted returns
    according to the Sharpe ratio metric.
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Finding max Sharpe portfolio for assets: {request.assets}")
        
        engine = OptimizationEngine(db)
        
        # Convert constraints format
        constraints_dict = None
        if request.constraints:
            constraints_dict = {
                asset: {'min': constraint.min_weight, 'max': constraint.max_weight}
                for asset, constraint in request.constraints.items()
            }
        
        # Find optimal portfolio
        result = engine.find_max_sharpe_portfolio(
            assets=request.assets,
            start_date=request.start_date,
            end_date=request.end_date,
            constraints=constraints_dict
        )
        
        calculation_time = time.time() - start_time
        logger.info(f"Max Sharpe portfolio found in {calculation_time:.2f} seconds")
        
        # Convert numpy types to Python types for JSON serialization
        weights = {k: float(v) for k, v in result['weights'].items()}
        
        return MaxSharpeResponse(
            success=True,
            weights=weights,
            expected_return=float(result['expected_return']),
            volatility=float(result['volatility']),
            sharpe_ratio=float(result['sharpe_ratio']),
            optimization_success=result['optimization_success'],
            calculation_time_seconds=calculation_time
        )
        
    except ValueError as e:
        logger.error(f"Validation error in max Sharpe calculation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in max Sharpe calculation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during optimization"
        )