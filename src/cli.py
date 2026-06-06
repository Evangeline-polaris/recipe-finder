from typing import Any, Dict, List, Optional

from storage import (
    load_recipes,
    update_rating,
    toggle_favorite,
    get_favorites,
    export_favorites,
    import_favorites,
)
from matcher import (
    load_synonyms,
    load_substitutions,
    normalize_ingredients_list,
    weighted_match,
)
from filter_sort import (
    filter_by_max_time,
    filter_by_cuisine,
    filter_by_dietary,
    sort_recipes,
    get_cuisine_groups,
    get_all_cuisines,
)
from shopping import generate_shopping_list, scale_recipe
from recommender import weekly_plan
from display import (
    parse_ingredients_input,
    print_recipe_result,
    print_results_summary,
    print_recipe_list,
)


# ============================================================
# 输入验证辅助函数
# ============================================================


def _prompt_yes_no(prompt: str) -> bool:
    """循环询问 y/n，直到用户输入有效值为止。

    Args:
        prompt: 显示给用户的提示信息（不含「(y/n)」后缀）。

    Returns:
        True 如果用户输入「y」，False 如果用户输入「n」。
    """
    while True:
        choice = input(f"{prompt} (y/n): ").strip().lower()
        if choice == "y":
            return True
        if choice == "n":
            return False
        print("无效输入，请输入 y 或 n")


def _prompt_int_range(
    prompt: str, min_val: int, max_val: int, allow_zero: bool = True
) -> int:
    """循环询问一个范围内的整数，直到用户输入有效值为止。

    Args:
        prompt: 显示给用户的提示信息。
        min_val: 最小可接受值（含）。
        max_val: 最大可接受值（含）。
        allow_zero: 是否允许 0 作为特殊返回码（默认 True）。

    Returns:
        用户输入的有效整数。
    """
    while True:
        choice = input(f"{prompt}: ").strip()
        if choice == "0" and allow_zero:
            return 0
        try:
            num = int(choice)
            if min_val <= num <= max_val:
                return num
            print(
                f"无效输入，请输入 {min_val}~{max_val} 之间的数字"
                + ("，或 0 跳过" if allow_zero else "")
            )
        except ValueError:
            print("输入无效，请输入数字")


def _get_valid_dietary_tags() -> set:
    """从所有菜谱中提取去重的饮食标签集合，用于输入验证。

    Returns:
        所有已知饮食标签的集合（小写）。
    """
    recipes = load_recipes()
    tags: set = set()
    for r in recipes:
        for tag in r.get("dietary_tags", []):
            tags.add(tag.strip().lower())
    return tags


# ============================================================
# 菜单函数
# ============================================================


def main_menu():
    """Display the main interactive menu loop.

    Presents five options: search recipes by ingredients, exit, weekly meal
    plan, rate a recipe, and favorites management.  Loops until the user
    selects exit.
    """
    print("\n===== 智能食谱查找器 =====")
    while True:
        print("\n1. 输入食材查找菜谱")
        print("2. 一周推荐计划")
        print("3. 给菜谱评分")
        print("4. 收藏夹管理")
        print("5. 退出")
        choice = input("\n请选择: ").strip()

        if choice == "1":
            search_recipes_menu()
        elif choice == "2":
            weekly_plan_menu()
        elif choice == "3":
            rate_recipe_menu()
        elif choice == "4":
            favorites_menu()
        elif choice == "5":
            print("再见!")
            break
        else:
            print("无效选择，请重新输入")


def get_user_ingredients():
    """从命令行交互获取用户输入的食材列表。

    提示用户输入逗号分隔的食材名称，使用 ``parse_ingredients_input``
    解析并返回原始名称列表。

    Returns:
        食材名称列表（原始名称，未归一化）。如果用户未输入则返回空列表。
    """
    user_input = input("请输入你拥有的食材（用逗号分隔）: ").strip()
    return parse_ingredients_input(user_input) if user_input else []


