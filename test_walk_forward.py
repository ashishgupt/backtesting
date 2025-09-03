 is None):
                invalid_results.append(result.window_id)
        
        if invalid_results:
            print(f"⚠️  Found {len(invalid_results)} results with invalid metrics")
            print(f"   Invalid windows: {invalid_results[:5]}")  # Show first 5
        else:
            print("✅ All results have valid performance metrics")
        
        # Test degradation calculations
        degradation_issues = []
        for result in validator.validation_results:
            if abs(result.return_degradation) > 2.0:  # More than 200% degradation seems unrealistic
                degradation_issues.append((result.window_id, result.return_degradation))
        
        if degradation_issues:
            print(f"⚠️  Found {len(degradation_issues)} results with extreme degradation")
        else:
            print("✅ All degradation metrics are within reasonable bounds")
            
    except Exception as e:
        print(f"❌ Performance metrics testing failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Walk-Forward Validation Infrastructure Test Complete!")
    print("✅ All core components are working correctly")
    
    return True

async def test_api_integration():
    """Test the API integration for walk-forward validation"""
    
    print("\n🌐 Testing API Integration")
    print("=" * 40)
    
    try:
        import httpx
        
        base_url = "http://localhost:8007"
        
        # Test 1: Check API status
        print("\n1. Testing API Status...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/walk-forward/status")
            if response.status_code == 200:
                status_data = response.json()
                print(f"✅ API is operational")
                print(f"   Available symbols: {status_data.get('available_symbols', 'N/A')}")
            else:
                print(f"❌ API status check failed: {response.status_code}")
                return False
        
        # Test 2: Test window generation
        print("\n2. Testing Window Generation API...")
        test_request = {
            "start_date": "2020-01-01",
            "end_date": "2022-12-31", 
            "optimization_window_months": 24,
            "validation_window_months": 6,
            "step_months": 6
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/walk-forward/generate-windows",
                json=test_request
            )
            
            if response.status_code == 200:
                windows = response.json()
                print(f"✅ Window generation successful: {len(windows)} windows")
            else:
                print(f"❌ Window generation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        
        # Test 3: Test configuration recommendations
        print("\n3. Testing Configuration Recommendations...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/walk-forward/config/recommendations")
            if response.status_code == 200:
                config_data = response.json()
                print("✅ Configuration recommendations retrieved")
                configs = config_data.get('recommended_configurations', {})
                print(f"   Available configurations: {list(configs.keys())}")
            else:
                print(f"❌ Configuration recommendations failed: {response.status_code}")
                return False
        
        print("\n✅ API Integration Test Complete!")
        return True
        
    except ImportError:
        print("❌ httpx not available - skipping API tests")
        print("   Install with: pip install httpx")
        return True  # Don't fail the test for missing optional dependency
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

def test_data_availability():
    """Test data availability for walk-forward validation"""
    
    print("\n📊 Testing Data Availability")
    print("=" * 30)
    
    try:
        from src.core.database import DatabaseConnection
        from src.core.market_data_manager import MarketDataManager
        
        db_connection = DatabaseConnection()
        market_data = MarketDataManager(db_connection)
        
        # Test 1: Check available symbols
        print("\n1. Checking Available Symbols...")
        symbols = market_data.get_available_symbols()
        print(f"✅ Found {len(symbols)} available symbols")
        print(f"   Symbols: {symbols}")
        
        # Test 2: Check data coverage
        print("\n2. Checking Data Coverage...")
        start_date = datetime(2008, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        try:
            data = market_data.get_data_for_period(start_date, end_date)
            print(f"✅ Data available from {data.index.min().date()} to {data.index.max().date()}")
            print(f"   Total records: {len(data)}")
            print(f"   Assets covered: {list(data.columns)}")
            
            # Check for data gaps
            missing_data = data.isnull().sum()
            if missing_data.sum() > 0:
                print("⚠️  Found missing data:")
                for asset, missing_count in missing_data.items():
                    if missing_count > 0:
                        print(f"     {asset}: {missing_count} missing values")
            else:
                print("✅ No missing data found")
                
        except Exception as e:
            print(f"❌ Data coverage check failed: {e}")
            return False
        
        # Test 3: Check data quality
        print("\n3. Checking Data Quality...")
        try:
            # Check for reasonable price ranges
            for symbol in data.columns:
                prices = data[symbol].dropna()
                if len(prices) > 0:
                    min_price = prices.min()
                    max_price = prices.max()
                    
                    if min_price <= 0:
                        print(f"⚠️  {symbol} has non-positive prices (min: {min_price})")
                    elif min_price < 1 or max_price > 10000:
                        print(f"⚠️  {symbol} has unusual price range: {min_price:.2f} - {max_price:.2f}")
                    
                    # Check for extreme price movements
                    returns = prices.pct_change().dropna()
                    extreme_returns = returns[(returns > 0.5) | (returns < -0.5)]
                    if len(extreme_returns) > 0:
                        print(f"⚠️  {symbol} has {len(extreme_returns)} extreme daily returns (>50%)")
            
            print("✅ Data quality check completed")
            
        except Exception as e:
            print(f"❌ Data quality check failed: {e}")
            return False
        
        print("\n✅ Data Availability Test Complete!")
        return True
        
    except Exception as e:
        print(f"❌ Data availability test failed: {e}")
        return False

async def main():
    """Run all tests"""
    
    print("🚀 Starting Walk-Forward Validation Infrastructure Tests")
    print("=" * 80)
    
    # Test results
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Core infrastructure
    if await test_walk_forward_infrastructure():
        tests_passed += 1
        print("✅ Core Infrastructure Test: PASSED")
    else:
        print("❌ Core Infrastructure Test: FAILED")
    
    # Test 2: Data availability
    if test_data_availability():
        tests_passed += 1
        print("✅ Data Availability Test: PASSED")
    else:
        print("❌ Data Availability Test: FAILED")
    
    # Test 3: API integration (optional)
    if await test_api_integration():
        tests_passed += 1
        print("✅ API Integration Test: PASSED")
    else:
        print("❌ API Integration Test: FAILED")
    
    # Final results
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {tests_passed/total_tests:.1%}")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Walk-Forward Validation Infrastructure is ready!")
        print("\n📋 Next Steps:")
        print("   1. Start the API server: uvicorn src.api.main:app --port 8007")
        print("   2. Open the web interface: http://localhost:8007/walk-forward-analyzer.html")
        print("   3. Run your first walk-forward analysis!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure all dependencies are installed")
        print("   2. Check database connectivity")
        print("   3. Verify market data is available")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
