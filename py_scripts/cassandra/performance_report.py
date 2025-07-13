from cassandra.cluster import Cluster
from collections import defaultdict
from datetime import date, timedelta

selected_date = date.fromisoformat('2024-10-30')

class CassandraPerformanceReport:
    def __init__(self, host: str = 'localhost', port: int = 9042, keyspace: str = 'my_keyspace'):
        self.host = host
        self.port = port
        self.keyspace = keyspace
        self.cluster = None
        self.session = None
        self.start_date = selected_date - timedelta(days=30)
        self._connect()

    def _connect(self):
        try:
            self.cluster = Cluster([self.host], port=self.port)
            self.session = self.cluster.connect(self.keyspace)
            print("Connected to Cassandra cluster")
        except Exception as e:
            print(f"Error connecting to Cassandra: {e}")
            raise

    def query_1_ctr_per_campaign_day(self, campaign_id, day):
        rows = self.session.execute(
            "SELECT clicks, impressions FROM ad_campaign_performance_by_day WHERE campaign_id=%s AND date=%s",
            (campaign_id, day)
        )
        for row in rows:
            impressions = row.impressions
            clicks = row.clicks
            ctr = (clicks / impressions) * 100 if impressions > 0 else 0
            print(f"[Query 1] Campaign {campaign_id} on {day}: CTR = {ctr:.2f}%")

    def query_2_top5_advertisers_spend(self):
        spend = defaultdict(float)
        for i in range(31):
            d = self.start_date + timedelta(days=i)
            rows = self.session.execute(
                "SELECT advertiser_id, total_spend FROM top_advertisers_by_spend WHERE day=%s", (d,)
            )
            for row in rows:
                spend[row.advertiser_id] += float(row.total_spend)

        top5 = sorted(spend.items(), key=lambda x: x[1], reverse=True)[:5]
        print("[Query 2] Top 5 advertisers by spend in the past 30 days:")
        for adv_id, total in top5:
            print(f"Advertiser {adv_id}: ${total:.2f}")

    def query_3_last_10_ads(self, user_id):
        rows = self.session.execute(
            "SELECT timestamp, advertiser_id, campaign_id, action FROM user_engagement_history WHERE user_id=%s LIMIT 50",
            (user_id,)
        )

        impressions = []
        clicks_by_campaign = set()

        for row in rows:
            if row.action == 'click':
                clicks_by_campaign.add(row.campaign_id)
            elif row.action == 'impression':
                impressions.append(row)

        print(f"[Query 3] Last 10 ads seen by user {user_id}:")
        for imp in impressions[:10]:
            clicked = 'Yes' if imp.campaign_id in clicks_by_campaign else 'No'
            print(
                f"{imp.timestamp}: Campaign {imp.campaign_id} from Advertiser {imp.advertiser_id} - Clicked: {clicked}")

    def query_4_top10_users_clicks(self):
        user_clicks = defaultdict(int)
        for i in range(31):
            d = self.start_date + timedelta(days=i)
            rows = self.session.execute(
                "SELECT user_id, clicks FROM user_activity_by_day WHERE day=%s", (d,)
            )
            for row in rows:
                user_clicks[row.user_id] += row.clicks

        top10 = sorted(user_clicks.items(), key=lambda x: x[1], reverse=True)[:10]
        print("[Query 4] Top 10 users by clicks (30d):")
        for user_id, clicks in top10:
            print(f"User {user_id}: {clicks} clicks")

    def query_5_top5_advertisers_by_region(self, region):
        advertiser_spend = defaultdict(float)
        for i in range(31):
            d = self.start_date + timedelta(days=i)
            rows = self.session.execute(
                "SELECT advertiser_id, total_spend FROM advertiser_spend_by_region_day WHERE region=%s AND day=%s",
                (region, d)
            )
            for row in rows:
                advertiser_spend[row.advertiser_id] += float(row.total_spend)

        top5 = sorted(advertiser_spend.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"[Query 5] Top 5 advertisers by spend in {region} (30d):")
        for adv_id, total in top5:
            print(f"Advertiser {adv_id}: ${total:.2f}")

    def close(self):
        if self.session:
            self.session.shutdown()
        if self.cluster:
            self.cluster.shutdown()

if __name__ == "__main__":
    manager = None
    try:
        manager = CassandraPerformanceReport()

        manager.query_1_ctr_per_campaign_day(campaign_id=110, day=selected_date - timedelta(days=1))
        manager.query_2_top5_advertisers_spend()
        manager.query_3_last_10_ads(user_id=31676)
        manager.query_4_top10_users_clicks()
        manager.query_5_top5_advertisers_by_region(region="USA")
    except Exception as err:
        print(f"Exception: {err}")
    finally:
        if manager:
            manager.close()