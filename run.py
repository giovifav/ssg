"""Bootstrap script to set up a virtual environment, install dependencies, and run the TUI.

This helper performs these steps:
- Ensure a local virtual environment exists (and pip is up to date)
- Install dependencies from requirements.txt
- Launch the application using the virtual environment's Python

It is intended to be executed directly by end users on Windows (PowerShell) or
other platforms.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path
import re

MIN_PYTHON = (3, 8)
if sys.version_info < MIN_PYTHON:
    sys.exit(f"Richiede Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} o superiore.")

VENV_DIR = Path(".venv")
REQ_FILE = Path("requirements.txt")
APP_FILE = Path("main.py")


def python_in_venv():
    """Return the python interpreter path inside the venv (platform-aware)."""
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"


def run(cmd: list[str], venv: bool = False) -> None:
    """Run a command, optionally inside the virtual environment.

    Args:
        cmd: Command list (e.g., ["-m", "pip", "install", "-r", "requirements.txt"]).
        venv: If True, execute using the venv's python.
    """
    if venv:
        cmd = [str(python_in_venv())] + cmd
    subprocess.check_call(cmd, shell=False)


def run_capture(cmd: list[str], venv: bool = False):
    """Run a command and capture stdout/stderr.

    Returns (returncode, stdout, stderr)
    """
    if venv:
        cmd = [str(python_in_venv())] + cmd
    proc = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    return proc.returncode, out, err


def ensure_venv():
    """Create the virtual environment if missing and ensure pip is up-to-date."""
    if not VENV_DIR.exists():
        print("➡ Creo virtual environment...")
        venv.create(VENV_DIR, with_pip=True)

        # Ensure pip is available and upgraded
        run(["-m", "ensurepip", "--upgrade"], venv=True)
        run(["-m", "pip", "install", "--upgrade", "pip"], venv=True)


def check_requirements():
    """Check if requirements are satisfied (or file is absent).

    Strategy:
    - If no requirements.txt, return True.
    - Try `pip check` (conflicts etc.). If fails, return False.
    - Parse requirements.txt and verify each top-level requirement can be imported or is installed.
    - If any missing, return False.
    """
    if not REQ_FILE.exists():
        return True  # No requirements file

    print("➡ Controllo dipendenze...")
    # 1) pip check
    rc, out, err = run_capture(["-m", "pip", "check"], venv=True)
    if rc != 0:
        return False

    # 2) parse requirements and verify install/import
    try:
        req_lines = REQ_FILE.read_text(encoding="utf-8").splitlines()
    except Exception:
        return True

    def parse_pkg(line: str) -> str | None:
        s = line.strip()
        if not s or s.startswith("#"):
            return None
        # Split markers and extras/version
        s = s.split(";")[0].strip()
        s = s.split(" ")[0].strip()
        return s or None

    # map requirement names to import test modules when needed
    import_checks = {
        "Pillow": "PIL",
        "python-frontmatter": "frontmatter",
        "markdown": "markdown",
        "jinja2": "jinja2",
        "toml": "toml",
        "textual[syntax]": "textual",
    }

    missing = []
    for line in req_lines:
        spec = parse_pkg(line)
        if not spec:
            continue
        name = spec
        # normalize extras e.g., textual[syntax] -> textual
        base = re.split(r"[\[=<>!~]", name, maxsplit=1)[0]
        mod = import_checks.get(name) or import_checks.get(base) or base
        code = (
            "import importlib, sys; "
            f"mod='{mod}'; "
            "sys.exit(0 if importlib.util.find_spec(mod) else 1)"
        )
        rc, _, _ = run_capture(["-c", code], venv=True)
        if rc != 0:
            missing.append(name)

    return len(missing) == 0


def install_requirements():
    """Install or update dependencies from requirements.txt if present."""
    if REQ_FILE.exists():
        print("➡ Installo/aggiorno dipendenze...")
        run(["-m", "pip", "install", "-r", str(REQ_FILE)], venv=True)


def run_app():
    """Launch the app inside the virtual environment."""
    print("➡ Avvio applicazione...")
    run([str(APP_FILE)], venv=True)


if __name__ == "__main__":
    ensure_venv()

    if not check_requirements():
        install_requirements()
        # Re-check after install; avoid infinite loop in case of persistent issues
        if not check_requirements():
            print("⚠ Alcune dipendenze potrebbero mancare o essere non compatibili. Procedo comunque.")

    run_app()

    if os.name == "nt" and sys.stdin.isatty():
        input("Premi INVIO per chiudere...")
