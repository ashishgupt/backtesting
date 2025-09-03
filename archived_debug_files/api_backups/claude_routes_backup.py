"""
🤖 Claude Integration API Routes
Natural language portfolio recommendations
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import logging

from src.models.database import get_db
from src.core.portfolio_engine import PortfolioEngine
from src.core.optimization_engine import OptimizationEngine
from src.ai.claude_advisor import ClaudePortfolioAdvisor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Claude Integration"])

# Request/Response Models
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

class PortfolioAnalysisRequest(BaseModel):
    allocation: dict = Field(..., description="Portfolio allocation to analyze")
    question: str = Field(..., description="Question about the portfolio")

class AnalysisResponse(BaseModel):
    analysis: str = Field(..., description="Natural language analysis")
    key_insights: list = Field(..., description="Key insights about the portfolio")
    suggestions: list = Field(..., description="Improvement suggestions")

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
    Get natural language portfolio recommendation or analysis based on user message
    
    Enhanced to handle:
    - Conversation context and follow-up questions
    - Portfolio recommendations with memory of previous interactions  
    - Rebalancing strategy questions  
    - Recovery/drawdown analysis
    - Context-aware responses
    
    Examples of supported queries:
    - "I'm 35 and want a balanced portfolio for retirement"
    - "What's the best rebalancing strategy for my Roth IRA?"
    - "How long would recovery take if this portfolio dropped 30%?"
    - "What about if I increase bonds in that portfolio?" (follow-up)
    - "Explain why you recommended that allocation" (context-aware)
    """
    try:
        logger.info(f"Processing recommendation request: {request.message}")
        logger.info(f"Raw user_context: {request.user_context}")
        
        # Extract conversation context
        context = request.user_context
        message_analysis = context.messageAnalysis if context and context.messageAnalysis else {}
        user_preferences = context.userPreferences if context else {}
        last_recommendation = context.lastRecommendation if context else None
        conversation_history = context.conversationHistory if context else []
        
        logger.info(f"Extracted message_analysis: {message_analysis}")
        logger.info(f"Context: {len(conversation_history)} messages, follow-up: {message_analysis.get('isFollowUp', False)}")
        
        # Get engines with proper database session
        portfolio_engine, optimization_engine, claude_advisor = get_engines(db)
        
        # Enhanced context-aware processing
        user_message = request.message.lower()
        
        # Check for follow-up questions that reference previous recommendations
        is_followup = message_analysis.get('isFollowUp', False)
        logger.info(f"Is follow-up: {is_followup}")
        
        if is_followup and last_recommendation:
            logger.info("Processing as follow-up question")
            # Handle follow-up questions with context from previous recommendation
            if any(word in user_message for word in ["explain", "why", "how", "tell me"]):
                explanation = claude_advisor.generate_explanation(
                    request.message, 
                    previous_context=last_recommendation
                )
                return create_context_response(explanation, last_recommendation)
            
            elif any(word in user_message for word in ["modify", "adjust", "change", "different", "instead", "what about"]):
                # Handle modification requests
                modified_recommendation = claude_advisor.generate_modified_recommendation(
                    request.message,
                    base_recommendation=last_recommendation,
                    user_preferences=user_preferences
                )
                return modified_recommendation
        
        # Handle different types of requests based on analysis
        request_type = message_analysis.get('requestType', 'new_portfolio')
        logger.info(f"Request type: {request_type}")
        
        if request_type == 'rebalancing':
            logger.info("Processing as rebalancing request")
            rebalancing_response = claude_advisor.generate_rebalancing_recommendation(
                request.message, 
                portfolio_allocation=last_recommendation.get('allocation') if last_recommendation else None
            )
            return create_context_response(rebalancing_response, last_recommendation)
            
        elif request_type == 'recovery_analysis':
            logger.info("Processing as recovery analysis request") 
            recovery_response = claude_advisor.generate_explanation(request.message, last_recommendation)
            return create_context_response(recovery_response, last_recommendation)
        
        elif request_type == 'risk_analysis':
            logger.info("Processing as risk analysis request")
            risk_response = claude_advisor.generate_risk_analysis(
                request.message,
                user_context=user_preferences,
                previous_allocation=last_recommendation.get('allocation') if last_recommendation else None
            )
            return create_context_response(risk_response, last_recommendation)
        
        else:
            logger.info("Processing as new portfolio recommendation request")
            # Generate new portfolio recommendation with conversation context
            try:
                enhanced_message = enrich_message_with_context(
                    request.message, 
                    user_preferences, 
                    conversation_history
                )
                
                logger.info(f"Enhanced message: {enhanced_message}")
                recommendation = claude_advisor.generate_recommendation(enhanced_message)
                logger.info(f"Generated recommendation type: {type(recommendation)}")
                logger.info(f"Generated recommendation: {recommendation}")
                
                if recommendation is None:
                    logger.error("generate_recommendation returned None")
                    return create_context_response("Sorry, I couldn't generate a recommendation at this time. Please try again.", last_recommendation)
                
                # DEBUG: Use a simple formatted response instead of the complex method
                try:
                    simple_formatted_response = f"🎯 Portfolio Recommendation: {recommendation.risk_profile.value.title()} allocation with {recommendation.expected_cagr:.1%} expected returns."
                    logger.info(f"Formatted response: {simple_formatted_response}")
                except Exception as e:
                    logger.error(f"Error formatting response: {e}")
                    simple_formatted_response = "Portfolio recommendation generated successfully."
                logger.error(f"Error formatting response: {e}")
                simple_formatted_response = "Portfolio recommendation generated successfully."
                
                return ChatResponse(
                    recommendation=simple_formatted_response,
                    allocation=recommendation.allocation,
                    expected_cagr=recommendation.expected_cagr,
                    expected_volatility=recommendation.expected_volatility,
                    max_drawdown=recommendation.max_drawdown,
                    sharpe_ratio=recommendation.sharpe_ratio,
                    risk_profile=recommendation.risk_profile.value,
                    confidence_score=recommendation.confidence_score
                )
            except Exception as inner_e:
                logger.error(f"Error in recommendation generation block: {inner_e}")
                return create_context_response("Sorry, I encountered an error generating your recommendation. Please try again.", last_recommendation)
        
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")

