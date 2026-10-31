"""应用共用路径定义。"""

# 使用面向对象的路径接口统一处理不同平台的路径分隔符。
from pathlib import Path
# 将内置设置模板序列化为首次运行的 JSON 文件。
import json
# 读取解释器运行状态，以区分源码环境和 PyInstaller 打包环境。
import sys

def _application_root() -> Path:
    """返回应用可写根目录。

    打包后运行时，返回exe所在目录
    在源码环境中则返回当前仓库根目录。
    """
    # PyInstaller 会设置 ``frozen`` 标志，此时以可执行文件位置作为根目录。
    if getattr(sys, "frozen", False):
        # 解析符号链接并取父目录，得到用户实际启动的安装位置。
        return Path(sys.executable).resolve().parent
    # 本文件位于 ``src/frp_gui/utils``，向上三级即可回到仓库根目录。
    return Path(__file__).resolve().parents[3]

# 应用根目录承载用户可修改的配置、日志和运行文件。
PROJECT_ROOT = _application_root()


CONFIG_DIR = PROJECT_ROOT / "config"
LOG_DIR = PROJECT_ROOT / "logs"
RUNTIME_DIR = PROJECT_ROOT / "runtime"

# 首次创建配置和界面回退共用的默认设置，仅在此处维护。
DEFAULT_EASYFRP_SETTINGS: dict[str, str | bool] = {
    "client_mode": "frpc",
    "launch_at_start": False,
    "auto_run": False,
}

def ensure_runtime_directories() -> None:
    """创建运行目录、空 TOML 文件，并用内置模板初始化应用设置。

    已存在的目录和用户配置不会被覆盖，因此该函数可在每次启动时安全调用。
    """
    # 逐一保证启动阶段必需的可写目录存在。
    for directory in (CONFIG_DIR, LOG_DIR, RUNTIME_DIR):
        # 同时创建缺失的父目录；目录已存在时保持不变。
        directory.mkdir(parents=True, exist_ok=True)
    # TOML 初始内容为空；应用设置从共用模板生成，不再依赖打包资源。
    initial_configs = {
        "frpc.toml": "",
        "frps.toml": "",
        "config.json": json.dumps(DEFAULT_EASYFRP_SETTINGS, ensure_ascii=False, indent=2) + "\n",
    }
    for filename, content in initial_configs.items():
        # 独占创建模式确保重复启动或同时启动时都不会覆盖已有文件。
        try:
            with (CONFIG_DIR / filename).open("x", encoding="utf-8") as config_file:
                config_file.write(content)
        except FileExistsError:
            continue
