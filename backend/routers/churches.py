from fastapi import APIRouter, Depends, HTTPException
from holyhub.database import Database
from backend.deps import get_db
from backend.utils import compute_tags

router = APIRouter()

_DIM_QUERY = """
    SELECT
        c.church_id AS id,
        c.name,
        c.address,
        c.city,
        c.state,
        c.denomination,
        c.service_times,
        ROUND(AVG(r.rating), 1)               AS avg_rating,
        COUNT(r.review_id)                    AS review_count,
        AVG(r.worship_energy)                 AS avg_worship_energy,
        AVG(r.community_warmth)               AS avg_community_warmth,
        AVG(r.sermon_depth)                   AS avg_sermon_depth,
        AVG(r.childrens_programs)             AS avg_childrens_programs,
        AVG(r.theological_openness)           AS avg_theological_openness,
        AVG(r.facilities)                     AS avg_facilities
    FROM Churches c
    LEFT JOIN Reviews r ON c.church_id = r.church_id
"""


def _row_to_church(row, include_dims: bool = False) -> dict:
    dims = {
        "worship_energy": row["avg_worship_energy"],
        "community_warmth": row["avg_community_warmth"],
        "sermon_depth": row["avg_sermon_depth"],
        "childrens_programs": row["avg_childrens_programs"],
        "theological_openness": row["avg_theological_openness"],
        "facilities": row["avg_facilities"],
    }
    church = {
        "id": row["id"],
        "name": row["name"],
        "address": row["address"],
        "city": row["city"],
        "state": row["state"],
        "denomination": row["denomination"],
        "service_times": row["service_times"],
        "avg_rating": row["avg_rating"],
        "review_count": row["review_count"],
        "tags": compute_tags(dims, row["review_count"] or 0),
    }
    if include_dims:
        church["dimensions"] = {k: (round(v, 2) if v is not None else None) for k, v in dims.items()}
    return church


@router.get("/churches")
def list_churches(city: str = "", state: str = "", db: Database = Depends(get_db)):
    query = _DIM_QUERY + "WHERE c.city = ? AND c.state = ? GROUP BY c.church_id"
    rows = db.execute_query(query, (city, state))
    return [_row_to_church(row) for row in rows]


@router.get("/churches/{church_id}")
def get_church(church_id: int, db: Database = Depends(get_db)):
    query = _DIM_QUERY + "WHERE c.church_id = ? GROUP BY c.church_id"
    rows = db.execute_query(query, (church_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Church not found")
    return _row_to_church(rows[0], include_dims=True)
