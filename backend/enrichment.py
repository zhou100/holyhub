"""
Google Places enrichment — lazy, cached, hard-capped at 3 000 calls/month.

Flow:
  1. Check if church already enriched → return cached data (free)
  2. Check monthly counter → if >= MONTHLY_CAP, skip (free)
  3. Call Places API: Find Place → Place Details → store photos/hours
  4. Increment counter
"""
import json
import logging
import os
from datetime import datetime, timezone

import requests

log = logging.getLogger(__name__)

MONTHLY_CAP = 3_000          # stays well within $200 free tier
PHOTOS_PER_CHURCH = 3
PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_KEY", "")

FIND_URL   = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
DETAIL_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PHOTO_URL  = "https://maps.googleapis.com/maps/api/place/photo"


def _this_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _usage(con) -> int:
    month = _this_month()
    row = con.execute(
        "SELECT count FROM api_usage WHERE month=? AND service='google_places'",
        (month,)
    ).fetchone()
    return row[0] if row else 0


def _increment(con) -> None:
    month = _this_month()
    con.execute("""
        INSERT INTO api_usage (month, service, count) VALUES (?, 'google_places', 1)
        ON CONFLICT(month, service) DO UPDATE SET count = count + 1
    """, (month,))
    con.commit()


def _find_place_id(name: str, lat: float, lon: float) -> str | None:
    if not PLACES_API_KEY:
        return None
    r = requests.get(FIND_URL, params={
        "input": name,
        "inputtype": "textquery",
        "locationbias": f"point:{lat},{lon}",
        "fields": "place_id",
        "key": PLACES_API_KEY,
    }, timeout=5)
    candidates = r.json().get("candidates", [])
    return candidates[0]["place_id"] if candidates else None


def _fetch_details(place_id: str) -> dict:
    r = requests.get(DETAIL_URL, params={
        "place_id": place_id,
        "fields": (
            "website,formatted_phone_number,opening_hours,photos,"
            "rating,user_ratings_total,reviews,"
            "editorial_summary,wheelchair_accessible_entrance,formatted_address"
        ),
        "key": PLACES_API_KEY,
    }, timeout=5)
    return r.json().get("result", {})


def _photo_url(photo_ref: str) -> str:
    return (
        f"{PHOTO_URL}?maxwidth=800"
        f"&photo_reference={photo_ref}"
        f"&key={PLACES_API_KEY}"
    )


def enrich(church_id: int, con) -> dict | None:
    """
    Attempt to enrich a church with Google Places data.
    Returns the enrichment dict (photos, hours, etc.) or None if skipped.
    Always safe to call — never raises, never exceeds cap.
    """
    if not PLACES_API_KEY:
        return None

    row = con.execute(
        """SELECT name, latitude, longitude, website, phone,
                  google_place_id, google_photos, google_hours, google_enriched_at,
                  google_rating, google_review_count, google_reviews,
                  google_editorial, google_wheelchair, google_address
           FROM Churches WHERE church_id = ?""",
        (church_id,)
    ).fetchone()

    if not row:
        return None

    (name, lat, lon, website, phone, place_id, photos_json, hours_json, enriched_at,
     g_rating, g_review_count, g_reviews_json, g_editorial, g_wheelchair, g_address) = row

    # Already enriched — return cache
    if enriched_at:
        return {
            "photos":       json.loads(photos_json)   if photos_json   else [],
            "hours":        json.loads(hours_json)    if hours_json    else [],
            "rating":       g_rating,
            "review_count": g_review_count,
            "reviews":      json.loads(g_reviews_json) if g_reviews_json else [],
            "editorial":    g_editorial,
            "wheelchair":   bool(g_wheelchair) if g_wheelchair is not None else None,
            "address":      g_address,
        }

    # Hard cap check
    if _usage(con) >= MONTHLY_CAP:
        log.info("Google Places monthly cap reached — skipping enrichment")
        return None

    if not lat or not lon:
        return None

    try:
        # Find Place ID
        if not place_id:
            place_id = _find_place_id(name, lat, lon)
            _increment(con)
            if not place_id:
                # Mark as attempted so we don't keep retrying
                con.execute(
                    "UPDATE Churches SET google_enriched_at=? WHERE church_id=?",
                    (datetime.now(timezone.utc).isoformat(), church_id)
                )
                con.commit()
                return None

        # Fetch details
        details = _fetch_details(place_id)
        _increment(con)

        # Extract photos
        photo_refs = [p["photo_reference"] for p in details.get("photos", [])[:PHOTOS_PER_CHURCH]]
        photos = [_photo_url(ref) for ref in photo_refs]

        # Extract opening hours
        hours = details.get("opening_hours", {}).get("weekday_text", [])

        # Extract new fields
        rating       = details.get("rating")
        review_count = details.get("user_ratings_total")
        raw_reviews  = details.get("reviews", [])
        reviews = [
            {
                "author":  r.get("author_name"),
                "rating":  r.get("rating"),
                "text":    r.get("text"),
                "time":    r.get("relative_time_description"),
            }
            for r in raw_reviews
        ]
        editorial   = details.get("editorial_summary", {}).get("overview")
        wheelchair  = details.get("wheelchair_accessible_entrance")
        g_address   = details.get("formatted_address")

        # Fill in missing website/phone/address from Google if not already in DB
        g_website = details.get("website")
        g_phone   = details.get("formatted_phone_number")

        con.execute("""
            UPDATE Churches SET
                google_place_id    = ?,
                google_photos      = ?,
                google_hours       = ?,
                google_enriched_at = ?,
                google_rating      = ?,
                google_review_count= ?,
                google_reviews     = ?,
                google_editorial   = ?,
                google_wheelchair  = ?,
                google_address     = ?,
                website  = COALESCE(NULLIF(website,  ''), ?),
                phone    = COALESCE(NULLIF(phone,    ''), ?)
            WHERE church_id = ?
        """, (
            place_id,
            json.dumps(photos),
            json.dumps(hours),
            datetime.now(timezone.utc).isoformat(),
            rating, review_count,
            json.dumps(reviews),
            editorial,
            1 if wheelchair else (0 if wheelchair is False else None),
            g_address,
            g_website, g_phone,
            church_id,
        ))
        con.commit()

        log.info(f"Enriched church {church_id} ({name}): {len(photos)} photos, rating={rating}")
        return {
            "photos":       photos,
            "hours":        hours,
            "rating":       rating,
            "review_count": review_count,
            "reviews":      reviews,
            "editorial":    editorial,
            "wheelchair":   wheelchair,
            "address":      g_address,
        }

    except Exception as e:
        log.warning(f"Enrichment failed for church {church_id}: {e}")
        return None
