-- Top 5 Campaigns by Click-Through Rate (CTR)
SELECT
    c.campaign_id,
    c.campaign_name,
    COUNT(DISTINCT ai.impression_id) AS impressions,
    COUNT(ac.click_id) AS clicks,
    ROUND(COUNT(ac.click_id) * 100.0 / COUNT(DISTINCT ai.impression_id), 2) AS ctr_percentage
FROM campaigns c
JOIN ad_impressions ai ON c.campaign_id = ai.campaign_id
LEFT JOIN ad_clicks ac ON ai.impression_id = ac.impression_id
WHERE ai.impression_timestamp BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY c.campaign_id, c.campaign_name
ORDER BY ctr_percentage DESC
LIMIT 5;

-- Advertisers with Highest Spend in the Last 30 Days
SELECT
    a.advertiser_id,
    a.advertiser_name,
    ROUND(SUM(ai.ad_cost), 2) AS total_spent
FROM advertisers a
JOIN campaigns c ON a.advertiser_id = c.advertiser_id
JOIN ad_impressions ai ON c.campaign_id = ai.campaign_id
WHERE ai.impression_timestamp BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY a.advertiser_id, a.advertiser_name
ORDER BY total_spent DESC;

-- Cost Efficiency: Average CPC and CPM per Campaign
SELECT
    c.campaign_id,
    c.campaign_name,
    ROUND(SUM(ai.ad_cost) / NULLIF(COUNT(ac.click_id), 0), 2) AS avg_cpc,
    ROUND(SUM(ai.ad_cost) / NULLIF(COUNT(ai.impression_id), 0) * 1000, 2) AS avg_cpm
FROM campaigns c
JOIN ad_impressions ai ON c.campaign_id = ai.campaign_id
LEFT JOIN ad_clicks ac ON ai.impression_id = ac.impression_id
WHERE ai.impression_timestamp BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY c.campaign_id, c.campaign_name;

-- Top Locations by Total Ad Revenue from Clicks
SELECT
    ai.user_location,
    ROUND(SUM(ai.ad_revenue), 2) AS total_revenue
FROM ad_impressions ai
JOIN ad_clicks ac ON ai.impression_id = ac.impression_id
WHERE ai.impression_timestamp BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY ai.user_location
ORDER BY total_revenue DESC
LIMIT 10;

-- Top 10 Most Engaged Users by Clicks
SELECT
    u.user_id,
    COUNT(ac.click_id) AS total_clicks
FROM users u
JOIN ad_impressions ai ON u.user_id = ai.user_id
JOIN ad_clicks ac ON ai.impression_id = ac.impression_id
WHERE ac.click_timestamp BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY u.user_id
ORDER BY total_clicks DESC
LIMIT 10;

-- Campaigns with > 80% Budget Spent
SELECT
    c.campaign_id,
    c.campaign_name,
    c.budget,
    c.remaining_budget,
    ROUND((c.budget - c.remaining_budget) / c.budget * 100, 2) AS percent_spent
FROM campaigns c
WHERE (c.budget - c.remaining_budget) / c.budget >= 0.80
ORDER BY percent_spent DESC;

-- CTR Comparison Across Devices
SELECT
    ai.device,
    COUNT(DISTINCT ai.impression_id) AS impressions,
    COUNT(ac.click_id) AS clicks,
    ROUND(COUNT(ac.click_id) * 100.0 / COUNT(DISTINCT ai.impression_id), 2) AS ctr_percentage
FROM ad_impressions ai
LEFT JOIN ad_clicks ac ON ai.impression_id = ac.impression_id
WHERE ai.impression_timestamp BETWEEN '2024-11-01' AND '2024-11-30'
GROUP BY ai.device
ORDER BY ctr_percentage DESC;







