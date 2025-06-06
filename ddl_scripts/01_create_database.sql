-- Create a database
CREATE DATABASE IF NOT EXISTS set_db;

-- Use that database
USE set_db;

-- To able to insert data from file
GRANT FILE ON *.* TO 'set_user'@'%';
FLUSH PRIVILEGES;