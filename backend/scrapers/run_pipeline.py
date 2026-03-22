"""
Church data pipeline runner.

Usage:
  python -m backend.scrapers.run_pipeline --source osm
  python -m backend.scrapers.run_pipeline --source irs --limit 500
  python -m backend.scrapers.run_pipeline --source dedup --dry-run
  python -m backend.scrapers.run_pipeline --all
"""
import argparse
import logging
import sqlite3
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _count(db_path: str) -> int:
    con = sqlite3.connect(db_path)
    n = con.execute("SELECT COUNT(*) FROM Churches").fetchone()[0]
    con.close()
    return n


def main() -> None:
    p = argparse.ArgumentParser(description="HolyHub church data pipeline")
    p.add_argument("--db", default="holyhub.db", help="Path to SQLite database")
    p.add_argument(
        "--source", choices=["migrate", "osm", "fill", "irs", "dedup"],
        help="Run a single pipeline step",
    )
    p.add_argument("--all", action="store_true", help="Run all steps in order")
    p.add_argument("--limit", type=int, default=0,
                   help="IRS: limit geocoding to N records (0 = all, use for testing)")
    p.add_argument("--no-geocode", action="store_true",
                   help="IRS: skip geocoding (faster, records will have no lat/lon)")
    p.add_argument("--dry-run", action="store_true",
                   help="Dedup: report duplicates without deleting")
    args = p.parse_args()

    if not args.source and not args.all:
        p.print_help()
        sys.exit(1)

    steps = [args.source] if args.source else ["migrate", "osm", "fill", "irs", "dedup"]

    for step in steps:
        log.info(f"\n{'='*60}\nStep: {step.upper()}\n{'='*60}")
        before = _count(args.db)

        if step == "migrate":
            from backend.scrapers.migrate import migrate
            migrate(args.db)

        elif step == "fill":
            from backend.scrapers.fill_locations import fill
            updated = fill(args.db)
            log.info(f"Fill: {updated} records updated with city/state")

        elif step == "osm":
            from backend.scrapers.osm_scraper import scrape
            inserted = scrape(args.db)
            log.info(f"OSM: {inserted} new churches added")

        elif step == "irs":
            from backend.scrapers.irs_importer import load
            inserted = load(args.db, limit=args.limit, geocode=not args.no_geocode)
            log.info(f"IRS: {inserted} new churches added")

        elif step == "dedup":
            from backend.scrapers.dedup import run
            removed = run(args.db, dry_run=args.dry_run)
            log.info(f"Dedup: {removed} duplicates removed")

        after = _count(args.db)
        log.info(f"DB size: {before:,} → {after:,} churches")

    final = _count(args.db)
    log.info(f"\nPipeline complete. Total churches in DB: {final:,}")


if __name__ == "__main__":
    main()
