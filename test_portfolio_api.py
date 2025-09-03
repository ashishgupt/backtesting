#!/usr/bin/env python3
"""
Test script to verify the portfolio optimization API is working correctly.
This simulates the call that the guided dashboard should make.
"""

import requests
import json

def test_portfolio_optimization():
    """Test the enhanced portfolio optimization endpoint"""
    
    # API endpoint
    url = "http://localhost:8007/api/enhanced/portfolio/optimize"
    
    # Request data matching what the guided dashboard will send
    request_data = {
        "current_savings": 100000,
        "target_amount": None,
        "time_horizon": 20,
        "account_type": "taxable",
        "new_money_available": False,
        "max_annual_contribution": None
    }
    
    print("🔄 Testing portfolio optimization API...")
    print(f"URL: {url}")
    print(f"Request data: {json.dumps(request_data, indent=2)}")
    
    try:
        # Make the API call
        response = requests.post(
            url,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30  # 30 second timeout
        )
        
        print(f"\n✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API call successful!")
            
            # API returns list of portfolios directly
            if isinstance(result, list):
                print(f"Number of portfolios returned: {len(result)}")
                
                # Show the portfolios
                for i, portfolio in enumerate(result, 1):
                    print(f"\n📊 Portfolio {i}: {portfolio.get('strategy', 'Unknown')}")
                    print(f"   Expected Return: {portfolio.get('expected_return', 0):.2%}")
                    print(f"   Volatility: {portfolio.get('volatility', 0):.2%}")
                    print(f"   Sharpe Ratio: {portfolio.get('sharpe_ratio', 0):.2f}")
                    
                    allocation = portfolio.get('allocation', {})
                    if allocation:
                        print("   Allocation:")
                        for asset, weight in allocation.items():
                            if weight > 0.001:  # Only show assets with >0.1%
                                print(f"     {asset}: {weight:.1%}")
            else:
                print("❌ Unexpected response format (not a list)")
                return False
                
            print(f"\n🎯 Test PASSED - API is working correctly!")
            return True
            
        else:
            print(f"❌ API call failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ API call timed out (>30 seconds)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API call failed with error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_portfolio_optimization()
    if success:
        print("\n🎉 Portfolio optimization API is ready for guided dashboard!")
    else:
        print("\n🚨 Portfolio optimization API needs debugging!")
