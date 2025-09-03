# Enhanced Claude Routes - AI Agent Integration
"""
🤖 AI Agent Integration API Routes
Replaces rule-based routing with Claude API tool-calling capabilities.

EVOLUTION: Rule-based RequestClassifier → AI Agent with intelligent orchestration
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import logging
import os
from datetime import datetime

from src.models.database import get_db
from src.core.portfolio_engine import PortfolioEngine
from src.core.optimization_engine import OptimizationEngine  
from src.ai.claude_advisor import ClaudePortfolioAdvisor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Claude AI Agent"])

# Request/Response Models (enhanced from existing)
class ConversationContext(BaseModel):
    sessionId: Optional[str] = None
    conversationHistory: Optional[list] = []
    userPreferences: Optional[dict] = {}
    lastRecommendation: Optional[dict] = None
    userProfile: Optional[dict] = {}
    messageAnalysis: Optional[dict] = {}

class ChatRequest(BaseModel):
    message: str = Field(..., description="Natural language portfolio request")
    user_context: Optional[ConversationContext] = Field(default=None, description="Conversation context and user preferences")
    agent_mode: str = Field(default="ai_agent", description="Processing mode: ai_agent or rule_based")

class ChatResponse(BaseModel):
    recommendation: str = Field(..., description="Natural language recommendation")
    allocation: dict = Field(..., description="Recommended portfolio allocation")
    expected_cagr: float = Field(..., description="Expected annual return")
    expected_volatility: float = Field(..., description="Expected volatility")
    max_drawdown: float = Field(..., description="Maximum historical drawdown")
    sharpe_ratio: float = Field(..., description="Risk-adjusted return ratio")
    risk_profile: str = Field(..., description="Detected risk profile")
    confidence_score: float = Field(..., description="Recommendation confidence (0-1)")
    
    # Enhanced fields for AI Agent
    processing_mode: str = Field(default="ai_agent", description="How request was processed")
    tool_calls_made: Optional[list] = Field(default=[], description="Analytics tools used")
    synthesis_quality: Optional[str] = Field(default="good", description="Response synthesis quality")
    response_time_ms: Optional[int] = Field(default=0, description="Processing time")

# Initialize AI Agent (with fallback to rule-based)
try:
    from src.ai.claude_ai_agent import ClaudeAIAgent
    ai_agent = ClaudeAIAgent()
    AGENT_AVAILABLE = True
    logger.info("AI Agent initialized successfully")
except Exception as e:
    logger.warning(f"AI Agent initialization failed, falling back to rule-based: {e}")
    AGENT_AVAILABLE = False
    
    # Keep existing RequestClassifier as fallback
    from src.api.claude_routes import RequestClassifier
    rule_based_classifier = RequestClassifier()

# Initialize engines with database session
def get_engines(db: Session = Depends(get_db)):
    portfolio_engine = PortfolioEngine(db)
    optimization_engine = OptimizationEngine()
    claude_advisor = ClaudePortfolioAdvisor(portfolio_engine, optimization_engine)
    return portfolio_engine, optimization_engine, claude_advisor

@router.post("/recommend", response_model=ChatResponse)
async def get_portfolio_recommendation(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    🚀 ENHANCED: AI Agent-powered portfolio recommendations
    
    NEW ARCHITECTURE:
    - AI Agent with Claude API tool-calling (primary)
    - Rule-based RequestClassifier (fallback)
    - Intelligent multi-tool orchestration
    - Comprehensive response synthesis
    
    CAPABILITIES:
    - Multi-API orchestration: "Is this safe for retirement?" → timeline + crisis + recovery
    - Context-aware recommendations with conversation memory
    - Intelligent tool selection based on question semantics
    - Synthesis of results from multiple analytics engines
    """
    start_time = datetime.now()
    processing_mode = "unknown"
    
    try:
        logger.info(f"Processing request: {request.message}")
        
        # Extract conversation context
        context = request.user_context.__dict__ if request.user_context else None
        
        # ENHANCED: AI Agent Processing (Primary Path)
        if AGENT_AVAILABLE and request.agent_mode == "ai_agent":
            try:
                processing_mode = "ai_agent"
                logger.info("Using AI Agent for request processing")
                
                # Process with AI Agent
                agent_response = await ai_agent.process_request(request.message, context)
                
                # Convert to API response format
                processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                return ChatResponse(
                    recommendation=agent_response.recommendation,
                    allocation=agent_response.allocation,
                    expected_cagr=agent_response.expected_cagr,
                    expected_volatility=agent_response.expected_volatility,
                    max_drawdown=agent_response.max_drawdown,
                    sharpe_ratio=agent_response.sharpe_ratio,
                    risk_profile=agent_response.risk_profile,
                    confidence_score=agent_response.confidence_score,
                    processing_mode=processing_mode,
                    tool_calls_made=agent_response.tool_calls_made,
                    synthesis_quality=agent_response.synthesis_quality,
                    response_time_ms=processing_time
                )
                
            except Exception as e:
                logger.error(f"AI Agent processing failed, falling back to rule-based: {e}")
                processing_mode = "fallback_rule_based"
        
        # FALLBACK: Rule-based Processing (Original System)
        if not AGENT_AVAILABLE or request.agent_mode == "rule_based" or processing_mode == "fallback_rule_based":
            logger.info("Using rule-based processing")
            processing_mode = "rule_based"
            
            # Use existing rule-based logic
            classification = rule_based_classifier.classify_request(
                request.message, 
                context
            )
            
            logger.info(f"Request classified as: {classification['request_type']}")
            
            # Handle analytical requests
            if classification['request_type'] != 'new_portfolio':
                response = await handle_analysis_request_legacy(classification, request, context)
            else:
                response = await handle_portfolio_recommendation_legacy(request, db)
            
            # Enhance response with processing metadata
            response.processing_mode = processing_mode
            response.tool_calls_made = [classification['request_type']]
            response.synthesis_quality = "legacy"
            response.response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return response
        
    except Exception as e:
        logger.error(f"All processing methods failed: {e}")
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Emergency fallback
        return ChatResponse(
            recommendation=f"❌ **Processing Error**: I encountered an issue analyzing your request: {str(e)}. Please try rephrasing your question or contact support if this persists.",
            allocation={"VTI": 0.40, "VTIAX": 0.20, "BND": 0.15, "VNQ": 0.10, "GLD": 0.05, "VWO": 0.07, "QQQ": 0.03},
            expected_cagr=0.10,
            expected_volatility=0.15,
            max_drawdown=-0.25,
            sharpe_ratio=0.65,
            risk_profile="balanced",
            confidence_score=0.30,
            processing_mode="emergency_fallback",
            tool_calls_made=[],
            synthesis_quality="poor",
            response_time_ms=processing_time
        )

