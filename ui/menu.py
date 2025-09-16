"""Main menu components with modern grid layout."""

from __future__ import annotations

from textual.widgets import Button, Label, Static
from textual.containers import Horizontal, Grid, Container
from .utils import set_card_titles


class MainMenu(Container):
    """Main menu with modern grid layout and icons."""

    # Local (screen-only) key bindings for Footer
    BINDINGS = [
        ("n", "new_site", "New"),
        ("o", "open_site", "Open"),
    ]

    def compose(self) -> None:  # type: ignore[override]
        from i18n import translate
        # Bordered card wrapper
        with Container(id="menu-card", classes="panel"):
            # Header moved to border title

            with Grid(id="menu-grid", classes="grid-2x2"):
                # Pulsante 1: Nuovo sito
                with Horizontal(classes="menu-card"):
                    self.init_button = Button(translate("menu_new_site"), id="init", classes="menu-button")
                    yield self.init_button

                # Pulsante 2: Apri sito
                with Horizontal(classes="menu-card"):
                    self.open_button = Button(translate("menu_open_site"), id="open_site", classes="menu-button")
                    yield self.open_button

                # Pulsante 3: Tema
                with Horizontal(classes="menu-card"):
                    self.theme_button = Button(translate("menu_theme"), id="choose_theme", classes="menu-button")
                    yield self.theme_button

                # Pulsante 4: Lingua
                with Horizontal(classes="menu-card"):
                    self.language_button = Button(translate("menu_language"), id="choose_language", classes="menu-button")
                    yield self.language_button

        # Footer hint removed; Footer widget shows key bindings

    def on_show(self) -> None:  # type: ignore[override]
        """Initialize menu focus and styling when the screen becomes visible."""
        from i18n import translate
        # Apply border title and subtitle to the card
        try:
            card = self.query_one("#menu-card")
            subtitle = translate("menu_shortcuts_hint")
            if len(subtitle) > 80:
                subtitle = subtitle[:77] + "..."
            set_card_titles(card, translate("menu_choose_action"), subtitle)
        except Exception:
            pass
        self.update_button_content()
        # Keep focus on the container so Footer shows local bindings
        try:
            self.focus()
        except Exception:
            pass

    def update_button_content(self) -> None:
        """Update button labels (kept for compatibility)."""
        from i18n import translate
        try:
            if hasattr(self, 'init_button'):
                self.init_button.label = translate("menu_new_site")
            if hasattr(self, 'open_button'):
                self.open_button.label = translate("menu_open_site")
            if hasattr(self, 'theme_button'):
                self.theme_button.label = translate("menu_theme")
            if hasattr(self, 'language_button'):
                self.language_button.label = translate("menu_language")
        except Exception:
            pass  # Safe no-op if widgets not mounted yet

    # Actions used by local key bindings
    def action_new_site(self) -> None:
        try:
            for child in list(self.app.body.children):  # type: ignore[attr-defined]
                child.remove()
            from .wizard import InitWizard
            self.app.body.mount(InitWizard())  # type: ignore[attr-defined]
        except Exception:
            pass

    def action_open_site(self) -> None:
        try:
            for child in list(self.app.body.children):  # type: ignore[attr-defined]
                child.remove()
            from .site_actions import SiteActions
            self.app.body.mount(SiteActions())  # type: ignore[attr-defined]
        except Exception:
            pass
