-- This is a table for impressions. We store here all impression events with bid and cost information
-- Each impression is a unique ad event
-- Links directly to campaign and user
CREATE TABLE ad_impressions (
    impression_id VARCHAR(50) PRIMARY KEY,
    campaign_id INT NOT NULL,
    user_id INT NOT NULL,
    device ENUM('Mobile', 'Desktop', 'Tablet', 'Other'),
    location_id INT, -- user's location at time of impression
    impression_timestamp TIMESTAMP NOT NULL,
    bid_amount DECIMAL(8,4),
    ad_cost DECIMAL(8,4),
    ad_revenue DECIMAL(8,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES countries(country_id) ON DELETE SET NULL,
    INDEX idx_impressions_campaign_timestamp (campaign_id, impression_timestamp),
    INDEX idx_impressions_user_device (user_id, device),
    INDEX idx_impressions_user_location (user_id, location_id),
    INDEX idx_impressions_timestamp (impression_timestamp),
    INDEX idx_impressions_campaign_user (campaign_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;