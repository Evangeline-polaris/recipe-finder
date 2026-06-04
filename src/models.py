from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Recipe:
    id: str
    name: str
    ingredients: List[Dict[str, str]]
    steps: List[str]
    prep_time: int
    cook_time: int
    cuisine: str
    dietary_tags: List[str]
    nutrition: Dict[str, float]
    rating: float
    ratings_count: int
    is_favorite: bool

    @classmethod
    def from_dict(cls, data: dict) -> "Recipe":
        return cls(
            id=data["id"],
            name=data["name"],
            ingredients=data["ingredients"],
            steps=data["steps"],
            prep_time=data["prep_time"],
            cook_time=data["cook_time"],
            cuisine=data["cuisine"],
            dietary_tags=data["dietary_tags"],
            nutrition=data["nutrition"],
            rating=data["rating"],
            ratings_count=data["ratings_count"],
            is_favorite=data["is_favorite"],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "ingredients": self.ingredients,
            "steps": self.steps,
            "prep_time": self.prep_time,
            "cook_time": self.cook_time,
            "cuisine": self.cuisine,
            "dietary_tags": self.dietary_tags,
            "nutrition": self.nutrition,
            "rating": self.rating,
            "ratings_count": self.ratings_count,
            "is_favorite": self.is_favorite,
        }