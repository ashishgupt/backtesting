#!/usr/bin/env python3
"""
Test script to verify the APIs used by the guided dashboard are working correctly
"""

import requests
import json
import time

# API base URL
API_BASE = "http://localhost:8007"

# Test portfolio allocation
test_allocation = {
    "VTI": 0.4,
    "VTIAX": 0.3, 
    "BND": 0.2,
    "VNQ": 0.1
}

def test_portfolio_analysis():
    """Test the portfolio analysis endpoint"""
    print("🧪 Testing portfolio analysis API...")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/backtest/portfolio",
            headers={"Content-Type": "application/json"},
            json={
                "allocation": {
                    "allocation": test_allocation
                },
                "start_date": "2015-01-01",
                "end_date": "2024-12-31"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Portfolio analysis successful!")
            print(f"   CAGR: {data.get('metrics', {}).get('cagr', 0)*100:.2f}%")
            print(f"   Sharpe: {data.get('metrics', {}).get('sharpe_ratio', 0):.2f}")
            return True
        else:
            print(f"❌ Portfolio analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Portfolio analysis error: {e}")
        return False

def test_stress_test():
    """Test the stress test endpoint"""
    print("🧪 Testing stress test API...")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/analyze/stress-test",
            headers={"Content-Type": "application/json"},
            json={
                "allocation": test_allocation,
                "crisis_periods": ['2008-financial-crisis', '2020-covid-crash', '2022-bear-market']
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stress test successful!")
            print(f"   Number of crises analyzed: {len(data.get('crisis_analysis', []))}")
            return True
        else:
            print(f"❌ Stress test failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Stress test error: {e}")
        return False

def test_rebalancing():
    """Test the rebalancing analysis endpoint"""
    print("🧪 Testing rebalancing analysis API...")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/rebalancing/analyze-strategy",
            headers={"Content-Type": "application/json"},
            json={
                "target_allocation": test_allocation,
                "method": "quarterly",
                "account_type": "taxable",
                "start_date": "2020-01-01",
                "end_date": "2024-12-31",
                "initial_value": 100000.0,
                "annual_contribution": 0.0
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Rebalancing analysis successful!")
            print(f"   Analysis completed for allocation: {list(test_allocation.keys())}")
            return True
        else:
            print(f"❌ Rebalancing analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Rebalancing analysis error: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 Testing Guided Dashboard APIs")
    print("=" * 50)
    
    tests = [
        test_portfolio_analysis,
        test_stress_test,
        test_rebalancing
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
        time.sleep(1)  # Brief pause between tests
    
    print("=" * 50)
    print(f"📊 Test Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All APIs are working correctly!")
        return True
    else:
        print("⚠️  Some APIs have issues - check the guided dashboard")
        return False

if __name__ == "__main__":
    main()
