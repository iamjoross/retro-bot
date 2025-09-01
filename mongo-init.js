// MongoDB initialization script

// Switch to assistant database
db = db.getSiblingDB("assistant");

// Create a user for the application
db.createUser({
  user: "assistant_user",
  pwd: "assistant_pass",
  roles: [
    {
      role: "readWrite",
      db: "assistant",
    },
  ],
});

// Create collections and indexes
db.createCollection("conversations");

// Create indexes for better performance (no user_id needed)
db.conversations.createIndex({ updated_at: -1 });
db.conversations.createIndex({ created_at: -1 });

print("MongoDB initialized successfully for Assistant App");
