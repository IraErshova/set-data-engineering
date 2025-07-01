db = db.getSiblingDB('set_db');

db.createUser({
  user: "set_user",
  pwd: "set_password",
  roles: [
    {
      role: "readWrite",
      db: "set_db"
    }
  ]
});