-- This is a junction table to establish many-to-many relationship between users and interests

CREATE TABLE users_interests (
    user_id INT NOT NULL,
    interest_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, interest_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (interest_id) REFERENCES interests(interest_id) ON DELETE CASCADE,
    INDEX idx_users_interests_user (user_id),
    INDEX idx_users_interests_interest (interest_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
