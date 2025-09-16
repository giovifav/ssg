"""UI logging wrapper."""

from __future__ import annotations

from textual.widgets import Log


class UILog(Log):
    """Wrapper over Textual's native Log widget with a simple write() API.

    Falls back gracefully if write_line is not available in the current Textual version.
    """

    def write(self, message: str) -> None:
        """Append a message to the log output."""
        try:
            self.write_line(str(message))
        except Exception:
            # Fallback to update if write_line is unavailable
            current = getattr(self, "_buffer", [])  # type: ignore[attr-defined]
            current.append(str(message))
            if len(current) > 200:
                current[:] = current[-200:]
            try:
                self._buffer = current  # type: ignore[attr-defined]
                self.update("\n".join(current))
            except Exception:
                pass
