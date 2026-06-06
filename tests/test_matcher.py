"""Unit tests for src/matcher.py."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from matcher import (
    is_seasoning,
    normalize_ingredient_name,
    normalize_ingredients_list,
    get_missing_seasonings,
    get_missing_main_ingredients,
    weighted_match,
    SEASONINGS,
)


# ──────────────────────────────────────────────
# is_seasoning
# ──────────────────────────────────────────────


def test_is_seasoning_true():
    assert is_seasoning("盐") is True
    assert is_seasoning("酱油") is True
    assert is_seasoning("葱") is True
    assert is_seasoning("白糖") is True


def test_is_seasoning_false():
    assert is_seasoning("鸡胸肉") is False
    assert is_seasoning("番茄") is False
    assert is_seasoning("牛肉") is False


def test_is_seasoning_not_in_set():
    assert is_seasoning("不存在的调料xyz") is False


# ──────────────────────────────────────────────
# normalize_ingredient_name
# ──────────────────────────────────────────────


def test_normalize_exact_standard():
    names = normalize_ingredient_name("番茄", {"番茄": ["西红柿", "tomato"]})
    assert names == "番茄"


def test_normalize_variant_to_standard():
    names = normalize_ingredient_name("西红柿", {"番茄": ["西红柿", "tomato"]})
    assert names == "番茄"


def test_normalize_case_insensitive():
    names = normalize_ingredient_name("TOMATO", {"番茄": ["西红柿", "tomato"]})
    assert names == "番茄"


def test_normalize_standard_case_insensitive():
    names = normalize_ingredient_name("番 茄".replace(" ", ""), {"番茄": ["西红柿"]})
    # Just verifying standard itself is handled
    names = normalize_ingredient_name("番茄", {"番茄": ["西红柿"]})
    assert names == "番茄"


def test_normalize_no_match():
    names = normalize_ingredient_name("未知食材xyz", {"番茄": ["西红柿"]})
    assert names == "未知食材xyz"


def test_normalize_empty_dict():
    names = normalize_ingredient_name("番茄", {})
    assert names == "番茄"


# ──────────────────────────────────────────────
# normalize_ingredients_list
# ──────────────────────────────────────────────


def test_normalize_list_empty():
    result = normalize_ingredients_list([], {"番茄": ["西红柿"]})
    assert result == []


def test_normalize_list_single():
    result = normalize_ingredients_list(["西红柿"], {"番茄": ["西红柿"]})
    assert result == ["番茄"]


def test_normalize_list_multiple():
    result = normalize_ingredients_list(
        ["西红柿", "鸡胸肉", "青椒"], {"番茄": ["西红柿"], "灯笼椒": ["青椒"]}
    )
    assert result == ["番茄", "鸡胸肉", "灯笼椒"]


# ──────────────────────────────────────────────
# get_missing_seasonings
# ──────────────────────────────────────────────


def test_seasonings_all_present():
    missing = get_missing_seasonings(
        ["盐", "酱油", "葱"],
        [{"name": "盐"}, {"name": "酱油"}, {"name": "葱"}],
        {},
    )
    assert missing == []


def test_seasonings_partial_missing():
    missing = get_missing_seasonings(
        ["盐"],
        [{"name": "盐"}, {"name": "酱油"}, {"name": "葱"}],
        {},
    )
    assert set(missing) == {"酱油", "葱"}
    assert len(missing) == 2


def test_seasonings_recipe_has_none():
    missing = get_missing_seasonings(
        ["盐"],
        [{"name": "番茄"}, {"name": "鸡蛋"}],
        {},
    )
    assert missing == []


def test_seasonings_empty_recipe():
    missing = get_missing_seasonings(["盐"], [], {})
    assert missing == []


def test_seasonings_user_empty():
    missing = get_missing_seasonings(
        [],
        [{"name": "盐"}, {"name": "酱油"}],
        {},
    )
    assert "盐" in missing
    assert "酱油" in missing


def test_seasonings_with_synonym_normalization():
    synonyms = {"番茄": ["西红柿"]}
    missing = get_missing_seasonings(
        ["盐"],
        [{"name": "盐"}, {"name": "酱油"}],
        synonyms,
    )
    assert "酱油" in missing


# ──────────────────────────────────────────────
# get_missing_main_ingredients
# ──────────────────────────────────────────────


def test_main_all_present():
    missing = get_missing_main_ingredients(
        ["番茄", "鸡蛋"],
        [{"name": "番茄"}, {"name": "鸡蛋"}],
        {},
    )
    assert missing == []


def test_main_partial_missing():
    missing = get_missing_main_ingredients(
        ["番茄"],
        [{"name": "番茄"}, {"name": "鸡蛋"}, {"name": "猪肉"}],
        {},
    )
    assert set(missing) == {"鸡蛋", "猪肉"}
    assert len(missing) == 2


def test_main_skips_seasonings():
    missing = get_missing_main_ingredients(
        ["番茄"],
        [{"name": "番茄"}, {"name": "盐"}, {"name": "酱油"}],
        {},
    )
    assert missing == []


def test_main_all_seasonings():
    missing = get_missing_main_ingredients(
        [],
        [{"name": "盐"}, {"name": "酱油"}],
        {},
    )
    assert missing == []


def test_main_empty_recipe():
    missing = get_missing_main_ingredients(["番茄"], [], {})
    assert missing == []


# ──────────────────────────────────────────────
# weighted_match
# ──────────────────────────────────────────────


def test_weighted_full_match():
    ratio, missing_main, missing_seasonings, subs = weighted_match(
        ["番茄", "鸡蛋"],
        [{"name": "番茄"}, {"name": "鸡蛋"}],
        {},
        {},
        allow_substitution=False,
    )
    assert ratio == 1.0
    assert missing_main == []
    assert subs == {}


def test_weighted_partial_one_missing():
    ratio, missing_main, _, _ = weighted_match(
        ["番茄"],
        [{"name": "番茄"}, {"name": "鸡蛋"}],
        {},
        {},
        allow_substitution=False,
    )
    assert ratio == 0.5
    assert missing_main == ["鸡蛋"]


def test_weighted_no_common_main():
    ratio, missing_main, _, _ = weighted_match(
        ["胡萝卜"],
        [{"name": "番茄"}, {"name": "鸡蛋"}],
        {},
        {},
        allow_substitution=False,
    )
    assert ratio == 0.0
    assert sorted(missing_main) == ["番茄", "鸡蛋"]


def test_weighted_empty_recipe():
    ratio, missing_main, missing_seasonings, subs = weighted_match(
        ["番茄", "鸡蛋"],
        [],
        {},
        {},
    )
    assert ratio == 0.0
    assert missing_main == []
    assert subs == {}


def test_weighted_only_seasonings_in_recipe():
    ratio, missing_main, missing_seasonings, subs = weighted_match(
        ["盐"],
        [{"name": "盐"}, {"name": "酱油"}],
        {},
        {},
    )
    # All are seasonings → denominator = 0 → ratio = 1.0
    assert ratio == 1.0
    assert missing_main == []
    assert missing_seasonings == ["酱油"]


def test_weighted_substitution_applied():
    substitutions = {"五花肉": ["猪肉"]}
    ratio, missing_main, _, subs = weighted_match(
        ["猪肉", "青椒"],
        [{"name": "五花肉"}, {"name": "青椒"}],
        {},
        substitutions,
        allow_substitution=True,
    )
    assert ratio == 0.9  # 1.0 + 0.8 / 2
    assert missing_main == []
    assert subs == {"五花肉": "猪肉"}


def test_weighted_substitution_disabled():
    substitutions = {"五花肉": ["猪肉"]}
    ratio, missing_main, _, subs = weighted_match(
        ["猪肉", "青椒"],
        [{"name": "五花肉"}, {"name": "青椒"}],
        {},
        substitutions,
        allow_substitution=False,
    )
    assert ratio == 0.5  # only 青椒 matched
    assert missing_main == ["五花肉"]
    assert subs == {}


def test_weighted_substitution_no_candidate_in_user():
    substitutions = {"五花肉": ["猪肉"]}
    ratio, missing_main, _, subs = weighted_match(
        ["牛肉", "青椒"],
        [{"name": "五花肉"}, {"name": "青椒"}],
        {},
        substitutions,
        allow_substitution=True,
    )
    assert ratio == 0.5  # only 青椒 matched
    assert missing_main == ["五花肉"]
    assert subs == {}


def test_weighted_substitution_no_entry():
    ratio, missing_main, _, subs = weighted_match(
        ["牛肉"],
        [{"name": "五花肉"}],
        {},
        {},
        allow_substitution=True,
    )
    assert ratio == 0.0
    assert missing_main == ["五花肉"]
    assert subs == {}


def test_weighted_missing_seasonings_returned():
    ratio, missing_main, missing_seasonings, _ = weighted_match(
        ["番茄", "鸡蛋"],
        [{"name": "番茄"}, {"name": "鸡蛋"}, {"name": "盐"}, {"name": "酱油"}],
        {},
        {},
    )
    assert ratio == 1.0
    assert missing_main == []
    assert "盐" in missing_seasonings
    assert "酱油" in missing_seasonings


def test_weighted_synonym_normalization_in_recipe():
    synonyms = {"番茄": ["西红柿"]}
    ratio, missing_main, _, _ = weighted_match(
        ["番茄"],
        [{"name": "西红柿"}, {"name": "鸡蛋"}],
        synonyms,
        {},
    )
    assert ratio == 0.5
    assert missing_main == ["鸡蛋"]


def test_substitution_candidate_normalized_via_synonym():
    synonyms = {"五花肉": ["pork belly"]}
    substitutions = {"五花肉": ["pork belly"]}
    ratio, missing_main, _, subs = weighted_match(
        ["pork belly"],
        [{"name": "五花肉"}],
        synonyms,
        substitutions,
        allow_substitution=True,
    )
    assert ratio == 0.8
    assert missing_main == []
    assert subs == {"五花肉": "pork belly"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
