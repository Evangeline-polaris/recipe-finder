"""Shared display and parsing utilities for recipe search results."""

from typing import Any, Dict, List


def parse_ingredients_input(raw: str) -> List[str]:
    """Split a comma-separated ingredient string into a cleaned list.

    Handles both half-width (,) and full-width (，) commas.
    """
    return [i.strip() for i in raw.replace("，", ",").split(",") if i.strip()]


def print_recipe_result(
    recipe: Dict[str, Any],
    info: Dict[str, Any],
    index: int,
) -> None:
    """Print a single recipe result line with match ratio and missing items.

    Args:
        recipe: The recipe dict.
        info: Match info dict with keys ``match_ratio``, ``missing_main``,
              ``missing_seasonings``, ``sub_items``.
        index: 1-based display index.
    """
    pct = f"{int(info['match_ratio'] * 100)}%"
    line = f"{index}. {recipe['name']} — {pct}"

    extras = []
    sub_items = info.get("sub_items", {})
    if sub_items:
        sub_strs = [f"{user_ing}→{rcp_ing}" for rcp_ing, user_ing in sub_items.items()]
        extras.append(f"替换: {'、'.join(sub_strs)}")

    parts = [line]
    if extras:
        parts.append(f" ({'; '.join(extras)})")
    print("".join(parts))

    missing_main = info.get("missing_main", [])
    missing_seasonings = info.get("missing_seasonings", [])
    if missing_main:
        print(f"    还需主料：{'、'.join(missing_main)}")
    if missing_seasonings:
        print(f"    还需调料: {'、'.join(missing_seasonings)}")

    total_time = recipe.get("prep_time", 0) + recipe.get("cook_time", 0)
    calories = recipe.get("nutrition", {}).get("calories", 0)
    print(f"    总耗时: {total_time} 分钟 | 热量: {calories:.0f} kcal")


def print_results_summary(
    results: List[Dict[str, Any]],
    total_count: int,
    top_n: int,
) -> None:
    """Print a summary line for search results.

    If the total number of available results exceeds *top_n*, prints a
    message indicating how many were found and how many are being shown.
    Otherwise simply prints the total count.

    Args:
        results: The list of recipe result dicts to display.
        total_count: Total number of matching recipes (may exceed len(results)).
        top_n: The maximum number of results originally requested.
    """
    if total_count > top_n:
        print(f"\n找到 {total_count} 个符合条件的菜谱，显示前 {len(results)} 条:\n")
    else:
        print(f"\n找到 {total_count} 个符合条件的菜谱:\n")


def print_recipe_list(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Print all recipe results in the list and return a display map.

    Returns:
        Dict mapping 1-based index to recipe dict (for shopping list selection).
    """
    display_map: Dict[int, Dict[str, Any]] = {}
    for idx, info in enumerate(results, 1):
        recipe = info["recipe"]
        display_map[idx] = recipe
        print_recipe_result(recipe, info, idx)
    return display_map
