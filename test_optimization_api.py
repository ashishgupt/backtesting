#!/usr/bin/env python3
"""
Test the portfolio optimization API endpoints
"""
import requests
import json

def test_optimization_api():
    print("🧪 Testing Portfolio Optimization API")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8007"
    
    # Test 1: Max Sharpe Ratio Portfolio
    print("1. Testing Max Sharpe Ratio endpoint...")
    max_sharpe_request = {
        "assets": ["VTI", "VTIAX", "BND"],
        "start_date": "2015-01-02",
        "end_date": "2024-12-31"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/optimize/max-sharpe",
            json=max_sharpe_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Max Sharpe response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Max Sharpe optimization successful!")
            print(f"  Optimal allocation:")
            for asset, weight in data['weights'].items():
                print(f"    {asset}: {weight:.1%}")
            print(f"  Expected Return: {data['expected_return']:.2%}")
            print(f"  Volatility: {data['volatility']:.2%}") 
            print(f"  Sharpe Ratio: {data['sharpe_ratio']:.3f}")
            print(f"  Calculation time: {data.get('calculation_time_seconds', 0):.2f}s")
        else:
            print(f"❌ Max Sharpe failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Max Sharpe error: {e}")
    
    # Test 2: Efficient Frontier (smaller number for faster testing)
    print(f"\n2. Testing Efficient Frontier endpoint...")
    frontier_request = {
        "assets": ["VTI", "VTIAX", "BND"],
        "start_date": "2015-01-02", 
        "end_date": "2024-12-31",
        "num_portfolios": 20  # Smaller number for testing
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/optimize/efficient-frontier",
            json=frontier_request,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Efficient frontier response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Efficient frontier calculation successful!")
            print(f"  Generated {data['num_portfolios']} portfolios")
            print(f"  Assets: {', '.join(data['assets'])}")
            print(f"  Calculation time: {data.get('calculation_time_seconds', 0):.2f}s")
            
            # Show best and worst portfolios by Sharpe ratio
            portfolios = data['portfolios']
            if portfolios:
                best_portfolio = max(portfolios, key=lambda p: p['sharpe_ratio'])
                worst_portfolio = min(portfolios, key=lambda p: p['sharpe_ratio'])
                
                print(f"  Best Sharpe portfolio:")
                for asset, weight in best_portfolio['weights'].items():
                    print(f"    {asset}: {weight:.1%}")
                print(f"    Sharpe: {best_portfolio['sharpe_ratio']:.3f}")
                
                print(f"  Conservative portfolio:")
                for asset, weight in worst_portfolio['weights'].items():
                    print(f"    {asset}: {weight:.1%}")
                print(f"    Sharpe: {worst_portfolio['sharpe_ratio']:.3f}")
        else:
            print(f"❌ Efficient frontier failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Efficient frontier error: {e}")
    
    # Test 3: Constrained optimization
    print(f"\n3. Testing constrained max Sharpe optimization...")
    constrained_request = {
        "assets": ["VTI", "VTIAX", "BND"],
        "start_date": "2015-01-02",
        "end_date": "2024-12-31",
        "constraints": {
            "VTI": {"min_weight": 0.4, "max_weight": 0.8},
            "BND": {"min_weight": 0.1, "max_weight": 0.3}
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/optimize/max-sharpe",
            json=constrained_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Constrained optimization response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Constrained optimization successful!")
            print(f"  Constrained allocation:")
            for asset, weight in data['weights'].items():
                print(f"    {asset}: {weight:.1%}")
            print(f"  Sharpe Ratio: {data['sharpe_ratio']:.3f}")
        else:
            print(f"❌ Constrained optimization failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Constrained optimization error: {e}")

    print(f"\n✅ Optimization API testing completed!")

if __name__ == "__main__":
    test_optimization_api()