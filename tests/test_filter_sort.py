"""Unit tests for src/filter_sort.py."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from filter_sort import (
    filter_by_max_time,
    filter_by_cuisine,
    filter_by_dietary,
    sort_recipes,
    get_all_cuisines,
)


# ──────────────────────────────────────────────
# Test data
# ──────────────────────────────────────────────

SAMPLE_RECIPES = [
    {
        "id": "001",
        "name": "番茄炒鸡蛋",
        "prep_time": 5,
        "cook_time": 10,
        "cuisine": "中餐",
        "dietary_tags": ["素食", "无麸质"],
        "nutrition": {"calories": 180.0},
    },
    {
        "id": "002",
        "name": "意大利面",
        "prep_time": 10,
        "cook_time": 15,
        "cuisine": "意大利",
        "dietary_tags": ["素食"],
        "nutrition": {"calories": 350.0},
    },
    {
        "id": "003",
        "name": "宫保鸡丁",
        "prep_time": 15,
        "cook_time": 10,
        "cuisine": "川菜",
        "dietary_tags": ["无麸质"],
        "nutrition": {"calories": 280.0},
    },
    {
        "id": "004",
        "name": "牛排",
        "prep_time": 5,
        "cook_time": 20,
        "cuisine": "西餐",
        "dietary_tags": [],
        "nutrition": {"calories": 450.0},
    },
    {
        "id": "005",
        "name": "紫菜蛋花汤",
        "prep_time": 5,
        "cook_time": 5,
        "cuisine": "中餐",
        "dietary_tags": ["素食", "无麸质"],
        "nutrition": {"calories": 80.0},
    },
]


# ──────────────────────────────────────────────
# filter_by_max_time
# ──────────────────────────────────────────────


def test_filter_time_30():
    result = filter_by_max_time(SAMPLE_RECIPES, 30)
    ids = {r["id"] for r in result}
    assert "001" in ids  # 5+10=15 ≤ 30
    assert "002" in ids  # 10+15=25 ≤ 30
    assert "003" in ids  # 15+10=25 ≤ 30
    assert "004" in ids  # 5+20=25 ≤ 30
    assert "005" in ids  # 5+5=10 ≤ 30
    assert len(result) == 5  # all recipes ≤ 30


def test_filter_time_15():
    result = filter_by_max_time(SAMPLE_RECIPES, 15)
    ids = {r["id"] for r in result}
    assert "001" in ids  # 15
    assert "005" in ids  # 10
    assert "002" not in ids  # 25
    assert "003" not in ids  # 25


def test_filter_time_boundary():
    result = filter_by_max_time(SAMPLE_RECIPES, 10)
    ids = {r["id"] for r in result}
    assert "005" in ids  # 10 exactly


def test_filter_time_zero():
    result = filter_by_max_time(SAMPLE_RECIPES, 0)
    assert result == []


def test_filter_time_empty():
    result = filter_by_max_time([], 30)
    assert result == []


def test_filter_time_missing_fields():
    recipes = [{"id": "x", "name": "未知"}]
    result = filter_by_max_time(recipes, 30)
    assert len(result) == 1  # 0+0 = 0 ≤ 30


# ──────────────────────────────────────────────
# filter_by_cuisine
# ──────────────────────────────────────────────


def test_filter_cuisine_single():
    result = filter_by_cuisine(SAMPLE_RECIPES, ["中餐"])
    ids = {r["id"] for r in result}
    assert ids == {"001", "005"}


def test_filter_cuisine_multiple():
    result = filter_by_cuisine(SAMPLE_RECIPES, ["中餐", "意大利"])
    ids = {r["id"] for r in result}
    assert ids == {"001", "002", "005"}


def test_filter_cuisine_no_match():
    result = filter_by_cuisine(SAMPLE_RECIPES, ["法餐"])
    assert result == []


def test_filter_cuisine_empty_list():
    result = filter_by_cuisine([], ["中餐"])
    assert result == []


def test_filter_cuisine_empty_target():
    result = filter_by_cuisine(SAMPLE_RECIPES, [])
    assert result == []


def test_filter_cuisine_missing_field():
    recipes = [{"id": "x", "name": "未知"}]
    result = filter_by_cuisine(recipes, ["中餐"])
    assert result == []  # cuisine="", not in set


# ──────────────────────────────────────────────
# filter_by_dietary
# ──────────────────────────────────────────────


def test_filter_dietary_vegetarian():
    result = filter_by_dietary(SAMPLE_RECIPES, ["素食"])
    ids = {r["id"] for r in result}
    assert ids == {"001", "002", "005"}


def test_filter_dietary_gluten_free():
    result = filter_by_dietary(SAMPLE_RECIPES, ["无麸质"])
    ids = {r["id"] for r in result}
    assert ids == {"001", "003", "005"}


def test_filter_dietary_both_vegetarian_and_gluten_free():
    result = filter_by_dietary(SAMPLE_RECIPES, ["素食", "无麸质"])
    ids = {r["id"] for r in result}
    assert ids == {"001", "005"}


def test_filter_dietary_no_match():
    result = filter_by_dietary(SAMPLE_RECIPES, ["纯肉食"])
    assert result == []


def test_filter_dietary_empty_required():
    result = filter_by_dietary(SAMPLE_RECIPES, [])
    assert len(result) == len(SAMPLE_RECIPES)  # empty set is subset of everything


def test_filter_dietary_empty_list():
    result = filter_by_dietary([], ["素食"])
    assert result == []


def test_filter_dietary_missing_field():
    recipes = [{"id": "x", "name": "未知"}]
    result = filter_by_dietary(recipes, ["素食"])
    assert result == []


# ──────────────────────────────────────────────
# sort_recipes
# ──────────────────────────────────────────────


def test_sort_by_match_percent_descending():
    match = {"001": 0.5, "002": 0.9, "003": 0.2, "004": 0.7, "005": 0.1}
    result = sort_recipes(
        SAMPLE_RECIPES, "match_percent", reverse=True, match_percents=match
    )
    assert result[0]["id"] == "002"
    assert result[-1]["id"] == "005"


def test_sort_by_match_percent_ascending():
    match = {"001": 0.5, "002": 0.9, "003": 0.2, "004": 0.7, "005": 0.1}
    result = sort_recipes(
        SAMPLE_RECIPES, "match_percent", reverse=False, match_percents=match
    )
    assert result[0]["id"] == "005"
    assert result[-1]["id"] == "002"


def test_sort_by_match_requires_match_percents():
    with pytest.raises(ValueError, match="match_percents is required"):
        sort_recipes(SAMPLE_RECIPES, "match_percent")


def test_sort_by_total_time_ascending():
    result = sort_recipes(SAMPLE_RECIPES, "total_time", reverse=False)
    # 005: 10, 001: 15, 002: 25, 003: 25, 004: 25
    assert result[0]["id"] == "005"
    assert result[1]["id"] == "001"


def test_sort_by_total_time_descending():
    result = sort_recipes(SAMPLE_RECIPES, "total_time", reverse=True)
    total_004 = 25  # 5+20
    total_first = result[0].get("prep_time", 0) + result[0].get("cook_time", 0)
    assert total_first >= total_004


def test_sort_by_calories_ascending():
    result = sort_recipes(SAMPLE_RECIPES, "calories", reverse=False)
    ids = [r["id"] for r in result]
    assert ids[0] == "005"  # 80 cal
    assert ids[-1] == "004"  # 450 cal


def test_sort_by_calories_descending():
    result = sort_recipes(SAMPLE_RECIPES, "calories", reverse=True)
    ids = [r["id"] for r in result]
    assert ids[0] == "004"  # 450 cal
    assert ids[-1] == "005"  # 80 cal


def test_sort_invalid_key():
    with pytest.raises(ValueError, match="Invalid sort_key"):
        sort_recipes(SAMPLE_RECIPES, "nonexistent")


def test_sort_empty_list():
    result = sort_recipes([], "calories")
    assert result == []


def test_sort_missing_nutrition():
    recipes = [{"id": "x", "name": "未知"}]
    result = sort_recipes(recipes, "calories", reverse=False)
    assert len(result) == 1


def test_sort_match_percent_missing_id():
    match = {"001": 0.5}
    result = sort_recipes(
        SAMPLE_RECIPES, "match_percent", reverse=True, match_percents=match
    )
    # 001 first (0.5), rest have 0.0 default
    assert result[0]["id"] == "001"


# ──────────────────────────────────────────────
# get_all_cuisines
# ──────────────────────────────────────────────


def test_get_all_cuisines():
    cuisines = get_all_cuisines(SAMPLE_RECIPES)
    assert cuisines == sorted(["中餐", "意大利", "川菜", "西餐"])


def test_get_all_cuisines_empty():
    assert get_all_cuisines([]) == []


def test_get_all_cuisines_missing_field():
    recipes = [{"id": "x", "name": "未知"}]
    assert get_all_cuisines(recipes) == []


def test_get_all_cuisines_duplicate():
    recipes = [
        {"cuisine": "中餐"},
        {"cuisine": "中餐"},
        {"cuisine": "西餐"},
    ]
    assert get_all_cuisines(recipes) == ["中餐", "西餐"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
