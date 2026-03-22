"""Add new columns to existing holyhub.db without dropping data."""
import sqlite3
import sys


def migrate(db_path: str = "holyhub.db") -> None:
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    existing = {row[1] for row in cur.execute("PRAGMA table_info(Churches)")}

    new_columns = [
        ("zip_code",    "TEXT"),
        ("website",     "TEXT"),
        ("phone",       "TEXT"),
        ("source",      "TEXT DEFAULT 'manual'"),
        ("external_id", "TEXT"),
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
    ]
    for name, ddl in new_indexes:
        cur.execute(ddl)
        print(f"  index ensured: {name}")

    con.commit()
    con.close()
    print("Migration complete.")


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "holyhub.db"
    migrate(db_path)
