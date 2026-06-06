"""Unit tests for src/shopping.py."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from shopping import format_quantity, scale_recipe, generate_shopping_list


# ──────────────────────────────────────────────
# format_quantity
# ──────────────────────────────────────────────


def test_format_integer_scale():
    assert format_quantity("500克", 2) == "1000克"


def test_format_float_scale():
    assert format_quantity("1.5汤匙", 2) == "3汤匙"


def test_format_half_scale():
    assert format_quantity("500克", 0.5) == "250克"


def test_format_half_scale_float_result():
    assert format_quantity("1.5汤匙", 0.5) == "0.75汤匙"


def test_format_no_number():
    assert format_quantity("适量", 3) == "适量"


def test_format_factor_one():
    assert format_quantity("500克", 1.0) == "500克"


def test_format_multiple_numbers_uses_first():
    # "2个约300g" → first number is "2"
    assert format_quantity("2个约300g", 3) == "6个约300g"


def test_format_zero_factor():
    result = format_quantity("500克", 0)
    assert result == "0克"


def test_format_empty_quantity():
    result = format_quantity("", 2)
    assert result == ""


# ──────────────────────────────────────────────
# scale_recipe
# ──────────────────────────────────────────────

SAMPLE_RECIPE = {
    "id": "001",
    "name": "番茄炒鸡蛋",
    "ingredients": [
        {"name": "番茄", "quantity": "2个"},
        {"name": "鸡蛋", "quantity": "3个"},
        {"name": "盐", "quantity": "适量"},
    ],
    "steps": ["打蛋", "炒番茄", "混合"],
    "prep_time": 5,
    "cook_time": 10,
}


def test_scale_recipe_doubled():
    scaled = scale_recipe(SAMPLE_RECIPE, 2.0)
    assert scaled["id"] == "001"
    assert scaled["ingredients"][0]["quantity"] == "4个"
    assert scaled["ingredients"][1]["quantity"] == "6个"
    assert scaled["ingredients"][2]["quantity"] == "适量"


def test_scale_recipe_original_unchanged():
    original_qty = SAMPLE_RECIPE["ingredients"][0]["quantity"]
    scale_recipe(SAMPLE_RECIPE, 3.0)
    assert SAMPLE_RECIPE["ingredients"][0]["quantity"] == original_qty


def test_scale_recipe_factor_one():
    scaled = scale_recipe(SAMPLE_RECIPE, 1.0)
    assert scaled["ingredients"][0]["quantity"] == "2个"


def test_scale_recipe_no_ingredients():
    recipe = {"id": "002", "name": "纯水"}
    scaled = scale_recipe(recipe, 2.0)
    assert scaled["id"] == "002"
    assert scaled.get("ingredients") is None or scaled.get("ingredients") == []


def test_scale_recipe_ingredient_no_quantity():
    recipe = {
        "id": "003",
        "name": "test",
        "ingredients": [{"name": "番茄"}],
    }
    scaled = scale_recipe(recipe, 2.0)
    assert "quantity" not in scaled["ingredients"][0]


# ──────────────────────────────────────────────
# generate_shopping_list
# ──────────────────────────────────────────────


def test_shopping_all_have():
    shopping = generate_shopping_list(
        {
            "ingredients": [
                {"name": "番茄", "quantity": "2个"},
                {"name": "鸡蛋", "quantity": "3个"},
            ]
        },
        ["番茄", "鸡蛋"],
        {},
    )
    assert shopping == []


def test_shopping_missing_main():
    shopping = generate_shopping_list(
        {
            "ingredients": [
                {"name": "番茄", "quantity": "2个"},
                {"name": "鸡蛋", "quantity": "3个"},
            ]
        },
        ["番茄"],
        {},
    )
    assert len(shopping) == 1
    assert shopping[0]["name"] == "鸡蛋"
    assert shopping[0]["quantity"] == "3个"
    assert shopping[0]["is_seasoning"] is False


def test_shopping_missing_seasoning_included():
    shopping = generate_shopping_list(
        {"ingredients": [{"name": "盐", "quantity": "适量"}]},
        [],
        {},
        include_seasonings=True,
    )
    assert len(shopping) == 1
    assert shopping[0]["name"] == "盐"
    assert shopping[0]["is_seasoning"] is True


def test_shopping_missing_seasoning_excluded():
    shopping = generate_shopping_list(
        {"ingredients": [{"name": "盐", "quantity": "适量"}]},
        [],
        {},
        include_seasonings=False,
    )
    assert shopping == []


def test_shopping_empty_recipe():
    shopping = generate_shopping_list(
        {"ingredients": []},
        ["番茄"],
        {},
    )
    assert shopping == []


def test_shopping_no_ingredients_key():
    shopping = generate_shopping_list(
        {},
        ["番茄"],
        {},
    )
    assert shopping == []


def test_shopping_synonym_match():
    synonyms = {"番茄": ["西红柿"]}
    shopping = generate_shopping_list(
        {"ingredients": [{"name": "西红柿", "quantity": "2个"}]},
        ["番茄"],
        synonyms,
    )
    assert shopping == []


def test_shopping_synonym_no_match():
    synonyms = {"番茄": ["西红柿"]}
    shopping = generate_shopping_list(
        {"ingredients": [{"name": "西红柿", "quantity": "2个"}]},
        ["鸡蛋"],
        synonyms,
    )
    assert len(shopping) == 1
    assert shopping[0]["name"] == "西红柿"
    assert shopping[0]["is_seasoning"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
