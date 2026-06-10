"""
FastAPI web server for the Recipe Finder application.

Provides a REST API and serves the SPA frontend.
"""

import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Ensure src/ is on path for imports from sibling modules
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from storage import (
    load_recipes,
    update_rating,
    toggle_favorite,
    get_favorites,
    export_favorites,
    import_favorites,
)
from matcher import (
    load_synonyms,
    load_substitutions,
    normalize_ingredients_list,
    weighted_match,
)
from filter_sort import (
    filter_by_max_time,
    filter_by_cuisine,
    filter_by_dietary,
    sort_recipes,
    get_cuisine_groups,
    get_all_cuisines,
)
from shopping import generate_shopping_list, scale_recipe
from recommender import weekly_plan
from display import parse_ingredients_input

# ────────────────────────────────────────────────────
# FastAPI application
# ────────────────────────────────────────────────────

app = FastAPI(
    title="智能食谱查找器 API",
    description="根据现有食材智能匹配菜谱的 REST API",
    version="2.0.0",
)

# Mount static files directory
_static_dir = os.path.join(_current_dir, "static")
os.makedirs(_static_dir, exist_ok=True)


# ────────────────────────────────────────────────────
# Pydantic request/response models
# ────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    ingredients: str  # comma-separated
    allow_substitution: bool = False
    max_time: Optional[int] = None
    cuisine_list: Optional[List[str]] = None
    dietary_list: Optional[List[str]] = None
    sort_by: str = "match"  # match | time | calories
    top_n: int = 10


class WeeklyPlanRequest(BaseModel):
    ingredients: str
    allow_substitution: bool = False
    num_days: int = 3


class RateRequest(BaseModel):
    recipe_id: str
    score: int  # 1-5


class FavoriteToggleRequest(BaseModel):
    recipe_id: str


class ExportRequest(BaseModel):
    filepath: Optional[str] = None


class ImportRequest(BaseModel):
    filepath: str


class ScaleRequest(BaseModel):
    recipe_id: str
    factor: float

    class Config:
        extra = "allow"


# ────────────────────────────────────────────────────
# API endpoints
# ────────────────────────────────────────────────────


@app.get("/")
async def root():
    """Serve the SPA frontend page."""
    index_path = os.path.join(_static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        {"message": "智能食谱查找器 API 已就绪。请访问 /docs 查看 API 文档。"}
    )


@app.get("/api/filters")
async def get_filters():
    """Return available filter options (cuisine groups, dietary tags)."""
    recipes = load_recipes()
    cuisine_groups = get_cuisine_groups(recipes)
    all_cuisines = sorted(get_all_cuisines(recipes))

    tags: set = set()
    for r in recipes:
        for tag in r.get("dietary_tags", []):
            tags.add(tag.strip())

    # Preferred order
    TAG_ORDER = [
        "荤菜", "素食", "纯素食", "低卡", "低碳水", "快手", "无麸质", "高蛋白"
    ]
    sorted_tags = [t for t in TAG_ORDER if t in tags]
    for t in sorted(tags):
        if t not in sorted_tags:
            sorted_tags.append(t)

    return {
        "cuisine_groups": {
            region: sorted(cuisines)
            for region, cuisines in cuisine_groups.items()
        },
        "all_cuisines": all_cuisines,
        "dietary_tags": sorted_tags,
    }


