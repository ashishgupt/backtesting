# AI Agent Tool Definitions for Portfolio Analytics
"""
Tool definitions for Claude API integration - converts existing analytics endpoints
into Claude-callable tools with proper descriptions and parameter specifications.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

class PortfolioAnalyticsTool:
    """Base class for portfolio analytics tools"""
    
    def __init__(self, name: str, description: str, endpoint: str, method: str = "POST"):
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.method = method
        self.api_base = "http://127.0.0.1:8007"

class ToolRegistry:
    """Registry of all available portfolio analytics tools for Claude"""
    
    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        """Get all tools in Claude API tool format"""
        return [
            {
                "name": "recovery_analysis",
                "description": """
                Analyze portfolio recovery times from drawdowns. 
                
                Use when users ask about:
                - How long to recover from losses
                - Recovery periods, bounce-back time  
                - Time underwater after crashes
                - Portfolio resilience during downturns
                
                Returns detailed recovery statistics and patterns.
                """,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "allocation": {
                            "type": "object",
                            "description": "Portfolio allocation (symbol -> weight)",
                            "additionalProperties": {"type": "number"}
                        },
                        "start_date": {
                            "type": "string", 
                            "format": "date",
                            "description": "Analysis start date (YYYY-MM-DD)",
                            "default": "2015-01-02"
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date", 
                            "description": "Analysis end date (YYYY-MM-DD)",
                            "default": "2024-12-31"
                        },
                        "min_drawdown_pct": {
                            "type": "number",
                            "description": "Minimum drawdown threshold (0.10 = 10%)",
                            "default": 0.10
                        }
                    },
                    "required": ["allocation"]
                }
            },
            {
                "name": "crisis_analysis", 
                "description": """
                Stress test portfolio performance during major market crises.
                
                Use when users ask about:
                - How portfolio performs in crashes (2008, 2020, 2022)
                - Stress testing, bear market resilience
                - Crisis performance, worst-case scenarios
                - Portfolio safety during recessions
                
                Returns performance during major historical crisis periods.
                """,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "allocation": {
                            "type": "object",
                            "description": "Portfolio allocation (symbol -> weight)",
                            "additionalProperties": {"type": "number"}
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Analysis start date (YYYY-MM-DD)",
                            "default": "2004-01-02"
                        },
                        "end_date": {
                            "type": "string", 
                            "format": "date",
                            "description": "Analysis end date (YYYY-MM-DD)",
                            "default": "2024-12-31"
                        }
                    },
                    "required": ["allocation"]
                }
            },
            {
                "name": "rebalancing_analysis",
                "description": """
                Analyze different rebalancing strategies for optimal portfolio maintenance.
                
                Use when users ask about:
                - When/how often to rebalance
                - Threshold vs time-based rebalancing
                - Rebalancing strategy optimization
                - Portfolio drift management
                
                Returns comparison of different rebalancing approaches.
                """, 
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "allocation": {
                            "type": "object",
                            "description": "Target portfolio allocation (symbol -> weight)",
                            "additionalProperties": {"type": "number"}
                        },
                        "initial_amount": {
                            "type": "number",
                            "description": "Initial investment amount",
                            "default": 100000
                        },
                        "account_type": {
                            "type": "string",
                            "enum": ["tax_free", "taxable", "tax_deferred"],
                            "description": "Account type for tax implications",
                            "default": "tax_free"
                        },
                        "contribution_schedule": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Monthly contribution schedule",
                            "default": []
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "default": "2020-01-02"
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date", 
                            "default": "2024-12-31"
                        }
                    },
                    "required": ["allocation"]
                }
            },
            {
                "name": "rolling_analysis",
                "description": """
                Analyze portfolio performance consistency across rolling time periods.
                
                Use when users ask about:
                - Performance consistency over time
                - 3-year, 5-year rolling returns
                - Portfolio stability across different periods
                - Risk consistency analysis
                
                Returns rolling period performance statistics.
                """,
                "input_schema": {
                    "type": "object", 
                    "properties": {
                        "allocation": {
                            "type": "object",
                            "description": "Portfolio allocation (symbol -> weight)",
                            "additionalProperties": {"type": "number"}
                        },
                        "period_years": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Rolling window sizes in years",
                            "default": [3, 5, 10]
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                            "default": "2015-01-02"
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                            "default": "2024-12-31" 
                        }
                    },
                    "required": ["allocation"]
                }
            },
            {
                "name": "timeline_analysis",
                "description": """
                Provide age and timeline-based investment recommendations.
                
                Use when users ask about:
                - Age-appropriate asset allocation
                - Investment timeline planning
                - Lifecycle investing recommendations
                - Retirement planning allocation
                
                Returns age-based portfolio recommendations.
                """,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "age": {
                            "type": "integer",
                            "minimum": 18,
                            "maximum": 100,
                            "description": "Investor age",
                            "default": 35
                        },
                        "retirement_age": {
                            "type": "integer", 
                            "minimum": 50,
                            "maximum": 80,
                            "description": "Target retirement age",
                            "default": 65
                        },
                        "risk_tolerance": {
                            "type": "string",
                            "enum": ["conservative", "balanced", "aggressive"],
                            "description": "Risk tolerance level",
                            "default": "balanced"
                        },
                        "investment_horizon_years": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 50, 
                            "description": "Investment timeline in years",
                            "default": 10
        self.api_base = "http://127.0.0.1:8007"
        self.endpoint_mapping = {
            "recovery_analysis": "/api/analyze/recovery-analysis",
            "crisis_analysis": "/api/analyze/stress-test", 
            "rebalancing_analysis": "/api/rebalancing/analyze-strategies",
            "rolling_analysis": "/api/analyze/rolling-periods",
            "timeline_analysis": "/api/analyze/timeline-risk",
            "generate_portfolio": "/api/chat/recommend"
        }
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call against the appropriate API endpoint"""
        import httpx
        
        endpoint = self.endpoint_mapping.get(tool_name)
        if not endpoint:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Handle special case for portfolio generation
        if tool_name == "generate_portfolio":
            return await self._call_portfolio_generation(parameters)
        
        # Standard analytics endpoint call
        url = f"{self.api_base}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=parameters)
                
            if response.status_code != 200:
                return {
                    "error": f"API call failed: {response.status_code}",
                    "details": response.text
                }
            
            return response.json()
            
        except Exception as e:
            return {
                "error": f"Tool execution failed: {str(e)}"
            }
    
    async def _call_portfolio_generation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle portfolio generation tool call"""
        import httpx
        
        # Convert to expected format
        request_data = {
            "message": parameters.get("message", ""),
            "user_context": {
                "userPreferences": {
                    "risk_tolerance": parameters.get("risk_preference", "balanced"),
                    "investment_amount": parameters.get("investment_amount", 100000)
                }
            }
        }
        
        url = f"{self.api_base}/api/chat/recommend"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=request_data)
                
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Portfolio generation failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "error": f"Portfolio generation error: {str(e)}"
            }

# Default portfolio allocation for analysis tools
DEFAULT_PORTFOLIO = {
    "VTI": 0.40,    # US Total Stock Market
    "VTIAX": 0.20,  # International Stocks  
    "BND": 0.15,    # US Total Bond Market
    "VNQ": 0.10,    # US Real Estate (REITs)
    "GLD": 0.05,    # Gold Commodity
    "VWO": 0.07,    # Emerging Markets
    "QQQ": 0.03     # Technology Growth
}
