from __future__ import annotations

from typing import Final


THEME_OPTIONS: Final[list[dict[str, str]]] = [
    {"id": "neo-brutalism", "label": "Neo Brutalism"},
    {"id": "glassmorphism", "label": "Glassmorphism"},
    {"id": "bootstrap-light", "label": "Bootstrap Light"},
    {"id": "glassbox-dark", "label": "Glassbox Dark"},
    {"id": "fortinet", "label": "Fortinet"},
]

THEME_IDS: Final[set[str]] = {theme["id"] for theme in THEME_OPTIONS}
DEFAULT_THEME: Final[str] = "neo-brutalism"


def normalize_theme(theme: str | None) -> str:
    if theme in THEME_IDS:
        return theme
    return DEFAULT_THEME