@app.post("/api/search")
async def search_recipes(req: SearchRequest):
    """Search recipes by ingredients with optional filters and sorting."""
    ingredients_list = parse_ingredients_input(req.ingredients)
    if not ingredients_list:
        raise HTTPException(status_code=400, detail="食材列表不能为空")

    recipes = load_recipes()
    synonyms = load_synonyms()
    substitutions = load_substitutions()

    user_normalized = normalize_ingredients_list(ingredients_list, synonyms)

    # ── Matching ──
    all_results: List[Dict[str, Any]] = []
    for recipe in recipes:
        ratio, missing_main, missing_seasonings, sub_items = weighted_match(
            user_normalized,
            recipe["ingredients"],
            synonyms,
            substitutions,
            allow_substitution=req.allow_substitution,
        )
        if ratio > 0:
            all_results.append(
                {
                    "recipe": recipe,
                    "match_ratio": ratio,
                    "missing_main": missing_main,
                    "missing_seasonings": missing_seasonings,
                    "sub_items": sub_items,
                }
            )

    if not all_results:
        return {
            "results": [],
            "total_count": 0,
            "user_normalized": user_normalized,
        }

    match_percents = {r["recipe"]["id"]: r["match_ratio"] for r in all_results}
    filtered = [r["recipe"] for r in all_results]

    # ── Filtering ──
    if req.max_time is not None and req.max_time > 0:
        filtered = filter_by_max_time(filtered, req.max_time)
    if req.cuisine_list:
        filtered = filter_by_cuisine(filtered, req.cuisine_list)
    if req.dietary_list:
        filtered = filter_by_dietary(filtered, req.dietary_list)

    if not filtered:
        return {
            "results": [],
            "total_count": 0,
            "user_normalized": user_normalized,
        }

    # ── Sorting ──
    if req.sort_by == "time":
        filtered = sort_recipes(filtered, "total_time", reverse=False)
    elif req.sort_by == "calories":
        filtered = sort_recipes(filtered, "calories", reverse=False)
    else:
        filtered = sort_recipes(
            filtered, "match_percent", reverse=True, match_percents=match_percents
        )

    total_count = len(filtered)
    filtered = filtered[: req.top_n]

    # ── Build result dicts ──
    results: List[Dict[str, Any]] = []
    for recipe in filtered:
        info = next(
            (r for r in all_results if r["recipe"]["id"] == recipe["id"]),
            None,
        )
        if info:
            results.append(info)
        else:
            results.append(
                {
                    "recipe": recipe,
                    "match_ratio": match_percents.get(recipe["id"], 0.0),
                    "missing_main": [],
                    "missing_seasonings": [],
                    "sub_items": {},
                }
            )

    return {
        "results": results,
        "total_count": total_count,
        "user_normalized": user_normalized,
    }


@app.post("/api/weekly-plan")
async def get_weekly_plan(req: WeeklyPlanRequest):
    """Generate a weekly meal plan based on available ingredients."""
    ingredients_list = parse_ingredients_input(req.ingredients)
    if not ingredients_list:
        raise HTTPException(status_code=400, detail="食材列表不能为空")

    recipes = load_recipes()
    synonyms = load_synonyms()
    substitutions = load_substitutions()
    user_normalized = normalize_ingredients_list(ingredients_list, synonyms)

    plan_details = weekly_plan(
        user_ingredients=user_normalized,
        recipes=recipes,
        substitutions=substitutions,
        allow_substitution=req.allow_substitution,
        num_days=req.num_days,
    )

    if not plan_details:
        return {"plan": []}

    # Serialize plan details
    plan = []
    for detail in plan_details:
        recipe = detail["recipe"]
        if not isinstance(recipe, dict):
            recipe = recipe.to_dict() if hasattr(recipe, "to_dict") else dict(recipe)
        plan.append(
            {
                "recipe": recipe,
                "score": float(detail["score"]),
                "missing_main": detail.get("missing_main", []),
                "missing_seasonings": detail.get("missing_seasonings", []),
                "sub_items": detail.get("sub_items", {}),
            }
        )

    return {"plan": plan, "user_normalized": user_normalized}


@app.get("/api/recipes")
async def list_recipes():
    """Return all recipes (for rating and favorites management)."""
    recipes = load_recipes()
    # Return lightweight list (name, id, rating, cuisine, is_favorite)
    light = []
    for r in recipes:
        light.append(
            {
                "id": r["id"],
                "name": r["name"],
                "cuisine": r.get("cuisine", ""),
                "rating": r.get("rating", 0.0),
                "ratings_count": r.get("ratings_count", 0),
                "is_favorite": r.get("is_favorite", False),
                "calories": r.get("nutrition", {}).get("calories", 0),
                "total_time": r.get("prep_time", 0) + r.get("cook_time", 0),
            }
        )
    return {"recipes": light}


