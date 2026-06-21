"""项目共用路径定义。"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
PROFILE_DIR = DATA_DIR / "profile"
FRPC_PROFILE_DIR = PROFILE_DIR / "frpc"
FRPC_GLOBAL_PROFILE_DIR = FRPC_PROFILE_DIR / "global"
FRPC_CONNECTION_PROFILE_DIR = FRPC_PROFILE_DIR / "connections"
LOG_DIR = PROJECT_ROOT / "logs"
RESOURCE_DIR = PROJECT_ROOT / "resources"
ICON_DIR = RESOURCE_DIR / "icons"
APP_ICON_PATH = ICON_DIR / "easyfrp_app.ico"
HEADER_LOGO_PATH = ICON_DIR / "easyfrp_header_logo_small.png"
STATUS_ICON_PATH = ICON_DIR / "easyfrp_status_24.png"
TRAY_ICON_PATH = ICON_DIR / "easyfrp_tray.ico"
RUNTIME_DIR = PROJECT_ROOT / "runtime"


def ensure_runtime_directories() -> None:
    """创建应用程序运行时可能写入数据的目录。"""
    for directory in (CONFIG_DIR, LOG_DIR, RUNTIME_DIR):
        directory.mkdir(parents=True, exist_ok=True)
