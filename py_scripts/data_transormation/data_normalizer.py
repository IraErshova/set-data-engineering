#!/usr/bin/env python3
import pandas as pd
import os

def normalize_ad_events():
    df = pd.read_csv('dataset/ad_events.csv', nrows=3_000_000)
    # Remove duplicates
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset='EventID')
    
    # Fix data types
    df['CampaignStartDate'] = pd.to_datetime(df['CampaignStartDate'], errors='coerce')
    df['CampaignEndDate'] = pd.to_datetime(df['CampaignEndDate'], errors='coerce')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df['ClickTimestamp'] = pd.to_datetime(df['ClickTimestamp'], errors='coerce')

    # Fix numeric columns
    numeric_cols = ['BidAmount', 'AdCost', 'AdRevenue', 'Budget', 'RemainingBudget']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    
    # Fix boolean column
    df['WasClicked'] = df['WasClicked'].map({'True': True, 'False': False, True: True, False: False})
    
    # Save normalized data
    df.to_csv("dataset_normalized/ad_events.csv", index=False)
    return df

def normalize_campaigns():
    """Normalize campaigns data and save to dataset_normalized folder."""
    df_campaigns = pd.read_csv('dataset/campaigns.csv')
    
    # Fix data types
    df_campaigns['CampaignStartDate'] = pd.to_datetime(df_campaigns['CampaignStartDate'], errors='coerce')
    df_campaigns['CampaignEndDate'] = pd.to_datetime(df_campaigns['CampaignEndDate'], errors='coerce')
    
    # Fix numeric columns
    numeric_cols = ['Budget', 'RemainingBudget']
    df_campaigns[numeric_cols] = df_campaigns[numeric_cols].apply(pd.to_numeric, errors='coerce')

    # Split into parts using comma
    parts = df_campaigns['TargetingCriteria'].str.split(',', expand=True)

    # Strip whitespace
    parts = parts.apply(lambda col: col.str.strip())

    # Extract age range from the first part
    age_parts = parts[0].str.extract(r'Age\s+(\d+)-(\d+)').astype('Int64')

    # Assign normalized columns
    df_campaigns['age_from'] = age_parts[0]
    df_campaigns['age_to'] = age_parts[1]
    df_campaigns['interest'] = parts[1]
    df_campaigns['country'] = parts[2]
    
    # Save normalized data
    df_campaigns.to_csv("dataset_normalized/campaigns.csv", index=False)
    return df_campaigns

def normalize_users():
    """Normalize users data and save to dataset_normalized folder."""
    df_users = pd.read_csv('dataset/users.csv')
    
    # Fix data types
    df_users['SignupDate'] = pd.to_datetime(df_users['SignupDate'], errors='coerce')
    
    # Save normalized data
    df_users.to_csv("dataset_normalized/users.csv", index=False)
    return df_users

def normalize_datasets():
    # Create output directory if it doesn't exist
    os.makedirs("dataset_normalized", exist_ok=True)
    
    # Check if all normalized files already exist
    required_files = ['users.csv', 'campaigns.csv', 'ad_events.csv']
    all_files_exist = all(os.path.exists(os.path.join("dataset_normalized", file)) for file in required_files)
    
    if all_files_exist:
        print("\nAll datasets have been normalized and saved to dataset_normalized folder.")
        return
    
    # Normalize all datasets
    print("Normalizing ad_events data...")
    normalize_ad_events()

    print("\nNormalizing campaigns data...")
    normalize_campaigns()

    print("\nNormalizing users data...")
    normalize_users()

    print("\nAll datasets have been normalized and saved to dataset_normalized folder.")