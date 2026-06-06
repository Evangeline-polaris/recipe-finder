#!/usr/bin/env python3
"""Recipe Finder entry point.

Supports both interactive menu mode and command-line mode.
When ``--ingredients`` is provided the tool runs in command-line mode
and prints results directly to stdout.  Otherwise it launches the
interactive TUI.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from cli import main_menu, run_search
from shopping import generate_shopping_list, scale_recipe
from display import (
    parse_ingredients_input,
    print_results_summary,
    print_recipe_result,
)


def _print_command_results(search_result, top_n=None):
    """Pretty-print search results to stdout for command-line mode.

    Args:
        search_result: dict returned by ``run_search``.
        top_n: if given, only print the first *top_n* results (overrides
               what was already truncated by run_search).  None means
               print all results in the dict.
    """
    results = search_result["results"]
    total = search_result["total_count"]

    if not results:
        print("未找到匹配的菜谱。")
        return None  # no best recipe for --shopping

    display = results[:top_n] if top_n else results
    print_results_summary(display, total, top_n=top_n or len(display))

    for idx, info in enumerate(display, 1):
        print_recipe_result(info["recipe"], info, idx)

    return results[0] if results else None


def main():
    """Parse command-line arguments and dispatch to the appropriate mode.

    If ``--ingredients`` is provided, runs in command-line mode: performs a
    recipe search and prints results (and optionally a shopping list with
    scaling) directly to stdout.  Otherwise, launches the interactive TUI via
    ``main_menu()``.
    """
    parser = argparse.ArgumentParser(
        description="智能食谱查找器 — 根据现有食材匹配菜谱",
    )
    parser.add_argument(
        "-i",
        "--ingredients",
        type=str,
        default=None,
        help="用户拥有的食材（逗号分隔字符串）。提供此参数则进入命令行模式。",
    )
    parser.add_argument(
        "-s",
        "--allow-substitution",
        action="store_true",
        default=False,
        help="是否允许食材替换（默认不允许）。",
    )
    parser.add_argument(
        "--max-time",
        type=int,
        default=None,
        help="最大总耗时（分钟），可选。",
    )
    parser.add_argument(
        "--cuisine",
        nargs="*",
        default=None,
        help="按菜系过滤，支持多个（如 --cuisine 中餐 川菜）。",
    )
    parser.add_argument(
        "--dietary",
        nargs="*",
        default=None,
        help="按饮食标签过滤，支持多个（如 --dietary 素食 无麸质）。",
    )
    parser.add_argument(
        "--sort",
        choices=["match", "time", "calories"],
        default="match",
        help="排序方式：match（匹配度降序），time（总耗时升序），calories（热量升序）。默认 match。",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="显示前 N 条结果（默认 5）。",
    )
    parser.add_argument(
        "--shopping",
        action="store_true",
        default=False,
        help="对最佳匹配菜谱生成购物清单。",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=None,
        help="缩放倍数（例如 0.5 表示减半），需与 --shopping 配合使用。",
    )

    args = parser.parse_args()

    # ---- 命令行模式 ----
    if args.ingredients:
        ingredients_list = parse_ingredients_input(args.ingredients)
        if not ingredients_list:
            print("错误：--ingredients 不能为空。")
            sys.exit(1)

        search_result = run_search(
            ingredients_list=ingredients_list,
            allow_substitution=args.allow_substitution,
            max_time=args.max_time,
            cuisine_list=args.cuisine,
            dietary_list=args.dietary,
            sort_by=args.sort,
            top_n=args.top,
        )

        best = _print_command_results(search_result, top_n=args.top)

        # ---- 购物清单 / 缩放 ----
        if args.shopping and best is not None:
            synonyms = search_result["synonyms"]
            user_normalized = search_result["user_normalized"]
            recipe = best["recipe"]

            # Normalize user ingredients for shopping list
            shopping = generate_shopping_list(
                recipe,
                user_normalized,
                synonyms,
                include_seasonings=True,
            )
            if shopping:
                print(f"\n【购物清单】- {recipe['name']}")
                for item in shopping:
                    tag = "调料" if item["is_seasoning"] else "主料"
                    print(f"  - {item['name']} " f"{item['quantity']} ({tag})")
            else:
                print("\n该菜谱所有材料您都已具备！")

            if args.scale is not None:
                factor = args.scale
                if factor <= 0:
                    print("缩放倍数必须大于 0，已取消。")
                else:
                    scaled = scale_recipe(recipe, factor)
                    label = f"{factor} 倍" if factor >= 1 else f"×{factor}"
                    print(f"\n【缩放后配方】- " f"{scaled['name']} ({label}份量):")
                    for ing in scaled.get("ingredients", []):
                        print(f"  - {ing['name']} " f"{ing.get('quantity', '')}")

        return

    # ---- 交互式菜单模式 ----
    main_menu()


if __name__ == "__main__":
    main()
