import os
from typing import Annotated
from fastapi import FastAPI, Query
import redis
from mysql.connector import pooling

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


@app.get("/")
def read_root():
    return {
        "message": "Advertising Data API",
        "endpoints": {
            "campaign_performance": "/campaign/{campaign_id}/performance",
            "advertiser_spending": "/advertiser/{advertiser_id}/spending",
            "user_engagements": "/user/{user_id}/engagements",
            "performance_stats": "/performance/stats",
            "performance_comparison": "/performance/comparison",
            "cache_status": "/cache/status"
        },
        "documentation": "/docs"
    }


# API Endpoints
@app.get("/campaign/{campaign_id}/performance")
def get_campaign_performance(campaign_id: int, no_cache: Annotated[
    bool, Query(description="Skip cache for performance testing")] = False):
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


@app.get("/advertiser/{advertiser_id}/spending")
def get_advertisers_spend(advertiser_id: int,
                          no_cache: Annotated[bool, Query(description="Skip cache for performance testing")] = False):
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


@app.get("/user/{user_id}/engagements")
def get_user_engagements(user_id: int,
                         no_cache: Annotated[bool, Query(description="Skip cache for performance testing")] = False):
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
