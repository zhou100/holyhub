"""
Seed script for HolyHub demo.
Deletes holyhub.db and recreates it from scratch with seed data.

Run from project root:
    python backend/seed.py
"""
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from holyhub.database import Database

DB_PATH = "holyhub.db"

# Remove existing DB so _initialize_database runs fresh
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"Removed existing {DB_PATH}")

db = Database(db_path=DB_PATH)
db.connect()

# ── Churches ────────────────────────────────────────────────────────────────
churches = [
    # Brooklyn, NY — primary demo city (≥5 required)
    ("Brooklyn Tabernacle", "17 Smith St", "Brooklyn", "NY",
     "Non-denominational", "Sun 8am, 10am, 12pm, 6pm"),
    ("St. Ann & the Holy Trinity", "157 Montague St", "Brooklyn", "NY",
     "Episcopal", "Sun 8am, 10am"),
    ("Concord Baptist Church of Christ", "833 Marcy Ave", "Brooklyn", "NY",
     "Baptist", "Sun 8am, 11am"),
    ("Our Lady of Lebanon Maronite Cathedral", "113 Remsen St", "Brooklyn", "NY",
     "Maronite Catholic", "Sun 9am, 11:30am"),
    ("First Presbyterian Church of Brooklyn", "124 Henry St", "Brooklyn", "NY",
     "Presbyterian", "Sun 10:30am"),
    ("Middle Collegiate Church", "112 2nd Ave", "Brooklyn", "NY",
     "Reformed Church in America", "Sun 11am"),
    ("Church of the Open Door", "1060 Atlantic Ave", "Brooklyn", "NY",
     "Non-denominational", "Sun 9am, 11am, 6pm"),
    # Manhattan, NY
    ("Redeemer Presbyterian Church", "150 W 83rd St", "New York", "NY",
     "Presbyterian", "Sun 9am, 11am, 6pm"),
    ("Cathedral Church of St. John the Divine", "1047 Amsterdam Ave", "New York", "NY",
     "Episcopal", "Sun 8am, 9am, 11am"),
    ("Riverside Church", "490 Riverside Dr", "New York", "NY",
     "Non-denominational / Baptist", "Sun 10:45am"),
]

church_ids = []
for name, address, city, state, denom, times in churches:
    cid = db.execute_insert(
        "INSERT INTO Churches (name, address, city, state, denomination, service_times) VALUES (?, ?, ?, ?, ?, ?)",
        (name, address, city, state, denom, times),
    )
    church_ids.append(cid)

print(f"Inserted {len(church_ids)} churches")

