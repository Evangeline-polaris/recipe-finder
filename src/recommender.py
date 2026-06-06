import copy
from typing import Dict, List

from matcher import (
    is_seasoning,
    normalize_ingredient_name,
    normalize_ingredients_list,
    weighted_match,
)


def get_required_main_ingredients(recipe, synonyms: Dict[str, List[str]]) -> List[str]:
    """Return the normalized names of all main (non-seasoning) ingredients
    required by a recipe.

    Args:
        recipe: A Recipe object (or dict with an "ingredients" key containing
                a list of dicts with "name").
        synonyms: Synonym mapping for normalizing ingredient names.

    Returns:
        A deduplicated list of normalized main ingredient names that are not
        seasonings.
    """
    ingredients = (
        recipe.ingredients if hasattr(recipe, "ingredients") else recipe["ingredients"]
    )
    recipe_names = [item["name"] for item in ingredients]
    normalized = normalize_ingredients_list(recipe_names, synonyms)
    main_ingredients = [name for name in normalized if not is_seasoning(name)]
    # Deduplicate while preserving order
    seen: set = set()
    result: List[str] = []
    for name in main_ingredients:
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


def weekly_plan(
    user_ingredients: List[str],
    recipes: list,
    substitutions: Dict[str, List[str]],
    allow_substitution: bool,
    num_days: int = 3,
) -> List[Dict]:
    """Recommend a weekly meal plan using a greedy algorithm.

    For each day, the recipe with the highest weighted_match ratio against the
    current virtual pantry is selected.  After selection, the recipe's missing
    main ingredients are added to the virtual pantry (simulating "purchasing"
    them) so that subsequent recommendations benefit from the expanded set.

    Args:
        user_ingredients: Already-normalized list of ingredient names.
        recipes: List of Recipe objects (or dicts with "ingredients").
        substitutions: Substitution rules map for weighted_match.
        allow_substitution: Whether to apply ingredient substitution.
        num_days: Number of recipes to recommend (default 3).

    Returns:
        A list of plan detail dicts, each containing:
        - ``recipe``: the matched recipe dict/object
        - ``score``: match ratio (0.0–1.0)
        - ``missing_main``: list of missing main ingredient names
        - ``missing_seasonings``: list of missing seasoning names
        - ``sub_items``: dict mapping recipe ingredient → user ingredient
          for substitutions

        The list may be shorter than num_days if no more recipes can be
        matched.
    """
    # Work on a mutable copy of the user's ingredients
    virtual_pantry: List[str] = list(user_ingredients)
    remaining = list(recipes)
    plan: List[Dict] = []

    from matcher import load_synonyms

    synonyms: Dict[str, List[str]] = load_synonyms()

    for _ in range(num_days):
        if not remaining:
            break

        best_recipe = None
        best_score = -1.0
        best_missing_main: List[str] = []
        best_missing_seasonings: List[str] = []
        best_sub_items: Dict[str, str] = {}

        for recipe in remaining:
            # Extract ingredient list (handle both Recipe objects and dicts)
            recipe_ingredients = (
                recipe.ingredients
                if hasattr(recipe, "ingredients")
                else recipe["ingredients"]
            )
            score, missing_main, missing_seasonings, sub_items = weighted_match(
                user_ingredients=virtual_pantry,
                recipe_ingredients=recipe_ingredients,
                synonyms=synonyms,
                substitutions=substitutions,
                allow_substitution=allow_substitution,
            )
            if score > best_score:
                best_score = score
                best_recipe = recipe
                best_missing_main = missing_main
                best_missing_seasonings = missing_seasonings
                best_sub_items = sub_items

        # Stop early if no recipe has a positive match
        if best_recipe is None or best_score <= 0.0:
            break

        plan.append(
            {
                "recipe": best_recipe,
                "score": best_score,
                "missing_main": best_missing_main,
                "missing_seasonings": best_missing_seasonings,
                "sub_items": best_sub_items,
            }
        )
        remaining.remove(best_recipe)

        # Simulate buying: add the recipe's main ingredients to the virtual pantry
        required_main = get_required_main_ingredients(best_recipe, synonyms)
        pantry_set = set(virtual_pantry)
        for name in required_main:
            if name not in pantry_set:
                virtual_pantry.append(name)
                pantry_set.add(name)

    return plan
