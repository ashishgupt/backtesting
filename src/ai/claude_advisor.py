"""
🤖 Claude Portfolio Advisor
Natural language interface for portfolio recommendations using backtesting data
"""
import json
import re
from typing import Dict, List, Optional, Tuple
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
class PortfolioRecommendation:
    """Structured portfolio recommendation with reasoning"""
    allocation: Dict[str, float]
    expected_cagr: float
    expected_volatility: float
    max_drawdown: float
    sharpe_ratio: float
    reasoning: str
    risk_profile: InvestorProfile
    confidence_score: float  # 0.0 to 1.0

class ClaudePortfolioAdvisor:
    """
    Natural language portfolio advisor that integrates with backtesting engine
    Provides conversational interface for portfolio recommendations
    """
    
    def __init__(self, backtesting_engine, optimization_engine):
        self.backtesting_engine = backtesting_engine
        self.optimization_engine = optimization_engine
        self.available_assets = ["VTI", "VTIAX", "BND"]
        
        # Pre-computed reference portfolios
        self.reference_portfolios = {
            InvestorProfile.CONSERVATIVE: {"VTI": 0.3, "VTIAX": 0.2, "BND": 0.5},
            InvestorProfile.BALANCED: {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
            InvestorProfile.AGGRESSIVE: {"VTI": 0.7, "VTIAX": 0.3, "BND": 0.0}
        }
    
    def parse_natural_language_request(self, user_message: str) -> Dict:
        """
        Parse natural language portfolio request and extract key parameters
        """
        user_message = user_message.lower()
        
        # Initialize parsing results
        parsed = {
            "risk_tolerance": None,
            "investment_horizon": None, 
            "specific_assets": [],
            "allocation_preferences": {},
            "constraints": {},
            "goals": [],
            "amount": None
        }
        
        # Risk tolerance keywords
        if any(word in user_message for word in ["conservative", "safe", "low risk", "stable"]):
            parsed["risk_tolerance"] = InvestorProfile.CONSERVATIVE
        elif any(word in user_message for word in ["aggressive", "high risk", "growth", "risky"]):
            parsed["risk_tolerance"] = InvestorProfile.AGGRESSIVE
        elif any(word in user_message for word in ["balanced", "moderate", "medium risk"]):
            parsed["risk_tolerance"] = InvestorProfile.BALANCED
            
        # Investment horizon
        if any(word in user_message for word in ["retire", "retirement", "long term", "decades", "30 years", "20 years"]):
            parsed["investment_horizon"] = "long_term"
        elif any(word in user_message for word in ["short term", "few years", "5 years", "3 years", "near term", "next year", "1 year", "soon"]):
            parsed["investment_horizon"] = "short_term"
        else:
            parsed["investment_horizon"] = "medium_term"
            
        # Extract specific timeframes
        time_match = re.search(r'(\d+)\s*years?', user_message)
        if time_match:
            years = int(time_match.group(1))
            parsed["years_to_invest"] = years
            if years <= 5:
                parsed["investment_horizon"] = "short_term"
            elif years >= 15:
                parsed["investment_horizon"] = "long_term"
            else:
                parsed["investment_horizon"] = "medium_term"
                
        # Handle "next year", "1 year" cases
        if "next year" in user_message or "1 year" in user_message:
            parsed["years_to_invest"] = 1
            parsed["investment_horizon"] = "short_term"
            
        # Asset preferences
        if "international" in user_message or "global" in user_message or "vtiax" in user_message:
            parsed["specific_assets"].append("VTIAX")
        if "domestic" in user_message or "us" in user_message or "vti" in user_message:
            parsed["specific_assets"].append("VTI")
        if "bonds" in user_message or "fixed income" in user_message or "bnd" in user_message:
            parsed["specific_assets"].append("BND")
            
        # Goals
        if any(word in user_message for word in ["income", "dividend", "yield"]):
            parsed["goals"].append("income")
        if any(word in user_message for word in ["growth", "appreciation", "returns"]):
            parsed["goals"].append("growth")
            
        # Amount
        amount_match = re.search(r'\$?([\d,]+)', user_message)
        if amount_match:
            parsed["amount"] = float(amount_match.group(1).replace(',', ''))
            
        return parsed
    
    def generate_recommendation(self, user_request: str) -> PortfolioRecommendation:
        """
        Generate portfolio recommendation based on natural language request
        """
        parsed = self.parse_natural_language_request(user_request)
        logger.info(f"Parsed request: {parsed}")
        
        # Determine base portfolio from risk tolerance
        risk_profile = parsed["risk_tolerance"] or InvestorProfile.BALANCED
        base_allocation = self.reference_portfolios[risk_profile].copy()
        
        # CRITICAL FIX: Adjust allocation based on investment horizon
        investment_horizon = parsed.get("investment_horizon", "medium_term")
        
        if investment_horizon == "short_term":
            # Short-term: Increase bonds, reduce volatility
            bond_boost = 0.2  # Add 20% more to bonds
            base_allocation["BND"] = min(0.6, base_allocation.get("BND", 0) + bond_boost)
            # Reduce stocks proportionally
            stock_reduction = bond_boost / 2
            base_allocation["VTI"] = max(0.1, base_allocation.get("VTI", 0) - stock_reduction)
            base_allocation["VTIAX"] = max(0.1, base_allocation.get("VTIAX", 0) - stock_reduction)
            
        elif investment_horizon == "long_term":
            # Long-term: Increase stocks, reduce bonds for growth
            stock_boost = 0.2  # Add 20% more to stocks
            base_allocation["VTI"] = min(0.8, base_allocation.get("VTI", 0) + stock_boost * 0.6)
            base_allocation["VTIAX"] = min(0.4, base_allocation.get("VTIAX", 0) + stock_boost * 0.4)
            # Reduce bonds
            base_allocation["BND"] = max(0.0, base_allocation.get("BND", 0) - stock_boost)
        
        # Handle specific years mentioned
        if "years_to_invest" in parsed:
            years = parsed["years_to_invest"]
            if years <= 3:
                # Very short term - heavy bonds
                base_allocation = {"VTI": 0.2, "VTIAX": 0.1, "BND": 0.7}
            elif years <= 7:
                # Short-medium term - moderate bonds
                base_allocation = {"VTI": 0.4, "VTIAX": 0.2, "BND": 0.4}
            elif years >= 20:
                # Very long term - heavy stocks
                base_allocation = {"VTI": 0.7, "VTIAX": 0.3, "BND": 0.0}
        
        # Adjust based on specific preferences
        if parsed["specific_assets"]:
            # If user mentioned specific assets, increase their allocation
            for asset in parsed["specific_assets"]:
                if asset in base_allocation:
                    base_allocation[asset] = min(1.0, base_allocation[asset] + 0.1)
                    
        # Normalize allocations to sum to 1.0
        total = sum(base_allocation.values())
        if total > 0:
            base_allocation = {k: v/total for k, v in base_allocation.items()}
        
        # CRITICAL FIX: Re-evaluate risk profile based on FINAL allocation
        bond_percentage = base_allocation.get("BND", 0)
        stock_percentage = base_allocation.get("VTI", 0) + base_allocation.get("VTIAX", 0)
        
        # Determine actual risk profile from final allocation
        if bond_percentage >= 0.5:  # 50%+ bonds = conservative
            actual_risk_profile = InvestorProfile.CONSERVATIVE
        elif stock_percentage >= 0.8:  # 80%+ stocks = aggressive  
            actual_risk_profile = InvestorProfile.AGGRESSIVE
        else:  # Everything else = balanced
            actual_risk_profile = InvestorProfile.BALANCED
        
        # Run backtesting on recommended portfolio
        try:
            backtest_result = self.backtesting_engine.backtest_portfolio(
                allocation=base_allocation,
                start_date="2015-01-02",
                end_date="2024-12-31",
                initial_value=parsed["amount"] or 10000,
                rebalance_frequency="monthly"
            )
            
            metrics = backtest_result["performance_metrics"]
            
            # Generate reasoning
            reasoning = self._generate_reasoning(parsed, base_allocation, metrics)
            
            return PortfolioRecommendation(
                allocation=base_allocation,
                expected_cagr=metrics["cagr"],
                expected_volatility=metrics["volatility"],
                max_drawdown=metrics["max_drawdown"],
                sharpe_ratio=metrics["sharpe_ratio"],
                reasoning=reasoning,
                risk_profile=actual_risk_profile,  # Use corrected risk profile
                confidence_score=0.85  # High confidence for tested allocations
            )
            
        except Exception as e:
            logger.error(f"Backtesting failed: {e}")
            # Return a basic recommendation if backtesting fails
            return PortfolioRecommendation(
                allocation=base_allocation,
                expected_cagr=0.08,  # Conservative estimate
                expected_volatility=0.15,
                max_drawdown=-0.25,
                sharpe_ratio=0.5,
                reasoning="Basic allocation based on risk profile (backtesting unavailable)",
                risk_profile=actual_risk_profile,  # Use corrected risk profile
                confidence_score=0.6
            )
    
    def _generate_reasoning(self, parsed: Dict, allocation: Dict[str, float], metrics: Dict) -> str:
        """Generate human-readable reasoning for the recommendation"""
        
        reasoning_parts = []
        
        # Risk assessment
        risk_profile = parsed["risk_tolerance"]
        if risk_profile == InvestorProfile.CONSERVATIVE:
            reasoning_parts.append(
                f"Given your conservative approach, this portfolio emphasizes stability with "
                f"{allocation.get('BND', 0):.0%} in bonds to reduce volatility."
            )
        elif risk_profile == InvestorProfile.AGGRESSIVE:
            reasoning_parts.append(
                f"For aggressive growth, this portfolio is {allocation.get('VTI', 0) + allocation.get('VTIAX', 0):.0%} "
                f"stocks with minimal bond allocation to maximize long-term returns."
            )
        else:
            reasoning_parts.append(
                f"This balanced approach combines {allocation.get('VTI', 0) + allocation.get('VTIAX', 0):.0%} "
                f"stocks with {allocation.get('BND', 0):.0%} bonds for growth with manageable risk."
            )
        
        # International diversification
        if allocation.get('VTIAX', 0) > 0.15:
            reasoning_parts.append(
                f"International diversification ({allocation.get('VTIAX', 0):.0%} VTIAX) "
                f"reduces single-country risk and captures global growth opportunities."
            )
        
        # Performance context
        reasoning_parts.append(
            f"Historical backtesting (2015-2024) shows {metrics['cagr']:.1%} annual returns "
            f"with {metrics['max_drawdown']:.1%} maximum drawdown. "
            f"Sharpe ratio of {metrics['sharpe_ratio']:.2f} indicates good risk-adjusted returns."
        )
        
        # Investment horizon consideration
        horizon = parsed.get("investment_horizon", "medium_term")
        years = parsed.get("years_to_invest")
        
        if horizon == "short_term" or (years and years <= 5):
            reasoning_parts.append(
                f"With a short investment timeline ({years} years) " if years else "With a short-term focus, " +
                "this allocation emphasizes capital preservation with higher bond allocation to reduce volatility risk."
            )
        elif horizon == "long_term" or (years and years >= 15):
            reasoning_parts.append(
                f"With a long investment timeline ({years} years) " if years else "With a long-term horizon, " +
                "this allocation favors growth assets (stocks) to maximize compound returns over time, accepting short-term volatility."
            )
        else:
            reasoning_parts.append(
                "Medium-term horizon balances growth potential with stability for intermediate goals."
            )
            
        return " ".join(reasoning_parts)
    
    def format_recommendation_response(self, recommendation: PortfolioRecommendation) -> str:
        """Format recommendation as natural language response"""
        
        response = f"""🎯 **Portfolio Recommendation**

**Allocation:**
"""
        
        for asset, weight in recommendation.allocation.items():
            if weight > 0.01:  # Only show meaningful allocations
                asset_name = {
                    "VTI": "US Total Stock Market (VTI)",
                    "VTIAX": "International Stocks (VTIAX)", 
                    "BND": "US Total Bond Market (BND)"
                }.get(asset, asset)
                response += f"• {weight:.0%} - {asset_name}\n"
        
        response += f"""
**Expected Performance:**
• Annual Returns: {recommendation.expected_cagr:.1%}
• Volatility: {recommendation.expected_volatility:.1%}
• Maximum Drawdown: {recommendation.max_drawdown:.1%}
• Sharpe Ratio: {recommendation.sharpe_ratio:.2f}

**Analysis:**
{recommendation.reasoning}

**Risk Profile:** {recommendation.risk_profile.value.title()}
**Confidence:** {recommendation.confidence_score:.0%}

*Based on historical data (2015-2024). Past performance doesn't guarantee future results.*
"""
        
        return response

# Example usage and testing
if __name__ == "__main__":
    # This would normally be integrated with the actual engines
    print("🤖 Claude Portfolio Advisor - Test Mode")
    print("This module provides natural language portfolio recommendations")
    print("Integration with backtesting engine required for full functionality")
