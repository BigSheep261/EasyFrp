"""项目共用路径定义。"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
LOG_DIR = PROJECT_ROOT / "logs"
RESOURCE_DIR = PROJECT_ROOT / "resources"
RUNTIME_DIR = PROJECT_ROOT / "runtime"


def ensure_runtime_directories() -> None:
    """创建应用程序运行时可能写入数据的目录。"""
    for directory in (CONFIG_DIR, LOG_DIR, RUNTIME_DIR):
        directory.mkdir(parents=True, exist_ok=True)