# ============================================================
# 核心搜索函数（供 CLI 菜单和命令行模式共用）
# ============================================================


def run_search(
    ingredients_list: List[str],
    allow_substitution: bool = False,
    max_time: Optional[int] = None,
    cuisine_list: Optional[List[str]] = None,
    dietary_list: Optional[List[str]] = None,
    sort_by: str = "match",
    top_n: int = 10,
) -> Dict[str, Any]:
    """Run a recipe search with the given parameters and return structured results.

    This function encapsulates matching, filtering, sorting, and truncation
    so that both the interactive menu and the command-line mode can reuse the
    same core logic.
    """
    recipes = load_recipes()
    synonyms = load_synonyms()
    substitutions = load_substitutions()

    user_normalized = normalize_ingredients_list(ingredients_list, synonyms)

    # ---- 匹配 ----
    all_results: List[Dict[str, Any]] = []
    for recipe in recipes:
        ratio, missing_main, missing_seasonings, sub_items = weighted_match(
            user_normalized,
            recipe["ingredients"],
            synonyms,
            substitutions,
            allow_substitution=allow_substitution,
        )
        if ratio > 0:
            all_results.append(
                {
                    "recipe": recipe,
                    "match_ratio": ratio,
                    "missing_main": missing_main,
                    "missing_seasonings": missing_seasonings,
                    "sub_items": sub_items,
                }
            )

    if not all_results:
        return {
            "results": [],
            "total_count": 0,
            "user_normalized": user_normalized,
            "synonyms": synonyms,
            "match_percents": {},
        }

    # Build match_percents for all results
    match_percents = {r["recipe"]["id"]: r["match_ratio"] for r in all_results}

    # Extract recipe-only list for filter/sort functions
    filtered = [r["recipe"] for r in all_results]

    # ---- 筛选 ----
    if max_time is not None and max_time > 0:
        filtered = filter_by_max_time(filtered, max_time)
    if cuisine_list is not None and len(cuisine_list) > 0:
        filtered = filter_by_cuisine(filtered, cuisine_list)
    if dietary_list is not None and len(dietary_list) > 0:
        filtered = filter_by_dietary(filtered, dietary_list)

    if not filtered:
        return {
            "results": [],
            "total_count": 0,
            "user_normalized": user_normalized,
            "synonyms": synonyms,
            "match_percents": match_percents,
        }

    # ---- 排序 ----
    if sort_by == "time":
        filtered = sort_recipes(filtered, "total_time", reverse=False)
    elif sort_by == "calories":
        filtered = sort_recipes(filtered, "calories", reverse=False)
    else:
        # default: match descending
        filtered = sort_recipes(
            filtered,
            "match_percent",
            reverse=True,
            match_percents=match_percents,
        )

    total_count = len(filtered)
    filtered = filtered[:top_n]

    # Build result dicts for the filtered list
    results: List[Dict[str, Any]] = []
    for recipe in filtered:
        # Find original match info
        info = next(
            (r for r in all_results if r["recipe"]["id"] == recipe["id"]),
            None,
        )
        if info:
            results.append(info)
        else:
            results.append(
                {
                    "recipe": recipe,
                    "match_ratio": match_percents.get(recipe["id"], 0.0),
                    "missing_main": [],
                    "missing_seasonings": [],
                    "sub_items": {},
                }
            )

    return {
        "results": results,
        "total_count": total_count,
        "user_normalized": user_normalized,
        "synonyms": synonyms,
        "match_percents": match_percents,
    }


# ============================================================
# 1. 查找菜谱（交互式菜单）
# ============================================================


