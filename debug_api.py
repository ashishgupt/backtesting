#!/usr/bin/env python3
"""
Test script to debug the portfolio optimization API response format.
"""

import requests
import json

def debug_api_response():
    """Debug the actual API response format"""
    
    url = "http://localhost:8007/api/enhanced/portfolio/optimize"
    request_data = {
        "current_savings": 100000,
        "target_amount": None,
        "time_horizon": 20,
        "account_type": "taxable",
        "new_money_available": False,
        "max_annual_contribution": None
    }
    
    print("🔍 Debugging API response format...")
    
    try:
        response = requests.post(url, json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Response received")
            print(f"📋 Response type: {type(result)}")
            print(f"📋 Response keys (if dict): {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            print(f"\n📄 Full response:")
            print(json.dumps(result, indent=2, default=str))
            
            return result
            
        else:
            print(f"❌ API failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    return None

if __name__ == "__main__":
    debug_api_response()
