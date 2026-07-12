"""Qt 应用程序启动模块。"""

# 导入解释器参数，未显式传参时将其交给 Qt 解析。
import sys
# 使用抽象序列类型，使调用方可以传入列表、元组等参数集合。
from collections.abc import Sequence

# 导入 Qt 应用对象，负责管理全局状态与事件循环。
from PyQt6.QtWidgets import QApplication

# 导入运行目录初始化函数，确保服务启动前所需路径均可用。
from frp_gui.utils.paths import ensure_runtime_directories
# 导入应用主窗口，在事件循环开始前完成构建与显示。
from frp_gui.ui.main_window import MainWindow


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """创建并配置 Qt 应用程序实例。

    Args:
        argv: 交给 Qt 解析的命令行参数；为 ``None`` 时使用当前进程参数。

    Returns:
        已设置应用名称和组织名称的 Qt 全局应用对象。
    """
    # 复制外部参数以避免 Qt 修改调用方持有的可变序列。
    arguments = list(argv) if argv is not None else sys.argv
    # 创建进程级唯一的 Qt 应用对象，并让 Qt 处理平台相关参数。
    application = QApplication(arguments)
    # 设置稳定的应用名称，供窗口系统和 Qt 配置机制识别。
    application.setApplicationName("EasyFrp")
    # 设置组织名称，使应用级配置拥有统一命名空间。
    application.setOrganizationName("EasyFrp")
    # 将完整配置后的实例交给启动流程继续使用。
    return application


def run(argv: Sequence[str] | None = None) -> int:
    """初始化运行环境并启动桌面应用程序的事件循环。

    Args:
        argv: 可选的 Qt 命令行参数；省略时沿用当前进程参数。

    Returns:
        Qt 事件循环结束时给出的进程退出码。
    """
    # 先创建日志、配置和运行时目录，避免界面加载服务时访问缺失路径。
    ensure_runtime_directories()
    # 构建全局 Qt 应用对象，后续所有控件都依附于该实例。
    application = create_application(argv)
    # 实例化顶层窗口并完成各业务页面的装配。
    window = MainWindow()
    # 显示主窗口后再进入事件循环，确保首帧能够正常绘制。
    window.show()
    # 阻塞处理用户事件，直至应用退出并返回对应状态码。
    return application.exec()