@app.get("/api/recipes/{recipe_id}")
async def get_recipe_detail(recipe_id: str):
    """Return full detail of a single recipe."""
    recipes = load_recipes()
    for r in recipes:
        if r["id"] == recipe_id:
            return {"recipe": r}
    raise HTTPException(status_code=404, detail="菜谱未找到")


@app.post("/api/rate")
async def rate_recipe(req: RateRequest):
    """Rate a recipe (1-5 stars)."""
    if not 1 <= req.score <= 5:
        raise HTTPException(status_code=400, detail="评分必须是 1~5 的整数")
    success = update_rating(req.recipe_id, req.score)
    if not success:
        raise HTTPException(status_code=400, detail="评分失败")
    return {"success": True}


@app.post("/api/favorites/toggle")
async def toggle_fav(req: FavoriteToggleRequest):
    """Toggle a recipe's favorite status."""
    toggle_favorite(req.recipe_id)
    return {"success": True}


@app.get("/api/favorites")
async def list_favorites():
    """Return the user's favorites list."""
    favorites = get_favorites()
    light = []
    for r in favorites:
        light.append(
            {
                "id": r["id"],
                "name": r["name"],
                "cuisine": r.get("cuisine", ""),
                "rating": r.get("rating", 0.0),
                "calories": r.get("nutrition", {}).get("calories", 0),
                "total_time": r.get("prep_time", 0) + r.get("cook_time", 0),
            }
        )
    return {"favorites": light}


@app.post("/api/favorites/export")
async def export_fav(req: ExportRequest = None):
    """Export favorites to a JSON file."""
    if req and req.filepath:
        count = export_favorites(req.filepath)
    else:
        count = export_favorites()
    return {"count": count, "filepath": req.filepath if req else "data/favorites.json"}


@app.post("/api/favorites/import")
async def import_fav(req: ImportRequest):
    """Import favorites from a JSON file."""
    count = import_favorites(req.filepath)
    if count <= 0:
        raise HTTPException(status_code=400, detail="导入失败：文件不存在或所有菜谱已收藏")
    return {"count": count}


@app.post("/api/shopping")
async def shopping_list(
    recipe_id: str = Query(..., description="Recipe ID"),
    ingredients: str = Query("", description="Comma-separated user ingredients"),
    include_seasonings: bool = Query(True),
):
    """Generate a shopping list for a recipe."""
    recipes = load_recipes()
    recipe = None
    for r in recipes:
        if r["id"] == recipe_id:
            recipe = r
            break
    if not recipe:
        raise HTTPException(status_code=404, detail="菜谱未找到")

    synonyms = load_synonyms()
    ingredients_list = parse_ingredients_input(ingredients) if ingredients else []
    user_normalized = normalize_ingredients_list(ingredients_list, synonyms)

    shopping = generate_shopping_list(
        recipe, user_normalized, synonyms, include_seasonings=include_seasonings
    )
    return {"shopping": shopping}


@app.post("/api/scale")
async def scale(req: ScaleRequest):
    """Scale a recipe by a given factor."""
    if req.factor <= 0:
        raise HTTPException(status_code=400, detail="缩放倍数必须大于 0")

    recipes = load_recipes()
    recipe = None
    for r in recipes:
        if r["id"] == req.recipe_id:
            recipe = r
            break
    if not recipe:
        raise HTTPException(status_code=404, detail="菜谱未找到")

    scaled = scale_recipe(recipe, req.factor)
    return {"scaled": scaled}


# ────────────────────────────────────────────────────
# Static files (must be after API routes)
# ────────────────────────────────────────────────────

@app.get("/{filename:path}")
async def serve_static(filename: str):
    """Serve static files (CSS, JS, images, etc.)."""
    file_path = os.path.join(_static_dir, filename)
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # Fallback: serve index.html for SPA routing
    index_path = os.path.join(_static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="文件未找到")