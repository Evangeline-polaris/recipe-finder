"""批量给 recipes.json 打饮食标签。

标签规则（含冲突检测）：
  - 素食：食材不含肉类/鱼类/海鲜关键词
  - 荤菜：食材含肉类/鱼类/海鲜关键词  （与素食互斥）
  - 纯素食：素食 + 不含蛋/奶/黄油/蜂蜜等动物产品
  - 高蛋白：protein >= 30g
  - 低卡：calories <= 250 kcal
  - 低碳水：carbs <= 20g
  - 快手：total_time <= 30 min

已存在的标签（素食/无麸质）不会被覆盖，只追加新标签。
运行前自动备份 data/recipes.json -> data/recipes.json.bak
"""

import json
import shutil
import os

MEAT_KEYWORDS = [
    "肉", "猪", "牛", "羊", "鸡", "鸭", "鹅", "鱼", "虾", "蟹", "贝", "鱿",
    "培根", "火腿", "香肠", "腊肠", "咸鱼", "肉末", "排骨", "里脊", "肘子",
    "五花", "腿肉", "胸肉", "鸡翅", "鸡腿", "鸡爪", "鸡胗", "鸡心",
    "牛腩", "牛腱", "牛尾", "牛排", "羊排", "羊腿", "三文鱼", "鳕鱼",
    "金枪鱼", "沙丁", "龙虾", "牡蛎", "蛤蜊", "海参", "鲍鱼",
    "lamb", "beef", "chicken", "pork", "fish", "shrimp", "prawn",
    "crab", "lobster", "mussel", "oyster", "salmon", "tuna", "cod",
    "sardine", "bacon", "sausage", "ham", "turkey", "duck", "goose",
    "veal", "venison", "mince", "meat", "squid", "octopus", "scallop",
    "anchovy", "caviar", "鳗", "鲈", "鲫", "鲤", "鳊", "鲶", "鲢",
    "鳝", "泥鳅", "带鱼", "黄鱼", "马鲛", "剥皮鱼", "多宝鱼",
]

ANIMAL_PRODUCT_KEYWORDS = [
    "蛋", "鸡蛋", "鸭蛋", "鹅蛋", "鹌鹑蛋",
    "奶", "牛奶", "奶粉", "黄油", "奶油", "芝士", "奶酪",
    "蜂蜜", "酸奶", "炼乳", "淡奶", "酥油",
    "egg", "milk", "butter", "cream", "cheese", "honey",
    "yogurt", "ghee", "whey", "curd",
]

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RECIPES_PATH = os.path.join(BASE_DIR, "data", "recipes.json")
BACKUP_PATH = os.path.join(BASE_DIR, "data", "recipes.json.bak")


def has_meat(recipe: dict) -> bool:
    """检查菜谱食材中是否包含肉类/鱼类/海鲜。"""
    for ing in recipe.get("ingredients", []):
        name_lower = ing["name"].lower()
        for kw in MEAT_KEYWORDS:
            if kw in name_lower:
                return True
    return False


def has_animal_product(recipe: dict) -> bool:
    """检查菜谱食材中是否包含动物产品（蛋/奶/黄油等）。"""
    for ing in recipe.get("ingredients", []):
        name_lower = ing["name"].lower()
        for kw in ANIMAL_PRODUCT_KEYWORDS:
            if kw in name_lower:
                return True
    return False


def compute_tags(recipe: dict) -> list:
    """根据菜谱内容计算应添加的标签列表（不包含已有标签）。"""
    existing = set(recipe.get("dietary_tags", []))
    new_tags = set()

    meat = has_meat(recipe)
    animal = has_animal_product(recipe)

    # ---- 互斥判断：素食 vs 荤菜 ----
    # 如果已有素食标签，保持不动，不标荤菜
    if "素食" not in existing:
        if meat:
            new_tags.add("荤菜")
        else:
            # 不含肉类 → 素食
            new_tags.add("素食")
            # 纯素食：素食 + 不含动物产品
            if not animal:
                new_tags.add("纯素食")
    else:
        # 已有素食标签，检查是否纯素食
        if not animal and "纯素食" not in existing:
            new_tags.add("纯素食")

    # ---- 营养标签 ----
    n = recipe.get("nutrition", {})
    protein = n.get("protein", 0)
    calories = n.get("calories", 0)
    carbs = n.get("carbs", 0)

    if protein >= 30:
        new_tags.add("高蛋白")
    if calories <= 250:
        new_tags.add("低卡")
    if carbs <= 20:
        new_tags.add("低碳水")

    # ---- 时长标签 ----
    total_time = recipe.get("prep_time", 0) + recipe.get("cook_time", 0)
    if total_time <= 30:
        new_tags.add("快手")

    # 只返回新标签（排除已存在的）
    return [t for t in new_tags if t not in existing]


def main():
    # 备份原文件
    shutil.copy2(RECIPES_PATH, BACKUP_PATH)
    print(f"已备份到: {BACKUP_PATH}")

    with open(RECIPES_PATH, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    stats = {"新增荤菜": 0, "新增素食": 0, "新增纯素食": 0, "新增高蛋白": 0,
             "新增低卡": 0, "新增低碳水": 0, "新增快手": 0}

    for recipe in recipes:
        new_tags = compute_tags(recipe)
        if new_tags:
            existing = recipe.get("dietary_tags", [])
            recipe["dietary_tags"] = existing + new_tags
            for t in new_tags:
                stats[f"新增{t}"] = stats.get(f"新增{t}", 0) + 1

    with open(RECIPES_PATH, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)

    print("\n标签打标完成！统计：")
    for tag, count in stats.items():
        print(f"  {tag}: {count} 道")
    print(f"\n总计新增标签: {sum(stats.values())} 个")


if __name__ == "__main__":
    main()