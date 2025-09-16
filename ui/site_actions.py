"""Generate existing site screen and folder picker.

- SiteActions redesigned: single-column layout inside a bordered card
- English UI and screen-specific keybindings shown in Footer
  - b: Browse
  - g: Generate
  - e: Edit
  - p: Preview
  - Backspace: Back
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Header, Footer, Input, Label, Static
from textual.containers import Vertical, Horizontal, Container
from .utils import set_card_titles


class SiteActions(Container):
    """Form to select an existing site and generate output (single-column)."""

    # Screen-only key bindings for the global Footer
    BINDINGS = [
        Binding("b", "browse_site", "browse_shortcut"),
        Binding("g", "generate_site", "generate_shortcut"),
        Binding("e", "edit_site", "edit_shortcut"),
        Binding("p", "preview_site", "preview_shortcut"),
        Binding("backspace", "back", "back_shortcut"),
    ]

    def compose(self) -> ComposeResult:  # type: ignore[override]
        """Build a compact single-column layout inside a bordered card."""
        from i18n import translate
        with Vertical(id="generator-layout"):
            # Bordered card wrapper for consistency with menu/wizard
            with Vertical(id="generator-card", classes="panel"):
                # Descriptions moved to border subtitle

                # Site path input + actions
                with Vertical(classes="field-container"):
                    yield Label(translate("site_folder_path"), classes="text-label")
                    with Horizontal(classes="field-inline"):
                        yield Button(translate("browse"), id="browse_site", classes="btn-secondary")
                        yield Input(placeholder=translate("home_path"), id="sitepath")

                with Horizontal(classes="button-group"):
                    yield Button(translate("generate"), id="go", classes="btn-primary")
                    yield Button(translate("edit"), id="edit_selected_site", classes="btn-secondary")
                    yield Button(translate("preview"), id="preview", classes="btn-secondary")
                    yield Button(translate("back"), id="back", classes="btn-secondary")

    # -------------------------- Keybinding actions -------------------------- #

    def on_mount(self) -> None:  # type: ignore[override]
        """Prefill site path from persisted user configuration, if available."""
        from i18n import translate
        # Apply border title and subtitle to the card
        try:
            card = self.query_one("#generator-card")
            subtitle = translate("open_site_guide")
            if len(subtitle) > 80:
                subtitle = subtitle[:77] + "..."
            set_card_titles(card, translate("open_site_title"), subtitle)
        except Exception:
            pass
        try:
            last = self.app.config_manager.get_last_site_path()  # type: ignore[attr-defined]
            if last:
                from textual.widgets import Input
                self.query_one("#sitepath", Input).value = last
        except Exception:
            pass

    def action_browse_site(self) -> None:
        """Open folder picker into the site path field."""
        try:
            self.app.pick_folder_into("#sitepath")  # type: ignore[attr-defined]
        except Exception:
            pass

    def action_generate_site(self) -> None:
        """Trigger site generation via the App handler."""
        try:
            self.app.handle_generate()  # type: ignore[attr-defined]
        except Exception:
            pass

    def action_edit_site(self) -> None:
        """Open the editor for the selected site via the App handler."""
        try:
            self.app.handle_edit_site()  # type: ignore[attr-defined]
        except Exception:
            pass

    def action_preview_site(self) -> None:
        """Open site preview if generated."""
        try:
            self.app.handle_preview()  # type: ignore[attr-defined]
        except Exception:
            pass

    def action_back(self) -> None:
        """Return to the main menu."""
        try:
            self.app.show_main_menu()  # type: ignore[attr-defined]
        except Exception:
            pass

    # -------------------------- UI events ---------------------------------- #

    def on_button_pressed(self, event) -> None:  # type: ignore[override]
        """Handle button clicks; stop propagation to avoid double handling."""
        btn_id = (event.button.id or "")
        if btn_id == "browse_site":
            self.action_browse_site()
        elif btn_id == "go":
            self.action_generate_site()
        elif btn_id == "edit_selected_site":
            self.action_edit_site()
        elif btn_id == "preview":
            self.action_preview_site()
        elif btn_id == "back":
            self.action_back()
        # Stop at the source to prevent App.on_button_pressed duplicate handling
        try:
            event.stop()
        except Exception:
            pass


class FolderPicker(ModalScreen[str | None]):
    """Modal folder picker using DirectoryTree.

    Returns the selected directory path as a string, or None if cancelled.
    """

    def __init__(self, start_dir: Path) -> None:
        super().__init__()
        self.start_dir = start_dir
        self._selected: Optional[Path] = start_dir

    def compose(self) -> ComposeResult:  # type: ignore[override]
        from i18n import translate
        yield Header(show_clock=False)
        with Vertical(id="folder-picker-layout"):
            # Bordered card wrapper for consistency with menu/wizard
            with Vertical(id="folder-picker-card", classes="panel"):
                yield Label(translate("folder_picker_guide"))
                yield DirectoryTree(str(self.start_dir), id="tree")
                with Horizontal():
                    yield Button(translate("select"), id="confirm")
                    yield Button(translate("cancel"), id="cancel")
        yield Footer()

    def on_mount(self) -> None:  # type: ignore[override]
        # Focus the tree for immediate navigation
        tree = self.query_one("#tree", DirectoryTree)
        tree.focus()
        # Set expansion for the card and tree
        try:
            card = self.query_one("#folder-picker-card")
            card.styles.height = "1fr"
            tree.styles.height = "1fr"
        except Exception:
            pass

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:  # type: ignore[override]
        # Selecting a directory updates the current selection without closing
        try:
            self._selected = Path(event.path)
        except Exception:
            self._selected = None

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:  # type: ignore[override]
        # If a file is selected, use its parent directory
        path = Path(event.path).parent
        self.dismiss(str(path))

    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "confirm":
            # Confirm the current selection (folder)
            if self._selected is None:
                # If nothing is selected, use the starting directory
                self._selected = self.start_dir
            self.dismiss(str(self._selected))
