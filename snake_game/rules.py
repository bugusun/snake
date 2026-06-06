"""Mode and food rule definitions for the Snake game."""

from __future__ import annotations

from dataclasses import dataclass



@dataclass(frozen=True)
class ModeConfig:
    name: str
    description: str
    speed_multiplier: float = 1.0
    obstacle_bonus: int = 0
    wrap_walls: bool = False
    golden_food_chance: float = 0.12
    ice_food_chance: float = 0.10


@dataclass(frozen=True)
class FoodRule:
    name: str
    texture_key: str
    score: int
    grow: int
    slow_duration: float = 0.0


MODES: tuple[ModeConfig, ...] = (
    ModeConfig(
        name="经典模式",
        description="速度平衡，边界墙正常碰撞。",
    ),
    ModeConfig(
        name="疾速模式",
        description="节奏略快；障碍地图中吃到食物有额外分数。",
        speed_multiplier=1.15,
        obstacle_bonus=1,
        golden_food_chance=0.16,
        ice_food_chance=0.06,
    ),
    ModeConfig(
        name="穿墙模式",
        description="外边界变成隧道，内部障碍仍会撞毁。",
        speed_multiplier=1.0,
        wrap_walls=True,
        golden_food_chance=0.10,
        ice_food_chance=0.14,
    ),
)


FOOD_RULES = {
    "apple": FoodRule(name="普通苹果", texture_key="food", score=1, grow=1),
    "gold": FoodRule(name="金苹果", texture_key="gold_food", score=3, grow=1),
    "ice": FoodRule(name="冰莓", texture_key="ice_food", score=1, grow=1, slow_duration=4.0),
}
