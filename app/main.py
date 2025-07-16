import json
import os
import time
import redis
from typing import Annotated
from fastapi import FastAPI, Query, HTTPException
from mysql.connector import pooling

# TTL settings in seconds
TTL_CAMPAIGN_PERFORMANCE = 30
TTL_ADVERTISER_SPENDING = 300  # 5 minutes
TTL_USER_ENGAGEMENTS = 120

app = FastAPI(title="My API")

# Redis connection
redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True
)
mysql_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=os.environ.get("MYSQL_HOST", "mysql"),
    port=int(os.environ.get("MYSQL_PORT", 3306)),
    user=os.environ.get("MYSQL_USER", "set_user"),
    password=os.environ.get("MYSQL_PASSWORD", "set_password"),
    database=os.environ.get("MYSQL_DB", "set_db")
)
performance_stats = {
    'with_cache': [],
    'without_cache': []
}


def get_mysql_connection():
    return mysql_pool.get_connection()


def get_redis_client():
    return redis_client


def get_from_cache(key: str):
    # Get data from Redis cache
    try:
        cached_data = redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        print(f"Cache read error: {e}")
        return None


def set_in_cache(key: str, data, ttl: int):
    # Set data in Redis cache with TTL
    try:
        redis_client.setex(key, ttl, json.dumps(data, default=str))
        return True
    except Exception as e:
        print(f"Cache write error: {e}")
        return False

def calculate_avg(times_list):
    return sum(times_list) / len(times_list) if times_list else 0

def measure_time(func):
    # Decorator to measure execution time
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    return wrapper

@measure_time
def get_campaign_performance_from_db(campaign_id: int):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    try:
        query = """
                SELECT
                    ai.campaign_id,
                    COUNT(DISTINCT ai.impression_id) AS impressions,
                    COUNT(DISTINCT ac.click_id) AS clicks,
                    IFNULL(COUNT(DISTINCT ac.click_id) / NULLIF(COUNT(DISTINCT ai.impression_id), 0), 0) * 100 AS ctr,
                    SUM(ai.ad_cost) AS ad_spend
                FROM
                    ad_impressions ai
                LEFT JOIN
                    ad_clicks ac ON ai.impression_id = ac.impression_id
                WHERE ai.campaign_id = %s
                GROUP BY
                    ai.campaign_id;
                """
        cursor.execute(query, (campaign_id,))
        result = cursor.fetchone()
        if result is None:
            return {"error": "Data not found"}

        keys = ["campaign_id", "impressions", "clicks", "ctr", "ad_spend"]
        return dict(zip(keys, result))

    finally:
        cursor.close()
        conn.close()

@measure_time
def get_advertisers_spend_from_db(advertiser_id: int):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    try:
        query = """
                SELECT
                    c.advertiser_id,
                    SUM(ai.ad_cost) AS ad_spend
                FROM
                    ad_impressions ai
                    JOIN campaigns c ON c.campaign_id = ai.campaign_id
                WHERE c.advertiser_id = %s
                GROUP BY
                    c.advertiser_id;
                """
        cursor.execute(query, (advertiser_id,))
        result = cursor.fetchone()
        if result is None:
            return {"error": "Data not found"}

        keys = ["advertiser_id", "ad_spend"]
        return dict(zip(keys, result))

    finally:
        cursor.close()
        conn.close()

@measure_time
def get_user_engagements_from_db(user_id: int):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    try:
        query = """
                SELECT
                    c.advertiser_id,
                    ai.campaign_id,
                    ai.impression_id,
                    ac.click_id,
                    ai.impression_timestamp AS impression_time,
                    ac.click_timestamp AS click_time
                FROM
                    ad_impressions ai
                    JOIN ad_clicks ac ON ai.impression_id = ac.impression_id
                    JOIN campaigns c ON c.campaign_id = ai.campaign_id
                WHERE
                    ai.user_id = %s
                ORDER BY
                    ac.click_timestamp DESC;
                """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        if result is None:
            return {"error": "Data not found"}

        keys = ["advertiser_id", "campaign_id", "impression_id", "click_id", "impression_time", "click_time"]
        # Convert each row to a dictionary
        data = [dict(zip(keys, row)) for row in result]
        return data

    finally:
        cursor.close()
        conn.close()


@app.get("/")
def read_root():
    return {
        "message": "Advertising Data API",
    }


