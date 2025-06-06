import mysql.connector
from mysql.connector import Error
import argparse
import sys
from typing import List, Tuple
from py_scripts.data_transformer import DataTransformer


class DataInserter:
    def __init__(self, host: str = 'localhost', database: str = 'set_db',
                 user: str = 'set_user', password: str = 'set_password'):
        """Initialize the inserter with MySQL database connection"""
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.cursor = None
        self.advertiser_mapping = None
        self._connect_to_mysql()

    def _connect_to_mysql(self):
        """connection to database"""
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                use_unicode=True
            )
            self.cursor = self.conn.cursor()
            print(f"Successfully connected to MySQL database: {self.database}")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise

    def insert_advertisers(self, advertisers_data: List[Tuple[str]]):
        """Insert advertisers into the database"""
        print("Inserting advertisers")
        try:
            self.cursor.executemany(
                "INSERT IGNORE INTO advertisers (advertiser_name) VALUES (%s)",
                advertisers_data
            )
            self.conn.commit()

            # Create advertiser mapping for later use
            self.cursor.execute("SELECT advertiser_id, advertiser_name FROM advertisers")
            self.advertiser_mapping = {name: id for id, name in self.cursor.fetchall()}
            print(f"Loaded {len(advertisers_data)} advertisers")
        except Error as e:
            print(f"Error inserting advertisers: {e}")
            raise

    def insert_campaigns(self, campaigns_data: List[Tuple]):
        """Insert campaigns into the database"""
        print("Inserting campaigns")
        insert_query = """
                       INSERT INTO campaigns
                       (campaign_id, advertiser_id, campaign_name, campaign_start_date,
                        campaign_end_date, targeting_criteria, ad_slot_size, budget, remaining_budget)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY
                       UPDATE
                           campaign_name =
                       VALUES (campaign_name), campaign_start_date =
                       VALUES (campaign_start_date), campaign_end_date =
                       VALUES (campaign_end_date), targeting_criteria =
                       VALUES (targeting_criteria), ad_slot_size =
                       VALUES (ad_slot_size), budget =
                       VALUES (budget), remaining_budget =
                       VALUES (remaining_budget) \
                       """

        # Transform campaign data to include advertiser_id
        # Use campaign[1] to find the advertiser_id from the mappin
        # replace the advertiser name with advertiser_id
        # only includes campaigns for which the advertiser_id exists (skip unknown advertisers)
        transformed_data = []
        for campaign in campaigns_data:
            advertiser_id = self.advertiser_mapping.get(campaign[1])
            if advertiser_id:
                transformed_data.append((
                    campaign[0],  # campaign_id
                    advertiser_id,  # advertiser_id
                    campaign[2],  # campaign_name
                    campaign[3],  # campaign_start_date
                    campaign[4],  # campaign_end_date
                    campaign[5],  # targeting_criteria
                    campaign[6],  # ad_slot_size
                    campaign[7],  # budget
                    campaign[8]  # remaining_budget
                ))

        try:
            self.cursor.executemany(insert_query, transformed_data)
            self.conn.commit()
            print(f"Loaded {len(transformed_data)} campaigns")
        except Error as e:
            print(f"Error inserting campaigns: {e}")
            raise

    def insert_users(self, users_data: List[Tuple]):
        """Insert users into the database"""
        print("Inserting users")
        insert_query = """
                       INSERT INTO users
                           (user_id, age, gender, location, interests, signup_date)
                       VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY
                       UPDATE
                           age =
                       VALUES (age), gender =
                       VALUES (gender), location =
                       VALUES (location), interests =
                       VALUES (interests), signup_date =
                       VALUES (signup_date) \
                       """

        try:
            self.cursor.executemany(insert_query, users_data)
            self.conn.commit()
            print(f"Loaded {len(users_data)} users")
        except Error as e:
            print(f"Error inserting users: {e}")
            raise

    def insert_impressions_and_clicks(self, impressions_data: List[Tuple], clicks_data: List[Tuple]):
        """Insert ad impressions and clicks into the database"""
        print("Inserting impressions and clicks")

        # Insert impressions
        insert_impressions_query = """
                                   INSERT INTO ad_impressions
                                   (impression_id, campaign_id, user_id, device, user_location,
                                    impression_timestamp, bid_amount, ad_cost, ad_revenue)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY
                                   UPDATE
                                       campaign_id =
                                   VALUES (campaign_id), user_id =
                                   VALUES (user_id), device =
                                   VALUES (device), user_location =
                                   VALUES (user_location), impression_timestamp =
                                   VALUES (impression_timestamp), bid_amount =
                                   VALUES (bid_amount), ad_cost =
                                   VALUES (ad_cost), ad_revenue =
                                   VALUES (ad_revenue) \
                                   """
        try:
            self.cursor.executemany(insert_impressions_query, impressions_data)
            print(f"Loaded {len(impressions_data)} impressions")
        except Error as e:
            print(f"Error inserting impressions: {e}")
            raise

        # Insert clicks
        if clicks_data:
            insert_clicks_query = """
                                  INSERT INTO ad_clicks
                                      (impression_id, click_timestamp)
                                  VALUES (%s, %s) ON DUPLICATE KEY
                                  UPDATE
                                      click_timestamp =
                                  VALUES (click_timestamp) \
                                  """
            try:
                self.cursor.executemany(insert_clicks_query, clicks_data)
                print(f"Loaded {len(clicks_data)} clicks")
            except Error as e:
                print(f"Error inserting clicks: {e}")
                raise

        self.conn.commit()

    def close(self):
        """
        Close the database connection
        """
        if self.conn:
            self.conn.close()


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Transform and load advertising data into MySQL database')

    parser.add_argument('--host', default='localhost', help='MySQL host (default: localhost)')
    parser.add_argument('--database', default='set_db', help='MySQL database name (default: set_db)')
    parser.add_argument('--user', default='set_user', help='MySQL user (default: set_user)')
    parser.add_argument('--password', default='set_password', help='MySQL password (default: set_password)')

    return parser.parse_args()


def transform_and_insert_data():
    args = parse_args()
    # Initialize Inserter
    inserter = DataInserter(
        host=args.host,
        database=args.database,
        user=args.user,
        password=args.password
    )
    # Initialize transformer
    transformer = DataTransformer()

    try:
        # Load and transform data
        transformer.load_and_process_data(
            ad_events_file="dataset_normalized/ad_events.csv",
            campaigns_file="dataset_normalized/campaigns.csv",
            users_file="dataset_normalized/users.csv"
        )

        # Extract and transform data
        advertisers_data = transformer.extract_advertisers()
        campaigns_data = transformer.transform_campaigns()
        users_data = transformer.transform_users()

        transformer.create_campaign_mapping()

        # Insert data in correct order
        inserter.insert_users(users_data)
        inserter.insert_advertisers(advertisers_data)
        inserter.insert_campaigns(campaigns_data)

        # Transform and insert impressions and clicks
        impressions_data, clicks_data = transformer.transform_impressions_and_clicks()
        inserter.insert_impressions_and_clicks(impressions_data, clicks_data)

        print("Data transformation and loading completed successfully!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'inserter' in locals():
            inserter.close()
