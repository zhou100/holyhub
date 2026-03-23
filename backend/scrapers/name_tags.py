"""
Infer `language` and `cultural_background` from church name + denomination.

Rules are applied in priority order — first match wins.
Run once (or re-run anytime; it only updates rows where both fields are NULL).
Pass --force to re-tag everything.

Usage:
    python -m backend.scrapers.name_tags           # tag un-tagged rows
    python -m backend.scrapers.name_tags --force   # re-tag all rows
    python -m backend.scrapers.name_tags --dry-run # print matches, don't write
"""

import re
import sqlite3
import sys
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Pattern tables
# Each entry: (regex_pattern, language, cultural_background)
# cultural_background=None means inherit from context (language already says it)
# Order matters — first match wins.
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    pattern: str
    language: str | None
    cultural_background: str | None

RULES: list[Rule] = [
    # ── Spanish / Latino ────────────────────────────────────────────────────
    # "san/santa" alone are too ambiguous (San Mateo, Santa Barbara are US place names)
    Rule(r"iglesia|primera\b|segundo\b|nueva\b|cristo\b|dios\b|señor\b|"
         r"espiritu\b|sagrada\b|virgen\b|nuestra\b|evangelio\b|parroquia\b|"
         r"templo\b|catedral\b|hispana|hispanica|latina|latino|española|español",
         "Spanish", "Hispanic/Latino"),

    # ── Korean ───────────────────────────────────────────────────────────────
    Rule(r"korean|한국|코리안", "Korean", "Korean"),

    # ── Chinese (Mandarin / Cantonese) ───────────────────────────────────────
    Rule(r"chinese|mandarin|cantonese|中文|华人|taiwanese|台灣|台湾",
         "Chinese", "Chinese"),

    # ── Vietnamese ───────────────────────────────────────────────────────────
    Rule(r"vietnamese|viet\b|việt", "Vietnamese", "Vietnamese"),

    # ── Filipino / Tagalog ───────────────────────────────────────────────────
    Rule(r"filipino|pilipino|tagalog|philippine", "Filipino", "Filipino"),

    # ── Portuguese / Brazilian ───────────────────────────────────────────────
    Rule(r"portuguesa|brasileira|brasil\b|lusitano|lusitana|portuguese",
         "Portuguese", "Brazilian/Portuguese"),

    # ── Haitian Creole / French ──────────────────────────────────────────────
    Rule(r"haitian|haïtien|haitien|francophone|française|creole",
         "Haitian Creole", "Haitian"),

    # ── Arabic ───────────────────────────────────────────────────────────────
    Rule(r"\barabic\b|\barab\b", "Arabic", "Arab"),

    # ── Amharic / East African ──────────────────────────────────────────────
    Rule(r"ethiopian|eritrean|amharic|oromo", "Amharic", "East African"),

    # ── Hmong ────────────────────────────────────────────────────────────────
    Rule(r"\bhmong\b", "Hmong", "Hmong"),

    # ── Hindi / South Asian ─────────────────────────────────────────────────
    # "Indian" alone is ambiguous (Native American vs South Asian); require a language
    Rule(r"\bhindi\b|\bpunjabi\b|\btelugu\b|\btamil\b|\bmalayalam\b|\bsouth asian\b",
         "Hindi", "South Asian"),

    # ── Japanese ─────────────────────────────────────────────────────────────
    Rule(r"\bjapanese\b", "Japanese", "Japanese"),

    # ── African American (cultural, English language) ────────────────────────
    # AME = African Methodist Episcopal; many historic Black church traditions
    # Explicitly exclude "Zion Lutheran/Methodist/Reformed" — those are historically white.
    Rule(r"\bame\b(?!\s*zion\s+lutheran|\s*zion\s+methodist)|"
         r"african methodist episcopal|"
         r"national baptist|progressive national|"
         r"national missionary baptist|"
         r"colored methodist|c\.m\.e\.|"
         r"mount zion\b|"
         r"\bame zion\b",
         "English", "African American"),

    # ── Swahili / African (continental) ─────────────────────────────────────
    # Exclude "African Methodist Episcopal" — that's African American, not African
    Rule(r"\bswahili\b|\bafrican\b(?!\s+methodist)", "Swahili", "African"),
]

_COMPILED: list[tuple[re.Pattern, str | None, str | None]] = [
    (re.compile(r.pattern, re.IGNORECASE), r.language, r.cultural_background)
    for r in RULES
]


def detect(name: str, denomination: str | None) -> tuple[str | None, str | None]:
    """Return (language, cultural_background) for a church row."""
    text = f"{name} {denomination or ''}"
    for pattern, lang, culture in _COMPILED:
        if pattern.search(text):
            return lang, culture
    return None, None


def run(db_path: str = "holyhub.db", force: bool = False, dry_run: bool = False) -> None:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    if force:
        rows = con.execute(
            "SELECT church_id, name, denomination FROM Churches"
        ).fetchall()
    else:
        rows = con.execute(
            """SELECT church_id, name, denomination FROM Churches
               WHERE language IS NULL AND cultural_background IS NULL"""
        ).fetchall()

    print(f"Processing {len(rows)} churches …")
    tagged = 0

    for row in rows:
        lang, culture = detect(row["name"], row["denomination"])
        if lang or culture:
            tagged += 1
            if dry_run:
                print(f"  [{row['church_id']}] {row['name']}  →  lang={lang}  culture={culture}")
            else:
                con.execute(
                    "UPDATE Churches SET language=?, cultural_background=? WHERE church_id=?",
                    (lang, culture, row["church_id"])
                )

    if not dry_run:
        con.commit()

    con.close()
    print(f"Done. Tagged {tagged}/{len(rows)} churches.")


if __name__ == "__main__":
    force   = "--force"   in sys.argv
    dry_run = "--dry-run" in sys.argv
    db_path = next((a for a in sys.argv[1:] if not a.startswith("--")), "holyhub.db")
    run(db_path, force=force, dry_run=dry_run)
