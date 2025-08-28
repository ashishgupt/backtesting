"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import datetime
from decimal import Decimal

class PortfolioAllocation(BaseModel):
    """Portfolio allocation model with validation for 3-asset and 7-asset portfolios"""
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
            raise ValueError(f"Allocation weights must sum to 1.0, got {total:.6f}")
            
        # Check for negative weights
        if any(weight < 0 for weight in v.values()):
            raise ValueError("Allocation weights cannot be negative")
            
        # Validate asset symbols - support both 3-asset and 7-asset portfolios
        valid_symbols = {
            # Original 3-asset universe
            'VTI', 'VTIAX', 'BND',
            # Expanded 4 new assets  
            'VNQ', 'GLD', 'VWO', 'QQQ'
        }
        
        provided_symbols = set(v.keys())
        invalid_symbols = provided_symbols - valid_symbols
        
        if invalid_symbols:
            raise ValueError(f"Invalid asset symbols: {invalid_symbols}. Valid symbols: {sorted(valid_symbols)}")
        
        # Allow 3-asset (legacy) or 7-asset allocations, but enforce minimum diversity
        if len(provided_symbols) < 2:
            raise ValueError("Portfolio must contain at least 2 assets for diversification")
            
        return v


class SevenAssetPortfolioAllocation(BaseModel):
    """Specialized 7-asset portfolio allocation with enhanced examples"""
    allocation: Dict[str, float] = Field(
        ...,
        description="7-asset allocation weights with full diversification",
        example={
            "VTI": 0.40,    # US Total Market - 40%
            "VTIAX": 0.20,  # International - 20%  
            "BND": 0.15,    # Bonds - 15%
            "VNQ": 0.10,    # REITs - 10%
            "GLD": 0.05,    # Gold - 5%
            "VWO": 0.05,    # Emerging Markets - 5%
            "QQQ": 0.05     # Tech Growth - 5%
        }
    )
    
    @validator('allocation')
    def validate_7_asset_allocation(cls, v):
        # Reuse the same validation as PortfolioAllocation
        return PortfolioAllocation.validate_allocation(v)
        
    def get_asset_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Return detailed asset class breakdown"""
        asset_info = {
            'VTI': {'name': 'US Total Market', 'class': 'US_EQUITY', 'weight': self.allocation.get('VTI', 0)},
            'VTIAX': {'name': 'International Developed', 'class': 'INTL_EQUITY', 'weight': self.allocation.get('VTIAX', 0)},
            'BND': {'name': 'US Bonds', 'class': 'US_BONDS', 'weight': self.allocation.get('BND', 0)},
            'VNQ': {'name': 'Real Estate', 'class': 'REIT', 'weight': self.allocation.get('VNQ', 0)},
            'GLD': {'name': 'Gold', 'class': 'COMMODITY', 'weight': self.allocation.get('GLD', 0)},
            'VWO': {'name': 'Emerging Markets', 'class': 'EMERGING_MARKETS', 'weight': self.allocation.get('VWO', 0)},
            'QQQ': {'name': 'Technology Growth', 'class': 'LARGE_CAP_GROWTH', 'weight': self.allocation.get('QQQ', 0)}
        }
        return {k: v for k, v in asset_info.items() if v['weight'] > 0}

class BacktestRequest(BaseModel):
    """Backtest request parameters with support for 7-asset portfolios and 20-year history"""
    allocation: PortfolioAllocation
    initial_value: float = Field(10000.0, gt=0, description="Initial portfolio value in USD")
    start_date: str = Field("2015-01-02", description="Backtest start date (YYYY-MM-DD). Can go back to 2004-01-01 for 20-year analysis")
    end_date: str = Field("2024-12-31", description="Backtest end date (YYYY-MM-DD)")
    rebalance_frequency: str = Field("monthly", description="Rebalancing frequency")
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        try:
            datetime.datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}")
        return v
    
    @validator('rebalance_frequency')
    def validate_rebalance_frequency(cls, v):
        valid_frequencies = ['daily', 'monthly', 'quarterly', 'annually']
        if v not in valid_frequencies:
            raise ValueError(f"Invalid rebalance frequency. Must be one of: {valid_frequencies}")
        return v


class SevenAssetBacktestRequest(BaseModel):
    """Specialized backtest request for 7-asset portfolios with enhanced defaults"""
    allocation: SevenAssetPortfolioAllocation
    initial_value: float = Field(100000.0, gt=0, description="Initial portfolio value (default: $100k for 7-asset portfolios)")
    start_date: str = Field("2004-01-01", description="Start date - 20 years for comprehensive analysis")
    end_date: str = Field("2024-12-31", description="End date")
    rebalance_frequency: str = Field("quarterly", description="Quarterly rebalancing for tax efficiency")
    
    @validator('start_date', 'end_date')
    def validate_dates(cls, v):
        try:
            datetime.datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}")
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