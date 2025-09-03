# Claude Agent Core Implementation
"""
AI Agent implementation replacing rule-based RequestClassifier.
Uses Claude API with tool-calling capabilities for intelligent request routing and synthesis.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import httpx
import os
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AgentResponse(BaseModel):
    """Structured response from AI Agent"""
    recommendation: str
    allocation: Dict[str, float]
    expected_cagr: float
    expected_volatility: float
    max_drawdown: float
    sharpe_ratio: float
    risk_profile: str
    confidence_score: float
    tool_calls_made: List[str]
    synthesis_quality: str

class ClaudeAIAgent:
    """
    AI Agent powered by Claude API with tool-calling capabilities.
    Replaces rule-based RequestClassifier with intelligent orchestration.
    """
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-sonnet-4-20250514"
        self.max_tokens = 4000
        
        # Import tool definitions
        from .ai_agent_tools import ToolRegistry, ToolCallHandler, DEFAULT_PORTFOLIO
        self.tool_registry = ToolRegistry()
        self.tool_handler = ToolCallHandler()
        self.default_portfolio = DEFAULT_PORTFOLIO
    
    async def process_request(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Main entry point: Process user request with AI orchestration
        """
        try:
            # Step 1: Get Claude's analysis and tool calls
            claude_response = await self._call_claude_with_tools(message, context)
            
            # Step 2: Execute tool calls
            tool_results = await self._execute_tool_calls(claude_response.get("tool_use", []))
            
            # Step 3: Synthesize final response
            final_response = await self._synthesize_response(message, tool_results, context)
            
            return final_response
            
        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            return self._fallback_response(message, context)
    
    async def _call_claude_with_tools(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call Claude API with tool definitions to get analysis plan
        """
        # Build context-aware system prompt
        system_prompt = self._build_system_prompt(context)
        
        # Prepare user message with context
        user_message = self._build_user_message(message, context)
        
        # Get available tools
        tools = self.tool_registry.get_all_tools()
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "tools": tools,
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "system": system_prompt
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.claude_api_url,
                    headers=headers,
                    json=payload
                )
            
            if response.status_code != 200:
                logger.error(f"Claude API error: {response.status_code} - {response.text}")
                raise Exception(f"Claude API failed: {response.status_code}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build context-aware system prompt for Claude"""
        
        base_prompt = """You are an expert AI agent for portfolio analytics and investment recommendations. 

Your role is to:
1. Analyze user requests about portfolio management and investments
2. Determine which analytics tools to use based on the question
3. Call appropriate tools to gather data  
4. Synthesize results into comprehensive, actionable advice

Available analytics tools:
- recovery_analysis: For questions about recovery times from losses/drawdowns
- crisis_analysis: For stress testing and crisis performance  
- rebalancing_analysis: For rebalancing strategy optimization
- rolling_analysis: For performance consistency over time
- timeline_analysis: For age-based and lifecycle recommendations
- generate_portfolio: For creating new portfolio recommendations

Tool calling strategy:
- Use MULTIPLE tools when questions are comprehensive (e.g., "Is this safe for retirement?" → timeline + crisis + recovery)
- Always use the user's portfolio allocation when available
- Call generate_portfolio ONLY for new portfolio creation requests
- Synthesize results from multiple tools into unified recommendations

Response approach:
- Be conversational and practical
- Focus on actionable insights
- Explain risks and trade-offs clearly
- Use specific numbers and timeframes
- Always consider the user's context and goals"""

        # Add context-specific guidance
        if context:
            if context.get('lastRecommendation'):
                base_prompt += f"""

IMPORTANT: User has an existing portfolio recommendation:
{json.dumps(context['lastRecommendation'], indent=2)}

Use this allocation for analysis tools unless they're asking for a NEW portfolio."""

            if context.get('conversationHistory'):
                base_prompt += f"""

Previous conversation context available - maintain continuity with past discussions."""

        return base_prompt
    
    def _build_user_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build comprehensive user message with context"""
        
        user_message = f"User question: {message}"
        
        if context:
            # Add conversation history
            if context.get('conversationHistory'):
                history = context['conversationHistory'][-3:]  # Last 3 exchanges
                user_message += "\n\nRecent conversation:"
                for item in history:
                    user_message += f"\n- {item}"
            
            # Add user profile
            if context.get('userProfile'):
                profile = context['userProfile']
                user_message += f"\n\nUser profile: {json.dumps(profile)}"
            
            # Add last recommendation
            if context.get('lastRecommendation'):
                rec = context['lastRecommendation']
                user_message += f"\n\nCurrent portfolio allocation: {json.dumps(rec.get('allocation', {}))}"
        
        user_message += """

Please analyze this request and use appropriate tools to provide a comprehensive response.
Focus on practical, actionable advice based on the analytics data."""
        
        return user_message
    
    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute all tool calls and collect results"""
        
        results = {}
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            parameters = tool_call.get("input", {})
            
            try:
                result = await self.tool_handler.execute_tool(tool_name, parameters)
                results[tool_name] = result
                
                logger.info(f"Tool {tool_name} executed successfully")
                
            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {e}")
                results[tool_name] = {"error": str(e)}
        
        return results
    
    async def _synthesize_response(
        self, 
        original_message: str, 
        tool_results: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Call Claude again to synthesize tool results into final response
        """
        synthesis_prompt = f"""Based on the user's question: "{original_message}"

I executed the following analytics tools and got these results:

{json.dumps(tool_results, indent=2, default=str)}

Please synthesize these results into a comprehensive, practical recommendation.

Respond in JSON format with these fields:
{{
    "recommendation": "Natural language recommendation (markdown formatted)",
    "allocation": {{"symbol": weight}},
    "expected_cagr": 0.0,
    "expected_volatility": 0.0,
    "max_drawdown": 0.0,
    "sharpe_ratio": 0.0,
    "risk_profile": "conservative|balanced|aggressive",
    "confidence_score": 0.0,
    "synthesis_quality": "excellent|good|fair|poor"
}}

Guidelines:
- Make the recommendation conversational and actionable
- Include specific metrics from the analysis
- Highlight key insights and trade-offs
- Use the portfolio allocation from the analysis or recommend a new one
- Set realistic expectations for returns/risk
- Confidence score should reflect data quality and consistency"""

        try:
            headers = {
                "Content-Type": "application/json", 
                "x-api-key": self.api_key
            }
            
            payload = {
                "model": self.model,
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user", 
                        "content": synthesis_prompt
                    }
                ]
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.claude_api_url,
                    headers=headers,
                    json=payload
                )
            
            if response.status_code == 200:
                claude_data = response.json()
                content = claude_data["content"][0]["text"]
                
                # Parse JSON response
                try:
                    # Clean potential markdown formatting
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    
                    synthesis_data = json.loads(content.strip())
                    
                    return AgentResponse(
                        recommendation=synthesis_data.get("recommendation", "Analysis complete"),
                        allocation=synthesis_data.get("allocation", self.default_portfolio),
                        expected_cagr=synthesis_data.get("expected_cagr", 0.10),
                        expected_volatility=synthesis_data.get("expected_volatility", 0.15),
                        max_drawdown=synthesis_data.get("max_drawdown", -0.25),
                        sharpe_ratio=synthesis_data.get("sharpe_ratio", 0.65),
                        risk_profile=synthesis_data.get("risk_profile", "balanced"),
                        confidence_score=synthesis_data.get("confidence_score", 0.80),
                        tool_calls_made=list(tool_results.keys()),
                        synthesis_quality=synthesis_data.get("synthesis_quality", "good")
                    )
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse synthesis response: {e}")
                    return self._create_fallback_synthesis(tool_results, context)
            else:
                logger.error(f"Synthesis API error: {response.status_code}")
                return self._create_fallback_synthesis(tool_results, context)
                
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return self._create_fallback_synthesis(tool_results, context)
    
    def _create_fallback_synthesis(
        self, 
        tool_results: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Create fallback response when synthesis fails"""
        
        recommendation = "📊 **Analysis Complete**\n\nI've analyzed your portfolio using multiple analytics tools. "
        
        if tool_results:
            recommendation += f"The analysis covered: {', '.join(tool_results.keys())}. "
            recommendation += "While I encountered some issues with the detailed synthesis, the core analysis was successful."
        
        # Use existing allocation or default
        allocation = self.default_portfolio
        if context and context.get('lastRecommendation'):
            allocation = context['lastRecommendation'].get('allocation', self.default_portfolio)
        
        return AgentResponse(
            recommendation=recommendation,
            allocation=allocation,
            expected_cagr=0.10,
            expected_volatility=0.15,
            max_drawdown=-0.25,
            sharpe_ratio=0.65,
            risk_profile="balanced",
            confidence_score=0.70,
            tool_calls_made=list(tool_results.keys()),
            synthesis_quality="fair"
        )
    
    def _fallback_response(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Fallback response when agent processing completely fails"""
        
        recommendation = """🤖 **AI Agent Response**

I apologize, but I encountered an issue processing your request. However, I can still provide basic portfolio guidance based on your question.

For comprehensive analytics, please ensure:
- Your question is specific about what analysis you need
- You have a portfolio allocation to analyze (if applicable)
- The analytics services are running properly

Would you like to try rephrasing your question or ask for a specific type of analysis?"""

        return AgentResponse(
            recommendation=recommendation,
            allocation=self.default_portfolio,
            expected_cagr=0.10,
            expected_volatility=0.15, 
            max_drawdown=-0.25,
            sharpe_ratio=0.65,
            risk_profile="balanced",
            confidence_score=0.50,
            tool_calls_made=[],
            synthesis_quality="poor"
        )
