"""Breadcrumb navigation component for SSG TUI."""

from __future__ import annotations

from textual.widgets import Static


class Breadcrumb(Static):
    """Breadcrumb navigation component.

    Shows the current navigation path: Home > Current Screen > Sub-action
    """

    def __init__(self, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._crumbs: list[str] = ["Home"]

    def set_path(self, path: list[str]) -> None:
        """Update the breadcrumb path."""
        self._crumbs = ["Home"] + path
        self.update_breadcrumb()

    def add_crumb(self, crumb: str, icon: str = "") -> None:
        """Add a new crumb to the path."""
        if icon:
            crumb = f"{icon} {crumb}"
        self._crumbs.append(crumb)
        self.update_breadcrumb()

    def pop_crumb(self) -> str | None:
        """Remove the last crumb and return it."""
        if len(self._crumbs) > 1:  # Always keep Home
            removed = self._crumbs.pop()
            self.update_breadcrumb()
            return removed
        return None

    def update_breadcrumb(self) -> None:
        """Update the display of the breadcrumb."""
        display_crumbs = []
        for i, crumb in enumerate(self._crumbs):
            if i == 0:
                display_crumbs.append(f"[bold blue]{crumb}[/bold blue]")
            elif i == len(self._crumbs) - 1:
                display_crumbs.append(f"[bold]{crumb}[/bold]")
            else:
                display_crumbs.append(crumb)

        separator = " › "
        breadcrumb_text = separator.join(display_crumbs)
        self.update(breadcrumb_text)

    def reset(self) -> None:
        """Reset breadcrumb to home."""
        self._crumbs = ["Home"]
        self.update_breadcrumb()


class BreadcrumbBar(Static):
    """A complete breadcrumb bar with navigation controls."""

    def __init__(self, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.breadcrumb = Breadcrumb()
        self._can_go_back = False

    def compose(self):
        """Compose the breadcrumb bar with back button and current path."""
        from textual.containers import Horizontal
        from textual.widgets import Button

        with Horizontal(id="breadcrumb-container"):
            self.back_button = Button("Indietro", id="breadcrumb-back")
            self.back_button.disabled = not self._can_go_back
            yield self.back_button

            # Spacer
            yield Static(" ", classes="breadcrumb-spacer")

            self.breadcrumb.update_breadcrumb()
            yield self.breadcrumb

    def set_path(self, path: list[str]) -> None:
        """Update the breadcrumb path."""
        self.breadcrumb.set_path(path)
        self._update_back_button()

    def add_crumb(self, crumb: str, icon: str = "") -> None:
        """Add a new crumb to the path."""
        self.breadcrumb.add_crumb(crumb, icon)
        self._update_back_button()

    def pop_crumb(self) -> str | None:
        """Remove the last crumb and return it."""
        result = self.breadcrumb.pop_crumb()
        self._update_back_button()
        return result

    def reset(self) -> None:
        """Reset breadcrumb to home."""
        self.breadcrumb.reset()
        self._update_back_button()

    def _update_back_button(self) -> None:
        """Update the back button state based on path depth."""
        self._can_go_back = len(self.breadcrumb._crumbs) > 1
        if hasattr(self, 'back_button'):
            self.back_button.disabled = not self._can_go_back

    async def on_button_pressed(self, event) -> None:
        """Handle back button press."""
        from textual.widgets import Button
        if event.button.id == "breadcrumb-back" and self._can_go_back:
            # Pop the current crumb and emit navigation event
            removed_crumb = self.pop_crumb()
            if removed_crumb:
                self.post_message(BreadcrumbBackEvent(crumb=removed_crumb))


# Custom message for breadcrumb navigation
class BreadcrumbBackEvent:
    """Event triggered when user navigates back via breadcrumb."""

    def __init__(self, crumb: str) -> None:
        self.crumb = crumb


# Predefined breadcrumb paths for common screens
class BreadcrumbPaths:
    """Predefined breadcrumb paths for different screens."""

    HOME = []
    WIZARD_INIT = ["Nuovo Sito"]
    WIZARD_STEP = lambda step: ["Nuovo Sito", f"Passo {step}/4"]
    SITE_OPEN = ["Apri Sito"]
    SITE_EDIT = ["Modifica Sito"]
    GENERATE_SITE = ["Genera Sito"]
    SETTINGS = ["Impostazioni"]
