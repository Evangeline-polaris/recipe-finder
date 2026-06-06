"""
购物清单生成和配方缩放功能模块。

提供缺失原料清单生成、配方份量缩放等功能。
"""

import copy
import re
from typing import Dict, List

from matcher import normalize_ingredient_name, SEASONINGS


def format_quantity(quantity_str: str, factor: float) -> str:
    """将用量字符串中的数字部分乘以缩放系数。

    解析规则：
    - 提取字符串中第一个数字（整数或浮点数，如 "500"、"1.5"）。
    - 乘以 factor 后替换回原字符串。
    - 如果找不到数字，则保留原字符串。
    - 整数结果去掉末尾的 ".0"，非整数结果保留最多 2 位小数。

    Args:
        quantity_str: 原始用量字符串，如 "500克"、"2个"、"1.5汤匙"。
        factor: 缩放系数，如 2 表示双倍，0.5 表示减半。

    Returns:
        缩放后的用量字符串。

    Example:
        >>> format_quantity("500克", 2)
        "1000克"
        >>> format_quantity("1.5汤匙", 2)
        "3汤匙"
        >>> format_quantity("适量", 3)
        "适量"
    """
    if factor == 1.0:
        return quantity_str

    match = re.search(r"\d+\.?\d*", quantity_str)
    if not match:
        return quantity_str

    original_num_str = match.group()
    original_num = float(original_num_str)
    new_num = original_num * factor

    # 格式化新数字：整数去掉 .0，非整数保留最多 2 位小数
    if new_num == int(new_num):
        new_num_str = str(int(new_num))
    else:
        new_num_str = f"{new_num:.2f}".rstrip("0").rstrip(".")

    return quantity_str[: match.start()] + new_num_str + quantity_str[match.end() :]


def scale_recipe(recipe: Dict, factor: float) -> Dict:
    """按指定倍数缩放配方份量，返回新菜谱对象。

    对 ingredients 中每一项的 quantity 字段进行数字缩放。
    原始菜谱不会被修改。

    Args:
        recipe: 原始菜谱字典，需包含 "ingredients" 列表。
        factor: 缩放系数。1.0 保持不变，2.0 双倍，0.5 减半。

    Returns:
        缩放后的新菜谱字典（深拷贝）。

    Example:
        >>> doubled = scale_recipe(recipe, 2.0)
        >>> doubled["ingredients"][0]["quantity"]
        "4个"
    """
    scaled = copy.deepcopy(recipe)
    for ingredient in scaled.get("ingredients", []):
        if "quantity" in ingredient:
            ingredient["quantity"] = format_quantity(ingredient["quantity"], factor)
    return scaled


def generate_shopping_list(
    recipe: Dict,
    user_ingredients: List[str],
    synonyms: Dict[str, List[str]],
    include_seasonings: bool = True,
) -> List[Dict]:
    """生成菜谱中用户缺少的原料购物清单。

    遍历菜谱的 ingredients，对每个原料：
    1. 归一化名称（使用同义词库）。
    2. 判断是否为调料（基于 SEASONINGS 集合）。
    3. 如果用户已有该原料，跳过。
    4. 如果原料是调料且 include_seasonings=False，跳过。
    5. 否则加入购物清单。

    Args:
        recipe: 目标菜谱字典，需包含 "ingredients" 列表。
        user_ingredients: 用户输入的原料列表（已归一化）。
        synonyms: 同义词映射字典，用于归一化菜谱原料名称。
        include_seasonings: 是否在购物清单中包含调料。默认 True。

    Returns:
        缺失原料列表，每个元素为：
        {"name": str, "quantity": str, "is_seasoning": bool}

    Example:
        >>> shopping = generate_shopping_list(recipe, ["番茄", "鸡蛋"], synonyms)
        >>> for item in shopping:
        ...     print(f"{item['name']} × {item['quantity']}")
    """
    user_set = set(user_ingredients)
    shopping_list: List[Dict] = []

    for ingredient in recipe.get("ingredients", []):
        raw_name = ingredient.get("name", "")
        normalized = normalize_ingredient_name(raw_name, synonyms)
        is_seasoning = normalized in SEASONINGS

        # 用户已有该原料
        if normalized in user_set:
            continue

        # 调料且用户选择不包含调料
        if is_seasoning and not include_seasonings:
            continue

        shopping_list.append(
            {
                "name": raw_name,
                "quantity": ingredient.get("quantity", ""),
                "is_seasoning": is_seasoning,
            }
        )

    return shopping_list
