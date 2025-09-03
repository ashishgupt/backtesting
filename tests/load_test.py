"""
🚀 Load Testing for Portfolio Backtesting API
Tests concurrent user capacity and response times
"""
import asyncio
import aiohttp
import time
import json
import statistics
import random

class PortfolioLoadTester:
    """Load testing suite for portfolio backtesting system"""
    
    def __init__(self, base_url="http://127.0.0.1:8007"):
        self.base_url = base_url
        
    async def test_endpoint(self, session, endpoint, data=None, method="GET"):
        """Test single endpoint and measure response time"""
        start_time = time.time()
        
        try:
            if method == "POST":
                async with session.post(f"{self.base_url}{endpoint}", json=data) as response:
                    result = await response.json()
                    response_time = time.time() - start_time
                    return {
                        "status": response.status,
                        "response_time": response_time,
                        "success": response.status == 200,
                        "endpoint": endpoint
                    }
            else:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    result = await response.json()
                    response_time = time.time() - start_time
                    return {
                        "status": response.status,
                        "response_time": response_time,
                        "success": response.status == 200,
                        "endpoint": endpoint
                    }
        except Exception as e:
            return {
                "status": 500,
                "response_time": time.time() - start_time,
                "success": False,
                "error": str(e),
                "endpoint": endpoint
            }
    
    async def concurrent_test(self, num_users=10, test_duration=30):
        """Run concurrent user simulation"""
        print(f"🚀 Starting load test: {num_users} concurrent users for {test_duration} seconds")
        
        # Test scenarios
        test_scenarios = [
            {"endpoint": "/health", "method": "GET", "weight": 10},
            {"endpoint": "/api/data/assets", "method": "GET", "weight": 5},
            {
                "endpoint": "/api/backtest/portfolio",
                "method": "POST", 
                "data": {
                    "allocation": {"allocation": {"VTI": 0.6, "VTIAX": 0.3, "BND": 0.1}},
                    "initial_value": 10000,
                    "start_date": "2020-01-01",
                    "end_date": "2024-01-01",
                    "rebalance_frequency": "monthly"
                },
                "weight": 3
            },
            {
                "endpoint": "/api/chat/recommend",
                "method": "POST",
                "data": {"message": "I want a balanced portfolio for retirement"},
                "weight": 2
            },
            {
                "endpoint": "/api/optimize/max-sharpe",
                "method": "POST",
                "data": {
                    "assets": ["VTI", "VTIAX", "BND"],
                    "start_date": "2020-01-01",
                    "end_date": "2024-01-01"
                },
                "weight": 1
            }
        ]
        
        # Prepare weighted scenario list
        weighted_scenarios = []
        for scenario in test_scenarios:
            weighted_scenarios.extend([scenario] * scenario["weight"])
        
        results = []
        start_time = time.time()
        
        # Create connector with connection limits
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            
            # Function to simulate single user
            async def simulate_user(user_id):
                user_results = []
                user_start = time.time()
                
                while (time.time() - user_start) < test_duration:
                    # Random scenario selection
                    scenario = random.choice(weighted_scenarios)
                    
                    # Execute test
                    result = await self.test_endpoint(
                        session, 
                        scenario["endpoint"],
                        scenario.get("data"),
                        scenario["method"]
                    )
                    result["user_id"] = user_id
                    user_results.append(result)
                    
                    # Random delay between requests (0.5-2 seconds)
                    await asyncio.sleep(random.uniform(0.5, 2.0))
                
                return user_results
            
            # Launch concurrent users
            tasks = [simulate_user(i) for i in range(num_users)]
            user_results_list = await asyncio.gather(*tasks)
            
            # Flatten results
            for user_results in user_results_list:
                results.extend(user_results)
        
        total_time = time.time() - start_time
        
        # Analyze results
        self.analyze_results(results, total_time, num_users)
        
        return results
    
    def analyze_results(self, results, total_time, num_users):
        """Analyze and display test results"""
        print(f"\n📊 LOAD TEST RESULTS")
        print(f"=" * 50)
        
        # Overall statistics
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r["success"])
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
        
        print(f"Total Requests: {total_requests}")
        print(f"Successful: {successful_requests}")
        print(f"Failed: {failed_requests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Requests/Second: {total_requests / total_time:.1f}")
        print(f"Duration: {total_time:.1f} seconds")
        print(f"Concurrent Users: {num_users}")
        
        # Response time statistics
        if successful_requests > 0:
            successful_results = [r for r in results if r["success"]]
            response_times = [r["response_time"] for r in successful_results]
            
            print(f"\n⏱️  RESPONSE TIME ANALYSIS")
            print(f"-" * 30)
            print(f"Average: {statistics.mean(response_times):.3f}s")
            print(f"Median: {statistics.median(response_times):.3f}s")
            print(f"Min: {min(response_times):.3f}s")
            print(f"Max: {max(response_times):.3f}s")
            print(f"95th percentile: {sorted(response_times)[int(len(response_times) * 0.95)]:.3f}s")
        
        # Endpoint breakdown
        endpoint_stats = {}
        for result in results:
            endpoint = result["endpoint"]
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {"total": 0, "success": 0, "times": []}
            
            endpoint_stats[endpoint]["total"] += 1
            if result["success"]:
                endpoint_stats[endpoint]["success"] += 1
                endpoint_stats[endpoint]["times"].append(result["response_time"])
        
        print(f"\n🎯 ENDPOINT PERFORMANCE")
        print(f"-" * 60)
        for endpoint, stats in endpoint_stats.items():
            success_rate = (stats["success"] / stats["total"]) * 100
            avg_time = statistics.mean(stats["times"]) if stats["times"] else 0
            print(f"{endpoint}")
            print(f"  Requests: {stats['total']}, Success: {success_rate:.1f}%, Avg Time: {avg_time:.3f}s")
        
        # Performance assessment
        print(f"\n🚦 PERFORMANCE ASSESSMENT")
        print(f"-" * 30)
        
        if success_rate >= 99:
            print("✅ Excellent reliability")
        elif success_rate >= 95:
            print("⚠️  Good reliability")
        else:
            print("❌ Poor reliability - investigate failures")
            
        if successful_requests > 0:
            avg_response_time = statistics.mean([r["response_time"] for r in successful_results])
            if avg_response_time < 2.0:
                print("✅ Excellent response times")
            elif avg_response_time < 5.0:
                print("⚠️  Acceptable response times")
            else:
                print("❌ Slow response times - optimization needed")

async def run_load_test():
    """Run comprehensive load test suite"""
    tester = PortfolioLoadTester()
    
    print("🔧 Portfolio Backtesting API - Load Testing Suite")
    print("=" * 60)
    
    # Test 1: Light load
    print("\n1️⃣  LIGHT LOAD TEST (5 users, 30 seconds)")
    await tester.concurrent_test(num_users=5, test_duration=30)
    
    # Test 2: Medium load  
    print("\n2️⃣  MEDIUM LOAD TEST (15 users, 60 seconds)")
    await tester.concurrent_test(num_users=15, test_duration=60)
    
    # Test 3: Heavy load
    print("\n3️⃣  HEAVY LOAD TEST (30 users, 30 seconds)")
    await tester.concurrent_test(num_users=30, test_duration=30)
    
    print("\n🎯 Load testing complete!")
    print("💡 Check results above for performance insights")

if __name__ == "__main__":
    # Run the load test
    asyncio.run(run_load_test())
