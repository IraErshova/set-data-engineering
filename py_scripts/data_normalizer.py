#!/usr/bin/env python3
import pandas as pd
import os

def normalize_ad_events():
    """Normalize ad_events data and save to dataset_normalized folder"""
    # Fix file by separating data from TargetingCriteria column (due to unquoted commas)
    fixed_rows = []
    with open("dataset/ad_events.csv", 'r') as f:
        header = f.readline().strip().split(',')

        for line in f:
            parts = line.strip().split(',')

            # 18 columns + 3 from TargetingCriteria
            if len(parts) >= 20:
                # Recombine TargetingCriteria (assumed to be split into 3 parts at positions 5,6,7)
                fixed = (
                    parts[:5] +                                     # EventID to CampaignEndDate
                    [','.join(parts[5:8]).strip()] +                # TargetingCriteria (3 parts)
                    parts[8:]                                       # Remaining columns
                )

                # Only accept rows that fix to exactly 18 columns
                if len(fixed) == 18:
                    fixed_rows.append(fixed)

    df = pd.DataFrame(fixed_rows, columns=header)
    
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