def search_recipes_menu():
    """Interactive recipe search with filtering, sorting, shopping list, and scaling.

    Prompts the user for ingredient input, optional substitution settings, and
    filter criteria (max time, cuisine, dietary tags).  Displays sorted results
    and allows the user to view a shopping list and scale a selected recipe.
    """
    ingredients = get_user_ingredients()
    if not ingredients:
        print("未输入任何食材")
        return

    allow_sub = _prompt_yes_no("是否允许食材替换？")

    print(f"\n您输入的食材: {', '.join(ingredients)}")

    # ---- 收集筛选参数 ----
    max_time: Optional[int] = None
    if _prompt_yes_no("是否需要按最大总耗时过滤？"):
        while True:
            try:
                max_time = int(input("请输入最大总耗时（分钟）: ").strip())
                if max_time > 0:
                    break
                print("请输入大于 0 的数字")
            except ValueError:
                print("输入无效，请输入数字")

    cuisine_list: Optional[List[str]] = None
    if _prompt_yes_no("是否需要按菜系过滤？"):
        recipes_all = load_recipes()
        cuisine_groups = get_cuisine_groups(recipes_all)
        valid_cuisines = set(get_all_cuisines(recipes_all))

        # ── 第一级：选择大区 ──
        region_names = list(cuisine_groups.keys())
        print("\n请选择菜系大类：")
        for idx, region in enumerate(region_names, 1):
            count = len(cuisine_groups[region])
            print(f"  {idx}. {region}（{count} 种菜系）")
        print("  0. 跳过")

        region_choice = _prompt_int_range(
            "请输入序号", 0, len(region_names), allow_zero=True
        )
        if region_choice == 0:
            cuisine_list = None
        else:
            selected_region = region_names[region_choice - 1]
            sub_cuisines = cuisine_groups[selected_region]
            print(f"\n{selected_region}可选: {', '.join(sub_cuisines)}")

            # 循环验证菜系输入
            while True:
                cuisine_input = input(
                    "请输入菜系（多个用逗号分隔，留空=选择全部）: "
                ).strip()
                if not cuisine_input:
                    # 留空则选中该大区下所有菜系
                    cuisine_list = list(sub_cuisines)
                    break
                parsed = parse_ingredients_input(cuisine_input)
                invalid = [c for c in parsed if c not in valid_cuisines]
                if invalid:
                    print(
                        f"无效菜系: {', '.join(invalid)}。"
                        f" 可用菜系: {', '.join(sorted(sub_cuisines))}"
                    )
                else:
                    cuisine_list = parsed
                    break

    dietary_list: Optional[List[str]] = None
    if _prompt_yes_no("是否需要按饮食标签过滤？"):
        valid_tags = _get_valid_dietary_tags()
        if not valid_tags:
            print("没有可用的饮食标签。")
        else:
            TAG_ORDER = [
                "荤菜",
                "素食",
                "纯素食",
                "低卡",
                "低碳水",
                "快手",
                "无麸质",
                "高蛋白",
            ]
            sorted_tags = [t for t in TAG_ORDER if t in valid_tags]
            tag_map = {str(i): tag for i, tag in enumerate(sorted_tags, 1)}
            print(
                f"可用标签: "
                f"{', '.join(f'{i}.{tag}' for i, tag in enumerate(sorted_tags, 1))}"
            )
            # 循环验证序号输入
            while True:
                tags_input = input(
                    "请输入饮食标签序号（多个用逗号分隔，如 1,4，留空跳过）: "
                ).strip()
                if not tags_input:
                    dietary_list = None
                    break
                invalid_nums = []
                selected_tags = []
                for part in tags_input.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    if part in tag_map:
                        selected_tags.append(tag_map[part])
                    else:
                        invalid_nums.append(part)
                if invalid_nums:
                    print(
                        f"无效序号: {', '.join(invalid_nums)}。"
                        f" 可选: 1-{len(sorted_tags)}"
                    )
                elif not selected_tags:
                    print("未选择任何标签，请重新输入")
                else:
                    dietary_list = selected_tags
                    break

    # ---- 排序 ----
    print("\n请选择排序方式：")
    print("1. 按匹配度降序")
    print("2. 按总耗时升序")
    print("3. 按热量升序")
    sort_choice = _prompt_int_range("请输入序号 (1/2/3)", 1, 3, allow_zero=False)
    sort_map = {1: "match", 2: "time", 3: "calories"}
    sort_by = sort_map[sort_choice]

    # ---- 执行搜索 ----
    search_result = run_search(
        ingredients_list=ingredients,
        allow_substitution=allow_sub,
        max_time=max_time,
        cuisine_list=cuisine_list,
        dietary_list=dietary_list,
        sort_by=sort_by,
        top_n=10,
    )

    results = search_result["results"]
    total = search_result["total_count"]
    user_normalized = search_result["user_normalized"]
    synonyms = search_result["synonyms"]

    if not results:
        print("\n没有符合条件的菜谱。")
        return

    print_results_summary(results, total, top_n=10)

    # Use shared display function
    display_map = print_recipe_list(results)

    # ---- 查看制作方法 ----
    step_choice = _prompt_int_range(
        "\n输入菜谱编号查看制作方法 (0=跳过)",
        0,
        max(display_map.keys()) if display_map else 1,
        allow_zero=True,
    )
    if step_choice != 0 and step_choice in display_map:
        recipe = display_map[step_choice]
        print(f"\n【制作方法】- {recipe['name']}")
        for i, step in enumerate(recipe.get("steps", []), 1):
            print(f"  {i}. {step}")
        print()

    # ---- 购物清单交互 ----
    shop_choice = _prompt_int_range(
        "\n输入菜谱编号查看购物清单 (0=跳过)",
        0,
        max(display_map.keys()) if display_map else 1,
        allow_zero=True,
    )
    if shop_choice != 0:
        if shop_choice in display_map:
            selected = display_map[shop_choice]
            shopping = generate_shopping_list(
                selected,
                user_normalized,
                synonyms,
                include_seasonings=True,
            )
            if shopping:
                print(f"\n【购物清单】- {selected['name']}")
                for item in shopping:
                    tag = "调料" if item["is_seasoning"] else "主料"
                    print(f"  - {item['name']} " f"{item['quantity']} ({tag})")
            else:
                print("该菜谱所有材料您都已具备！")

            # ---- 配方缩放 ----
            if _prompt_yes_no("是否需要缩放配方？"):
                while True:
                    factor_input = input(
                        "请输入缩放倍数（如 2 表示双倍，0.5 表示减半）: "
                    ).strip()
                    try:
                        factor = float(factor_input)
                        if factor <= 0:
                            print("缩放倍数必须大于 0，请重新输入")
                            continue
                        scaled = scale_recipe(selected, factor)
                        label = f"{factor} 倍" if factor >= 1 else f"×{factor}"
                        print(f"\n【缩放后配方】- " f"{scaled['name']} ({label}份量):")
                        for ing in scaled.get("ingredients", []):
                            print(f"  - {ing['name']} " f"{ing.get('quantity', '')}")
                        break
                    except ValueError:
                        print("输入无效，请输入数字")
        else:
            print("无效编号，已跳过。")


