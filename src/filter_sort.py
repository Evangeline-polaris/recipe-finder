"""
筛选和排序功能模块。

提供菜谱的时间筛选、菜系筛选、饮食标签筛选，以及多维度排序功能。
所有筛选和排序函数均返回新的菜谱列表，不修改原始数据。
筛选条件可组合使用（先筛选再排序）。
"""

from typing import Dict, List, Optional


def filter_by_max_time(recipes: List[Dict], max_minutes: int) -> List[Dict]:
    """筛选总耗时不超过指定分钟数的菜谱。

    总耗时 = prep_time + cook_time。

    Args:
        recipes: 菜谱列表，每个菜谱字典需包含 prep_time 和 cook_time 字段。
        max_minutes: 最大总耗时（分钟，含等于）。

    Returns:
        满足 prep_time + cook_time <= max_minutes 的菜谱列表。

    Example:
        >>> filter_by_max_time(recipes, 30)
        [{"name": "番茄炒鸡蛋", "prep_time": 10, "cook_time": 8, ...}, ...]
    """
    return [
        r
        for r in recipes
        if r.get("prep_time", 0) + r.get("cook_time", 0) <= max_minutes
    ]


def filter_by_cuisine(recipes: List[Dict], cuisine_list: List[str]) -> List[Dict]:
    """筛选菜系在指定列表中的菜谱。

    Args:
        recipes: 菜谱列表，每个菜谱字典需包含 cuisine 字段。
        cuisine_list: 目标菜系列表，如 ["中餐", "川菜"]。

    Returns:
        菜系在 cuisine_list 中的菜谱列表。

    Example:
        >>> filter_by_cuisine(recipes, ["川菜", "粤菜"])
        [{"name": "酸辣土豆丝", "cuisine": "川菜", ...}, ...]
    """
    cuisine_set = set(cuisine_list)
    return [r for r in recipes if r.get("cuisine", "") in cuisine_set]


def filter_by_dietary(recipes: List[Dict], required_tags: List[str]) -> List[Dict]:
    """筛选满足所有饮食标签要求的菜谱。

    菜谱的 dietary_tags 必须包含 required_tags 中的所有标签才算匹配。

    Args:
        recipes: 菜谱列表，每个菜谱字典需包含 dietary_tags 字段。
        required_tags: 必须满足的饮食标签列表，如 ["素食"]。

    Returns:
        满足所有饮食标签要求的菜谱列表。

    Example:
        >>> filter_by_dietary(recipes, ["素食", "无麸质"])
        [{"name": "酸辣土豆丝", "dietary_tags": ["素食", "无麸质"], ...}]
    """
    required = set(required_tags)
    return [r for r in recipes if required.issubset(set(r.get("dietary_tags", [])))]


def sort_recipes(
    recipes: List[Dict],
    sort_key: str,
    reverse: bool = False,
    match_percents: Optional[Dict[str, float]] = None,
) -> List[Dict]:
    """按指定字段对菜谱列表排序（返回新列表）。

    支持三种排序方式：
    - "match_percent": 按匹配率排序，需要传入 match_percents 字典。
    - "total_time": 按总耗时（prep_time + cook_time）排序。
    - "calories": 按热量（nutrition.calories）排序。

    Args:
        recipes: 菜谱列表。
        sort_key: 排序字段，可选 "match_percent"、"total_time"、"calories"。
        reverse: 是否降序排列，默认 False（升序）。
        match_percents: 匹配率字典，key 为菜谱 id，value 为匹配率（0.0~1.0）。
            仅在 sort_key="match_percent" 时需要提供。

    Returns:
        排序后的新列表。

    Raises:
        ValueError: 当 sort_key 无效时抛出。
        ValueError: 当 sort_key="match_percent" 但未提供 match_percents 时抛出。

    Example:
        >>> match_dict = {"a1b2": 0.85, "c3d4": 0.50}
        >>> sort_recipes(recipes, "match_percent", reverse=True, match_percents=match_dict)
    """
    if sort_key == "match_percent":
        if match_percents is None:
            raise ValueError("match_percents is required when sort_key='match_percent'")
        return sorted(
            recipes,
            key=lambda r: match_percents.get(r.get("id", ""), 0.0),
            reverse=reverse,
        )
    elif sort_key == "total_time":
        return sorted(
            recipes,
            key=lambda r: r.get("prep_time", 0) + r.get("cook_time", 0),
            reverse=reverse,
        )
    elif sort_key == "calories":
        return sorted(
            recipes,
            key=lambda r: r.get("nutrition", {}).get("calories", 0.0),
            reverse=reverse,
        )
    else:
        raise ValueError(
            f"Invalid sort_key: {sort_key!r}. "
            f"Expected one of: 'match_percent', 'total_time', 'calories'."
        )


