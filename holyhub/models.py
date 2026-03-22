## models.py

from typing import List, Dict, Any, Optional

class Church:
    """
    Represents a Church entity with attributes to store relevant information.
    """
    def __init__(self, church_id: int, name: str, address: str, city: str, state: str, zip_code: str, latitude: float, longitude: float):
        self.church_id = church_id
        self.name = name
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.latitude = latitude
        self.longitude = longitude

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Church object into a dictionary.
        """
        return {
            "church_id": self.church_id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "latitude": self.latitude,
            "longitude": self.longitude
        }

class Review:
    """
    Represents a Review entity with attributes to store relevant information.
    
    Attributes:
        review_id (int): Unique identifier for the review
        church_id (int): ID of the church being reviewed
        user_id (int): ID of the user who wrote the review
        username (str): Username of the reviewer
        rating (float): Rating value between 1 and 5
        comment (str): Review text content
        timestamp (str): When the review was created
    """
    
    def __init__(self,
                 review_id: int,
                 church_id: int,
                 rating: float,
                 comment: str,
                 timestamp: str,
                 worship_energy: Optional[float] = None,
                 community_warmth: Optional[float] = None,
                 sermon_depth: Optional[float] = None,
                 childrens_programs: Optional[float] = None,
                 theological_openness: Optional[float] = None,
                 facilities: Optional[float] = None):
        self.review_id = review_id
        self.church_id = church_id
        self.rating = self._validate_rating(rating)
        self.comment = comment
        self.timestamp = timestamp
        self.worship_energy = worship_energy
        self.community_warmth = community_warmth
        self.sermon_depth = sermon_depth
        self.childrens_programs = childrens_programs
        self.theological_openness = theological_openness
        self.facilities = facilities

    def _validate_rating(self, rating: float) -> float:
        """
        Validates that rating is between 1 and 5.
        
        Args:
            rating: The rating value to validate
            
        Returns:
            The validated rating value
            
        Raises:
            ValueError: If rating is outside valid range
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return rating

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Review object into a dictionary.
        
        Returns:
            Dictionary containing all review attributes
        """
        return {
            "review_id": self.review_id,
            "church_id": self.church_id,
            "user_id": self.user_id,
            "username": self.username,
            "rating": self.rating,
            "comment": self.comment,
            "timestamp": self.timestamp
        }

    @staticmethod
    def calculate_average(reviews: List['Review']) -> float:
        """
        Calculates the average rating from a list of reviews.
        
        Args:
            reviews: List of Review objects
            
        Returns:
            Average rating rounded to 1 decimal place
            
        Raises:
            ValueError: If reviews list is empty
        """
        if not reviews:
            raise ValueError("Cannot calculate average of empty reviews list")
            
        total = sum(review.rating for review in reviews)
        return round(total / len(reviews), 1)

class User:
    """
    Represents a User entity with attributes to store relevant information.
    """
    def __init__(self, 
                 user_id: int, 
                 username: str, 
                 email: str, 
                 password_hash: str,
                 created_at: Optional[str] = None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the User object into a dictionary.
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at
        }