# ── Reviews ──────────────────────────────────────────────────────────────────
# (church_index, rating, comment, we, cw, sd, cp, to_, fac)
# Dimension scale: 1-5.  None = reviewer left blank.
reviews = [
    # Brooklyn Tabernacle (idx 0) — vibrant worship, strong community
    (0, 5.0, "The choir is world-famous for a reason. You feel it in your chest.", 5.0, 4.8, 4.2, 4.0, 3.8, 4.5),
    (0, 5.0, "Packed every Sunday — the energy is electric.", 5.0, 4.9, 4.0, 4.2, 3.5, 4.3),
    (0, 4.0, "Wonderful worship, though sermons can run long.", 4.8, 4.5, 3.8, 3.5, 3.5, 4.0),
    (0, 5.0, "Great kids programs, very welcoming to newcomers.", 4.9, 4.9, 4.1, 4.5, 3.8, 4.4),
    # St. Ann & Holy Trinity (idx 1) — traditional, deep sermons, beautiful building
    (1, 4.0, "Stunning Gothic interior. The liturgy feels ancient and meaningful.", 3.0, 3.8, 4.8, 2.5, 3.5, 5.0),
    (1, 5.0, "Rector gives some of the most intellectually serious sermons I've heard.", 2.8, 4.0, 5.0, 2.0, 3.0, 4.8),
    (1, 3.0, "Very traditional — beautiful if that's your style, cold if not.", 2.5, 3.0, 4.5, 1.5, 2.5, 4.9),
    (1, 4.0, "Lovely choir, small congregation, feels intimate.", 3.2, 3.5, 4.7, 2.0, 2.8, 4.7),
    # Concord Baptist (idx 2) — strong community, gospel energy
    (2, 5.0, "This congregation has been the heart of Bedford-Stuyvesant for generations.", 4.5, 5.0, 4.0, 4.5, 3.2, 3.8),
    (2, 4.0, "Powerful gospel choir, deeply rooted community.", 4.8, 4.8, 3.8, 4.0, 3.0, 3.5),
    (2, 5.0, "The most welcoming church I've visited in Brooklyn.", 4.3, 5.0, 4.2, 4.8, 3.5, 3.6),
    (2, 4.0, "Sermons grounded in social justice — refreshingly relevant.", 4.0, 4.9, 4.0, 4.2, 4.0, 3.4),
    # Our Lady of Lebanon (idx 3) — traditional, intimate
    (3, 4.0, "Unique Maronite liturgy — a slice of Lebanese culture in Brooklyn.", 3.2, 4.2, 4.3, 2.5, 2.5, 4.2),
    (3, 5.0, "The incense, the chanting — takes you somewhere else entirely.", 3.8, 4.5, 4.5, 2.0, 2.0, 4.5),
    (3, 3.0, "Very traditional. Not welcoming to those outside the Lebanese community.", 2.8, 2.8, 3.8, 1.5, 1.5, 3.8),
    # First Presbyterian (idx 4) — progressive, intellectual
    (4, 4.0, "Open and affirming congregation — very LGBTQ+ welcoming.", 3.0, 4.5, 4.3, 3.5, 5.0, 3.8),
    (4, 5.0, "Thoughtful sermons, educated congregation, great coffee hour.", 3.2, 4.8, 4.8, 3.0, 4.8, 3.5),
    (4, 4.0, "Quiet worship — contemplative and intellectual.", 2.8, 4.3, 4.5, 2.5, 4.5, 3.5),
    (4, 3.0, "A bit small and aging. Great theology, hope it grows.", 2.5, 4.0, 4.2, 2.0, 4.3, 3.2),
    # Middle Collegiate (idx 5) — progressive, vibrant, inclusive
    (5, 5.0, "The most joyful, inclusive church I've ever attended. Dance, music, love.", 5.0, 5.0, 4.0, 4.5, 5.0, 4.0),
    (5, 5.0, "Drag queens in the choir, refugees in the pews. This is church.", 4.8, 5.0, 4.2, 4.3, 5.0, 4.2),
    (5, 4.0, "Not traditional at all — but genuinely transformative.", 4.5, 4.8, 3.8, 4.0, 4.8, 3.8),
    (5, 5.0, "Best music in New York. Full stop.", 5.0, 4.9, 3.5, None, 4.5, 4.0),
    # Church of the Open Door (idx 6) — energetic, family-focused
    (6, 4.0, "Modern worship style, great for families.", 4.5, 4.5, 3.8, 5.0, 4.0, 4.5),
    (6, 5.0, "Kids loved the children's program. We'll be back.", 4.0, 4.8, 3.5, 5.0, 3.8, 4.3),
    (6, 4.0, "Contemporary feel — not my style but clearly well-run.", 4.2, 4.2, 3.5, 4.5, 4.0, 4.0),
    # Redeemer Presbyterian (idx 7) — Manhattan, intellectual
    (7, 5.0, "Tim Keller's legacy still runs deep. Intellectually rigorous.", 3.5, 4.5, 5.0, 3.5, 3.5, 4.5),
    (7, 4.0, "Excellent sermons. The faith-and-work integration is unique.", 3.2, 4.3, 4.8, 3.0, 3.8, 4.2),
    (7, 5.0, "Great for young professionals.", 3.0, 4.8, 4.5, 3.0, 3.5, 4.0),
    # Cathedral of St. John (idx 8) — grand, progressive, facilities
    (8, 5.0, "The largest cathedral in the world. Standing inside is humbling.", 3.5, 4.0, 4.2, 3.0, 4.5, 5.0),
    (8, 4.0, "Very inclusive, interfaith-friendly. The space alone is worth a visit.", 3.0, 4.2, 4.0, 3.5, 4.8, 5.0),
    (8, 3.0, "Feels more like a museum than a congregation sometimes.", 2.5, 3.5, 3.8, 2.5, 4.0, 5.0),
    # Riverside Church (idx 9) — progressive, social justice
    (9, 5.0, "Social justice preaching at its finest. MLK preached here.", 3.8, 4.8, 4.8, 3.0, 5.0, 4.8),
    (9, 4.0, "Politically active, intellectually stimulating, inclusive.", 3.5, 4.5, 4.5, 2.5, 4.8, 4.5),
    (9, 5.0, "The view from the tower. The activism. The music. All 5 stars.", 3.5, 4.5, 4.5, 2.5, 5.0, 4.8),
]

for (church_idx, rating, comment, we, cw, sd, cp, to_, fac) in reviews:
    db.execute_insert(
        """INSERT INTO Reviews
           (church_id, rating, comment, worship_energy, community_warmth,
            sermon_depth, childrens_programs, theological_openness, facilities)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (church_ids[church_idx], rating, comment, we, cw, sd, cp, to_, fac),
    )

print(f"Inserted {len(reviews)} reviews")

# Verify
count = db.execute_query("SELECT COUNT(*) AS n FROM Churches")[0]["n"]
rcount = db.execute_query("SELECT COUNT(*) AS n FROM Reviews")[0]["n"]
print(f"DB verified: {count} churches, {rcount} reviews")
print("Seed complete. Run: uvicorn backend.main:app --reload")
