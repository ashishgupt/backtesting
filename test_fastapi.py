#!/usr/bin/env python3
"""
Test the FastAPI application
"""
import subprocess
import time
import requests
import json

def test_fastapi_server():
    """Test the FastAPI server endpoints"""
    print("🧪 Testing FastAPI Portfolio Backtesting API")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
        else:
            print(f"Health check failed: {response.text}")
            
        # Test root endpoint
        print("\nTesting root endpoint...")
        response = requests.get(f"{base_url}/")
        print(f"Root status: {response.status_code}")
        if response.status_code == 200:
            print(f"Root response: {response.json()}")
            
        # Test assets endpoint
        print("\nTesting assets endpoint...")
        response = requests.get(f"{base_url}/api/data/assets")
        print(f"Assets status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['count']} assets")
        else:
            print(f"Assets endpoint failed: {response.text}")
            
        # Test data status endpoint
        print("\nTesting data status endpoint...")
        response = requests.get(f"{base_url}/api/data/status")
        print(f"Data status: {response.status_code}")
        if response.status_code == 200:
            print(f"Data status: {response.json()}")
            
        # Test backtesting endpoint
        print("\nTesting backtesting endpoint...")
        backtest_data = {
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
        
        response = requests.post(
            f"{base_url}/api/backtest/portfolio",
            json=backtest_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Backtest status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Backtest completed successfully!")
            print(f"Final value: ${data['final_value']:,.2f}")
            print(f"CAGR: {data['performance_metrics']['cagr']:.2%}")
            print(f"Cache hit: {data['cache_hit']}")
        else:
            print(f"Backtest failed: {response.text}")
            
        print(f"\n✅ FastAPI testing completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to FastAPI server at localhost:8000")
        print("Make sure to run: uvicorn src.api.main:app --reload")
        
    except Exception as e:
        print(f"❌ Error testing FastAPI: {e}")

if __name__ == "__main__":
    test_fastapi_server()