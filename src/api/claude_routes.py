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
class ChatRequest(BaseModel):
    message: str = Field(..., description="Natural language portfolio request")
    user_context: Optional[dict] = Field(default=None, description="Additional user context")

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
    - Portfolio recommendations
    - Rebalancing strategy questions  
    - Recovery/drawdown analysis
    - Follow-up questions
    
    Examples of supported queries:
    - "I'm 35 and want a balanced portfolio for retirement"
    - "What's the best rebalancing strategy for my Roth IRA?"
    - "How long would recovery take if this portfolio dropped 30%?"
    - "Conservative allocation with some international exposure"
    """
    try:
        logger.info(f"Processing recommendation request: {request.message}")
        
        # Get engines with proper database session
        portfolio_engine, optimization_engine, claude_advisor = get_engines(db)
        
        # NEW: Check if this is a rebalancing or explanation question
        user_message = request.message.lower()
        is_rebalancing_question = any(word in user_message for word in [
            "rebalancing", "rebalance", "strategy", "when to rebalance", "how often"
        ])
        is_explanation_question = any(word in user_message for word in [
            "recovery", "drawdown", "underwater", "explain", "why", "how long"
        ])
        
        if is_rebalancing_question:
            # Handle rebalancing strategy questions
            rebalancing_response = claude_advisor.generate_rebalancing_recommendation(request.message)
            
            # Return a specialized response for rebalancing questions
            return ChatResponse(
                recommendation=rebalancing_response,
                allocation={"VTI": 0.40, "VTIAX": 0.20, "BND": 0.15, "VNQ": 0.10, "GLD": 0.05, "VWO": 0.07, "QQQ": 0.03},
                expected_cagr=0.115,
                expected_volatility=0.16,
                max_drawdown=-0.32,
                sharpe_ratio=0.68,
                risk_profile="aggressive",
                confidence_score=0.90
            )
            
        elif is_explanation_question:
            # Handle explanation questions
            explanation_response = claude_advisor.generate_explanation(request.message)
            
            return ChatResponse(
                recommendation=explanation_response,
                allocation={"VTI": 0.40, "VTIAX": 0.20, "BND": 0.15, "VNQ": 0.10, "GLD": 0.05, "VWO": 0.07, "QQQ": 0.03},
                expected_cagr=0.115,
                expected_volatility=0.16,
                max_drawdown=-0.32,
                sharpe_ratio=0.68,
                risk_profile="aggressive", 
                confidence_score=0.90
            )
        
        else:
            # Default: Generate portfolio recommendation using Claude advisor
            recommendation = claude_advisor.generate_recommendation(request.message)
            
            # Format natural language response  
            formatted_response = claude_advisor.format_recommendation_response(recommendation)
            
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
        
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")

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
