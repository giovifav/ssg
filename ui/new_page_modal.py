"""New page creation modal."""

from __future__ import annotations

from pathlib import Path
from datetime import date

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label
from textual.containers import Vertical, Horizontal
from .utils import set_card_titles


class NewPageModal(ModalScreen[dict | None]):
    """Modal to create a new Markdown page with front matter.

    Returns a dict with keys: name, title, date; or None if cancelled.
    """

    def __init__(self, default_name: str = "", default_title: str = "", default_date: str | None = None, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        from datetime import date as _date
        self.default_name = default_name
        self.default_title = default_title
        self.default_date = default_date or _date.today().isoformat()

    def compose(self) -> ComposeResult:  # type: ignore[override]
        """Compose the new page modal with fields for name, title, and date."""
        from i18n import translate
        with Vertical(id="modal-dialog"):
            # Bordered card wrapper for consistency with menu/wizard
            with Vertical(id="new-page-card", classes="panel"):
                # Fieldset only; description moved to border subtitle
                yield Label(translate("file_name"), id="lbl-name")
                yield Input(placeholder=translate("file_name_placeholder"), id="np-name")
                yield Label(translate("page_title"), id="lbl-title")
                yield Input(placeholder=translate("page_title_placeholder"), id="np-title")
                yield Label(translate("date"), id="lbl-date")
                yield Input(placeholder=translate("date_placeholder"), id="np-date")
                with Horizontal(id="modal-buttons"):
                    yield Button(translate("create"), id="np-confirm")
                    yield Button(translate("cancel"), id="np-cancel")

    def on_mount(self) -> None:  # type: ignore[override]
        from i18n import translate
        # Apply border title and a concise subtitle
        try:
            card = self.query_one("#new-page-card")
            subtitle = translate("new_page_modal_guide")
            if len(subtitle) > 60:
                subtitle = subtitle[:57] + "..."
            set_card_titles(card, translate("new_page_modal_title"), subtitle)
        except Exception:
            pass
        self.query_one("#np-name", Input).value = self.default_name
        self.query_one("#np-title", Input).value = self.default_title
        self.query_one("#np-date", Input).value = self.default_date
        self.query_one("#np-name", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        if event.button.id == "np-confirm":
            name = self.query_one("#np-name", Input).value.strip()
            title = self.query_one("#np-title", Input).value.strip()
            date_value = self.query_one("#np-date", Input).value.strip()
            if not name:
                self.dismiss(None)
                return
            if not name.lower().endswith(".md"):
                name += ".md"
            self.dismiss({"name": name, "title": title or Path(name).stem.replace("-", " "), "date": date_value})
        elif event.button.id == "np-cancel":
            self.dismiss(None)
