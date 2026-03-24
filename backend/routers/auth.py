import os
import sqlite3
import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.deps import get_db, Database

router = APIRouter()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


async def verify_google_token(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": token},
        )
    if r.status_code != 200:
        raise HTTPException(401, "Invalid Google token")
    info = r.json()
    if GOOGLE_CLIENT_ID and info.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(401, "Token audience mismatch")
    return info


class TokenBody(BaseModel):
    token: str


@router.post("/auth/verify")
async def auth_verify(body: TokenBody, db: Database = Depends(get_db)):
    info = await verify_google_token(body.token)
    google_id = info["sub"]
    email = info.get("email", "")
    name = info.get("name", "")
    avatar_url = info.get("picture", "")

    con = sqlite3.connect(db.db_path)
    con.row_factory = sqlite3.Row
    try:
        con.execute(
            """INSERT INTO Users (google_id, email, name, avatar_url)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(google_id) DO UPDATE SET
                 email=excluded.email, name=excluded.name, avatar_url=excluded.avatar_url""",
            (google_id, email, name, avatar_url),
        )
        con.commit()
        row = con.execute(
            "SELECT user_id, name, email, avatar_url FROM Users WHERE google_id=?",
            (google_id,),
        ).fetchone()
        return dict(row)
    finally:
        con.close()
