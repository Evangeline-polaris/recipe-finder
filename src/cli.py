def main_menu():
    while True:
        print("\n===== 智能食谱查找器 =====")
        print("1. 输入食材")
        print("q. 退出")
        choice = input("\n请选择: ").strip()

        if choice == "1":
            input_ingredients()
        elif choice.lower() == "q":
            print("再见!")
            break
        else:
            print("无效选择，请重新输入")


def input_ingredients():
    ingredients = input("请输入你拥有的食材（用逗号分隔）: ").strip()
    if ingredients:
        items = [i.strip() for i in ingredients.split(",") if i.strip()]
        print(f"你输入的食材: {', '.join(items)}")
    else:
        print("未输入任何食材")
