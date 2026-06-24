"""Shared application paths."""

from pathlib import Path
import shutil
import sys


def _application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return PROJECT_ROOT


PROJECT_ROOT = _application_root()
BUNDLE_ROOT = _bundle_root()
CONFIG_DIR = PROJECT_ROOT / "config"
BUNDLED_CONFIG_DIR = BUNDLE_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
PROFILE_DIR = DATA_DIR / "profile"
FRPC_PROFILE_DIR = PROFILE_DIR / "frpc"
FRPC_GLOBAL_PROFILE_DIR = FRPC_PROFILE_DIR / "global"
FRPC_CONNECTION_PROFILE_DIR = FRPC_PROFILE_DIR / "connections"
LOG_DIR = PROJECT_ROOT / "logs"
RESOURCE_DIR = BUNDLE_ROOT / "resources"
ICON_DIR = RESOURCE_DIR / "icons"
APP_ICON_PATH = ICON_DIR / "easyfrp_app.ico"
HEADER_LOGO_PATH = ICON_DIR / "easyfrp_header_logo_small.png"
STATUS_ICON_PATH = ICON_DIR / "easyfrp_status_24.png"
TRAY_ICON_PATH = ICON_DIR / "easyfrp_tray.ico"
RUNTIME_DIR = PROJECT_ROOT / "runtime"


def ensure_runtime_directories() -> None:
    """Create writable runtime directories and seed default config files."""
    for directory in (CONFIG_DIR, LOG_DIR, RUNTIME_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    if BUNDLED_CONFIG_DIR == CONFIG_DIR or not BUNDLED_CONFIG_DIR.exists():
        return
    for source_path in BUNDLED_CONFIG_DIR.iterdir():
        if not source_path.is_file() or source_path.name == ".gitkeep":
            continue
        target_path = CONFIG_DIR / source_path.name
        if not target_path.exists():
            shutil.copy2(source_path, target_path)
