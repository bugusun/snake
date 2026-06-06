"""Shared configuration for the Snake game."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_ROOT / "assets" / "generated"


@dataclass(frozen=True)
class Settings:
    title: str = "程序化贴图贪吃蛇"
    cell_size: int = 32
    grid_width: int = 22
    grid_height: int = 16
    side_panel_width: int = 260
    fps: int = 60
    base_moves_per_second: float = 5.8
    speed_step_score: int = 6
    max_moves_per_second: float = 12.0
    starting_length: int = 4

    @property
    def board_width(self) -> int:
        return self.grid_width * self.cell_size

    @property
    def board_height(self) -> int:
        return self.grid_height * self.cell_size

    @property
    def window_width(self) -> int:
        return self.board_width + self.side_panel_width

    @property
    def window_height(self) -> int:
        return self.board_height


SETTINGS = Settings()