def get_all_cuisines(recipes: List[Dict]) -> List[str]:
    """获取所有菜谱的去重菜系列表（按字母/拼音排序）。

    用于 CLI 界面中让用户选择菜系。

    Args:
        recipes: 菜谱列表，每个菜谱字典需包含 cuisine 字段。

    Returns:
        已排序的去重菜系列表。

    Example:
        >>> get_all_cuisines(recipes)
        ["川菜", "粤菜", "中餐"]
    """
    cuisines: set = set()
    for r in recipes:
        cuisine = r.get("cuisine", "")
        if cuisine:
            cuisines.add(cuisine)
    return sorted(cuisines)


# ---------------------------------------------------------------------------
# 按地理区域分组的菜系映射表（新导入菜谱的菜系均在此注册）
# ---------------------------------------------------------------------------
_CUISINE_REGION_MAP: Dict[str, str] = {
    # ── 中餐家族 ──
    "中餐": "中餐家族",
    "川菜": "中餐家族",
    "粤菜": "中餐家族",
    # ── 亚洲菜系 ──
    "日料": "亚洲菜系",
    "韩餐": "亚洲菜系",
    "印度菜": "亚洲菜系",
    "泰国菜": "亚洲菜系",
    "越南菜": "亚洲菜系",
    "马来西亚菜": "亚洲菜系",
    "菲律宾菜": "亚洲菜系",
    "土耳其菜": "亚洲菜系",
    "沙特阿拉伯菜": "亚洲菜系",
    "叙利亚菜": "亚洲菜系",
    # ── 欧洲菜系 ──
    "意大利菜": "欧洲菜系",
    "法国菜": "欧洲菜系",
    "西班牙菜": "欧洲菜系",
    "英国菜": "欧洲菜系",
    "希腊菜": "欧洲菜系",
    "俄罗斯菜": "欧洲菜系",
    "波兰菜": "欧洲菜系",
    "荷兰菜": "欧洲菜系",
    "葡萄牙菜": "欧洲菜系",
    "爱尔兰菜": "欧洲菜系",
    "克罗地亚菜": "欧洲菜系",
    "挪威菜": "欧洲菜系",
    "乌克兰菜": "欧洲菜系",
    "斯洛伐克菜": "欧洲菜系",
    # ── 美洲菜系 ──
    "美式": "美洲菜系",
    "墨西哥菜": "美洲菜系",
    "加拿大菜": "美洲菜系",
    "阿根廷菜": "美洲菜系",
    "委内瑞拉菜": "美洲菜系",
    "乌拉圭菜": "美洲菜系",
    "牙买加菜": "美洲菜系",
    "巴西菜": "美洲菜系",
    "智利菜": "美洲菜系",
    # ── 非洲及其他 ──
    "摩洛哥菜": "非洲及其他",
    "埃及菜": "非洲及其他",
    "突尼斯菜": "非洲及其他",
    "阿尔及利亚菜": "非洲及其他",
    "肯尼亚菜": "非洲及其他",
    "澳大利亚菜": "非洲及其他",
    "其他": "非洲及其他",
}

# 分组顺序（用户可见的大类顺序）
_REGION_ORDER: List[str] = [
    "中餐家族",
    "亚洲菜系",
    "欧洲菜系",
    "美洲菜系",
    "非洲及其他",
]


def get_cuisine_groups(recipes: List[Dict]) -> Dict[str, List[str]]:
    """将菜谱的菜系按地理区域分组，返回用于两级菜单展示的字典。

    第一级为大区（中餐家族 / 亚洲 / 欧洲 / 美洲 / 非洲及其他），
    每个大区下包含若干具体菜系（已去重、已排序）。

    Args:
        recipes: 菜谱列表。

    Returns:
        OrderedDict-alike: key 为大区名，value 为该大区下的菜系列表。
        大区按 ``_REGION_ORDER`` 顺序输出，菜系列表按中文拼音排序。

    Example:
        >>> groups = get_cuisine_groups(recipes)
        >>> for region, cuisines in groups.items():
        ...     print(f"{region}: {cuisines}")
    """
    groups: Dict[str, List[str]] = {region: [] for region in _REGION_ORDER}
    seen: Dict[str, set] = {region: set() for region in _REGION_ORDER}

    # 收集每个大区下的菜系
    for r in recipes:
        cuisine = r.get("cuisine", "")
        if not cuisine:
            continue
        region = _CUISINE_REGION_MAP.get(cuisine, "非洲及其他")
        if region not in seen:
            seen[region] = set()
        seen[region].add(cuisine)

    # 排序每个大区下的菜系，过滤掉空大区
    result: Dict[str, List[str]] = {}
    for region in _REGION_ORDER:
        if seen.get(region):
            result[region] = sorted(seen[region])
    return result
