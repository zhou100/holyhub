import os
import sqlite3
import httpx
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional
from holyhub.database import Database
from holyhub.review_services import ReviewServices
from backend.deps import get_db

router = APIRouter()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in to leave a review")
    token = authorization.split(" ", 1)[1]
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": token},
        )
    if r.status_code != 200:
        raise HTTPException(401, "Invalid or expired token — please sign in again")
    info = r.json()
    if GOOGLE_CLIENT_ID and info.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(401, "Token audience mismatch")
    return {
        "google_id": info["sub"],
        "name": info.get("name", ""),
        "avatar_url": info.get("picture", ""),
        "email": info.get("email", ""),
    }


class ReviewCreate(BaseModel):
    church_id: int
    rating: float = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    worship_energy: Optional[float] = Field(None, ge=1, le=5)
    community_warmth: Optional[float] = Field(None, ge=1, le=5)
    sermon_depth: Optional[float] = Field(None, ge=1, le=5)
    childrens_programs: Optional[float] = Field(None, ge=1, le=5)
    theological_openness: Optional[float] = Field(None, ge=1, le=5)
    facilities: Optional[float] = Field(None, ge=1, le=5)


@router.get("/reviews/{church_id}")
def get_reviews(church_id: int, db: Database = Depends(get_db)):
    svc = ReviewServices(db)
    reviews = svc.get_reviews(church_id)

    dim_keys = ["worship_energy", "community_warmth", "sermon_depth",
                "childrens_programs", "theological_openness", "facilities"]
    agg = {}
    for key in dim_keys:
        vals = [r[key] for r in reviews if r.get(key) is not None]
        agg[key] = round(sum(vals) / len(vals), 2) if vals else None

    return {"dimensions": agg, "reviews": reviews}


@router.post("/reviews", status_code=201)
async def submit_review(
    payload: ReviewCreate,
    db: Database = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    con = sqlite3.connect(db.db_path)
    con.row_factory = sqlite3.Row
    try:
        # Upsert user
        con.execute(
            """INSERT INTO Users (google_id, email, name, avatar_url)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(google_id) DO UPDATE SET
                 email=excluded.email, name=excluded.name, avatar_url=excluded.avatar_url""",
            (user["google_id"], user.get("email", ""), user["name"], user["avatar_url"]),
        )
        row = con.execute(
            "SELECT user_id FROM Users WHERE google_id=?", (user["google_id"],)
        ).fetchone()
        user_id = row["user_id"]

        cur = con.execute(
            """INSERT INTO Reviews (
                church_id, rating, comment,
                worship_energy, community_warmth, sermon_depth,
                childrens_programs, theological_openness, facilities,
                user_id, reviewer_name, reviewer_avatar
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                payload.church_id, payload.rating, payload.comment,
                payload.worship_energy, payload.community_warmth, payload.sermon_depth,
                payload.childrens_programs, payload.theological_openness, payload.facilities,
                user_id, user["name"], user["avatar_url"],
            ),
        )
        con.commit()
        return {"review_id": cur.lastrowid}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        con.close()
