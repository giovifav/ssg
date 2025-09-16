"""Simple text input modal."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual import events
from textual.widgets import Button, Input, Label
from textual.containers import Vertical, Horizontal
from .utils import set_card_titles


class TextInputModal(ModalScreen[str]):
    """A modal dialog to get text input from the user."""

    def __init__(self, title: str, prompt: str, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.title_text = title
        self.prompt_text = prompt

    def compose(self) -> ComposeResult:  # type: ignore[override]
        """Compose the simple text input modal UI."""
        with Vertical(id="modal-dialog"):
            # Bordered card wrapper for consistency with menu/wizard
            with Vertical(id="text-input-card", classes="panel"):
                yield Input(placeholder="Enter name", id="modal-input")
                with Horizontal(id="modal-buttons"):
                    yield Button("Confirm", id="modal-confirm")
                    yield Button("Cancel", id="modal-cancel")

    def on_mount(self) -> None:  # type: ignore[override]
        # Apply border title and subtitle to the card using the provided title/prompt
        try:
            card = self.query_one("#text-input-card")
            subtitle = self.prompt_text.strip()
            if len(subtitle) > 60:
                subtitle = subtitle[:57] + "..."
            set_card_titles(card, self.title_text, subtitle)
        except Exception:
            pass
        self.query_one("#modal-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        if event.button.id == "modal-confirm":
            input_value = self.query_one("#modal-input", Input).value.strip()
            self.dismiss(input_value)
        elif event.button.id == "modal-cancel":
            self.dismiss("")

    async def on_input_submitted(self, event: Input.Submitted) -> None:  # type: ignore[override]
        self.dismiss(event.value.strip())
