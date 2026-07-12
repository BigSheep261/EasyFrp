"""应用共用路径定义。"""

# 使用面向对象的路径接口统一处理不同平台的路径分隔符。
from pathlib import Path
# 导入高级文件复制工具，用于首次运行时部署默认配置。
import shutil
# 读取解释器运行状态，以区分源码环境和 PyInstaller 打包环境。
import sys


def _application_root() -> Path:
    """返回应用可写根目录。

    在打包程序中，配置和日志应放在可执行文件旁；在源码环境中则返回
    仓库根目录。这样上层代码无需感知当前的分发方式。

    Returns:
        应用持久化数据所在的绝对根路径。
    """
    # PyInstaller 会设置 ``frozen`` 标志，此时以可执行文件位置作为根目录。
    if getattr(sys, "frozen", False):
        # 解析符号链接并取父目录，得到用户实际启动的安装位置。
        return Path(sys.executable).resolve().parent
    # 本文件位于 ``src/frp_gui/utils``，向上三级即可回到仓库根目录。
    return Path(__file__).resolve().parents[3]


def _bundle_root() -> Path:
    """返回打包资源的只读根目录。

    Returns:
        PyInstaller 临时解包目录；源码运行时则与项目根目录相同。
    """
    # 单文件打包模式通过 ``_MEIPASS`` 暴露临时资源目录。
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # 该属性由 PyInstaller 动态注入，因此通过 ``sys`` 实例读取。
        return Path(sys._MEIPASS)
    # 源码模式下资源直接位于项目目录，无需额外转换。
    return PROJECT_ROOT


# 应用根目录承载用户可修改的配置、数据、日志和运行文件。
PROJECT_ROOT = _application_root()
# 资源根目录指向打包内置文件；源码模式下与应用根目录一致。
BUNDLE_ROOT = _bundle_root()
# 用户实际读写的配置目录位于应用根目录下。
CONFIG_DIR = PROJECT_ROOT / "config"
# 默认配置的来源目录可能位于 PyInstaller 的临时解包位置。
BUNDLED_CONFIG_DIR = BUNDLE_ROOT / "config"
# 数据目录集中保存用户创建的持久化业务数据。
DATA_DIR = PROJECT_ROOT / "data"
# 配置档案的共同父目录，便于按业务角色继续分层。
PROFILE_DIR = DATA_DIR / "profile"
# frpc 客户端的全部配置档案统一放在此目录。
FRPC_PROFILE_DIR = PROFILE_DIR / "frpc"
# 全局客户端参数与具体代理连接分开保存。
FRPC_GLOBAL_PROFILE_DIR = FRPC_PROFILE_DIR / "global"
# 每条 frpc 代理连接使用独立档案，便于增删和组合。
FRPC_CONNECTION_PROFILE_DIR = FRPC_PROFILE_DIR / "connections"
# 日志目录保存 frpc、frps 以及应用自身的运行输出。
LOG_DIR = PROJECT_ROOT / "logs"
# 运行时目录用于放置或查找 frpc、frps 可执行文件。
RUNTIME_DIR = PROJECT_ROOT / "runtime"


def ensure_runtime_directories() -> None:
    """创建可写运行目录，并从程序包中补齐缺失的默认配置。

    已存在的目录和用户配置不会被覆盖，因此该函数可在每次启动时安全调用。
    """
    # 逐一保证启动阶段必需的可写目录存在。
    for directory in (CONFIG_DIR, LOG_DIR, RUNTIME_DIR):
        # 同时创建缺失的父目录；目录已存在时保持不变。
        directory.mkdir(parents=True, exist_ok=True)
    # 源码模式无需复制；打包资源不存在时也没有可部署内容。
    if BUNDLED_CONFIG_DIR == CONFIG_DIR or not BUNDLED_CONFIG_DIR.exists():
        # 提前结束可避免把配置文件复制到自身或访问无效目录。
        return
    # 枚举程序包附带的默认配置，按需部署到用户可写目录。
    for source_path in BUNDLED_CONFIG_DIR.iterdir():
        # 忽略子目录和仅用于版本控制占位的空文件。
        if not source_path.is_file() or source_path.name == ".gitkeep":
            # 跳过当前条目并继续检查下一份默认配置。
            continue
        # 保持源文件名不变，构造用户配置的目标位置。
        target_path = CONFIG_DIR / source_path.name
        # 只补齐缺失文件，绝不覆盖用户已经修改过的配置。
        if not target_path.exists():
            # 连同时间戳等元数据复制默认配置，完成首次运行初始化。
            shutil.copy2(source_path, target_path)
