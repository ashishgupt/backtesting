#!/usr/bin/env python3
"""
Test the full FastAPI backtesting endpoint
"""
import requests
import json

def test_backtest_api():
    print("🧪 Testing Portfolio Backtesting API")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8004"
    
    # Test backtesting endpoint with proper structure
    print("Testing backtesting endpoint...")
    backtest_request = {
        "allocation": {
            "allocation": {
                "VTI": 0.6,
                "VTIAX": 0.3,
                "BND": 0.1
            }
        },
        "initial_value": 10000,
        "start_date": "2015-01-02",
        "end_date": "2024-12-31",
        "rebalance_frequency": "monthly"
    }
    
    print(f"Request: {json.dumps(backtest_request, indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/backtest/portfolio",
            json=backtest_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Backtest successful!")
            print(f"Final value: ${data['final_value']:,.2f}")
            print(f"CAGR: {data['performance_metrics']['cagr']:.2%}")
            print(f"Max Drawdown: {data['performance_metrics']['max_drawdown']:.2%}")
            print(f"Sharpe Ratio: {data['performance_metrics']['sharpe_ratio']:.2f}")
            print(f"Calculation time: {data.get('calculation_time_seconds', 0):.2f}s")
            print(f"Cache hit: {data['cache_hit']}")
        else:
            print(f"❌ Backtest failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_backtest_api()