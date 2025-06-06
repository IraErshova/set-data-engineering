import pandas as pd
import os
import sys
from typing import Tuple
from tqdm import tqdm

class DataTransformer:
    def __init__(self):
        self.ad_events = None
        self.campaigns = None
        self.users = None
        self.campaign_mapping = None
        self.advertiser_mapping = None
        self.transformed_dir = "dataset_transformed"
        
        # Create directory if it doesn't exist
        if not os.path.exists(self.transformed_dir):
            os.makedirs(self.transformed_dir)

    def load_and_process_data(self, ad_events_file: str, campaigns_file: str, users_file: str):
        """Load CSV files and process them for normalization"""
        print("Loading CSV files...")

        # Verify files exist
        for file_path in [ad_events_file, campaigns_file, users_file]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

        # Load data
        self.ad_events = pd.read_csv(ad_events_file)
        self.campaigns = pd.read_csv(campaigns_file)
        self.users = pd.read_csv(users_file)

        print(f"Loaded {len(self.ad_events)} ad events, {len(self.campaigns)} campaigns, {len(self.users)} users")

        # Clean and prepare data
        self._clean_data()

    def _clean_data(self):
        self.ad_events['ClickTimestamp'] = self.ad_events['ClickTimestamp'].replace('', None)
        self.ad_events['WasClicked'] = self.ad_events['WasClicked'].astype(bool)

        # Convert date columns
        date_columns = ['CampaignStartDate', 'CampaignEndDate']
        for col in date_columns:
            if col in self.ad_events.columns:
                self.ad_events[col] = pd.to_datetime(self.ad_events[col]).dt.date
            if col in self.campaigns.columns:
                self.campaigns[col] = pd.to_datetime(self.campaigns[col]).dt.date

        self.ad_events['Timestamp'] = pd.to_datetime(self.ad_events['Timestamp'])

        if 'SignupDate' in self.users.columns:
            self.users['SignupDate'] = pd.to_datetime(self.users['SignupDate']).dt.date

        print("Data preparing finished")

        return self.ad_events, self.campaigns, self.users

    def extract_advertisers(self) -> str:
        """Extract unique advertisers from data and save to CSV"""
        print("Processing advertisers...")

        # Get unique advertisers from both ad_events and campaigns
        advertisers_from_events = set(self.ad_events['AdvertiserName'].dropna().unique())
        advertisers_from_campaigns = set(self.campaigns['AdvertiserName'].dropna().unique())
        unique_advertisers = advertisers_from_events.union(advertisers_from_campaigns)

        # Create DataFrame with advertiser_id starting from 1
        advertisers_df = pd.DataFrame({
            'advertiser_id': range(1, len(unique_advertisers) + 1),
            'advertiser_name': sorted(list(unique_advertisers))
        })
        
        # Create advertiser mapping for campaigns file
        self.advertiser_mapping = dict(zip(advertisers_df['advertiser_name'], advertisers_df['advertiser_id']))
        
        output_path = os.path.join(self.transformed_dir, 'advertisers.csv')
        advertisers_df.to_csv(output_path, index=False)
        print(f"Saved {len(unique_advertisers)} advertisers to {output_path}")
        
        return output_path

    def transform_campaigns(self) -> str:
        """Transform campaign data and save to CSV"""
        print("Processing campaigns")

        campaigns_data = []
        for _, row in tqdm(self.campaigns.iterrows(), total=len(self.campaigns), desc="Processing campaigns"):
            advertiser_id = self.advertiser_mapping.get(row['AdvertiserName'])
            if advertiser_id is None:
                print(f"Advertiser not found: {row['AdvertiserName']}")
                continue

            campaigns_data.append({
                'campaign_id': int(row['CampaignID']),
                'advertiser_id': advertiser_id,
                'campaign_name': str(row['CampaignName']),
                'campaign_start_date': row['CampaignStartDate'],
                'campaign_end_date': row['CampaignEndDate'],
                'targeting_criteria': str(row.get('TargetingCriteria', '')),
                'ad_slot_size': str(row.get('AdSlotSize', '')),
                'budget': float(row.get('Budget', 0)) if pd.notna(row.get('Budget', 0)) else 0.0,
                'remaining_budget': float(row.get('RemainingBudget', 0)) if pd.notna(row.get('RemainingBudget', 0)) else 0.0
            })

        # Create DataFrame and save to CSV
        campaigns_df = pd.DataFrame(campaigns_data)
        output_path = os.path.join(self.transformed_dir, 'campaigns.csv')
        campaigns_df.to_csv(output_path, index=False)
        print(f"Saved {len(campaigns_data)} campaigns to {output_path}")
        
        return output_path

    def transform_users(self) -> str:
        """Transform user data and save to CSV"""
        print("Processing users...")

        users_data = []
        for _, row in tqdm(self.users.iterrows(), total=len(self.users), desc="Processing users"):
            gender = row.get('Gender', '')
            if gender not in ['Male', 'Female', 'Non-Binary', 'Other', 'Prefer not to say']:
                gender = 'Other'

            users_data.append({
                'user_id': int(row['UserID']),
                'age': int(row.get('Age')),
                'gender': gender,
                'location': str(row.get('Location', '')),
                'interests': str(row.get('Interests', '')),
                'signup_date': row.get('SignupDate')
            })

        # Create DataFrame and save to CSV
        users_df = pd.DataFrame(users_data)
        output_path = os.path.join(self.transformed_dir, 'users.csv')
        users_df.to_csv(output_path, index=False)
        print(f"Saved {len(users_data)} users to {output_path}")
        
        return output_path

    def transform_impressions_and_clicks(self) -> Tuple[str, str]:
        """Transform ad impressions and clicks data and save to CSV files"""
        print("Processing impressions and clicks")

        impressions_data = []
        clicks_data = []

        # Create a mapping of campaign names to campaign IDs for quick lookup
        campaign_lookup = dict(zip(self.campaigns['CampaignName'], self.campaigns['CampaignID']))

        for _, row in tqdm(self.ad_events.iterrows(), total=len(self.ad_events), desc="Processing ad events"):
            # Get campaign_id directly from campaign name
            campaign_id = campaign_lookup.get(row['CampaignName'])

            if not campaign_id:
                print(f"Campaign not found for: {row['CampaignName']}")
                continue

            # Prepare impression data
            impressions_data.append({
                'impression_id': row['EventID'],
                'campaign_id': campaign_id,
                'user_id': row['UserID'],
                'device': row.get('Device', ''),
                'user_location': row.get('Location', ''),
                'impression_timestamp': row['Timestamp'],
                'bid_amount': row.get('BidAmount', 0),
                'ad_cost': row.get('AdCost', 0),
                'ad_revenue': row.get('AdRevenue', 0)
            })

            # If this impression was clicked, prepare click data
            if row['WasClicked'] and pd.notna(row['ClickTimestamp']):
                clicks_data.append({
                    'impression_id': row['EventID'],
                    'click_timestamp': row['ClickTimestamp']
                })

        # Save impressions to CSV
        impressions_df = pd.DataFrame(impressions_data)
        impressions_path = os.path.join(self.transformed_dir, 'ad_impressions.csv')
        impressions_df.to_csv(impressions_path, index=False)
        print(f"Saved {len(impressions_data)} impressions to {impressions_path}")

        # Save clicks to CSV
        clicks_df = pd.DataFrame(clicks_data)
        clicks_path = os.path.join(self.transformed_dir, 'ad_clicks.csv')
        clicks_df.to_csv(clicks_path, index=False)
        print(f"Saved {len(clicks_data)} clicks to {clicks_path}")

        return impressions_path, clicks_path


def transform_datasets():
    transformer = DataTransformer()

    try:
        # Load and transform data
        transformer.load_and_process_data(
            ad_events_file="dataset_normalized/ad_events.csv",
            campaigns_file="dataset_normalized/campaigns.csv",
            users_file="dataset_normalized/users.csv"
        )
        print("Data transformation and loading completed successfully!")

        # Transform and save data to CSV files
        transformer.transform_users()
        transformer.extract_advertisers()
        transformer.transform_campaigns()
        transformer.transform_impressions_and_clicks()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)