# ⛪ HolyHub

Find your church — rated on what actually matters.

HolyHub lets you search churches by city and leave anonymous reviews across six dimensions: worship energy, community warmth, sermon depth, children's programs, theological stance, and facilities.

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + SQLite |
| Frontend | React (Vite) |
| Tests | pytest (28 tests) |

## Setup

**Prerequisites:** Python 3.10+, Node 18+

```bash
# Clone
git clone https://github.com/zhou100/holyhub.git
cd holyhub

# Backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..

# Seed the database
make seed
```

## Running locally

```bash
# Terminal 1 — backend (http://localhost:8000)
make dev-backend

# Terminal 2 — frontend (http://localhost:5173)
make dev-frontend
```

Open [http://localhost:5173](http://localhost:5173) and try **Brooklyn, NY**.

## Commands

```
make dev-backend   Start the API server (uses venv Python)
make dev-frontend  Start the Vite dev server
make seed          Seed 10 churches + 35 reviews
make test          Run the full test suite
make install       Install all dependencies
```

## API

```
GET  /api/churches?city=Brooklyn&state=NY   Search churches
GET  /api/churches/:id                      Church detail + dimensions
GET  /api/reviews/:church_id               Reviews + aggregated dimensions
POST /api/reviews                          Submit an anonymous review
```

## Review dimensions

Each review optionally rates six dimensions on a 1–5 scale:

- **Worship energy** — Is the service lively or contemplative?
- **Community warmth** — Do people make you feel welcome?
- **Sermon depth** — Are the sermons substantive?
- **Children's programs** — Quality of kids ministry
- **Theological stance** — ← Traditional / Progressive →
- **Facilities** — Building and amenities

Tags (e.g. "Vibrant worship", "Progressive", "Traditional") are computed automatically once a church has 3+ reviews.

## Project structure

```
backend/        FastAPI app, routers, seed script
holyhub/        Core services (database, location, reviews)
frontend/       React + Vite
tests/          pytest test suite
```
