"""
Fill in missing city/state/zip for churches that have lat/lon but no address data.

Uses the `reverse_geocoder` library — a fast offline kdtree lookup against
GeoNames data. No API calls, no rate limits, ~1M lookups/sec.
"""
import logging
import sqlite3
import sys

import reverse_geocoder as rg

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

# GeoNames → USPS state abbreviation mapping
ADMIN1_TO_STATE = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC",
}


def fill(db_path: str = "holyhub.db", batch_size: int = 10000) -> int:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")

    # Only process records that have lat/lon but are missing city or state
    rows = con.execute(
        """SELECT church_id, latitude, longitude, city, state
           FROM Churches
           WHERE latitude IS NOT NULL
             AND (city IS NULL OR city = '' OR state IS NULL OR state = '')"""
    ).fetchall()

    log.info(f"Found {len(rows):,} churches needing location fill")
    if not rows:
        log.info("Nothing to do.")
        con.close()
        return 0

    coords = [(r["latitude"], r["longitude"]) for r in rows]

    log.info("Running reverse geocode (offline kdtree) …")
    results = rg.search(coords, mode=1, verbose=False)

    updated = 0
    cur = con.cursor()
    for i, (row, res) in enumerate(zip(rows, results)):
        city  = row["city"] or res.get("name", "")
        admin1 = res.get("admin1", "")
        state = row["state"] or ADMIN1_TO_STATE.get(admin1, "")

        if not city and not state:
            continue

        cur.execute(
            "UPDATE Churches SET city = ?, state = ? WHERE church_id = ?",
            (city, state, row["church_id"]),
        )
        updated += 1

        if updated % batch_size == 0:
            con.commit()
            log.info(f"  {updated:,} / {len(rows):,} updated …")

    con.commit()
    con.close()
    log.info(f"Location fill complete. Updated {updated:,} records.")
    return updated


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "holyhub.db"
    fill(db_path)
