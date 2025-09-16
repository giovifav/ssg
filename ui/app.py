"""Main TUI application."""

from __future__ import annotations

import sys
import os
import webbrowser

# Ensure we can import from the parent directory
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll

from .log import UILog
from .menu import MainMenu
from .wizard import InitWizard
from .editor import SiteEditorScreen
from .site_actions import SiteActions, FolderPicker

# Import top-level modules - use absolute imports
from site_generator import generate_site
from initialization import initialize_site

# User config manager
from config_manager import ConfigManager

# Import path adjustments will be updated when we create __init__.py


class SSGApp(App):
    """Textual TUI for Gio's static site generator.

    The app provides two main actions: initialize a new site and generate a
    site from an existing project directory.
    """

    # Use absolute path resolution relative to this file to ensure CSS loads
    CSS_PATH = str(Path(__file__).with_name("UItheme.css"))

    def compose(self) -> ComposeResult:  # type: ignore[override]
        """Compose the main application layout with header, body, log and footer."""
        from textual.widgets import Header, Footer
        yield Header(show_clock=True)
        with Vertical():
            self.body = Vertical(id="app-body")
            yield self.body
            with VerticalScroll(id="log-container"):
                self.ui_log = UILog()
                yield self.ui_log
        yield Footer()

    def on_mount(self) -> None:  # type: ignore[override]
        """Initialize the app at startup and show the main menu."""
        # Load user config and apply theme and language
        self.config_manager = ConfigManager()
        try:
            self.theme = self.config_manager.get_theme()
        except Exception as e:
            self.ui_log.write(f"Warning: Failed to load theme, using default (gruvbox): {e}")
            self.theme = "gruvbox"

        # Initialize i18n with saved language
        try:
            language = self.config_manager.get_language()
            from i18n import set_global_language
            set_global_language(language)
        except Exception as e:
            # Fall back to default language (English) if there's any error
            self.ui_log.write(f"Warning: Failed to load language, using default (English): {e}")

        # Responsive logic disabled to test base layout
        self.show_main_menu()



    def show_main_menu(self) -> None:
        """Show the main menu screen, replacing any current view."""
        for child in list(self.body.children):
            child.remove()
        self.body.mount(MainMenu())



    async def on_button_pressed(self, event) -> None:  # type: ignore[override]
        """Route button clicks from child screens to the appropriate handlers."""
        from textual.widgets import Button
        # type: ignore[override]
        button_pressed_event = event  # Reassign for type checking
        btn_id = button_pressed_event.button.id or ""
        if btn_id == "init":
            for child in list(self.body.children):
                child.remove()
            self.body.mount(InitWizard())
        elif btn_id == "open_site":
            for child in list(self.body.children):
                child.remove()
            self.body.mount(SiteActions())
        elif btn_id == "back":
            self.show_main_menu()
        elif btn_id == "create":
            self.handle_create()
        elif btn_id == "go":
            self.handle_generate()
        elif btn_id == "edit_selected_site":
            self.handle_edit_site()
        elif btn_id == "choose_theme":
            self.open_theme_picker()
        elif btn_id == "choose_language":
            self.open_language_picker()
        elif btn_id in ("browse_base", "w_browse_base"):
            # Handle wizard directory picker - check for new wizard first, then old ones
            if btn_id == "browse_base":
                self.pick_folder_into("#base_path")
            elif btn_id == "w_browse_base":
                self.pick_folder_into("#w_base")
        elif btn_id == "browse_site":
            self.pick_folder_into("#sitepath")

    # -------------------------- Actions ---------------------------------- #

    def handle_create(self) -> None:
        """Handle initialization form submission."""
        from textual.widgets import Input
        # type: ignore[arg-type]
        folder = self.query_one("#folder", Input).value.strip()
        base = self.query_one("#base", Input).value.strip()  # type: ignore[arg-type]
        sitename = self.query_one("#sitename", Input).value.strip()  # type: ignore[arg-type]
        author = self.query_one("#author", Input).value.strip()  # type: ignore[arg-type]

        if not folder:
            self.ui_log.write("Folder name is required.")
            return
        if not base:
            self.ui_log.write("Base path is required.")
            return

        base_path = Path(base).expanduser().resolve()
        try:
            site_root = initialize_site(base_path, folder, sitename or folder, author or "")
            self.ui_log.write(f"Site created at: {site_root}")
            # Persist newly created site and base directory
            try:
                self.config_manager.set_last_site_path(site_root)
                self.config_manager.set_last_base_dir(base_path)
            except Exception as e:
                self.ui_log.write(f"Warning: Failed to save site preferences: {e}")
        except Exception as e:  # pragma: no cover - UI error path
            self.ui_log.write(f"Error: {e}")

    def handle_edit_site(self) -> None:
        """Handles launching the site editor for the selected site."""
        from textual.widgets import Input
        # type: ignore[arg-type]
        sitepath = self.query_one("#sitepath", Input).value.strip()
        if not sitepath:
            self.ui_log.write("Site path is required to edit.")
            return
        site_root = Path(sitepath).expanduser().resolve()
        if not site_root.is_dir():
            self.ui_log.write(f"Error: Site path is not a valid directory: {site_root}")
            return

        # Persist last opened site
        try:
            self.config_manager.set_last_site_path(site_root)
        except Exception:
            pass

        for child in list(self.body.children):
            child.remove()
        self.body.mount(SiteEditorScreen(site_path=site_root))

    def pick_folder_into(self, input_selector: str) -> None:
        """Open the folder picker and put the result into the given Input widget.

        Uses a callback-based screen push to avoid requiring a worker context.
        """
        from textual.widgets import Input
        # Default start directory from config (falls back to current value/home)
        start_default = Path(self.config_manager.get_last_base_dir()) if hasattr(self, "config_manager") else Path.home()
        start = Path(self.query_one(input_selector, Input).value or start_default).expanduser()

        def on_done(result: str | None) -> None:
            if result:
                self.query_one(input_selector, Input).value = result
                # Persist last base dir for future convenience
                try:
                    self.config_manager.set_last_base_dir(result)
                except Exception:
                    pass

        # Push the modal screen; callback will run when it is dismissed
        self.push_screen(FolderPicker(start), callback=on_done)

    def handle_generate(self) -> None:
        """Handle generation form submission."""
        from textual.widgets import Input
        # type: ignore[arg-type]
        sitepath = self.query_one("#sitepath", Input).value.strip()
        if not sitepath:
            self.ui_log.write("Site path is required.")
            return
        site_root = Path(sitepath).expanduser().resolve()
        # Persist last site path
        try:
            self.config_manager.set_last_site_path(site_root)
        except Exception:
            pass
        try:
            generate_site(site_root, self.ui_log)
        except Exception as e:  # pragma: no cover - UI error path
            self.ui_log.write(f"Error: {e}")

    def handle_preview(self) -> None:
        """Handle preview button; open site in browser if generated."""
        from textual.widgets import Input
        # type: ignore[arg-type]
        sitepath = self.query_one("#sitepath", Input).value.strip()
        if not sitepath:
            self.ui_log.write("Site path is required for preview.")
            return
        site_root = Path(sitepath).expanduser().resolve()
        output_dir = site_root / "output"
        if not output_dir.exists() or not output_dir.is_dir():
            self.ui_log.write("Site not generated yet. Please generate first.")
            return
        index_file = output_dir / "index.html"
        if not index_file.exists():
            self.ui_log.write("Index file not found in output.")
            return
        try:
            webbrowser.open(f"file://{index_file.absolute()}")
            self.ui_log.write("Opening preview in browser...")
        except Exception as e:
            self.ui_log.write(f"Error opening preview: {e}")

    # -------------------------- Theme Picker -------------------------- #
    def open_theme_picker(self) -> None:
        """Open a simple theme picker modal and apply the chosen theme."""
        from textual.widgets import OptionList
        from textual.widgets.option_list import Option
        from textual.screen import ModalScreen
        from textual.app import ComposeResult

        THEMES = [
            "gruvbox",
            "nord",
            "tokyo-night",
            "textual-dark",
            "solarized-light",
        ]

        class ThemePicker(ModalScreen[str | None]):
            def compose(self) -> ComposeResult:  # type: ignore[override]
                yield OptionList(*(Option(name) for name in THEMES), id="theme-options")

            def on_mount(self) -> None:  # type: ignore[override]
                self.query_one(OptionList).focus()

            def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:  # type: ignore[override]
                self.dismiss(str(event.option.prompt))

        def on_done(result: str | None) -> None:
            if result:
                try:
                    self.theme = result
                    # Persist theme selection
                    try:
                        self.config_manager.set_theme(result)
                    except Exception:
                        pass
                    self.ui_log.write(f"Theme changed to: {result}")
                except Exception as e:
                    self.ui_log.write(f"Error applying theme '{result}': {e}")

        self.push_screen(ThemePicker(), callback=on_done)

    # -------------------------- Language Picker -------------------------- #
    def open_language_picker(self) -> None:
        """Open a simple language picker modal and apply the chosen language."""
        from textual.widgets import OptionList
        from textual.widgets.option_list import Option
        from textual.screen import ModalScreen
        from textual.app import ComposeResult

        LANGUAGES = [
            "en",
            "it",
        ]

        class LanguagePicker(ModalScreen[str | None]):
            def compose(self) -> ComposeResult:  # type: ignore[override]
                yield OptionList(*(Option("English (en)" if lang == "en" else "Italiano (it)", lang) for lang in LANGUAGES), id="language-options")

            def on_mount(self) -> None:  # type: ignore[override]
                self.query_one(OptionList).focus()

            def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:  # type: ignore[override]
                # Get the language code from the selected option
                if "en" in str(event.option.prompt).lower():
                    self.dismiss("en")
                elif "it" in str(event.option.prompt).lower():
                    self.dismiss("it")
                else:
                    self.dismiss(None)

        def on_done(result: str | None) -> None:
            if result:
                try:
                    # Change global language
                    from i18n import set_global_language
                    set_global_language(result)
                    # Persist language selection
                    try:
                        self.config_manager.set_language(result)
                    except Exception:
                        pass
                    # Refresh the main menu to show updated translations
                    self.show_main_menu()
                    self.ui_log.write(f"Language changed to: {result}")
                except Exception as e:
                    self.ui_log.write(f"Error applying language '{result}': {e}")

        self.push_screen(LanguagePicker(), callback=on_done)
