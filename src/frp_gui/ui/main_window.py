"""EasyFrp 主窗口。

主窗口只负责页面装配、导航、公共状态提示和退出清理。
具体的 FRP 配置与进程控制由各自页面负责。
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from frp_gui.ui.pages.dashboard import EasyFrpDashBoard
from frp_gui.ui.pages.frpc_config_view import FrpcConfigView
from frp_gui.ui.pages.frpc_control_view import FrpcControlView
from frp_gui.ui.pages.frps_config_view import FrpsConfigView
from frp_gui.ui.pages.frps_control_view import FrpsControlView
from frp_gui.ui.pages.setting_view import EasyfrpConfigView


PAGE_DASHBOARD = 0
PAGE_FRPC_CONTROL = 1
PAGE_FRPC_CONFIG = 2
PAGE_FRPS_CONTROL = 3
PAGE_FRPS_CONFIG = 4
PAGE_SETTINGS = 5


class MainWindow(QMainWindow):
    """承载应用页面并协调导航。"""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("EasyFrp")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setFixedSize(960, 640)

        self.sidebar = QListWidget(self)
        self.sidebar.setObjectName("sidebarNavigation")
        self.sidebar.setFixedWidth(180)

        self.page_stack = QStackedWidget(self)
        self.page_stack.setObjectName("pageStack")

        self.easyfrp_dashboard_view = EasyFrpDashBoard(self)
        self.frpc_control_view = FrpcControlView(self)
        self.frpc_config_view = FrpcConfigView(self)
        self.frps_control_view = FrpsControlView(self)
        self.frps_config_view = FrpsConfigView(self)
        self.easyfrp_config_view = EasyfrpConfigView(self)
        self._pages = (
            self.easyfrp_dashboard_view,
            self.frpc_control_view,
            self.frpc_config_view,
            self.frps_control_view,
            self.frps_config_view,
            self.easyfrp_config_view,
        )

        self._sidebar_page_routes: list[int] = []
        self._client_mode = "frpc"

        self._build_ui()
        self._connect_signals()
        self._apply_startup_settings()

    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.page_stack, stretch=1)
        self.setCentralWidget(central_widget)

        for page in self._pages:
            self.page_stack.addWidget(page)

        self.statusBar().showMessage("就绪")

    def _connect_signals(self) -> None:
        self.sidebar.currentRowChanged.connect(self._handle_sidebar_row_changed)

        for page in self._pages:
            page.status_message_changed.connect(self._show_main_message)

        self.easyfrp_config_view.settings_changed.connect(
            self._handle_settings_changed
        )

    def _apply_startup_settings(self) -> None:
        settings = self.easyfrp_config_view.current_settings
        client_mode = "frps" if settings.get("client_mode") == "frps" else "frpc"
        self._refresh_sidebar_for_mode(client_mode)

        if settings.get("auto_run") is True:
            QTimer.singleShot(0, lambda: self._auto_run_client_mode(client_mode))

    def _refresh_sidebar_for_mode(
        self,
        client_mode: str,
        *,
        selected_page: int | None = None,
    ) -> None:
        self._client_mode = "frps" if client_mode == "frps" else "frpc"

        if selected_page is None:
            selected_page = self.page_stack.currentIndex()

        mode_pages = (
            [("frps 控制", PAGE_FRPS_CONTROL), ("frps 配置", PAGE_FRPS_CONFIG)]
            if self._client_mode == "frps"
            else [("frpc 控制", PAGE_FRPC_CONTROL), ("frpc 配置", PAGE_FRPC_CONFIG)]
        )
        items = [
            ("Dashboard", PAGE_DASHBOARD),
            *mode_pages,
            ("设置", PAGE_SETTINGS),
        ]

        self.sidebar.blockSignals(True)
        self.sidebar.clear()
        self._sidebar_page_routes.clear()

        for label, page_index in items:
            self.sidebar.addItem(QListWidgetItem(label))
            self._sidebar_page_routes.append(page_index)

        try:
            row = self._sidebar_page_routes.index(selected_page)
        except ValueError:
            row = 0

        self.sidebar.setCurrentRow(row)
        self.sidebar.blockSignals(False)
        self._handle_sidebar_row_changed(row)

    def _handle_sidebar_row_changed(self, row: int) -> None:
        if 0 <= row < len(self._sidebar_page_routes):
            self.page_stack.setCurrentIndex(self._sidebar_page_routes[row])

    def _handle_settings_changed(self, settings: dict) -> None:
        client_mode = settings.get("client_mode")
        if client_mode not in {"frpc", "frps"}:
            client_mode = self._client_mode

        selected_page = (
            PAGE_SETTINGS
            if self.page_stack.currentIndex() == PAGE_SETTINGS
            else None
        )
        self._refresh_sidebar_for_mode(
            client_mode,
            selected_page=selected_page,
        )

    def _auto_run_client_mode(self, client_mode: str) -> None:
        if client_mode == "frps":
            started = self.frps_control_view.start_frps()
        else:
            started = self.frpc_control_view.start_frpc()

        if started:
            self._show_main_message(f"已按设置自动启动 {client_mode}")

    def _show_main_message(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.frpc_control_view.shutdown()
        self.frps_control_view.shutdown()
        super().closeEvent(event)
