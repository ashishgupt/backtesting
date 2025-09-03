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
from src.api.optimization_routes_v2 import router as optimization_v2_router
from src.api.claude_routes import router as claude_router
from src.api.analysis_routes import router as analysis_router
from src.api.rebalancing_routes import router as rebalancing_router
from src.api.enhanced_optimization_routes import router as enhanced_optimization_router
from src.api.walk_forward_routes import router as walk_forward_router
from src.api.regime_routes import router as regime_router

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
app.include_router(optimization_v2_router)
app.include_router(enhanced_optimization_router)
app.include_router(walk_forward_router)
app.include_router(claude_router)
app.include_router(analysis_router)
app.include_router(rebalancing_router)
app.include_router(regime_router)

# Add direct route alias for frontend compatibility
from src.api.optimization_routes_v2 import optimize_portfolio as optimize_portfolio_v2
from src.api.optimization_routes_v2 import OptimizationRequestAPI

@app.post("/optimize")
async def optimize_portfolio_alias(request: OptimizationRequestAPI, db: Session = Depends(get_db)):
    """Direct alias for /api/portfolio/optimize for frontend compatibility"""
    return await optimize_portfolio_v2(request, db)

# Mount static files for web UI
app.mount("/static", StaticFiles(directory="web"), name="static")

@app.get("/chat")
async def serve_chat_ui():
    """Serve the Claude portfolio chat UI"""
    return FileResponse("web/index.html")

@app.get("/portfolio-optimizer-enhanced.html")
async def serve_enhanced_optimizer():
    """Serve the enhanced portfolio optimizer UI"""
    return FileResponse("web/portfolio-optimizer-enhanced.html")

@app.get("/portfolio-optimizer.html")
async def serve_basic_optimizer():
    """Serve the basic portfolio optimizer UI"""
    return FileResponse("web/portfolio-optimizer.html")

@app.get("/dashboard.html")
async def serve_dashboard():
    """Serve the dashboard UI"""
    return FileResponse("web/dashboard.html")

@app.get("/api_pie_test.html")
async def serve_api_pie_test():
    """Serve the API pie chart test UI"""
    return FileResponse("web/api_pie_test.html")

@app.get("/portfolio-optimizer-simple.html")
async def serve_simple_optimizer():
    """Serve the simple portfolio optimizer with working pie charts"""
    return FileResponse("web/portfolio-optimizer-simple.html")

@app.get("/chartjs_test.html")
async def serve_chartjs_test():
    """Serve the Chart.js test page"""
    return FileResponse("web/chartjs_test.html")

@app.get("/pie_chart_test.html")
async def serve_pie_chart_test():
    """Serve the pie chart test with hardcoded data"""
    return FileResponse("web/pie_chart_test.html")

@app.get("/cdn_test.html")
async def serve_cdn_test():
    """Serve the CDN Chart.js test"""
    return FileResponse("web/cdn_test.html")

@app.get("/rebalancing-analyzer.html")
async def serve_rebalancing_analyzer():
    """Serve the rebalancing strategy analyzer UI"""
    return FileResponse("web/rebalancing-analyzer.html")

@app.get("/walk-forward-analyzer.html")
async def serve_walk_forward_analyzer():
    """Serve the walk-forward validation analyzer UI"""
    return FileResponse("web/walk-forward-analyzer.html")

@app.get("/regime-analyzer.html")
async def serve_regime_analyzer():
    """Serve the market regime analyzer UI"""
    return FileResponse("web/regime-analyzer.html")

@app.get("/guided-dashboard.html")
async def serve_guided_dashboard():
    """Serve the guided portfolio analysis dashboard UI"""
    return FileResponse("web/guided-dashboard.html")



# Database dependency - removed since it's now imported from database.py

@app.get("/")
async def serve_index():
    """Serve the main index page"""
    return FileResponse("web/index.html")

@app.get("/index.html")
async def serve_index_html():
    """Serve the main index page with .html extension"""
    return FileResponse("web/index.html")

@app.get("/api/health")
async def api_health():
    """API health check endpoint"""
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
    import os
    port = int(os.getenv("PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)