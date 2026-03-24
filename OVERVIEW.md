# ChurchMap — Project Overview

## What is ChurchMap?

ChurchMap is a church discovery platform that helps people find a church that actually fits them — not just the nearest one, but the *right* one. Instead of relying on generic star ratings or outdated directories, ChurchMap surfaces what matters to churchgoers: worship energy, community warmth, sermon depth, children's programs, theological stance, and facilities.

**Live:** [churchmap.vercel.app](https://churchmap.vercel.app)

---

## The Problem

Finding a new church is notoriously hard. Google Maps shows you a star rating and hours. Church websites are marketing material. Word-of-mouth only works if you know people. There's no Yelp for churches — and generic restaurant-style reviews don't capture what people actually want to know before walking through the door on a Sunday.

---

## What It Does

- **Search by city/state** — auto-detects your location via IP geolocation on first visit
- **Map + list view** — Google Maps-style: clicking a card flies the map to that church and opens an inline detail panel without leaving the page
- **6-dimension ratings** — Worship Energy, Community Warmth, Sermon Depth, Children's Programs, Theological Stance, Facilities
- **Smart tags** — derived from aggregate dimension scores (e.g., "Vibrant worship", "Deep sermons", "Progressive")
- **Photos, hours, and contact info** — enriched from Google Places for ~4,000 churches
- **Similar churches** — vector-distance matching on dimension ratings to surface churches that feel alike
- **Google Sign-In** — authenticated reviews tied to real Google accounts
- **Filter + sort** — by distance, rating, review count, denomination, language, cultural background

---

## Data Pipeline

| Stage | Source | Scale |
|-------|--------|-------|
| Church roster | IRS 990 tax exemption database + OpenStreetMap | ~5,400 US churches |
| Deduplication | Name + address fuzzy match | Reduced to ~5,400 unique |
| Geocoding | Nominatim (OSM) | Lat/lon for all entries |
| Enrichment | Google Places API (Text Search + Place Details) | ~3,984 enriched ($194 one-time) |
| Storage | SQLite (baked into Docker image) | ~45 MB DB |

The entire dataset lives in a single SQLite file committed into the Docker image. No external database service — the data ships with the code.

---

## System Design

### Architecture

```
Browser (Vercel)          Backend (Fly.io)          Data
──────────────────        ─────────────────         ──────────────
React + Leaflet   ──────► FastAPI (Python)   ──────► SQLite (baked in)
Vite / SPA                2 machines                holyhub.db
                          Auto-scale to 0

Google GSI ──────────────► /api/auth/verify
                           (tokeninfo verification)
```

### Why SQLite?

For a read-heavy discovery app with a static dataset, SQLite outperforms a hosted database on almost every axis:

- **Zero latency** — queries run in-process; no network hop to Postgres/RDS
- **Zero cost** — no managed DB bill; data rides inside the Docker image
- **Simple deploys** — `fly deploy` rebuilds the image with the latest data baked in
- **Sufficient scale** — SQLite handles thousands of concurrent reads comfortably at this data size

The tradeoff: writes (reviews) hit whichever machine handles the request, so review data isn't shared across Fly.io machines in real time. Acceptable for a low-write demo; a future migration to Turso (SQLite with replication) or Postgres resolves this cleanly.

### Why Fly.io + Vercel?

| Concern | Choice | Why |
|---------|--------|-----|
| Frontend | **Vercel** | Zero-config SPA hosting, GitHub auto-deploy, global CDN, free tier |
| Backend | **Fly.io** | Runs real Docker containers (needed for SQLite file), anycast routing, scale-to-zero = ~$2–5/month idle |
| Database | **SQLite in Docker** | No separate service; data baked into image at deploy time |

Vercel can't run a persistent SQLite file — it's serverless functions with ephemeral filesystems. Fly.io runs a real Linux container, so the DB file persists across requests within a machine and survives cold starts because it's baked into the image.

Scale-to-zero on Fly.io means the backend machines shut down when idle and restart in ~1–2 seconds on the next request. For a demo/hackathon with intermittent traffic, this keeps costs near zero between bursts.

### Why FastAPI?

- Native async support for concurrent request handling
- Automatic OpenAPI docs at `/docs`
- Thin and fast — no ORM overhead; raw SQLite queries via `sqlite3`
- Python ecosystem for the data pipeline (scraping, enrichment, dedup) means one language end-to-end

---

## Auth Design

Google Sign-In uses the GSI (Google Identity Services) library directly in the browser. The ID token returned by Google is sent to the backend, which verifies it against Google's tokeninfo endpoint — no JWT library, no session store, no cookies. The token is re-verified on every protected request (review submission).

```
Browser                    Backend                    Google
───────                    ───────                    ──────
[Sign In with Google] ───► POST /api/auth/verify ──► tokeninfo?id_token=...
                           ◄── { user_id, name }  ◄── { sub, email, name }
Store token in localStorage
[Submit Review] ──────────► POST /api/reviews
                            Authorization: Bearer <id_token>
```

---

## Value Proposition

**For churchgoers:** The only platform that rates churches on dimensions that actually matter for fit — not just "good service" or star rating.

**For churches:** Honest feedback across six dimensions surfaces specific strengths and growth areas that generic reviews can't.

**For the market:** No direct competitor. Google Maps and Yelp treat churches like restaurants. ChurchMap is purpose-built for the discovery problem specific to faith communities.

---

## Numbers

- **~5,400** US churches in the database
- **~3,984** enriched with Google Photos, hours, contact info, and editorial summaries
- **6** rating dimensions per review
- **$194** total data enrichment cost (one-time Google Places API spend)
- **~$2–5/month** infrastructure cost at low traffic (Fly.io scale-to-zero + Vercel free tier)
- **< 200ms** median API response time (SQLite in-process, no DB network hop)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, React Router, Leaflet (maps) |
| Styling | CSS custom properties, Fraunces (serif) + Plus Jakarta Sans |
| Backend | FastAPI (Python 3.11) |
| Database | SQLite (baked into Docker image) |
| Auth | Google Identity Services (GSI) + tokeninfo verification |
| Data enrichment | Google Places API (Text Search + Place Details) |
| Data sources | IRS 990 database, OpenStreetMap |
| Hosting | Vercel (frontend) + Fly.io (backend, 2 machines) |
| Deploy | GitHub → Vercel auto-deploy; `fly deploy` for backend |
