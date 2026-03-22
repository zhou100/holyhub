from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from holyhub.database import Database
from holyhub.review_services import ReviewServices
from backend.deps import get_db
from backend.utils import compute_tags

router = APIRouter()


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

    # Compute aggregate dimensions from stored reviews
    dim_keys = ["worship_energy", "community_warmth", "sermon_depth",
                "childrens_programs", "theological_openness", "facilities"]
    agg = {}
    for key in dim_keys:
        vals = [r[key] for r in reviews if r[key] is not None]
        agg[key] = round(sum(vals) / len(vals), 2) if vals else None

    return {"dimensions": agg, "reviews": reviews}


@router.post("/reviews", status_code=201)
def submit_review(payload: ReviewCreate, db: Database = Depends(get_db)):
    svc = ReviewServices(db)
    review_id = svc.submit_review(payload.church_id, payload.model_dump())
    if not review_id:
        raise HTTPException(status_code=500, detail="Failed to submit review")
    return {"review_id": review_id}