# Legacy handlers for fallback (keeping existing functions)
async def handle_analysis_request_legacy(classification: dict, request: ChatRequest, context) -> ChatResponse:
    """Legacy analysis request handler (existing logic)"""
    try:
        # Create analysis request payload
        analysis_request = rule_based_classifier.create_analysis_request(
            classification, 
            request.message,
            context
        )
        
        # Make API call to analysis endpoint
        endpoint_url = f"{rule_based_classifier.api_base}{classification['endpoint']}"
        
        logger.info(f"Calling analysis endpoint: {endpoint_url}")
        
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint_url, json=analysis_request)
            
        if response.status_code != 200:
            logger.error(f"Analysis API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Analysis service unavailable")
        
        analysis_data = response.json()
        
        # Format response conversationally
        formatted_response = rule_based_classifier.format_analysis_response(
            classification, 
            analysis_data, 
            request.message
        )
        
        # Get allocation for response
        allocation = rule_based_classifier.get_default_allocation(
            context.get('lastRecommendation') if context else None
        )
        
        # Return in standard ChatResponse format
        return ChatResponse(
            recommendation=formatted_response,
            allocation=allocation,
            expected_cagr=context.get('lastRecommendation', {}).get('expected_cagr', 0.115) if context else 0.115,
            expected_volatility=context.get('lastRecommendation', {}).get('expected_volatility', 0.16) if context else 0.16,
            max_drawdown=context.get('lastRecommendation', {}).get('max_drawdown', -0.32) if context else -0.32,
            sharpe_ratio=context.get('lastRecommendation', {}).get('sharpe_ratio', 0.68) if context else 0.68,
            risk_profile=context.get('lastRecommendation', {}).get('risk_profile', 'balanced') if context else 'balanced',
            confidence_score=0.85
        )
        
    except Exception as e:
        logger.error(f"Legacy analysis request failed: {e}")
        raise

async def handle_portfolio_recommendation_legacy(request: ChatRequest, db: Session) -> ChatResponse:
    """Legacy portfolio recommendation handler (existing logic)"""
    # Get engines with proper database session
    portfolio_engine, optimization_engine, claude_advisor = get_engines(db)
    
    # Generate new portfolio recommendation
    recommendation = claude_advisor.generate_recommendation(request.message)
    
    if recommendation is None:
        logger.error("generate_recommendation returned None")
        raise HTTPException(status_code=500, detail="Failed to generate recommendation")
    
    # Format the response
    formatted_response = f"🎯 Portfolio Recommendation: {recommendation.risk_profile.value.title()} allocation with {recommendation.expected_cagr:.1%} expected returns."
    
    return ChatResponse(
        recommendation=formatted_response,
        allocation=recommendation.allocation,
        expected_cagr=recommendation.expected_cagr,
        expected_volatility=recommendation.expected_volatility,
        max_drawdown=recommendation.max_drawdown,
        sharpe_ratio=recommendation.sharpe_ratio,
        risk_profile=recommendation.risk_profile.value,
        confidence_score=recommendation.confidence_score
    )

# Health check endpoints for monitoring
@router.get("/agent-status")
async def get_agent_status():
    """Check AI Agent availability and system status"""
    status = {
        "ai_agent_available": AGENT_AVAILABLE,
        "fallback_available": True,
        "claude_api_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "recommended_mode": "ai_agent" if AGENT_AVAILABLE else "rule_based"
    }
    
    if AGENT_AVAILABLE:
        try:
            # Test agent responsiveness  
            test_response = await ai_agent._call_claude_with_tools(
                "Test message", 
                None
            )
            status["agent_responsive"] = True
        except:
            status["agent_responsive"] = False
    
    return status

# Configuration endpoint for switching modes
@router.post("/configure")
async def configure_agent(
    default_mode: str = "ai_agent",
    enable_fallback: bool = True
):
    """Configure AI Agent behavior"""
    
    if default_mode not in ["ai_agent", "rule_based"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    return {
        "status": "configured",
        "default_mode": default_mode,
        "fallback_enabled": enable_fallback,
        "agent_available": AGENT_AVAILABLE
    }
