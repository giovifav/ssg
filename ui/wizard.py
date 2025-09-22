"""Compact single-column wizard for initializing new sites (English), with screen-specific keybindings.

- Layout: single column inside a bordered card
- Keybindings (shown in the app's Footer):
  - b: Browse Base
  - c: Create Site
  - Backspace: Back to Menu
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button, Input, Label, Static, OptionList
from textual.widgets.option_list import Option
from textual.containers import Vertical, Horizontal, Container
from .utils import set_card_titles


class InitWizard(Container):
    """Single-column wizard for creating new sites with directory picker."""

    # Screen-specific keybindings; shown by the global Footer when available
    BINDINGS = [
        Binding("b", "browse_base", "Browse Base"),
        Binding("c", "create_site", "Create Site"),
        Binding("backspace", "back", "Back"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:  # type: ignore[override]
        from i18n import translate
        # Apply border title to the card
        try:
            card = self.query_one("#wizard-card")
            subtitle = translate("new_site_guide")
            if len(subtitle) > 60:
                subtitle = subtitle[:57] + "..."
            set_card_titles(card, translate("new_site_title"), subtitle)
        except Exception:
            pass

    def compose(self) -> ComposeResult:  # type: ignore[override]
        """Compose a compact single-column wizard layout."""
        from i18n import translate
        with Vertical(id="wizard-layout"):
            # Bordered card wrapper for the whole form
            with Vertical(id="wizard-card", classes="panel"):
                # Header / help moved to border title

                # Fields (single column)
                with Vertical(classes="field-container"):
                    yield Label(translate("site_folder_name"), classes="text-label")
                    yield Input(
                        placeholder=translate("site_folder_placeholder"),
                        id="site_folder",
                        classes="wizard-input",
                    )

                with Vertical(classes="field-container"):
                    yield Label(translate("base_directory"), classes="text-label")
                    with Horizontal():
                        yield Input(
                            value=str(getattr(self.app, "config_manager", None).get_last_base_dir() if getattr(self.app, "config_manager", None) else Path.home()),
                            id="base_path",
                            classes="wizard-input",
                        )
                        yield Button(translate("browse"), id="browse_base", classes="btn-secondary")

                with Vertical(classes="field-container"):
                    yield Label(translate("site_display_name"), classes="text-label")
                    yield Input(
                        placeholder=translate("site_display_placeholder"),
                        id="site_name",
                        classes="wizard-input",
                    )

                with Vertical(classes="field-container"):
                    yield Label(translate("author_optional"), classes="text-label")
                    yield Input(
                        placeholder=translate("author_placeholder"),
                        id="author",
                        classes="wizard-input",
                    )

                with Vertical(classes="field-container"):
                    yield Label(translate("theme_selection"), classes="text-label")
                    yield OptionList(
                        Option("Moderno", "moderno"),
                        Option("Semplice", "semplice"),
                        Option("98", "98"),
                        id="theme_selection_optionlist",
                        classes="wizard-input",
                        initial_index=0,
                    )

                # Actions
                with Horizontal(classes="button-group"):
                    yield Button(translate("back_to_menu"), id="back", classes="btn-secondary")
                    yield Button(translate("create_site"), id="create_site", classes="btn-primary")

    # -------------------------- Keybinding actions -------------------------- #

    def action_browse_base(self) -> None:
        """Keybinding: Open the folder picker for Base Directory."""
        self._open_directory_picker()

    def action_create_site(self) -> None:
        """Keybinding: Trigger site creation."""
        self._create_site()

    def action_back(self) -> None:
        """Keybinding: Go back to the main menu."""
        self.app.show_main_menu()  # type: ignore[attr-defined]

    # -------------------------- UI events ---------------------------------- #

    def on_button_pressed(self, event) -> None:  # type: ignore[override]
        """Handle button press events for the wizard."""
        button_id = event.button.id

        if button_id == "browse_base":
            # Avoid double handling: open picker here and stop event bubbling to App
            self._open_directory_picker()
            try:
                event.stop()
            except Exception:
                pass

        elif button_id == "create_site":
            self._create_site()

        elif button_id == "back":
            self.app.show_main_menu()  # type: ignore[attr-defined]

    # -------------------------- Helpers ------------------------------------ #

    def _open_directory_picker(self) -> None:
        """Open the app's folder picker and write the result into #base_path."""
        try:
            # Delegate to the app helper to ensure consistent modal handling
            self.app.pick_folder_into("#base_path")  # type: ignore[attr-defined]
        except Exception as e:  # Fallback with log in case of issues
            try:
                self.app.ui_log.write(f"Error opening folder picker: {e}")  # type: ignore[attr-defined]
            except Exception:
                pass

    def _create_site(self) -> None:
        """Validates fields and creates the new site."""
        from textual.widgets import Input

        # Get field values
        folder_name = self.query_one("#site_folder", Input).value.strip()
        base_path = self.query_one("#base_path", Input).value.strip()
        site_name = self.query_one("#site_name", Input).value.strip()
        author = self.query_one("#author", Input).value.strip()

        # Get selected theme
        option_list = self.query_one("#theme_selection_optionlist", OptionList)
        selected_index = option_list.highlighted_index or 0
        selected_option = option_list.get_option(selected_index)
        selected_theme = selected_option.value or "moderno"

        # Validation
        from i18n import translate
        if not folder_name:
            self.app.ui_log.write(translate("log_messages.folder_required"))  # type: ignore[attr-defined]
            return

        if not base_path:
            self.app.ui_log.write(translate("log_messages.base_path_required"))  # type: ignore[attr-defined]
            return

        # Use site name or fallback to folder name
        display_name = site_name or folder_name

        try:
            # Initialize the site
            try:
                from initialization import initialize_site
                site_root = initialize_site(Path(base_path).expanduser().resolve(), folder_name, display_name, author, selected_theme)
            except ImportError:
                from ..initialization import initialize_site
                site_root = initialize_site(Path(base_path).expanduser().resolve(), folder_name, display_name, author, selected_theme)

            # Persist site and base dir
            try:
                self.app.config_manager.set_last_site_path(site_root)  # type: ignore[attr-defined]
                self.app.config_manager.set_last_base_dir(Path(base_path).expanduser().resolve())  # type: ignore[attr-defined]
            except Exception:
                pass

            # Log success and return to main menu
            self.app.ui_log.write(f"Site created successfully at: {site_root}")  # type: ignore[attr-defined]
            self.app.show_main_menu()  # type: ignore[attr-defined]

        except Exception as e:
            self.app.ui_log.write(f"Error creating site: {e}")  # type: ignore[attr-defined]