def create_context_response(response_text: str, last_recommendation: dict = None) -> ChatResponse:
    """Create a response for context-aware queries"""
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

def enrich_message_with_context(message: str, user_preferences: dict, conversation_history: list) -> str:
    """Enrich the user message with context from previous conversations"""
    enriched_parts = [message]
    
    # Add user preferences context if available
    if user_preferences:
        if 'riskProfile' in user_preferences:
            enriched_parts.append(f"User prefers {user_preferences['riskProfile']} risk profile.")
        if 'accountType' in user_preferences:
            enriched_parts.append(f"Account type: {user_preferences['accountType']}.")
        if 'timeline' in user_preferences:
            enriched_parts.append(f"Investment timeline: {user_preferences['timeline']}.")
    
    # Add conversation context for continuity
    if conversation_history:
        recent_messages = conversation_history[-3:]  # Last 3 messages for context
        context_summary = "Previous discussion context: "
        for msg in recent_messages:
            if msg.get('role') == 'user':
                context_summary += f"User asked: {msg.get('content', '')[:50]}... "
    
    return " ".join(enriched_parts)

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_portfolio(
    request: PortfolioAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze existing portfolio and answer questions about it
    
    Examples:
    - "How risky is this portfolio?"
    - "What's the expected return?"  
    - "How does this compare to a balanced portfolio?"
    """
    try:
        logger.info(f"Analyzing portfolio: {request.allocation}")
        
        # Get engines with proper database session
        portfolio_engine, optimization_engine, claude_advisor = get_engines(db)
        
        # Run backtesting on the provided allocation
        backtest_result = portfolio_engine.backtest_portfolio(
            allocation=request.allocation,
            start_date="2015-01-02",
            end_date="2024-12-31", 
            initial_value=10000,
            rebalance_frequency="monthly"
        )
        
        metrics = backtest_result["performance_metrics"]
        
        # Generate analysis based on the question
        analysis = generate_portfolio_analysis(request.allocation, metrics, request.question)
        key_insights = extract_key_insights(metrics, request.allocation)
        suggestions = generate_improvement_suggestions(request.allocation, metrics)
        
        return AnalysisResponse(
            analysis=analysis,
            key_insights=key_insights,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Portfolio analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/examples")
async def get_example_queries():
    """Get example queries that users can ask"""
    return {
        "recommendation_examples": [
            "I'm 25 and want an aggressive growth portfolio",
            "Conservative allocation for someone near retirement",
            "Balanced portfolio with international diversification",
            "I have $100,000 to invest for 30 years",
            "Low-risk portfolio with steady income"
        ],
        "analysis_examples": [
            "How risky is my current portfolio?",
            "What returns should I expect?",
            "Is this portfolio too conservative?",
            "How does this compare to the S&P 500?",
            "What's my downside risk?"
        ]
    }

def generate_portfolio_analysis(allocation: dict, metrics: dict, question: str) -> str:
    """Generate natural language analysis of portfolio"""
    
    question_lower = question.lower()
    
    # Determine portfolio characteristics
    stock_allocation = allocation.get("VTI", 0) + allocation.get("VTIAX", 0)
    bond_allocation = allocation.get("BND", 0)
    international_allocation = allocation.get("VTIAX", 0)
    
    if "risk" in question_lower:
        risk_level = "low" if bond_allocation > 0.5 else "high" if stock_allocation > 0.8 else "moderate"
        analysis = f"""This portfolio has {risk_level} risk characteristics. 
        
        With {stock_allocation:.0%} in stocks and {bond_allocation:.0%} in bonds, the portfolio shows:
        • Historical volatility of {metrics['volatility']:.1%}
        • Maximum drawdown of {metrics['max_drawdown']:.1%} (worst historical loss)
        • Sharpe ratio of {metrics['sharpe_ratio']:.2f} (risk-adjusted returns)
        
        The {risk_level} risk profile aligns with the {stock_allocation:.0%} stock allocation."""
        
    elif "return" in question_lower or "performance" in question_lower:
        analysis = f"""Expected performance based on historical data (2015-2024):
        
        • Annual Returns: {metrics['cagr']:.1%}
        • Total Return: {metrics['total_return']:.1%} over 10 years
        • Risk-Adjusted Returns: {metrics['sharpe_ratio']:.2f} Sharpe ratio
        
        This {stock_allocation:.0%} stock / {bond_allocation:.0%} bond allocation delivered solid returns 
        with {metrics['volatility']:.1%} annual volatility."""
        
    elif "compare" in question_lower:
        analysis = f"""Portfolio comparison insights:
        
        Your allocation ({stock_allocation:.0%} stocks, {bond_allocation:.0%} bonds):
        • CAGR: {metrics['cagr']:.1%}
        • Max Drawdown: {metrics['max_drawdown']:.1%}
        • Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
        
        This is more {'conservative' if bond_allocation > 0.3 else 'aggressive'} than a typical 60/40 portfolio."""
        
    else:
        # General analysis
        analysis = f"""Portfolio Overview:
        
        Asset Allocation:
        • US Stocks (VTI): {allocation.get('VTI', 0):.0%}
        • International Stocks (VTIAX): {allocation.get('VTIAX', 0):.0%}  
        • Bonds (BND): {allocation.get('BND', 0):.0%}
        
        Historical Performance (2015-2024):
        • Annual Returns: {metrics['cagr']:.1%}
        • Volatility: {metrics['volatility']:.1%}
        • Maximum Loss: {metrics['max_drawdown']:.1%}
        • Risk-Adjusted Returns: {metrics['sharpe_ratio']:.2f}"""
    
    return analysis

def extract_key_insights(metrics: dict, allocation: dict) -> list:
    """Extract key insights about the portfolio"""
    insights = []
    
    stock_allocation = allocation.get("VTI", 0) + allocation.get("VTIAX", 0)
    bond_allocation = allocation.get("BND", 0)
    international_allocation = allocation.get("VTIAX", 0)
    
    # Risk insights
    if metrics["max_drawdown"] < -0.30:
        insights.append("High drawdown risk - portfolio could lose 30%+ in market downturns")
    elif metrics["max_drawdown"] > -0.15:
        insights.append("Lower drawdown risk - conservative allocation limits major losses")
        
    # Return insights  
    if metrics["cagr"] > 0.12:
        insights.append("Strong historical returns - above typical market performance")
    elif metrics["cagr"] < 0.08:
        insights.append("Conservative returns - prioritizes stability over growth")
        
    # Allocation insights
    if international_allocation > 0.25:
        insights.append("Good international diversification reduces US market dependence")
    elif international_allocation < 0.1:
        insights.append("Heavy US focus - consider international diversification")
        
    if bond_allocation > 0.4:
        insights.append("Bond-heavy allocation provides stability but limits growth potential")
    elif bond_allocation < 0.1 and stock_allocation > 0.8:
        insights.append("Aggressive stock allocation - suitable for long-term growth")
        
    return insights

def generate_improvement_suggestions(allocation: dict, metrics: dict) -> list:
    """Generate improvement suggestions for the portfolio"""
    suggestions = []
    
    stock_allocation = allocation.get("VTI", 0) + allocation.get("VTIAX", 0)
    bond_allocation = allocation.get("BND", 0)
    international_allocation = allocation.get("VTIAX", 0)
    
    # Diversification suggestions
    if international_allocation < 0.15:
        suggestions.append("Consider increasing international exposure (VTIAX) to 20-30% for better diversification")
        
    # Risk suggestions based on Sharpe ratio
    if metrics["sharpe_ratio"] < 0.5:
        suggestions.append("Low risk-adjusted returns - consider rebalancing for better Sharpe ratio")
        
    # Age-appropriate suggestions (would need user age input)
    if bond_allocation < 0.1 and stock_allocation > 0.9:
        suggestions.append("Consider adding 10-20% bonds for risk management as you approach retirement")
    elif bond_allocation > 0.5 and stock_allocation < 0.5:
        suggestions.append("If you're young, consider more stock allocation for long-term growth")
        
    # Performance-based suggestions
    if metrics["volatility"] > 0.20:
        suggestions.append("High volatility - add bonds to reduce portfolio swings")
    elif metrics["volatility"] < 0.10:
        suggestions.append("Very low volatility - consider more growth assets if timeline permits")
        
    return suggestions
