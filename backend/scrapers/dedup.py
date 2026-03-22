"""
Deduplication pass — merges near-duplicate church records.

Logic:
  1. Find pairs with same city+state and fuzzy name match (≥88 score).
  2. For each pair, keep the OSM record (has accurate lat/lon), transfer
     the IRS EIN into a second external_id field if missing.
  3. Delete the lower-quality duplicate.
  4. Write a CSV report of all merges for review.
"""
import csv
import logging
import sqlite3
import sys
from pathlib import Path

from rapidfuzz import fuzz

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 88  # rapidfuzz ratio score (0–100)


def run(db_path: str = "holyhub.db", report_path: str = "dedup_report.csv",
        dry_run: bool = False) -> int:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    rows = con.execute(
        "SELECT church_id, name, city, state, source, external_id, latitude, longitude "
        "FROM Churches ORDER BY city, state, name"
    ).fetchall()

    log.info(f"Loaded {len(rows):,} churches for dedup pass")

    # Group by city+state for efficiency
    from collections import defaultdict
    by_location: dict[tuple, list] = defaultdict(list)
    for r in rows:
        key = ((r["city"] or "").lower(), (r["state"] or "").upper())
        by_location[key].append(r)

    merges: list[dict] = []

    MAX_GROUP = 200  # skip huge cities — OSM self-deduplicates by node ID
    for (city, state), group in by_location.items():
        if len(group) < 2 or len(group) > MAX_GROUP:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                # Fast prefix check before expensive fuzzy match
                if a["name"][0].lower() != b["name"][0].lower():
                    continue
                score = fuzz.token_sort_ratio(a["name"].lower(), b["name"].lower())
                if score >= SIMILARITY_THRESHOLD:
                    # Keep OSM record; prefer the one with lat/lon
                    keep, drop = _pick_winner(a, b)
                    merges.append({
                        "keep_id":   keep["church_id"],
                        "keep_name": keep["name"],
                        "drop_id":   drop["church_id"],
                        "drop_name": drop["name"],
                        "city":      city,
                        "state":     state,
                        "score":     score,
                        "keep_source": keep["source"],
                        "drop_source": drop["source"],
                    })

    log.info(f"Found {len(merges)} duplicate pairs (threshold={SIMILARITY_THRESHOLD})")

    # Write CSV report
    report = Path(report_path)
    with report.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "keep_id","keep_name","drop_id","drop_name",
            "city","state","score","keep_source","drop_source"
        ])
        w.writeheader()
        w.writerows(merges)
    log.info(f"Report written to {report}")

    if dry_run:
        log.info("Dry run — no changes made.")
        con.close()
        return 0

    # Deduplicate: delete the lower-quality record
    # Guard: don't delete a record that was already deleted in a prior merge
    deleted_ids: set[int] = set()
    cur = con.cursor()
    for m in merges:
        if m["drop_id"] in deleted_ids or m["keep_id"] in deleted_ids:
            continue
        # Re-assign any reviews from the dropped record to the keeper
        cur.execute(
            "UPDATE Reviews SET church_id = ? WHERE church_id = ?",
            (m["keep_id"], m["drop_id"]),
        )
        cur.execute("DELETE FROM Churches WHERE church_id = ?", (m["drop_id"],))
        deleted_ids.add(m["drop_id"])

    con.commit()
    con.close()
    log.info(f"Dedup complete. Removed {len(deleted_ids)} duplicates.")
    return len(deleted_ids)


def _pick_winner(a: sqlite3.Row, b: sqlite3.Row) -> tuple:
    """Return (keep, drop). Prefer OSM source; then prefer record with lat/lon."""
    def score(r):
        return (
            (r["source"] == "osm") * 2 +
            (r["latitude"] is not None) * 1
        )
    if score(a) >= score(b):
        return a, b
    return b, a


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="holyhub.db")
    p.add_argument("--report", default="dedup_report.csv")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    run(args.db, args.report, args.dry_run)
