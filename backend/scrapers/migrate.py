"""Add new columns to existing holyhub.db without dropping data."""
import sqlite3
import sys


def migrate(db_path: str = "holyhub.db") -> None:
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    existing = {row[1] for row in cur.execute("PRAGMA table_info(Churches)")}

    new_columns = [
        ("zip_code",              "TEXT"),
        ("website",               "TEXT"),
        ("phone",                 "TEXT"),
        ("source",                "TEXT DEFAULT 'manual'"),
        ("external_id",           "TEXT"),
        ("google_place_id",       "TEXT"),
        ("google_photos",         "TEXT"),   # JSON array of photo URLs
        ("google_hours",          "TEXT"),   # JSON array of weekday strings
        ("google_enriched_at",    "TEXT"),   # ISO timestamp
        ("google_rating",         "REAL"),   # Google aggregate rating
        ("google_review_count",   "INTEGER"),# Number of Google reviews
        ("google_reviews",        "TEXT"),   # JSON array of review objects
        ("google_editorial",      "TEXT"),   # Editorial summary description
        ("google_wheelchair",     "INTEGER"),# 1 = wheelchair accessible
        ("google_address",        "TEXT"),   # Formatted address from Google
        ("language",              "TEXT"),   # Detected primary service language
        ("cultural_background",   "TEXT"),   # Detected cultural/ethnic community
    ]
    for col, typedef in new_columns:
        if col not in existing:
            cur.execute(f"ALTER TABLE Churches ADD COLUMN {col} {typedef}")
            print(f"  added column: {col}")
        else:
            print(f"  already exists: {col}")

    new_indexes = [
        ("idx_churches_zip",      "CREATE INDEX IF NOT EXISTS idx_churches_zip ON Churches(zip_code)"),
        ("idx_churches_latlon",   "CREATE INDEX IF NOT EXISTS idx_churches_latlon ON Churches(latitude, longitude)"),
        ("idx_churches_external", "CREATE INDEX IF NOT EXISTS idx_churches_external ON Churches(external_id)"),
        ("idx_churches_enriched", "CREATE INDEX IF NOT EXISTS idx_churches_enriched ON Churches(google_enriched_at)"),
    ]

    # Users table for Google Sign-In
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id  TEXT UNIQUE NOT NULL,
            email      TEXT,
            name       TEXT,
            avatar_url TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    print("  ensured: Users table")

    # Add reviewer columns to Reviews
    reviews_existing = {row[1] for row in cur.execute("PRAGMA table_info(Reviews)")}
    for col, typedef in [
        ("user_id",         "INTEGER REFERENCES Users(user_id)"),
        ("reviewer_name",   "TEXT"),
        ("reviewer_avatar", "TEXT"),
    ]:
        if col not in reviews_existing:
            cur.execute(f"ALTER TABLE Reviews ADD COLUMN {col} {typedef}")
            print(f"  added Reviews column: {col}")
        else:
            print(f"  already exists: Reviews.{col}")

    # api_usage table for monthly cap tracking
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            month   TEXT NOT NULL,
            service TEXT NOT NULL,
            count   INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (month, service)
        )
    """)
    for name, ddl in new_indexes:
        cur.execute(ddl)
        print(f"  index ensured: {name}")

    con.commit()
    con.close()
    print("Migration complete.")


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "holyhub.db"
    migrate(db_path)
