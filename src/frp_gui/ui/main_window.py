"""应用程序主窗口。

main_window 是整个 UI 的外壳。
它不再直接写 frpc 的启动/停止细节，只负责：
1. 创建左侧侧边栏。
2. 创建右侧页面容器。
3. 根据侧边栏选择切换不同 page。
"""

from PyQt6.QtCore import QEvent, QObject, QPoint, QRect, Qt, QTimer
from PyQt6.QtGui import QAction, QCloseEvent, QIcon, QMouseEvent, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from frp_gui.core.paths import (
    APP_ICON_PATH,
    HEADER_LOGO_PATH,
    TRAY_ICON_PATH,
)
from frp_gui.core.easyfrp_config_service import EasyfrpConfigService
from frp_gui.ui.pages.easyfrp_config_view import EasyfrpConfigView
from frp_gui.ui.pages.frpc_config_view import FrpcConfigView
from frp_gui.ui.pages.frpc_control_view import FrpcControlView
from frp_gui.ui.pages.frps_config_view import FrpsConfigView
from frp_gui.ui.pages.frps_control_view import FrpsControlView
from frp_gui.ui.theme import apply_app_theme

WINDOW_OPACITY = 1
MIN_WINDOW_WIDTH = 760
MIN_WINDOW_HEIGHT = 520
RESIZE_MARGIN = 8

PAGE_FRPC_CONTROL = 0
PAGE_FRPC_CONFIG = 1
PAGE_FRPS_CONTROL = 2
PAGE_FRPS_CONFIG = 3
PAGE_SETTINGS = 4


