"""
Test Enhanced Rebalancing Strategy Analysis - Sprint 5 Phase 7

Tests the rebalancing analyzer with realistic portfolio scenarios:
- Balanced portfolio across different rebalancing methods
- Tax-aware analysis for different account types
- Performance comparison and recommendations
- API integration testing

This demonstrates the intellectual honesty approach by showing real costs and trade-offs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import asyncio
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from src.models.base import DatabaseManager
from src.backtesting.rebalancing_analyzer import (
    RebalancingAnalyzer, RebalancingMethod, AccountType
)

def load_test_data():
    """Load historical data for testing"""
    try:
        # Create database connection
        db = DatabaseManager()
        df = db.get_historical_data()
        logger.info(f"✅ Loaded {len(df)} days of historical data")
        return df
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        return None

def test_single_strategy_analysis():
    """Test analysis of a single rebalancing strategy"""
    logger.info("🧪 Testing single strategy analysis...")
    
    # Load data
    data = load_test_data()
    if data is None:
        return False
        
    # Create analyzer
    analyzer = RebalancingAnalyzer(data)
    
    # Test balanced portfolio with quarterly rebalancing in taxable account
    target_allocation = {
        "VTI": 0.30,      # US Total Stock Market
        "VTIAX": 0.20,    # International
        "BND": 0.25,      # US Total Bond Market
        "VNQ": 0.10,      # Real Estate
        "GLD": 0.05,      # Gold
        "VWO": 0.05,      # Emerging Markets
        "QQQ": 0.05       # Tech Growth
    }
    
    try:
        analysis = analyzer.analyze_rebalancing_strategy(
            target_allocation=target_allocation,
            method=RebalancingMethod.QUARTERLY,
            account_type=AccountType.TAXABLE,
            start_date="2014-01-01",
            end_date="2024-01-01",
            initial_value=100000.0,
            annual_contribution=6000.0
        )
        
        logger.info("📊 Single Strategy Analysis Results:")
        logger.info(f"   Method: {analysis.method.value}")
        logger.info(f"   Account Type: {analysis.account_type.value}")
        logger.info(f"   Total Return: {analysis.total_return:.1%}")
        logger.info(f"   Annualized Return: {analysis.annualized_return:.1%}")
        logger.info(f"   Volatility: {analysis.volatility:.1%}")
        logger.info(f"   Sharpe Ratio: {analysis.sharpe_ratio:.3f}")
        logger.info(f"   Max Drawdown: {analysis.max_drawdown:.1%}")
        logger.info(f"   Number of Rebalances: {analysis.num_rebalances}")
        logger.info(f"   Total Transaction Costs: ${analysis.total_transaction_costs:,.2f}")
        logger.info(f"   Total Tax Drag: ${analysis.total_tax_drag:,.2f}")
        logger.info(f"   Total Drag: ${analysis.total_drag:,.2f}")
        logger.info(f"   Cost Efficiency Ratio: {analysis.cost_efficiency_ratio:.2f}")
        
        # Show recent rebalancing events
        if analysis.rebalancing_events:
            logger.info(f"   Recent Rebalancing Events ({len(analysis.rebalancing_events)} total):")
            for event in analysis.rebalancing_events[-3:]:  # Last 3 events
                logger.info(f"     {event.date.strftime('%Y-%m-%d')}: {event.trigger_reason} - "
                          f"Cost: ${event.transaction_cost:.2f}, Tax: ${event.tax_impact:.2f}")
        
        logger.info("✅ Single strategy analysis completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Single strategy analysis failed: {e}")
        return False

def test_strategy_comparison():
    """Test comparison of multiple rebalancing strategies"""
    logger.info("🧪 Testing strategy comparison...")
    
    # Load data
    data = load_test_data()
    if data is None:
        return False
        
    # Create analyzer
    analyzer = RebalancingAnalyzer(data)
    
    # Conservative portfolio for comparison
    target_allocation = {
        "VTI": 0.25,      # US Total Stock Market
        "VTIAX": 0.15,    # International
        "BND": 0.40,      # US Total Bond Market (higher allocation)
        "VNQ": 0.08,      # Real Estate
        "GLD": 0.07,      # Gold
        "VWO": 0.03,      # Emerging Markets
        "QQQ": 0.02       # Tech Growth (minimal)
    }
    
    try:
        # Test multiple account types
        for account_type in [AccountType.TAXABLE, AccountType.TAX_DEFERRED]:
            logger.info(f"🏦 Testing {account_type.value} account...")
            
            # Compare all strategies
            results = analyzer.compare_rebalancing_strategies(
                target_allocation=target_allocation,
                account_type=account_type,
                start_date="2014-01-01",
                end_date="2024-01-01",
                initial_value=100000.0,
                annual_contribution=12000.0  # Higher contributions
            )
            
            if not results:
                logger.error(f"❌ No results for {account_type.value}")
                continue
                
            logger.info(f"📊 Comparison Results for {account_type.value}:")
            logger.info("   Method              | Ann. Return | Volatility | Sharpe | Rebalances | Total Costs")
            logger.info("   -------------------|-------------|------------|---------|-----------|------------")
            
            for method, analysis in results.items():
                logger.info(f"   {method.value:<19} | "
                          f"{analysis.annualized_return:>9.1%} | "
                          f"{analysis.volatility:>8.1%} | "
                          f"{analysis.sharpe_ratio:>6.3f} | "
                          f"{analysis.num_rebalances:>9} | "
                          f"${analysis.total_drag:>9,.0f}")
            
            # Get recommendation
            best_method, explanation = analyzer.recommend_rebalancing_strategy(
                results, account_type
            )
            
            logger.info(f"🏆 Recommended Strategy for {account_type.value}:")
            logger.info(f"   Method: {best_method.value}")
            logger.info(f"   Explanation: {explanation}")
            
        logger.info("✅ Strategy comparison completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Strategy comparison failed: {e}")
        return False

def test_tax_aware_analysis():
    """Test tax-aware rebalancing analysis"""
    logger.info("🧪 Testing tax-aware analysis...")
    
    # Load data
    data = load_test_data() 
    if data is None:
        return False
        
    # Create analyzer
    analyzer = RebalancingAnalyzer(data)
    
    # Growth-oriented portfolio
    target_allocation = {
        "VTI": 0.35,      # US Total Stock Market
        "VTIAX": 0.15,    # International
        "BND": 0.15,      # US Total Bond Market (lower allocation)
        "VNQ": 0.15,      # Real Estate
        "GLD": 0.05,      # Gold
        "VWO": 0.10,      # Emerging Markets
        "QQQ": 0.05       # Tech Growth
    }
    
    try:
        # Compare new money only vs traditional rebalancing in taxable account
        methods_to_compare = [
            RebalancingMethod.NEW_MONEY_ONLY,
            RebalancingMethod.QUARTERLY,
            RebalancingMethod.THRESHOLD_10_PERCENT
        ]
        
        results = {}
        for method in methods_to_compare:
            analysis = analyzer.analyze_rebalancing_strategy(
                target_allocation=target_allocation,
                method=method,
                account_type=AccountType.TAXABLE,
                start_date="2016-01-01",  # Shorter period for stability
                end_date="2024-01-01",
                initial_value=50000.0,
                annual_contribution=18000.0  # Max IRA contribution equivalent
            )
            results[method] = analysis
        
        logger.info("📊 Tax-Aware Analysis - Taxable Account:")
        logger.info("   Method              | Ann. Return | Tax Drag | Total Costs | Net Benefit")
        logger.info("   -------------------|-------------|----------|-------------|------------")
        
        for method, analysis in results.items():
            net_benefit = analysis.annualized_return - (analysis.total_drag / analysis.performance_timeline.iloc[0]['portfolio_value']) / 8  # Annualized cost impact
            logger.info(f"   {method.value:<19} | "
                      f"{analysis.annualized_return:>9.1%} | "
                      f"${analysis.total_tax_drag:>7,.0f} | "
                      f"${analysis.total_drag:>9,.0f} | "
                      f"{net_benefit:>9.1%}")
        
        # Highlight new money benefits
        new_money_analysis = results[RebalancingMethod.NEW_MONEY_ONLY]
        quarterly_analysis = results[RebalancingMethod.QUARTERLY]
        
        tax_savings = quarterly_analysis.total_tax_drag - new_money_analysis.total_tax_drag
        cost_savings = quarterly_analysis.total_drag - new_money_analysis.total_drag
        
        logger.info(f"💰 New Money Strategy Benefits:")
        logger.info(f"   Tax Savings vs Quarterly: ${tax_savings:,.2f}")
        logger.info(f"   Total Cost Savings: ${cost_savings:,.2f}")
        logger.info(f"   Annual Benefit: ~{(cost_savings / (8 * 50000)) * 100:.2f}% of initial portfolio")
        
        logger.info("✅ Tax-aware analysis completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Tax-aware analysis failed: {e}")
        return False

def test_api_integration():
    """Test API integration (if server is running)"""
    logger.info("🧪 Testing API integration...")
    
    try:
        import requests
        import time
        
        base_url = "http://localhost:8007"
        
        # Test info endpoint
        response = requests.get(f"{base_url}/api/rebalancing/info", timeout=10)
        if response.status_code == 200:
            info = response.json()
            logger.info(f"✅ API Info endpoint working - {len(info['available_methods'])} methods available")
        else:
            logger.warning(f"⚠️ API Info endpoint failed: {response.status_code}")
            return False
        
        # Test single strategy analysis
        request_data = {
            "target_allocation": {
                "VTI": 0.30,
                "VTIAX": 0.20,
                "BND": 0.25,
                "VNQ": 0.10,
                "GLD": 0.05,
                "VWO": 0.05,
                "QQQ": 0.05
            },
            "method": "quarterly",
            "account_type": "taxable",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "initial_value": 50000.0,
            "annual_contribution": 6000.0
        }
        
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/rebalancing/analyze-strategy",
            json=request_data,
            timeout=30
        )
        analysis_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Single strategy API analysis completed in {analysis_time:.1f} seconds")
            logger.info(f"   Return: {result['performance']['annualized_return']:.1%}")
            logger.info(f"   Rebalances: {result['rebalancing_stats']['num_rebalances']}")
            logger.info(f"   Total Costs: ${result['rebalancing_stats']['total_drag']:.0f}")
        else:
            logger.error(f"❌ Single strategy API failed: {response.status_code} - {response.text}")
            return False
        
        # Test comparison endpoint (shorter time period for speed)
        comparison_request = {
            "target_allocation": {
                "VTI": 0.40,
                "VTIAX": 0.20,
                "BND": 0.25,
                "VNQ": 0.15
            },
            "account_type": "tax_deferred",
            "start_date": "2020-01-01", 
            "end_date": "2024-01-01",
            "initial_value": 100000.0,
            "methods": ["quarterly", "annual", "new_money_only"]
        }
        
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/rebalancing/compare-strategies",
            json=comparison_request,
            timeout=60
        )
        comparison_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Strategy comparison API completed in {comparison_time:.1f} seconds")
            logger.info(f"   Recommended: {result['recommendation']['method']}")
            logger.info(f"   Strategies compared: {len(result['comparison_results'])}")
        else:
            logger.error(f"❌ Strategy comparison API failed: {response.status_code} - {response.text}")
            return False
        
        logger.info("✅ API integration tests completed successfully!")
        return True
        
    except requests.RequestException as e:
        logger.warning(f"⚠️ API server not running or not accessible: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ API integration test failed: {e}")
        return False

def main():
    """Run all rebalancing analyzer tests"""
    logger.info("🚀 Starting Enhanced Rebalancing Strategy Analysis Tests")
    logger.info("=" * 70)
    
    tests = [
        ("Single Strategy Analysis", test_single_strategy_analysis),
        ("Strategy Comparison", test_strategy_comparison), 
        ("Tax-Aware Analysis", test_tax_aware_analysis),
        ("API Integration", test_api_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name}...")
        logger.info("-" * 50)
        
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name} CRASHED: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Enhanced Rebalancing Analysis is ready!")
        logger.info("\n📋 Next Steps:")
        logger.info("   1. Start the API server: python -m src.api.main")
        logger.info("   2. Test the endpoints at http://localhost:8007/docs")
        logger.info("   3. Build the web interface for rebalancing analysis")
        logger.info("   4. Move to Phase 8: Market Regime Awareness Foundation")
    else:
        logger.error("❌ Some tests failed - review the errors above")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
