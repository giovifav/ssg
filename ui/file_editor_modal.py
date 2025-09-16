"""Generic file editor modal with optional syntax highlighting.

This module defines a Textual ModalScreen subclass that provides a generic
text editor for non-Markdown files. It includes an editable file-name field,
optional syntax highlighting (requires ``textual[syntax]`` extras), and a
wrap toggle button. The modal returns either the edited content as a string
or a payload dict that includes a potential new file name, allowing callers
to rename files safely.

Notes:
- The Textual TextArea syntax-highlighting features are optional and depend on
  the installed Textual version and extras. The component degrades gracefully
  when these features are unavailable.
- The layout is designed to match other screens in the application, using a
  bordered card style.

Example:
    The modal is typically pushed onto the active screen and dismissed with
    either edited content or None on cancel.

    >>> # app.push_screen(FileEditorModal(Path("/path/to/file.txt")))
    ... # The modal handles saving and cancellation internally.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual import events
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, TextArea, Input
from textual.containers import Vertical, Horizontal, VerticalScroll
from .utils import set_card_titles


class FileEditorModal(ModalScreen[dict | str | None]):
    """A modal dialog to edit file content for non-Markdown text files.

    The modal hosts a filename input, a growing TextArea editor, and a small
    toolbar with Save, Cancel, and Wrap toggle. On save, the modal dismisses
    with either a plain string (edited content) or a payload dict containing
    both the edited content and a potential new file name.

    Args:
        file_path: Path of the file being edited. Used to load initial content
            and infer the language for optional syntax highlighting.
        name: Optional widget name (Textual).
        id: Optional widget id (Textual).
        classes: Optional CSS classes for styling (Textual).

    Returns:
        On successful save, the dismissed value is either:
            - ``str``: the edited content (if filename unchanged).
            - ``dict``: a payload ``{"content": str, "new_name": str}`` if the user
              changed the filename (caller can then perform a safe rename).
        ``None`` is returned on cancel.
    """

    def __init__(
        self,
        file_path: Path,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the file editor modal.

        Args:
            file_path: Path to the file to read and edit.
            name: Optional Textual name for the widget.
            id: Optional Textual id for the widget.
            classes: Optional Textual CSS class list.
        """
        super().__init__(name=name, id=id, classes=classes)
        self.file_path = file_path
        # Read initial content if the file exists; otherwise start empty.
        self.original_content = (
            self.file_path.read_text(encoding="utf-8") if self.file_path.exists() else ""
        )
        # Track wrap preference; synced with the editor instance on mount.
        self._wrap_enabled: bool = True

    # ------------------------ Compose UI ------------------------
    def compose(self) -> ComposeResult:  # type: ignore[override]
        """Compose the file editor modal UI.

        Returns:
            A Textual ``ComposeResult`` with a card-like layout containing:
            - A "File name" input field.
            - A growing TextArea for the file contents.
            - A row of action buttons (Save, Cancel, Wrap toggle).
        """
        with Vertical(id="modal-dialog"):
            # Bordered card wrapper for consistency with other screens.
            with Vertical(id="file-editor-card", classes="panel"):
                # Filename field.
                with Vertical(id="file-name-field"):
                    yield Label("File name", classes="text-label")
                    yield Input(value=self.file_path.name, id="file-name-input")
                # Wrap textarea in VerticalScroll for proper space coverage
                with VerticalScroll(id="file-editor-pane"):
                    yield TextArea(self.original_content, id="file-editor-textarea")
                with Horizontal(id="modal-buttons"):
                    yield Button("Save", id="editor-save")
                    yield Button("Cancel", id="editor-cancel")
                    yield Button("Wrap: On", id="toggle-wrap")

    # ------------------------ Lifecycle ------------------------
    def on_mount(self) -> None:  # type: ignore[override]
        """Finalize setup after the modal is mounted.

        - Applies a border title to the card using the file name.
        - Focuses the editor and attempts to enable syntax highlighting.
        - Syncs the wrap flag and button label with the current editor state.
        """
        # Apply border title to the card using the file name
        try:
            card = self.query_one("#file-editor-card")
            set_card_titles(card, f"Edit file: {self.file_path.name}", "")
            # Set expansion for the card
            card.styles.height = "1fr"
        except Exception:
            # Non-fatal: some Textual versions may differ
            pass

        editor = self.query_one("#file-editor-textarea", TextArea)
        editor.focus()

        # Try to enable syntax highlighting if supported
        self._configure_editor_syntax(editor)

        # Apply initial wrap and sync button label
        current_wrap = self._get_wrap(editor)
        if current_wrap is not None:
            self._wrap_enabled = bool(current_wrap)
        self._apply_wrap(editor, self._wrap_enabled)
        self._sync_wrap_button_label()

    # ------------------------ Events ------------------------
    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        """Handle button press events from the modal toolbar.

        Args:
            event: The button press event from Textual.
        """
        editor = self.query_one("#file-editor-textarea", TextArea)
        if event.button.id == "editor-save":
            self._dismiss_with_payload(editor)
        elif event.button.id == "editor-cancel":
            # Return None to signal cancel explicitly
            self.dismiss(None)
        elif event.button.id == "toggle-wrap":
            self._wrap_enabled = not self._wrap_enabled
            self._apply_wrap(editor, self._wrap_enabled)
            self._sync_wrap_button_label()

    def on_key(self, event: events.Key) -> None:  # type: ignore[override]
        """Keyboard shortcuts handler.

        - ``Ctrl+S`` to save and dismiss with content/payload.
        - ``Esc`` to cancel and dismiss with ``None``.

        Args:
            event: The Textual key event.
        """
        key = (event.key or "").lower()
        ctrl = bool(getattr(event, "ctrl", False))
        if key == "s" and ctrl:
            editor = self.query_one("#file-editor-textarea", TextArea)
            self._dismiss_with_payload(editor)
            try:
                event.stop()
            except Exception:
                pass
        elif key in {"escape", "esc"}:
            self.dismiss(None)
            try:
                event.stop()
            except Exception:
                pass

    # ------------------------ Helpers ------------------------
    def _read_editor_text(self, editor: TextArea) -> str:
        """Return the current text from the editor in a version-robust way.

        Some Textual versions expose ``TextArea.text``, while others provide
        ``TextArea.value``. This helper abstracts that difference.

        Args:
            editor: The TextArea instance from which to read.

        Returns:
            The current editor content as a string.
        """
        # Be robust across Textual versions: prefer '.text', fall back to '.value'
        txt = getattr(editor, "text", None)
        if txt is None:
            txt = getattr(editor, "value", "")
        return str(txt)

    def _current_input_name(self) -> str:
        """Return a sanitized file name from the input field.

        The returned value is the base name component only. If the input is
        empty or only contains directories, the original file name is used as
        a fallback.

        Returns:
            The sanitized file name (no directories).
        """
        # Handle cases where user might enter a full path - extract just the filename component
        try:
            name = self.query_one("#file-name-input", Input).value.strip()
        except Exception:
            return self.file_path.name
        # Keep only the final component in case of path-like input
        return Path(name).name or self.file_path.name

    def _dismiss_with_payload(self, editor: TextArea) -> None:
        """Dismiss the modal with a save payload derived from the UI state.

        If the filename is unchanged, dismiss with a plain string (content)
        for backward compatibility. If the name changed, dismiss with a dict
        containing the content and the new name so the caller can rename
        safely.

        Args:
            editor: The TextArea widget containing the edited text.
        """
        content = self._read_editor_text(editor)
        new_name = self._current_input_name()

        # Normalize extension: if the user removed it, keep the original suffix
        if Path(new_name).suffix == "":
            new_name = Path(new_name).with_suffix(self.file_path.suffix).name

        # If unchanged, return plain content for backward compatibility
        if new_name == self.file_path.name:
            self.dismiss(content)
            return

        # Otherwise return a dict so caller can perform rename safely
        self.dismiss({"content": content, "new_name": new_name})

    def _configure_editor_syntax(self, editor: TextArea) -> None:
        """Configure optional syntax highlighting and editor visuals.

        - Selects a visible built-in theme if supported.
        - Sets the language based on file extension with fallbacks.
        - Enables line numbers and current line highlighting when available.

        The function is resilient to missing extras or API differences between
        Textual versions, silently ignoring unsupported attributes.

        Args:
            editor: The TextArea instance to configure.
        """
        # Resolve desired language from file suffix
        language = self._detect_language_from_suffix(self.file_path.suffix.lower())

        # Pick a visible theme so highlighting differences are obvious
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
            # Non-fatal if themes are unsupported
            pass

        # Apply language if supported; try reasonable fallbacks (especially for TOML)
        try:
            if hasattr(editor, "language") and language:
                langs = set(getattr(editor, "available_languages", set()) or [])
                chosen = None
                if not langs or language in langs:
                    chosen = language
                else:
                    # Fallback candidates if exact language not present
                    fallback_map = {
                        "toml": ["toml", "ini"],
                        "javascript": ["javascript", "js"],
                        "typescript": ["typescript", "ts"],
                        "html": ["html", "htm"],
                        "yaml": ["yaml", "yml"],
                        "ini": ["ini"],
                        "json": ["json"],
                        "python": ["python"],
                        "css": ["css"],
                        "text": ["text"],
                    }
                    for cand in fallback_map.get(language, [language]):
                        if not langs or cand in langs:
                            chosen = cand
                            break
                if chosen:
                    editor.language = chosen  # type: ignore[attr-defined]
        except Exception:
            # Ignore if the running Textual doesn't support syntax extras
            pass

        # Line numbers and cursor line highlight make code editing clearer
        try:
            if hasattr(editor, "show_line_numbers"):
                editor.show_line_numbers = True  # type: ignore[attr-defined]
            if hasattr(editor, "highlight_cursor_line"):
                editor.highlight_cursor_line = True  # type: ignore[attr-defined]
        except Exception:
            pass

    def _get_wrap(self, editor: TextArea) -> Optional[bool]:
        """Return the current wrap flag if detectable, otherwise ``None``.

        Args:
            editor: The TextArea instance to inspect.

        Returns:
            The current wrap setting (True/False) or ``None`` if not supported
            by the current Textual version.
        """
        # Try known attribute names across Textual versions
        for attr in ("soft_wrap", "wrap", "wrap_lines", "word_wrap"):
            if hasattr(editor, attr):
                try:
                    return bool(getattr(editor, attr))  # type: ignore[no-any-return]
                except Exception:
                    continue
        return None

    def _apply_wrap(self, editor: TextArea, enabled: bool) -> None:
        """Set the wrapping behavior using a supported attribute name.

        Args:
            editor: The TextArea instance to configure.
            enabled: Whether soft wrapping should be enabled.
        """
        for attr in ("soft_wrap", "wrap", "wrap_lines", "word_wrap"):
            if hasattr(editor, attr):
                try:
                    setattr(editor, attr, bool(enabled))
                    return
                except Exception:
                    continue

    def _sync_wrap_button_label(self) -> None:
        """Update the wrap toggle button label to reflect the current state."""
        try:
            btn = self.query_one("#toggle-wrap", Button)
            btn.label = f"Wrap: {'On' if self._wrap_enabled else 'Off'}"
        except Exception:
            pass

    @staticmethod
    def _detect_language_from_suffix(suffix: str) -> Optional[str]:
        """Best-effort language detection from a file extension.

        This mapping is intentionally conservative to avoid mismatches. Unknown
        extensions return ``None`` so that no language is applied.

        Args:
            suffix: The file extension including the leading dot (e.g., ``.py``).

        Returns:
            A language identifier string understood by Textual's syntax engine,
            or ``None`` if no suitable language is known for the suffix.
        """
        # Provide syntax highlighting support for common file extensions
        mapping = {
            ".py": "python",
            ".json": "json",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "ini",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".js": "javascript",
            ".ts": "typescript",
            ".txt": "text",
        }
        return mapping.get(suffix)
