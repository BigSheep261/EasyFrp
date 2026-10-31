"""仅承载 frpc、frps 手动控制页面的主窗口。"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from frp_gui.ui.pages.frpc_control_view import FrpcControlView
from frp_gui.ui.pages.frps_control_view import FrpsControlView


class MainWindow(QMainWindow):
    """提供两个固定控制入口、公共状态栏和退出清理。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EasyFrp")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setFixedSize(960, 640)

        self.sidebar = QListWidget(self)
        self.sidebar.setObjectName("sidebarNavigation")
        self.sidebar.setFixedWidth(180)
        self.sidebar.addItems(["frpc 控制", "frps 控制"])

        self.page_stack = QStackedWidget(self)
        self.page_stack.setObjectName("pageStack")
        self.frpc_control_view = FrpcControlView(self)
        self.frps_control_view = FrpsControlView(self)
        for page in (self.frpc_control_view, self.frps_control_view):
            self.page_stack.addWidget(page)
            page.status_message_changed.connect(self.statusBar().showMessage)

        central_widget = QWidget(self)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.page_stack, stretch=1)
        self.setCentralWidget(central_widget)

        self.sidebar.currentRowChanged.connect(self.page_stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)
        self.statusBar().showMessage("就绪")

    def closeEvent(self, event: QCloseEvent) -> None:
        """退出时停止两个控制页管理的进程。"""
        self.frpc_control_view.shutdown()
        self.frps_control_view.shutdown()
        super().closeEvent(event)
