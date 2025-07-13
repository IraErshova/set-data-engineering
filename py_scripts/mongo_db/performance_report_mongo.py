import pymongo
import argparse
import sys
import csv
from datetime import datetime, timedelta, timezone
import os
from tabulate import tabulate

# def write_data_to_report(writer, title, data):
#     # write section title
#     writer.writerow([title])
#     # write header
#     # writer.writerow(columns)
#     # write data rows
#     writer.writerows(data)
#     # add empty rows as separator
#     writer.writerow([])
#     writer.writerow([])

class PerformanceReportMongo:
    def __init__(self, host: str = 'localhost', database: str = 'set_db',
                 user: str = 'set_user', password: str = 'set_password', port: int = 27017) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.mongo_client = None
        self.mongo_db = None
        self.output_folder = 'reports'
        self._connect_mongodb()

    def _connect_mongodb(self):
        try:
            self.mongo_client = pymongo.MongoClient(
                host=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                authSource=self.database,
            )
            self.mongo_db = self.mongo_client[self.database]
            self.mongo_db.command({'ping': 1})

            print("Successfully connected to MongoDB")

        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise


    def close(self):
        """Close the database connection"""
        if self.mongo_client:
            self.mongo_client.close()

    def execute_queries(self):
        # Create report file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"performance_report_{timestamp}.csv"
        csv_filepath = os.path.join(self.output_folder, csv_filename)

        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            print("1. All ad interactions for a random user:")
            self.query_ad_interactions_for_random_user(writer)
            print("\n2. Last 5 ad sessions for a user:")
            self.query_last_5_ad_sessions_for_user(writer)
            print("\n3. Ad clicks per hour per campaign for an advertiser in last 24h:")
            self.query_ad_clicks_per_hour_per_campaign(writer)
            print("\n4. Users who have seen the same ad 5+ times but never clicked:")
            self.query_users_with_repeated_impressions_no_clicks(writer)
            print("\n5. Top 3 most engaged ad categories for a user:")
            self.query_top_3_ad_categories_for_user(writer)

    def query_ad_interactions_for_random_user(self, writer):
        if self.mongo_db is None:
            print("MongoDB connection is not initialized.")
            return None
        """Retrieve all ad interactions (impressions and clicks) for one random user."""
        pipeline = [
            # get random user_id
            {"$sample": {"size": 1}},
            {"$project": {"user_id": 1}},
            # find all sessions for that user
            {"$lookup": {
                "from": "ad_sessions",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "sessions"
            }},
            {"$unwind": "$sessions"},
            {"$unwind": "$sessions.impressions"},
            # final structure
            {"$project": {
                "_id": 0,
                "user_id": 1,
                "impression": "$sessions.impressions"
            }}
        ]

        results = list(self.mongo_db["ad_sessions"].aggregate(pipeline))
        if not results:
            print("No user found.")
            return None

        user_id = results[0]["user_id"]
        all_impressions = [r["impression"] for r in results]

        print(f"Random user_id: {user_id}")
        print(f"Total ad interactions: {len(all_impressions)}")

        print(tabulate(all_impressions[:10], headers="keys", tablefmt="grid"))
        if len(all_impressions) > 10:
            print(f"...and {len(all_impressions) - 10} more.")

        # Write to CSV
        if all_impressions:
            writer.writerow([f"All ad interactions for random user {user_id}"])
            if all_impressions and isinstance(all_impressions[0], dict):
                writer.writerow(list(all_impressions[0].keys()))
                for row in all_impressions:
                    writer.writerow([row.get(k, "") for k in all_impressions[0].keys()])
            else:
                for row in all_impressions:
                    writer.writerow([row])
            writer.writerow([])
            writer.writerow([])
        return all_impressions

    def query_last_5_ad_sessions_for_user(self, writer):
        if self.mongo_db is None:
            print("MongoDB connection is not initialized.")
            return None
        """Retrieve a user's last 5 ad sessions with timestamps and click behavior."""
        pipeline = [
            # random user
            {"$sample": {"size": 1}},
            {"$project": {"user_id": 1}},
            # find sessions for this user
            {"$lookup": {
                "from": "ad_sessions",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "sessions"
            }},
            # get all sessions
            {"$unwind": "$sessions"},
            {"$project": {
                "_id": 0,
                "user_id": 1,
                "session_start": "$sessions.session_start",
                "session_end": "$sessions.session_end",
                "impressions": "$sessions.impressions"
            }},
            {"$sort": {"session_end": -1}},
            {"$limit": 5},
            {"$addFields": {
                "clicks": {
                    "$size": {
                        "$filter": {
                            "input": "$impressions",
                            "as": "imp",
                            "cond": {"$eq": ["$$imp.clicked", True]}
                        }
                    }
                }
            }},
            {"$project": {
                "user_id": 1,
                "session_start": 1,
                "session_end": 1,
                "clicks": 1
            }}
        ]

        results = list(self.mongo_db["ad_sessions"].aggregate(pipeline))

        if not results:
            print("No sessions found.")
            return None

        print(f"Random user_id: {results[0]['user_id']}")
        for s in results:
            print(f"Session: {s['session_start']} - {s['session_end']}, Clicks: {s['clicks']}")

        # Write to CSV
        if results:
            writer.writerow([f"Last 5 ad sessions for user {results[0]['user_id']}"])
            writer.writerow(list(results[0].keys()))
            for row in results:
                writer.writerow([row.get(k, "") for k in results[0].keys()])
            writer.writerow([])
            writer.writerow([])
        return results

    def query_ad_clicks_per_hour_per_campaign(self, writer):
        if self.mongo_db is None:
            print("MongoDB connection is not initialized.")
            return None
        # I select an adviser that has clicks
        advertiser_id = 49
        # I select a date from the DB
        target_date_str = "2024-10-11"
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        next_day = target_date + timedelta(days=1)

        pipeline = [
            {"$unwind": "$impressions"},
            {"$match": {
                "impressions.advertiser_id": advertiser_id,
                "impressions.clicked": True,
                "impressions.timestamp": {
                    "$gte": target_date,
                    "$lt": next_day
                }
            }},
            {"$group": {
                "_id": {
                    "campaign_id": "$impressions.campaign_id",
                    "hour": {"$hour": "$impressions.timestamp"}
                },
                "clicks": {"$sum": 1}
            }},
            {"$sort": {"_id.campaign_id": 1, "_id.hour": 1}}
        ]

        results = list(self.mongo_db["ad_sessions"].aggregate(pipeline))

        if not results:
            print(f"No ad clicks found for {target_date_str}.")
            return None

        print(f"Ad clicks per hour on {target_date_str}:")
        for r in results:
            print(f"Campaign {r['_id']['campaign_id']} Hour {r['_id']['hour']}: {r['clicks']} clicks")

        # Write to CSV
        if results:
            writer.writerow([f"Ad clicks per hour per campaign for advertiser {advertiser_id} on {target_date_str}"])
            writer.writerow(["campaign_id", "hour", "clicks"])
            for row in results:
                writer.writerow([
                    row["_id"].get("campaign_id", ""),
                    row["_id"].get("hour", ""),
                    row.get("clicks", "")
                ])
            writer.writerow([])
            writer.writerow([])
        return results

    def query_top_3_ad_categories_for_user(self, writer):
        if self.mongo_db is None:
            print("MongoDB connection is not initialized.")
            return None
        """Retrieve a user's top 3 most engaged ad categories based on past clicks."""
        pipeline = [
            {"$match": {"user_id": 541198 }}, # this user has clicks
            # get all sessions for that user
            {"$lookup": {
                "from": "ad_sessions",
                "localField": "user_id",
                "foreignField": "user_id",
                "as": "sessions"
            }},
            {"$unwind": "$sessions"},
            {"$unwind": "$sessions.impressions"},
            # get for only clicked impressions
            {"$match": {"sessions.impressions.clicked": True}},
            # group by campaign_interest
            {"$group": {
                "_id": "$sessions.impressions.campaign_interest",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            # get top 3
            {"$limit": 3}
        ]

        results = list(self.mongo_db["ad_sessions"].aggregate(pipeline))

        if not results:
            print("No user or clicked impressions found.")
            return None

        print("Top 3 engaged ad categories for a user 541198:")
        for r in results:
            category = r["_id"] or "Unknown"
            print(f"Category: {category}, Clicks: {r['count']}")

        # Write to CSV
        if results:
            writer.writerow(["Top 3 most engaged ad categories for user 541198"])
            writer.writerow(["category", "clicks"])
            for row in results:
                writer.writerow([
                    row.get("_id", "Unknown"),
                    row.get("count", "")
                ])
            writer.writerow([])
            writer.writerow([])
        return results

    def query_users_with_repeated_impressions_no_clicks(self, writer):
        if self.mongo_db is None:
            print("MongoDB connection is not initialized.")
            return None
        """Find users who have seen the same ad 5+ times but never clicked."""
        pipeline = [
            {"$unwind": "$impressions"},
            {"$group": {
                "_id": {"user_id": "$user_id", "impression_id": "$impressions.impression_id"},
                "count": {"$sum": 1},
                "clicked": {"$max": "$impressions.clicked"}
            }},
            {"$match": {"count": {"$gte": 5}, "clicked": False}},
            {"$group": {"_id": "$_id.user_id", "ads": {"$addToSet": "$_id.impression_id"}}},
            {"$match": {"ads.0": {"$exists": True}}}
        ]
        results = list(self.mongo_db["ad_sessions"].aggregate(pipeline))
        if not results:
            print("No such data found.")
            return None
        for r in results[:10]:
            print(f"User {r['_id']} saw ads {r['ads']} 5+ times but never clicked.")
        if len(results) > 10:
            print(f"...and {len(results) - 10} more.")
        # Write to CSV
        if results:
            writer.writerow(["Users who have seen the same ad 5+ times but never clicked"])
            writer.writerow(["user_id", "ad_ids"])
            for row in results:
                writer.writerow([
                    row.get("_id", ""),
                    ", ".join(str(ad) for ad in row.get("ads", []))
                ])
            writer.writerow([])
            writer.writerow([])
        return results


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Insert data into MongoDB')

    parser.add_argument('--host', default='localhost', help='MongoDB host (default: localhost)')
    parser.add_argument('--database', default='set_db', help='MongoDB database name (default: set_db)')
    parser.add_argument('--user', default='set_user', help='MongoDB user (default: set_user)')
    parser.add_argument('--password', default='set_password', help='MongoDB password (default: set_password)')
    parser.add_argument('--port', default=27017, help='MongoDB port (default: 27017)')

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    perf_report = PerformanceReportMongo(
        host=args.host,
        database=args.database,
        user=args.user,
        password=args.password,
        port=args.port,
    )

    try:
        perf_report.execute_queries()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        perf_report.close()