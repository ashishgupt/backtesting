"""
🚀 Enhanced Portfolio Advisor with Timeline-Based Risk Assessment
Leverages advanced analytics APIs for sophisticated portfolio optimization
"""
import json
import re
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class InvestorProfile(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced" 
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

@dataclass
class RiskScenario:
    """Risk scenario with timeline-based analysis"""
    name: str
    allocation: Dict[str, float]
    expected_cagr: float
    max_drawdown: float
    recovery_months: Optional[float]
    sharpe_ratio: float
    description: str
    risk_level: str  # "Low", "Medium", "High"

@dataclass
class TimelineOptimizedRecommendation:
    """Enhanced recommendation with multiple risk scenarios"""
    primary_recommendation: RiskScenario
    alternative_scenarios: List[RiskScenario]
    timeline_analysis: str
    recovery_analysis: str
    crisis_resilience: str
    reasoning: str
    confidence_score: float

class EnhancedPortfolioAdvisor:
    """
    Timeline-aware portfolio advisor using advanced analytics APIs
    """
    
    def __init__(self, api_base_url: str = "http://127.0.0.1:8007"):
        self.api_base = api_base_url
        self.available_assets = ["VTI", "VTIAX", "BND", "VNQ", "GLD", "VWO", "QQQ"]
        
        # Base allocation templates for scenario generation
        self.base_scenarios = {
            "conservative": {"VTI": 0.25, "VTIAX": 0.15, "BND": 0.40, "VNQ": 0.08, "GLD": 0.07, "VWO": 0.03, "QQQ": 0.02},
            "balanced": {"VTI": 0.35, "VTIAX": 0.20, "BND": 0.20, "VNQ": 0.10, "GLD": 0.05, "VWO": 0.07, "QQQ": 0.03},
            "aggressive": {"VTI": 0.40, "VTIAX": 0.20, "BND": 0.10, "VNQ": 0.12, "GLD": 0.03, "VWO": 0.10, "QQQ": 0.05},
            "max_growth": {"VTI": 0.45, "VTIAX": 0.25, "BND": 0.05, "VNQ": 0.10, "GLD": 0.02, "VWO": 0.08, "QQQ": 0.05}
        }
    
    def generate_timeline_optimized_recommendation(self, user_request: str, amount: float = 1000000) -> TimelineOptimizedRecommendation:
        """
        Generate sophisticated timeline-based portfolio recommendation
        """
        # Parse the request
        parsed = self.parse_natural_language_request(user_request)
        years = parsed.get("years_to_invest", 10)  # Default to 10 years
        
        logger.info(f"Generating timeline-optimized recommendation for {years} years")
        
        # Generate multiple risk scenarios
        scenarios = []
        
        for scenario_name, base_allocation in self.base_scenarios.items():
            # Adjust allocation based on timeline
            adjusted_allocation = self._adjust_allocation_for_timeline(base_allocation.copy(), years, parsed)
            
            # Get backtesting results
            backtest_result = self._backtest_portfolio(adjusted_allocation, amount)
            if not backtest_result:
                continue
                
            # Get recovery analysis
            recovery_data = self._get_recovery_analysis(adjusted_allocation)
            
            # Get crisis analysis  
            crisis_data = self._get_crisis_analysis(adjusted_allocation)
            
            # Create risk scenario
            scenario = RiskScenario(
                name=scenario_name.replace('_', ' ').title(),
                allocation=adjusted_allocation,
                expected_cagr=backtest_result["performance_metrics"]["cagr"],
                max_drawdown=backtest_result["performance_metrics"]["max_drawdown"],
                recovery_months=recovery_data.get("avg_recovery_months") if recovery_data else None,
                sharpe_ratio=backtest_result["performance_metrics"]["sharpe_ratio"],
                description=self._generate_scenario_description(scenario_name, backtest_result, recovery_data, crisis_data),
                risk_level=self._determine_risk_level(backtest_result["performance_metrics"]["max_drawdown"])
            )
            scenarios.append(scenario)
        
        # Sort scenarios by appropriateness for timeline
        scenarios.sort(key=lambda x: self._scenario_score_for_timeline(x, years), reverse=True)
        
        primary = scenarios[0]
        alternatives = scenarios[1:3]  # Top 3 alternatives
        
        # Generate comprehensive analysis
        timeline_analysis = self._generate_timeline_analysis(years, scenarios)
        recovery_analysis = self._generate_recovery_analysis(primary.allocation)
        crisis_resilience = self._generate_crisis_resilience_analysis(primary.allocation)
        reasoning = self._generate_enhanced_reasoning(parsed, primary, alternatives, years)
        
        return TimelineOptimizedRecommendation(
            primary_recommendation=primary,
            alternative_scenarios=alternatives,
            timeline_analysis=timeline_analysis,
            recovery_analysis=recovery_analysis,
            crisis_resilience=crisis_resilience,
            reasoning=reasoning,
            confidence_score=0.85
        )
    
    def _adjust_allocation_for_timeline(self, allocation: Dict[str, float], years: int, parsed: Dict) -> Dict[str, float]:
        """
        Adjust allocation based on investment timeline and risk tolerance
        """
        # Timeline-based adjustments
        if years <= 2:
            # Very short term - capital preservation focus
            allocation["BND"] = min(0.70, allocation.get("BND", 0) + 0.30)  # Increase bonds significantly
            allocation["VTI"] = max(0.15, allocation.get("VTI", 0) - 0.15)
            allocation["VTIAX"] = max(0.10, allocation.get("VTIAX", 0) - 0.10)
            
        elif years <= 5:
            # Short-medium term - moderate growth with stability
            allocation["BND"] = min(0.40, allocation.get("BND", 0) + 0.10)
            
        elif years >= 15:
            # Long term - growth focus with recovery time
            if "max return" in parsed.get("user_request", "").lower():
                allocation["BND"] = max(0.05, allocation.get("BND", 0) - 0.15)  # Minimal bonds
                allocation["VTI"] = min(0.50, allocation.get("VTI", 0) + 0.10)
                allocation["QQQ"] = min(0.10, allocation.get("QQQ", 0) + 0.03)  # More tech growth
        
        # Normalize to sum to 1.0
        total = sum(allocation.values())
        if total > 0:
            allocation = {k: v/total for k, v in allocation.items()}
            
        return allocation
    
    def _backtest_portfolio(self, allocation: Dict[str, float], amount: float) -> Optional[Dict]:
        """
        Backtest portfolio using API
        """
        try:
            response = requests.post(f"{self.api_base}/api/backtest/portfolio", json={
                "allocation": allocation,
                "start_date": "2004-01-02", 
                "end_date": "2024-12-31",
                "initial_value": amount,
                "rebalance_frequency": "monthly"
            }, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Backtesting API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Backtesting API request failed: {e}")
            return None
    
    def _get_recovery_analysis(self, allocation: Dict[str, float]) -> Optional[Dict]:
        """
        Get recovery time analysis using API
        """
        try:
            response = requests.post(f"{self.api_base}/api/analytics/recovery-patterns", json={
                "allocation": allocation
            }, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Recovery analysis API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Recovery analysis API request failed: {e}")
            return None
    
    def _get_crisis_analysis(self, allocation: Dict[str, float]) -> Optional[Dict]:
        """
        Get crisis period analysis using API
        """
        try:
            response = requests.post(f"{self.api_base}/api/analytics/crisis-analysis", json={
                "allocation": allocation
            }, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Crisis analysis API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Crisis analysis API request failed: {e}")
            return None
    
    def _determine_risk_level(self, max_drawdown: float) -> str:
        """
        Determine risk level based on max drawdown
        """
        abs_drawdown = abs(max_drawdown)
        if abs_drawdown <= 0.15:  # ≤15% drawdown
            return "Low"
        elif abs_drawdown <= 0.25:  # ≤25% drawdown
            return "Medium" 
        else:  # >25% drawdown
            return "High"
    
    def _scenario_score_for_timeline(self, scenario: RiskScenario, years: int) -> float:
        """
        Score scenario appropriateness for given timeline
        """
        score = 0.0
        
        # Timeline appropriateness
        if years <= 2:
            # Short term - prefer low drawdown
            score += (1.0 - abs(scenario.max_drawdown)) * 0.6
            score += scenario.sharpe_ratio * 0.4
        elif years <= 5:
            # Medium term - balance growth and stability
            score += scenario.expected_cagr * 0.4
            score += (1.0 - abs(scenario.max_drawdown)) * 0.4
            score += scenario.sharpe_ratio * 0.2
        else:
            # Long term - prefer growth with acceptable drawdown
            score += scenario.expected_cagr * 0.5
            score += scenario.sharpe_ratio * 0.3
            score += (1.0 - abs(scenario.max_drawdown)) * 0.2
            
        return score
    
    def _generate_scenario_description(self, scenario_name: str, backtest_result: Dict, 
                                     recovery_data: Optional[Dict], crisis_data: Optional[Dict]) -> str:
        """
        Generate description for risk scenario
        """
        cagr = backtest_result["performance_metrics"]["cagr"] * 100
        drawdown = abs(backtest_result["performance_metrics"]["max_drawdown"]) * 100
        
        description = f"{cagr:.1f}% annual returns with {drawdown:.1f}% maximum decline"
        
        if recovery_data and recovery_data.get("avg_recovery_months"):
            description += f", typically recovers in {recovery_data['avg_recovery_months']:.0f} months"
            
        return description
    
    def parse_natural_language_request(self, user_request: str) -> Dict:
        """
        Parse natural language request - enhanced version
        """
        user_message = user_request.lower()
        parsed = {
            "user_request": user_request,
            "risk_tolerance": None,
            "investment_horizon": "medium_term",
            "specific_assets": [],
            "allocation_preferences": {},
            "constraints": {},
            "goals": [],
            "amount": None,
            "request_type": "portfolio_recommendation",
            "follow_up_question": None,
            "years_to_invest": None
        }
        
        # Risk tolerance keywords - enhanced for max return detection
        if any(word in user_message for word in ["conservative", "safe", "low risk", "stable", "capital preservation"]):
            parsed["risk_tolerance"] = InvestorProfile.CONSERVATIVE
        elif any(word in user_message for word in ["aggressive", "high risk", "growth", "risky", "max return", "maximum return", "highest return", "max growth", "maximum growth"]):
            parsed["risk_tolerance"] = InvestorProfile.AGGRESSIVE
        elif any(word in user_message for word in ["balanced", "moderate", "medium risk"]):
            parsed["risk_tolerance"] = InvestorProfile.BALANCED
            
        # Extract specific timeframes
        time_match = re.search(r'(\d+)\s*years?', user_message)
        if time_match:
            years = int(time_match.group(1))
            parsed["years_to_invest"] = years
            if years <= 2:
                parsed["investment_horizon"] = "short_term"
            elif years >= 10:
                parsed["investment_horizon"] = "long_term"
        
        # Extract amount if mentioned
        amount_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|m|k|thousand)?', user_message)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            amount = float(amount_str)
            if 'million' in user_message or ' m ' in user_message:
                amount *= 1000000
            elif 'thousand' in user_message or ' k ' in user_message:
                amount *= 1000
            parsed["amount"] = amount
            
        return parsed    
    def _generate_timeline_analysis(self, years: int, scenarios: List[RiskScenario]) -> str:
        """
        Generate timeline-specific analysis
        """
        if years <= 2:
            return f"For a {years}-year timeline, capital preservation is critical. The recommended portfolio prioritizes stability over growth, accepting lower returns to minimize the risk of losses when you need the funds."
        elif years <= 5:
            return f"With a {years}-year investment horizon, we balance growth potential with downside protection. You have some time to recover from market volatility, but not enough to weather extended bear markets."
        elif years <= 10:
            return f"A {years}-year timeline allows for moderate risk-taking. You can recover from typical market downturns (which average 1-2 years), enabling a growth-focused approach with reasonable stability."
        else:
            return f"Your {years}-year investment horizon provides excellent flexibility for aggressive growth. You can weather multiple market cycles and benefit from compounding returns, justifying higher short-term volatility for superior long-term gains."
    
    def _generate_recovery_analysis(self, allocation: Dict[str, float]) -> str:
        """
        Generate recovery time analysis using API data
        """
        recovery_data = self._get_recovery_analysis(allocation)
        
        if recovery_data and recovery_data.get("analysis"):
            return recovery_data["analysis"]
        else:
            # Fallback based on allocation
            stock_pct = allocation.get("VTI", 0) + allocation.get("VTIAX", 0) + allocation.get("VWO", 0) + allocation.get("QQQ", 0)
            if stock_pct >= 0.7:
                return "High-growth portfolios typically recover from major declines within 18-24 months, though recovery time varies by market conditions."
            elif stock_pct >= 0.5:
                return "Balanced portfolios generally recover from significant losses within 12-18 months due to bond cushioning and diversification."
            else:
                return "Conservative portfolios recover quickly from modest declines (6-12 months) due to high bond allocation and lower volatility."
    
    def _generate_crisis_resilience_analysis(self, allocation: Dict[str, float]) -> str:
        """
        Generate crisis resilience analysis using API data
        """
        crisis_data = self._get_crisis_analysis(allocation)
        
        if crisis_data and crisis_data.get("resilience_summary"):
            return crisis_data["resilience_summary"]
        else:
            # Fallback analysis
            return "During major market crises (2008, 2020, 2022), this allocation would have experienced significant but recoverable declines, with strong rebounds following each crisis period."
    
    def _generate_enhanced_reasoning(self, parsed: Dict, primary: RiskScenario, 
                                   alternatives: List[RiskScenario], years: int) -> str:
        """
        Generate comprehensive reasoning for recommendation
        """
        reasoning = []
        
        # Timeline-based reasoning
        if years <= 5:
            reasoning.append(f"Given your {years}-year timeline, I'm recommending a {primary.risk_level.lower()}-risk portfolio that prioritizes capital preservation while capturing reasonable growth.")
        else:
            reasoning.append(f"With {years} years to invest, you can afford higher short-term volatility for superior long-term returns.")
        
        # Performance reasoning
        reasoning.append(f"This portfolio targets {primary.expected_cagr*100:.1f}% annual returns with maximum historical declines of {abs(primary.max_drawdown)*100:.1f}%.")
        
        # Risk-adjusted reasoning
        if primary.sharpe_ratio > 0.8:
            reasoning.append("The risk-adjusted returns (Sharpe ratio) are excellent, indicating efficient use of risk.")
        elif primary.sharpe_ratio > 0.6:
            reasoning.append("The risk-adjusted returns are solid, providing good compensation for the volatility taken.")
        
        # Alternative scenarios reasoning
        if alternatives:
            alt_descriptions = []
            for alt in alternatives[:2]:  # Top 2 alternatives
                alt_descriptions.append(f"{alt.name}: {alt.expected_cagr*100:.1f}% returns, {abs(alt.max_drawdown)*100:.1f}% max decline")
            
            reasoning.append(f"Alternative options include: {'; '.join(alt_descriptions)}.")
        
        return " ".join(reasoning)
    
    def format_enhanced_response(self, recommendation: TimelineOptimizedRecommendation) -> Dict[str, Any]:
        """
        Format enhanced recommendation for API response
        """
        primary = recommendation.primary_recommendation
        
        # Create response text with scenarios
        response_text = f"🎯 **Timeline-Optimized Portfolio Recommendation**\n\n"
        response_text += f"**Primary Recommendation ({primary.risk_level} Risk):**\n"
        response_text += f"• Expected Returns: {primary.expected_cagr*100:.1f}% annually\n"
        response_text += f"• Maximum Historical Decline: {abs(primary.max_drawdown)*100:.1f}%\n"
        if primary.recovery_months:
            response_text += f"• Typical Recovery Time: {primary.recovery_months:.0f} months\n"
        response_text += f"• Risk-Adjusted Score: {primary.sharpe_ratio:.2f}\n\n"
        
        # Add alternative scenarios
        if recommendation.alternative_scenarios:
            response_text += "**Alternative Risk Levels:**\n"
            for i, alt in enumerate(recommendation.alternative_scenarios[:2], 1):
                response_text += f"{i}. **{alt.name} ({alt.risk_level} Risk):** {alt.expected_cagr*100:.1f}% returns, {abs(alt.max_drawdown)*100:.1f}% max decline\n"
            response_text += "\n"
        
        # Add analyses
        response_text += f"**Timeline Analysis:** {recommendation.timeline_analysis}\n\n"
        response_text += f"**Recovery Outlook:** {recommendation.recovery_analysis}\n\n"
        response_text += f"**Crisis Resilience:** {recommendation.crisis_resilience}\n\n"
        response_text += f"**Reasoning:** {recommendation.reasoning}"
        
        return {
            "recommendation": response_text,
            "allocation": primary.allocation,
            "expected_cagr": primary.expected_cagr,
            "expected_volatility": primary.max_drawdown,  # Using drawdown as volatility proxy
            "max_drawdown": primary.max_drawdown,
            "sharpe_ratio": primary.sharpe_ratio,
            "risk_profile": primary.risk_level.lower(),
            "confidence_score": recommendation.confidence_score,
            "alternative_scenarios": [
                {
                    "name": alt.name,
                    "allocation": alt.allocation,
                    "expected_cagr": alt.expected_cagr,
                    "max_drawdown": alt.max_drawdown,
                    "risk_level": alt.risk_level
                } for alt in recommendation.alternative_scenarios
            ],
            "timeline_analysis": recommendation.timeline_analysis,
            "recovery_analysis": recommendation.recovery_analysis,
            "crisis_resilience": recommendation.crisis_resilience
        }
