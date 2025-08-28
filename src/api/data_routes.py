"""
Data management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from typing import List

from src.models.database import get_db
from src.models.schemas import Asset, DailyPrice
from src.core.data_manager import DataManager
from src.api.models import (
    AssetListResponse, AssetInfo, PriceDataResponse, PriceData, DataStatusResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/data", tags=["data"])

@router.get("/assets", response_model=AssetListResponse)
async def list_assets(db: Session = Depends(get_db)):
    """
    Get list of all available assets for backtesting
    """
    try:
        assets = db.query(Asset).all()
        
        asset_list = [
            AssetInfo(
                symbol=asset.symbol,
                name=asset.name,
                asset_class=asset.asset_class,
                expense_ratio=float(asset.expense_ratio) if asset.expense_ratio else None
            )
            for asset in assets
        ]
        
        return AssetListResponse(
            assets=asset_list,
            count=len(asset_list)
        )
        
    except Exception as e:
        logger.error(f"Error fetching assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch asset list"
        )

@router.get("/assets/{symbol}/info", response_model=AssetInfo)
async def get_asset_info(symbol: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific asset
    """
    try:
        asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {symbol} not found"
            )
            
        return AssetInfo(
            symbol=asset.symbol,
            name=asset.name,
            asset_class=asset.asset_class,
            expense_ratio=float(asset.expense_ratio) if asset.expense_ratio else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching asset info for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch asset information"
        )@router.get("/prices/{symbol}", response_model=PriceDataResponse)
async def get_price_data(
    symbol: str, 
    start_date: str = "2015-01-01",
    end_date: str = "2024-12-31",
    db: Session = Depends(get_db)
):
    """
    Get historical price data for a specific asset
    """
    try:
        # Query price data
        prices = db.query(DailyPrice).filter(
            DailyPrice.symbol == symbol.upper(),
            DailyPrice.date >= start_date,
            DailyPrice.date <= end_date
        ).order_by(DailyPrice.date).all()
        
        if not prices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No price data found for {symbol}"
            )
            
        price_list = [
            PriceData(
                date=price.date,
                symbol=price.symbol,
                adj_close=float(price.adj_close),
                volume=price.volume,
                dividend=float(price.dividend) if price.dividend else None
            )
            for price in prices
        ]
        
        return PriceDataResponse(
            symbol=symbol.upper(),
            data=price_list,
            count=len(price_list),
            date_range={
                "start": str(prices[0].date),
                "end": str(prices[-1].date)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch price data"
        )

@router.post("/refresh")
async def refresh_data(db: Session = Depends(get_db)):
    """
    Refresh all historical price data from Yahoo Finance
    """
    try:
        logger.info("Starting data refresh")
        data_manager = DataManager(db)
        
        # Refresh data for all assets
        result = data_manager.refresh_all_data()
        
        logger.info("Data refresh completed successfully")
        return {
            "success": True,
            "message": "Data refresh completed",
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Error during data refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh data"
        )

@router.get("/status", response_model=DataStatusResponse)
async def get_data_status(db: Session = Depends(get_db)):
    """
    Get current data status and statistics
    """
    try:
        # Get total records count
        total_records = db.query(DailyPrice).count()
        
        # Get assets count
        assets_count = db.query(Asset).count()
        
        # Get date range
        date_range = db.execute(text("""
            SELECT MIN(date) as oldest_date, MAX(date) as latest_date 
            FROM daily_prices
        """)).fetchone()
        
        oldest_date = str(date_range.oldest_date) if date_range.oldest_date else None
        latest_date = str(date_range.latest_date) if date_range.latest_date else None
        
        # Determine status
        status = "healthy" if total_records > 0 else "no_data"
        
        return DataStatusResponse(
            status=status,
            total_records=total_records,
            assets_count=assets_count,
            latest_date=latest_date,
            oldest_date=oldest_date
        )
        
    except Exception as e:
        logger.error(f"Error getting data status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get data status"
        )