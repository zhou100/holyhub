-- Database schema for HolyHub

CREATE TABLE IF NOT EXISTS Churches (
    church_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    denomination TEXT,
    service_times TEXT,
    latitude REAL,
    longitude REAL
);

CREATE TABLE IF NOT EXISTS Reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    church_id INTEGER,
    rating REAL,
    comment TEXT,
    worship_energy REAL,
    community_warmth REAL,
    sermon_depth REAL,
    childrens_programs REAL,
    theological_openness REAL,
    facilities REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (church_id) REFERENCES Churches(church_id)
);

CREATE INDEX IF NOT EXISTS idx_churches_location ON Churches(city, state);
CREATE INDEX IF NOT EXISTS idx_reviews_church ON Reviews(church_id);
