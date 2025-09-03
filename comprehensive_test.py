#!/usr/bin/env python3
"""
Complete diagnostic test for the card update issue.
"""

import webbrowser
import time

def run_comprehensive_test():
    """Run a comprehensive test to identify the card update issue"""
    
    print("🔬 COMPREHENSIVE DIAGNOSTIC TEST")
    print("=" * 50)
    
    print("📋 ISSUE: Portfolio cards show hardcoded data instead of API results")
    print("🎯 GOAL: Find exactly where the card update process is failing")
    
    print(f"\n🚀 STEP 1: Opening guided dashboard...")
    url = "http://localhost:8007/guided-dashboard.html"
    webbrowser.open(url)
    
    input("⏸️  Press ENTER when page loads...")
    
    print(f"\n🧪 STEP 2: Manual DOM test")
    print("1. Open browser Dev Tools (F12)")
    print("2. Go to Console tab") 
    print("3. Paste and run this command:")
    print("   window.testCardValues()")
    print("4. This should set all card values to 'TEST 1: 99.9% annually' etc.")
    
    result = input("❓ Did the test values appear in the cards? (y/n): ").lower().strip()
    
    if result != 'y':
        print("❌ ISSUE: DOM elements cannot be updated")
        print("   POSSIBLE CAUSES:")
        print("   • DOM elements don't exist or wrong selectors")
        print("   • JavaScript errors preventing execution")
        print("   • CSS hiding the elements")
        print("   • Wrong HTML structure")
        return False
    
    print("✅ DOM elements can be updated successfully")
    
    print(f"\n📝 STEP 3: Fill form and trigger API call")
    print("Fill the form with:")
    print("   Age: 35")
    print("   Amount: 100000") 
    print("   Timeline: 20 years")
    print("   Account: Taxable")
    
    input("⏸️  Form filled? Press ENTER...")
    
    print(f"\n🚀 STEP 4: Click 'Continue to Portfolio Selection'")
    print("WATCH THE CONSOLE for these messages:")
    print("   '🚀 Loading sophisticated optimized portfolios with real API call...'")
    print("   '📡 Making API call to /api/enhanced/portfolio/optimize...'")
    print("   '✅ API call successful, received optimization results:'")
    print("   '🎯 Transformed optimized portfolios:'")
    print("   '🔧 updateCardMetrics called for: Conservative ...'")
    
    input("⏸️  Ready to click? Press ENTER then click button...")
    
    print(f"\n⏱️  STEP 5: During the 15-20 second wait...")
    print("Check the Console tab for error messages")
    print("Check the Network tab to verify API call is made")
    
    input("⏸️  API call finished? Press ENTER...")
    
    print(f"\n🔍 STEP 6: Post-API diagnostic")
    print("In the console, run these commands one by one:")
    print("1. window.optimizedPortfolios")
    print("   (Should show array of 3 portfolio objects)")
    print("2. window.debugCardUpdate()")
    print("   (Should attempt to update cards with real data)")
    
    input("⏸️  Diagnostic commands run? Press ENTER...")
    
    print(f"\n🎯 STEP 7: Final verification")
    result = input("❓ Do cards now show API data (not TEST values)? (y/n): ").lower().strip()
    
    if result == 'y':
        print("🎉 SUCCESS! Cards are updating with API data")
        print("   The issue may have been a timing or caching problem")
        return True
    else:
        print("❌ ISSUE PERSISTS: Cards still not showing API data")
        
        print(f"\n🔧 DEBUGGING NEXT STEPS:")
        print("1. Check if window.optimizedPortfolios contains real data")
        print("2. Check if updateCardMetrics function is being called")
        print("3. Check for JavaScript errors in console")
        print("4. Verify DOM selectors are finding correct elements")
        
        specific_issue = input("❓ What did you observe? (no-data/no-calls/errors/other): ").lower().strip()
        
        if specific_issue == 'no-data':
            print("🔍 Issue: optimizedPortfolios is empty or has wrong data")
            print("   CHECK: API transformation function")
        elif specific_issue == 'no-calls':
            print("🔍 Issue: updateCardMetrics not being called")  
            print("   CHECK: initializePortfolioCards function")
        elif specific_issue == 'errors':
            print("🔍 Issue: JavaScript errors preventing updates")
            print("   CHECK: Console for error messages")
        else:
            print("🔍 Issue: Other problem")
            print("   CHECK: All of the above")
            
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    if success:
        print("\n🏆 TEST PASSED: Issue resolved!")
    else:
        print("\n⚠️  TEST FAILED: Issue requires further investigation")
        print("   Next step: Check the specific debugging guidance above")
