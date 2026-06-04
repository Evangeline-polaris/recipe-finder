import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from models import Recipe


def test_to_dict_from_dict_roundtrip():
    """测试 to_dict 和 from_dict 的往返一致性"""
    recipe = Recipe(
        id="001",
        name="番茄炒蛋",
        ingredients=[
            {"name": "番茄", "quantity": "2个"},
            {"name": "鸡蛋", "quantity": "3个"},
        ],
        steps=["打蛋", "炒蛋", "炒番茄", "混合"],
        prep_time=5,
        cook_time=10,
        cuisine="中餐",
        dietary_tags=["素食"],
        nutrition={"热量": 150.0, "蛋白质": 10.0},
        rating=4.5,
        ratings_count=100,
        is_favorite=True,
    )

    data = recipe.to_dict()
    restored = Recipe.from_dict(data)

    assert restored.id == recipe.id
    assert restored.name == recipe.name
    assert restored.ingredients == recipe.ingredients
    assert restored.steps == recipe.steps
    assert restored.prep_time == recipe.prep_time
    assert restored.cook_time == recipe.cook_time
    assert restored.cuisine == recipe.cuisine
    assert restored.dietary_tags == recipe.dietary_tags
    assert restored.nutrition == recipe.nutrition
    assert restored.rating == recipe.rating
    assert restored.ratings_count == recipe.ratings_count
    assert restored.is_favorite == recipe.is_favorite


def test_serialized_fields():
    """测试序列化后字段值正确"""
    recipe = Recipe(
        id="002",
        name="意大利面",
        ingredients=[
            {"name": "意面", "quantity": "200g"},
            {"name": "番茄酱", "quantity": "50g"},
        ],
        steps=["煮面", "炒酱", "混合"],
        prep_time=5,
        cook_time=15,
        cuisine="意大利",
        dietary_tags=["素食"],
        nutrition={"热量": 350.0, "碳水": 60.0},
        rating=4.2,
        ratings_count=50,
        is_favorite=False,
    )

    data = recipe.to_dict()
    assert data["name"] == "意大利面"
    assert data["cuisine"] == "意大利"
    assert data["prep_time"] == 5
    assert data["is_favorite"] is False
    assert len(data["ingredients"]) == 2
    assert data["ingredients"][0] == {"name": "意面", "quantity": "200g"}


if __name__ == "__main__":
    test_to_dict_from_dict_roundtrip()
    test_serialized_fields()
    print("所有测试通过!")