import json
import os


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RECIPES_FILE = os.path.join(DATA_DIR, "recipes.json")


def load_recipes():
    """Load all recipes from the JSON data file.

    Reads ``data/recipes.json`` and returns the decoded list of recipe
    dictionaries.  Returns an empty list if the file does not exist.

    Returns:
        List[Dict]: A list of recipe dictionaries loaded from disk.
    """
    if not os.path.exists(RECIPES_FILE):
        return []
    with open(RECIPES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_recipes(recipes):
    """Persist the given list of recipes to the JSON data file.

    Creates the data directory if it does not exist, then writes the recipes
    to ``data/recipes.json`` with UTF-8 encoding and 2-space indentation.

    Args:
        recipes: List of recipe dictionaries to save.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RECIPES_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)


def update_rating(recipe_id, new_score):
    """Update a recipe's rating with a new user score.

    Computes the weighted average of the existing rating and the new score,
    increments ratings_count, and saves the updated recipes back to disk.

    Args:
        recipe_id: The id of the recipe to update (string).
        new_score: The user's rating, must be an integer between 1 and 5.

    Returns:
        True if the recipe was found and updated, False otherwise.
    """
    # Validate score range
    if not isinstance(new_score, int) or new_score < 1 or new_score > 5:
        return False

    recipes = load_recipes()

    for recipe in recipes:
        if recipe.get("id") == recipe_id:
            old_rating = recipe.get("rating", 0.0)
            count = recipe.get("ratings_count", 0)
            new_avg = (old_rating * count + new_score) / (count + 1)
            recipe["rating"] = new_avg
            recipe["ratings_count"] = count + 1
            save_recipes(recipes)
            return True

    # Recipe not found
    return False


def toggle_favorite(recipe_id):
    """Toggle the is_favorite flag for a recipe.

    If the recipe is currently not a favorite, it becomes one; if it already
    is a favorite, it gets removed from favorites.

    Args:
        recipe_id: The id of the recipe to toggle (string).

    Returns:
        The new favorite status (True/False) if the recipe was found,
        or None if no recipe matched the given id.
    """
    recipes = load_recipes()

    for recipe in recipes:
        if recipe.get("id") == recipe_id:
            current = recipe.get("is_favorite", False)
            recipe["is_favorite"] = not current
            save_recipes(recipes)
            return recipe["is_favorite"]

    return None


def get_favorites():
    """Return all recipes that are marked as favorites.

    Returns:
        A list of recipe dictionaries where is_favorite is True.
    """
    recipes = load_recipes()
    return [recipe for recipe in recipes if recipe.get("is_favorite", False)]


def export_favorites(filepath="data/favorites.json"):
    """Export favorite recipes to a standalone JSON file.

    Writes basic information (id, name, cuisine) for each favorite recipe
    so that the list can be shared or imported later.

    Args:
        filepath: Destination file path (default: data/favorites.json).

    Returns:
        The number of favorites exported.
    """
    favorites = get_favorites()
    data = []
    for recipe in favorites:
        data.append(
            {
                "id": recipe.get("id"),
                "name": recipe.get("name"),
                "cuisine": recipe.get("cuisine", ""),
            }
        )
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return len(data)


def import_favorites(filepath):
    """Import favorite recipes from a previously exported JSON file.

    Reads a list of recipe IDs from the file and sets is_favorite=True for
    each matching recipe.  Existing favorites are not overwritten (they stay
    True), i.e. this is a merge operation.

    Args:
        filepath: Path to the exported favorites JSON file.

    Returns:
        The number of recipes whose is_favorite was set to True by this
        import (excluding those that were already favorites).
    """
    if not os.path.exists(filepath):
        return 0

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Collect IDs to import
    ids_to_fav = {item["id"] for item in data if "id" in item}
    if not ids_to_fav:
        return 0

    recipes = load_recipes()
    count = 0

    for recipe in recipes:
        if recipe.get("id") in ids_to_fav:
            if not recipe.get("is_favorite", False):
                recipe["is_favorite"] = True
                count += 1

    if count > 0:
        save_recipes(recipes)

    return count
