from typing import List, Dict, Optional
from holyhub.database import Database
import logging


class ReviewServices:
    def __init__(self, db: Database):
        self.db = db

    def get_reviews(self, church_id: int) -> List[Dict]:
        query = """
            SELECT review_id, church_id, rating, comment,
                   worship_energy, community_warmth, sermon_depth,
                   childrens_programs, theological_openness, facilities,
                   created_at, reviewer_name, reviewer_avatar
            FROM Reviews
            WHERE church_id = ?
            ORDER BY created_at DESC
        """
        try:
            rows = self.db.execute_query(query, (church_id,))
            return [
                {
                    "id": row["review_id"],
                    "rating": row["rating"],
                    "comment": row["comment"],
                    "worship_energy": row["worship_energy"],
                    "community_warmth": row["community_warmth"],
                    "sermon_depth": row["sermon_depth"],
                    "childrens_programs": row["childrens_programs"],
                    "theological_openness": row["theological_openness"],
                    "facilities": row["facilities"],
                    "created_at": row["created_at"],
                    "reviewer_name": row["reviewer_name"],
                    "reviewer_avatar": row["reviewer_avatar"],
                }
                for row in rows
            ]
        except Exception as e:
            logging.error(f"Error fetching reviews: {e}")
            return []

    def submit_review(self, church_id: int, review: Dict) -> Optional[int]:
        query = """
            INSERT INTO Reviews (
                church_id, rating, comment,
                worship_energy, community_warmth, sermon_depth,
                childrens_programs, theological_openness, facilities
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            review_id = self.db.execute_insert(query, (
                church_id,
                review.get("rating"),
                review.get("comment"),
                review.get("worship_energy"),
                review.get("community_warmth"),
                review.get("sermon_depth"),
                review.get("childrens_programs"),
                review.get("theological_openness"),
                review.get("facilities"),
            ))
            return review_id
        except Exception as e:
            logging.error(f"Error submitting review: {e}")
            return None
