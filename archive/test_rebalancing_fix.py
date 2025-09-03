#!/usr/bin/env python3

import json
import requests
import sys

def test_rebalancing_fix():
    """Test that the rebalancing API fix works correctly"""
    
    print("🧪 Testing Rebalancing Strategy Analysis Fix")
    print("=" * 50)
    
    # Test the API endpoint that the guided dashboard now uses
    api_url = "http://localhost:8007/api/rebalancing/compare-strategies"
    
    payload = {
        "target_allocation": {
            "VTI": 0.60,
            "VTIAX": 0.20,
            "BND": 0.20
        },
        "methods": ["5_percent_threshold", "quarterly", "annual"],
        "account_type": "taxable",
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "initial_value": 100000.0,
        "annual_contribution": 0.0
    }
    
    try:
        print("1️⃣ Testing API endpoint...")
        response = requests.post(api_url, json=payload, timeout=10)
        
        if not response.ok:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
        data = response.json()
        print(f"✅ API request successful (status: {response.status_code})")
        
        print("2️⃣ Checking response structure...")
        required_keys = ['summary_comparison', 'recommendation', 'analysis_period']
        for key in required_keys:
            if key not in data:
                print(f"❌ Missing required key: {key}")
                return False
        print("✅ Response structure is correct")
        
        print("3️⃣ Testing data transformation (simulating frontend)...")
        summary_comparison = data.get('summary_comparison', {})
        if not summary_comparison:
            print("❌ No summary_comparison data found")
            return False
            
        # Simulate the frontend transformation
        strategies = []
        for method, metrics in summary_comparison.items():
            strategy_name = method.replace('_', ' ').title()
            strategies.append({
                'strategy_name': strategy_name,
                'net_return': metrics.get('annualized_return', 0),
                'annual_cost_savings': metrics.get('cost_efficiency', 0),
                'frequency': 'Annual' if method == 'annual' else 'Quarterly' if method == 'quarterly' else 'Threshold-based'
            })
        
        if not strategies:
            print("❌ No strategies found in summary_comparison")
            return False
            
        print(f"✅ Successfully converted {len(strategies)} strategies:")
        for strategy in strategies:
            print(f"   - {strategy['strategy_name']}: {strategy['net_return']*100:.2f}% return")
        
        # Find best strategy
        best_strategy = max(strategies, key=lambda s: s['net_return'])
        print(f"✅ Best strategy identified: {best_strategy['strategy_name']} ({best_strategy['net_return']*100:.2f}% return)")
        
        print("4️⃣ Testing error handling...")
        # Test with invalid data to make sure error handling works
        invalid_payload = {**payload, "methods": ["invalid_method"]}
        invalid_response = requests.post(api_url, json=invalid_payload, timeout=10)
        
        if invalid_response.ok:
            print("❌ Expected error for invalid method, but API returned success")
            return False
        
        print("✅ Error handling works correctly for invalid methods")
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ The rebalancing strategy analysis bug is FIXED!")
        print("✅ Frontend will now receive proper data structure")
        print("✅ Step 5 in guided dashboard should work correctly")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        print("   Make sure the server is running on localhost:8007")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_rebalancing_fix()
    sys.exit(0 if success else 1)
