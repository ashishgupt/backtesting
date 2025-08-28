#!/usr/bin/env python3
"""
Portfolio Engine Optimization Test

SPRINT 2, Phase 1, Week 3: Portfolio Engine Performance Comparison
Tests optimized vs original engine performance for 7-asset portfolios
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import time
import numpy as np
from datetime import datetime

def test_engine_performance():
    """Test both original and optimized portfolio engines"""
    
    print("🚀 SPRINT 2, PHASE 1, WEEK 3: Portfolio Engine Optimization")
    print("=" * 70)
    
    # Test allocation: 7-asset diversified portfolio
    test_allocation = {
        'VTI': 0.35,     # US Total Market - 35%
        'VTIAX': 0.15,   # International - 15%
        'BND': 0.25,     # Bonds - 25%
        'VNQ': 0.10,     # REITs - 10%  
        'GLD': 0.05,     # Gold - 5%
        'VWO': 0.05,     # Emerging Markets - 5%
        'QQQ': 0.05      # Technology - 5%
    }
    
    # Test parameters
    test_cases = [
        {
            'name': '4-year backtest',
            'start_date': '2020-01-01',
            'end_date': '2024-12-31',
            'target_time': 0.3  # Target: <0.3s for 4-year
        },
        {
            'name': '10-year backtest', 
            'start_date': '2015-01-01',
            'end_date': '2024-12-31',
            'target_time': 0.5  # Target: <0.5s for 10-year
        },
        {
            'name': '20-year backtest',
            'start_date': '2004-01-01', 
            'end_date': '2024-12-31',
            'target_time': 1.0  # Target: <1.0s for 20-year
        }
    ]
    
    print("\n🔧 Testing API Performance (Current Implementation):")
    
    # Test current API performance
    try:
        import requests
        
        api_results = {}
        
        for test_case in test_cases:
            print(f"\n   📊 {test_case['name']}:")
            
            backtest_request = {
                'allocation': {'allocation': test_allocation},
                'initial_value': 10000,
                'start_date': test_case['start_date'],
                'end_date': test_case['end_date'],
                'rebalance_frequency': 'quarterly'
            }
            
            start_time = time.time()
            response = requests.post(
                'http://127.0.0.1:8006/api/backtest/portfolio',
                json=backtest_request, 
                timeout=30
            )
            api_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                server_time = result['calculation_time_seconds']
                api_results[test_case['name']] = {
                    'api_time': api_time,
                    'server_time': server_time,
                    'cagr': result['performance_metrics']['cagr'],
                    'sharpe': result['performance_metrics']['sharpe_ratio']
                }
                
                status = "🎯 TARGET MET" if server_time <= test_case['target_time'] else "🚨 NEEDS OPTIMIZATION"
                print(f"      API total: {api_time:.2f}s")
                print(f"      Server calculation: {server_time:.2f}s")
                print(f"      {status} (target: ≤{test_case['target_time']:.1f}s)")
                print(f"      CAGR: {result['performance_metrics']['cagr']:.2%}")
            else:
                print(f"      ❌ API error: {response.status_code}")
                api_results[test_case['name']] = {'error': True}
                
    except Exception as e:
        print(f"      ⚠️  API not available: {e}")
        print("         To test API: docker-compose up -d")
        api_results = {}
    
    print("\n🧪 Testing Optimized Engine (Direct):")
    
    # Test optimized engine directly (if database is accessible)
    try:
        from src.core.portfolio_engine_optimized import OptimizedPortfolioEngine
        
        engine = OptimizedPortfolioEngine()
        optimized_results = {}
        
        for test_case in test_cases:
            print(f"\n   ⚡ {test_case['name']}:")
            
            start_time = time.time()
            result = engine.backtest_portfolio(
                allocation=test_allocation,
                initial_value=10000,
                start_date=test_case['start_date'],
                end_date=test_case['end_date'],
                rebalance_frequency='quarterly'
            )
            optimized_time = time.time() - start_time
            
            optimized_results[test_case['name']] = {
                'time': optimized_time,
                'cagr': result['performance_metrics']['cagr'],
                'sharpe': result['performance_metrics']['sharpe_ratio']
            }
            
            status = "🎯 TARGET MET" if optimized_time <= test_case['target_time'] else "🚨 STILL NEEDS WORK"
            print(f"      Optimized calculation: {optimized_time:.2f}s")
            print(f"      {status} (target: ≤{test_case['target_time']:.1f}s)")
            print(f"      CAGR: {result['performance_metrics']['cagr']:.2%}")
            
            # Compare with API if available
            if test_case['name'] in api_results and 'server_time' in api_results[test_case['name']]:
                original_time = api_results[test_case['name']]['server_time']
                speedup = original_time / optimized_time
                print(f"      🏃 Speedup: {speedup:.1f}x faster than original")
                
                # Validate results match
                api_cagr = api_results[test_case['name']]['cagr']
                if abs(result['performance_metrics']['cagr'] - api_cagr) < 0.0001:
                    print(f"      ✅ Results match original (CAGR difference: {abs(result['performance_metrics']['cagr'] - api_cagr):.4f})")
                else:
                    print(f"      ⚠️  Results differ from original (CAGR difference: {abs(result['performance_metrics']['cagr'] - api_cagr):.4f})")
                    
    except Exception as e:
        print(f"      ⚠️  Optimized engine test failed: {e}")
        print("         Ensure database is running: docker-compose up -d")
        optimized_results = {}
    
    print("\n" + "=" * 70)
    print("🎯 OPTIMIZATION SUMMARY:")
    
    if optimized_results:
        print("\n✅ PERFORMANCE TARGETS:")
        for test_case in test_cases:
            if test_case['name'] in optimized_results:
                opt_time = optimized_results[test_case['name']]['time']
                target = test_case['target_time']
                status = "✅ MET" if opt_time <= target else "❌ MISSED"
                print(f"   {test_case['name']}: {opt_time:.2f}s ≤ {target:.1f}s {status}")
        
        print(f"\n🚀 OPTIMIZATION IMPACT:")
        for test_case in test_cases:
            if (test_case['name'] in optimized_results and 
                test_case['name'] in api_results and 
                'server_time' in api_results[test_case['name']]):
                
                orig_time = api_results[test_case['name']]['server_time']
                opt_time = optimized_results[test_case['name']]['time']
                speedup = orig_time / opt_time
                
                print(f"   {test_case['name']}: {orig_time:.2f}s → {opt_time:.2f}s ({speedup:.1f}x faster)")
        
        # Overall assessment
        all_targets_met = all(
            optimized_results[tc['name']]['time'] <= tc['target_time']
            for tc in test_cases
            if tc['name'] in optimized_results
        )
        
        print(f"\n📊 SPRINT 2, PHASE 1, WEEK 3 STATUS:")
        if all_targets_met:
            print("   ✅ ALL PERFORMANCE TARGETS MET!")
            print("   🚀 Ready for Phase 2: Advanced Risk Analytics")
        else:
            print("   🔧 Some targets missed - further optimization needed")
    
    else:
        print("   ⚠️  Could not test optimized engine - database connection needed")
        print("      Run: docker-compose up -d && python test_portfolio_optimization.py")

if __name__ == "__main__":
    test_engine_performance()
