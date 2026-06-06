"""Chinese-friendly font loading helpers."""

from __future__ import annotations

import pygame


FONT_CANDIDATES = (
    "Microsoft YaHei",
    "SimHei",
    "SimSun",
    "Noto Sans CJK SC",
    "Noto Sans SC",
    "WenQuanYi Micro Hei",
    "Arial Unicode MS",
)


def load_ui_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Load a UI font that can render Chinese on common systems."""

    font_path = None
    for candidate in FONT_CANDIDATES:
        font_path = pygame.font.match_font(candidate, bold=bold)
        if font_path:
            break

    font = pygame.font.Font(font_path, size) if font_path else pygame.font.Font(None, size)
    font.set_bold(bold)
    return font

