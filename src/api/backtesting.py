"""
Backtesting API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import time
from typing import Dict, Any

from src.models.database import get_db
from src.core.portfolio_engine import PortfolioEngine
from src.api.models import (
    BacktestRequest, BacktestResponse, PerformanceMetrics, ErrorResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/backtest", tags=["backtesting"])

@router.post("/portfolio", response_model=BacktestResponse)
async def backtest_portfolio(
    request: BacktestRequest,
    db: Session = Depends(get_db)
):
    """
    Backtest a portfolio with the given allocation and parameters
    
    This endpoint performs a comprehensive backtest of a portfolio allocation
    and returns detailed performance metrics.
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting backtest for allocation: {request.allocation.allocation}")
        
        # Create portfolio engine
        engine = PortfolioEngine(db)
        
        # Check if we have cached results first
        allocation_dict = request.allocation.allocation
        cached_result = engine.get_cached_portfolio_snapshot(allocation_dict)
        
        if cached_result:
            logger.info("Returning cached backtest result")
            calculation_time = time.time() - start_time
            
            # Convert cached result to response format
            metrics = PerformanceMetrics(
                total_return=cached_result.total_return or 0,
                cagr=cached_result.cagr or 0,
                volatility=cached_result.volatility or 0,
                max_drawdown=cached_result.max_drawdown or 0,
                sharpe_ratio=cached_result.sharpe_ratio or 0,
                sortino_ratio=0,  # Not stored in cache yet
                win_rate=0,       # Not stored in cache yet
                total_trading_days=0  # Not stored in cache yet
            )
            
            # Calculate final value from total return
            final_value = request.initial_value * (1 + metrics.total_return)
            
            return BacktestResponse(
                success=True,
                allocation=allocation_dict,
                initial_value=request.initial_value,
                final_value=final_value,
                performance_metrics=metrics,
                calculation_time_seconds=calculation_time,
                cache_hit=True
            )
        
        # Run fresh backtest
        logger.info("Running fresh backtest calculation")
        results = engine.backtest_portfolio(
            allocation=allocation_dict,
            initial_value=request.initial_value,
            start_date=request.start_date,
            end_date=request.end_date,
            rebalance_frequency=request.rebalance_frequency
        )
        
        # Save results to cache
        metrics_dict = results['performance_metrics']
        engine.save_portfolio_snapshot(allocation_dict, metrics_dict)
        
        # Convert to response format
        metrics = PerformanceMetrics(**metrics_dict)
        
        calculation_time = time.time() - start_time
        logger.info(f"Backtest completed in {calculation_time:.2f} seconds")
        
        return BacktestResponse(
            success=True,
            allocation=allocation_dict,
            initial_value=request.initial_value,
            final_value=results['final_value'],
            performance_metrics=metrics,
            calculation_time_seconds=calculation_time,
            cache_hit=False
        )
        
    except ValueError as e:
        logger.error(f"Validation error during backtest: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during backtest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during backtesting"
        )