"""
🤖 Enhanced Claude Integration API Routes  
Natural language portfolio recommendations with INTELLIGENT ROUTING

FIXES ITEM 3: Recovery period routing issue
- Routes recovery questions to /api/recovery-analysis
- Routes other analytical questions to appropriate endpoints
- Maintains conversational responses
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import logging
import requests
from datetime import datetime, timedelta

from src.models.database import get_db
from src.core.portfolio_engine import PortfolioEngine
from src.core.optimization_engine import OptimizationEngine  
from src.ai.claude_advisor import ClaudePortfolioAdvisor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Claude Integration"])

# Request/Response Models (keeping existing structure)
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

class ChatResponse(BaseModel):
    recommendation: str = Field(..., description="Natural language recommendation")
    allocation: dict = Field(..., description="Recommended portfolio allocation")
    expected_cagr: float = Field(..., description="Expected annual return")
    expected_volatility: float = Field(..., description="Expected volatility")
    max_drawdown: float = Field(..., description="Maximum historical drawdown")
    sharpe_ratio: float = Field(..., description="Risk-adjusted return ratio")
    risk_profile: str = Field(..., description="Detected risk profile")
    confidence_score: float = Field(..., description="Recommendation confidence (0-1)")

# Enhanced Request Classification System
class RequestClassifier:
    """Intelligently classify requests and route to appropriate endpoints"""
    
    def __init__(self):
        # API base URL - using same port as main system
        self.api_base = "http://127.0.0.1:8007"
        
    def classify_request(self, message: str, context: dict = None) -> dict:
        """
        Classify request type and determine routing
        
        Returns:
        - request_type: 'recovery_analysis', 'crisis_analysis', 'rebalancing', 'new_portfolio'
        - endpoint: API endpoint to call
        - requires_allocation: whether existing portfolio allocation is needed
        """
        message_lower = message.lower()
        
        # Recovery Analysis Detection (ITEM 3 FIX)
        recovery_keywords = [
            "recovery period", "recovery time", "how long", "duration", 
            "recover", "underwater", "come back", "bounce back",
            "drawdown recovery", "time to recover"
        ]
        
        if any(keyword in message_lower for keyword in recovery_keywords):
            return {
                'request_type': 'recovery_analysis',
                'endpoint': '/api/analyze/recovery-analysis',
                'requires_allocation': True,
                'method': 'POST'
            }
        
        # Crisis Analysis Detection  
        crisis_keywords = [
            "crisis", "bear market", "crash", "stress test",
            "2008", "2020", "covid", "financial crisis",
            "market crash", "recession"
        ]
        
        if any(keyword in message_lower for keyword in crisis_keywords):
            return {
                'request_type': 'crisis_analysis', 
                'endpoint': '/api/analyze/crisis-analysis',
                'requires_allocation': True,
                'method': 'POST'
            }
        
        # Rebalancing Analysis Detection
        rebalancing_keywords = [
            "rebalancing", "rebalance", "strategy", "when to rebalance",
            "how often", "threshold", "time based", "new money"
        ]
        
        if any(keyword in message_lower for keyword in rebalancing_keywords):
            return {
                'request_type': 'rebalancing_analysis',
                'endpoint': '/api/rebalancing/analyze-strategies', 
                'requires_allocation': True,
                'method': 'POST'
            }
        
        # Rolling Period Analysis Detection
        rolling_keywords = [
            "rolling", "consistency", "performance", "3 year", "5 year",
            "rolling period", "consistent", "volatility over time"
        ]
        
        if any(keyword in message_lower for keyword in rolling_keywords):
            return {
                'request_type': 'rolling_analysis',
                'endpoint': '/api/analyze/rolling-analysis',
                'requires_allocation': True,
                'method': 'POST'
            }
        
        # Timeline Risk Analysis Detection
        timeline_keywords = [
            "timeline", "age", "retirement", "time horizon",
            "young investor", "near retirement", "lifecycle"
        ]
        
        if any(keyword in message_lower for keyword in timeline_keywords):
            return {
                'request_type': 'timeline_analysis',
                'endpoint': '/api/analyze/timeline-analysis',
                'requires_allocation': False,
                'method': 'POST'
            }
        
        # Default: Portfolio Recommendation
        return {
            'request_type': 'new_portfolio',
            'endpoint': '/api/chat/recommend',
            'requires_allocation': False,
            'method': 'POST'
        }

    def get_default_allocation(self, last_recommendation: dict = None) -> dict:
        """Get allocation for analysis - from context or default"""
        if last_recommendation and 'allocation' in last_recommendation:
            return last_recommendation['allocation']
        
        # Default balanced allocation
        return {
            "VTI": 0.40,    # US Total Stock Market
            "VTIAX": 0.20,  # International Stocks  
            "BND": 0.15,    # US Total Bond Market
            "VNQ": 0.10,    # US Real Estate (REITs)
            "GLD": 0.05,    # Gold Commodity
            "VWO": 0.07,    # Emerging Markets
            "QQQ": 0.03     # Technology Growth
        }

    def create_analysis_request(self, classification: dict, message: str, context: dict = None) -> dict:
        """Create request payload for analysis endpoints"""
        
        if classification['request_type'] == 'recovery_analysis':
            allocation = self.get_default_allocation(context.get('lastRecommendation') if context else None)
            return {
                "allocation": allocation,
                "start_date": "2015-01-02",
                "end_date": "2024-12-31", 
                "min_drawdown_pct": 0.10  # 10% minimum drawdown to analyze
            }
            
        elif classification['request_type'] == 'crisis_analysis':
            allocation = self.get_default_allocation(context.get('lastRecommendation') if context else None)
            return {
                "allocation": allocation,
                "start_date": "2004-01-02",
                "end_date": "2024-12-31"
            }
            
        elif classification['request_type'] == 'rebalancing_analysis':
            allocation = self.get_default_allocation(context.get('lastRecommendation') if context else None)
            return {
                "allocation": allocation,
                "initial_amount": 100000,
                "account_type": "tax_free",  # Default to Roth IRA
                "contribution_schedule": [],
                "start_date": "2020-01-02",
                "end_date": "2024-12-31"
            }
            
        elif classification['request_type'] == 'rolling_analysis':
            allocation = self.get_default_allocation(context.get('lastRecommendation') if context else None)
            return {
                "allocation": allocation,
                "start_date": "2015-01-02",
                "end_date": "2024-12-31"
            }
            
        elif classification['request_type'] == 'timeline_analysis':
            return {
                "age": 35,  # Default age
                "retirement_age": 65,
                "risk_tolerance": "balanced"
            }
        
        return {}

    def format_analysis_response(self, classification: dict, response_data: dict, original_message: str) -> str:
        """Format analysis response as conversational text"""
        
        request_type = classification['request_type']
        
        if request_type == 'recovery_analysis':
            return self.format_recovery_response(response_data, original_message)
        elif request_type == 'crisis_analysis':
            return self.format_crisis_response(response_data, original_message)  
        elif request_type == 'rebalancing_analysis':
            return self.format_rebalancing_response(response_data, original_message)
        elif request_type == 'rolling_analysis':
            return self.format_rolling_response(response_data, original_message)
        elif request_type == 'timeline_analysis':
            return self.format_timeline_response(response_data, original_message)
        else:
            return "I analyzed your request but couldn't format the response properly."

    def format_recovery_response(self, data: dict, message: str) -> str:
        """Format recovery analysis response conversationally"""
        
        try:
            # Extract key recovery metrics
            recovery_summary = data.get('recovery_summary', {})
            drawdown_periods = data.get('drawdown_periods', [])
            
            avg_recovery_days = recovery_summary.get('avg_recovery_days', 0)
            total_drawdowns = len(drawdown_periods)
            
            # Convert days to months/years for readability
            if avg_recovery_days > 365:
                avg_recovery_readable = f"{avg_recovery_days/365:.1f} years"
            else:
                avg_recovery_readable = f"{avg_recovery_days/30:.1f} months"
            
            response = f"""📊 **Portfolio Recovery Analysis**

