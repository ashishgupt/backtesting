#!/usr/bin/env python3
"""
Quick test to verify the enhanced portfolio optimization API endpoint is working
"""

import requests
import json

def test_enhanced_optimization_api():
    """Test the /api/enhanced/portfolio/optimize endpoint"""
    
    url = "http://localhost:8007/api/enhanced/portfolio/optimize"
    
    # Test payload matching what the guided dashboard sends
    payload = {
        "current_savings": 100000,
        "target_amount": 300000,
        "time_horizon": 20,
        "account_type": "taxable",
        "new_money_available": True,
        "max_annual_contribution": 6000
    }
    
    print("🚀 Testing Enhanced Portfolio Optimization API...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response Successful!")
            
            if isinstance(data, list) and len(data) > 0:
                print(f"📈 Received {len(data)} optimized portfolios")
                
                for i, portfolio in enumerate(data):
                    strategy = portfolio.get('strategy', f'Portfolio {i}')
                    expected_return = portfolio.get('expected_return', 0)
                    volatility = portfolio.get('volatility', 0)
                    sharpe = portfolio.get('sharpe_ratio', 0)
                    
                    print(f"\n{strategy}:")
                    print(f"  Expected Return: {expected_return:.1%}")
                    print(f"  Volatility: {volatility:.1%}")
                    print(f"  Sharpe Ratio: {sharpe:.2f}")
                    
                    # Check if allocation exists
                    if 'allocation' in portfolio:
                        print(f"  Assets: {len(portfolio['allocation'])} different assets")
                
                return True
            else:
                print("❌ Invalid response format - expected list of portfolios")
                return False
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_server_health():
    """Quick health check of the server"""
    try:
        response = requests.get("http://localhost:8007/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Server is not responding")
        return False

if __name__ == "__main__":
    print("🧪 API ENDPOINT TESTING")
    print("=" * 40)
    
    # Check server health first
    if test_server_health():
        print()
        
        # Test the optimization API
        if test_enhanced_optimization_api():
            print("\n🎉 API endpoint is working correctly!")
            print("\n💡 The guided dashboard should now make real API calls")
            print("   when users transition from Step 1 to Step 2.")
        else:
            print("\n⚠️ API endpoint has issues - guided dashboard may fall back to mock data")
    else:
        print("\n❌ Server is not running. Start it with:")
        print("   python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8007 --reload")
