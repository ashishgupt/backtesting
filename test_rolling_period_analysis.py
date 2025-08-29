#!/usr/bin/env python3
"""
Test script for Rolling Period Analysis functionality

Tests the new Sprint 2, Phase 2 rolling period analysis engine
including API endpoints and core functionality.
"""

import sys
import os
import time
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Add src to path for imports
sys.path.append('/Users/ashish/Claude/backtesting')

def test_api_endpoint(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Test an API endpoint and return the response"""
    base_url = "http://localhost:8006"
    url = f"{base_url}{endpoint}"
    
    print(f"\n🔍 Testing {endpoint}")
    print(f"📤 Request payload: {json.dumps(payload, indent=2, default=str)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Response time: {elapsed_time:.2f}s")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            
            # Print key metrics from the response
            if 'summary' in result:
                summary = result['summary']
                print(f"📈 Average CAGR: {summary['avg_cagr'] * 100:.1f}%")
                print(f"📊 Total windows analyzed: {summary['total_windows']}")
                print(f"🎯 Consistency score: {summary['consistency_score']:.3f}")
                print(f"📉 CAGR range: {summary['min_cagr'] * 100:.1f}% to {summary['max_cagr'] * 100:.1f}%")
                
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return {"error": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"🔥 Request failed: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"🔥 Unexpected error: {e}")
        return {"error": str(e)}


def test_core_functionality():
    """Test the core rolling period analyzer directly"""
    print("🧪 Testing Core Rolling Period Analyzer...")
    
    try:
        from src.core.data_manager import DataManager
        from src.core.portfolio_engine_optimized import OptimizedPortfolioEngine
        from src.core.rolling_period_analyzer import RollingPeriodAnalyzer
        
        # Initialize components
        data_manager = DataManager()
        portfolio_engine = OptimizedPortfolioEngine()
        analyzer = RollingPeriodAnalyzer(portfolio_engine)
        
        # Test portfolio
        allocation = {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1}
        
        print(f"📊 Testing 3-year rolling analysis for allocation: {allocation}")
        start_time = time.time()
        
        # Perform 3-year rolling analysis
        periods, summary = analyzer.analyze_rolling_periods(
            allocation=allocation,
            period_years=3,
            start_date=datetime(2015, 1, 1),
            end_date=datetime(2024, 1, 1)
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"⏱️  Analysis time: {elapsed_time:.2f}s")
        print(f"✅ Generated {len(periods)} rolling windows")
        print(f"📈 Average CAGR: {summary.avg_cagr * 100:.1f}%")
        print(f"📊 CAGR std dev: {summary.cagr_std * 100:.1f}%")
        print(f"🎯 Consistency score: {summary.consistency_score:.3f}")
        print(f"📅 Best period: {summary.best_period.start_date.strftime('%Y-%m-%d')} to {summary.best_period.end_date.strftime('%Y-%m-%d')} ({summary.best_period.cagr * 100:.1f}%)")
        print(f"📅 Worst period: {summary.worst_period.start_date.strftime('%Y-%m-%d')} to {summary.worst_period.end_date.strftime('%Y-%m-%d')} ({summary.worst_period.cagr * 100:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Core functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_health():
    """Test if the API is healthy and ready"""
    print("🏥 Checking API health...")
    
    try:
        response = requests.get("http://localhost:8006/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API Status: {health_data['status']}")
            print(f"💾 Database: {health_data['database']}")
            return health_data['status'] == 'healthy'
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"🔥 API health check failed: {e}")
        return False


def main():
    """Run comprehensive tests for Rolling Period Analysis"""
    print("🚀 Rolling Period Analysis - Test Suite")
    print("=" * 50)
    
    # Check API health first
    if not test_api_health():
        print("\n🛑 API is not healthy. Please start the API server first.")
        return False
    
    # Test core functionality
    print("\n" + "=" * 50)
    if not test_core_functionality():
        print("\n🛑 Core functionality tests failed.")
        return False
    
    # Test API endpoints
    print("\n" + "=" * 50)
    print("🌐 Testing API Endpoints...")
    
    # Test 1: Single period analysis
    single_period_payload = {
        "allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1},
        "period_years": 5,
        "start_date": "2015-01-01T00:00:00Z",
        "end_date": "2024-01-01T00:00:00Z"
    }
    
    result1 = test_api_endpoint("/api/analyze/rolling-periods", single_period_payload)
    if "error" in result1:
        print("🛑 Single period analysis test failed.")
        return False
    
    # Test 2: Multi-period analysis
    multi_period_payload = {
        "allocation": {"VTI": 0.7, "BND": 0.3},
        "period_years_list": [3, 5],
        "start_date": "2015-01-01T00:00:00Z",
        "end_date": "2024-01-01T00:00:00Z"
    }
    
    result2 = test_api_endpoint("/api/analyze/rolling-periods/multi", multi_period_payload)
    if "error" in result2:
        print("🛑 Multi-period analysis test failed.")
        return False
    
    # Test 3: Portfolio comparison
    comparison_payload = {
        "portfolios": {
            "Conservative": {"VTI": 0.3, "BND": 0.7},
            "Balanced": {"VTI": 0.6, "BND": 0.4},
            "Aggressive": {"VTI": 0.8, "VTIAX": 0.2}
        },
        "period_years": 5
    }
    
    result3 = test_api_endpoint("/api/analyze/rolling-periods/compare", comparison_payload)
    if "error" in result3:
        print("🛑 Portfolio comparison test failed.")
        return False
    else:
        # Print ranking results
        if 'ranking' in result3:
            print("\n🏆 Portfolio Ranking:")
            for rank_data in result3['ranking']:
                print(f"  {rank_data['rank']}. {rank_data['portfolio_name']}: "
                      f"{rank_data['avg_cagr']:.1f}% CAGR, "
                      f"{rank_data['avg_sharpe']:.2f} Sharpe")
    
    # Test 4: Examples endpoint
    print(f"\n🔍 Testing /api/analyze/rolling-periods/examples")
    try:
        response = requests.get("http://localhost:8006/api/analyze/rolling-periods/examples")
        if response.status_code == 200:
            examples = response.json()
            print("✅ Examples endpoint working")
            print(f"📚 Available examples: {list(examples.keys())}")
        else:
            print(f"❌ Examples endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"🔥 Examples endpoint error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Rolling Period Analysis - All Tests Complete!")
    print("✅ Sprint 2, Phase 2 Week 4 - Rolling Period Analysis Engine: READY")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