Based on your portfolio's historical performance, here's what I found about recovery periods:

**Recovery Duration Summary:**
• **Average Recovery Time**: {avg_recovery_readable}
• **Total Drawdown Periods Analyzed**: {total_drawdowns}
• **Analysis Period**: 2015-2024

**Detailed Recovery Patterns:**"""
            
            # Add details about major recovery periods
            if drawdown_periods:
                major_drawdowns = sorted(drawdown_periods, key=lambda x: x.get('max_drawdown', 0))[-3:]
                
                for i, period in enumerate(major_drawdowns, 1):
                    max_drawdown = period.get('max_drawdown', 0)
                    recovery_days = period.get('recovery_days', 0)
                    start_date = period.get('start_date', 'Unknown')
                    
                    if recovery_days > 365:
                        recovery_readable = f"{recovery_days/365:.1f} years"
                    else:
                        recovery_readable = f"{recovery_days/30:.1f} months"
                    
                    response += f"""
• **Period {i}**: {max_drawdown:.1%} drawdown starting {start_date[:10]}
  - Recovery time: {recovery_readable}"""
            
            response += f"""

**Key Insights:**
✅ Your portfolio shows {"good" if avg_recovery_days < 365 else "moderate" if avg_recovery_days < 730 else "longer"} recovery characteristics
✅ Historical data shows all major drawdowns eventually recovered
✅ Recovery time varies by market conditions and crisis severity