# API Endpoints
@app.get("/campaign/{campaign_id}/performance")
def get_campaign_performance(campaign_id: int, no_cache: Annotated[
    bool, Query(description="Skip cache for performance testing")] = False):
    cache_key = f"campaign_performance:{campaign_id}"
    start_time = time.time()

    # Check cache first (unless no_cache is True)
    if not no_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data:
            end_time = time.time()
            performance_stats['with_cache'].append(end_time - start_time)
            return cached_data

    # Query database
    result, db_time = get_campaign_performance_from_db(campaign_id)

    if result is None:
        return {"error": "Data not found"}

    # Store in cache
    if not no_cache:
        set_in_cache(cache_key, result, TTL_CAMPAIGN_PERFORMANCE)

    end_time = time.time()
    total_time = end_time - start_time

    if no_cache:
        performance_stats['without_cache'].append(total_time)
        print(performance_stats['without_cache'])
    else:
        performance_stats['with_cache'].append(total_time)

    return result


@app.get("/advertiser/{advertiser_id}/spending")
def get_advertisers_spend(advertiser_id: int,
                          no_cache: Annotated[bool, Query(description="Skip cache for performance testing")] = False):
    cache_key = f"advertiser_spending:{advertiser_id}"
    start_time = time.time()

    if not no_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data:
            end_time = time.time()
            performance_stats['with_cache'].append(end_time - start_time)
            return cached_data

    # Query database
    result, db_time = get_advertisers_spend_from_db(advertiser_id)

    if result is None:
        return {"error": "Data not found"}

    # Store in cache
    if not no_cache:
        set_in_cache(cache_key, result, TTL_ADVERTISER_SPENDING)

    end_time = time.time()
    total_time = end_time - start_time

    if no_cache:
        performance_stats['without_cache'].append(total_time)
        print(performance_stats['without_cache'])
    else:
        performance_stats['with_cache'].append(total_time)

    return result


@app.get("/user/{user_id}/engagements")
def get_user_engagements(user_id: int,
                         no_cache: Annotated[bool, Query(description="Skip cache for performance testing")] = False):
    cache_key = f"user_engagements:{user_id}"
    start_time = time.time()

    if not no_cache:
        cached_data = get_from_cache(cache_key)
        if cached_data:
            end_time = time.time()
            performance_stats['with_cache'].append(end_time - start_time)
            return cached_data

    # Query database
    result, db_time = get_user_engagements_from_db(user_id)

    if not result:
        return {"error": "Data not found"}

    # Store in cache
    if not no_cache:
        set_in_cache(cache_key, result, TTL_USER_ENGAGEMENTS)

    end_time = time.time()
    total_time = end_time - start_time

    if no_cache:
        performance_stats['without_cache'].append(total_time)
        print(performance_stats['without_cache'])
    else:
        performance_stats['with_cache'].append(total_time)

    return result


@app.get("/performance/stats")
async def get_performance_stats():
    total_requests = len(performance_stats['with_cache']) + len(performance_stats['without_cache'])
    cache_hits = len(performance_stats['with_cache'])

    return {
        "total_requests": total_requests,
        "cache_hits": cache_hits,
        "avg_response_time_with_cache": calculate_avg(performance_stats['with_cache']),
        "avg_response_time_without_cache": calculate_avg(performance_stats['without_cache']),
        "performance_improvement": (
                calculate_avg(performance_stats['without_cache']) - calculate_avg(performance_stats['with_cache'])
        ) if performance_stats['with_cache'] and performance_stats['without_cache'] else 0
    }


@app.get("/performance/comparison")
async def get_performance_comparison():
    with_cache_avg = calculate_avg(performance_stats['with_cache'])
    without_cache_avg = calculate_avg(performance_stats['without_cache'])

    total_requests = len(performance_stats['with_cache']) + len(performance_stats['without_cache'])
    cache_hits = len(performance_stats['with_cache'])

    return {
        "comparison_table": {
            "metric": ["Average Response Time", "Cache Hit Ratio", "Performance Improvement"],
            "with_redis_cache": [
                f"{with_cache_avg:.4f}s",
                f"{(cache_hits / total_requests * 100):.1f}%" if total_requests > 0 else "0%",
                f"{((without_cache_avg - with_cache_avg) / without_cache_avg * 100):.1f}%" if without_cache_avg > 0 else "N/A"
            ],
            "without_redis_cache": [
                f"{without_cache_avg:.4f}s",
                "0%",
                "0%"
            ]
        },
        "raw_data": {
            "with_cache_times": performance_stats['with_cache'],
            "without_cache_times": performance_stats['without_cache']
        }
    }


@app.get("/performance/reset")
async def reset_performance_stats():
    performance_stats['with_cache'].clear()
    performance_stats['without_cache'].clear()
    return {"message": "success"}


@app.get("/cache/clear")
async def clear_cache():
    try:
        await redis_client.flushdb()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
