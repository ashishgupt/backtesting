"""
Timeline-Aware Risk Analysis Engine for Portfolio Backtesting

This module provides timeline-aware risk recommendations based on investment horizon,
age, and risk tolerance to optimize portfolio allocations for different life stages.
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .portfolio_engine_optimized import OptimizedPortfolioEngine
from .crisis_period_analyzer import CrisisPeriodAnalyzer
from .recovery_time_analyzer import RecoveryTimeAnalyzer


class RiskTolerance(str, Enum):
    """Risk tolerance levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate" 
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


class LifeStage(str, Enum):
    """Life stage categories"""
    YOUNG_ACCUMULATOR = "young_accumulator"  # 20s-30s
    MID_CAREER = "mid_career"  # 40s-50s
    PRE_RETIREMENT = "pre_retirement"  # 55-65
    RETIREMENT = "retirement"  # 65+


@dataclass
class InvestorProfile:
    """Complete investor profile for timeline-aware recommendations"""
    age: int
    investment_horizon_years: int
    risk_tolerance: RiskTolerance
    life_stage: LifeStage
    account_type: str = "taxable"  # taxable, 401k, ira, roth_ira
    current_portfolio_value: Optional[float] = None
    monthly_contribution: Optional[float] = None
    retirement_target_value: Optional[float] = None


@dataclass
class TimelineRiskRecommendation:
    """Risk-adjusted portfolio recommendation based on timeline"""
    recommended_allocation: Dict[str, float]
    allocation_rationale: str
    risk_level: str
    expected_annual_return: float
    expected_volatility: float
    max_drawdown_expectation: float
    recovery_time_expectation: int  # days
    rebalancing_frequency: str
    key_risks: List[str]
    timeline_specific_notes: List[str]
    confidence_score: float  # 0-100


@dataclass
class TimelineAnalysisResult:
    """Complete timeline-aware analysis result"""
    investor_profile: InvestorProfile
    current_allocation_analysis: Optional[Dict[str, Any]]
    recommended_allocation: TimelineRiskRecommendation
    scenario_analysis: Dict[str, Dict[str, float]]  # bull/bear/normal scenarios
    milestone_projections: List[Dict[str, Any]]  # 5, 10, 20 year projections
    adjustment_triggers: List[str]  # When to rebalance/adjust


