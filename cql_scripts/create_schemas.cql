-- Ad campaign performance over time
CREATE TABLE ad_campaign_performance_by_day (
    campaign_id UUID,
    date DATE,
    impressions COUNTER,
    clicks COUNTER,
    PRIMARY KEY ((campaign_id), date)
);

-- Top advertisers by total ad spend
CREATE TABLE top_advertisers_by_spend (
    day DATE,
    advertiser_id UUID,
    advertiser_name TEXT,
    total_spend DECIMAL,
    PRIMARY KEY (day, total_spend, advertiser_id)
) WITH CLUSTERING ORDER BY (total_spend DESC);

-- User engagement history
CREATE TABLE user_engagement_history (
    user_id UUID,
    timestamp TIMESTAMP,
    ad_id UUID,
    campaign_id UUID,
    action TEXT, -- 'impression' | 'click'
    PRIMARY KEY ((user_id), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);

-- Most active users
CREATE TABLE user_activity_by_day (
    day DATE,
    impressions BIGINT,
    clicks BIGINT,
    user_id UUID,
    PRIMARY KEY ((day), impressions, clicks, user_id)
) WITH CLUSTERING ORDER BY (impressions DESC, clicks DESC);

-- High-spending advertisers by region
CREATE TABLE advertiser_spend_by_region (
    region TEXT,
    advertiser_id UUID,
    advertiser_name TEXT,
    total_spend DECIMAL,
    PRIMARY KEY ((region), total_spend, advertiser_id)
) WITH CLUSTERING ORDER BY (total_spend DESC);
