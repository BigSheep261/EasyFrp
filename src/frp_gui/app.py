"""Qt 应用程序启动模块。"""

import sys
from collections.abc import Sequence

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from frp_gui.core.paths import APP_ICON_PATH, ensure_runtime_directories
from frp_gui.ui.main_window import MainWindow


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """创建并配置 Qt 应用程序实例。"""
    arguments = list(argv) if argv is not None else sys.argv
    application = QApplication(arguments)
    application.setApplicationName("EasyFrp")
    application.setOrganizationName("EasyFrp")
    if APP_ICON_PATH.exists():
        application.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    apply_stylesheet(application, theme="dark_teal.xml")
    return application


def run(argv: Sequence[str] | None = None) -> int:
    """启动桌面应用程序的事件循环。"""
    ensure_runtime_directories()
    application = create_application(argv)
    window = MainWindow()
    window.show()
    return application.exec()
