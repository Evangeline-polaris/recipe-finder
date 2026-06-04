import json
import os
from typing import Dict, List, Set, Tuple


SEASONINGS: Set[str] = {
    "盐", "糖", "白糖", "冰糖", "油", "食用油", "味精", "鸡精",
    "酱油", "生抽", "老抽", "醋", "白醋", "料酒", "胡椒粉",
    "花椒", "花椒粉", "八角", "桂皮", "香叶", "葱", "姜", "蒜",
    "辣椒", "干辣椒", "淀粉", "水淀粉", "水",
}


def load_synonyms(filepath: str = "data/synonyms.json") -> Dict[str, List[str]]:
    """Load the synonym mapping from a JSON file.

    The JSON file should map standard ingredient names to lists of synonyms.
    Example: {"番茄": ["西红柿", "圣女果"]}

    Args:
        filepath: Path to the synonyms JSON file.

    Returns:
        A dictionary mapping standard names to lists of synonyms.
        Returns an empty dict if the file does not exist.
    """
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_ingredient_name(name: str, synonyms: Dict[str, List[str]]) -> str:
    """Normalize a single ingredient name to its standard form.

    If the given name matches a synonym (a value in the synonyms dict),
    return the corresponding standard name (key).
    Otherwise, return the original name unchanged.
    Matching is case-insensitive (lowercase comparison), but the returned
    value preserves the standard name's original casing.

    Args:
        name: The ingredient name to normalize.
        synonyms: A dict mapping standard names to lists of synonym strings.

    Returns:
        The normalized ingredient name, or the original name if no match.
    """
    name_lower = name.lower()
    for standard, variants in synonyms.items():
        for variant in variants:
            if variant.lower() == name_lower:
                return standard
        if standard.lower() == name_lower:
            return standard
    return name


def normalize_ingredients_list(
    ingredients: List[str], synonyms: Dict[str, List[str]]
) -> List[str]:
    """Normalize a list of ingredient names.

    Applies normalize_ingredient_name to each element.

    Args:
        ingredients: List of ingredient name strings.
        synonyms: A dict mapping standard names to lists of synonym strings.

    Returns:
        A list of normalized ingredient names.
    """
    return [normalize_ingredient_name(name, synonyms) for name in ingredients]


def _is_seasoning(name: str) -> bool:
    """Check if a normalized ingredient name is a seasoning.

    Args:
        name: The (already normalized) ingredient name.

    Returns:
        True if the name is in the SEASONINGS set.
    """
    return name in SEASONINGS


def get_missing_seasonings(
    user_ingredients: List[str],
    recipe_ingredients: List[Dict[str, str]],
    synonyms: Dict[str, List[str]],
) -> List[str]:
    """Return the seasonings that a recipe requires but the user lacks.

    Normalizes both user and recipe ingredient names, then finds recipe
    seasonings that are not present in the user's ingredient list.

    Args:
        user_ingredients: List of ingredient name strings the user has.
        recipe_ingredients: List of dicts, each with a "name" key.
        synonyms: A dict mapping standard names to lists of synonym strings.

    Returns:
        A list of normalized seasoning names the user is missing,
        sorted alphabetically.
    """
    user_normalized = set(normalize_ingredients_list(user_ingredients, synonyms))
    recipe_names = [item["name"] for item in recipe_ingredients]
    recipe_normalized = normalize_ingredients_list(recipe_names, synonyms)

    recipe_seasonings = {n for n in recipe_normalized if _is_seasoning(n)}
    missing = sorted(recipe_seasonings - user_normalized)
    return missing


