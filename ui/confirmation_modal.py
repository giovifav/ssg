"""Simple confirmation modal with message display."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.containers import Vertical, Horizontal
from .utils import set_card_titles


class ConfirmationModal(ModalScreen[bool | None]):
    """Modal dialog to display a message and get user confirmation.

    Returns True if confirmed, False if cancelled, None if dismissed.
    """

    def __init__(self, title: str, message: str, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.title_text = title
        self.message_text = message

    def compose(self) -> ComposeResult:  # type: ignore[override]
        """Compose the confirmation modal with message and buttons."""
        from i18n import translate
        with Vertical(id="modal-dialog"):
            # Bordered card wrapper for consistency with menu/wizard
            with Vertical(id="confirmation-card", classes="panel"):
                yield Label(self.message_text, id="confirm-message")
                with Horizontal(id="modal-buttons"):
                    yield Button(translate("confirm"), id="confirm-btn")
                    yield Button(translate("cancel"), id="cancel-btn")

    def on_mount(self) -> None:  # type: ignore[override]
        from i18n import translate
        # Apply border title and subtitle to the card
        try:
            card = self.query_one("#confirmation-card")
            subtitle = "Conferma l'operazione"  # Could make this configurable
            if len(subtitle) > 60:
                subtitle = subtitle[:57] + "..."
            set_card_titles(card, self.title_text, subtitle)
        except Exception:
            pass
        # Focus the confirm button by default
        self.query_one("#confirm-btn", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        if event.button.id == "confirm-btn":
            self.dismiss(True)
        elif event.button.id == "cancel-btn":
            self.dismiss(False)
