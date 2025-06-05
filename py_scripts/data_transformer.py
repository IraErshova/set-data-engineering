import pandas as pd
import os
from typing import Dict, List, Tuple

class DataTransformer:
    def __init__(self):
        self.ad_events = None
        self.campaigns = None
        self.users = None
        self.campaign_mapping = None

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


    def extract_advertisers(self) -> List[Tuple[str]]:
        """
        Extract unique advertisers from data
        Returns list of tuples with advertiser names
        """
        print("Processing advertisers...")

        # Get unique advertisers from both ad_events and campaigns
        advertisers_from_events = set(self.ad_events['AdvertiserName'].dropna().unique())
        advertisers_from_campaigns = set(self.campaigns['AdvertiserName'].dropna().unique())
        unique_advertisers = advertisers_from_events.union(advertisers_from_campaigns)

        return [(advertiser,) for advertiser in unique_advertisers]


    def transform_campaigns(self) -> List[Tuple]:
        """Transform campaign data for database insertion"""
        print("Processing campaigns")

        campaigns_data = []
        for _, row in self.campaigns.iterrows():
            campaigns_data.append((
                int(row['CampaignID']),
                str(row['AdvertiserName']),
                str(row['CampaignName']),
                row['CampaignStartDate'],
                row['CampaignEndDate'],
                str(row.get('TargetingCriteria', '')),
                str(row.get('AdSlotSize', '')),
                float(row.get('Budget', 0)) if pd.notna(row.get('Budget', 0)) else 0.0,
                float(row.get('RemainingBudget', 0)) if pd.notna(row.get('RemainingBudget', 0)) else 0.0
            ))

        return campaigns_data


    def transform_users(self) -> List[Tuple]:
        """Transform user data for database insertion"""
        print("Processing users...")

        users_data = []
        for _, row in self.users.iterrows():
            gender = row.get('Gender', '')
            if gender not in ['Male', 'Female', 'Non-Binary', 'Other', 'Prefer not to say']:
                gender = 'Other'

            users_data.append((
                int(row['UserID']),
                int(row.get('Age')),
                gender,
                str(row.get('Location', '')),
                str(row.get('Interests', '')),
                row.get('SignupDate')
            ))

        return users_data


    def create_campaign_mapping(self) -> Dict[Tuple[str, str], int]:
        """Create mapping from campaign name + advertiser to campaign_id"""
        print("Creating campaign mapping")

        self.campaign_mapping = {}
        for _, row in self.campaigns.iterrows():
            key = (row['AdvertiserName'], row['CampaignName'])
            self.campaign_mapping[key] = row['CampaignID']

        return self.campaign_mapping


    def transform_impressions_and_clicks(self) -> Tuple[List[Tuple], List[Tuple]]:
        """Transform ad impressions and clicks data for database insertion"""
        print("Processing impressions and clicks")

        impressions_data = []
        clicks_data = []

        for _, row in self.ad_events.iterrows():
            # Get campaign_id from mapping
            campaign_key = (row['AdvertiserName'], row['CampaignName'])
            campaign_id = self.campaign_mapping.get(campaign_key)

            if not campaign_id:
                print(f"Campaign not found for: {campaign_key}")
                continue

            # Prepare impression data
            impressions_data.append((
                row['EventID'],  # EventID as impression_id
                campaign_id,
                row['UserID'],
                row.get('Device', ''),
                row.get('Location', ''),  # User location at time of impression
                row['Timestamp'],
                row.get('BidAmount', 0),
                row.get('AdCost', 0),
                row.get('AdRevenue', 0)
            ))

            # If this impression was clicked, prepare click data
            if row['WasClicked'] and pd.notna(row['ClickTimestamp']):
                clicks_data.append((
                    row['EventID'],  # Links to impression
                    row['ClickTimestamp']
                ))

        return impressions_data, clicks_data