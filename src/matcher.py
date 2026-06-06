import json
import os
from typing import Dict, List, Set, Tuple


SEASONINGS: Set[str] = {
    # ===== 盐 =====
    "盐",
    "海盐",
    "粗盐",
    # ===== 糖 =====
    "糖",
    "白糖",
    "冰糖",
    "红糖",
    "细砂糖",
    "糖粉",
    "黑糖",
    "德麦拉拉糖",
    "深色软红糖",
    # ===== 油 =====
    "油",
    "食用油",
    "橄榄油",
    "葵花籽油",
    "菜籽油",
    "花生油",
    "椰子油",
    "初榨橄榄油",
    "香油",
    "猪油",
    "黄油",
    "芥花籽油",
    "花生油",
    "松露油",
    "高温烹饪油",
    "菜籽油",
    # ===== 味精/鸡精 =====
    "味精",
    "鸡精",
    # ===== 酱油 =====
    "酱油",
    "生抽",
    "老抽",
    "蒸鱼豉油",
    # ===== 醋 =====
    "醋",
    "白醋",
    "香醋",
    "镇江香醋",
    "红酒醋",
    "苹果醋",
    "麦芽醋",
    "雪莉醋",
    "纯素白葡萄酒醋",
    "白葡萄酒醋",
    # ===== 料酒/酒 =====
    "料酒",
    "米酒",
    "绍兴料酒",
    "啤酒",
    "清酒",
    "葡萄酒",
    "白葡萄酒",
    "红葡萄酒",
    "白兰地",
    "黑朗姆酒",
    "干雪莉酒",
    "干白葡萄酒",
    "雪莉酒",
    "甜雪莉酒",
    # ===== 胡椒粉 =====
    "胡椒粉",
    "白胡椒粉",
    "黑胡椒粉",
    # ===== 花椒 =====
    "花椒",
    "花椒粉",
    "贡布胡椒",
    # ===== 八角/桂皮/香叶/丁香 =====
    "八角",
    "桂皮",
    "香叶",
    "丁香",
    "丁香粉",
    "多香果",
    "多香果粉",
    # ===== 葱姜蒜 =====
    "葱",
    "葱花",
    "姜",
    "蒜",
    "姜粉",
    "细香葱",
    "南姜",
    "蒜粒",
    "蒜粉",
    "姜蒜酱",
    "姜酱",
    "南姜酱",
    "蒜蓉酱",
    # ===== 辣椒 =====
    "辣椒",
    "干辣椒",
    "辣椒粉",
    "红辣椒",
    "剁椒",
    "泡椒",
    "青辣椒",
    "苏格兰帽椒",
    "辣椒油",
    "辣椒酱",
    "烟熏辣椒粉",
    "卡宴辣椒粉",
    "安乔干辣椒",
    "鸟眼辣椒",
    "辣椒碎",
    "干红辣椒",
    "红辣椒碎",
    "红辣椒粉",
    "红椒碎",
    # ===== 咖喱 =====
    "咖喱粉",
    "咖喱酱",
    "牙买加咖喱粉",
    "马德拉斯咖喱酱",
    "玛莎曼咖喱酱",
    "帕能咖喱酱",
    "泰式绿咖喱酱",
    "泰式红咖喱酱",
    # ===== 孜然 =====
    "孜然",
    "孜然粉",
    "孜然籽",
    # ===== 姜黄 =====
    "姜黄",
    "姜黄粉",
    # ===== 香草 =====
    "百里香",
    "迷迭香",
    "牛至",
    "罗勒",
    "欧芹",
    "薄荷",
    "肉豆蔻",
    "罗勒叶",
    "莳萝",
    "香菜",
    "韭菜",
    "蒜苗",
    "大葱",
    "欧芹碎",
    "鲜欧芹碎",
    "香菜叶",
    "香菜籽",
    "香菜粉",
    "干莳萝",
    "干薄荷",
    "干牛至",
    "葫芦巴",
    "鲜罗勒",
    "鲜百里香",
    "辣薄荷",
    "马郁兰",
    "鼠尾草",
    "漆树粉",
    "龙蒿叶",
    "肉豆蔻粉",
    # ===== 肉桂 =====
    "肉桂",
    "肉桂粉",
    "肉桂棒",
    # ===== 淀粉/面粉 =====
    "淀粉",
    "水淀粉",
    "玉米淀粉",
    "面包糠",
    "淀粉水",
    "中筋面粉",
    "面粉",
    "自发粉",
    "黄豆粉",
    "糯米粉",
    "荞麦粉",
    "粗粒小麦粉",
    "高筋白面粉",
    "高筋全麦粉",
    "天妇罗粉",
    "白面粉",
    # ===== 鱼露/蚝油 =====
    "鱼露",
    "蚝油",
    "辣酱油",
    # ===== 酱料 =====
    "干黄酱",
    "甜面酱",
    "郫县豆瓣酱",
    "芥末酱",
    "花生酱",
    "烧烤酱",
    "焦糖酱",
    "焦糖糖浆",
    "辣椒酱",
    "奇米丘里酱",
    "芝麻酱",
    "恩奇拉达酱",
    "海鲜酱",
    "辣酱",
    "墨西哥鲜酱",
    "苏梅酱",
    "红椒酱",
    "甜辣酱",
    "塔巴斯科辣酱",
    "白芝麻酱",
    "罗望子酱",
    "香草豆酱",
    "第戎芥末酱",
    "英式芥末酱",
    "芥末粉",
    "芥末籽",
    # ===== 汁 =====
    "柠檬汁",
    "青柠汁",
    # ===== 高汤/汤底 =====
    "高汤",
    "鸡汤",
    "牛肉汤",
    "蔬菜高汤",
    "高汤块",
    "海鲜高汤",
    "蔬菜高汤块",
    # ===== 香草精 =====
    "香草精",
    "香草",
    "香草荚",
    "香草糖",
    # ===== 泡打粉/小苏打/酵母 =====
    "泡打粉",
    "小苏打",
    "酵母",
    "快速酵母",
    "即发酵母",
    # ===== 其他 =====
    "水",
    "可可粉",
    "五香粉",
    "芝麻",
    "枫糖浆",
    "多用途调料",
    "葛缕子籽",
    "水瓜柳",
    "清蜂蜜",
    "椰子糖",
    "吉士粉",
    "法吉塔调料",
    "茴香籽",
    "葛拉姆马萨拉",
    "吉利丁片",
    "金黄细砂糖",
    "黄金糖浆",
    "白砂糖",
    "哈里萨辣酱",
    "意大利综合香料",
    "卡布萨香料",
    "浅色软红糖",
    "混合香料",
    "糖蜜",
    "罂粟籽",
    "罂粟籽粉",
    "椰糖",
    "粉色食用色素",
    "德式酸菜",
    "调味料",
    "荷兰香料粉",
    "糖浆",
    "甜烟熏辣椒粉",
    "泰式辣椒酱",
    "无味吉利丁",
    "油醋汁",
    "黄色食用色素",
}


