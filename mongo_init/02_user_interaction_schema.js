// Create the user_interaction collection with validation schema
db = db.getSiblingDB('set_db');

db.createCollection("user_interaction", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["user_id", "demographics", "interaction_history"],
         properties: {
            user_id: {
               bsonType: "int",
               description: "must be an integer and is required"
            },
            demographics: {
               bsonType: "object",
               required: ["age", "gender", "location"],
               properties: {
                  age: {
                     bsonType: "int",
                     minimum: 1,
                     maximum: 120,
                     description: "must be an integer between 1 and 120"
                  },
                  gender: {
                     enum: ["Male", "Female", "Non-Binary", "Other", "Prefer not to say"],
                     description: "must be one of the enum values"
                  },
                  interests: {
                     bsonType: "array",
                     items: {
                        bsonType: "string"
                     }
                  },
                  location: {
                     bsonType: "string",
                     description: "'location' must be a string and is required"
                  }
               }
            },
            interaction_history: {
               bsonType: "object",
               required: ["total_impressions", "total_clicks"],
               properties: {
                  total_impressions: {
                     bsonType: "int",
                     minimum: 0
                  },
                  total_clicks: {
                     bsonType: "int",
                     minimum: 0
                  }
               }
            },
            created_at: { bsonType: "date" },
            updated_at: { bsonType: "date" }
         }
      }
   }
});

// Create indexes for optimal query performance
db.user_interaction.createIndex({ "user_id": 1 }, { unique: true });
db.user_interaction.createIndex({ "demographics.age": 1, "demographics.gender": 1 });
