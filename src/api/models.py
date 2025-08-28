"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import datetime
from decimal import Decimal

class PortfolioAllocation(BaseModel):
    """Portfolio allocation model with validation"""
    allocation: Dict[str, float] = Field(
        ..., 
        description="Asset allocation weights (symbol -> weight)",
        example={"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1}
    )
    
    @validator('allocation')
    def validate_allocation(cls, v):
        if not v:
            raise ValueError("Allocation cannot be empty")
            
        # Check if weights sum to 1.0 (with small tolerance for floating point)
        total = sum(v.values())
        if abs(total - 1.0) > 0.0001:
            raise ValueError(f"Allocation weights must sum to 1.0, got {total}")
            
        # Check for negative weights
        if any(weight < 0 for weight in v.values()):
            raise ValueError("Allocation weights cannot be negative")
            
        # Check for valid asset symbols (basic validation)
        valid_symbols = {'VTI', 'VTIAX', 'BND'}
        invalid_symbols = set(v.keys()) - valid_symbols
        if invalid_symbols:
            raise ValueError(f"Invalid asset symbols: {invalid_symbols}")
            
        return v

class BacktestRequest(BaseModel):
    """Backtest request parameters"""
    allocation: PortfolioAllocation
    initial_value: float = Field(10000.0, gt=0, description="Initial portfolio value in USD")
    start_date: str = Field("2015-01-02", description="Backtest start date (YYYY-MM-DD)")
    end_date: str = Field("2024-12-31", description="Backtest end date (YYYY-MM-DD)")
    rebalance_frequency: str = Field("monthly", description="Rebalancing frequency")
    
    @validator('rebalance_frequency')
    def validate_rebalance_frequency(cls, v):
        valid_frequencies = ['daily', 'monthly', 'quarterly', 'annually']
        if v not in valid_frequencies:
            raise ValueError(f"Invalid rebalance frequency. Must be one of: {valid_frequencies}")
        return v

class PerformanceMetrics(BaseModel):
    """Portfolio performance metrics"""
    total_return: float = Field(..., description="Total return as decimal (e.g., 1.5 = 150%)")
    cagr: float = Field(..., description="Compound Annual Growth Rate as decimal")
    volatility: float = Field(..., description="Annualized volatility as decimal")
    max_drawdown: float = Field(..., description="Maximum drawdown as decimal (negative)")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    win_rate: float = Field(..., description="Win rate as decimal (e.g., 0.65 = 65%)")
    total_trading_days: int = Field(..., description="Total number of trading days")

class BacktestResponse(BaseModel):
    """Backtest response with results"""
    success: bool = Field(True, description="Whether backtest completed successfully")
    allocation: Dict[str, float] = Field(..., description="Portfolio allocation used")
    initial_value: float = Field(..., description="Initial portfolio value")
    final_value: float = Field(..., description="Final portfolio value")
    performance_metrics: PerformanceMetrics = Field(..., description="Portfolio performance metrics")
    calculation_time_seconds: Optional[float] = Field(None, description="Time taken to calculate")
    cache_hit: bool = Field(False, description="Whether result was retrieved from cache")

class AssetInfo(BaseModel):
    """Asset information model"""
    symbol: str = Field(..., description="Asset ticker symbol")
    name: str = Field(..., description="Asset name")
    asset_class: str = Field(..., description="Asset class (equity, bond, etc.)")
    expense_ratio: Optional[float] = Field(None, description="Expense ratio as decimal")

class AssetListResponse(BaseModel):
    """Response model for asset list"""
    assets: List[AssetInfo] = Field(..., description="List of available assets")
    count: int = Field(..., description="Number of assets")

class PriceData(BaseModel):
    """Price data point"""
    date: datetime.date = Field(..., description="Price date")
    symbol: str = Field(..., description="Asset symbol")
    adj_close: float = Field(..., description="Adjusted closing price")
    volume: Optional[int] = Field(None, description="Trading volume")
    dividend: Optional[float] = Field(None, description="Dividend amount")

class PriceDataResponse(BaseModel):
    """Response model for price data"""
    symbol: str = Field(..., description="Asset symbol")
    data: List[PriceData] = Field(..., description="Price data points")
    count: int = Field(..., description="Number of data points")
    date_range: Dict[str, str] = Field(..., description="Date range of data")

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    detail: Optional[str] = Field(None, description="Additional error details")

class DataStatusResponse(BaseModel):
    """Data status response"""
    status: str = Field(..., description="Overall data status")
    total_records: int = Field(..., description="Total price records in database")
    assets_count: int = Field(..., description="Number of assets with data")
    latest_date: Optional[str] = Field(None, description="Latest price date")
    oldest_date: Optional[str] = Field(None, description="Oldest price date")