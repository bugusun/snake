"""Programmatic PNG texture generation and loading."""

from __future__ import annotations

import random
from pathlib import Path

import pygame

from snake_game.settings import ASSET_DIR, SETTINGS


TEXTURE_FILES = {
    "snake_head": "snake_head.png",
    "snake_head_blink": "snake_head_blink.png",
    "snake_head_tongue": "snake_head_tongue.png",
    "snake_body": "snake_body.png",
    "snake_tail": "snake_tail.png",
    "food": "food.png",
    "gold_food": "gold_food.png",
    "ice_food": "ice_food.png",
    "grass_tile": "grass_tile.png",
    "wall_tile": "wall_tile.png",
    "particle": "particle.png",
}


def ensure_generated_textures(asset_dir: Path = ASSET_DIR) -> None:
    """Create or refresh all program-generated texture PNG files."""

    asset_dir.mkdir(parents=True, exist_ok=True)
    size = SETTINGS.cell_size

    generators = {
        "snake_head": _make_snake_head,
        "snake_head_blink": _make_snake_head_blink,
        "snake_head_tongue": _make_snake_head_tongue,
        "snake_body": _make_snake_body,
        "snake_tail": _make_snake_tail,
        "food": _make_food,
        "gold_food": _make_gold_food,
        "ice_food": _make_ice_food,
        "grass_tile": _make_grass_tile,
        "wall_tile": _make_wall_tile,
        "particle": _make_particle,
    }

    for texture_name, generator in generators.items():
        target = asset_dir / TEXTURE_FILES[texture_name]
        surface = generator(size)
        pygame.image.save(surface, str(target))


def load_textures(asset_dir: Path = ASSET_DIR) -> dict[str, pygame.Surface]:
    """Load generated textures as alpha-aware surfaces."""

    ensure_generated_textures(asset_dir)
    return {
        name: pygame.image.load(str(asset_dir / filename)).convert_alpha()
        for name, filename in TEXTURE_FILES.items()
    }


def _make_surface(size: int, color: tuple[int, int, int, int] = (0, 0, 0, 0)) -> pygame.Surface:
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    surface.fill(color)
    return surface