class MainWindow(QMainWindow):
    """EasyFrp 的顶层窗口。"""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("EasyFrp")
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # 设置整个主窗口透明度。Qt 使用 0.0 到 1.0 表示窗口不透明度：
        # 1.0 表示完全不透明，0.75 表示约 75% 不透明，也就是能看到一些背景。
        self.setWindowOpacity(WINDOW_OPACITY)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(960, 640)

        self.sidebar_container = QWidget(self)
        self.content_container = QWidget(self)
        self.window_controls_container = QWidget(self)
        self.minimize_button = QPushButton("—", self)
        self.maximize_button = QPushButton("□", self)
        self.close_button = QPushButton("×", self)
        self.logo_label = QLabel(self)
        self.main_message_frame = QFrame(self)
        self.main_message_label = QLabel("就绪", self)
        self._drag_position: QPoint | None = None
        self._resize_edges: set[str] = set()
        self._resize_start_geometry = QRect()
        self._resize_start_position = QPoint()
        self._sidebar_page_routes: list[int] = []
        self._client_mode = "frpc"
        self.logo_label.setObjectName("logoLabel")
        self.sidebar_container.setObjectName("sidebarContainer")
        self.content_container.setObjectName("contentContainer")
        self.page_stack = QStackedWidget(self)
        self.page_stack.setObjectName("pageStack")
        self.minimize_button.setObjectName("windowButton")
        self.maximize_button.setObjectName("windowButton")
        self.close_button.setObjectName("closeButton")

        # 左侧侧边栏：负责展示可切换的页面入口。
        self.sidebar = QListWidget(self)

        # 右侧页面容器：QStackedWidget 类似前端里的 router-view。
        # 它可以同时持有多个页面，但一次只显示其中一个。

        self.frpc_control_view = FrpcControlView(self)
        self.frpc_config_view = FrpcConfigView(self)
        self.frps_control_view = FrpsControlView(self)
        self.frps_config_view = FrpsConfigView(self)
        self.easyfrp_config_view = EasyfrpConfigView(self)
        self.tray_icon: QSystemTrayIcon | None = None

        self._build_ui()
        self._install_window_event_filters()
        self._build_tray_icon()
        self._connect_signals()
        self._apply_startup_settings()

    def closeEvent(self, event: QCloseEvent) -> None:
        """确保关闭 GUI 时，页面内正在运行的进程也能退出。"""
        if self.tray_icon is not None:
            self.tray_icon.hide()
        self.frpc_control_view.shutdown()
        self.frps_control_view.shutdown()
        super().closeEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """记录无边框窗口的拖动起点。"""
        if event.button() == Qt.MouseButton.LeftButton and not self.isMaximized():
            resize_edges = self._resize_edges_at_position(event.position().toPoint())
            if resize_edges:
                self._resize_edges = resize_edges
                self._resize_start_geometry = self.geometry()
                self._resize_start_position = event.globalPosition().toPoint()
                event.accept()
                return

        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._is_window_drag_area(event.position().toPoint())
        ):
            self._drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """拖动主界面顶部空白区域移动窗口。"""
        if self._resize_edges and event.buttons() & Qt.MouseButton.LeftButton:
            self._resize_window(event.globalPosition().toPoint())
            event.accept()
            return

        if (
            self._drag_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and not self.isMaximized()
        ):
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return

        self._update_resize_cursor(event.position().toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """结束无边框窗口拖动。"""
        self._drag_position = None
        self._resize_edges = set()
        self._update_resize_cursor(event.position().toPoint())
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """双击主界面顶部空白区域时切换最大化。"""
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._is_window_drag_area(event.position().toPoint())
            and not self._resize_edges_at_position(event.position().toPoint())
        ):
            self._toggle_maximized()
            event.accept()
            return

        super().mouseDoubleClickEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """让无边框窗口在子控件区域也能拖动和缩放。"""
        if not isinstance(watched, QWidget) or watched.window() is not self:
            return super().eventFilter(watched, event)
        if not isinstance(event, QMouseEvent):
            return super().eventFilter(watched, event)
        if watched in {
            self.minimize_button,
            self.maximize_button,
            self.close_button,
        }:
            return super().eventFilter(watched, event)

        local_position = watched.mapTo(self, event.position().toPoint())
        if event.type() == QEvent.Type.MouseButtonPress:
            return self._handle_filtered_mouse_press(event, local_position)
        if event.type() == QEvent.Type.MouseMove:
            return self._handle_filtered_mouse_move(event, local_position)
        if event.type() == QEvent.Type.MouseButtonRelease:
            return self._handle_filtered_mouse_release(event, local_position)

        return super().eventFilter(watched, event)

    def _build_ui(self) -> None:
        """搭建主窗口外壳布局。"""
        central_widget = QWidget(self)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_sidebar()
        self._build_pages()
        self._build_content_container()

        main_layout.addWidget(self.sidebar_container)
        main_layout.addWidget(self.content_container, stretch=1)
        self.setCentralWidget(central_widget)

    def _build_content_container(self) -> None:
        """创建右侧内容区，并放入窗口控制按钮和页面容器。"""
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._build_window_controls()

        content_layout.addWidget(self.window_controls_container)
        content_layout.addWidget(self.page_stack, stretch=1)

    def _install_window_event_filters(self) -> None:
        """给窗口和子控件安装鼠标过滤器，用于无边框缩放。"""
        widgets = [self, *self.findChildren(QWidget)]
        if self.sidebar.viewport() not in widgets:
            widgets.append(self.sidebar.viewport())

        for widget in widgets:
            widget.setMouseTracking(True)
            widget.installEventFilter(self)

    def _build_window_controls(self) -> None:
        """把原生标题栏按钮放到主界面右上角。"""
        self.window_controls_container.setObjectName("windowControlsContainer")
        self.window_controls_container.setFixedHeight(36)

        controls_layout = QHBoxLayout(self.window_controls_container)
        controls_layout.setContentsMargins(0, 4, 8, 4)
        controls_layout.setSpacing(2)
        controls_layout.addStretch()

        self.minimize_button.setToolTip("最小化")
        self.maximize_button.setToolTip("最大化")
        self.close_button.setToolTip("关闭")

        self.minimize_button.clicked.connect(self.showMinimized)
        self.maximize_button.clicked.connect(self._toggle_maximized)
        self.close_button.clicked.connect(self.close)

        controls_layout.addWidget(self.minimize_button)
        controls_layout.addWidget(self.maximize_button)
        controls_layout.addWidget(self.close_button)

    def _build_sidebar(self) -> None:
        """创建侧边栏。

        侧边栏的条目会根据当前客户端模式动态生成，实际页面映射由
        ``self._sidebar_page_routes`` 维护。
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

        sidebar_layout.addWidget(self.logo_label)
        sidebar_layout.addWidget(self.sidebar, stretch=1)
        sidebar_layout.addWidget(self.main_message_frame)

        self._build_main_message()

    def _build_pages(self) -> None:
        """把页面加入右侧页面容器。"""
        self.page_stack.addWidget(self.frpc_control_view)
        self.page_stack.addWidget(self.frpc_config_view)
        self.page_stack.addWidget(self.frps_control_view)
        self.page_stack.addWidget(self.frps_config_view)
        self.page_stack.addWidget(self.easyfrp_config_view)

    def _build_main_message(self) -> None:
        """创建主界面内的信息提示块，替代窗口底部状态栏。"""
        self.main_message_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.main_message_frame.setObjectName("mainMessageFrame")
        self.main_message_label.setObjectName("mainMessageText")

        message_layout = QVBoxLayout(self.main_message_frame)
        message_layout.setContentsMargins(10, 8, 10, 8)
        message_layout.setSpacing(4)

        message_title = QLabel("运行提示", self.main_message_frame)
        message_title.setObjectName("mainMessageTitle")
        self.main_message_label.setWordWrap(True)

        message_layout.addWidget(message_title)
        message_layout.addWidget(self.main_message_label)

    def _build_tray_icon(self) -> None:
        """创建 Windows 右下角系统托盘图标。

        QSystemTrayIcon 必须被对象属性持有，不能只放在局部变量里。
        如果局部变量在函数结束后被回收，托盘图标也会随之消失。
        """
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._show_main_message("当前系统不支持托盘图标")
            return

        tray_icon_path = TRAY_ICON_PATH if TRAY_ICON_PATH.exists() else APP_ICON_PATH
        if not tray_icon_path.exists():
            self._show_main_message("未找到托盘图标资源")
            return

        self.tray_icon = QSystemTrayIcon(QIcon(str(tray_icon_path)), self)
        self.tray_icon.setToolTip("EasyFrp")

        tray_menu = QMenu(self)

        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self._show_from_tray)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(lambda: self.close())

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._handle_tray_icon_activated)
        self.tray_icon.show()

    def _connect_signals(self) -> None:
        """连接主窗口级别的信号。"""
        self.sidebar.currentRowChanged.connect(self._handle_sidebar_row_changed)
        self.frpc_control_view.status_message_changed.connect(
            self._show_main_message
        )
        self.frpc_config_view.status_message_changed.connect(
            self._show_main_message
        )
        self.frps_control_view.status_message_changed.connect(
            self._show_main_message
        )
        self.frps_config_view.status_message_changed.connect(
            self._show_main_message
        )
        self.easyfrp_config_view.status_message_changed.connect(
            self._show_main_message
        )
        self.easyfrp_config_view.theme_changed.connect(self._handle_theme_changed)
        self.easyfrp_config_view.settings_changed.connect(
            self._handle_settings_changed
        )

    def _show_main_message(self, message: str) -> None:
        """把全局提示展示在主界面信息块里。"""
        self.main_message_label.setText(message)

    def _handle_filtered_mouse_press(
        self,
        event: QMouseEvent,
        local_position: QPoint,
    ) -> bool:
        if event.button() != Qt.MouseButton.LeftButton:
            return False

        if not self.isMaximized():
            resize_edges = self._resize_edges_at_position(local_position)
            if resize_edges:
                self._resize_edges = resize_edges
                self._resize_start_geometry = self.geometry()
                self._resize_start_position = event.globalPosition().toPoint()
                return True

        if self._is_window_drag_area(local_position):
            self._drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            return True
        return False

    def _handle_filtered_mouse_move(
        self,
        event: QMouseEvent,
        local_position: QPoint,
    ) -> bool:
        if self._resize_edges and event.buttons() & Qt.MouseButton.LeftButton:
            self._resize_window(event.globalPosition().toPoint())
            return True

        if (
            self._drag_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and not self.isMaximized()
        ):
            self.move(event.globalPosition().toPoint() - self._drag_position)
            return True

        self._update_resize_cursor(local_position)
        return False

    def _handle_filtered_mouse_release(
        self,
        _event: QMouseEvent,
        local_position: QPoint,
    ) -> bool:
        was_handling_window = (
            bool(self._resize_edges) or self._drag_position is not None
        )
        self._drag_position = None
        self._resize_edges = set()
        self._update_resize_cursor(local_position)
        return was_handling_window

    def _apply_startup_settings(self) -> None:
        """根据 config/config.json 应用启动时设置。"""
        try:
            settings = EasyfrpConfigService().load_settings()
        except (OSError, ValueError) as error:
            self._refresh_sidebar_for_mode("frpc")
            self._show_main_message(f"读取 EasyFrp 设置失败：{error}")
            return

        client_mode = settings.get("client_mode")
        if client_mode == "frps":
            self._refresh_sidebar_for_mode("frps")
        else:
            client_mode = "frpc"
            self._refresh_sidebar_for_mode("frpc")

        if settings.get("auto_run") is True:
            QTimer.singleShot(0, lambda: self._auto_run_client_mode(client_mode))

    def _auto_run_client_mode(self, client_mode: str) -> None:
        """启动设置中选中的 frpc/frps 进程。"""
        if client_mode == "frps":
            if self.frps_control_view.start_frps():
                self._show_main_message("已按设置自动启动 frps")
            return

        if self.frpc_control_view.start_frpc():
            self._show_main_message("已按设置自动启动 frpc")

    def _refresh_sidebar_for_mode(
        self,
        client_mode: str,
        *,
        selected_page: int | None = None,
    ) -> None:
        """按 frpc/frps 模式刷新侧边栏显示内容。"""
        self._client_mode = "frps" if client_mode == "frps" else "frpc"
        if selected_page is None:
            selected_page = (
                PAGE_FRPS_CONTROL
                if self._client_mode == "frps"
                else PAGE_FRPC_CONTROL
            )

        if self._client_mode == "frps":
            items = [
                ("frps 控制", PAGE_FRPS_CONTROL),
                ("frps 配置", PAGE_FRPS_CONFIG),
                ("设置", PAGE_SETTINGS),
            ]
        else:
            items = [
                ("frpc 控制", PAGE_FRPC_CONTROL),
                ("frpc 配置", PAGE_FRPC_CONFIG),
                ("设置", PAGE_SETTINGS),
            ]

        self.sidebar.blockSignals(True)
        self.sidebar.clear()
        self._sidebar_page_routes = []
        for label, page_index in items:
            self.sidebar.addItem(QListWidgetItem(label))
            self._sidebar_page_routes.append(page_index)

        try:
            row = self._sidebar_page_routes.index(selected_page)
        except ValueError:
            row = 0
        self.sidebar.setCurrentRow(row)
        self.sidebar.blockSignals(False)
        self.page_stack.setCurrentIndex(self._sidebar_page_routes[row])

    def _handle_sidebar_row_changed(self, row: int) -> None:
        """把侧边栏行号映射到真实页面索引。"""
        if row < 0 or row >= len(self._sidebar_page_routes):
            return
        self.page_stack.setCurrentIndex(self._sidebar_page_routes[row])

    def _handle_settings_changed(self, settings: dict) -> None:
        """设置保存后，根据客户端模式刷新侧边栏。"""
        current_page = self.page_stack.currentIndex()
        client_mode = settings.get("client_mode")
        if client_mode not in {"frpc", "frps"}:
            client_mode = self._client_mode

        selected_page = current_page if current_page == PAGE_SETTINGS else None
        self._refresh_sidebar_for_mode(client_mode, selected_page=selected_page)

    def _handle_theme_changed(self, theme_key: str) -> None:
        """Apply a selected UI variant from the settings page."""
        application = QApplication.instance()
        if application is None:
            return

        variant = apply_app_theme(application, theme_key)
        self._show_main_message(f"界面风格已切换为：{variant.name}")

    def _toggle_maximized(self) -> None:
        """切换窗口最大化和普通大小。"""
        if self.isMaximized():
            self.showNormal()
            self.maximize_button.setText("□")
            self.maximize_button.setToolTip("最大化")
            return

        self.showMaximized()
        self.maximize_button.setText("❐")
        self.maximize_button.setToolTip("还原")

    def _is_window_drag_area(self, position: QPoint) -> bool:
        """判断鼠标位置是否落在可拖动的主界面顶部空白区域。"""
        local_position = self.window_controls_container.mapFrom(self, position)
        return self.window_controls_container.rect().contains(local_position)

    def _resize_edges_at_position(self, position: QPoint) -> set[str]:
        """返回鼠标所在位置对应的窗口缩放边。"""
        if self.isMaximized():
            return set()

        rect = self.rect()
        edges: set[str] = set()
        if position.x() <= RESIZE_MARGIN:
            edges.add("left")
        elif position.x() >= rect.width() - RESIZE_MARGIN:
            edges.add("right")

        if position.y() <= RESIZE_MARGIN:
            edges.add("top")
        elif position.y() >= rect.height() - RESIZE_MARGIN:
            edges.add("bottom")
        return edges

    def _update_resize_cursor(self, position: QPoint) -> None:
        """根据鼠标位置更新无边框窗口的缩放光标。"""
        if self._drag_position is not None or self.isMaximized():
            self.unsetCursor()
            return

        edges = self._resize_edges or self._resize_edges_at_position(position)
        if {"top", "left"}.issubset(edges) or {"bottom", "right"}.issubset(edges):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif {"top", "right"}.issubset(edges) or {"bottom", "left"}.issubset(edges):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif "left" in edges or "right" in edges:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif "top" in edges or "bottom" in edges:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()

    def _resize_window(self, global_position: QPoint) -> None:
        """按鼠标拖拽距离调整无边框窗口大小。"""
        delta = global_position - self._resize_start_position
        geometry = QRect(self._resize_start_geometry)

        if "left" in self._resize_edges:
            max_left = geometry.right() - self.minimumWidth() + 1
            geometry.setLeft(
                min(max_left, self._resize_start_geometry.left() + delta.x())
            )
        if "right" in self._resize_edges:
            min_right = geometry.left() + self.minimumWidth() - 1
            geometry.setRight(
                max(min_right, self._resize_start_geometry.right() + delta.x())
            )
        if "top" in self._resize_edges:
            max_top = geometry.bottom() - self.minimumHeight() + 1
            geometry.setTop(
                min(max_top, self._resize_start_geometry.top() + delta.y())
            )
        if "bottom" in self._resize_edges:
            min_bottom = geometry.top() + self.minimumHeight() - 1
            geometry.setBottom(
                max(min_bottom, self._resize_start_geometry.bottom() + delta.y())
            )

        self.setGeometry(geometry)

    def _handle_tray_icon_activated(
        self,
        reason: QSystemTrayIcon.ActivationReason,
    ) -> None:
        """响应用户点击托盘图标。

        Windows 上常见交互是双击托盘图标恢复主窗口。
        右键菜单由 Qt 自动处理，不需要在这里额外判断。
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self) -> None:
        """从托盘菜单或双击托盘图标恢复主窗口。"""
        self.showNormal()
        self.raise_()
        self.activateWindow()