def is_seasoning(name: str) -> bool:
    """检查原料名称是否为调料。

    Args:
        name: 原料名称。

    Returns:
        True 如果该原料在预定义的调料集合中，否则 False。
    """
    return name in SEASONINGS


def load_synonyms(filepath: str = "data/synonyms.json") -> Dict[str, List[str]]:
    """从 JSON 文件加载同义词映射。

    Args:
        filepath: 同义词 JSON 文件路径，默认 ``data/synonyms.json``。

    Returns:
        同义词映射字典，key 为标准名称，value 为同义变体列表。
        如果文件不存在则返回空字典。
    """
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_substitutions(
    filepath: str = "data/substitutions.json",
) -> Dict[str, List[str]]:
    """从 JSON 文件加载食材替代规则。

    Args:
        filepath: 替代规则 JSON 文件路径，默认 ``data/substitutions.json``。

    Returns:
        替代规则字典，key 为菜谱中要求的原料，value 为可接受的替代品列表。
        如果文件不存在则返回空字典。
    """
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_ingredient_name(name: str, synonyms: Dict[str, List[str]]) -> str:
    """将单个原料名称归一化为标准形式。

    在同义词映射中查找匹配项：如果 name 是某个标准名称的变体，返回标准名称；
    如果 name 本身就是标准名称，直接返回。否则返回原名称。

    Args:
        name: 原始原料名称。
        synonyms: 同义词映射字典，key 为标准名称，value 为同义变体列表。

    Returns:
        归一化后的标准名称。
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
    """对原料名称列表进行批量归一化。

    Args:
        ingredients: 原始原料名称列表。
        synonyms: 同义词映射字典。

    Returns:
        归一化后的原料名称列表。
    """
    return [normalize_ingredient_name(name, synonyms) for name in ingredients]


def get_missing_seasonings(
    user_ingredients: List[str],
    recipe_ingredients: List[Dict[str, str]],
    synonyms: Dict[str, List[str]],
) -> List[str]:
    """获取菜谱所需但用户缺少的调料列表。

    先对双方原料名称进行同义词归一化，然后计算菜谱调料集合与
    用户调料集合的差集。

    Args:
        user_ingredients: 用户拥有的原料名称列表。
        recipe_ingredients: 菜谱的原料列表，每个元素包含 ``"name"`` 字段。
        synonyms: 同义词映射字典。

    Returns:
        用户缺少的调料名称列表（已排序）。
    """
    user_normalized = set(normalize_ingredients_list(user_ingredients, synonyms))
    recipe_names = [item["name"] for item in recipe_ingredients]
    recipe_normalized = normalize_ingredients_list(recipe_names, synonyms)

    recipe_seasonings = {n for n in recipe_normalized if is_seasoning(n)}
    missing = sorted(recipe_seasonings - user_normalized)
    return missing


def get_missing_main_ingredients(
    user_ingredients: List[str],
    recipe_ingredients: List[Dict[str, str]],
    synonyms: Dict[str, List[str]],
) -> List[str]:
    """获取菜谱所需但用户缺少的主料（非调料）列表。

    先归一化双方原料名称，排除调料后计算差集。

    Args:
        user_ingredients: 用户拥有的原料名称列表。
        recipe_ingredients: 菜谱的原料列表，每个元素包含 ``"name"`` 字段。
        synonyms: 同义词映射字典。

    Returns:
        用户缺少的主料名称列表（已排序）。
    """
    user_normalized = set(normalize_ingredients_list(user_ingredients, synonyms))
    recipe_names = [item["name"] for item in recipe_ingredients]
    recipe_normalized = normalize_ingredients_list(recipe_names, synonyms)

    recipe_main = {n for n in recipe_normalized if not is_seasoning(n)}
    missing = sorted(recipe_main - user_normalized)
    return missing


def weighted_match(
    user_ingredients: List[str],
    recipe_ingredients: List[Dict[str, str]],
    synonyms: Dict[str, List[str]],
    substitutions: Dict[str, List[str]],
    allow_substitution: bool = True,
) -> Tuple[float, List[str], List[str], Dict[str, str]]:
    """
    Calculate match ratio with optional ingredient substitution.

    Args:
        user_ingredients: Already-normalized list of ingredient names.
        recipe_ingredients: List of ingredient dicts (with "name" key).
        synonyms: Synonym mapping for normalizing recipe ingredients.
        substitutions: Substitution rules map.
        allow_substitution: Whether to apply substitution matching.

    Returns:
        (match_ratio, missing_main, missing_seasonings, substituted_items)
        - substituted_items: dict mapping recipe ingredient -> user ingredient
          that replaced it via substitution.
    """
    missing_seasonings_list = get_missing_seasonings(
        user_ingredients, recipe_ingredients, synonyms
    )

    if not recipe_ingredients:
        return 0.0, [], missing_seasonings_list, {}

    user_set = set(user_ingredients)
    recipe_names = [item["name"] for item in recipe_ingredients]
    recipe_normalized = normalize_ingredients_list(recipe_names, synonyms)

    # Identify main (non-seasoning) ingredients
    main_indices = [
        i for i, name in enumerate(recipe_normalized) if not is_seasoning(name)
    ]

    total_score = 0.0
    missing_main: List[str] = []
    substituted: Dict[str, str] = {}

    for idx in main_indices:
        name = recipe_normalized[idx]
        if name in user_set:
            total_score += 1.0
        elif allow_substitution and name in substitutions:
            # Try to find a matching substitute in the user's set
            candidates = substitutions[name]
            found = None
            for candidate in candidates:
                # Candidate may need normalization if it appears in synonyms
                candidate_norm = normalize_ingredient_name(candidate, synonyms)
                if candidate_norm in user_set:
                    found = candidate_norm
                    break
                if candidate in user_set:
                    found = candidate
                    break
            if found is not None:
                total_score += 0.8
                substituted[name] = found
            else:
                missing_main.append(name)
        else:
            missing_main.append(name)

    missing_main.sort()

    denominator = len(main_indices)
    ratio = total_score / denominator if denominator > 0 else 1.0

    return ratio, missing_main, missing_seasonings_list, substituted