def _make_snake_head(size: int) -> pygame.Surface:
    surface = _make_surface(size)
    body = pygame.Rect(3, 3, size - 6, size - 6)
    pygame.draw.rect(surface, (28, 145, 66), body, border_radius=10)
    pygame.draw.rect(surface, (12, 96, 45), body, width=3, border_radius=10)
    pygame.draw.arc(surface, (75, 205, 101), pygame.Rect(7, 6, size - 14, size - 13), 3.7, 5.8, 3)

    pygame.draw.circle(surface, (245, 255, 246), (size // 2 - 6, size // 2 - 5), 4)
    pygame.draw.circle(surface, (245, 255, 246), (size // 2 + 6, size // 2 - 5), 4)
    pygame.draw.circle(surface, (16, 44, 22), (size // 2 - 5, size // 2 - 5), 2)
    pygame.draw.circle(surface, (16, 44, 22), (size // 2 + 5, size // 2 - 5), 2)
    pygame.draw.arc(surface, (9, 65, 33), pygame.Rect(10, 13, size - 20, 10), 0.2, 2.9, 2)
    return surface


def _make_snake_head_blink(size: int) -> pygame.Surface:
    surface = _make_snake_head(size)
    pygame.draw.rect(surface, (28, 145, 66), pygame.Rect(size // 2 - 12, size // 2 - 10, 24, 9))
    pygame.draw.line(surface, (11, 61, 29), (size // 2 - 10, size // 2 - 5), (size // 2 - 3, size // 2 - 5), 2)
    pygame.draw.line(surface, (11, 61, 29), (size // 2 + 3, size // 2 - 5), (size // 2 + 10, size // 2 - 5), 2)
    return surface


def _make_snake_head_tongue(size: int) -> pygame.Surface:
    surface = _make_snake_head(size)
    pygame.draw.line(surface, (224, 65, 96), (size // 2, size - 9), (size // 2, size - 1), 2)
    pygame.draw.line(surface, (224, 65, 96), (size // 2, size - 1), (size // 2 - 4, size + 3), 2)
    pygame.draw.line(surface, (224, 65, 96), (size // 2, size - 1), (size // 2 + 4, size + 3), 2)
    return surface


def _make_snake_body(size: int) -> pygame.Surface:
    surface = _make_surface(size)
    body = pygame.Rect(2, 2, size - 4, size - 4)
    pygame.draw.rect(surface, (37, 171, 76), body, border_radius=6)
    pygame.draw.rect(surface, (12, 92, 43), body, width=3, border_radius=6)
    pygame.draw.line(surface, (95, 224, 119), (5, 5), (size - 6, 5), 2)
    pygame.draw.line(surface, (21, 123, 54), (5, size - 5), (size - 6, size - 5), 2)
    pygame.draw.arc(surface, (103, 232, 129), pygame.Rect(7, 7, size - 14, size - 14), 3.7, 5.6, 3)

    rng = random.Random(312)
    for _ in range(6):
        point = (rng.randrange(6, size - 6), rng.randrange(8, size - 6))
        pygame.draw.rect(surface, (63, 190, 86, 150), pygame.Rect(point[0], point[1], 3, 3), border_radius=1)
    return surface


def _make_snake_tail(size: int) -> pygame.Surface:
    surface = _make_surface(size)
    points = [(size // 2, 3), (size - 3, size - 8), (size - 3, size - 3), (3, size - 3), (3, size - 8)]
    pygame.draw.polygon(surface, (36, 151, 68), points)
    pygame.draw.polygon(surface, (14, 99, 47), points, width=3)
    pygame.draw.line(surface, (90, 216, 112), (7, size - 8), (size - 8, size - 8), 2)
    pygame.draw.circle(surface, (71, 203, 100), (size // 2, size // 2 + 3), size // 5)
    return surface


def _make_food(size: int) -> pygame.Surface:
    surface = _make_surface(size)
    pygame.draw.circle(surface, (211, 39, 46), (size // 2 - 3, size // 2 + 2), 10)
    pygame.draw.circle(surface, (232, 58, 54), (size // 2 + 5, size // 2 + 2), 10)
    pygame.draw.circle(surface, (145, 20, 34), (size // 2 + 1, size // 2 + 4), 12, width=2)
    pygame.draw.rect(surface, (97, 58, 28), pygame.Rect(size // 2 - 1, 4, 4, 9), border_radius=2)
    pygame.draw.ellipse(surface, (54, 163, 66), pygame.Rect(size // 2 + 3, 5, 12, 7))
    pygame.draw.circle(surface, (255, 184, 181), (size // 2 - 6, size // 2 - 3), 3)
    return surface


def _make_gold_food(size: int) -> pygame.Surface:
    surface = _make_surface(size)
    pygame.draw.circle(surface, (238, 175, 38), (size // 2, size // 2 + 2), 11)
    pygame.draw.circle(surface, (255, 221, 92), (size // 2 - 3, size // 2 - 2), 9)
    pygame.draw.circle(surface, (160, 104, 22), (size // 2, size // 2 + 2), 12, width=2)
    pygame.draw.polygon(surface, (255, 247, 180), [(size // 2 - 2, 7), (size // 2 + 2, 14), (size // 2 - 6, 14)])
    pygame.draw.circle(surface, (255, 250, 202), (size // 2 - 5, size // 2 - 5), 3)
    return surface


def _make_ice_food(size: int) -> pygame.Surface:
    surface = _make_surface(size)
    diamond = [(size // 2, 4), (size - 6, size // 2), (size // 2, size - 4), (6, size // 2)]
    pygame.draw.polygon(surface, (104, 208, 238), diamond)
    pygame.draw.polygon(surface, (35, 126, 177), diamond, width=2)
    pygame.draw.line(surface, (215, 250, 255), (size // 2, 7), (size // 2, size - 8), 2)
    pygame.draw.line(surface, (215, 250, 255), (9, size // 2), (size - 9, size // 2), 2)
    pygame.draw.circle(surface, (238, 255, 255), (size // 2 - 4, size // 2 - 5), 3)
    return surface


def _make_grass_tile(size: int) -> pygame.Surface:
    surface = _make_surface(size, (39, 91, 54, 255))
    pygame.draw.rect(surface, (44, 102, 60), pygame.Rect(0, 0, size, size), 0)
    pygame.draw.rect(surface, (30, 72, 46), pygame.Rect(0, 0, size, size), width=1)
    pygame.draw.line(surface, (54, 116, 67), (1, 1), (size - 2, 1), 1)
    pygame.draw.line(surface, (30, 72, 46), (1, size - 2), (size - 2, size - 2), 1)

    rng = random.Random(20260509)
    for _ in range(20):
        x = rng.randrange(0, size)
        y = rng.randrange(0, size)
        color = rng.choice([(52, 121, 68), (31, 74, 47), (62, 135, 75)])
        pygame.draw.line(surface, color, (x, y), (min(size, x + rng.randrange(2, 5)), y + 1), 1)
    return surface


def _make_wall_tile(size: int) -> pygame.Surface:
    surface = _make_surface(size, (89, 91, 98, 255))
    pygame.draw.rect(surface, (67, 69, 78), pygame.Rect(0, 0, size, size), width=3)
    pygame.draw.line(surface, (116, 119, 129), (0, size // 2), (size, size // 2), 2)
    pygame.draw.line(surface, (65, 67, 75), (size // 2, 0), (size // 2, size // 2), 2)
    pygame.draw.line(surface, (65, 67, 75), (size // 3, size // 2), (size // 3, size), 2)

    rng = random.Random(42)
    for _ in range(12):
        shade = rng.randrange(78, 130)
        pygame.draw.circle(surface, (shade, shade, shade + 6), (rng.randrange(4, size - 4), rng.randrange(4, size - 4)), 1)
    return surface


def _make_particle(size: int) -> pygame.Surface:
    surface = _make_surface(size)
    pygame.draw.circle(surface, (255, 239, 148, 220), (size // 2, size // 2), 4)
    pygame.draw.circle(surface, (255, 255, 226, 240), (size // 2 - 1, size // 2 - 1), 2)
    return surface