def get_missing_main_ingredients(
    user_ingredients: List[str],
    recipe_ingredients: List[Dict[str, str]],
    synonyms: Dict[str, List[str]],
) -> List[str]:
    """Return the non-seasoning ingredients that a recipe requires but the user lacks.

    Args:
        user_ingredients: List of ingredient name strings the user has.
        recipe_ingredients: List of dicts, each with a "name" key.
        synonyms: A dict mapping standard names to lists of synonym strings.

    Returns:
        A list of normalized main ingredient names the user is missing,
        sorted alphabetically.
    """
    user_normalized = set(normalize_ingredients_list(user_ingredients, synonyms))
    recipe_names = [item["name"] for item in recipe_ingredients]
    recipe_normalized = normalize_ingredients_list(recipe_names, synonyms)

    recipe_main = {n for n in recipe_normalized if not _is_seasoning(n)}
    missing = sorted(recipe_main - user_normalized)
    return missing


def exact_match(
    user_ingredients: List[str],
    recipe_ingredients: List[Dict[str, str]],
    synonyms: Dict[str, List[str]],
    ignore_seasonings: bool = True,
) -> bool:
    """Check if user ingredients fully cover all recipe ingredients.

    Normalizes both the user's ingredients and the recipe's ingredient names,
    then checks if the user set contains every recipe ingredient (ignoring
    quantities). When ignore_seasonings is True, seasoning ingredients are
    excluded from the comparison.

    Args:
        user_ingredients: List of ingredient name strings the user has.
        recipe_ingredients: List of dicts, each with a "name" key.
        synonyms: A dict mapping standard names to lists of synonym strings.
        ignore_seasonings: If True, exclude SEASONINGS from both sets.

    Returns:
        True if all (non-seasoning) recipe ingredients are present.
    """
    user_normalized = set(normalize_ingredients_list(user_ingredients, synonyms))
    recipe_names = [item["name"] for item in recipe_ingredients]
    recipe_normalized = set(normalize_ingredients_list(recipe_names, synonyms))

    if ignore_seasonings:
        user_normalized = {n for n in user_normalized if not _is_seasoning(n)}
        recipe_normalized = {n for n in recipe_normalized if not _is_seasoning(n)}

    return recipe_normalized.issubset(user_normalized)


def partial_match(
    user_ingredients: List[str],
    recipe_ingredients: List[Dict[str, str]],
    synonyms: Dict[str, List[str]],
    ignore_seasonings: bool = True,
) -> Tuple[float, List[str], List[str]]:
    """Calculate the match ratio and list missing ingredients.

    Normalizes both the user's ingredients and the recipe's ingredient names,
    then computes the ratio: (number of matched recipe main ingredients) /
    (total number of recipe main ingredients). Seasonings are excluded from
    the ratio calculation but reported separately alongside missing main
    ingredients.

    Args:
        user_ingredients: List of ingredient name strings the user has.
        recipe_ingredients: List of dicts, each with a "name" key.
        synonyms: A dict mapping standard names to lists of synonym strings.
        ignore_seasonings: If True, exclude SEASONINGS from the match ratio.

    Returns:
        A tuple of (match_ratio, missing_main_ingredients, missing_seasonings):
        - match_ratio: A float from 0.0 to 1.0.
        - missing_main_ingredients: List of main ingredient names the user lacks.
        - missing_seasonings: List of seasoning names the user lacks.
    """
    missing_main = get_missing_main_ingredients(
        user_ingredients, recipe_ingredients, synonyms
    )
    missing_seasonings = get_missing_seasonings(
        user_ingredients, recipe_ingredients, synonyms
    )

    if not recipe_ingredients:
        return 0.0, missing_main, missing_seasonings

    user_normalized = set(normalize_ingredients_list(user_ingredients, synonyms))
    recipe_names = [item["name"] for item in recipe_ingredients]
    recipe_normalized = set(normalize_ingredients_list(recipe_names, synonyms))

    if ignore_seasonings:
        recipe_normalized = {n for n in recipe_normalized if not _is_seasoning(n)}

    if not recipe_normalized:
        return 1.0, missing_main, missing_seasonings

    matched = recipe_normalized & user_normalized
    ratio = len(matched) / len(recipe_normalized)
    return ratio, missing_main, missing_seasonings
