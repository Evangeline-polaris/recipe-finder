import json
import os


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
RECIPES_FILE = os.path.join(DATA_DIR, 'recipes.json')


def load_recipes():
    if not os.path.exists(RECIPES_FILE):
        return []
    with open(RECIPES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_recipes(recipes):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RECIPES_FILE, 'w', encoding='utf-8') as f:
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
