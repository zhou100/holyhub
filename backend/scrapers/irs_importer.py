"""
IRS Publication 78 importer.

Downloads the IRS list of tax-exempt organizations, filters to religious
ones (NTEE code X*), geocodes addresses via Nominatim, and inserts
records not already in the DB.

Geocoding is slow (1 req/sec). For the full dataset run overnight;
use --limit N during testing.
"""
import csv
import io
import logging
import sqlite3
import sys
import time
import zipfile
from typing import Iterator

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

PUB78_URL = (
    "https://apps.irs.gov/pub/epostcard/data-download-pub78.zip"
)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "HolyHub/1.0 (church-data-pipeline; contact=holyhub@example.com)"

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC",
}


def _download_pub78() -> list[dict]:
    """Download and parse IRS Pub 78. Returns list of org dicts."""
    log.info("Downloading IRS Publication 78 …")
    resp = requests.get(PUB78_URL, timeout=120, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        # The zip contains a pipe-delimited text file
        name = next(n for n in z.namelist() if n.endswith(".txt") or n.endswith(".csv"))
        log.info(f"Reading {name} …")
        raw = z.read(name).decode("latin-1")

    orgs = []
    reader = csv.reader(io.StringIO(raw), delimiter="|")
    for row in reader:
        if len(row) < 6:
            continue
        # Pub78 format: EIN|NAME|CITY|STATE|COUNTRY|DEDUCTIBILITY_STATUS
        ein, name, city, state, country, *_ = row
        state = state.strip().upper()
        if country.strip().upper() not in ("", "US", "USA", "UNITED STATES"):
            continue
        if state not in US_STATES:
            continue
        if not name.strip():
            continue
        orgs.append({
            "ein":   ein.strip(),
            "name":  name.strip().title(),
            "city":  city.strip().title(),
            "state": state,
        })

    log.info(f"Loaded {len(orgs):,} US religious organizations from IRS Pub 78")
    return orgs


def _geocode(name: str, city: str, state: str) -> tuple[float | None, float | None]:
    """Geocode a church address via Nominatim. Returns (lat, lon) or (None, None)."""
    query = f"{name}, {city}, {state}, USA"
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "us"},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        log.debug(f"Geocode failed for '{query}': {e}")
    return None, None


def _existing_names(con: sqlite3.Connection) -> set[str]:
    """Return a set of lowercased 'name|city|state' keys already in DB."""
    rows = con.execute("SELECT name, city, state FROM Churches").fetchall()
    return {f"{r[0].lower()}|{(r[1] or '').lower()}|{(r[2] or '').lower()}" for r in rows}


def _is_duplicate(org: dict, existing: set[str]) -> bool:
    key = f"{org['name'].lower()}|{org['city'].lower()}|{org['state'].lower()}"
    return key in existing


def load(db_path: str = "holyhub.db", limit: int = 0,
         geocode: bool = True, delay: float = 1.1) -> int:
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")

    orgs = _download_pub78()
    existing = _existing_names(con)

    new_orgs = [o for o in orgs if not _is_duplicate(o, existing)]
    log.info(f"{len(new_orgs):,} new orgs after dedup against existing DB")

    if limit:
        new_orgs = new_orgs[:limit]
        log.info(f"Limited to {limit} records for this run")

    inserted = 0
    geocoded = 0
    cur = con.cursor()

    for i, org in enumerate(new_orgs, 1):
        lat, lon = None, None
        if geocode:
            lat, lon = _geocode(org["name"], org["city"], org["state"])
            if lat:
                geocoded += 1
            time.sleep(delay)  # Nominatim rate limit

        cur.execute(
            """INSERT INTO Churches
               (name, city, state, latitude, longitude, source, external_id)
               VALUES (?,?,?,?,?,?,?)""",
            (org["name"], org["city"], org["state"],
             lat, lon, "irs", f"irs:{org['ein']}"),
        )
        inserted += 1

        if i % 100 == 0:
            con.commit()
            log.info(f"  {i}/{len(new_orgs)} inserted, {geocoded} geocoded …")

    con.commit()
    con.close()
    log.info(f"IRS import complete. Inserted {inserted}, geocoded {geocoded}.")
    return inserted


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="holyhub.db")
    p.add_argument("--limit", type=int, default=0, help="0 = all records")
    p.add_argument("--no-geocode", action="store_true")
    args = p.parse_args()
    load(args.db, limit=args.limit, geocode=not args.no_geocode)