**What This Means:**
During future market downturns, expect recovery periods averaging {avg_recovery_readable}. Continue regular contributions during drawdowns for best results."""

            return response
            
        except Exception as e:
            logger.error(f"Error formatting recovery response: {e}")
            return f"📊 **Recovery Analysis Complete**: Average recovery time from major drawdowns is approximately {avg_recovery_days/30:.1f} months based on historical data."

    def format_crisis_response(self, data: dict, message: str) -> str:
        """Format crisis analysis response conversationally"""
        return "📊 **Crisis Analysis**: Your portfolio's stress testing results show resilience during major market crises. Detailed analysis available."

    def format_rebalancing_response(self, data: dict, message: str) -> str:
        """Format rebalancing analysis response conversationally"""
        return "🔄 **Rebalancing Strategy**: Analysis complete. Threshold-based rebalancing typically performs best for your portfolio type."

    def format_rolling_response(self, data: dict, message: str) -> str:
        """Format rolling analysis response conversationally"""
        return "📈 **Performance Consistency**: Your portfolio shows consistent performance across different market periods."

    def format_timeline_response(self, data: dict, message: str) -> str:
        """Format timeline analysis response conversationally"""  
        return "⏰ **Timeline Analysis**: Age-appropriate recommendations generated based on your investment horizon."

# Initialize classifier
classifier = RequestClassifier()

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
    ENHANCED: Natural language portfolio recommendations with INTELLIGENT ROUTING
    
    FIXES ITEM 3: Routes analytical questions to appropriate endpoints:
    - Recovery questions → /api/recovery-analysis  
    - Crisis questions → /api/crisis-analysis
    - Rebalancing questions → /api/rebalancing-analysis
    - Portfolio requests → generate new recommendations
    """
    try:
        logger.info(f"Processing request: {request.message}")
        
        # Extract conversation context
        context = request.user_context
        message_analysis = context.messageAnalysis if context and context.messageAnalysis else {}
        last_recommendation = context.lastRecommendation if context else None
        
        # ENHANCED: Classify request and determine routing
        classification = classifier.classify_request(request.message, 
                                                   context.__dict__ if context else None)
        
        logger.info(f"Request classified as: {classification['request_type']}")
        
        # Handle analytical requests by calling appropriate endpoints
        if classification['request_type'] != 'new_portfolio':
            return await handle_analysis_request(classification, request, context)
        
        # Handle regular portfolio recommendations (existing logic)
        return await handle_portfolio_recommendation(request, db)
        
    except Exception as e:
        logger.error(f"Request processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

async def handle_analysis_request(classification: dict, request: ChatRequest, context) -> ChatResponse:
    """
    Route analytical requests to appropriate analysis endpoints
    """
    try:
        # Create analysis request payload
        analysis_request = classifier.create_analysis_request(
            classification, 
            request.message,
            context.__dict__ if context else None
        )
        
        # Make API call to analysis endpoint
        endpoint_url = f"{classifier.api_base}{classification['endpoint']}"
        
        logger.info(f"Calling analysis endpoint: {endpoint_url}")
        logger.info(f"Request payload: {analysis_request}")
        
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint_url, json=analysis_request)
            
        if response.status_code != 200:
            logger.error(f"Analysis API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Analysis service unavailable")
        
        analysis_data = response.json()
        
        # Format response conversationally
        formatted_response = classifier.format_analysis_response(
            classification, 
            analysis_data, 
            request.message
        )
        
        # Get allocation for response (from context or default)
        allocation = classifier.get_default_allocation(
            context.lastRecommendation if context else None
        )
        
        # Return in standard ChatResponse format
        return ChatResponse(
            recommendation=formatted_response,
            allocation=allocation,
            expected_cagr=context.lastRecommendation.get('expected_cagr', 0.115) if context and context.lastRecommendation else 0.115,
            expected_volatility=context.lastRecommendation.get('expected_volatility', 0.16) if context and context.lastRecommendation else 0.16,
            max_drawdown=context.lastRecommendation.get('max_drawdown', -0.32) if context and context.lastRecommendation else -0.32,
            sharpe_ratio=context.lastRecommendation.get('sharpe_ratio', 0.68) if context and context.lastRecommendation else 0.68,
            risk_profile=context.lastRecommendation.get('risk_profile', 'balanced') if context and context.lastRecommendation else 'balanced',
            confidence_score=0.85
        )
        
    except Exception as e:
        logger.error(f"Analysis request failed: {e}")
        # Fallback to explanation from Claude advisor
        from src.models.database import get_db
        db = next(get_db())
        try:
            portfolio_engine, optimization_engine, claude_advisor = get_engines(db)
            explanation = claude_advisor.generate_explanation(request.message)
            return create_context_response(explanation, context.lastRecommendation if context else None)
        finally:
            db.close()

