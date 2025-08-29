#!/usr/bin/env python3
"""
Test Crisis Period Stress Testing and Recovery Analysis

This script tests the new Week 5 functionality:
- Crisis Period Stress Testing
- Recovery Time Analysis  
- Timeline-Aware Risk Recommendations
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime
from src.core.portfolio_engine_optimized import OptimizedPortfolioEngine
from src.core.crisis_period_analyzer import CrisisPeriodAnalyzer
from src.core.recovery_time_analyzer import RecoveryTimeAnalyzer
from src.core.timeline_risk_analyzer import (
    TimelineRiskAnalyzer, InvestorProfile, RiskTolerance, LifeStage
)

def test_crisis_period_analysis():
    """Test crisis period stress testing"""
    print("🔥 Testing Crisis Period Analysis...")
    
    # Initialize engines
    portfolio_engine = OptimizedPortfolioEngine()
    crisis_analyzer = CrisisPeriodAnalyzer(portfolio_engine)
    
    # Test allocation - Balanced portfolio
    allocation = {
        "VTI": 0.60,   # US Total Stock Market
        "VTIAX": 0.20, # International
        "BND": 0.20    # US Bonds
    }
    
    try:
        # Analyze crisis periods
        crisis_results, summary = crisis_analyzer.analyze_crisis_periods(allocation)
        
        print(f"✅ Successfully analyzed {len(crisis_results)} crisis periods")
        print(f"   Average crisis decline: {summary.avg_crisis_decline:.2%}")
        print(f"   Worst crisis decline: {summary.worst_crisis_decline:.2%}")
        print(f"   Overall resilience score: {summary.overall_resilience_score:.1f}/100")
        
        # Print details for each crisis
        for result in crisis_results:
            print(f"   📉 {result.crisis.name}: {result.crisis_decline:.2%} decline, "
                  f"resilience score: {result.resilience_score:.1f}")
            
        return True
        
    except Exception as e:
        print(f"❌ Crisis analysis failed: {e}")
        return False


def test_recovery_time_analysis():
    """Test recovery time analysis"""
    print("\n⏱️ Testing Recovery Time Analysis...")
    
    # Initialize engines
    portfolio_engine = OptimizedPortfolioEngine()
    recovery_analyzer = RecoveryTimeAnalyzer(portfolio_engine)
    
    # Test allocation - Aggressive portfolio
    allocation = {
        "VTI": 0.70,   # US Total Stock Market
        "VTIAX": 0.20, # International
        "VWO": 0.05,   # Emerging Markets
        "BND": 0.05    # US Bonds
    }
    
    try:
        # Analyze recovery patterns
        result = recovery_analyzer.analyze_recovery_patterns(
            allocation=allocation,
            start_date=datetime(2010, 1, 1),
            end_date=datetime(2024, 1, 1),
            min_drawdown_pct=0.10
        )
        
        print(f"✅ Recovery analysis completed")
        print(f"   Major drawdowns analyzed: {len(result.major_drawdowns)}")
        print(f"   Average recovery time: {result.avg_recovery_time_days or 'N/A'} days")
        print(f"   Recovery success rate: {result.recovery_success_rate:.1%}")
        print(f"   Resilience score: {result.resilience_metrics['resilience_score']:.1f}/100")
        
        # Show current drawdown status
        if result.current_drawdown:
            print(f"   ⚠️ Currently in drawdown: {result.current_drawdown.drawdown_pct:.2%}")
        else:
            print(f"   ✅ No current significant drawdown")
            
        return True
        
    except Exception as e:
        print(f"❌ Recovery analysis failed: {e}")
        return False


def test_timeline_risk_recommendations():
    """Test timeline-aware risk recommendations"""
    print("\n🎯 Testing Timeline Risk Recommendations...")
    
    # Initialize engines
    portfolio_engine = OptimizedPortfolioEngine()
    timeline_analyzer = TimelineRiskAnalyzer(portfolio_engine)
    
    # Test investor profile - Young aggressive investor
    investor_profile = InvestorProfile(
        age=28,
        investment_horizon_years=35,
        risk_tolerance=RiskTolerance.AGGRESSIVE,
        life_stage=LifeStage.YOUNG_ACCUMULATOR,
        account_type="401k",
        current_portfolio_value=25000,
        monthly_contribution=800,
        retirement_target_value=1500000
    )
    
    try:
        # Generate recommendations
        result = timeline_analyzer.generate_timeline_recommendation(investor_profile)
        
        print(f"✅ Timeline recommendation generated")
        print(f"   Recommended allocation: {result.recommended_allocation.recommended_allocation}")
        print(f"   Risk level: {result.recommended_allocation.risk_level}")
        print(f"   Expected annual return: {result.recommended_allocation.expected_annual_return:.2%}")
        print(f"   Expected volatility: {result.recommended_allocation.expected_volatility:.2%}")
        print(f"   Confidence score: {result.recommended_allocation.confidence_score:.1f}/100")
        
        # Show milestone projections
        print(f"   Milestone projections:")
        for projection in result.milestone_projections:
            print(f"     Age {projection['age_at_milestone']}: "
                  f"${projection['projected_value']:,.0f}")
        
        # Test scenario analysis
        scenarios = result.scenario_analysis
        print(f"   Scenario analysis:")
        for scenario, data in scenarios.items():
            print(f"     {scenario}: {data['annual_return']:.2%} return, "
                  f"{data['probability']:.0%} probability")
            
        return True
        
    except Exception as e:
        print(f"❌ Timeline recommendation failed: {e}")
        return False


def test_multi_portfolio_comparison():
    """Test comparing multiple portfolios across all analyses"""
    print("\n📊 Testing Multi-Portfolio Comparison...")
    
    # Initialize engines
    portfolio_engine = OptimizedPortfolioEngine()
    crisis_analyzer = CrisisPeriodAnalyzer(portfolio_engine)
    recovery_analyzer = RecoveryTimeAnalyzer(portfolio_engine)
    
    # Test portfolios
    portfolios = {
        "Conservative": {"VTI": 0.30, "BND": 0.70},
        "Balanced": {"VTI": 0.60, "VTIAX": 0.20, "BND": 0.20},
        "Aggressive": {"VTI": 0.50, "VTIAX": 0.30, "VWO": 0.10, "QQQ": 0.10}
    }
    
    try:
        # Compare recovery patterns
        recovery_results = recovery_analyzer.compare_recovery_patterns(portfolios)
        
        print(f"✅ Portfolio comparison completed")
        print(f"   Portfolios analyzed: {len(recovery_results)}")
        
        # Show resilience comparison
        resilience_scores = {}
        for name, result in recovery_results.items():
            score = result.resilience_metrics.get('resilience_score', 0)
            resilience_scores[name] = score
            print(f"   {name}: Resilience score {score:.1f}/100")
        
        # Find best performing portfolio
        best_portfolio = max(resilience_scores.keys(), key=lambda k: resilience_scores[k])
        print(f"   🏆 Most resilient portfolio: {best_portfolio}")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio comparison failed: {e}")
        return False


def run_comprehensive_test():
    """Run comprehensive test of all Week 5 functionality"""
    print("🚀 SPRINT 2, PHASE 2, WEEK 5 - COMPREHENSIVE TESTING")
    print("=" * 60)
    
    tests = [
        ("Crisis Period Analysis", test_crisis_period_analysis),
        ("Recovery Time Analysis", test_recovery_time_analysis), 
        ("Timeline Risk Recommendations", test_timeline_risk_recommendations),
        ("Multi-Portfolio Comparison", test_multi_portfolio_comparison)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 OVERALL: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED - Week 5 functionality ready for deployment!")
    else:
        print("⚠️ Some tests failed - review implementation before deployment")
    
    return passed == len(results)


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
