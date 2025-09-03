#!/usr/bin/env python3
"""
Debug script to check what exactly is happening with the card updates.
"""

import requests
import json

def debug_card_update_issue():
    """Debug why cards aren't updating with API data"""
    
    print("🔍 DEBUGGING: Card Update Issue")
    print("=" * 50)
    
    # First, let's test what the API actually returns
    print("1. Testing API Response Format...")
    
    api_url = "http://localhost:8007/api/enhanced/portfolio/optimize"
    request_data = {
        "current_savings": 100000,
        "target_amount": None,
        "time_horizon": 20,
        "account_type": "taxable",
        "new_money_available": False,
        "max_annual_contribution": None
    }
    
    try:
        response = requests.post(api_url, json=request_data, timeout=30)
        if response.status_code == 200:
            api_data = response.json()
            
            print("✅ API Response Structure:")
            print(f"   Type: {type(api_data)}")
            print(f"   Length: {len(api_data) if isinstance(api_data, list) else 'N/A'}")
            
            if isinstance(api_data, list) and len(api_data) > 0:
                sample = api_data[0]
                print(f"   Sample Portfolio Keys: {list(sample.keys())}")
                print(f"   Strategy: '{sample.get('strategy', 'N/A')}'")
                print(f"   Expected Return: {sample.get('expected_return', 'N/A')}")
                print(f"   Volatility: {sample.get('volatility', 'N/A')}")
                print(f"   Allocation Keys: {list(sample.get('allocation', {}).keys())}")
                
                # Show what the transformation should produce
                print(f"\n📊 Expected Transformed Data:")
                for i, portfolio in enumerate(api_data):
                    strategy = portfolio.get('strategy', 'unknown')
                    expected_return = portfolio.get('expected_return', 0)
                    volatility = portfolio.get('volatility', 0)
                    
                    print(f"   Portfolio {i+1}:")
                    print(f"     Strategy: '{strategy}' -> '{strategy.capitalize()}'")
                    print(f"     Expected Return: {expected_return} -> {expected_return*100:.1f}% annually")
                    
                    # Risk description logic
                    if volatility < 0.12:
                        risk_desc = 'Low (Steady)'
                    elif volatility < 0.20:
                        risk_desc = 'Medium (Some ups/downs)'
                    else:
                        risk_desc = 'Higher (More volatility)'
                    print(f"     Risk: {volatility} -> '{risk_desc}'")
                    
                    # 10-year projection
                    current_amount = 100000
                    ten_year_value = current_amount * (1 + expected_return) ** 10
                    if ten_year_value < 1000000:
                        projection = f"${ten_year_value/1000:.0f}K"
                    else:
                        projection = f"${ten_year_value/1000000:.1f}M"
                    print(f"     10-Year: ${current_amount} -> {projection}")
                    print()
                    
        else:
            print(f"❌ API Error: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return
    
    print("2. Checking Browser JavaScript Issues...")
    print("   🔍 Possible Issues to Check:")
    print("   • Console errors when updateCardMetrics() is called")
    print("   • Card elements not found (querySelector failures)")
    print("   • Data field attributes missing or incorrect")
    print("   • JavaScript exceptions preventing updates")
    print("   • Timing issues with DOM updates")
    
    print("\n3. Recommended Debug Steps:")
    print("   1. Open browser Dev Tools (F12)")
    print("   2. Go to Console tab")
    print("   3. Fill form and click 'Continue to Portfolio Selection'")
    print("   4. Watch for these console messages:")
    print("      - '🔧 updateCardMetrics called for: ...'")
    print("      - 'Metrics container found: ...'")
    print("      - 'Return element found: ...'")
    print("      - 'Setting return value to: ...'")
    print("   5. Check if any errors appear in console")
    
    print("\n4. Manual Verification:")
    print("   After API call completes, manually check in console:")
    print("   ```javascript")
    print("   // Check if cards exist")
    print("   document.querySelectorAll('.risk-profile[data-profile]').length")
    print("   ")
    print("   // Check if metrics elements exist")
    print("   document.querySelectorAll('[data-field=\"expected_return\"]').length")
    print("   ")
    print("   // Check current values")
    print("   document.querySelector('[data-field=\"expected_return\"]').textContent")
    print("   ```")

if __name__ == "__main__":
    debug_card_update_issue()
