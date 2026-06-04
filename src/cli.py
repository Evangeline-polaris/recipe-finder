from storage import load_recipes
from matcher import (
    load_synonyms,
    load_substitutions,
    normalize_ingredients_list,
    weighted_match,
    exact_match,
)
from filter_sort import (
    filter_by_max_time,
    filter_by_cuisine,
    filter_by_dietary,
    sort_recipes,
    get_all_cuisines,
)
from shopping import generate_shopping_list, scale_recipe


def main_menu():
    print("\n===== 智能食谱查找器 =====")
    while True:
        print("\n1. 输入食材查找菜谱")
        print("2. 查看收藏夹")
        print("3. 一周推荐计划")
        print("4. 退出")
        choice = input("\n请选择: ").strip()

        if choice == "1":
            ingredients = get_user_ingredients()
            if not ingredients:
                print("未输入任何食材")
                continue

            sub_choice = input("是否允许食材替换？(y/n): ").strip().lower()
            allow_sub = sub_choice == "y"

            print(f"\n您输入的食材: {', '.join(ingredients)}")

            recipes = load_recipes()
            synonyms = load_synonyms()
            substitutions = load_substitutions()

            user_normalized = normalize_ingredients_list(ingredients, synonyms)

            results = []
            for recipe in recipes:
                ratio, missing_main, missing_seasonings, sub_items = weighted_match(
                    user_normalized,
                    recipe["ingredients"],
                    synonyms,
                    substitutions,
                    allow_substitution=allow_sub,
                )
                if ratio > 0:
                    results.append(
                        (ratio, missing_main, missing_seasonings, sub_items, recipe)
                    )

            if not results:
                print("\n未找到匹配的菜谱，请尝试其他食材。")
                continue

            # 构建匹配率字典和菜谱列表
            match_percents = {
                recipe["id"]: ratio
                for ratio, _, _, _, recipe in results
            }
            filtered = [recipe for _, _, _, _, recipe in results]

            # ---- 筛选步骤 ----

            # 1. 最大总耗时
            time_choice = input("\n是否需要按最大总耗时过滤？(y/n): ").strip().lower()
            if time_choice == "y":
                try:
                    max_min = int(input("请输入最大总耗时（分钟）: ").strip())
                    filtered = filter_by_max_time(filtered, max_min)
                    if not filtered:
                        print("\n没有符合条件的菜谱。")
                        continue
                except ValueError:
                    print("输入无效，跳过时间过滤。")

            # 2. 菜系过滤
            cuisine_choice = input("\n是否需要按菜系过滤？(y/n): ").strip().lower()
            if cuisine_choice == "y":
                all_cuisines = get_all_cuisines(recipes)
                print(f"可选菜系: {', '.join(all_cuisines)}")
                cuisine_input = input("请输入菜系（多个用逗号分隔）: ").strip()
                if cuisine_input:
                    cuisines = [
                        c.strip()
                        for c in cuisine_input.replace("，", ",").split(",")
                        if c.strip()
                    ]
                    filtered = filter_by_cuisine(filtered, cuisines)
                    if not filtered:
                        print("\n没有符合条件的菜谱。")
                        continue

            # 3. 饮食标签过滤
            dietary_choice = input("\n是否需要按饮食标签过滤？(y/n): ").strip().lower()
            if dietary_choice == "y":
                tags_input = input("请输入饮食标签（多个用逗号分隔，如：素食,无麸质）: ").strip()
                if tags_input:
                    tags = [
                        t.strip()
                        for t in tags_input.replace("，", ",").split(",")
                        if t.strip()
                    ]
                    filtered = filter_by_dietary(filtered, tags)
                    if not filtered:
                        print("\n没有符合条件的菜谱。")
                        continue

            # ---- 排序步骤 ----
            print("\n请选择排序方式：")
            print("1. 按匹配度降序")
            print("2. 按总耗时升序")
            print("3. 按热量升序")
            sort_choice = input("请输入序号 (1/2/3): ").strip()

            if sort_choice == "1":
                filtered = sort_recipes(
                    filtered, "match_percent", reverse=True,
                    match_percents=match_percents,
                )
            elif sort_choice == "2":
                filtered = sort_recipes(filtered, "total_time", reverse=False)
            elif sort_choice == "3":
                filtered = sort_recipes(filtered, "calories", reverse=False)
            else:
                # 默认按匹配度降序
                print("输入无效，默认按匹配度降序排序。")
                filtered = sort_recipes(
                    filtered, "match_percent", reverse=True,
                    match_percents=match_percents,
                )

            # ---- 显示结果 ----
            # 构建结果查找映射
            result_map = {
                recipe["id"]: (ratio, missing_main, missing_seasonings, sub_items)
                for ratio, missing_main, missing_seasonings, sub_items, recipe in results
            }

            total = len(filtered)
            display = filtered[:10]

            if total > 10:
                print(f"\n找到 {total} 个符合条件的菜谱，显示前 10 条:\n")
            else:
                print(f"\n找到 {total} 个符合条件的菜谱:\n")

            # 构建编号 -> recipe 映射（用于购物清单）
            display_map = {}

            for idx, recipe in enumerate(display, 1):
                recipe_id = recipe["id"]
                display_map[idx] = recipe
                ratio, missing_main, missing_seasonings, sub_items = result_map[
                    recipe_id
                ]
                pct = f"{int(ratio * 100)}%"
                line = f"{idx}. {recipe['name']} — {pct}"
                extras = []
                if sub_items:
                    sub_strs = [
                        f"{user_ing}→{rcp_ing}"
                        for rcp_ing, user_ing in sub_items.items()
                    ]
                    extras.append(f"替换: {'、'.join(sub_strs)}")
                parts = [line]
                if extras:
                    parts.append(f" ({'; '.join(extras)})")
                print("".join(parts))
                if missing_main:
                    print(f"    还需材料：{'、'.join(missing_main)}")
                if missing_seasonings:
                    print(f"    还需调料: {'、'.join(missing_seasonings)}")
                total_time = recipe.get("prep_time", 0) + recipe.get("cook_time", 0)
                calories = recipe.get("nutrition", {}).get("calories", 0)
                print(f"    总耗时: {total_time} 分钟 | 热量: {calories:.0f} kcal")

            # ---- 购物清单交互 ----
            shop_choice = input(
                "\n输入菜谱编号查看购物清单 (0=跳过): "
            ).strip()
            if shop_choice != "0":
                try:
                    num = int(shop_choice)
                    if num in display_map:
                        selected = display_map[num]
                        shopping = generate_shopping_list(
                            selected, user_normalized, synonyms,
                            include_seasonings=True,
                        )
                        if shopping:
                            print(f"\n【购物清单】- {selected['name']}")
                            for item in shopping:
                                tag = "调料" if item["is_seasoning"] else "主料"
                                print(
                                    f"  - {item['name']} "
                                    f"{item['quantity']} ({tag})"
                                )
                        else:
                            print("该菜谱所有材料您都已具备！")

                        # ---- 配方缩放 ----
                        scale_choice = input(
                            "\n是否需要缩放配方？(y/n): "
                        ).strip().lower()
                        if scale_choice == "y":
                            factor_input = input(
                                "请输入缩放倍数（如 2 表示双倍，0.5 表示减半）: "
                            ).strip()
                            try:
                                factor = float(factor_input)
                                if factor <= 0:
                                    print("缩放倍数必须大于 0，已取消。")
                                else:
                                    scaled = scale_recipe(selected, factor)
                                    label = (
                                        f"{factor} 倍" if factor >= 1
                                        else f"×{factor}"
                                    )
                                    print(
                                        f"\n【缩放后配方】- "
                                        f"{scaled['name']} ({label}份量):"
                                    )
                                    for ing in scaled.get("ingredients", []):
                                        print(
                                            f"  - {ing['name']} "
                                            f"{ing.get('quantity', '')}"
                                        )
                            except ValueError:
                                print("输入无效，已取消缩放。")
                    else:
                        print("无效编号，已跳过。")
                except ValueError:
                    print("输入无效，已跳过。")

        elif choice == "2":
            print("\n功能开发中，敬请期待。")

        elif choice == "3":
            print("\n功能开发中，敬请期待。")

        elif choice == "4":
            print("再见!")
            break

        else:
            print("无效选择，请重新输入")


def get_user_ingredients():
    user_input = input("请输入你拥有的食材（用逗号分隔）: ").strip()
    if user_input:
        items = [
            i.strip()
            for i in user_input.replace("，", ",").split(",")
            if i.strip()
        ]
        return items
    return []