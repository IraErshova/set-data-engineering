-- This is a table for campaign information
-- Linked to advertisers

CREATE TABLE campaigns (
    campaign_id INT PRIMARY KEY,
    advertiser_id INT NOT NULL,
    campaign_name VARCHAR(100) NOT NULL,
    campaign_start_date DATE NOT NULL,
    campaign_end_date DATE NOT NULL,
    targeting_criteria TEXT,
    targeting_age_from INT CHECK (targeting_age_from > 0),
    targeting_age_to INT CHECK (targeting_age_to > 0),
    targeting_interest_id INT,
    targeting_country_id INT,
    ad_slot_size VARCHAR(50),
    budget DECIMAL(12,2),
    remaining_budget DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (advertiser_id) REFERENCES advertisers(advertiser_id) ON DELETE CASCADE,
    FOREIGN KEY (targeting_interest_id) REFERENCES interests(interest_id) ON DELETE SET NULL,
    FOREIGN KEY (targeting_country_id) REFERENCES countries(country_id) ON DELETE SET NULL,
    UNIQUE KEY uk_advertiser_campaign (advertiser_id, campaign_name),
    INDEX idx_campaigns_advertiser (advertiser_id),
    INDEX idx_campaigns_dates (campaign_start_date, campaign_end_date),
    INDEX idx_campaigns_interest (targeting_interest_id),
    INDEX idx_campaigns_country (targeting_country_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;