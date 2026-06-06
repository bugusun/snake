"""Headless validation entry for the Snake game."""

from __future__ import annotations

import os
from collections import deque


def run_smoke_test() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    import pygame

    from snake_game.assets import TEXTURE_FILES
    from snake_game.fonts import load_ui_font
    from snake_game.game import DOWN, LEFT, RIGHT, UP, Food, GameState, SnakeGame
    from snake_game.rules import FOOD_RULES, MODES
    from snake_game.settings import ASSET_DIR

    game = SnakeGame()
    missing = [filename for filename in TEXTURE_FILES.values() if not (ASSET_DIR / filename).exists()]
    if missing:
        raise AssertionError(f"missing generated textures: {missing}")

    body_rect = game.textures["snake_body"].get_bounding_rect(1)
    tail_rect = game.textures["snake_tail"].get_bounding_rect(1)
    assert body_rect.width >= game.settings.cell_size - 4
    assert body_rect.height >= game.settings.cell_size - 4
    assert tail_rect.width >= game.settings.cell_size - 6
    assert tail_rect.height >= game.settings.cell_size - 6

    assert game.state == GameState.MAIN_MENU
    assert len(game.maps) >= 7
    assert len(game.map_menu.items) == len(game.maps)
    assert len(game.main_menu.items) >= 5
    assert game.settings.base_moves_per_second <= 6.0
    assert game.settings.max_moves_per_second <= 12.5

    center_x = game.settings.grid_width // 2
    center_y = game.settings.grid_height // 2
    safe_zone = {
        (x, y)
        for x in range(center_x - 5, center_x + 3)
        for y in range(center_y - 2, center_y + 3)
    }
    for map_config in game.maps:
        assert not map_config.obstacles & safe_zone
        free_cells = [
            (x, y)
            for x in range(1, game.settings.grid_width - 1)
            for y in range(1, game.settings.grid_height - 1)
            if (x, y) not in map_config.obstacles
        ]
        assert len(free_cells) >= 120

    font = load_ui_font(24)
    for sample in ("开始游戏", "地图选择", "玩法说明", "连击倒计时"):
        rendered = font.render(sample, True, (255, 255, 255))
        assert rendered.get_width() > 0

    menu_width = min(520, game.settings.window_width - 180)
    for menu in (game.main_menu, game.map_menu, game.mode_menu):
        for item in menu.items:
            label = game.font.render(item.label, True, (255, 255, 255))
            assert label.get_width() <= menu_width - 110

    footer_width = game.settings.window_width - 96
    description_width = min(680, game.settings.window_width - 160) - 24
    for map_config in game.maps:
        footer = f"当前地图：{map_config.name}｜{map_config.description}"
        fitted = game._render_fitted_text(footer, game.small_font, (255, 255, 255), footer_width)
        assert fitted.get_width() <= footer_width
        assert game.small_font.size(map_config.description)[0] <= description_width
    for mode in MODES:
        footer = f"当前模式：{mode.name}｜{mode.description}"
        fitted = game._render_fitted_text(footer, game.small_font, (255, 255, 255), footer_width)
        assert fitted.get_width() <= footer_width
        assert game.small_font.size(mode.description)[0] <= description_width

    game._handle_keydown(pygame.K_DOWN)
    assert game.main_menu.selected_index == 1
    game._handle_keydown(pygame.K_RETURN)
    assert game.state == GameState.MAP_SELECT
    game._handle_keydown(pygame.K_ESCAPE)
    assert game.state == GameState.MAIN_MENU
    for map_index in range(len(game.maps)):
        game.map_menu.select(map_index)
        game._activate_map_menu()
        assert game.map_index == map_index
        assert game.state == GameState.MAIN_MENU
    game.map_menu.select(1)
    game._activate_map_menu()
    assert game.current_map.name == "石阵花园"
    assert game.state == GameState.MAIN_MENU

    game.main_menu.select(2)
    game._handle_keydown(pygame.K_RETURN)
    assert game.state == GameState.MODE_SELECT
    game.mode_menu.select(1)
    game._activate_mode_menu()
    assert game.current_mode.name == "疾速模式"
    assert game.state == GameState.MAIN_MENU

    game._start_game()
    assert game.state == GameState.RUNNING
    walkable_max_x = game.settings.grid_width - 2
    walkable_max_y = game.settings.grid_height - 2
    assert game._tail_direction([(18, 5), (walkable_max_x, 5), (1, 5)]) == LEFT
    assert game._tail_direction([(3, 5), (1, 5), (walkable_max_x, 5)]) == RIGHT
    assert game._tail_direction([(5, 12), (5, walkable_max_y), (5, 1)]) == UP
    assert game._tail_direction([(5, 3), (5, 1), (5, walkable_max_y)]) == DOWN
    game._rotate_for_direction(game.textures["snake_tail"], (walkable_max_x - 1, 0))

    game.mode_index = 2
    game.snake.body = deque([(2, 5), (1, 5), (walkable_max_x, 5)])
    game.snake.direction = RIGHT
    game.snake.queued_direction = RIGHT
    game.previous_body = list(game.snake.body)
    game.food = Food((10, 10), "apple", FOOD_RULES["apple"])
    game._draw_snake()

    wrap_cases = (
        (deque([(walkable_max_x, 4), (walkable_max_x - 1, 4), (walkable_max_x - 2, 4)]), RIGHT, (1, 4)),
        (deque([(1, 6), (2, 6), (3, 6)]), LEFT, (walkable_max_x, 6)),
        (deque([(7, 1), (7, 2), (7, 3)]), UP, (7, walkable_max_y)),
        (deque([(9, walkable_max_y), (9, walkable_max_y - 1), (9, walkable_max_y - 2)]), DOWN, (9, 1)),
    )
    for body, direction, expected_head in wrap_cases:
        game.snake.body = body
        game.snake.direction = direction
        game.snake.queued_direction = direction
        game.previous_body = list(body)
        game.food = Food((10, 10), "apple", FOOD_RULES["apple"])
        game._advance_snake()
        assert game.snake.head == expected_head
        game._draw_snake()

    for _ in range(3):
        game._advance_snake()
        game._update(1 / 60)
        game._draw()

    game._end_game()
    assert game.state == GameState.GAME_OVER
    game._restart()
    assert game.state == GameState.RUNNING
    assert game.score == 0
    pygame.quit()


if __name__ == "__main__":
    run_smoke_test()
    print("smoke_test=ok")
