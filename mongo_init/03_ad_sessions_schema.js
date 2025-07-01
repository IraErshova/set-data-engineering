db = db.getSiblingDB('set_db');

db.createCollection("ad_sessions", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "session_start", "session_end", "impressions"],
      properties: {
        user_id: { bsonType: "int" },
        device: { bsonType: "string" },
        session_start: { bsonType: "date" },
        session_end: { bsonType: "date" },
        impressions: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["impression_id", "campaign_id", "timestamp", "clicked"],
            properties: {
              impression_id: { bsonType: "string" },
              campaign_id: { bsonType: "int" },
              campaign_name: { bsonType: "string" },
              advertiser_id: { bsonType: "int" },
              timestamp: { bsonType: "date" },
              location: {
                bsonType: "string",
              },
              bid_amount: { bsonType: "double" },
              ad_cost: { bsonType: "double" },
              ad_revenue: { bsonType: "double" },
              clicked: { bsonType: "bool" },
              click_events: {
                bsonType: "array",
                items: { bsonType: "object", properties: { click_timestamp: { bsonType: "date" } } }
              }
            }
          }
        }
      }
    }
  }
});

db.ad_sessions.createIndex({ user_id: 1 })
db.ad_sessions.createIndex({ "impressions.timestamp": 1 })
db.ad_sessions.createIndex({ "impressions.advertiser_id": 1, "impressions.timestamp": -1 })
db.ad_sessions.createIndex({ "impressions.campaign_id": 1, "impressions.timestamp": -1 })
db.ad_sessions.createIndex({ "impressions.clicked": 1 })

// Compound index for complex queries
db.ad_sessions.createIndex({
  "user_id": 1,
  "impressions.timestamp": -1
});


