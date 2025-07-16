import requests
import time
import statistics
from tabulate import tabulate

BASE_URL = "http://localhost:8000"

def make_request(endpoint, no_cache=False):
    start_time = time.time()
    params = {"no_cache": "true"} if no_cache else {}

    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params)
        end_time = time.time()

        if response.status_code == 200:
            return {
                "success": True,
                "response_time": end_time - start_time,
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "response_time": end_time - start_time,
                "error": response.json()
            }
    except Exception as e:
        end_time = time.time()
        return {
            "success": False,
            "response_time": end_time - start_time,
            "error": str(e)
        }

def test_endpoint(endpoint, iterations=10):
    print(f"Testing {endpoint}")
    # reset performance data
    make_request("/performance/reset")

    # test with cache (first run will be without cache)
    print("Testing with cache")
    cached_times = []

    for i in range(iterations):
        result = make_request(endpoint, no_cache=False)
        if result["success"]:
            cached_times.append(result["response_time"])

    # clear cache between tests
    make_request("/cache/clear")

    # test without cache
    print("Testing without cache")
    non_cached_times = []

    for i in range(iterations):
        result = make_request(endpoint, no_cache=True)
        if result["success"]:
            non_cached_times.append(result["response_time"])

    return {
        "endpoint": endpoint,
        "cached_times": cached_times,
        "non_cached_times": non_cached_times,
        "cached_avg": statistics.mean(cached_times) if cached_times else 0,
        "non_cached_avg": statistics.mean(non_cached_times) if non_cached_times else 0,
        "cached_median": statistics.median(cached_times) if cached_times else 0,
        "non_cached_median": statistics.median(non_cached_times) if non_cached_times else 0,
    }

def run_test():
    # Test endpoints
    endpoints = [
        "/campaign/1/performance",
        "/campaign/2/performance",
        "/campaign/3/performance",
        "/campaign/4/performance",
        "/advertiser/4/spending",
        "/advertiser/5/spending",
        "/advertiser/6/spending",
        "/advertiser/43/spending",
        "/user/454646/engagements",
        "/user/498117/engagements",
        "/user/88611/engagements",
        "/user/175096/engagements"
    ]

    results = []

    for endpoint in endpoints:
        try:
            result = test_endpoint(endpoint, iterations=15)
            results.append(result)

            # Small delay between tests
            time.sleep(0.5)
        except Exception as e:
            print(f"Error testing {endpoint}: {e}")

    return results

def get_api_stats():
    try:
        result = make_request("/performance/stats")
        if result["success"]:
            return result["data"]
        return None
    except Exception as e:
        print(f"Error getting API stats: {e}")
        return None


def format_results_table(results):
    headers = [
        "Endpoint",
        "Avg Time (Cached)",
        "Avg Time (No Cache)",
        "Median Time (Cached)",
        "Median Time (No Cache)",
        "Performance Improvement",
        "Cache Hit Benefit"
    ]

    table_data = []

    for result in results:
        cached_avg = result["cached_avg"]
        non_cached_avg = result["non_cached_avg"]

        if non_cached_avg > 0:
            improvement = ((non_cached_avg - cached_avg) / non_cached_avg) * 100
        else:
            improvement = 0

        if len(result["cached_times"]) > 1:
            cache_hit_avg = statistics.mean(result["cached_times"][1:])  # Skip first request
            cache_miss_time = result["cached_times"][0] if result["cached_times"] else 0

            if cache_miss_time > 0:
                cache_benefit = ((cache_miss_time - cache_hit_avg) / cache_miss_time) * 100
            else:
                cache_benefit = 0
        else:
            cache_benefit = 0

        table_data.append([
            result["endpoint"].split("/")[-1],
            f"{cached_avg:.4f}s",
            f"{non_cached_avg:.4f}s",
            f"{result['cached_median']:.4f}s",
            f"{result['non_cached_median']:.4f}s",
            f"{improvement:.1f}%",
            f"{cache_benefit:.1f}%"
        ])

    return tabulate(table_data, headers=headers, tablefmt="grid")


def main():
    results = run_test()

    if not results:
        return

    print("PERFORMANCE TEST RESULTS")
    print(format_results_table(results))

    # Get API statistics
    api_stats = get_api_stats()
    if api_stats:
        print(f"API STATISTICS")
        print(f"Total Requests: {api_stats.get('total_requests', 0)}")
        print(f"Cache Hits: {api_stats.get('cache_hits', 0)}")
        print(f"Cache Hit Ratio: {api_stats.get('cache_hit_ratio', 0):.2%}")
        print(f"Overall Performance Improvement: {api_stats.get('performance_improvement', 0):.4f}s")

    # overall metrics
    total_cached_avg = statistics.mean([r["cached_avg"] for r in results if r["cached_avg"] > 0])
    total_non_cached_avg = statistics.mean([r["non_cached_avg"] for r in results if r["non_cached_avg"] > 0])

    if total_non_cached_avg > 0:
        overall_improvement = ((total_non_cached_avg - total_cached_avg) / total_non_cached_avg) * 100
        print(f"Redis caching provides {overall_improvement:.1f}% performance improvement on average")
        print(f"Average response time: {total_cached_avg:.4f}s (cached) vs {total_non_cached_avg:.4f}s (no cache)")
        print(f"Time saved per request: {(total_non_cached_avg - total_cached_avg):.4f}s")


if __name__ == "__main__":
    main()
