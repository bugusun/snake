"""Main game loop and polished Snake gameplay logic."""

from __future__ import annotations

import math
import random
import sys
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

import pygame

from snake_game.assets import load_textures
from snake_game.fonts import load_ui_font
from snake_game.maps import MapConfig, build_map_catalog
from snake_game.menu import Menu, MenuItem
from snake_game.rules import FOOD_RULES, MODES, FoodRule, ModeConfig
from snake_game.settings import SETTINGS, Settings


Point = tuple[int, int]
Direction = tuple[int, int]

UP: Direction = (0, -1)
DOWN: Direction = (0, 1)
LEFT: Direction = (-1, 0)
RIGHT: Direction = (1, 0)


class GameState(Enum):
    MAIN_MENU = auto()
    MAP_SELECT = auto()
    MODE_SELECT = auto()
    HELP = auto()
    RUNNING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


@dataclass
class Snake:
    body: deque[Point]
    direction: Direction
    queued_direction: Direction

    @property
    def head(self) -> Point:
        return self.body[0]


@dataclass
class Food:
    position: Point
    kind: str
    rule: FoodRule


@dataclass
class Particle:
    position: tuple[float, float]
    velocity: tuple[float, float]
    age: float
    lifetime: float
    color: tuple[int, int, int]


class SnakeGame:
    """A complete playable Snake game with menus, maps, and smooth movement."""

    def __init__(self, settings: Settings = SETTINGS) -> None:
        pygame.init()
        pygame.display.set_caption(settings.title)

        self.settings = settings
        self.screen = pygame.display.set_mode((settings.window_width, settings.window_height))
        self.clock = pygame.time.Clock()
        self.textures = load_textures()

        self.font = load_ui_font(25)
        self.large_font = load_ui_font(46, bold=True)
        self.medium_font = load_ui_font(32, bold=True)
        self.small_font = load_ui_font(19)

        self.rng = random.Random()
        self.maps = build_map_catalog(settings.grid_width, settings.grid_height)
        self.map_index = 0
        self.mode_index = 0
        self.state = GameState.MAIN_MENU
        self.previous_state = GameState.MAIN_MENU

        self.main_menu = Menu(
            [
                MenuItem("开始游戏", "start"),
                MenuItem("地图选择", "map"),
                MenuItem("模式选择", "mode"),
                MenuItem("玩法说明", "help"),
                MenuItem("退出游戏", "quit"),
            ]
        )
        self.map_menu = Menu([MenuItem(map_config.name, str(index)) for index, map_config in enumerate(self.maps)])
        self.mode_menu = Menu([MenuItem(mode.name, str(index)) for index, mode in enumerate(MODES)])

        self.score = 0
        self.best_score = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.last_food_name = "普通苹果"
        self.pending_growth = 0
        self.move_timer = 0.0
        self.animation_progress = 1.0
        self.slow_timer = 0.0
        self.screen_flash = 0.0
        self.head_bump = 0.0
        self.previous_body: list[Point] = []
        self.particles: list[Particle] = []
        self.snake = self._new_snake()
        self.previous_body = list(self.snake.body)
        self.food = self._spawn_food()

    @property
    def current_map(self) -> MapConfig:
        return self.maps[self.map_index]

    @property
    def current_mode(self) -> ModeConfig:
        return MODES[self.mode_index]

    def run(self) -> None:
        while True:
            delta_time = self.clock.tick(self.settings.fps) / 1000.0
            self._handle_events()
            self._update(delta_time)
            self._draw()

    def _new_snake(self) -> Snake:
        start_x = self.settings.grid_width // 2
        start_y = self.settings.grid_height // 2
        body = deque((start_x - offset, start_y) for offset in range(self.settings.starting_length))
        return Snake(body=body, direction=RIGHT, queued_direction=RIGHT)

    def _start_game(self) -> None:
        self.score = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.last_food_name = "普通苹果"
        self.pending_growth = 0
        self.move_timer = 0.0
        self.animation_progress = 1.0
        self.slow_timer = 0.0
        self.screen_flash = 0.0
        self.head_bump = 0.0
        self.particles.clear()
        self.snake = self._new_snake()
        self.previous_body = list(self.snake.body)
        self.food = self._spawn_food()
        self.state = GameState.RUNNING

    def _restart(self) -> None:
        self._start_game()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_keydown(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            if self.state == GameState.RUNNING:
                self.previous_state = self.state
                self.state = GameState.PAUSED
            elif self.state in (GameState.MAP_SELECT, GameState.MODE_SELECT, GameState.HELP, GameState.GAME_OVER):
                self.state = GameState.MAIN_MENU
            else:
                self._quit()
            return

        if self.state == GameState.MAIN_MENU:
            self._handle_menu_input(key, self.main_menu, self._activate_main_menu)
            return
        if self.state == GameState.MAP_SELECT:
            self._handle_menu_input(key, self.map_menu, self._activate_map_menu)
            return
        if self.state == GameState.MODE_SELECT:
            self._handle_menu_input(key, self.mode_menu, self._activate_mode_menu)
            return
        if self.state == GameState.HELP:
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE):
                self.state = GameState.MAIN_MENU
            return
        if self.state == GameState.PAUSED:
            if key in (pygame.K_p, pygame.K_SPACE, pygame.K_RETURN):
                self.state = GameState.RUNNING
            if key == pygame.K_r:
                self._restart()
            return
        if self.state == GameState.GAME_OVER:
            if key in (pygame.K_r, pygame.K_SPACE, pygame.K_RETURN):
                self._restart()
            return

        self._handle_gameplay_input(key)

    def _handle_menu_input(self, key: int, menu: Menu, activate: callable) -> None:
        if key in (pygame.K_UP, pygame.K_w):
            menu.move(-1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            menu.move(1)
        elif pygame.K_1 <= key <= pygame.K_9:
            index = key - pygame.K_1
            if index < len(menu.items):
                menu.select(index)
                activate()
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            activate()

    def _activate_main_menu(self) -> None:
        action = self.main_menu.selected.action
        if action == "start":
            self._start_game()
        elif action == "map":
            self.map_menu.select(self.map_index)
            self.state = GameState.MAP_SELECT
        elif action == "mode":
            self.mode_menu.select(self.mode_index)
            self.state = GameState.MODE_SELECT
        elif action == "help":
            self.state = GameState.HELP
        elif action == "quit":
            self._quit()

    def _activate_map_menu(self) -> None:
        self.map_index = int(self.map_menu.selected.action)
        self.state = GameState.MAIN_MENU

    def _activate_mode_menu(self) -> None:
        self.mode_index = int(self.mode_menu.selected.action)
        self.state = GameState.MAIN_MENU

    def _handle_gameplay_input(self, key: int) -> None:
        if key == pygame.K_p:
            self.previous_state = self.state
            self.state = GameState.PAUSED
            return

        direction_by_key = {
            pygame.K_UP: UP,
            pygame.K_w: UP,
            pygame.K_DOWN: DOWN,
            pygame.K_s: DOWN,
            pygame.K_LEFT: LEFT,
            pygame.K_a: LEFT,
            pygame.K_RIGHT: RIGHT,
            pygame.K_d: RIGHT,
        }
        if key in direction_by_key:
            requested = direction_by_key[key]
            if not self._is_reverse(requested, self.snake.direction):
                self.snake.queued_direction = requested

    def _update(self, delta_time: float) -> None:
        self._update_particles(delta_time)
        self.screen_flash = max(0.0, self.screen_flash - delta_time)
        self.head_bump = max(0.0, self.head_bump - delta_time)
        self.slow_timer = max(0.0, self.slow_timer - delta_time)

        if self.state != GameState.RUNNING:
            return

        self.combo_timer = max(0.0, self.combo_timer - delta_time)
        if self.combo_timer == 0.0:
            self.combo = 0

        self.move_timer += delta_time
        step_delay = self._step_delay()
        self.animation_progress = min(1.0, self.move_timer / step_delay)
        while self.move_timer >= step_delay:
            self.move_timer -= step_delay
            self._advance_snake()
            step_delay = self._step_delay()
            self.animation_progress = min(1.0, self.move_timer / step_delay)
            if self.state == GameState.GAME_OVER:
                break

    def _advance_snake(self) -> None:
        self.previous_body = list(self.snake.body)
        self.snake.direction = self.snake.queued_direction
        next_head = (
            self.snake.head[0] + self.snake.direction[0],
            self.snake.head[1] + self.snake.direction[1],
        )

        if self.current_mode.wrap_walls:
            next_head = self._wrap_point(next_head)
        elif self._hits_outer_wall(next_head):
            self._end_game()
            return

        if next_head in self.current_map.obstacles:
            self._end_game()
            return

        will_eat = next_head == self.food.position
        body_to_check = self.snake.body if will_eat or self.pending_growth > 0 else list(self.snake.body)[:-1]
        if next_head in body_to_check:
            self._end_game()
            return

        self.snake.body.appendleft(next_head)
        if will_eat:
            self._eat_food()
        elif self.pending_growth > 0:
            self.pending_growth -= 1
        else:
            self.snake.body.pop()

    def _eat_food(self) -> None:
        rule = self.food.rule
        bonus = self.current_mode.obstacle_bonus if self.current_map.obstacles else 0
        self.combo = self.combo + 1 if self.combo_timer > 0 else 1
        self.combo_timer = 4.0
        combo_bonus = min(3, self.combo // 3)
        self.score += rule.score + bonus + combo_bonus
        self.last_food_name = rule.name
        self.pending_growth += max(0, rule.grow - 1)
        self.best_score = max(self.best_score, self.score)
        if rule.slow_duration:
            self.slow_timer = rule.slow_duration
        self.head_bump = 0.20
        self._spawn_food_particles(self.food.position, rule.texture_key)
        self.food = self._spawn_food()

    def _spawn_food(self) -> Food:
        occupied = set(self.snake.body) | self.current_map.obstacles
        free_cells = [
            (x, y)
            for y in range(1, self.settings.grid_height - 1)
            for x in range(1, self.settings.grid_width - 1)
            if (x, y) not in occupied
        ]
        if not free_cells:
            self._end_game()
            return Food(self.snake.head, "apple", FOOD_RULES["apple"])

        roll = self.rng.random()
        if roll < self.current_mode.golden_food_chance:
            kind = "gold"
        elif roll < self.current_mode.golden_food_chance + self.current_mode.ice_food_chance:
            kind = "ice"
        else:
            kind = "apple"
        return Food(self.rng.choice(free_cells), kind, FOOD_RULES[kind])

    def _end_game(self) -> None:
        self.state = GameState.GAME_OVER
        self.best_score = max(self.best_score, self.score)
        self.screen_flash = 0.35

    def _step_delay(self) -> float:
        return 1.0 / self._moves_per_second()

    def _moves_per_second(self) -> float:
        speed_bonus = self.score // self.settings.speed_step_score
        speed = self.settings.base_moves_per_second + speed_bonus
        speed *= self.current_mode.speed_multiplier
        if self.slow_timer > 0:
            speed *= 0.72
        return min(speed, self.settings.max_moves_per_second)

    def _hits_outer_wall(self, point: Point) -> bool:
        x, y = point
        return x <= 0 or y <= 0 or x >= self.settings.grid_width - 1 or y >= self.settings.grid_height - 1

    def _wrap_point(self, point: Point) -> Point:
        x, y = point
        if x <= 0:
            x = self.settings.grid_width - 2
        elif x >= self.settings.grid_width - 1:
            x = 1
        if y <= 0:
            y = self.settings.grid_height - 2
        elif y >= self.settings.grid_height - 1:
            y = 1
        return x, y

    def _draw(self) -> None:
        self.screen.fill((24, 28, 34))
        if self.state in (GameState.MAIN_MENU, GameState.MAP_SELECT, GameState.MODE_SELECT, GameState.HELP):
            self._draw_menu_scene()
        else:
            self._draw_board()
            self._draw_food()
            self._draw_snake()
            self._draw_particles()
            self._draw_side_panel()
            self._draw_overlay()
        self._draw_flash()
        pygame.display.flip()

    def _draw_menu_scene(self) -> None:
        self._draw_board(draw_snake_preview=False)
        overlay = pygame.Surface((self.settings.window_width, self.settings.window_height), pygame.SRCALPHA)
        overlay.fill((8, 12, 18, 188))
        self.screen.blit(overlay, (0, 0))

        title = self.large_font.render("程序化贴图贪吃蛇", True, (238, 255, 235))
        subtitle = self.small_font.render("慢速调校 · 多关卡挑战 · 方格感更清晰", True, (166, 204, 178))
        self.screen.blit(title, title.get_rect(center=(self.settings.window_width // 2, 56)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.settings.window_width // 2, 94)))

        if self.state == GameState.MAIN_MENU:
            self._draw_menu(self.main_menu, "主菜单", 158)
            self._draw_menu_footer()
        elif self.state == GameState.MAP_SELECT:
            self._draw_menu(self.map_menu, "选择地图", 140, self._map_descriptions())
        elif self.state == GameState.MODE_SELECT:
            self._draw_menu(self.mode_menu, "选择模式", 156, self._mode_descriptions())
        elif self.state == GameState.HELP:
            self._draw_help()

    def _draw_menu(self, menu: Menu, heading: str, start_y: int, descriptions: list[str] | None = None) -> None:
        heading_surface = self.medium_font.render(heading, True, (255, 239, 192))
        self.screen.blit(heading_surface, heading_surface.get_rect(center=(self.settings.window_width // 2, start_y - 38)))

        compact = len(menu.items) > 5
        width = min(520, self.settings.window_width - 180)
        option_height = 36 if compact else 42
        row_stride = 43 if compact else 52
        x = (self.settings.window_width - width) // 2

        for index, item in enumerate(menu.items):
            y = start_y + index * row_stride
            selected = index == menu.selected_index
            rect = pygame.Rect(x, y, width, option_height)
            fill = (65, 98, 76) if selected else (33, 43, 49)
            border = (150, 226, 132) if selected else (77, 91, 98)
            pygame.draw.rect(self.screen, fill, rect, border_radius=9)
            pygame.draw.rect(self.screen, border, rect, width=2, border_radius=9)

            number_rect = pygame.Rect(rect.x + 14, rect.y + (rect.height - 24) // 2, 32, 24)
            pygame.draw.rect(self.screen, (28, 54, 38), number_rect, border_radius=8)
            number = self.small_font.render(str(index + 1), True, (230, 244, 219))
            self.screen.blit(number, number.get_rect(center=number_rect.center))

            label_color = (244, 252, 239) if selected else (198, 209, 205)
            label = self.font.render(item.label, True, label_color)
            self.screen.blit(label, (rect.x + 60, rect.centery - label.get_height() // 2))

            if selected:
                marker = self.small_font.render("▶", True, (255, 230, 132))
                self.screen.blit(marker, marker.get_rect(center=(rect.right - 28, rect.centery)))

        if descriptions and menu.items:
            selected_index = min(menu.selected_index, len(descriptions) - 1)
            desc_text = descriptions[selected_index]
            desc_y = start_y + (len(menu.items) - 1) * row_stride + option_height + 12
            if desc_y + 42 <= self.settings.window_height - 10:
                desc_width = min(680, self.settings.window_width - 160)
                desc_rect = pygame.Rect((self.settings.window_width - desc_width) // 2, desc_y, desc_width, 38)
                pygame.draw.rect(self.screen, (22, 32, 38), desc_rect, border_radius=10)
                pygame.draw.rect(self.screen, (75, 100, 94), desc_rect, width=1, border_radius=10)
                desc = self.small_font.render(desc_text, True, (184, 203, 193))
                self.screen.blit(desc, desc.get_rect(center=desc_rect.center))

    def _draw_menu_footer(self) -> None:
        lines = [
            f"当前地图：{self.current_map.name}｜{self.current_map.description}",
            f"当前模式：{self.current_mode.name}｜{self.current_mode.description}",
            "↑↓ / W S 选择；Enter / Space / 数字键确认。",
        ]
        y = self.settings.window_height - 88
        max_width = self.settings.window_width - 96
        for line in lines:
            text = self._render_fitted_text(line, self.small_font, (177, 194, 186), max_width)
            self.screen.blit(text, text.get_rect(center=(self.settings.window_width // 2, y)))
            y += 26

    def _render_fitted_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        max_width: int,
    ) -> pygame.Surface:
        surface = font.render(text, True, color)
        if surface.get_width() <= max_width:
            return surface
        scale = max_width / surface.get_width()
        height = max(1, int(surface.get_height() * scale))
        return pygame.transform.smoothscale(surface, (max_width, height))

    def _draw_help(self) -> None:
        lines = [
            "使用方向键或 W A S D 移动。",
            "P 暂停；Esc 暂停或返回菜单；失败后按 R 重新开始。",
            "金苹果加 3 分；冰莓会让蛇短暂减速。",
            "疾速模式起速更快；穿墙模式会把边界变成隧道。",
            "疾速模式下，障碍地图中的食物都会额外加 1 分。",
            "按空格、回车或退格键返回。",
        ]
        x = 205
        y = 168
        heading = self.medium_font.render("玩法说明", True, (255, 239, 192))
        self.screen.blit(heading, (x, y - 48))
        max_width = self.settings.window_width - x - 90
        for line in lines:
            y = self._draw_wrapped_text(line, x, y, max_width, self.font, (225, 235, 226), 34)
            y += 8

    def _draw_wrapped_text(
        self,
        text: str,
        x: int,
        y: int,
        max_width: int,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        line_height: int,
    ) -> int:
        current = ""
        for char in text:
            candidate = current + char
            if current and font.size(candidate)[0] > max_width:
                surface = font.render(current, True, color)
                self.screen.blit(surface, (x, y))
                y += line_height
                current = char
            else:
                current = candidate
        if current:
            surface = font.render(current, True, color)
            self.screen.blit(surface, (x, y))
            y += line_height
        return y

    def _map_descriptions(self) -> list[str]:
        return [map_config.description for map_config in self.maps]

    def _mode_descriptions(self) -> list[str]:
        return [mode.description for mode in MODES]

    def _draw_board(self, draw_snake_preview: bool = True) -> None:
        cell = self.settings.cell_size
        for y in range(self.settings.grid_height):
            for x in range(self.settings.grid_width):
                position = (x * cell, y * cell)
                texture = self.textures["wall_tile"] if self._is_wall_cell(x, y) else self.textures["grass_tile"]
                self.screen.blit(texture, position)

        panel_left = self.settings.board_width
        pygame.draw.rect(
            self.screen,
            (30, 34, 43),
            pygame.Rect(panel_left, 0, self.settings.side_panel_width, self.settings.window_height),
        )
        pygame.draw.line(self.screen, (72, 78, 91), (panel_left, 0), (panel_left, self.settings.window_height), 2)

        if draw_snake_preview:
            return

    def _draw_food(self) -> None:
        pulse = 1.0 + math.sin(pygame.time.get_ticks() / 140.0) * 0.06
        texture = self.textures[self.food.rule.texture_key]
        if pulse != 1.0:
            size = max(1, int(self.settings.cell_size * pulse))
            texture = pygame.transform.smoothscale(texture, (size, size))
        rect = texture.get_rect(center=self._cell_center(self.food.position))
        self.screen.blit(texture, rect)

    def _draw_snake(self) -> None:
        current = list(self.snake.body)
        previous = self._aligned_previous_body(current)
        progress = self.animation_progress if self.state == GameState.RUNNING else 1.0

        for index in range(len(current) - 1, -1, -1):
            segment = current[index]
            old_segment = previous[index] if index < len(previous) else segment
            pixel = self._interpolated_pixel(old_segment, segment, progress)
            is_head = index == 0
            is_tail = index == len(current) - 1

            if is_head:
                texture = self._animated_head_texture()
                texture = self._rotate_for_direction(texture, self.snake.direction)
                if self.head_bump > 0:
                    scale = 1.0 + (self.head_bump / 0.20) * 0.12
                    size = int(self.settings.cell_size * scale)
                    texture = pygame.transform.smoothscale(texture, (size, size))
                    rect = texture.get_rect(center=(pixel[0] + self.settings.cell_size // 2, pixel[1] + self.settings.cell_size // 2))
                    self.screen.blit(texture, rect)
                else:
                    self.screen.blit(texture, pixel)
            elif is_tail:
                direction = self._tail_direction(current)
                texture = self._rotate_for_direction(self.textures["snake_tail"], direction)
                self.screen.blit(texture, pixel)
            else:
                texture = self.textures["snake_body"]
                if self.slow_timer > 0:
                    texture = texture.copy()
                    texture.fill((120, 210, 255, 45), special_flags=pygame.BLEND_RGBA_ADD)
                self.screen.blit(texture, pixel)

    def _draw_particles(self) -> None:
        for particle in self.particles:
            alpha = max(0, min(255, int(255 * (1 - particle.age / particle.lifetime))))
            surface = self.textures["particle"].copy()
            surface.fill((*particle.color, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            rect = surface.get_rect(center=(int(particle.position[0]), int(particle.position[1])))
            self.screen.blit(surface, rect)

    def _draw_side_panel(self) -> None:
        left = self.settings.board_width + 24
        y = 28
        title = self.large_font.render("贪吃蛇", True, (223, 245, 225))
        self.screen.blit(title, (left, y))
        y += 60

        combo_text = f"x{self.combo}" if self.combo > 1 else "-"
        values = (
            ("分数", str(self.score)),
            ("最高", str(self.best_score)),
            ("速度", f"{self._moves_per_second():.0f}x"),
            ("连击", combo_text),
            ("食物", self.last_food_name),
            ("地图", self.current_map.name),
            ("模式", self.current_mode.name),
        )
        for label, value in values:
            self._draw_panel_text(label, value, left, y)
            y += 42

        if self.slow_timer > 0:
            slow = self.small_font.render(f"冰冻减速：{self.slow_timer:.1f} 秒", True, (155, 227, 255))
            self.screen.blit(slow, (left, y + 6))
            y += 28

        if self.combo > 1:
            combo_bonus = min(3, self.combo // 3)
            next_combo = 3 - (self.combo % 3)
            bonus_line = f"当前额外加分：+{combo_bonus}" if combo_bonus else f"再吃 {next_combo} 个触发奖励"
            combo_lines = [f"连击倒计时：{self.combo_timer:.1f} 秒", bonus_line]
            for combo_line in combo_lines:
                combo = self.small_font.render(combo_line, True, (255, 224, 119))
                self.screen.blit(combo, (left, y + 2))
                y += 24

        help_lines = ["移动：方向键 / WASD", "暂停：P 或 Esc", "重开：R", "菜单：Esc"]
        for line in help_lines:
            text = self.small_font.render(line, True, (176, 187, 198))
            self.screen.blit(text, (left, y))
            y += 26

    def _draw_panel_text(self, label: str, value: str, x: int, y: int) -> None:
        label_surface = self.small_font.render(label, True, (140, 151, 164))
        value_surface = self.font.render(value, True, (245, 248, 245))
        self.screen.blit(label_surface, (x, y))
        self.screen.blit(value_surface, (x, y + 21))

    def _draw_overlay(self) -> None:
        if self.state == GameState.RUNNING:
            return

        overlay = pygame.Surface((self.settings.board_width, self.settings.board_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        self.screen.blit(overlay, (0, 0))

        if self.state == GameState.PAUSED:
            title, subtitle = "已暂停", "按 P / 空格继续，按 Esc 返回菜单"
        else:
            title, subtitle = "游戏结束", "按 R / 空格再来一局，按 Esc 返回菜单"

        title_surface = self.large_font.render(title, True, (255, 245, 214))
        subtitle_surface = self.font.render(subtitle, True, (231, 238, 230))
        title_rect = title_surface.get_rect(center=(self.settings.board_width // 2, self.settings.board_height // 2 - 28))
        subtitle_rect = subtitle_surface.get_rect(center=(self.settings.board_width // 2, self.settings.board_height // 2 + 26))
        self.screen.blit(title_surface, title_rect)
        self.screen.blit(subtitle_surface, subtitle_rect)

    def _draw_flash(self) -> None:
        if self.screen_flash <= 0:
            return
        alpha = int(145 * min(1.0, self.screen_flash / 0.35))
        flash = pygame.Surface((self.settings.window_width, self.settings.window_height), pygame.SRCALPHA)
        flash.fill((220, 58, 48, alpha))
        self.screen.blit(flash, (0, 0))

    def _update_particles(self, delta_time: float) -> None:
        alive: list[Particle] = []
        for particle in self.particles:
            particle.age += delta_time
            if particle.age >= particle.lifetime:
                continue
            particle.position = (
                particle.position[0] + particle.velocity[0] * delta_time,
                particle.position[1] + particle.velocity[1] * delta_time,
            )
            alive.append(particle)
        self.particles = alive

    def _spawn_food_particles(self, point: Point, texture_key: str) -> None:
        center = self._cell_center(point)
        color_by_texture = {
            "food": (255, 104, 94),
            "gold_food": (255, 218, 83),
            "ice_food": (138, 228, 255),
        }
        color = color_by_texture.get(texture_key, (255, 240, 140))
        for index in range(12):
            angle = (math.tau / 12) * index
            speed = self.rng.uniform(52, 112)
            self.particles.append(
                Particle(
                    position=(float(center[0]), float(center[1])),
                    velocity=(math.cos(angle) * speed, math.sin(angle) * speed),
                    age=0.0,
                    lifetime=self.rng.uniform(0.28, 0.52),
                    color=color,
                )
            )

    def _animated_head_texture(self) -> pygame.Surface:
        phase = (pygame.time.get_ticks() // 140) % 12
        if phase == 0:
            return self.textures["snake_head_blink"]
        if phase in (5, 6):
            return self.textures["snake_head_tongue"]
        return self.textures["snake_head"]

    def _aligned_previous_body(self, current: list[Point]) -> list[Point]:
        if not self.previous_body:
            return current
        previous = list(self.previous_body)
        if len(previous) < len(current):
            previous.extend([previous[-1]] * (len(current) - len(previous)))
        return previous[: len(current)]

    def _interpolated_pixel(self, start: Point, end: Point, progress: float) -> tuple[int, int]:
        cell = self.settings.cell_size
        if abs(end[0] - start[0]) > 1 or abs(end[1] - start[1]) > 1:
            return end[0] * cell, end[1] * cell
        x = (start[0] + (end[0] - start[0]) * progress) * cell
        y = (start[1] + (end[1] - start[1]) * progress) * cell
        return int(round(x)), int(round(y))

    def _cell_center(self, point: Point) -> tuple[int, int]:
        cell = self.settings.cell_size
        return point[0] * cell + cell // 2, point[1] * cell + cell // 2

    def _is_wall_cell(self, x: int, y: int) -> bool:
        return self._is_border_cell(x, y) or (x, y) in self.current_map.obstacles

    def _is_border_cell(self, x: int, y: int) -> bool:
        return x == 0 or y == 0 or x == self.settings.grid_width - 1 or y == self.settings.grid_height - 1

    def _tail_direction(self, body: list[Point]) -> Direction:
        if len(body) < 2:
            return self.snake.direction
        tail = body[-1]
        before_tail = body[-2]
        return self._normalize_direction((before_tail[0] - tail[0], before_tail[1] - tail[1]))

    def _normalize_direction(self, direction: Direction) -> Direction:
        dx, dy = direction
        if dx > 1:
            return LEFT
        if dx < -1:
            return RIGHT
        if dy > 1:
            return UP
        if dy < -1:
            return DOWN
        if direction in (UP, DOWN, LEFT, RIGHT):
            return direction
        return self.snake.direction if self.snake.direction in (UP, DOWN, LEFT, RIGHT) else RIGHT

    def _rotate_for_direction(self, texture: pygame.Surface, direction: Direction) -> pygame.Surface:
        direction = self._normalize_direction(direction)
        angle_by_direction = {
            UP: 0,
            RIGHT: -90,
            DOWN: 180,
            LEFT: 90,
        }
        return pygame.transform.rotate(texture, angle_by_direction[direction])

    @staticmethod
    def _is_reverse(first: Direction, second: Direction) -> bool:
        return first[0] + second[0] == 0 and first[1] + second[1] == 0

    @staticmethod
    def _quit() -> None:
        pygame.quit()
        sys.exit()