# ============================================================
# 3. 一周推荐计划
# ============================================================


def weekly_plan_menu():
    """贪心式一周菜谱推荐，并支持生成合并购物清单。"""
    ingredients = get_user_ingredients()
    if not ingredients:
        print("未输入任何食材")
        return

    allow_sub = _prompt_yes_no("是否允许食材替换？")

    while True:
        days_input = input("计划推荐几天？（默认3）: ").strip()
        if not days_input:
            num_days = 3
            break
        try:
            num_days = int(days_input)
            if num_days < 1:
                print("请输入至少 1 天")
                continue
            break
        except ValueError:
            print("输入无效，请输入数字")

    recipes = load_recipes()
    synonyms = load_synonyms()
    substitutions = load_substitutions()
    user_normalized = normalize_ingredients_list(ingredients, synonyms)

    # weekly_plan now returns full details — no re-computation needed
    plan_details = weekly_plan(
        user_ingredients=user_normalized,
        recipes=recipes,
        substitutions=substitutions,
        allow_substitution=allow_sub,
        num_days=num_days,
    )

    if not plan_details:
        print("\n未能生成任何推荐菜谱，请尝试更多食材。")
        return

    print(f"\n===== 一周推荐计划（共 {len(plan_details)} 道菜）=====\n")

    for idx, detail in enumerate(plan_details, 1):
        recipe = detail["recipe"]
        # Build info dict matching what print_recipe_result expects
        info = {
            "match_ratio": detail["score"],
            "missing_main": detail["missing_main"],
            "missing_seasonings": detail["missing_seasonings"],
            "sub_items": detail["sub_items"],
        }
        print_recipe_result(
            recipe if isinstance(recipe, dict) else recipe.to_dict(),
            info,
            idx,
        )

    # ---- 选择菜品 ----
    print(f"\n可选菜品编号: 1 ~ {len(plan_details)}")
    selection_input = input(
        "请输入要加入购物清单的菜品编号（逗号分隔，如 1,3,5，留空=全选）: "
    ).strip()

    selected_details = []
    if not selection_input:
        # 留空 = 全选
        selected_details = list(plan_details)
    else:
        selected_nums = parse_ingredients_input(selection_input)
        invalid_nums = []
        for part in selected_nums:
            try:
                num = int(part)
                if 1 <= num <= len(plan_details):
                    selected_details.append(plan_details[num - 1])
                else:
                    invalid_nums.append(part)
            except ValueError:
                invalid_nums.append(part)
        if invalid_nums:
            print(f"无效编号: {', '.join(invalid_nums)}，已跳过。")
            if not selected_details:
                print("没有选中任何有效菜品。")
                return

    # ---- 合并购物清单 ----
    if _prompt_yes_no("是否生成合并购物清单？"):
        # 对用户选中的菜品生成购物清单并合并去重
        merged: dict = {}  # key = normalized_name, value = item_dict
        for detail in selected_details:
            recipe = detail["recipe"]
            shopping = generate_shopping_list(
                recipe if isinstance(recipe, dict) else recipe.to_dict(),
                user_normalized,
                synonyms,
                include_seasonings=True,
            )
            for item in shopping:
                key = item["name"]
                if key not in merged:
                    merged[key] = item

        if merged:
            print(
                f"\n【合并购物清单】- "
                f"基于 {len(selected_details)} 道菜品，共 {len(merged)} 项"
            )
            for item in merged.values():
                tag = "调料" if item["is_seasoning"] else "主料"
                print(f"  - {item['name']} {item['quantity']} ({tag})")
        else:
            print("\n您已具备所选菜品的所有食材！")


