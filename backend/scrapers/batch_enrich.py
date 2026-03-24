"""
Batch Google Places enrichment — burns through the monthly cap on the best churches first.

Priority order:
  1. Churches with user reviews (most impactful for demo)
  2. Churches in major US cities (most likely to be visited)
  3. Everything else with lat/lon

Usage:
    python -m backend.scrapers.batch_enrich              # up to MONTHLY_CAP
    python -m backend.scrapers.batch_enrich --limit 500  # stop after N churches
    python -m backend.scrapers.batch_enrich --dry-run    # count only, no API calls
"""

import sqlite3
import sys
import time
from datetime import datetime

from backend import enrichment


PRIORITY_CITIES = {
    "new york", "los angeles", "chicago", "houston", "phoenix",
    "philadelphia", "san antonio", "san diego", "dallas", "san jose",
    "austin", "jacksonville", "fort worth", "columbus", "charlotte",
    "indianapolis", "san francisco", "seattle", "denver", "washington",
    "nashville", "oklahoma city", "el paso", "boston", "portland",
    "las vegas", "memphis", "louisville", "baltimore", "milwaukee",
    "atlanta", "miami", "minneapolis", "tulsa", "cleveland",
    "raleigh", "colorado springs", "virginia beach", "omaha", "long beach",
}


def _candidates(con, limit: int) -> list:
    """Return church IDs in priority order, up to limit."""
    rows = con.execute("""
        SELECT c.church_id, c.name, c.city, COUNT(r.review_id) AS rc
        FROM Churches c
        LEFT JOIN Reviews r ON c.church_id = r.church_id
        WHERE c.latitude IS NOT NULL
          AND c.longitude IS NOT NULL
          AND c.google_enriched_at IS NULL
        GROUP BY c.church_id
        ORDER BY
            rc DESC,
            CASE WHEN LOWER(c.city) IN ({})
                 THEN 0 ELSE 1 END,
            c.church_id
        LIMIT ?
    """.format(",".join("?" * len(PRIORITY_CITIES))),
        (*PRIORITY_CITIES, limit)
    ).fetchall()
    return rows


def run(db_path: str = "holyhub.db", limit: int | None = None, dry_run: bool = False) -> None:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    cap    = enrichment.MONTHLY_CAP
    used   = enrichment._usage(con)
    budget = cap - used
    max_churches = budget // 2          # 2 API calls per church (Find + Details)

    if limit is not None:
        max_churches = min(max_churches, limit)

    print(f"Monthly cap:     {cap:,}")
    print(f"Already used:    {used:,}")
    print(f"Remaining calls: {budget:,}")
    print(f"Max churches:    {max_churches:,}")

    if max_churches <= 0:
        print("Cap reached — nothing to do.")
        con.close()
        return

    candidates = _candidates(con, max_churches)
    print(f"Candidates:      {len(candidates):,}")
    print()

    if dry_run:
        for r in candidates[:20]:
            print(f"  [{r[0]}] {r[1]} ({r[2]})  reviews={r[3]}")
        if len(candidates) > 20:
            print(f"  … and {len(candidates) - 20} more")
        con.close()
        return

    ok = skipped = errors = 0
    start = time.time()

    for i, row in enumerate(candidates):
        church_id, name, city, _ = row
        result = enrichment.enrich(church_id, con)

        if result is None:
            skipped += 1
        elif result.get("photos") or result.get("hours"):
            ok += 1
        else:
            skipped += 1

        if (i + 1) % 50 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            remaining = len(candidates) - (i + 1)
            eta = remaining / rate if rate > 0 else 0
            used_now = enrichment._usage(con)
            print(
                f"  [{i+1}/{len(candidates)}]  ok={ok}  skip={skipped}  "
                f"api_calls={used_now}  "
                f"elapsed={elapsed:.0f}s  eta={eta:.0f}s"
            )

    elapsed = time.time() - start
    final_usage = enrichment._usage(con)
    print()
    print(f"Done in {elapsed:.1f}s")
    print(f"  Enriched:   {ok:,}")
    print(f"  Skipped:    {skipped:,}")
    print(f"  API calls:  {final_usage:,} / {cap:,}")
    print(f"  Est. cost:  ${final_usage * 0.018:.2f}")
    con.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    limit   = None
    for arg in sys.argv[1:]:
        if arg.startswith("--limit="):
            limit = int(arg.split("=")[1])
        elif arg == "--limit" and sys.argv.index(arg) + 1 < len(sys.argv):
            limit = int(sys.argv[sys.argv.index(arg) + 1])
    db_path = next(
        (a for a in sys.argv[1:] if not a.startswith("--") and a.endswith(".db")),
        "holyhub.db"
    )
    run(db_path, limit=limit, dry_run=dry_run)
