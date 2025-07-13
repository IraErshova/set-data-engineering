import pandas as pd
from cassandra.cluster import Cluster


class CassandraDataInserter:
    def __init__(self, host: str = 'localhost', port: int = 9042, keyspace: str = 'my_keyspace'):
        self.advertisers_df = None
        self.users_df = None
        self.campaigns_df = None
        self.events_df = None
        self.host = host
        self.port = port
        self.keyspace = keyspace
        self.cluster = None
        self.session = None
        self.campaign_mapper = {}
        self.advertiser_mapper = {}
        self._connect()

    def _connect(self):
        try:
            self.cluster = Cluster([self.host], port=self.port)
            self.session = self.cluster.connect(self.keyspace)
            print(f"Connected to Cassandra cluster with keyspace: {self.keyspace}")
        except Exception as err:
            print(f"Error connecting to Cassandra: {err}")
            raise

    def load_csv_data(self):
        """Load CSV files from the specified directory"""
        try:
            events_path = "dataset_normalized/ad_events.csv"
            campaigns_path = "dataset_normalized/campaigns.csv"
            users_path = "dataset_normalized/users.csv"
            advertisers_path = "csv_data/advertisers.csv"

            print("Loading CSV files...")
            self.events_df = pd.read_csv(events_path, parse_dates=["Timestamp", "ClickTimestamp"])
            self.campaigns_df = pd.read_csv(campaigns_path)
            self.users_df = pd.read_csv(users_path)
            self.advertisers_df = pd.read_csv(advertisers_path)

            print(f"Loaded data from csv files")

            # Create mappings
            self._create_mappings()

        except Exception as err:
            print(f"Error loading CSV data: {err}")
            raise

    def _create_mappings(self):
        # Create a mapping of campaign names to campaign IDs for quick lookup
        self.campaign_mapper = dict(zip(self.campaigns_df['CampaignName'], self.campaigns_df['CampaignID']))

        # Advertiser name to id mapping
        self.advertiser_mapper = dict(zip(self.advertisers_df['advertiser_name'], self.advertisers_df['advertiser_id']))

        print(f"Created mappings for campaigns and advertisers")

    def insert_user_engagement_history(self):
        """Insert user engagement history data"""
        if self.session is None:
            raise Exception("Session is not initialized.")

        print("Inserting user engagement history...")

        user_engagement_stmt = self.session.prepare("""
            INSERT INTO user_engagement_history (user_id, timestamp, advertiser_id, campaign_id, action)
            VALUES (?, ?, ?, ?, ?)
        """)

        for _, row in self.events_df.iterrows():
            try:
                user_id = int(row['UserID'])
                timestamp = pd.to_datetime(row['Timestamp'])
                advertiser_id = self.advertiser_mapper[row['AdvertiserName']]
                campaign_id = self.campaign_mapper[row['CampaignName']]
                action = "click" if bool(row["WasClicked"]) else "impression"

                self.session.execute(user_engagement_stmt, (user_id, timestamp, advertiser_id, campaign_id, action))
            except Exception as err:
                print(f"Error inserting user engagement row: {err}")
                continue

        print("User engagement history inserted successfully")

    def insert_ad_campaign_performance(self):
        """Insert ad campaign performance by day data"""
        if self.session is None:
            raise Exception("Session is not initialized.")

        print("Inserting ad campaign performance by day...")

        # Aggregate performance data
        perf_data = self.events_df.groupby(["CampaignName", self.events_df["Timestamp"].dt.date]).agg(
            impressions=("WasClicked", "count"),
            clicks=("WasClicked", "sum")
        ).reset_index()

        perf_stmt = self.session.prepare("""
            UPDATE ad_campaign_performance_by_day
            SET impressions = impressions + ?, clicks = clicks + ?
            WHERE campaign_id = ? AND date = ?
        """)

        for _, row in perf_data.iterrows():
            try:
                campaign_id = self.campaign_mapper[row["CampaignName"]]
                self.session.execute(perf_stmt, (
                    int(row["impressions"]),
                    int(row["clicks"]),
                    campaign_id,
                    row["Timestamp"]
                ))
            except Exception as err:
                print(f"Error inserting campaign performance row: {err}")
                continue

        print("Ad campaign performance inserted successfully")

    def insert_user_activity_by_day(self):
        """Insert user activity by day data"""
        if self.session is None:
            raise Exception("Session is not initialized.")

        print("Inserting user activity by day...")

        # Aggregate user activity
        user_activity = self.events_df.groupby([self.events_df["Timestamp"].dt.date, "UserID"]).agg(
            impressions=("WasClicked", "count"),
            clicks=("WasClicked", "sum")
        ).reset_index()

        activity_stmt = self.session.prepare("""
            INSERT INTO user_activity_by_day (day, impressions, clicks, user_id)
            VALUES (?, ?, ?, ?)
        """)

        for _, row in user_activity.iterrows():
            try:
                self.session.execute(activity_stmt, (
                    row["Timestamp"],
                    int(row["impressions"]),
                    int(row["clicks"]),
                    int(row["UserID"])
                ))
            except Exception as err:
                print(f"Error inserting user activity row: {err}")
                continue

        print("User activity by day inserted successfully")

    def insert_top_advertisers_by_spend(self):
        """Insert top advertisers by spend data"""
        if self.session is None:
            raise Exception("Session is not initialized.")

        print("Inserting top advertisers by spend...")

        # Add day column and aggregate spend data
        self.events_df["Day"] = self.events_df["Timestamp"].dt.date
        spend_data = self.events_df.groupby(["Day", "AdvertiserName"]).agg(
            total_spend=("AdCost", "sum")
        ).reset_index()

        spend_stmt = self.session.prepare("""
            INSERT INTO top_advertisers_by_spend (day, advertiser_id, advertiser_name, total_spend)
            VALUES (?, ?, ?, ?)
        """)

        for _, row in spend_data.iterrows():
            try:
                self.session.execute(spend_stmt, (
                    row["Day"],
                    self.advertiser_mapper[row["AdvertiserName"]],
                    row["AdvertiserName"],
                    float(row["total_spend"])
                ))
            except Exception as err:
                print(f"Error inserting advertiser spend row: {err}")
                continue

        print("Top advertisers by spend inserted successfully")

    def insert_advertiser_spend_by_region(self):
        """Insert advertiser spend by region data"""
        if self.session is None:
            raise Exception("Session is not initialized.")

        print("Inserting advertiser spend by region...")

        # Aggregate region data
        region_data = self.events_df.groupby(["Location", "AdvertiserName"]).agg(
            total_spend=("AdCost", "sum")
        ).reset_index()

        region_stmt = self.session.prepare("""
            INSERT INTO advertiser_spend_by_region (region, advertiser_id, advertiser_name, total_spend)
            VALUES (?, ?, ?, ?)
        """)

        for _, row in region_data.iterrows():
            try:
                region = str(row["Location"])
                advertiser_name = row["AdvertiserName"]
                self.session.execute(region_stmt, (
                    region,
                    self.advertiser_mapper[advertiser_name],
                    advertiser_name,
                    float(row["total_spend"])
                ))
            except Exception as err:
                print(f"Error inserting region spend row: {err}")
                continue

        print("Advertiser spend by region inserted successfully")

    def insert_all_data(self):
        """Insert all data into Cassandra tables"""
        try:
            self.load_csv_data()

            # Insert data into all tables
            self.insert_user_engagement_history()
            self.insert_ad_campaign_performance()
            self.insert_user_activity_by_day()
            self.insert_top_advertisers_by_spend()
            self.insert_advertiser_spend_by_region()

            print("All data inserted into Cassandra successfully!")

        except Exception as err:
            print(f"Error inserting data: {err}")
            raise

    def close(self):
        """Close the Cassandra connection"""
        if self.session:
            self.session.shutdown()
        if self.cluster:
            self.cluster.shutdown()
        print("Cassandra connection closed")


if __name__ == "__main__":
    inserter = None
    try:
        inserter = CassandraDataInserter()
        inserter.insert_all_data()
    except Exception as error:
        print(f"Exception: {error}")
    finally:
        if inserter:
            inserter.close()
