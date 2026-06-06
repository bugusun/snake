"""Data-driven map definitions for the Snake game."""

from __future__ import annotations

from dataclasses import dataclass


Point = tuple[int, int]


@dataclass(frozen=True)
class MapConfig:
    name: str
    description: str
    obstacles: frozenset[Point]


def build_map_catalog(grid_width: int, grid_height: int) -> tuple[MapConfig, ...]:
    """Build a small catalog of safe, replayable maps."""

    return (
        MapConfig(
            name="青翠草地",
            description="开阔场地，没有内部障碍，适合熟悉操作。",
            obstacles=frozenset(),
        ),
        MapConfig(
            name="石阵花园",
            description="对称石阵与纵向通道，路线选择更紧张。",
            obstacles=frozenset(_stone_garden(grid_width, grid_height)),
        ),
        MapConfig(
            name="螺旋遗迹",
            description="断裂螺旋墙体，考验提前规划和转向节奏。",
            obstacles=frozenset(_spiral_ruins(grid_width, grid_height)),
        ),
        MapConfig(
            name="十字回廊",
            description="四向通道交错，适合练习提前转向和贴边穿行。",
            obstacles=frozenset(_cross_corridor(grid_width, grid_height)),
        ),
        MapConfig(
            name="双环迷宫",
            description="内外环墙错位留门，需要绕行寻找安全路线。",
            obstacles=frozenset(_double_ring(grid_width, grid_height)),
        ),
        MapConfig(
            name="桥岛水道",
            description="左右岛块夹出中路，桥口处更考验节奏。",
            obstacles=frozenset(_bridge_islands(grid_width, grid_height)),
        ),
        MapConfig(
            name="栅栏长廊",
            description="多段竖向栅栏形成蛇形路线，适合慢速观察格子。",
            obstacles=frozenset(_fence_lanes(grid_width, grid_height)),
        ),
    )


def _stone_garden(grid_width: int, grid_height: int) -> set[Point]:
    center_y = grid_height // 2
    obstacles: set[Point] = set()

    for y in range(3, grid_height - 3):
        if y not in (center_y - 1, center_y, center_y + 1):
            obstacles.add((6, y))
            obstacles.add((grid_width - 7, y))

    for x in range(8, grid_width - 8):
        obstacles.add((x, 4))
        obstacles.add((x, grid_height - 5))

    return _without_spawn_zone(obstacles, grid_width, grid_height)


def _spiral_ruins(grid_width: int, grid_height: int) -> set[Point]:
    obstacles: set[Point] = set()

    for x in range(4, grid_width - 4):
        obstacles.add((x, 3))
    for y in range(4, grid_height - 3):
        obstacles.add((grid_width - 5, y))
    for x in range(5, grid_width - 5):
        obstacles.add((x, grid_height - 4))
    for y in range(6, grid_height - 5):
        obstacles.add((5, y))
    for x in range(6, grid_width - 8):
        obstacles.add((x, 6))

    gaps = {
        (grid_width - 5, grid_height // 2),
        (grid_width - 5, grid_height // 2 + 1),
        (5, grid_height // 2),
        (grid_width // 2, 3),
        (grid_width // 2 + 1, 3),
    }
    obstacles.difference_update(gaps)
    return _without_spawn_zone(obstacles, grid_width, grid_height)


def _cross_corridor(grid_width: int, grid_height: int) -> set[Point]:
    center_x = grid_width // 2
    center_y = grid_height // 2
    obstacles: set[Point] = set()

    for y in range(2, grid_height - 2):
        if y not in range(center_y - 2, center_y + 3):
            obstacles.add((center_x - 4, y))
            obstacles.add((center_x + 4, y))

    for x in range(3, grid_width - 3):
        if x not in range(center_x - 4, center_x + 5):
            obstacles.add((x, center_y - 4))
            obstacles.add((x, center_y + 4))

    return _without_spawn_zone(obstacles, grid_width, grid_height)


def _double_ring(grid_width: int, grid_height: int) -> set[Point]:
    center_x = grid_width // 2
    center_y = grid_height // 2
    obstacles: set[Point] = set()

    for x in range(4, grid_width - 4):
        obstacles.add((x, 3))
        obstacles.add((x, grid_height - 4))
    for y in range(4, grid_height - 3):
        obstacles.add((4, y))
        obstacles.add((grid_width - 5, y))

    for x in range(7, grid_width - 7):
        obstacles.add((x, 6))
        obstacles.add((x, grid_height - 7))
    for y in range(7, grid_height - 6):
        obstacles.add((7, y))
        obstacles.add((grid_width - 8, y))

    gaps = {
        (center_x, 3),
        (center_x + 1, 3),
        (center_x, grid_height - 4),
        (center_x + 1, grid_height - 4),
        (4, center_y),
        (grid_width - 5, center_y),
        (7, center_y - 1),
        (grid_width - 8, center_y + 1),
    }
    obstacles.difference_update(gaps)
    return _without_spawn_zone(obstacles, grid_width, grid_height)


def _bridge_islands(grid_width: int, grid_height: int) -> set[Point]:
    center_y = grid_height // 2
    obstacles: set[Point] = set()

    for x in range(3, 8):
        for y in range(3, grid_height - 3):
            if y not in range(center_y - 1, center_y + 2):
                obstacles.add((x, y))

    for x in range(grid_width - 8, grid_width - 3):
        for y in range(3, grid_height - 3):
            if y not in range(center_y - 1, center_y + 2):
                obstacles.add((x, y))

    for x in range(8, grid_width - 8):
        obstacles.add((x, center_y - 4))
        obstacles.add((x, center_y + 4))

    return _without_spawn_zone(obstacles, grid_width, grid_height)


def _fence_lanes(grid_width: int, grid_height: int) -> set[Point]:
    obstacles: set[Point] = set()

    for column_index, x in enumerate(range(4, grid_width - 4, 4)):
        gap_start = 3 + (column_index % 3) * 3
        for y in range(2, grid_height - 2):
            if gap_start <= y <= gap_start + 2:
                continue
            obstacles.add((x, y))

    return _without_spawn_zone(obstacles, grid_width, grid_height)


def _without_spawn_zone(obstacles: set[Point], grid_width: int, grid_height: int) -> set[Point]:
    center_x = grid_width // 2
    center_y = grid_height // 2
    safe_zone = {
        (x, y)
        for x in range(center_x - 5, center_x + 3)
        for y in range(center_y - 2, center_y + 3)
    }
    return {
        point
        for point in obstacles
        if 0 < point[0] < grid_width - 1
        and 0 < point[1] < grid_height - 1
        and point not in safe_zone
    }
