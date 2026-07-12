"""EasyFrp 应用程序入口。"""

# 导入路径工具，以便从项目根目录定位源码目录。
from pathlib import Path
# 导入解释器接口，用于调整模块搜索路径并返回进程退出码。
import sys


# 以当前入口文件为锚点确定项目根目录，避免受启动时工作目录影响。
PROJECT_ROOT = Path(__file__).resolve().parent
# 源码采用 ``src`` 布局，需要显式定位实际的 Python 包目录。
SRC_DIR = PROJECT_ROOT / "src"

# 仅在源码目录尚未注册时将其放到搜索路径首位，防止重复插入。
if str(SRC_DIR) not in sys.path:
    # 优先加载当前项目源码，而不是环境中可能存在的同名安装包。
    sys.path.insert(0, str(SRC_DIR))

# 搜索路径准备完成后再导入应用启动函数。
from frp_gui.app import run


# 只在直接执行本文件时启动图形界面；被导入时不产生副作用。
if __name__ == "__main__":
    # 将 Qt 事件循环的返回值作为当前进程的退出状态。
    raise SystemExit(run())