class TimelineRiskAnalyzer:
    """
    Provides timeline-aware risk recommendations based on:
    - Investment horizon and age
    - Risk tolerance and life stage
    - Historical performance patterns
    - Crisis resilience analysis
    - Recovery time expectations
    """
    
    # Age-based allocation guidelines (stock percentage ranges)
    AGE_ALLOCATION_GUIDELINES = {
        LifeStage.YOUNG_ACCUMULATOR: {"min_stocks": 0.70, "max_stocks": 0.95, "target_stocks": 0.85},
        LifeStage.MID_CAREER: {"min_stocks": 0.50, "max_stocks": 0.80, "target_stocks": 0.65},
        LifeStage.PRE_RETIREMENT: {"min_stocks": 0.30, "max_stocks": 0.60, "target_stocks": 0.45},
        LifeStage.RETIREMENT: {"min_stocks": 0.20, "max_stocks": 0.50, "target_stocks": 0.35}
    }
    
    # Risk tolerance modifiers (adjustments to base allocation)
    RISK_MODIFIERS = {
        RiskTolerance.CONSERVATIVE: {"stock_adjustment": -0.15, "volatility_tolerance": 0.12},
        RiskTolerance.MODERATE: {"stock_adjustment": 0.0, "volatility_tolerance": 0.16},
        RiskTolerance.AGGRESSIVE: {"stock_adjustment": 0.10, "volatility_tolerance": 0.20},
        RiskTolerance.VERY_AGGRESSIVE: {"stock_adjustment": 0.20, "volatility_tolerance": 0.25}
    }
    
    def __init__(self, portfolio_engine: OptimizedPortfolioEngine):
        """
        Initialize with portfolio analysis engines
        
        Args:
            portfolio_engine: OptimizedPortfolioEngine for backtesting
        """
        self.portfolio_engine = portfolio_engine
        self.crisis_analyzer = CrisisPeriodAnalyzer(portfolio_engine)
        self.recovery_analyzer = RecoveryTimeAnalyzer(portfolio_engine)
        
    def generate_timeline_recommendation(
        self,
        investor_profile: InvestorProfile,
        current_allocation: Optional[Dict[str, float]] = None
    ) -> TimelineAnalysisResult:
        """
        Generate comprehensive timeline-aware investment recommendation
        
        Args:
            investor_profile: Complete investor profile
            current_allocation: Current portfolio allocation (optional)
            
        Returns:
            TimelineAnalysisResult with recommendations and analysis
        """
        # Analyze current allocation if provided
        current_analysis = None
        if current_allocation:
            current_analysis = self._analyze_current_allocation(
                current_allocation, investor_profile
            )
        
        # Generate recommended allocation
        recommended_allocation = self._generate_recommended_allocation(investor_profile)
        
        # Run scenario analysis
        scenario_analysis = self._run_scenario_analysis(
            recommended_allocation.recommended_allocation, investor_profile
        )
        
        # Generate milestone projections
        milestone_projections = self._generate_milestone_projections(
            recommended_allocation.recommended_allocation, investor_profile
        )
        
        # Identify adjustment triggers
        adjustment_triggers = self._identify_adjustment_triggers(investor_profile)
        
        return TimelineAnalysisResult(
            investor_profile=investor_profile,
            current_allocation_analysis=current_analysis,
            recommended_allocation=recommended_allocation,
            scenario_analysis=scenario_analysis,
            milestone_projections=milestone_projections,
            adjustment_triggers=adjustment_triggers
        )
    
    def _determine_life_stage(self, age: int) -> LifeStage:
        """Determine life stage based on age"""
        if age < 40:
            return LifeStage.YOUNG_ACCUMULATOR
        elif age < 55:
            return LifeStage.MID_CAREER
        elif age < 65:
            return LifeStage.PRE_RETIREMENT
        else:
            return LifeStage.RETIREMENT
    
    def _generate_recommended_allocation(
        self,
        profile: InvestorProfile
    ) -> TimelineRiskRecommendation:
        """Generate recommended portfolio allocation based on profile"""
        
        # Get base allocation guidelines for life stage
        guidelines = self.AGE_ALLOCATION_GUIDELINES[profile.life_stage]
        risk_modifier = self.RISK_MODIFIERS[profile.risk_tolerance]
        
        # Calculate target stock allocation
        base_stock_pct = guidelines["target_stocks"]
        adjusted_stock_pct = base_stock_pct + risk_modifier["stock_adjustment"]
        
        # Apply bounds
        min_stocks = max(0.1, guidelines["min_stocks"] + risk_modifier["stock_adjustment"])
        max_stocks = min(0.95, guidelines["max_stocks"] + risk_modifier["stock_adjustment"])
        final_stock_pct = max(min_stocks, min(max_stocks, adjusted_stock_pct))
        
        # Adjust for investment horizon
        horizon_adjustment = self._calculate_horizon_adjustment(
            profile.investment_horizon_years, profile.age
        )
        final_stock_pct += horizon_adjustment
        final_stock_pct = max(0.1, min(0.95, final_stock_pct))
        
        # Build recommended allocation
        recommended_allocation = self._build_allocation(
            stock_pct=final_stock_pct,
            profile=profile
        )
        
        # Backtest recommended allocation
        backtest_result = self.portfolio_engine.backtest_portfolio(
            allocation=recommended_allocation,
            start_date="2010-01-01",
            end_date="2024-01-01"
        )
        
        # Analyze expected metrics
        metrics = backtest_result['performance_metrics']
        expected_return = self._safe_float(metrics.get('cagr', 0.08))
        expected_volatility = self._safe_float(metrics.get('volatility', 0.15))
        max_drawdown = abs(self._safe_float(metrics.get('max_drawdown', -0.20)))
        
        # Estimate recovery time
        recovery_time = self._estimate_recovery_time(recommended_allocation)
        
        # Generate rationale and risk assessment
        rationale = self._generate_allocation_rationale(profile, final_stock_pct)
        key_risks = self._identify_key_risks(profile, recommended_allocation)
        timeline_notes = self._generate_timeline_notes(profile)
        
        # Rebalancing frequency recommendation
        rebalancing_freq = self._recommend_rebalancing_frequency(profile)
        
        # Risk level assessment
        risk_level = self._assess_risk_level(expected_volatility, max_drawdown)
        
        # Confidence score
        confidence_score = self._calculate_confidence_score(
            profile, recommended_allocation, expected_volatility
        )
        
        return TimelineRiskRecommendation(
            recommended_allocation=recommended_allocation,
            allocation_rationale=rationale,
            risk_level=risk_level,
            expected_annual_return=expected_return,
            expected_volatility=expected_volatility,
            max_drawdown_expectation=max_drawdown,
            recovery_time_expectation=recovery_time,
            rebalancing_frequency=rebalancing_freq,
            key_risks=key_risks,
            timeline_specific_notes=timeline_notes,
            confidence_score=confidence_score
        )
    
    def _calculate_horizon_adjustment(self, horizon_years: int, age: int) -> float:
        """Calculate stock allocation adjustment based on investment horizon"""
        
        # Longer horizons can tolerate more risk
        if horizon_years >= 30:
            return 0.10  # +10% stocks for very long horizon
        elif horizon_years >= 20:
            return 0.05  # +5% stocks for long horizon  
        elif horizon_years >= 10:
            return 0.0   # No adjustment for medium horizon
        elif horizon_years >= 5:
            return -0.05 # -5% stocks for shorter horizon
        else:
            return -0.10 # -10% stocks for very short horizon
    
    def _build_allocation(self, stock_pct: float, profile: InvestorProfile) -> Dict[str, float]:
        """Build specific asset allocation based on stock percentage"""
        
        bond_pct = 1.0 - stock_pct
        
        # For young accumulators with long horizons, include more growth assets
        if profile.life_stage == LifeStage.YOUNG_ACCUMULATOR and profile.investment_horizon_years > 20:
            allocation = {
                "VTI": stock_pct * 0.40,      # US Total Market
                "VTIAX": stock_pct * 0.30,    # International 
                "VWO": stock_pct * 0.15,      # Emerging Markets
                "QQQ": stock_pct * 0.10,      # Technology Growth
                "VNQ": stock_pct * 0.05,      # REITs
                "BND": bond_pct                # Bonds
            }
        # For mid-career, more balanced approach
        elif profile.life_stage == LifeStage.MID_CAREER:
            allocation = {
                "VTI": stock_pct * 0.50,      # US Total Market
                "VTIAX": stock_pct * 0.30,    # International
                "VWO": stock_pct * 0.10,      # Emerging Markets
                "VNQ": stock_pct * 0.05,      # REITs  
                "GLD": stock_pct * 0.05,      # Gold hedge
                "BND": bond_pct                # Bonds
            }
        # For pre-retirement and retirement, focus on stability
        else:
            allocation = {
                "VTI": stock_pct * 0.60,      # US Total Market
                "VTIAX": stock_pct * 0.25,    # International
                "VNQ": stock_pct * 0.10,      # REITs
                "GLD": stock_pct * 0.05,      # Gold hedge
                "BND": bond_pct                # Bonds
            }
        
        # Ensure allocation sums to 1.0
        total = sum(allocation.values())
        if total != 1.0:
            # Adjust largest component
            largest_asset = max(allocation.keys(), key=lambda k: allocation[k])
            allocation[largest_asset] += (1.0 - total)
        
        # Remove very small allocations (< 1%)
        allocation = {k: v for k, v in allocation.items() if v >= 0.01}
        
        return allocation
    
    def _analyze_current_allocation(
        self,
        allocation: Dict[str, float], 
        profile: InvestorProfile
    ) -> Dict[str, Any]:
        """Analyze current portfolio allocation relative to profile"""
        
        # Backtest current allocation
        backtest_result = self.portfolio_engine.backtest_portfolio(
            allocation=allocation,
            start_date="2010-01-01", 
            end_date="2024-01-01"
        )
        
        # Calculate stock/bond percentages
        stock_assets = {"VTI", "VTIAX", "VWO", "QQQ", "VNQ"}
        current_stock_pct = sum(allocation.get(asset, 0) for asset in stock_assets if asset in allocation)
        current_bond_pct = allocation.get("BND", 0)
        
        # Compare to guidelines
        guidelines = self.AGE_ALLOCATION_GUIDELINES[profile.life_stage]
        risk_modifier = self.RISK_MODIFIERS[profile.risk_tolerance]
        
        target_stock_range = {
            "min": guidelines["min_stocks"] + risk_modifier["stock_adjustment"],
            "max": guidelines["max_stocks"] + risk_modifier["stock_adjustment"],
            "target": guidelines["target_stocks"] + risk_modifier["stock_adjustment"]
        }
        
        # Risk assessment
        metrics = backtest_result['performance_metrics']
        current_volatility = self._safe_float(metrics.get('volatility', 0.15))
        target_volatility = risk_modifier["volatility_tolerance"]
        
        alignment_score = self._calculate_alignment_score(
            current_stock_pct, target_stock_range, current_volatility, target_volatility
        )
        
        return {
            "current_performance": metrics,
            "asset_allocation": {
                "stock_percentage": current_stock_pct,
                "bond_percentage": current_bond_pct,
                "other_percentage": 1.0 - current_stock_pct - current_bond_pct
            },
            "target_comparison": {
                "target_stock_range": target_stock_range,
                "stock_allocation_status": self._assess_allocation_status(current_stock_pct, target_stock_range),
                "volatility_status": self._assess_volatility_status(current_volatility, target_volatility)
            },
            "alignment_score": alignment_score,
            "recommendations": self._generate_current_allocation_feedback(
                current_stock_pct, target_stock_range, profile
            )
        }
    
    def _run_scenario_analysis(
        self,
        allocation: Dict[str, float],
        profile: InvestorProfile
    ) -> Dict[str, Dict[str, float]]:
        """Run bull/bear/normal market scenario analysis"""
        
        scenarios = {}
        
        # Normal scenario (historical average)
        normal_result = self.portfolio_engine.backtest_portfolio(
            allocation=allocation,
            start_date="2010-01-01",
            end_date="2024-01-01"
        )
        scenarios["normal_market"] = {
            "annual_return": self._safe_float(normal_result['performance_metrics'].get('cagr', 0.08)),
            "volatility": self._safe_float(normal_result['performance_metrics'].get('volatility', 0.15)),
            "max_drawdown": self._safe_float(normal_result['performance_metrics'].get('max_drawdown', -0.20)),
            "probability": 0.60
        }
        
        # Bull scenario (top 25% historical periods)
        scenarios["bull_market"] = {
            "annual_return": scenarios["normal_market"]["annual_return"] * 1.5,
            "volatility": scenarios["normal_market"]["volatility"] * 0.8,
            "max_drawdown": scenarios["normal_market"]["max_drawdown"] * 0.5,
            "probability": 0.25
        }
        
        # Bear scenario (crisis periods)
        bear_results, _ = self.crisis_analyzer.analyze_crisis_periods(allocation)
        if bear_results:
            avg_crisis_decline = np.mean([r.crisis_decline for r in bear_results])
            scenarios["bear_market"] = {
                "annual_return": avg_crisis_decline,
                "volatility": scenarios["normal_market"]["volatility"] * 1.5,
                "max_drawdown": avg_crisis_decline,
                "probability": 0.15
            }
        else:
            scenarios["bear_market"] = {
                "annual_return": -0.20,
                "volatility": scenarios["normal_market"]["volatility"] * 1.5,
                "max_drawdown": -0.35,
                "probability": 0.15
            }
        
        return scenarios
    
    def _generate_milestone_projections(
        self,
        allocation: Dict[str, float],
        profile: InvestorProfile
    ) -> List[Dict[str, Any]]:
        """Generate portfolio value projections for key milestones"""
        
        projections = []
        
        # Get expected return
        backtest_result = self.portfolio_engine.backtest_portfolio(
            allocation=allocation,
            start_date="2010-01-01",
            end_date="2024-01-01"
        )
        expected_return = self._safe_float(backtest_result['performance_metrics'].get('cagr', 0.08))
        
        # Starting values
        current_value = profile.current_portfolio_value or 10000  # Default $10k
        monthly_contrib = profile.monthly_contribution or 500     # Default $500/month
        
        # Project for 5, 10, 15, 20 year milestones
        for years in [5, 10, 15, 20]:
            if years <= profile.investment_horizon_years:
                
                # Calculate future value with contributions
                months = years * 12
                monthly_return = (1 + expected_return) ** (1/12) - 1
                
                # Future value of current portfolio
                fv_current = current_value * ((1 + expected_return) ** years)
                
                # Future value of monthly contributions (annuity)
                if monthly_return > 0:
                    fv_contributions = monthly_contrib * (
                        ((1 + monthly_return) ** months - 1) / monthly_return
                    )
                else:
                    fv_contributions = monthly_contrib * months
                
                total_projected_value = fv_current + fv_contributions
                
                # Age at milestone
                age_at_milestone = profile.age + years
                
                projections.append({
                    "years_from_now": years,
                    "age_at_milestone": age_at_milestone,
                    "projected_value": total_projected_value,
                    "total_contributions": monthly_contrib * months,
                    "growth_from_returns": total_projected_value - current_value - (monthly_contrib * months),
                    "purchasing_power": total_projected_value / ((1.03) ** years),  # Assume 3% inflation
                    "milestone_notes": self._generate_milestone_notes(age_at_milestone, total_projected_value)
                })
        
        return projections
    
    def _estimate_recovery_time(self, allocation: Dict[str, float]) -> int:
        """Estimate expected recovery time from major drawdowns"""
        try:
            recovery_result = self.recovery_analyzer.analyze_recovery_patterns(allocation)
            return int(recovery_result.avg_recovery_time_days or 365)
        except:
            # Default estimate based on allocation
            stock_pct = sum(allocation.get(asset, 0) for asset in ["VTI", "VTIAX", "VWO", "QQQ"])
            if stock_pct > 0.8:
                return 450  # 15 months for aggressive
            elif stock_pct > 0.6:
                return 365  # 12 months for balanced
            else:
                return 270  # 9 months for conservative
    
    def _generate_allocation_rationale(self, profile: InvestorProfile, stock_pct: float) -> str:
        """Generate human-readable rationale for allocation"""
        
        rationale_parts = []
        
        # Age and life stage reasoning
        rationale_parts.append(
            f"At age {profile.age} ({profile.life_stage.value.replace('_', ' ').title()}), "
            f"a {stock_pct:.0%} stock allocation balances growth potential with risk management."
        )
        
        # Risk tolerance reasoning
        risk_desc = {
            RiskTolerance.CONSERVATIVE: "conservative approach focuses on capital preservation",
            RiskTolerance.MODERATE: "moderate risk approach balances growth and stability", 
            RiskTolerance.AGGRESSIVE: "aggressive approach maximizes growth potential",
            RiskTolerance.VERY_AGGRESSIVE: "very aggressive approach prioritizes maximum returns"
        }
        rationale_parts.append(f"Your {risk_desc[profile.risk_tolerance]}.")
        
        # Timeline reasoning
        if profile.investment_horizon_years >= 20:
            rationale_parts.append(
                f"With {profile.investment_horizon_years} years until retirement, "
                "you can weather market volatility for higher long-term returns."
            )
        elif profile.investment_horizon_years >= 10:
            rationale_parts.append(
                f"Your {profile.investment_horizon_years}-year timeline allows for moderate risk-taking "
                "while maintaining some stability."
            )
        else:
            rationale_parts.append(
                f"With only {profile.investment_horizon_years} years remaining, "
                "capital preservation becomes more important than aggressive growth."
            )
        
        return " ".join(rationale_parts)
    
    def _identify_key_risks(self, profile: InvestorProfile, allocation: Dict[str, float]) -> List[str]:
        """Identify key risks for the recommended allocation"""
        
        risks = []
        
        stock_pct = sum(allocation.get(asset, 0) for asset in ["VTI", "VTIAX", "VWO", "QQQ"])
        
        # Market risk
        if stock_pct > 0.7:
            risks.append("High market volatility risk due to significant stock allocation")
        
        # Concentration risk
        us_pct = allocation.get("VTI", 0) + allocation.get("QQQ", 0)
        if us_pct > 0.6:
            risks.append("US market concentration risk")
        
        # Age-specific risks
        if profile.life_stage == LifeStage.PRE_RETIREMENT or profile.life_stage == LifeStage.RETIREMENT:
            risks.append("Sequence of returns risk near/in retirement")
        
        # Timeline risk
        if profile.investment_horizon_years < 10 and stock_pct > 0.5:
            risks.append("Short timeline may not allow recovery from market downturns")
        
        # Inflation risk
        if stock_pct < 0.4:
            risks.append("Inflation risk due to conservative allocation")
        
        return risks
    
    def _generate_timeline_notes(self, profile: InvestorProfile) -> List[str]:
        """Generate timeline-specific recommendations and notes"""
        
        notes = []
        
        # Life stage specific notes
        if profile.life_stage == LifeStage.YOUNG_ACCUMULATOR:
            notes.extend([
                "Prioritize tax-advantaged account contributions (401k, IRA)",
                "Consider increasing stock allocation as income grows",
                "Rebalance annually or when allocation drifts >5%"
            ])
        elif profile.life_stage == LifeStage.MID_CAREER:
            notes.extend([
                "Begin gradual shift toward more conservative allocation",
                "Consider tax-loss harvesting in taxable accounts",
                "Evaluate allocation annually as retirement approaches"
            ])
        elif profile.life_stage == LifeStage.PRE_RETIREMENT:
            notes.extend([
                "Begin reducing equity exposure 5-10 years before retirement",
                "Build cash/bond ladder for early retirement years",
                "Consider Roth conversions in low-income years"
            ])
        else:  # RETIREMENT
            notes.extend([
                "Maintain some equity exposure for inflation protection",
                "Use bond/cash for near-term expenses (1-3 years)",
                "Consider bucket strategy for retirement income"
            ])
        
        # Timeline specific
        if profile.investment_horizon_years < 5:
            notes.append("Consider more conservative allocation due to short timeline")
        elif profile.investment_horizon_years > 30:
            notes.append("Long timeline allows for more aggressive growth strategy")
        
        return notes
    
    def _recommend_rebalancing_frequency(self, profile: InvestorProfile) -> str:
        """Recommend rebalancing frequency based on profile"""
        
        if profile.life_stage == LifeStage.YOUNG_ACCUMULATOR:
            return "Annual or when allocation drifts >10%"
        elif profile.life_stage == LifeStage.MID_CAREER:
            return "Semi-annual or when allocation drifts >7%"
        else:
            return "Quarterly or when allocation drifts >5%"
    
    def _assess_risk_level(self, volatility: float, max_drawdown: float) -> str:
        """Assess overall risk level of allocation"""
        
        if volatility > 0.20 or abs(max_drawdown) > 0.30:
            return "High Risk"
        elif volatility > 0.15 or abs(max_drawdown) > 0.20:
            return "Moderate-High Risk"
        elif volatility > 0.10 or abs(max_drawdown) > 0.15:
            return "Moderate Risk"
        else:
            return "Conservative Risk"
    
    def _calculate_confidence_score(
        self,
        profile: InvestorProfile,
        allocation: Dict[str, float], 
        volatility: float
    ) -> float:
        """Calculate confidence score for recommendation (0-100)"""
        
        score = 80.0  # Base confidence
        
        # Adjust for risk tolerance alignment
        target_volatility = self.RISK_MODIFIERS[profile.risk_tolerance]["volatility_tolerance"]
        vol_diff = abs(volatility - target_volatility)
        if vol_diff < 0.02:
            score += 10  # Very well aligned
        elif vol_diff < 0.05:
            score += 5   # Well aligned
        else:
            score -= 5   # Poorly aligned
        
        # Adjust for timeline appropriateness
        if profile.investment_horizon_years >= 10:
            score += 5  # Good timeline for recommendations
        elif profile.investment_horizon_years < 5:
            score -= 10  # Challenging short timeline
        
        # Adjust for diversification
        if len(allocation) >= 5:
            score += 5  # Well diversified
        elif len(allocation) <= 3:
            score -= 5  # Limited diversification
        
        return max(0.0, min(100.0, score))
    
    def _calculate_alignment_score(
        self,
        current_stock_pct: float,
        target_range: Dict[str, float],
        current_vol: float,
        target_vol: float
    ) -> float:
        """Calculate how well current allocation aligns with target (0-100)"""
        
        # Stock allocation alignment (60% weight)
        if target_range["min"] <= current_stock_pct <= target_range["max"]:
            stock_score = 60.0
        else:
            distance = min(
                abs(current_stock_pct - target_range["min"]),
                abs(current_stock_pct - target_range["max"])
            )
            stock_score = max(0, 60 - (distance * 300))  # Penalize deviation
        
        # Volatility alignment (40% weight) 
        vol_diff = abs(current_vol - target_vol)
        vol_score = max(0, 40 - (vol_diff * 200))
        
        return stock_score + vol_score
    
    def _assess_allocation_status(self, current: float, target_range: Dict[str, float]) -> str:
        """Assess current allocation relative to target range"""
        
        if current < target_range["min"] - 0.1:
            return "Too Conservative"
        elif current > target_range["max"] + 0.1:
            return "Too Aggressive"
        elif target_range["min"] <= current <= target_range["max"]:
            return "Appropriate"
        else:
            return "Slightly Off Target"
    
    def _assess_volatility_status(self, current_vol: float, target_vol: float) -> str:
        """Assess current volatility relative to target"""
        
        if current_vol > target_vol + 0.05:
            return "Higher Risk Than Target"
        elif current_vol < target_vol - 0.05:
            return "Lower Risk Than Target"
        else:
            return "Appropriate Risk Level"
    
    def _generate_current_allocation_feedback(
        self,
        current_stock_pct: float,
        target_range: Dict[str, float],
        profile: InvestorProfile
    ) -> List[str]:
        """Generate feedback on current allocation"""
        
        feedback = []
        
        if current_stock_pct < target_range["min"] - 0.05:
            feedback.append("Consider increasing stock allocation for better long-term growth")
        elif current_stock_pct > target_range["max"] + 0.05:
            feedback.append("Consider reducing risk by increasing bond allocation")
        else:
            feedback.append("Current allocation is reasonably appropriate for your profile")
        
        return feedback
    
    def _generate_milestone_notes(self, age: int, projected_value: float) -> List[str]:
        """Generate notes for milestone projections"""
        
        notes = []
        
        if age >= 65:
            notes.append("Traditional retirement age reached")
            if projected_value >= 1000000:
                notes.append("Millionaire status achieved")
        elif age >= 59.5:
            notes.append("Penalty-free 401(k)/IRA withdrawals available")
        elif age >= 50:
            notes.append("Catch-up contribution eligibility begins")
        
        return notes
    
    def _identify_adjustment_triggers(self, profile: InvestorProfile) -> List[str]:
        """Identify when portfolio should be adjusted"""
        
        triggers = []
        
        # Age-based triggers
        milestone_ages = [50, 55, 59.5, 62, 65, 70]
        for milestone in milestone_ages:
            years_to_milestone = milestone - profile.age
            if 0 < years_to_milestone <= 5:
                triggers.append(f"Review allocation when you reach age {milestone}")
        
        # Life event triggers
        triggers.extend([
            "Major income change (promotion, job loss)",
            "Marriage or divorce",
            "Birth of children",
            "Home purchase or major expense",
            "Inheritance or windfall"
        ])
        
        # Market-based triggers
        triggers.extend([
            "Market decline >20% (bear market)",
            "Allocation drift >10% from target",
            "Major economic regime change"
        ])
        
        return triggers
    
    def _safe_float(self, value) -> float:
        """Convert to safe float that can be JSON serialized"""
        if value is None or np.isnan(value) or np.isinf(value):
            return 0.0
        return float(value)
