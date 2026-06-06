"""Small keyboard menu helpers for the Snake game."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MenuItem:
    label: str
    action: str


class Menu:
    """A minimal vertical menu with wrap-around selection."""

    def __init__(self, items: list[MenuItem]) -> None:
        self.items = items
        self.selected_index = 0

    @property
    def selected(self) -> MenuItem:
        return self.items[self.selected_index]

    def move(self, offset: int) -> None:
        self.selected_index = (self.selected_index + offset) % len(self.items)

    def select(self, index: int) -> None:
        self.selected_index = index % len(self.items)

