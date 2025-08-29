"""
FastAPI application for Portfolio Backtesting PoC
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any
import os

from src.models.database import SessionLocal, engine, get_db
from src.models import schemas
from src.core.portfolio_engine_optimized import OptimizedPortfolioEngine as PortfolioEngine
from src.core.data_manager import DataManager
from src.api.backtesting import router as backtesting_router
from src.api.data_routes import router as data_router
from src.api.optimization_routes import router as optimization_router
from src.api.claude_routes import router as claude_router
from src.api.analysis_routes import router as analysis_router
from src.api.rebalancing_routes import rebalancing_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Portfolio Backtesting API",
    description="AI-powered portfolio optimization and backtesting system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(backtesting_router)
app.include_router(data_router)
app.include_router(optimization_router)
app.include_router(claude_router)
app.include_router(analysis_router)
app.include_router(rebalancing_router)

# Mount static files for web UI
app.mount("/static", StaticFiles(directory="web"), name="static")

@app.get("/chat")
async def serve_chat_ui():
    """Serve the Claude portfolio chat UI"""
    return FileResponse("web/index.html")

# Database dependency - removed since it's now imported from database.py

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Portfolio Backtesting API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check including database connectivity"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
        
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "timestamp": "2025-08-27T00:00:00Z"  # In production, use actual timestamp
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)