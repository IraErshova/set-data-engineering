-- This is a table to store all infoarmation related to users

CREATE TABLE users (
    user_id INT PRIMARY KEY,
    age INT CHECK (age > 0),
    gender ENUM('Male', 'Female', 'Non-Binary', 'Other', 'Prefer not to say'),
    country_id INT,
    signup_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (country_id) REFERENCES countries(country_id) ON DELETE SET NULL,
    INDEX idx_users_demographics (age, gender),
    INDEX idx_users_country (country_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;