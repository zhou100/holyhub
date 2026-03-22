"""
OSM Overpass scraper — fetches all places of worship in the continental US.

Strategy: tile the bounding box into a grid of cells, query each cell,
collect results, bulk-insert into Churches. Skips records with no name.
"""
import sqlite3
import time
import sys
import logging
from typing import Generator

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Continental US bounding box
US_SOUTH, US_NORTH = 24.5, 49.5
US_WEST,  US_EAST  = -125.0, -66.0

# Grid dimensions — 15 columns × 10 rows = 150 tiles
COLS, ROWS = 15, 10

# US state abbreviations for filtering
US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC",
}

# OSM denomination tag → normalized label
DENOM_MAP = {
    "catholic":              "Catholic",
    "roman_catholic":        "Roman Catholic",
    "baptist":               "Baptist",
    "methodist":             "Methodist",
    "lutheran":              "Lutheran",
    "presbyterian":          "Presbyterian",
    "episcopal":             "Episcopal",
    "pentecostal":           "Pentecostal",
    "evangelical":           "Evangelical",
    "non-denominational":    "Non-denominational",
    "nondenominational":     "Non-denominational",
    "assemblies_of_god":     "Assemblies of God",
    "church_of_christ":      "Church of Christ",
    "seventh_day_adventist": "Seventh-day Adventist",
    "united_methodist":      "United Methodist",
    "reformed":              "Reformed",
    "anglican":              "Anglican",
    "orthodox":              "Orthodox",
    "jewish":                "Jewish",
    "islam":                 "Islamic",
    "muslim":                "Islamic",
}


def _tiles() -> Generator[tuple, None, None]:
    lat_step = (US_NORTH - US_SOUTH) / ROWS
    lon_step = (US_EAST - US_WEST) / COLS
    for r in range(ROWS):
        for c in range(COLS):
            south = US_SOUTH + r * lat_step
            north = south + lat_step
            west  = US_WEST + c * lon_step
            east  = west + lon_step
            yield south, west, north, east


def _query_tile(south: float, west: float, north: float, east: float,
                retries: int = 3) -> list[dict]:
    query = (
        f"[out:json][timeout:60];"
        f'node["amenity"="place_of_worship"]'
        f'({south:.4f},{west:.4f},{north:.4f},{east:.4f});'
        f"out body;"
    )
    for attempt in range(retries):
        try:
            resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=90)
            resp.raise_for_status()
            return resp.json().get("elements", [])
        except Exception as e:
            wait = 10 * (attempt + 1)
            log.warning(f"Tile ({south:.1f},{west:.1f}) attempt {attempt+1} failed: {e}. Retrying in {wait}s")
            time.sleep(wait)
    return []


def _normalize(el: dict) -> dict | None:
    tags = el.get("tags", {})
    name = tags.get("name", "").strip()
    if not name:
        return None

    state = (tags.get("addr:state") or "").strip().upper()
    if state and state not in US_STATES:
        return None

    raw_denom = (
        tags.get("denomination") or
        tags.get("religion") or ""
    ).lower().replace(" ", "_")
    denomination = DENOM_MAP.get(raw_denom, raw_denom.replace("_", " ").title() if raw_denom else None)

    return {
        "name":        name,
        "address":     tags.get("addr:street", ""),
        "city":        tags.get("addr:city", ""),
        "state":       state,
        "zip_code":    tags.get("addr:postcode", ""),
        "denomination":denomination,
        "website":     tags.get("website") or tags.get("contact:website", ""),
        "phone":       tags.get("phone") or tags.get("contact:phone", ""),
        "latitude":    el.get("lat"),
        "longitude":   el.get("lon"),
        "source":      "osm",
        "external_id": f"osm:{el['id']}",
    }


def scrape(db_path: str = "holyhub.db", delay: float = 2.0) -> int:
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")

    tiles = list(_tiles())
    total_tiles = len(tiles)
    inserted = 0
    skipped_dup = 0

    log.info(f"Scraping {total_tiles} tiles across the continental US …")

    for i, (south, west, north, east) in enumerate(tiles, 1):
        log.info(f"Tile {i}/{total_tiles}  ({south:.1f},{west:.1f})→({north:.1f},{east:.1f})")
        elements = _query_tile(south, west, north, east)

        rows = []
        for el in elements:
            rec = _normalize(el)
            if rec:
                rows.append(rec)

        if rows:
            cur = con.cursor()
            for rec in rows:
                # Skip if exact external_id already exists
                exists = cur.execute(
                    "SELECT 1 FROM Churches WHERE external_id = ?", (rec["external_id"],)
                ).fetchone()
                if exists:
                    skipped_dup += 1
                    continue
                cur.execute(
                    """INSERT INTO Churches
                       (name, address, city, state, zip_code, denomination,
                        website, phone, latitude, longitude, source, external_id)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (rec["name"], rec["address"], rec["city"], rec["state"],
                     rec["zip_code"], rec["denomination"], rec["website"],
                     rec["phone"], rec["latitude"], rec["longitude"],
                     rec["source"], rec["external_id"]),
                )
                inserted += 1
            con.commit()

        log.info(f"  → {len(rows)} records this tile | total inserted: {inserted}")
        time.sleep(delay)

    con.close()
    log.info(f"OSM scrape complete. Inserted {inserted}, skipped {skipped_dup} duplicates.")
    return inserted


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "holyhub.db"
    scrape(db_path)
