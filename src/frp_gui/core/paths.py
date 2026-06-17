"""Shared project path definitions."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
LOG_DIR = PROJECT_ROOT / "logs"
RESOURCE_DIR = PROJECT_ROOT / "resources"
RUNTIME_DIR = PROJECT_ROOT / "runtime"


def ensure_runtime_directories() -> None:
    """Create directories that may receive data while the app is running."""
    for directory in (CONFIG_DIR, LOG_DIR, RUNTIME_DIR):
        directory.mkdir(parents=True, exist_ok=True)
