"""Progress components for SSG TUI operations."""

from __future__ import annotations

from textual.widgets import Static
from textual.containers import Vertical, Horizontal


class ProgressBar(Static):
    """A simple progress bar widget."""

    def __init__(self, value: int = 0, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._value = max(0, min(100, value))  # Constrain between 0-100

    def set_value(self, value: int) -> None:
        """Set the progress value (0-100)."""
        self._value = max(0, min(100, value))
        self._update_display()

    def increment(self, amount: int = 1) -> None:
        """Increment the progress value by a given amount."""
        self._value = min(100, self._value + amount)
        self._update_display()

    def _update_display(self) -> None:
        """Update the visual display of the progress bar."""
        try:
            filled_width = int(self._value / 100 * 20)  # 20 characters wide
            filled = "█" * filled_width
            empty = "░" * (20 - filled_width)
            progress_display = f"[{filled}{empty}] {self._value}%"
            self.update(progress_display)
        except Exception:
            self.update(f"Progress: {self._value}%")


class ProgressIndicator(Static):
    """A full progress indicator with title and message."""

    def __init__(self, title: str = "Progress", message: str = "", name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.title = title
        self.message = message
        self.progress_bar = ProgressBar()
        self.status_icon = Static("⏳")

    def compose(self):
        from textual.containers import Vertical
        from i18n import translate
        title_text = self.title or translate("processing")
        message_text = self.message or translate("processing")
        with Vertical():
            yield Static(title_text, classes="text-subheader")
            yield Static(message_text, classes="text-muted")
            yield self.progress_bar

    def set_progress(self, value: int, message: str | None = None) -> None:
        """Update progress value and optionally the message."""
        self.progress_bar.set_value(value)
        if message:
            self.message = message
            self.query("Static", 2).update(message)

    def set_title(self, title: str) -> None:
        """Update the title."""
        self.title = title
        self.query("Static", 1).update(f"{title}")

    def set_message(self, message: str) -> None:
        """Update the message."""
        self.message = message
        self.query("Static", 2).update(message)

    def set_status(self, status: str) -> None:
        """Set the progress status (waiting, processing, complete, error)."""
        status_map = {
            "waiting": "[W]",
            "processing": "[P]",
            "complete": "[OK]",
            "error": "[ERR]",
            "success": "[DONE]"
        }
        icon = status_map.get(status, "[?]")
        self.status_icon.update(icon)


class LoadingSpinner(Static):
    """A simple loading spinner with message."""

    def __init__(self, message: str = "Loading...", name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.spinners = ["◐", "◓", "◑", "◒"]
        self.current_spinner = 0
        self.message = message
        self._running = False

        # Initialize display
        self.update(f"{self.spinners[self.current_spinner]} {self.message}")

    def start(self) -> None:
        """Start the spinner animation."""
        if not self._running:
            self._running = True
            self._animate()

    def stop(self) -> None:
        """Stop the spinner animation."""
        self._running = False

    def set_message(self, message: str) -> None:
        """Update the loading message."""
        self.message = message
        spinner = self.spinners[self.current_spinner]
        self.update(f"{spinner} {self.message}")

    def _animate(self) -> None:
        """Animate the spinner."""
        if self._running:
            self.current_spinner = (self.current_spinner + 1) % len(self.spinners)
            spinner = self.spinners[self.current_spinner]
            self.update(f"{spinner} {self.message}")
            self.set_timer(0.1, self._animate)


class StatusDisplay(Static):
    """A status display widget for showing operation states."""

    def __init__(self, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.set_status("ready")

    def set_status(self, status: str, message: str | None = None) -> None:
        """Set the status of the display."""
        status_config = {
            "ready": ("[R]", "Ready"),
            "waiting": ("[W]", "Waiting..."),
            "processing": ("[P]", "Processing..."),
            "complete": ("[OK]", "Complete"),
            "success": ("[DONE]", "Completed successfully!"),
            "error": ("[ERR]", "Error"),
            "warning": ("[WARN]", "Warning"),
            "info": ("[INFO]", "Information")
        }

        icon, default_msg = status_config.get(status, ("[?]", status))
        display_message = message or default_msg
        status_text = f"{icon} {display_message}"
        self.update(status_text)


class ProgressNotification(Static):
    """A notification-style progress widget."""

    def __init__(self, operation: str = "Operation", name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.operation = operation
        self._progress = ProgressBar()
        self.set_initial_state()

    def compose(self):
        from textual.containers import Horizontal, Vertical

        with Horizontal(id="notification-header"):
            yield Static(f"Starting {self.operation}", classes="text-subheader")

        # Progress area
        with Vertical():
            yield self._progress
            yield Static("Press Ctrl+C to cancel", classes="text-muted")

    def set_initial_state(self) -> None:
        """Set the initial display state."""
        self.update(f"Starting {self.operation}\nPreparing operation in progress...")

    def update_progress(self, value: int, step: str = "") -> None:
        """Update progress and current step."""
        progress_line = self._progress.set_value(value)
        step_info = f"\nStep: {step}" if step else ""
        self.update(f"Starting {self.operation}\n{progress_line}{step_info}")

    def complete(self, success: bool = True, message: str = "") -> None:
        """Mark the operation as complete."""
        icon = "[OK]" if success else "[ERR]"
        result_msg = message or ("Completed successfully!" if success else "Error during operation")
        self.update(f"{icon} {result_msg}")


# Usage examples and integration helpers
class ProgressComponents:
    """Utility class for creating and managing progress components."""

    @staticmethod
    def create_file_operation_progress(operation: str) -> ProgressNotification:
        """Create a progress notification for file operations."""
        return ProgressNotification(f"File {operation}")

    @staticmethod
    def create_network_operation_progress(operation: str) -> ProgressNotification:
        """Create a progress notification for network operations."""
        return ProgressNotification(f"Network {operation}")

    @staticmethod
    def create_build_progress() -> ProgressIndicator:
        """Create a build/compilation progress indicator."""
        return ProgressIndicator(
            title="Build in progress",
            message="Compiling project..."
        )

    @staticmethod
    def show_loading_overlay(app, message: str = "Loading..."):
        """Show a loading overlay on the application."""
        spinner = LoadingSpinner(message)
        app.overlay_add(spinner)
        return spinner
