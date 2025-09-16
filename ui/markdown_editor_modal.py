"""Markdown editor modal."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, TextArea, Markdown
from textual.containers import Vertical, Horizontal, VerticalScroll
from .utils import set_card_titles


class MarkdownPreviewModal(ModalScreen[str | None]):
    """Modal for previewing rendered Markdown."""

    def __init__(self, content: str, file_path: Path, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.content = content
        self.file_path = file_path

    def compose(self) -> ComposeResult:  # type: ignore[override]
        """Compose the Markdown preview modal."""
        with Vertical(id="modal-dialog"):
            with Vertical(id="preview-card", classes="panel"):
                with VerticalScroll(id="preview-pane"):
                    yield Markdown(self.content, id="md-preview")
                with Horizontal(id="modal-buttons"):
                    close_button = Button("Close", id="preview-close")
                    close_button.styles.min_width = 10
                    yield close_button

    def on_mount(self) -> None:  # type: ignore[override]
        try:
            card = self.query_one("#preview-card")
            set_card_titles(card, f"Preview: {self.file_path.name}", "Anteprima del Markdown")
            self.query_one("#preview-pane")  # ensure exists
        except Exception:
            pass
        # Hide terminal cursor
        try:
            self.console.set_cursor_visible(False)
        except Exception:
            pass

    def on_unmount(self) -> None:  # type: ignore[override]
        # Restore terminal cursor visibility
        try:
            self.console.set_cursor_visible(True)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        if event.button.id == "preview-close":
            self.dismiss()


class MarkdownEditorModal(ModalScreen[str | None]):
    """Modal editor for Markdown."""

    def __init__(self, file_path: Path, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.file_path = file_path
        self.original_content = self.file_path.read_text(encoding="utf-8") if self.file_path.exists() else ""

    def compose(self) -> ComposeResult:  # type: ignore[override]
        """Compose the Markdown editor modal with editor."""
        with Vertical(id="modal-dialog"):
            # Bordered card wrapper for consistency with menu/wizard
            with Vertical(id="md-editor-card", classes="panel"):
                yield TextArea(self.original_content, id="md-editor-textarea")
                with Horizontal(id="modal-buttons"):
                    save_button = Button("Save", id="editor-save")
                    save_button.styles.min_width = 10
                    yield save_button
                    preview_button = Button("Preview", id="md-preview-btn")
                    preview_button.styles.min_width = 10
                    yield preview_button
                    cancel_button = Button("Cancel", id="editor-cancel")
                    cancel_button.styles.min_width = 10
                    yield cancel_button

    def on_mount(self) -> None:  # type: ignore[override]
        # Apply border title and subtitle to the card using the file name
        try:
            card = self.query_one("#md-editor-card")
            set_card_titles(card, f"Editing: {self.file_path.name}", "Editor Markdown")
            # Set expansion for the card
            card.styles.height = "1fr"
        except Exception:
            pass
        # Hide terminal cursor (avoid blinking caret outside editor)
        try:
            self.console.set_cursor_visible(False)
        except Exception:
            pass
        editor = self.query_one("#md-editor-textarea", TextArea)
        editor.focus()
        # Configure syntax highlighting for markdown
        self._configure_editor_syntax(editor)

    def on_unmount(self) -> None:  # type: ignore[override]
        # Restore terminal cursor visibility
        try:
            self.console.set_cursor_visible(True)
        except Exception:
            pass

    def _read_editor_text(self) -> str:
        editor = self.query_one("#md-editor-textarea", TextArea)
        txt = getattr(editor, "text", None)
        if txt is None:
            txt = getattr(editor, "value", "")
        return str(txt)

    def _configure_editor_syntax(self, editor: TextArea) -> None:
        """Configure syntax highlighting for markdown editor.

        - Set language to markdown
        - Apply visible theme if supported
        - Enable line numbers and cursor line highlighting
        - Degrades gracefully if syntax extras are missing
        """
        # Set language to markdown
        try:
            if hasattr(editor, "language"):
                langs = set(getattr(editor, "available_languages", set()) or [])
                if not langs or "markdown" in langs:
                    editor.language = "markdown"  # type: ignore[attr-defined]
        except Exception:
            # Ignore if the running Textual doesn't support syntax extras
            pass

        # Apply visible theme
        try:
            themes = set(getattr(editor, "available_themes", set()) or [])
            if hasattr(editor, "theme") and themes:
                if "monokai" in themes:
                    editor.theme = "monokai"  # type: ignore[attr-defined]
                elif "vscode_dark" in themes:
                    editor.theme = "vscode_dark"  # type: ignore[attr-defined]
                elif "github_light" in themes:
                    editor.theme = "github_light"  # type: ignore[attr-defined]
        except Exception:
            pass

        # Enable line numbers for better editing experience
        try:
            if hasattr(editor, "show_line_numbers"):
                editor.show_line_numbers = True  # type: ignore[attr-defined]
        except Exception:
            pass

        # Enable cursor line highlighting
        try:
            if hasattr(editor, "highlight_cursor_line"):
                editor.highlight_cursor_line = True  # type: ignore[attr-defined]
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        if event.button.id == "editor-save":
            self.dismiss(self._read_editor_text())
        elif event.button.id == "md-preview-btn":
            self.app.push_screen(MarkdownPreviewModal(self._read_editor_text(), self.file_path))
        elif event.button.id == "editor-cancel":
            self.dismiss(None)
