import pandas as pd
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import RoundRobinPolicy
from cassandra.query import dict_factory
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


class CassandraDataInserter:
    def __init__(self, host: str = 'localhost', port: int = 9042, keyspace: str = 'my_keyspace', max_workers: int = 5):
        self.advertisers_df = None
        self.users_df = None
        self.campaigns_df = None
        self.events_df = None
        self.host = host
        self.port = port
        self.keyspace = keyspace
        self.max_workers = max_workers
        self.cluster = None
        self.session = None
        self.campaign_mapper = {}
        self.advertiser_mapper = {}
        self._connect()

    def _connect(self):
        try:
            profile = ExecutionProfile(
                request_timeout=30.0,
                load_balancing_policy=RoundRobinPolicy(),
                row_factory=dict_factory
            )

            self.cluster = Cluster([self.host], port=self.port, execution_profiles={EXEC_PROFILE_DEFAULT: profile})
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
            # select only 500k rows for efficiency
            self.events_df = pd.read_csv(
                events_path,
                nrows=500_000,
                parse_dates=["Timestamp", "ClickTimestamp"]
            )
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

    def _insert_with_executor(self, rows, worker_fn, label):
        print(f"Inserting {label}...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(worker_fn, row) for _, row in rows.iterrows()]
            results = []
            for f in tqdm(as_completed(futures), total=len(futures), desc=label):
                results.append(f.result())

        success_count = sum(results)
        failed_count = len(results) - success_count
        print(f"{label}: {success_count} inserted, {failed_count} failed")

    def _insert_user_engagement_row(self, row):
        user_id = int(row['UserID'])
        try:
            user_engagement_stmt = self.session.prepare("""
                INSERT INTO user_engagement_history (user_id, timestamp, advertiser_id, campaign_id, action)
                VALUES (?, ?, ?, ?, ?)
            """)
            
            timestamp = pd.to_datetime(row['Timestamp'])
            advertiser_id = self.advertiser_mapper[row['AdvertiserName']]
            campaign_id = self.campaign_mapper[row['CampaignName']]
            action = "click" if bool(row["WasClicked"]) else "impression"

            self.session.execute(user_engagement_stmt, (user_id, timestamp, advertiser_id, campaign_id, action))
            return True
        except Exception as err:
            print(f"Error inserting user engagement row with user_id {user_id}: {err}")
            return False

    def insert_user_engagement_history(self):
        self._insert_with_executor(self.events_df, self._insert_user_engagement_row, "user engagement history")

    def _insert_campaign_performance_row(self, row):
        campaign_id = self.campaign_mapper[row["CampaignName"]]
        try:
            perf_stmt = self.session.prepare("""
                UPDATE ad_campaign_performance_by_day
                SET impressions = impressions + ?, clicks = clicks + ?
                WHERE campaign_id = ? AND date = ?
            """)
            
            self.session.execute(perf_stmt, (
                int(row["impressions"]),
                int(row["clicks"]),
                campaign_id,
                row["Timestamp"]
            ))
            return True
        except Exception as err:
            print(f"Error inserting campaign performance row with campaign_id {campaign_id}: {err}")
            return False

    def insert_ad_campaign_performance(self):
        # Aggregate performance data
        perf_data = self.events_df.groupby(["CampaignName", self.events_df["Timestamp"].dt.date]).agg(
            impressions=("WasClicked", "count"),
            clicks=("WasClicked", "sum")
        ).reset_index()

        self._insert_with_executor(perf_data, self._insert_campaign_performance_row, "ad campaign performance by day")

    def _insert_user_activity_row(self, row):
        user_id = int(row['UserID'])
        try:
            activity_stmt = self.session.prepare("""
                INSERT INTO user_activity_by_day (day, impressions, clicks, user_id)
                VALUES (?, ?, ?, ?)
            """)
            self.session.execute(activity_stmt, (
                row["Timestamp"],
                int(row["impressions"]),
                int(row["clicks"]),
                user_id
            ))
            return True
        except Exception as err:
            print(f"Error inserting user activity row with user_id {user_id}: {err}")
            return False

    def insert_user_activity_by_day(self):
        # Aggregate user activity
        user_activity = None
        try:
            user_activity = self.events_df.groupby([self.events_df["Timestamp"].dt.date, "UserID"]).agg(
                impressions=("WasClicked", "count"),
                clicks=("WasClicked", "sum")
            ).reset_index()

        except Exception as err:
            print(err)

        self._insert_with_executor(user_activity, self._insert_user_activity_row, "user activity by day")

    def _insert_advertiser_spend_row(self, row):
        advertiser_id = self.advertiser_mapper[row["AdvertiserName"]]
        try:
            spend_stmt = self.session.prepare("""
                INSERT INTO top_advertisers_by_spend (day, advertiser_id, advertiser_name, total_spend)
                VALUES (?, ?, ?, ?)
            """)

            self.session.execute(spend_stmt, (
                row["Day"],
                advertiser_id,
                row["AdvertiserName"],
                float(row["total_spend"])
            ))
            return True
        except Exception as err:
            print(f"Error inserting advertiser spend row advertiser_id {advertiser_id}: {err}")
            return False

    def insert_top_advertisers_by_spend(self):
        # Add day column and aggregate spend data
        self.events_df["Day"] = self.events_df["Timestamp"].dt.date
        spend_data = self.events_df.groupby(["Day", "AdvertiserName"]).agg(
            total_spend=("AdCost", "sum")
        ).reset_index()

        self._insert_with_executor(spend_data, self._insert_advertiser_spend_row, "top advertisers by spend")

    def _insert_region_spend_row(self, row):
        advertiser_id = self.advertiser_mapper[row["AdvertiserName"]]
        try:
            region_stmt = self.session.prepare("""
                INSERT INTO advertiser_spend_by_region (region, advertiser_id, advertiser_name, total_spend)
                VALUES (?, ?, ?, ?)
            """)

            region = str(row["Location"])
            advertiser_name = row["AdvertiserName"]
            self.session.execute(region_stmt, (
                region,
                advertiser_id,
                advertiser_name,
                float(row["total_spend"])
            ))
            return True
        except Exception as err:
            print(f"Error inserting region spend row advertiser_id {advertiser_id}: {err}")
            return False

    def insert_advertiser_spend_by_region(self):
        # Aggregate region data
        region_data = self.events_df.groupby(["Location", "AdvertiserName"]).agg(
            total_spend=("AdCost", "sum")
        ).reset_index()

        self._insert_with_executor(region_data, self._insert_region_spend_row, "Advertiser spend by region")

    def _insert_region_spend_day_row(self, row):
        advertiser_id = self.advertiser_mapper[row["AdvertiserName"]]
        try:
            region_stmt = self.session.prepare("""
                INSERT INTO advertiser_spend_by_region_day (region, day, advertiser_id, advertiser_name, total_spend)
                VALUES (?, ?, ?, ?, ?)
            """)

            region = str(row["Location"])
            advertiser_name = row["AdvertiserName"]
            day = row["day"] # just a day, not full datetime
            self.session.execute(region_stmt, (
                region,
                day,
                advertiser_id,
                advertiser_name,
                float(row["total_spend"])
            ))
            return True
        except Exception as err:
            print(f"Error inserting region-day spend row advertiser_id {advertiser_id}: {err}")
            return False

    def insert_advertiser_spend_by_region_day(self):
        # Aggregate by day, location, and advertiser
        region_data = self.events_df.groupby([
            self.events_df["Timestamp"].dt.date,  # Extract only date part
            "Location",
            "AdvertiserName"
        ]).agg(
            total_spend=("AdCost", "sum")
        ).reset_index().rename(columns={"Timestamp": "day"})

        self._insert_with_executor(region_data, self._insert_region_spend_day_row, "Advertiser spend by region day")

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
            self.insert_advertiser_spend_by_region_day()

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
        inserter = CassandraDataInserter(max_workers=10)
        inserter.insert_all_data()
    except Exception as error:
        print(f"Exception: {error}")
    finally:
        if inserter:
            inserter.close()
