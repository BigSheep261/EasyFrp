"""应用程序主窗口。

main_window 是整个 UI 的外壳。
它不再直接写 frpc 的启动/停止细节，只负责：
1. 创建左侧侧边栏。
2. 创建右侧页面容器。
3. 根据侧边栏选择切换不同 page。
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from frp_gui.core.paths import APP_ICON_PATH, HEADER_LOGO_PATH, STATUS_ICON_PATH
from frp_gui.ui.pages.frpc_control_view import FrpcControlView


class MainWindow(QMainWindow):
    """EasyFrp 的顶层窗口。"""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("EasyFrp")
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(960, 640)

        self.sidebar_container = QWidget(self)
        self.logo_label = QLabel(self)

        # 左侧侧边栏：负责展示可切换的页面入口。
        self.sidebar = QListWidget(self)

        # 右侧页面容器：QStackedWidget 类似前端里的 router-view。
        # 它可以同时持有多个页面，但一次只显示其中一个。
        self.page_stack = QStackedWidget(self)

        self.frpc_control_view = FrpcControlView(self)

        self._build_ui()
        self._build_status_bar()
        self._connect_signals()
        self.sidebar.setCurrentRow(0)
        self.statusBar().showMessage("就绪")

    def closeEvent(self, event: QCloseEvent) -> None:
        """确保关闭 GUI 时，页面内正在运行的进程也能退出。"""
        self.frpc_control_view.shutdown()
        super().closeEvent(event)

    def _build_ui(self) -> None:
        """搭建主窗口外壳布局。"""
        central_widget = QWidget(self)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_sidebar()
        self._build_pages()

        main_layout.addWidget(self.sidebar_container)
        main_layout.addWidget(self.page_stack, stretch=1)
        self.setCentralWidget(central_widget)

    def _build_sidebar(self) -> None:
        """创建侧边栏。

        以后添加页面时，只需要继续 addItem，并在 _build_pages 里 addWidget。
        两边顺序保持一致，QListWidget 的 row 就能对应 QStackedWidget 的 index。
        """
        self.sidebar_container.setFixedWidth(180)
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(12, 14, 12, 10)
        sidebar_layout.setSpacing(10)

        self.logo_label.setFixedHeight(48)
        self.logo_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        if HEADER_LOGO_PATH.exists():
            logo_pixmap = QPixmap(str(HEADER_LOGO_PATH))
            self.logo_label.setPixmap(
                logo_pixmap.scaled(
                    156,
                    42,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.logo_label.setText("EasyFrp")

        self.sidebar.setObjectName("sidebarNavigation")
        self.sidebar.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.sidebar.setSpacing(4)
        self.sidebar.setStyleSheet(
            """
            QListWidget#sidebarNavigation {
                background: transparent;
                border: none;
                padding: 6px 0 0 0;
            }
            QListWidget#sidebarNavigation::item {
                min-height: 40px;
                padding: 8px 12px;
                border-radius: 6px;
            }
            QListWidget#sidebarNavigation::item:selected {
                background-color: #26a69a;
                color: white;
            }
            """
        )

        self.sidebar.addItem(QListWidgetItem("frpc 控制"))
        sidebar_layout.addWidget(self.logo_label)
        sidebar_layout.addWidget(self.sidebar, stretch=1)

    def _build_pages(self) -> None:
        """把页面加入右侧页面容器。"""
        self.page_stack.addWidget(self.frpc_control_view)

    def _build_status_bar(self) -> None:
        """Add the small FRP status icon used by the bottom status bar."""
        self.status_icon = QLabel(self)
        self.status_icon.setFixedSize(22, 22)
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_icon.setToolTip("EasyFrp FRP status")
        if STATUS_ICON_PATH.exists():
            status_pixmap = QPixmap(str(STATUS_ICON_PATH))
            self.status_icon.setPixmap(
                status_pixmap.scaled(
                    18,
                    18,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.statusBar().addPermanentWidget(self.status_icon)

    def _connect_signals(self) -> None:
        """连接主窗口级别的信号。"""
        self.sidebar.currentRowChanged.connect(self.page_stack.setCurrentIndex)
        self.frpc_control_view.status_message_changed.connect(
            self.statusBar().showMessage
        )
