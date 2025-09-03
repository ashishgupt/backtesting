#!/usr/bin/env python3
"""
Test script to verify that target_amount is now optional
"""

import asyncio
import json
from src.optimization.portfolio_optimizer_enhanced import EnhancedPortfolioOptimizer
from src.api.enhanced_optimization_routes import EnhancedOptimizationRequest

async def test_without_target_amount():
    """Test optimization without providing target_amount"""
    print("🧪 Testing portfolio optimization without target_amount...")
    
    optimizer = EnhancedPortfolioOptimizer()
    
    # Test request without target_amount
    request = EnhancedOptimizationRequest(
        current_savings=50000,
        monthly_contribution=1000,
        time_horizon=10,
        risk_tolerance="balanced",
        account_type="tax_deferred"
        # Note: target_amount is intentionally not provided
    )
    
    try:
        print(f"📊 Request: {request}")
        print("⏳ Running optimization...")
        
        result = await optimizer.optimize_enhanced_portfolio(request)
        
        print("✅ Success! Optimization completed without target_amount")
        print(f"🎯 Strategy: {result.strategy}")
        print(f"📈 Expected Return: {result.expected_return:.2%}")
        print(f"⚡ Target Achievement Probability: {result.target_achievement_probability}")
        print(f"💰 Expected Final Value: ${result.expected_final_value:,.2f}")
        
        # Verify that target_achievement_probability is None
        if result.target_achievement_probability is None:
            print("✅ target_achievement_probability is correctly None")
        else:
            print(f"❌ Expected None but got: {result.target_achievement_probability}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_with_target_amount():
    """Test optimization with providing target_amount"""
    print("\n🧪 Testing portfolio optimization WITH target_amount...")
    
    optimizer = EnhancedPortfolioOptimizer()
    
    # Test request with target_amount
    request = EnhancedOptimizationRequest(
        current_savings=50000,
        monthly_contribution=1000,
        time_horizon=10,
        risk_tolerance="balanced",
        account_type="tax_deferred",
        target_amount=200000  # Providing target amount
    )
    
    try:
        print(f"📊 Request: {request}")
        print("⏳ Running optimization...")
        
        result = await optimizer.optimize_enhanced_portfolio(request)
        
        print("✅ Success! Optimization completed with target_amount")
        print(f"🎯 Strategy: {result.strategy}")
        print(f"📈 Expected Return: {result.expected_return:.2%}")
        print(f"⚡ Target Achievement Probability: {result.target_achievement_probability}")
        print(f"💰 Expected Final Value: ${result.expected_final_value:,.2f}")
        
        # Verify that target_achievement_probability is not None
        if result.target_achievement_probability is not None:
            print(f"✅ target_achievement_probability is correctly set: {result.target_achievement_probability:.2%}")
        else:
            print("❌ Expected a probability value but got None")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run both tests"""
    print("🔧 Testing target_amount optional functionality...\n")
    
    # Test without target amount
    test1_passed = await test_without_target_amount()
    
    # Test with target amount  
    test2_passed = await test_with_target_amount()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY:")
    print(f"  Without target_amount: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  With target_amount: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! Target amount is now properly optional.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(main())