# ============================================================
# 4. 给菜谱评分
# ============================================================


def rate_recipe_menu():
    """列出所有菜谱供用户选择并评分。"""
    recipes = load_recipes()
    if not recipes:
        print("\n没有可评分的菜谱。")
        return

    print("\n===== 菜谱评分 =====")
    print(f"\n共 {len(recipes)} 道菜谱：\n")

    for idx, recipe in enumerate(recipes, 1):
        name = recipe["name"]
        rating = recipe.get("rating", 0.0)
        count = recipe.get("ratings_count", 0)
        print(f"  {idx}. {name}  (评分: {rating:.1f}, 评价数: {count})")

    choice = _prompt_int_range(
        "请选择菜谱编号 (0=返回)", 0, len(recipes), allow_zero=True
    )
    if choice == 0:
        return

    selected = recipes[choice - 1]
    recipe_id = selected["id"]
    recipe_name = selected["name"]

    while True:
        score_input = input(f"请为「{recipe_name}」评分（1~5星）: ").strip()
        try:
            score = int(score_input)
            if 1 <= score <= 5:
                break
            print("评分必须是 1~5 的整数")
        except ValueError:
            print("评分必须是整数")

    success = update_rating(recipe_id, score)
    if success:
        print(f"成功为「{recipe_name}」评分 {score} 星！")
    else:
        print("评分失败：评分必须是 1~5 的整数。")


