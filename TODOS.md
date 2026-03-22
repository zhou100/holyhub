# HolyHub — Implementation TODOs
Updated by /plan-ceo-review on 2026-03-22
Design doc: ~/.gstack/projects/holyhub/yujunz-unknown-design-20260321-231618.md
CEO plan: ~/.gstack/projects/holyhub/ceo-plans/2026-03-22-holyhub-hackathon.md

## CEO Review decisions (2026-03-22)

- **Demo CTA:** Add "Try: Brooklyn, NY →" hint link below search form (Search.jsx)
- **Animated bars:** CSS `fillBar` keyframe 0→value over 600ms ease-out (DimensionBars.jsx); `prefers-reduced-motion` override
- **Gradient photos:** Deterministic HSL gradient `hue = (church.id * 37) % 360` on ChurchCard.jsx
- **Post-submit animation:** `key={reviewCount}` on DimensionBars re-triggers animation; disable submit button while `isSubmitting` to prevent race
- **Theological stance label:** Rename "Theological openness" bar → "Theological stance" with sublabel `← Traditional / Progressive →`
- **ReviewForm:** Inline at bottom of ChurchDetail (not modal)
- **Null dimension bars:** Show muted empty bar with "No ratings yet" tooltip (not "0")
- **`avg_rating = null`:** Frontend shows "—" for churches with 0 reviews (not NaN/error)
- **ChurchDetail errors:** Individual error boundaries for each parallel fetch (`Promise.all` → separate try/catch per request)

---

## Architecture decisions locked in
- **1A** — `backend/deps.py` owns `db` singleton + `get_db()` FastAPI dependency (breaks circular import)
- **2A** — All service imports changed to `from holyhub.X import X` (fixes ModuleNotFoundError at runtime)
- **3A** — `with self.db:` blocks removed from ReviewServices (prevents closing shared connection on every call)
- **4A** — `compute_tags` uses `(dims.get("key") or 0)` guard (prevents `TypeError: None > float` crash)

---

## Step 0 — Package marker + schema + database.py (15 min)

- [ ] Create `holyhub/__init__.py` (empty — makes it importable as `holyhub.database`, etc.)
- [ ] Edit `holyhub/schema.sql`: add `denomination TEXT`, `service_times TEXT` to Churches; add 6 dim columns + drop `user_id` FK + remove `username` from Reviews (see design doc for exact SQL)
- [ ] Edit `holyhub/database.py`:
  - Add `self.connection.row_factory = sqlite3.Row` inside `connect()` after `sqlite3.connect()`
  - Add `execute_insert(query, params) -> int` method returning `cursor.lastrowid`
- [ ] Delete `holyhub.db` if it exists: `rm -f holyhub.db`

## Step 1 — Adapt existing services (20 min)

- [ ] Edit `holyhub/location_services.py`:
  - Change `from database import Database` → `from holyhub.database import Database`
  - Remove dead code: `get_location_by_ip` method + `import requests` + `import sqlite3` (startup crash risk)
  - Fix Bug 2: `SELECT id, name...` → `SELECT church_id AS id, name, address, city, state, denomination, service_times`
