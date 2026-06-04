def main_menu():
    print("\n===== 智能食谱查找器 =====")
    while True:
        print("\n1. 输入食材查找菜谱")
        print("2. 退出")
        choice = input("\n请选择: ").strip()

        if choice == "1":
            ingredients = get_user_ingredients()
            print(f"您输入的食材: {', '.join(ingredients)}")
        elif choice == "2":
            print("再见!")
            break
        else:
            print("无效选择，请重新输入")


def get_user_ingredients():
    user_input = input("请输入你拥有的食材（用逗号分隔）: ").strip()
    if user_input:
        items = [i.strip() for i in user_input.split(",") if i.strip()]
        return items
    return []