"""UI utility helpers for common behaviors across screens/modals."""
from __future__ import annotations

from typing import Any


def set_card_titles(card: Any, title: str, subtitle: str) -> None:
    """Set border title and subtitle on a card-like widget.

    Uses setattr to avoid coupling to specific Textual versions.
    """
    try:
        setattr(card, "border_title", title)
        setattr(card, "border_subtitle", subtitle)
    except Exception:
        # Graceful no-op if card doesn't support these attributes
        pass