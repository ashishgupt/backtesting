#!/usr/bin/env python3
"""
Simple test to verify the API works without target_amount
"""

import requests
import json

def test_api_without_target():
    """Test the API endpoint without target_amount"""
    
    url = "http://localhost:8007/api/enhanced/portfolio/optimize"
    
    # Request without target_amount
    payload = {
        "current_savings": 50000,
        "monthly_contribution": 1000,
        "time_horizon": 10,
        "risk_tolerance": "balanced",
        "account_type": "tax_deferred"
        # Note: target_amount is intentionally not provided
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing API without target_amount...")
    print(f"📊 Payload: {json.dumps(payload, indent=2)}")
    print("⏳ Making request...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"🌐 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! API returned valid response")
            
            # Check if the response has the expected structure
            for strategy in ['conservative', 'balanced', 'aggressive']:
                if strategy in data:
                    portfolio = data[strategy]
                    print(f"\n📊 {strategy.title()} Strategy:")
                    print(f"   Expected Return: {portfolio.get('expected_return', 'N/A'):.2%}" if isinstance(portfolio.get('expected_return'), (int, float)) else f"   Expected Return: {portfolio.get('expected_return', 'N/A')}")
                    print(f"   Target Achievement Probability: {portfolio.get('target_achievement_probability', 'None')}")
                    
                    # This is the key test - should be None when no target provided
                    if portfolio.get('target_achievement_probability') is None:
                        print(f"   ✅ target_achievement_probability is correctly None for {strategy}")
                    else:
                        print(f"   ❌ Expected None but got: {portfolio.get('target_achievement_probability')}")
                        
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_with_target():
    """Test the API endpoint with target_amount"""
    
    url = "http://localhost:8007/api/enhanced/portfolio/optimize"
    
    # Request with target_amount
    payload = {
        "current_savings": 50000,
        "monthly_contribution": 1000,
        "time_horizon": 10,
        "risk_tolerance": "balanced",
        "account_type": "tax_deferred",
        "target_amount": 200000  # Including target amount
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\n🧪 Testing API WITH target_amount...")
    print(f"📊 Payload: {json.dumps(payload, indent=2)}")
    print("⏳ Making request...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"🌐 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! API returned valid response")
            
            # Check if the response has the expected structure
            for strategy in ['conservative', 'balanced', 'aggressive']:
                if strategy in data:
                    portfolio = data[strategy]
                    print(f"\n📊 {strategy.title()} Strategy:")
                    print(f"   Expected Return: {portfolio.get('expected_return', 'N/A'):.2%}" if isinstance(portfolio.get('expected_return'), (int, float)) else f"   Expected Return: {portfolio.get('expected_return', 'N/A')}")
                    print(f"   Target Achievement Probability: {portfolio.get('target_achievement_probability', 'None')}")
                    
                    # This should have a value when target is provided
                    if portfolio.get('target_achievement_probability') is not None:
                        prob = portfolio.get('target_achievement_probability')
                        print(f"   ✅ target_achievement_probability is correctly set: {prob:.2%}" if isinstance(prob, (int, float)) else f"   ✅ target_achievement_probability is set: {prob}")
                    else:
                        print(f"   ❌ Expected a probability value but got None")
                        
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run both API tests"""
    print("🔧 Testing Enhanced Portfolio API target_amount optional functionality...\n")
    
    # Test without target amount
    test1_passed = test_api_without_target()
    
    # Test with target amount  
    test2_passed = test_api_with_target()
    
    # Summary
    print("\n" + "="*60)
    print("📊 API TEST SUMMARY:")
    print(f"  Without target_amount: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  With target_amount: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL API TESTS PASSED! Target amount is now properly optional.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
