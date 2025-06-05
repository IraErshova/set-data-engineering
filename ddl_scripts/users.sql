-- This is a table to store all infoarmation related to users

CREATE TABLE users (
    user_id INT PRIMARY KEY,
    age TINYINT UNSIGNED,
    gender ENUM('Male', 'Female', 'Non-Binary', 'Other', 'Prefer not to say'),
    location VARCHAR(80),
    interests TEXT,
    signup_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_demographics (age, gender),
    INDEX idx_users_location (location)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;