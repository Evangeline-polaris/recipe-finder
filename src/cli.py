from storage import load_recipes
from matcher import load_synonyms, normalize_ingredients_list, partial_match, exact_match


def main_menu():
    print("\n===== 智能食谱查找器 =====")
    while True:
        print("\n1. 输入食材查找菜谱")
        print("2. 退出")
        choice = input("\n请选择: ").strip()

        if choice == "1":
            ingredients = get_user_ingredients()
            if not ingredients:
                print("未输入任何食材")
                continue

            print(f"\n您输入的食材: {', '.join(ingredients)}")

            recipes = load_recipes()
            synonyms = load_synonyms()

            results = []
            for recipe in recipes:
                ratio, missing_main, missing_seasonings = partial_match(
                    ingredients, recipe["ingredients"], synonyms
                )
                if ratio > 0:
                    results.append(
                        (ratio, missing_main, missing_seasonings, recipe)
                    )

            if not results:
                print("\n未找到匹配的菜谱，请尝试其他食材。")
                continue

            results.sort(key=lambda x: x[0], reverse=True)

            print(f"\n找到 {len(results)} 个匹配菜谱:\n")
            for idx, (ratio, missing_main, missing_seasonings, recipe) in enumerate(results, 1):
                pct = f"{int(ratio * 100)}%"
                print(f"{idx}. {recipe['name']} — {pct}")
                if missing_main:
                    print(f"    还需材料：{'、'.join(missing_main)}")
                if missing_seasonings:
                    print(f"    还需调料: {'、'.join(missing_seasonings)}")

        elif choice == "2":
            print("再见!")
            break
        else:
            print("无效选择，请重新输入")


def get_user_ingredients():
    user_input = input("请输入你拥有的食材（用逗号分隔）: ").strip()
    if user_input:
        items = [i.strip() for i in user_input.replace("，", ",").split(",") if i.strip()]
        return items
    return []