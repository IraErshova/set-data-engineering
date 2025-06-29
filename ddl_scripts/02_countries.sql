-- This is a table to store countries information to avoid duplication across the DB

CREATE TABLE countries (
    country_id INT AUTO_INCREMENT PRIMARY KEY,
    country_name VARCHAR(255) NOT NULL UNIQUE,
    INDEX idx_country_id (country_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;