# ============================================================
# 5. 收藏夹管理
# ============================================================


def favorites_menu():
    """收藏夹管理子菜单：查看、添加、移除、导出、导入收藏。"""
    while True:
        print("\n===== 收藏夹管理 =====")
        print("1. 查看收藏列表")
        print("2. 添加菜谱到收藏")
        print("3. 移除收藏")
        print("4. 导出收藏夹到 JSON")
        print("5. 导入收藏夹 JSON")
        print("0. 返回主菜单")
        choice = input("\n请选择: ").strip()

        if choice == "1":
            # ---- 查看收藏列表 ----
            favorites = get_favorites()
            if not favorites:
                print("\n收藏夹为空。")
            else:
                print(f"\n===== 我的收藏（共 {len(favorites)} 道）=====\n")
                for idx, recipe in enumerate(favorites, 1):
                    rating = recipe.get("rating", 0.0)
                    print(f"  {idx}. {recipe['name']}  (评分: {rating:.1f})")

        elif choice == "2":
            # ---- 添加菜谱到收藏 ----
            recipes = load_recipes()
            if not recipes:
                print("\n没有可收藏的菜谱。")
                continue

            print(f"\n===== 添加收藏 =====")
            print(f"共 {len(recipes)} 道菜谱：\n")
            for idx, recipe in enumerate(recipes, 1):
                fav_mark = " ★" if recipe.get("is_favorite", False) else ""
                print(f"  {idx}. {recipe['name']}{fav_mark}")

            choice_num = _prompt_int_range(
                "请选择菜谱编号 (0=返回)", 0, len(recipes), allow_zero=True
            )
            if choice_num == 0:
                continue

            selected = recipes[choice_num - 1]
            if selected.get("is_favorite", False):
                print(f"「{selected['name']}」已在收藏夹中。")
            else:
                toggle_favorite(selected["id"])
                print(f"成功将「{selected['name']}」添加到收藏！")

        elif choice == "3":
            # ---- 移除收藏 ----
            favorites = get_favorites()
            if not favorites:
                print("\n收藏夹为空，没有可移除的菜谱。")
                continue

            print(f"\n===== 移除收藏 =====")
            print(f"共 {len(favorites)} 道收藏：\n")
            for idx, recipe in enumerate(favorites, 1):
                rating = recipe.get("rating", 0.0)
                print(f"  {idx}. {recipe['name']}  (评分: {rating:.1f})")

            choice_num = _prompt_int_range(
                "请选择编号 (0=返回)", 0, len(favorites), allow_zero=True
            )
            if choice_num == 0:
                continue

            selected = favorites[choice_num - 1]
            toggle_favorite(selected["id"])
            print(f"已将「{selected['name']}」从收藏夹移除。")

        elif choice == "4":
            # ---- 导出收藏夹 ----
            filepath = input(
                "请输入导出文件路径（默认: data/favorites.json）: "
            ).strip()
            if filepath:
                count = export_favorites(filepath)
            else:
                count = export_favorites()
            print(f"导出成功，共 {count} 道收藏菜谱。")

        elif choice == "5":
            # ---- 导入收藏夹 ----
            filepath = input("请输入要导入的 JSON 文件路径: ").strip()
            if not filepath:
                print("未输入文件路径，已取消。")
                continue
            count = import_favorites(filepath)
            if count > 0:
                print(f"导入成功，新增 {count} 道收藏菜谱。")
            else:
                print("导入失败：文件不存在或所有菜谱已收藏。")

        elif choice == "0":
            break

        else:
            print("无效选择，请重新输入")