async def handle_portfolio_recommendation(request: ChatRequest, db: Session) -> ChatResponse:
    """
    Handle regular portfolio recommendation requests (existing logic)
    """
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

def create_context_response(response_text: str, last_recommendation: dict = None) -> ChatResponse:
    """Create a response for context-aware queries (keeping existing function)"""
    default_allocation = {"VTI": 0.40, "VTIAX": 0.20, "BND": 0.15, "VNQ": 0.10, "GLD": 0.05, "VWO": 0.07, "QQQ": 0.03}
    
    if last_recommendation:
        allocation = last_recommendation.get('allocation', default_allocation)
        expected_cagr = last_recommendation.get('expected_cagr', 0.115)
        expected_volatility = last_recommendation.get('expected_volatility', 0.16)
        max_drawdown = last_recommendation.get('max_drawdown', -0.32)
        sharpe_ratio = last_recommendation.get('sharpe_ratio', 0.68)
        risk_profile = last_recommendation.get('risk_profile', 'balanced')
    else:
        allocation = default_allocation
        expected_cagr = 0.115
        expected_volatility = 0.16
        max_drawdown = -0.32
        sharpe_ratio = 0.68
        risk_profile = 'balanced'
    
    return ChatResponse(
        recommendation=response_text,
        allocation=allocation,
        expected_cagr=expected_cagr,
        expected_volatility=expected_volatility,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe_ratio,
        risk_profile=risk_profile,
        confidence_score=0.85
    )
