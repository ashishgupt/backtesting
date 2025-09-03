"""
Walk-Forward Validation API Routes

This module provides RESTful API endpoints for walk-forward validation
of portfolio optimization strategies.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from datetime import datetime, date
import logging
from pathlib import Path

from ..backtesting.walk_forward_validator import WalkForwardValidator, ValidationWindow, ValidationResult
from ..optimization.portfolio_optimizer_enhanced import EnhancedPortfolioOptimizer
from ..core.data_manager import DataManager
from ..models.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/walk-forward", tags=["walk-forward-validation"])

# Request/Response Models
class WalkForwardRequest(BaseModel):
    """Request model for walk-forward validation"""
    start_date: date = Field(..., description="Start date for analysis")
    end_date: date = Field(..., description="End date for analysis")
    strategies: Optional[List[str]] = Field(None, description="Strategies to test (default: all)")
    optimization_window_months: int = Field(36, ge=12, le=60, description="Optimization window in months")
    validation_window_months: int = Field(6, ge=1, le=24, description="Validation window in months")
    step_months: int = Field(3, ge=1, le=12, description="Step size in months")
    user_params: Optional[Dict] = Field(None, description="User parameters for optimization")

class ValidationWindowResponse(BaseModel):
    """Response model for validation window"""
    window_id: str
    optimization_start: datetime
    optimization_end: datetime
    validation_start: datetime
    validation_end: datetime

class ValidationResultResponse(BaseModel):
    """Response model for validation result"""
    window_id: str
    strategy_name: str
    optimization_period_days: int
    validation_period_days: int
    optimization_return: float
    optimization_risk: float
    optimization_sharpe: float
    validation_return: float
    validation_risk: float
    validation_sharpe: float
    portfolio_allocation: Dict[str, float]
    return_degradation: float
    risk_increase: float
    sharpe_degradation: float

class StrategyStatsResponse(BaseModel):
    """Response model for strategy statistics"""
    total_windows: int
    optimization_stats: Dict[str, float]
    validation_stats: Dict[str, float]
    degradation_stats: Dict[str, float]
    consistency: Dict[str, Union[int, float]]

class WalkForwardSummaryResponse(BaseModel):
    """Response model for walk-forward summary"""
    cross_strategy_analysis: Dict
    strategy_stats: Dict[str, StrategyStatsResponse]

class WalkForwardResponse(BaseModel):
    """Complete response model for walk-forward analysis"""
    summary: WalkForwardSummaryResponse
    detailed_results: List[ValidationResultResponse]
    analysis_config: Dict
    execution_time_seconds: Optional[float] = None

# Global validator instance (will be initialized on startup)
validator_instance: Optional[WalkForwardValidator] = None

def get_validator() -> WalkForwardValidator:
    """Get or create walk-forward validator instance"""
    global validator_instance
    
    if validator_instance is None:
        # Initialize components using existing system
        from sqlalchemy.orm import Session
        from ..models.database import SessionLocal
        
        # Create database session
        db = SessionLocal()
        
        try:
            data_manager = DataManager(db)
            optimizer = EnhancedPortfolioOptimizer(data_manager)
            validator_instance = WalkForwardValidator(data_manager, optimizer)
            logger.info("Walk-forward validator initialized")
        finally:
            db.close()
    
    return validator_instance

@router.get("/status", summary="Get walk-forward validator status")
async def get_status():
    """Get the status of the walk-forward validation system"""
    try:
        validator = get_validator()
        
        # Test database connection
        from sqlalchemy.orm import Session
        from ..models.database import SessionLocal
        
        # Test by creating a session
        db = SessionLocal()
        try:
            # Simple test query
            db.execute("SELECT 1")
            db_status = "connected"
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            db_status = "disconnected"
        finally:
            db.close()
            
        test_data = ["VTI", "VTIAX", "BND", "VNQ", "GLD", "VWO", "QQQ"]  # Default symbols
        
        return {
            "status": "operational",
            "available_symbols": len(test_data),
            "validator_ready": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Walk-forward validator not operational")

@router.post("/generate-windows", 
             summary="Generate validation windows",
             response_model=List[ValidationWindowResponse])
async def generate_windows(request: WalkForwardRequest):
    """Generate validation windows for walk-forward analysis"""
    try:
        validator = get_validator()
        
        windows = validator.generate_validation_windows(
            start_date=datetime.combine(request.start_date, datetime.min.time()),
            end_date=datetime.combine(request.end_date, datetime.min.time()),
            optimization_window_months=request.optimization_window_months,
            validation_window_months=request.validation_window_months,
            step_months=request.step_months
        )
        
        return [
            ValidationWindowResponse(
                window_id=w.window_id,
                optimization_start=w.optimization_start,
                optimization_end=w.optimization_end,
                validation_start=w.validation_start,
                validation_end=w.validation_end
            )
            for w in windows
        ]
        
    except Exception as e:
        logger.error(f"Error generating windows: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/validate-strategy",
             summary="Validate single strategy in a window",
             response_model=ValidationResultResponse)
async def validate_strategy(
    window_id: str,
    strategy_name: str,
    optimization_start: datetime,
    optimization_end: datetime,
    validation_start: datetime,
    validation_end: datetime,
    user_params: Optional[Dict] = None
):
    """Validate a single strategy in a specific validation window"""
    try:
        validator = get_validator()
        
        # Create validation window
        window = ValidationWindow(
            optimization_start=optimization_start,
            optimization_end=optimization_end,
            validation_start=validation_start,
            validation_end=validation_end,
            window_id=window_id
        )
        
        # Default user params if not provided
        if user_params is None:
            user_params = {
                'current_age': 35,
                'retirement_age': 65,
                'target_amount': 1000000,
                'initial_investment': 100000,
                'monthly_contribution': 2000,
                'risk_tolerance': 'balanced',
                'account_types': {
                    'tax_free': 0.3,
                    'tax_deferred': 0.4,
                    'taxable': 0.3
                }
            }
        
        result = validator.validate_strategy_window(window, strategy_name, user_params)
        
        return ValidationResultResponse(
            window_id=result.window_id,
            strategy_name=result.strategy_name,
            optimization_period_days=result.optimization_period_days,
            validation_period_days=result.validation_period_days,
            optimization_return=result.optimization_return,
            optimization_risk=result.optimization_risk,
            optimization_sharpe=result.optimization_sharpe,
            validation_return=result.validation_return,
            validation_risk=result.validation_risk,
            validation_sharpe=result.validation_sharpe,
            portfolio_allocation=result.portfolio_allocation,
            return_degradation=result.return_degradation,
            risk_increase=result.risk_increase,
            sharpe_degradation=result.sharpe_degradation
        )
        
    except Exception as e:
        logger.error(f"Error validating strategy: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/run-analysis",
             summary="Run complete walk-forward analysis",
             response_model=WalkForwardResponse)
async def run_walk_forward_analysis(request: WalkForwardRequest):
    """Run complete walk-forward validation analysis"""
    try:
        start_time = datetime.now()
        validator = get_validator()
        
        # Set default user params if not provided
        user_params = request.user_params
        if user_params is None:
            user_params = {
                'current_age': 35,
                'retirement_age': 65,
                'target_amount': 1000000,
                'initial_investment': 100000,
                'monthly_contribution': 2000,
                'risk_tolerance': 'balanced',
                'account_types': {
                    'tax_free': 0.3,
                    'tax_deferred': 0.4,
                    'taxable': 0.3
                }
            }
        
        # Set default strategies if not provided
        strategies = request.strategies
        if strategies is None:
            strategies = ['conservative', 'balanced', 'aggressive']
        
        # Run analysis
        logger.info(f"Starting walk-forward analysis with parameters: start_date={request.start_date}, end_date={request.end_date}")
        results = validator.run_walk_forward_analysis(
            start_date=datetime.combine(request.start_date, datetime.min.time()),
            end_date=datetime.combine(request.end_date, datetime.min.time()),
            strategies=strategies,
            user_params=user_params,
            optimization_window_months=request.optimization_window_months,
            validation_window_months=request.validation_window_months,
            step_months=request.step_months
        )
        
        logger.info(f"Analysis completed with {len(results.get('detailed_results', []))} results")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Convert results to response format
        detailed_results = [
            ValidationResultResponse(
                window_id=r.window_id,
                strategy_name=r.strategy_name,
                optimization_period_days=r.optimization_period_days,
                validation_period_days=r.validation_period_days,
                optimization_return=r.optimization_return,
                optimization_risk=r.optimization_risk,
                optimization_sharpe=r.optimization_sharpe,
                validation_return=r.validation_return,
                validation_risk=r.validation_risk,
                validation_sharpe=r.validation_sharpe,
                portfolio_allocation=r.portfolio_allocation,
                return_degradation=r.return_degradation,
                risk_increase=r.risk_increase,
                sharpe_degradation=r.sharpe_degradation
            )
            for r in results['detailed_results']
        ]
        
        # Convert strategy stats to response format
        strategy_stats = {}
        if 'summary' in results and isinstance(results['summary'], dict):
            for strategy, stats in results['summary'].items():
                if strategy != 'cross_strategy_analysis' and isinstance(stats, dict):
                    strategy_stats[strategy] = StrategyStatsResponse(**stats)
        
        return WalkForwardResponse(
            summary=WalkForwardSummaryResponse(
                cross_strategy_analysis=results['summary'].get('cross_strategy_analysis', {}),
                strategy_stats=strategy_stats
            ),
            detailed_results=detailed_results,
            analysis_config=results['analysis_config'],
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        logger.error(f"Error running walk-forward analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/summary",
            summary="Get summary of last analysis",
            response_model=WalkForwardSummaryResponse)
async def get_results_summary():
    """Get summary statistics from the last walk-forward analysis"""
    try:
        validator = get_validator()
        
        if not validator.validation_results:
            raise HTTPException(status_code=404, detail="No validation results available")
        
        summary = validator._generate_walk_forward_summary(validator.validation_results)
        
        # Convert strategy stats to response format
        strategy_stats = {}
        for strategy, stats in summary.items():
            if strategy != 'cross_strategy_analysis' and isinstance(stats, dict):
                strategy_stats[strategy] = StrategyStatsResponse(**stats)
        
        return WalkForwardSummaryResponse(
            cross_strategy_analysis=summary.get('cross_strategy_analysis', {}),
            strategy_stats=strategy_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/recommendations")
async def get_configuration_recommendations():
    """Get recommendations for walk-forward analysis configuration"""
    return {
        "recommended_configurations": {
            "quick_analysis": {
                "optimization_window_months": 24,
                "validation_window_months": 3,
                "step_months": 3,
                "description": "Fast analysis for initial testing",
                "expected_windows": "~15-20 windows",
                "expected_time": "5-10 minutes"
            },
            "standard_analysis": {
                "optimization_window_months": 36,
                "validation_window_months": 6,
                "step_months": 3,
                "description": "Balanced analysis for most use cases",
                "expected_windows": "~20-30 windows",
                "expected_time": "10-20 minutes"
            },
            "comprehensive_analysis": {
                "optimization_window_months": 48,
                "validation_window_months": 12,
                "step_months": 6,
                "description": "Thorough analysis for production strategies",
                "expected_windows": "~10-15 windows",
                "expected_time": "15-30 minutes"
            },
            "research_analysis": {
                "optimization_window_months": 60,
                "validation_window_months": 6,
                "step_months": 1,
                "description": "Detailed research with monthly reoptimization",
                "expected_windows": "~100+ windows",
                "expected_time": "1-3 hours"
            }
        },
        "parameter_guidelines": {
            "optimization_window_months": {
                "minimum": 12,
                "recommended": 36,
                "maximum": 60,
                "notes": "Longer windows provide more data but may include outdated market regimes"
            },
            "validation_window_months": {
                "minimum": 1,
                "recommended": 6,
                "maximum": 24,
                "notes": "Should be long enough to capture strategy performance but not too long to delay feedback"
            },
            "step_months": {
                "minimum": 1,
                "recommended": 3,
                "maximum": 12,
                "notes": "Smaller steps provide more data points but increase computation time"
            }
        },
        "data_requirements": {
            "minimum_history_years": 5,
            "recommended_history_years": 15,
            "optimal_history_years": 20,
            "notes": "More history allows for longer optimization windows and better crisis testing"
        }
    }
