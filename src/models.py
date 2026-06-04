from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Recipe:
    id: str
    name: str
    ingredients: List[str]
    steps: List[str]
    prep_time: int
    cook_time: int
    cuisine: str
    dietary_tags: List[str]
    nutrition: Dict[str, float]
    rating: float
    ratings_count: int
    is_favorite: bool