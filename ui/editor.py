"""Site editor screen redesigned to single-column with bordered card and screen-specific keybindings (English UI).

Keybindings (shown in Footer):
- p: New Page
- f: New File
- e: Edit File
- c: New Folder
- Backspace: Back
"""

from __future__ import annotations

import sys
import os
import webbrowser

# Ensure we can import from the parent directory
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button, DirectoryTree, Label, Static
from textual.containers import Vertical, Horizontal, Container
from .utils import set_card_titles

# Site generation - use absolute imports to avoid relative import issues
from site_generator import generate_site


class SiteEditorScreen(Container):
    """Screen for editing site files (single-column layout)."""

    # Screen-specific keybindings; displayed by the global Footer
    BINDINGS = [
        Binding("p", "new_page", "New Page"),
        Binding("f", "new_file", "New File"),
        Binding("e", "edit_file", "Edit File"),
        Binding("c", "new_dir", "New Folder"),
        Binding("b", "new_blog", "New Blog"),
        Binding("g", "generate_site", "Generate"),
        Binding("v", "preview_site", "Preview"),
        Binding("backspace", "back", "Back"),
    ]

    def __init__(
        self,
        site_path: Path | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.site_path = site_path if site_path else Path.home()
        self.current_dir = self.site_path
        # Track currently selected directory (for rename action)
        self._selected_dir: Optional[Path] = None

    def compose(self) -> ComposeResult:  # type: ignore[override]
        """Compose a compact single-column editor layout inside a bordered card."""
        from i18n import translate
        with Vertical(id="editor-layout"):
            # Bordered card wrapping the whole editor content
            with Vertical(id="editor-card", classes="panel"):
                # Site stats moved to border subtitle; keep stats widget for live updates
                self.site_stats = Static("", classes="site-stats")
                yield self.site_stats
                self._update_site_stats()

                # Directory tree
                yield Label(translate("file_browser"), classes="text-subheader")
                yield DirectoryTree(str(self.site_path), id="editor-tree")

                # Current directory status
                self.current_dir_status = Static("", classes="current-dir-status")
                yield self.current_dir_status

                # Toolbar actions
                with Horizontal(id="editor-toolbar", classes="panel"):
                    yield Button(translate("new_page"), id="new_page")
                    yield Button(translate("new_file"), id="new_file")
                    yield Button(translate("new_folder"), id="new_dir")
                    yield Button(translate("new_gallery"), id="new_gallery")
                    yield Button(translate("new_blog"), id="new_blog")
                    yield Button(translate("generate"), id="generate_site")
                    yield Button(translate("preview"), id="preview_site")
                    yield Button(translate("rename_folder"), id="rename_folder")
                    yield Button(translate("back"), id="back_from_editor")

        # Initialize status
        self._update_current_dir_status()

    def on_mount(self) -> None:  # type: ignore[override]
        from i18n import translate
        # Localize keybinding labels for the footer at runtime
        try:
            self.BINDINGS = [
                Binding("p", "new_page", translate("new_page")),
                Binding("f", "new_file", translate("new_file")),
                Binding("e", "edit_file", translate("edit_file")),
                Binding("c", "new_dir", translate("new_folder")),
                Binding("b", "new_blog", translate("new_blog")),
                Binding("g", "generate_site", translate("generate")),
                Binding("v", "preview_site", translate("preview")),
                Binding("backspace", "back", translate("back")),
            ]
        except Exception:
            pass
        # Apply border title and a concise subtitle (dynamic stats)
        try:
            card = self.query_one("#editor-card")
            # Compose a short subtitle with current root dir and counts
            dir_name = self.current_dir.name if self.current_dir != self.site_path else translate("root_directory")
            subtitle = f"{translate('current_directory')}: {dir_name}"
            if len(subtitle) > 60:
                subtitle = subtitle[:57] + "..."
            set_card_titles(card, translate("editor_title"), subtitle)
            # Set expansion programmatically
            card.styles.height = "1fr"
        except Exception:
            pass
        # Focus the tree for immediate navigation
        tree = self.query_one("#editor-tree", DirectoryTree)
        tree.focus()
        # Hide rename button initially (no folder selected yet)
        try:
            btn = self.query_one("#rename_folder", Button)
            btn.display = False  # type: ignore[attr-defined]
        except Exception:
            pass

    # -------------------------- Actions for keybindings --------------------- #

    async def action_new_page(self) -> None:
        await self._create_new_page()

    async def action_new_file(self) -> None:
        await self._create_new_file()

    async def action_edit_file(self) -> None:
        await self._edit_selected_file()

    async def action_new_dir(self) -> None:
        await self._create_new_directory()

    async def action_new_blog(self) -> None:
        await self._create_new_blog()

    def action_generate_site(self) -> None:
        self._generate_site()

    def action_preview_site(self) -> None:
        self._preview_site()

    def action_back(self) -> None:
        try:
            self.app.show_main_menu()  # type: ignore[attr-defined]
        except Exception:
            pass

    # -------------------------- Event handlers ----------------------------- #

    async def on_button_pressed(self, event) -> None:  # type: ignore[override]
        """Map buttons to actions; stop propagation to avoid double handling by App."""
        bid = (event.button.id or "")
        if bid == "new_file":
            await self._create_new_file()
        elif bid == "new_dir":
            await self._create_new_directory()
        elif bid == "new_page":
            await self._create_new_page()
        elif bid == "rename_folder":
            await self._rename_selected_folder()
        elif bid == "generate_site":
            self._generate_site()
        elif bid == "new_gallery":
            await self._create_new_gallery()
        elif bid == "new_blog":
            await self._create_new_blog()
        elif bid == "preview_site":
            self._preview_site()
        elif bid == "back_from_editor":
            self.action_back()
        try:
            event.stop()
        except Exception:
            pass

    def on_directory_tree_directory_selected(self, event) -> None:  # type: ignore[override]
        # Update current directory and status
        self.current_dir = Path(event.path)
        self._selected_dir = self.current_dir
        self.app.ui_log.write(f"Selected directory: {self.current_dir}")  # type: ignore[attr-defined]
        self._update_current_dir_status()
        # Ensure rename button visible when a directory is selected
        try:
            btn = self.query_one("#rename_folder", Button)
            btn.display = True  # type: ignore[attr-defined]
        except Exception:
            pass

    async def on_directory_tree_file_selected(self, event) -> None:  # type: ignore[override]
        file_path = Path(event.path)
        self.app.ui_log.write(f"Selected file: {file_path}")  # type: ignore[attr-defined]

        # No preview: we removed the preview panel to maximize the file picker area
        try:
            # Hide the rename button when a file (not a folder) is selected
            self._selected_dir = None
            try:
                btn = self.query_one("#rename_folder", Button)
                btn.display = False  # type: ignore[attr-defined]
            except Exception:
                pass
        except Exception:
            pass

        # Open the appropriate editor automatically for text files
        try:
            if file_path.exists() and file_path.is_file():
                text_file_extensions = {".txt", ".md", ".html", ".css", ".js", ".toml", ".json", ".py", ".ini", ".yaml", ".yml"}
                if file_path.suffix.lower() in text_file_extensions:
                    # Use dedicated Markdown editor for .md
                    if file_path.suffix.lower() == ".md":
                        screen = self._get_markdown_editor_modal(file_path)
                    else:
                        screen = self._get_file_editor_modal(file_path)
                    worker = self.run_worker(
                        self.app.push_screen_wait(screen),  # type: ignore[attr-defined]
                        exclusive=True,
                    )
                    await worker.wait()
                    edited_result = worker.result
                    if edited_result is None:
                        self.app.ui_log.write("Edit cancelled.")  # type: ignore[attr-defined]
                    else:
                        # Normalize result to content + optional new_name
                        if isinstance(edited_result, dict):
                            content = str(edited_result.get("content", ""))
                            new_name = str(edited_result.get("new_name", "")).strip() or None
                        else:
                            content = str(edited_result)
                            new_name = None
                        # Compare with current content
                        try:
                            original_content = file_path.read_text(encoding="utf-8")
                        except Exception:
                            original_content = None
                        if content != original_content or new_name:
                            try:
                                target_path = file_path
                                if new_name and new_name != file_path.name:
                                    candidate = file_path.with_name(new_name)
                                    if candidate.exists():
                                        self.app.ui_log.write(f"A file named '{new_name}' already exists.")  # type: ignore[attr-defined]
                                    else:
                                        file_path.rename(candidate)
                                        target_path = candidate
                                        self.app.ui_log.write(f"Renamed file to: {candidate.name}")  # type: ignore[attr-defined]
                                # Write content to the (possibly renamed) file
                                target_path.write_text(content, encoding="utf-8")
                                self.app.ui_log.write(f"Saved changes to: {target_path.name}")  # type: ignore[attr-defined]
                                # Refresh tree and focus the updated file
                                self._refresh_tree(focus_path=target_path)
                            except Exception as e:
                                self.app.ui_log.write(f"Error saving file: {e}")  # type: ignore[attr-defined]
                        else:
                            self.app.ui_log.write("No changes saved.")  # type: ignore[attr-defined]
                else:
                    self.app.ui_log.write(f"Cannot edit binary file: {file_path.name}")  # type: ignore[attr-defined]
        except Exception:
            # Be resilient to any editor errors; keep selection behavior working
            pass

    # -------------------------- Helpers ------------------------------------ #

    def _generate_site(self) -> None:
        """Generate the site using current site root and refresh UI."""
        from i18n import translate
        try:
            # Log start
            self.app.ui_log.write(f"{translate('generating')}...")  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            generate_site(self.site_path, getattr(self.app, "ui_log", None))
            try:
                self.app.ui_log.write(translate("complete"))  # type: ignore[attr-defined]
            except Exception:
                pass
        except Exception as e:
            try:
                # Localized generic error label if available
                err_label = translate("error")
                prefix = f"{err_label}: " if err_label else "Error: "
                self.app.ui_log.write(f"{prefix}{e}")  # type: ignore[attr-defined]
            except Exception:
                pass
        # Update stats and tree after generation
        try:
            self._update_site_stats()
            self._refresh_tree()
        except Exception:
            pass

    def _preview_site(self) -> None:
        """Open the site's output index.html in the default browser."""
        from i18n import translate
        from config import read_config
        try:
            cfg = read_config(self.site_path)
            output_path = self.site_path / cfg.output
            index_html = output_path / "index.html"
            if index_html.exists():
                url = index_html.as_uri()
                webbrowser.open(url)
                self.app.ui_log.write(translate("preview") + " opened in browser")  # type: ignore[attr-defined]
            else:
                self.app.ui_log.write("Site not generated yet - no output/index.html found")  # type: ignore[attr-defined]
        except Exception as e:
            try:
                self.app.ui_log.write(f"Error opening preview: {e}")  # type: ignore[attr-defined]
            except Exception:
                pass

    def _update_site_stats(self) -> None:
        """Update the site statistics display."""
        try:
            total_files = sum(1 for p in self.site_path.rglob("*") if p.is_file())
            total_dirs = sum(1 for p in self.site_path.rglob("*") if p.is_dir())
            self.site_stats.update(f"{total_files} files, {max(total_dirs - 1, 0)} folders")
        except Exception:
            self.site_stats.update("Stats not available")

    def _update_current_dir_status(self) -> None:
        """Update the current directory status display."""
        try:
            dir_name = self.current_dir.name if self.current_dir != self.site_path else "root"
            file_count = sum(1 for p in self.current_dir.iterdir() if p.is_file())
            dir_count = sum(1 for p in self.current_dir.iterdir() if p.is_dir())
            self.current_dir_status.update(f"{dir_name}: {file_count} files, {dir_count} folders")
        except Exception:
            self.current_dir_status.update("Directory status not available")

    def _refresh_tree(self, focus_path: Optional[Path] = None) -> None:
        """Refresh the directory tree and optionally focus a given path."""
        tree = self.query_one("#editor-tree", DirectoryTree)
        tree.path = str(self.site_path)  # Resetting path refreshes the tree
        tree.reload()
        if focus_path is not None:
            target = str(focus_path)

            def _try_focus() -> None:
                try:
                    if hasattr(tree, "action_select"):
                        parent = str(focus_path.parent)
                        tree.action_select(parent)  # type: ignore[attr-defined]
                        tree.action_select(target)  # type: ignore[attr-defined]
                except Exception:
                    pass

            self.set_timer(0.1, _try_focus)

    async def _create_new_file(self) -> None:
        """Handles creating a new file."""
        worker = self.run_worker(
            self.app.push_screen_wait(  # type: ignore[attr-defined]
                self._get_text_input_modal("New File", "Enter new file name:")
            ),
            exclusive=True,
        )
        await worker.wait()
        new_file_name = worker.result

        if new_file_name:
            new_file_path = self.current_dir / new_file_name
            try:
                new_file_path.touch()
                self.app.ui_log.write(f"Created new file: {new_file_path}")  # type: ignore[attr-defined]
                self._refresh_tree(focus_path=new_file_path)
            except Exception as e:
                self.app.ui_log.write(f"Error creating file: {e}")  # type: ignore[attr-defined]

    async def _create_new_gallery(self) -> None:
        """Create a _gallery folder with index.md including title and description.
        - Prompts for title and description via two sequential modals.
        - Ensures folder is created in the current directory (or inside content subtree if preferred).
        - Writes index.md with YAML front matter and a basic heading/description.
        """
        from i18n import translate
        # Ask for gallery title
        worker_title = self.run_worker(
            self.app.push_screen_wait(  # type: ignore[attr-defined]
                self._get_text_input_modal(translate("new_gallery_modal_title"), translate("new_gallery_modal_prompt_title"))
            ),
            exclusive=True,
        )
        await worker_title.wait()
        title = (worker_title.result or "").strip()
        if not title:
            return
        # Ask for gallery description
        worker_desc = self.run_worker(
            self.app.push_screen_wait(  # type: ignore[attr-defined]
                self._get_text_input_modal(translate("new_gallery_modal_title"), translate("new_gallery_modal_prompt_description"))
            ),
            exclusive=True,
        )
        await worker_desc.wait()
        description = (worker_desc.result or "").strip()

        # Determine target directory: use current if within content, otherwise content
        content_dir = self.site_path / "content"
        if self.current_dir.is_relative_to(content_dir):
            target_dir = self.current_dir
        else:
            # Show warning modal if selected folder is outside content
            confirm_modal = self._get_confirmation_modal(
                translate("warning"),
                translate("confirm_outside_content")
            )
            confirm_worker = self.run_worker(
                self.app.push_screen_wait(confirm_modal),  # type: ignore[attr-defined]
                exclusive=True,
            )
            await confirm_worker.wait()
            confirmed = confirm_worker.result
            if not confirmed:
                return  # User cancelled
            target_dir = content_dir

        # Ensure content directory exists
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.app.ui_log.write(f"Error creating directory: {e}")  # type: ignore[attr-defined]
            return
        # Create _gallery and index.md
        gallery_dir = target_dir / "_gallery"
        try:
            gallery_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            try:
                self.app.ui_log.write(f"Error creating _gallery folder: {e}")  # type: ignore[attr-defined]
            except Exception:
                pass
            return

        index_md = gallery_dir / "index.md"
        # Compose index.md content
        from datetime import date as _date
        safe_title = title
        body = description or ""
        content = (
            "---\n"
            f"title: {safe_title}\n"
            f"date: {_date.today().isoformat()}\n"
            "---\n\n"
            f"# {safe_title}\n\n"
            f"{body}\n"
        )
        try:
            # If exists, don't overwrite silently; append notice
            if index_md.exists():
                # Simple merge: keep existing content, do nothing
                self.app.ui_log.write(f"_gallery already exists: {index_md}")  # type: ignore[attr-defined]
            else:
                index_md.write_text(content, encoding="utf-8")
                self.app.ui_log.write(f"Created gallery: {index_md}")  # type: ignore[attr-defined]
            # Refresh UI tree focusing the new folder
            self._refresh_tree(focus_path=gallery_dir)
        except Exception as e:
            self.app.ui_log.write(f"Error creating gallery: {e}")  # type: ignore[attr-defined]

    async def _create_new_blog(self) -> None:
        """Create a _blog folder with index.md including title and description/introduction.
        - Prompts for title and description/introduction via two sequential modals.
        - Ensures folder is created in the current directory (or inside content subtree if preferred).
        - Writes index.md with YAML front matter and content that will be used as blog introduction.
        """
        from i18n import translate
        # Ask for blog title
        worker_title = self.run_worker(
            self.app.push_screen_wait(  # type: ignore[attr-defined]
                self._get_text_input_modal(translate("new_blog_modal_title"), translate("new_blog_modal_prompt_title"))
            ),
            exclusive=True,
        )
        await worker_title.wait()
        title = (worker_title.result or "").strip()
        if not title:
            return
        # Ask for blog description/introduction
        worker_desc = self.run_worker(
            self.app.push_screen_wait(  # type: ignore[attr-defined]
                self._get_text_input_modal(translate("new_blog_modal_title"), translate("new_blog_modal_prompt_description"))
            ),
            exclusive=True,
        )
        await worker_desc.wait()
        description = (worker_desc.result or "").strip()

        # Determine target directory: use current if within content, otherwise content
        content_dir = self.site_path / "content"
        if self.current_dir.is_relative_to(content_dir):
            target_dir = self.current_dir
        else:
            # Show warning modal if selected folder is outside content
            confirm_modal = self._get_confirmation_modal(
                translate("warning"),
                translate("confirm_outside_content")
            )
            confirm_worker = self.run_worker(
                self.app.push_screen_wait(confirm_modal),  # type: ignore[attr-defined]
                exclusive=True,
            )
            await confirm_worker.wait()
            confirmed = confirm_worker.result
            if not confirmed:
                return  # User cancelled
            target_dir = content_dir

        # Ensure content directory exists
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.app.ui_log.write(f"Error creating directory: {e}")  # type: ignore[attr-defined]
            return

        # Create _blog and index.md
        blog_dir = target_dir / "_blog"
        try:
            blog_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            try:
                self.app.ui_log.write(f"Error creating _blog folder: {e}")  # type: ignore[attr-defined]
            except Exception:
                pass
            return

        index_md = blog_dir / "index.md"
        # Compose index.md content - this will be used for blog title and introduction
        from datetime import date as _date
        safe_title = title
        body = description or ""
        content = (
            "---\n"
            f"title: {safe_title}\n"
            f"date: {_date.today().isoformat()}\n"
            "---\n\n"
            f"{body}\n"
        )
        try:
            # If exists, don't overwrite silently; append notice
            if index_md.exists():
                # Simple merge: keep existing content, do nothing
                self.app.ui_log.write(f"_blog already exists: {index_md}")  # type: ignore[attr-defined]
            else:
                index_md.write_text(content, encoding="utf-8")
                self.app.ui_log.write(f"Created blog: {index_md}")  # type: ignore[attr-defined]
            # Refresh UI tree focusing the new folder
            self._refresh_tree(focus_path=blog_dir)
        except Exception as e:
            self.app.ui_log.write(f"Error creating blog: {e}")  # type: ignore[attr-defined]

    async def _create_new_directory(self) -> None:
        """Handles creating a new directory."""
        worker = self.run_worker(
            self.app.push_screen_wait(  # type: ignore[attr-defined]
                self._get_text_input_modal("New Folder", "Enter new folder name:")
            ),
            exclusive=True,
        )
        await worker.wait()
        new_dir_name = worker.result

        if new_dir_name:
            new_dir_path = self.current_dir / new_dir_name
            try:
                new_dir_path.mkdir(parents=True, exist_ok=True)
                self.app.ui_log.write(f"Created new folder: {new_dir_path}")  # type: ignore[attr-defined]
                self._refresh_tree(focus_path=new_dir_path)
            except Exception as e:
                self.app.ui_log.write(f"Error creating folder: {e}")  # type: ignore[attr-defined]

    async def _edit_selected_file(self) -> None:
        """Handles editing the currently selected file."""
        tree = self.query_one("#editor-tree", DirectoryTree)
        # Try to get the selected file path from the tree
        file_path: Optional[Path] = None
        try:
            cursor_node = getattr(tree, "cursor_node", None)
            if cursor_node is not None and getattr(cursor_node, "data", None) is not None:
                data = cursor_node.data
                if hasattr(data, "path"):
                    p = Path(data.path)
                    if p.is_file():
                        file_path = p
        except Exception:
            file_path = None

        if file_path and file_path.is_file():
            text_file_extensions = {".txt", ".md", ".html", ".css", ".js", ".toml", ".json", ".py"}
            if file_path.suffix.lower() in text_file_extensions:
                original_content = file_path.read_text(encoding="utf-8")
                # Use a dedicated Markdown editor for .md files
                if file_path.suffix.lower() == ".md":
                    screen = self._get_markdown_editor_modal(file_path)
                else:
                    screen = self._get_file_editor_modal(file_path)
                worker = self.run_worker(
                    self.app.push_screen_wait(screen),  # type: ignore[attr-defined]
                    exclusive=True,
                )
                await worker.wait()
                edited_result = worker.result
                if edited_result is None:
                    self.app.ui_log.write("Edit cancelled.")  # type: ignore[attr-defined]
                else:
                    # Normalize result to content + optional new_name
                    if isinstance(edited_result, dict):
                        content = str(edited_result.get("content", ""))
                        new_name = str(edited_result.get("new_name", "")).strip() or None
                    else:
                        content = str(edited_result)
                        new_name = None
                    if content != original_content or new_name:
                        try:
                            target_path = file_path
                            if new_name and new_name != file_path.name:
                                candidate = file_path.with_name(new_name)
                                if candidate.exists():
                                    self.app.ui_log.write(f"A file named '{new_name}' already exists.")  # type: ignore[attr-defined]
                                else:
                                    file_path.rename(candidate)
                                    target_path = candidate
                                    self.app.ui_log.write(f"Renamed file to: {candidate.name}")  # type: ignore[attr-defined]
                            target_path.write_text(content, encoding="utf-8")
                            self.app.ui_log.write(f"Saved changes to: {target_path.name}")  # type: ignore[attr-defined]
                            self._refresh_tree(focus_path=target_path)
                        except Exception as e:
                            self.app.ui_log.write(f"Error saving file: {e}")  # type: ignore[attr-defined]
                    else:
                        self.app.ui_log.write("No changes saved.")  # type: ignore[attr-defined]
            else:
                self.app.ui_log.write(f"Cannot edit binary file: {file_path.name}")  # type: ignore[attr-defined]
        else:
            self.app.ui_log.write("No file selected for editing.")  # type: ignore[attr-defined]

    async def _create_new_page(self) -> None:
        """Create a new Markdown page with front matter and focus it in the tree."""
        worker = self.run_worker(
            self.app.push_screen_wait(  # type: ignore[attr-defined]
                self._get_new_page_modal()
            ),
            exclusive=True,
        )
        await worker.wait()
        data = worker.result
        if not data:
            return

        # Determine target directory: use current if within content, otherwise content
        content_dir = self.site_path / "content"
        if self.current_dir.is_relative_to(content_dir):
            target_dir = self.current_dir
        else:
            # Show warning modal if selected folder is outside content
            from i18n import translate
            confirm_modal = self._get_confirmation_modal(
                translate("warning"),
                translate("confirm_outside_content")
            )
            confirm_worker = self.run_worker(
                self.app.push_screen_wait(confirm_modal),  # type: ignore[attr-defined]
                exclusive=True,
            )
            await confirm_worker.wait()
            confirmed = confirm_worker.result
            if not confirmed:
                return  # User cancelled
            target_dir = content_dir

        # Ensure content directory exists
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.app.ui_log.write(f"Error creating directory: {e}")  # type: ignore[attr-defined]
            return

        from datetime import date as _date
        name = str(data.get("name", "")).strip()
        title = str(data.get("title", "")).strip()
        when = str(data.get("date", "")).strip() or _date.today().isoformat()
        if not name:
            return
        if not name.lower().endswith(".md"):
            name += ".md"
        new_file_path = target_dir / name
        if new_file_path.exists():
            self.app.ui_log.write(f"File already exists: {new_file_path}")  # type: ignore[attr-defined]
            self._refresh_tree(focus_path=new_file_path)
            return
        # Build content with YAML front matter
        safe_title = title or Path(name).stem.replace("-", " ").replace("_", " ")
        content = (
            "---\n"
            f"title: {safe_title}\n"
            f"date: {when}\n"
            "---\n\n"
            f"# {safe_title}\n\n"
        )
        try:
            new_file_path.write_text(content, encoding="utf-8")
            self.app.ui_log.write(f"Created page: {new_file_path}")  # type: ignore[attr-defined]
            self._refresh_tree(focus_path=new_file_path)
        except Exception as e:
            self.app.ui_log.write(f"Error creating page: {e}")  # type: ignore[attr-defined]

    # -------------------------- Modal helpers ------------------------------ #

    def _get_text_input_modal(self, title: str, prompt: str):
        """Create a text input modal.

        Args:
            title: Title displayed in the modal border.
            prompt: A short helper or question shown as subtitle/placeholder.

        Returns:
            A TextInputModal instance ready to be pushed as a screen.
        """
        from .input_modal import TextInputModal
        return TextInputModal(title=title, prompt=prompt)

    async def _rename_selected_folder(self) -> None:
        """Rename the currently selected folder in the tree.

        Only runs if a directory is selected; asks for the new name via modal,
        then performs an os-level rename and refreshes the tree focusing the new path.
        """
        # Validate selection
        if self._selected_dir is None or not self._selected_dir.exists() or not self._selected_dir.is_dir():
            self.app.ui_log.write("No folder selected for renaming.")  # type: ignore[attr-defined]
            return

        # Ask for the new name (not full path), prefill current name if supported
        worker = self.run_worker(
            self.app.push_screen_wait(  # type: ignore[attr-defined]
                self._get_text_input_modal("Rename Folder", f"Enter new name for '{self._selected_dir.name}':")
            ),
            exclusive=True,
        )
        await worker.wait()
        new_name = (worker.result or "").strip()
        if not new_name:
            self.app.ui_log.write("Rename cancelled.")  # type: ignore[attr-defined]
            return

        # Compute target path and validate
        target = self._selected_dir.parent / new_name
        if target.exists():
            self.app.ui_log.write(f"A file or folder named '{new_name}' already exists.")  # type: ignore[attr-defined]
            return

        # Perform rename
        try:
            old_dir = self._selected_dir
            old_dir.rename(target)
            self.app.ui_log.write(f"Renamed folder to: {target}")  # type: ignore[attr-defined]
            self._selected_dir = target
            # Also update current_dir if it was the renamed folder
            if self.current_dir == old_dir:
                self.current_dir = target
            # Refresh tree and focus new folder
            self._refresh_tree(focus_path=target)
            self._update_current_dir_status()
        except Exception as e:
            self.app.ui_log.write(f"Error renaming folder: {e}")  # type: ignore[attr-defined]

    def _get_new_page_modal(self):
        from .new_page_modal import NewPageModal
        return NewPageModal()

    def _get_markdown_editor_modal(self, file_path: Path):
        from .markdown_editor_modal import MarkdownEditorModal
        return MarkdownEditorModal(file_path=file_path)

    def _get_file_editor_modal(self, file_path: Path):
        from .file_editor_modal import FileEditorModal
        return FileEditorModal(file_path=file_path)

    def _get_confirmation_modal(self, title: str, message: str):
        from .confirmation_modal import ConfirmationModal
        return ConfirmationModal(title=title, message=message)
