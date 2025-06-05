-- This is a table for click events to optimize queries to avoid empty events when WasClicked is false
-- Links directly to impressions
CREATE TABLE ad_clicks (
    click_id INT AUTO_INCREMENT PRIMARY KEY,
    impression_id VARCHAR(50) NOT NULL UNIQUE,
    click_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (impression_id) REFERENCES ad_impressions(impression_id) ON DELETE CASCADE,
    INDEX idx_clicks_timestamp (click_timestamp),
    INDEX idx_clicks_impression (impression_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;