"""
Market Regime Awareness API Routes

This module provides API endpoints for market regime detection and analysis
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging
import pandas as pd

from ..regime.regime_detector import MarketRegimeDetector
from ..regime.regime_analyzer import RegimeAwareAnalyzer
from ..models.base import DatabaseManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/regime", tags=["regime-analysis"])

# Pydantic Models
class RegimeDetectionRequest(BaseModel):
    lookback_days: int = Field(default=252, ge=30, le=1000, 
                              description="Days to look back for regime detection")
    include_historical: bool = Field(default=False, 
                                    description="Include historical regime analysis")

class RegimeDetectionResponse(BaseModel):
    regime_type: str
    regime_name: str  
    confidence_score: float
    key_indicators: Dict
    supporting_factors: List[str]
    regime_description: str
    detection_date: datetime
    lookback_period: int

class HistoricalRegimeResponse(BaseModel):
    regime_history: List[Dict]
    regime_transitions: List[Dict]
    regime_summary: Dict

class RegimeRecommendationRequest(BaseModel):
    current_portfolio: Dict[str, float] = Field(
        description="Current portfolio allocation as {asset: weight}"
    )
    risk_tolerance: str = Field(default="balanced", 
                               pattern="^(conservative|balanced|aggressive)$",
                               description="Risk tolerance level")

class RegimeRecommendationResponse(BaseModel):
    current_regime: Dict
    regime_adjustments: Dict
    recommended_changes: Dict
    rebalancing_guidance: Dict
    risk_management_advice: List[str]
    monitoring_suggestions: List[str]

class PerformanceAnalysisRequest(BaseModel):
    portfolio_returns: List[float] = Field(description="Portfolio return series")
    return_dates: List[str] = Field(description="Dates for returns (YYYY-MM-DD format)")
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class PerformanceAnalysisResponse(BaseModel):
    regime_performance: Dict
    regime_summary: Dict
    current_regime_forecast: Dict
    strategy_recommendations: List[Dict]

# Initialize components
regime_detector = MarketRegimeDetector()
regime_analyzer = RegimeAwareAnalyzer()

@router.post("/detect-current", response_model=RegimeDetectionResponse)
async def detect_current_regime(request: RegimeDetectionRequest):
    """
    Detect the current market regime based on recent indicators
    """
    try:
        # Get price data from database
        db_manager = DatabaseManager()
        # Get the latest available date from database instead of using current date
        latest_date_query = """
        SELECT MAX(date) FROM daily_prices 
        WHERE symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
        """
        latest_result = db_manager.execute_query(latest_date_query)
        if latest_result and latest_result[0][0]:
            end_date = pd.to_datetime(latest_result[0][0])
        else:
            end_date = datetime.now()  # Fallback
            
        # Ensure minimum data for calculations: 252 days for 12m momentum + 200 days for MA + buffer
        min_required_days = max(365, 252 + 200 + 50)  # At least 502 days total
        total_days = max(request.lookback_days + 365, min_required_days)
        start_date = end_date - timedelta(days=total_days)
        
        query = """
        SELECT date, symbol, adj_close
        FROM daily_prices 
        WHERE date BETWEEN %s AND %s
        AND symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
        ORDER BY date, symbol
        """
        
        results = db_manager.execute_query(query, (start_date, end_date))
        
        if not results:
            raise HTTPException(status_code=404, detail="No price data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(results, columns=['date', 'symbol', 'price'])
        price_data = df.pivot(index='date', columns='symbol', values='price')
        price_data.index = pd.to_datetime(price_data.index)
        # Convert decimal to float and forward fill
        price_data = price_data.astype(float)
        price_data = price_data.ffill().dropna()
        
        if price_data.empty:
            raise HTTPException(status_code=404, detail="Insufficient price data")
        
        # Detect current regime
        regime_result = regime_detector.detect_current_regime(
            price_data, request.lookback_days
        )
        
        response = RegimeDetectionResponse(
            regime_type=regime_result['regime_type'],
            regime_name=regime_result['regime_name'],
            confidence_score=regime_result['confidence_score'], 
            key_indicators=regime_result['key_indicators'],
            supporting_factors=regime_result['supporting_factors'],
            regime_description=regime_result['regime_description'],
            detection_date=regime_result['detection_date'],
            lookback_period=regime_result['lookback_period']
        )
        
        logger.info(f"Current regime detected: {response.regime_name} "
                   f"(confidence: {response.confidence_score:.2f})")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in regime detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Regime detection failed: {str(e)}")

@router.get("/historical", response_model=HistoricalRegimeResponse)
async def get_historical_regimes(
    lookback_months: int = Query(default=36, ge=6, le=120, 
                                description="Months of historical analysis"),
    window_days: int = Query(default=126, ge=60, le=504,
                           description="Window size for regime detection"), 
    step_days: int = Query(default=21, ge=7, le=63,
                         description="Step size between detections")
):
    """
    Get historical market regime analysis over the specified period
    """
    try:
        # Get price data
        db_manager = DatabaseManager()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_months * 30 + window_days)
        
        query = """
        SELECT date, symbol, adj_close
        FROM daily_prices 
        WHERE date BETWEEN %s AND %s
        AND symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
        ORDER BY date, symbol
        """
        
        results = db_manager.execute_query(query, (start_date, end_date))
        
        if not results:
            raise HTTPException(status_code=404, detail="No historical price data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(results, columns=['date', 'symbol', 'price'])
        price_data = df.pivot(index='date', columns='symbol', values='price')
        price_data.index = pd.to_datetime(price_data.index)
        # Convert decimal to float and forward fill
        price_data = price_data.astype(float)
        price_data = price_data.ffill().dropna()
        
        # Detect historical regimes
        historical_regimes = regime_detector.detect_historical_regimes(
            price_data, window_days, step_days
        )
        
        if historical_regimes.empty:
            raise HTTPException(status_code=404, detail="No historical regimes detected")
        
        # Get regime transitions
        transitions = regime_detector.get_regime_transitions(historical_regimes)
        
        # Create response
        regime_history = []
        for date, row in historical_regimes.iterrows():
            regime_history.append({
                'date': date.isoformat(),
                'regime_type': row['regime_type'],
                'regime_name': row['regime_name'],
                'confidence': row['confidence'],
                'momentum_3m': row['momentum_3m'],
                'volatility_percentile': row['volatility_percentile'],
                'risk_regime': row['risk_regime']
            })
        
        # Process transitions
        transition_list = []
        for transition in transitions:
            transition_list.append({
                'date': transition['date'].isoformat(),
                'from_regime': transition['from_regime'],
                'to_regime': transition['to_regime'],
                'confidence': transition['confidence'],
                'duration_days': transition['duration_days']
            })
        
        # Generate summary
        regime_counts = historical_regimes['regime_type'].value_counts().to_dict()
        avg_confidence = historical_regimes['confidence'].mean()
        
        regime_summary = {
            'total_periods': len(historical_regimes),
            'regime_distribution': regime_counts,
            'average_confidence': avg_confidence,
            'transition_count': len(transitions),
            'analysis_period_days': lookback_months * 30
        }
        
        response = HistoricalRegimeResponse(
            regime_history=regime_history,
            regime_transitions=transition_list,
            regime_summary=regime_summary
        )
        
        logger.info(f"Historical regime analysis complete: {len(regime_history)} periods, "
                   f"{len(transitions)} transitions")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in historical regime analysis: {str(e)}")
        raise HTTPException(status_code=500, 
                          detail=f"Historical regime analysis failed: {str(e)}")
@router.post("/recommendations", response_model=RegimeRecommendationResponse)
async def get_regime_recommendations(request: RegimeRecommendationRequest):
    """
    Get regime-aware portfolio recommendations based on current market conditions
    """
    try:
        # Validate portfolio weights sum to approximately 1.0
        total_weight = sum(request.current_portfolio.values())
        if not (0.95 <= total_weight <= 1.05):
            raise HTTPException(
                status_code=400, 
                detail=f"Portfolio weights sum to {total_weight:.3f}, should sum to ~1.0"
            )
        
        # Get regime-aware recommendations
        recommendations = regime_analyzer.get_regime_aware_recommendations(
            request.current_portfolio, request.risk_tolerance
        )
        
        if not recommendations:
            raise HTTPException(status_code=500, detail="Failed to generate recommendations")
        
        response = RegimeRecommendationResponse(
            current_regime=recommendations['current_regime'],
            regime_adjustments=recommendations['regime_adjustments'],
            recommended_changes=recommendations['recommended_changes'],
            rebalancing_guidance=recommendations['rebalancing_guidance'],
            risk_management_advice=recommendations['risk_management_advice'],
            monitoring_suggestions=recommendations['monitoring_suggestions']
        )
        
        regime_name = recommendations['current_regime'].get('regime_name', 'Unknown')
        logger.info(f"Regime recommendations generated for {regime_name} regime")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating regime recommendations: {str(e)}")
        raise HTTPException(status_code=500, 
                          detail=f"Recommendation generation failed: {str(e)}")

@router.post("/performance-analysis", response_model=PerformanceAnalysisResponse)
async def analyze_performance_by_regime(request: PerformanceAnalysisRequest):
    """
    Analyze portfolio performance across different market regimes
    """
    try:
        # Validate input data
        if len(request.portfolio_returns) != len(request.return_dates):
            raise HTTPException(
                status_code=400,
                detail="Number of returns must match number of dates"
            )
        
        if len(request.portfolio_returns) < 30:
            raise HTTPException(
                status_code=400,
                detail="Need at least 30 return observations for regime analysis"
            )
        
        # Convert to pandas Series
        try:
            dates = pd.to_datetime(request.return_dates)
            returns = pd.Series(request.portfolio_returns, index=dates)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format in return_dates: {str(e)}"
            )
        
        # Parse date range if provided
        start_date = None
        end_date = None
        if request.start_date:
            try:
                start_date = pd.to_datetime(request.start_date)
            except:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
                
        if request.end_date:
            try:
                end_date = pd.to_datetime(request.end_date)
            except:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Perform regime-aware analysis
        analysis_result = regime_analyzer.analyze_performance_by_regime(
            returns, start_date, end_date
        )
        
        if not analysis_result:
            raise HTTPException(status_code=500, detail="Performance analysis failed")
        
        response = PerformanceAnalysisResponse(
            regime_performance=analysis_result.get('regime_performance', {}),
            regime_summary=analysis_result.get('regime_summary', {}),
            current_regime_forecast=analysis_result.get('current_regime_forecast', {}),
            strategy_recommendations=analysis_result.get('strategy_recommendations', [])
        )
        
        regime_count = len(analysis_result.get('regime_performance', {}))
        logger.info(f"Performance analysis complete for {regime_count} regimes")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in performance analysis: {str(e)}")
        raise HTTPException(status_code=500, 
                          detail=f"Performance analysis failed: {str(e)}")

@router.get("/indicators")
async def get_regime_indicators(
    lookback_days: int = Query(default=252, ge=30, le=1000,
                              description="Days to look back for indicator calculation")
):
    """
    Get current market regime indicators without full regime classification
    """
    try:
        # Get price data
        db_manager = DatabaseManager()
        # Get the latest available date from database instead of using current date
        latest_date_query = """
        SELECT MAX(date) FROM daily_prices 
        WHERE symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
        """
        latest_result = db_manager.execute_query(latest_date_query)
        if latest_result and latest_result[0][0]:
            end_date = pd.to_datetime(latest_result[0][0])
        else:
            end_date = datetime.now()  # Fallback
            
        start_date = end_date - timedelta(days=lookback_days + 365)  # Minimum 1 year + lookback for calculations
        
        query = """
        SELECT date, symbol, adj_close
        FROM daily_prices 
        WHERE date BETWEEN %s AND %s
        AND symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
        ORDER BY date, symbol
        """
        
        results = db_manager.execute_query(query, (start_date, end_date))
        
        if not results:
            raise HTTPException(status_code=404, detail="No price data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(results, columns=['date', 'symbol', 'price'])
        price_data = df.pivot(index='date', columns='symbol', values='price')
        price_data.index = pd.to_datetime(price_data.index)
        # Convert decimal to float and forward fill
        price_data = price_data.astype(float)
        price_data = price_data.ffill().dropna()
        
        # Calculate indicators
        from ..regime.regime_indicators import RegimeIndicatorCalculator
        calculator = RegimeIndicatorCalculator()
        
        indicators = calculator.calculate_all_indicators(price_data)
        
        if not indicators:
            raise HTTPException(status_code=500, detail="Failed to calculate indicators")
        
        # Clean NaN values for JSON serialization
        import math
        cleaned_indicators = {}
        for key, value in indicators.items():
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                cleaned_indicators[key] = None  # or 0.0 depending on preference
            else:
                cleaned_indicators[key] = value
        
        # Add interpretation
        regime_summary = calculator.get_regime_summary(cleaned_indicators)
        
        response = {
            'indicators': cleaned_indicators,
            'regime_summary': regime_summary,
            'calculation_date': datetime.now().isoformat(),
            'lookback_period': lookback_days
        }
        
        logger.info(f"Regime indicators calculated: {len(indicators)} indicators")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating regime indicators: {str(e)}")
        raise HTTPException(status_code=500, 
                          detail=f"Indicator calculation failed: {str(e)}")

@router.get("/regime-types")
async def get_regime_types():
    """
    Get information about all available market regime types
    """
    try:
        regime_info = {}
        
        for regime_type, details in regime_detector.regime_types.items():
            regime_info[regime_type] = {
                'name': details['name'],
                'description': details['description'],
                'characteristics': details['characteristics']
            }
        
        # Add regime adjustments info
        for regime_type in regime_info.keys():
            if regime_type in regime_analyzer.regime_adjustments:
                adjustments = regime_analyzer.regime_adjustments[regime_type]
                regime_info[regime_type]['adjustments'] = {
                    'equity_bias': adjustments.get('equity_bias', 0),
                    'volatility_target': adjustments.get('volatility_target', 0.15),
                    'rebalancing_frequency': adjustments.get('rebalancing_frequency', 'quarterly'),
                    'strategy_description': adjustments.get('description', '')
                }
        
        response = {
            'regime_types': regime_info,
            'total_regime_types': len(regime_info)
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting regime types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get regime types: {str(e)}")

@router.get("/health")
async def regime_health_check():
    """
    Health check endpoint for regime analysis services
    """
    try:
        # Test database connection
        db_manager = DatabaseManager()
        
        # Test query
        test_query = """
        SELECT COUNT(*) as count FROM daily_prices 
        WHERE symbol IN ('VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ')
        AND date >= %s
        """
        
        test_date = datetime.now() - timedelta(days=30)
        results = db_manager.execute_query(test_query, (test_date,))
        
        data_count = results[0][0] if results else 0
        
        health_status = {
            'status': 'healthy',
            'regime_detector': 'available',
            'regime_analyzer': 'available', 
            'database_connection': 'connected',
            'recent_data_points': data_count,
            'supported_assets': ['VTI', 'VTIAX', 'BND', 'VNQ', 'GLD', 'VWO', 'QQQ'],
            'regime_types_available': len(regime_detector.regime_types),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("Regime analysis health check passed")
        return health_status
        
    except Exception as e:
        logger.error(f"Regime analysis health check failed: {str(e)}")
        raise HTTPException(status_code=503, 
                          detail=f"Service unhealthy: {str(e)}")
