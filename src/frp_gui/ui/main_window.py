"""仅承载 frpc、frps 手动控制页面的主窗口。"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow

from frp_gui.ui.pages.frpc_control_view import FrpcControlView
from frp_gui.ui.pages.frps_control_view import FrpsControlView
from frp_gui.ui.weights.main_tab import EasyFrpTabWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._init_Weights()
        self._init_window()
        self._regTabBar()

    """注册主界面所有的控件"""
    def _init_Weights(self):
        self.frpc_control_view = FrpcControlView(self)
        self.frps_control_view = FrpsControlView(self)

        self.easyfrp_tabWidget = EasyFrpTabWidget(self)

    """注册主界面所有的属性"""
    def _init_window(self):
        self.setWindowTitle("EasyFrp")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setFixedSize(960, 640)
        self.setCentralWidget(self.easyfrp_tabWidget)

    """注册侧边栏的页面"""
    def _regTabBar(self):
        self.easyfrp_tabWidget.addTab(self.frpc_control_view, "frpc")
        self.easyfrp_tabWidget.addTab(self.frps_control_view, "frps")

    """退出时停止两个控制页管理的进程。"""
    def closeEvent(self, event: QCloseEvent) -> None:
        self.frpc_control_view.shutdown()
        self.frps_control_view.shutdown()
        super().closeEvent(event)
