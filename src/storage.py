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