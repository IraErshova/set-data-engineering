-- This is a table to store interests information to avoid duplication across the DB

CREATE TABLE interests (
    interest_id INT AUTO_INCREMENT PRIMARY KEY,
    interest_name VARCHAR(255) NOT NULL UNIQUE,
    INDEX idx_interest_id (interest_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;