- [ ] Edit `holyhub/review_services.py`:
  - Change imports: `from holyhub.database import Database`, `from holyhub.models import Review` (drop `auth_services` import)
  - Change constructor: `def __init__(self, db: Database)` (accept injected db, don't create own)
  - `get_reviews`: remove `with self.db:`, use named column access (`row['rating']`), return 6 dimension fields, remove Users JOIN
  - `submit_review(church_id, review)`: remove auth entirely, use `execute_insert()`, return `review_id`
- [ ] Edit `holyhub/models.py`:
  - Add 6 `Optional[float]` fields to `Review.__init__`: `worship_energy`, `community_warmth`, `sermon_depth`, `childrens_programs`, `theological_openness`, `facilities`

## Step 2 — Backend scaffold (15 min)

- [ ] Create `backend/__init__.py` (empty)
- [ ] Create `backend/routers/__init__.py` (empty)
- [ ] Create `backend/deps.py`:
  ```python
  from holyhub.database import Database
  db = Database()
  def get_db() -> Database:
      return db
  ```
- [ ] Create `backend/utils.py` — `compute_tags(dims, review_count)` with `(dims.get("key") or 0)` guard (Issue 4A)
- [ ] Create `backend/main.py` — FastAPI app, CORS `allow_origins=["http://localhost:5173"]`, startup hook that calls `deps.db.connect()`

## Step 3 — Routers (25 min)

- [ ] Create `backend/routers/churches.py`:
  - `GET /api/churches?city=&state=` — LEFT JOIN Reviews, GROUP BY church_id, compute_tags per church
  - `GET /api/churches/{id}` — same JOIN, plus `dimensions` dict embedded in response; 404 if not found
- [ ] Create `backend/routers/reviews.py`:
  - `GET /api/reviews/{church_id}` — returns `{dimensions: {...}, reviews: [...]}`
  - `POST /api/reviews` — Pydantic `ReviewCreate(BaseModel)` for validation, calls `execute_insert`, returns `{review_id: N}`

## Step 4 — Seed data (20 min)

- [ ] Create `backend/seed.py`:
  - 10 churches, **at least 5 in Brooklyn, NY** (for demo search)
  - 3-5 anonymous reviews each with realistic dimension scores
  - Run as: `python backend/seed.py` (deletes DB first, recreates from seed)

## Step 5 — React scaffold + Search page (30 min)

- [ ] Scaffold frontend: `npm create vite@latest frontend -- --template react`, install deps
- [ ] `frontend/src/pages/Search.jsx` — city/state input → `GET /api/churches` → ChurchCard list + loading state
- [ ] `frontend/src/components/ChurchCard.jsx` — name, denomination, avg_rating stars, tag chips, review count

## Step 6 — ChurchDetail page (30 min)

- [ ] `frontend/src/pages/ChurchDetail.jsx` — `Promise.all([GET /api/churches/{id}, GET /api/reviews/{id}])`, loading state until both resolve
- [ ] `frontend/src/components/DimensionBars.jsx` — 6 horizontal bars (0-5 scale, labelled)
- [ ] Individual review cards in ChurchDetail

## Step 7 — ReviewForm (15 min)

- [ ] `frontend/src/components/ReviewForm.jsx` — overall rating + comment + 6 dimension star inputs (optional per dim)
- [ ] `frontend/src/components/StarInput.jsx` — reusable 1-5 star selector
- [ ] On POST success: refetch `GET /api/reviews/{id}` + `GET /api/churches/{id}` to update bars + avg

## Step 8 — Polish (20 min)

- [ ] Empty states: "No churches found in {city}, {state}" and "No reviews yet — be the first!"
- [ ] Error toasts: failed review submission, API unreachable
- [ ] Verify `npm run dev` + `uvicorn backend.main:app --reload` both start clean from project root

---

## Tests (write alongside Step 2–4)

- [ ] Install test deps: `pip install pytest httpx`
- [ ] Create `tests/__init__.py`
- [ ] `tests/test_database.py` — execute_query returns Row, execute_insert returns lastrowid
- [ ] `tests/test_churches.py` — GET /api/churches returns list; GET /api/churches/{id} returns 200 + dims, 404 for missing
- [ ] `tests/test_reviews.py` — GET returns {dimensions, reviews}; POST returns {review_id}
- [ ] `tests/test_utils.py` — compute_tags: None inputs return [], count < 3 returns [], threshold conditions

Run with: `pytest tests/ -v` from project root

---

## Not in scope for demo

- Auth / login / signup
- IP geolocation (IPINFO cut)
- Map view
- Admin panel / moderation
- Photo uploads
- Production deployment

---

## Phase 2 backlog (post-hackathon)

- [ ] **Tag filter on search results** — Client-side filter by tag chip click. `activeTag` state in Search.jsx filters the already-fetched church array. No API call needed. Effort: S (CC: ~4 min). Depends on: tags showing on cards (in scope).
- [ ] **Similar churches on ChurchDetail** — `GET /api/churches/{id}/similar` returning top 3 by cosine similarity of 6-dim vectors. Small card row at bottom of detail page. Best with real crowdsourced data (weak on 10 seeded churches). Effort: M (CC: ~8 min). Depends on: churches having dimension scores in DB.
- [ ] **Church leader profile claiming** — Church can claim listing, add official description, respond to reviews. Requires auth layer first. Phase 3+.
- [ ] **Optional auth / user profiles** — Let reviewers optionally sign in to claim their reviews. No breaking change to anonymous reviews. Effort: L (CC: ~M).
- [ ] **Multi-city support** — Search any US city. Requires real crowdsourced data, not seed data. Phase 3+.
