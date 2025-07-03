#!/usr/bin/env python3
import os
from collections import defaultdict
from datetime import datetime, timezone
import pandas as pd
import pymongo
import argparse
from tqdm import tqdm


def parse_int(val):
    try:
        return int(val)
    except Exception:
        return 0


def parse_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0


def parse_date(val):
    # Expecting ISO format or timestamp
    try:
        return datetime.fromisoformat(val)
    except Exception:
        try:
            return datetime.fromtimestamp(float(val), timezone.utc)
        except Exception:
            return None


class DatabaseManager:
    def __init__(self, host: str = 'localhost', database: str = 'set_db',
                 user: str = 'set_user', password: str = 'set_password', port: int = 27017) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.mongo_client = None
        self.mongo_db = None
        self.ad_events = None
        self.campaigns = None
        self.advertisers = None
        self.users = None
        self._connect_mongodb()

    def _connect_mongodb(self):
        try:
            self.mongo_client = pymongo.MongoClient(
                host=self.host,
                port=27017,
                username=self.user,
                password=self.password,
                authSource=self.database,
            )
            self.mongo_db = self.mongo_client[self.database]
            self.mongo_db.command({'ping': 1})

            print("Pinged your deployment. You successfully connected to MongoDB!")

        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def close_connections(self):
        if self.mongo_client:
            self.mongo_client.close()

    def load_datasets(self, ad_events_file: str, campaigns_file: str, users_file: str, advertisers_file: str):
        print("Loading CSV files...")

        # Verify files exist
        for file_path in [ad_events_file, campaigns_file, users_file, advertisers_file]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

        # Load data
        self.ad_events = pd.read_csv(ad_events_file)
        self.advertisers = pd.read_csv(advertisers_file)
        self.campaigns = pd.read_csv(campaigns_file)
        self.users = pd.read_csv(users_file)

        print(f"Loaded {len(self.ad_events)} ad events, {len(self.campaigns)} campaigns, {len(self.users)} users")

    def insert_all_sessions_to_mongo(self):
        collection = self.mongo_db.ad_sessions
        # Group impressions by (user_id, device)
        sessions = defaultdict(list)
        try:
            for _, row in tqdm(self.ad_events.iterrows(), total=len(self.ad_events), desc="Processing ad events"):
                user_id = parse_int(row['UserID'])
                device = row['Device']
                key = (user_id, device)
                # Handle click events
                click_events = []
                click_time = parse_date(row.get('ClickTimestamp'))
                if click_time is not None:
                    click_events.append({'click_timestamp': click_time})

                campaign_data = self.campaigns.loc[
                    self.campaigns['CampaignName'] == row['CampaignName'],
                    ['CampaignID', 'interest', 'country']
                ].iloc[0]

                advertiser_id = self.advertisers.loc[
                    self.advertisers['advertiser_name'] == row['AdvertiserName'], 'advertiser_id']
                impression = {
                    'impression_id': row['EventID'],
                    'campaign_id': int(campaign_data['CampaignID']),
                    'campaign_interest': campaign_data['interest'],
                    'campaign_location': campaign_data['country'],
                    'campaign_name': row.get('CampaignName', ''),
                    'advertiser_id': int(advertiser_id.values[0]),
                    'timestamp': parse_date(row['Timestamp']),
                    'location': row.get('Location'),
                    'bid_amount': parse_float(row.get('BidAmount', 0)),
                    'ad_cost': parse_float(row.get('AdCost', 0)),
                    'ad_revenue': parse_float(row.get('AdRevenue', 0)),
                    'clicked': {'True': True, 'False': False, True: True, False: False, '': False}.get(
                        row.get('WasClicked', ''), False),
                    'click_events': click_events
                }
                sessions[key].append(impression)

            # Build session docs
            session_docs = []
            for (user_id, device), impressions in sessions.items():
                timestamps = [imp['timestamp'] for imp in impressions]
                session_doc = {
                    'user_id': user_id,
                    'device': device,
                    # mock session_start and session_end
                    'session_start': min(timestamps) if timestamps else datetime.now(timezone.utc),
                    'session_end': max(timestamps) if timestamps else datetime.now(timezone.utc),
                    'impressions': impressions
                }
                session_docs.append(session_doc)

            if session_docs:
                collection.insert_many(session_docs)
                print(f"Inserted {len(session_docs)} sessions.")
                return True
            else:
                print("No sessions to insert.")
                return False

        except Exception as e:
            print(f"Failed to insert sessions: {e}")
            return False

    def insert_all_users_to_mongo(self):
        if self.users is None:
            print("Users data is not loaded.")
            return False
        try:
            collection = self.mongo_db.user_interaction
            user_docs = []
            for _, row in tqdm(self.users.iterrows(), total=len(self.users), desc="Processing users"):
                interests_str = str(row.get('Interests', ''))
                if interests_str.lower() == 'nan' or interests_str.strip() == '':
                    interests_list = []
                else:
                    interests_list = [i.strip() for i in interests_str.split(',')]
                signup_date_val = row.get('SignupDate', None)
                if signup_date_val is not None and not pd.isna(signup_date_val):
                    signup_date = pd.to_datetime(signup_date_val)
                else:
                    signup_date = None
                user_doc = {
                    'user_id': int(row.get('UserID')),
                    'demographics': {
                        'age': int(row.get('Age')),
                        'gender': row.get('Gender', None),
                        'interests': interests_list,
                        'location': row.get('Location', None)
                    },
                    'signup_date': signup_date,
                    'created_at': datetime.now(timezone.utc),
                    'updated_at': datetime.now(timezone.utc),
                    'interaction_history': {
                        'total_impressions': 0,
                        'total_clicks': 0
                    }
                }
                user_docs.append(user_doc)
            if len(user_docs) > 0:
                result = collection.insert_many(user_docs)
                print(f"Inserted {len(result.inserted_ids)} users into user_interaction collection.")
                return True
            else:
                print("No user documents to insert.")
                return False
        except Exception as e:
            print(f"Failed to insert users: {e}")
            return False


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Insert data into MongoDB')

    parser.add_argument('--host', default='localhost', help='MongoDB host (default: localhost)')
    parser.add_argument('--database', default='set_db', help='MongoDB database name (default: set_db)')
    parser.add_argument('--user', default='set_user', help='MongoDB user (default: set_user)')
    parser.add_argument('--password', default='set_password', help='MongoDB password (default: set_password)')
    parser.add_argument('--port', default=27017, help='MongoDB port (default: 27017)')

    return parser.parse_args()


def insert_data_to_mongo():
    args = parse_args()
    db_manager = DatabaseManager(
        host=args.host,
        database=args.database,
        user=args.user,
        password=args.password,
        port=args.port,
    )

    print(db_manager.mongo_db)

    try:
        # Load and transform data
        db_manager.load_datasets(
            ad_events_file="dataset_normalized/ad_events.csv",
            campaigns_file="dataset_normalized/campaigns.csv",
            users_file="dataset_normalized/users.csv",
            advertisers_file="csv_data/advertisers.csv",
        )
        # Insert all users into MongoDB
        users = db_manager.insert_all_users_to_mongo()
        print(f"Users insert result: {users}")

        sessions = db_manager.insert_all_sessions_to_mongo()
        print(f"Sessions insert result: {sessions}")

    except Exception as e:
        print(e)
        return None
    finally:
        db_manager.close_connections()
