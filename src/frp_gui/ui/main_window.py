"""组装应用页面、侧边栏及无边框窗口交互的顶层主窗口。

main_window 是整个 UI 的外壳。
它不再直接写 frpc 的启动/停止细节，只负责：
1. 创建左侧侧边栏。
2. 创建右侧页面容器。
3. 根据侧边栏选择切换不同 page。
"""

# Qt 核心类型负责事件、坐标、几何和延迟调度，界面类型用于搭建窗口外壳。
from PyQt6.QtCore import QEvent, QObject, QPoint, QRect, Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# 设置服务提供启动偏好，页面类则作为主窗口页面栈的固定成员。
from frp_gui.backend.settings.settings_service import SettingsService
from frp_gui.ui.pages.setting_view import EasyfrpConfigView
from frp_gui.ui.pages.frpc_config_view import FrpcConfigView
from frp_gui.ui.pages.frpc_control_view import FrpcControlView
from frp_gui.ui.pages.frps_config_view import FrpsConfigView
from frp_gui.ui.pages.frps_control_view import FrpsControlView

# 集中定义窗口视觉与尺寸约束，便于后续统一调整无边框窗口体验。
WINDOW_OPACITY = 1
MIN_WINDOW_WIDTH = 760
MIN_WINDOW_HEIGHT = 520
RESIZE_MARGIN = 8

# 页面索引必须与加入 QStackedWidget 的顺序一致，用于侧边栏路由跳转。
PAGE_FRPC_CONTROL = 0
PAGE_FRPC_CONFIG = 1
PAGE_FRPS_CONTROL = 2
PAGE_FRPS_CONFIG = 3
PAGE_SETTINGS = 4


class MainWindow(QMainWindow):
    """承载全部业务页面，并协调导航、设置及无边框窗口行为。"""

    def __init__(self) -> None:
        """初始化主窗口控件、页面、信号以及启动设置。"""
        # 先完成 QMainWindow 的底层初始化，再配置窗口属性和子控件。
        super().__init__()

        # 使用自绘控制区代替系统标题栏，并设置基础窗口外观与尺寸。
        self.setWindowTitle("EasyFrp")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # 设置整个主窗口透明度。Qt 使用 0.0 到 1.0 表示窗口不透明度：
        # 1.0 表示完全不透明，0.75 表示约 75% 不透明，也就是能看到一些背景。
        self.setWindowOpacity(WINDOW_OPACITY)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(960, 640)

        # 左右主区域和自绘标题栏控件共同构成窗口外壳。
        self.sidebar_container = QWidget(self)
        self.content_container = QWidget(self)
        self.window_controls_container = QWidget(self)
        self.minimize_button = QPushButton("—", self)
        self.maximize_button = QPushButton("□", self)
        self.close_button = QPushButton("×", self)

        # 侧边栏底部提示块集中显示各页面上报的运行消息。
        self.main_message_frame = QFrame(self)
        self.main_message_label = QLabel("就绪", self)

        # 保存拖动和缩放手势的起始状态，以便连续鼠标事件共享上下文。
        self._drag_position: QPoint | None = None
        self._resize_edges: set[str] = set()
        self._resize_start_geometry = QRect()
        self._resize_start_position = QPoint()

        # 路由表把动态侧边栏行号映射到固定页面索引。
        self._sidebar_page_routes: list[int] = []

        # 默认按客户端模式构建导航，加载设置后再按实际值刷新。
        self._client_mode = "frpc"

        # 为主要容器和窗口按钮设置稳定对象名，供样式表精确匹配。
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
        # 各页面提前创建并长期保留，以维持编辑状态和进程控制状态。
        self.frpc_control_view = FrpcControlView(self)
        self.frpc_config_view = FrpcConfigView(self)
        self.frps_control_view = FrpsControlView(self)
        self.frps_config_view = FrpsConfigView(self)
        self.easyfrp_config_view = EasyfrpConfigView(self)

        # 严格按布局、事件、信号、设置的顺序完成主窗口装配。
        self._build_ui()
        self._install_window_event_filters()
        self._connect_signals()
        self._apply_startup_settings()

    def closeEvent(self, event: QCloseEvent) -> None:
        """确保关闭 GUI 时，页面内正在运行的进程也能退出。"""
        # 分别通知客户端和服务端控制页释放其托管的进程资源。
        self.frpc_control_view.shutdown()
        self.frps_control_view.shutdown()

        # 资源清理完成后交还 Qt 默认关闭流程处理事件。
        super().closeEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """记录无边框窗口的拖动起点。"""
        # 非最大化状态下优先判断边缘缩放，避免与顶部拖动手势冲突。
        if event.button() == Qt.MouseButton.LeftButton and not self.isMaximized():
            resize_edges = self._resize_edges_at_position(event.position().toPoint())
            if resize_edges:
                # 缓存命中的边、原始几何和全局坐标，用于后续计算尺寸增量。
                self._resize_edges = resize_edges
                self._resize_start_geometry = self.geometry()
                self._resize_start_position = event.globalPosition().toPoint()

                # 当前事件已转化为窗口缩放手势，不再交给子类默认逻辑。
                event.accept()
                return

        # 未触发缩放时，标题控制区的空白位置可用于拖动整个窗口。
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._is_window_drag_area(event.position().toPoint())
        ):
            # 保存鼠标相对窗口左上角的偏移，移动时可避免窗口跳变。
            self._drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

            # 标记事件已处理，防止默认控件行为重复响应。
            event.accept()
            return

        # 其他按键或区域保持 QMainWindow 的默认鼠标按下行为。
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """拖动主界面顶部空白区域移动窗口。"""
        # 已记录缩放边且左键仍按下时，持续根据全局坐标调整窗口尺寸。
        if self._resize_edges and event.buttons() & Qt.MouseButton.LeftButton:
            self._resize_window(event.globalPosition().toPoint())
            event.accept()
            return

        # 已开始标题栏拖动时，根据保存的偏移移动非最大化窗口。
        if (
            self._drag_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and not self.isMaximized()
        ):
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return

        # 没有活动手势时仅更新边缘光标，并保留默认移动事件处理。
        self._update_resize_cursor(event.position().toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """结束无边框窗口拖动。"""
        # 清空两类手势状态，使下一次按下从全新几何信息开始。
        self._drag_position = None
        self._resize_edges = set()

        # 根据释放位置恢复或更新缩放方向光标。
        self._update_resize_cursor(event.position().toPoint())

        # 继续执行 Qt 的标准释放事件流程。
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """双击主界面顶部空白区域时切换最大化。"""
        # 仅响应标题控制区内、且不位于缩放边缘的左键双击。
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._is_window_drag_area(event.position().toPoint())
            and not self._resize_edges_at_position(event.position().toPoint())
        ):
            self._toggle_maximized()
            event.accept()
            return

        # 其余双击事件交给父类，避免影响页面内部控件交互。
        super().mouseDoubleClickEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """让无边框窗口在子控件区域也能拖动和缩放。"""
        # 只处理属于当前窗口的 QWidget，其他对象沿用自身事件链。
        if not isinstance(watched, QWidget) or watched.window() is not self:
            return super().eventFilter(watched, event)

        # 键盘、绘制等非鼠标事件不参与窗口拖动与缩放。
        if not isinstance(event, QMouseEvent):
            return super().eventFilter(watched, event)

        # 标题栏按钮必须保留正常点击行为，不能被窗口手势截获。
        if watched in {
            self.minimize_button,
            self.maximize_button,
            self.close_button,
        }:
            return super().eventFilter(watched, event)

        # 把子控件局部坐标换算为主窗口坐标，统一进行边缘和拖动区判断。
        local_position = watched.mapTo(self, event.position().toPoint())

        # 按事件阶段分派给共享处理器，并用返回值决定是否拦截事件。
        if event.type() == QEvent.Type.MouseButtonPress:
            return self._handle_filtered_mouse_press(event, local_position)
        if event.type() == QEvent.Type.MouseMove:
            return self._handle_filtered_mouse_move(event, local_position)
        if event.type() == QEvent.Type.MouseButtonRelease:
            return self._handle_filtered_mouse_release(event, local_position)

        # 未关注的鼠标事件继续沿 Qt 默认过滤链传播。
        return super().eventFilter(watched, event)

    def _build_ui(self) -> None:
        """搭建主窗口外壳布局。"""
        # 中央控件使用零边距横向布局，让侧边栏与内容区紧密衔接。
        central_widget = QWidget(self)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 先分别构建导航、页面栈和右侧容器，再加入顶层布局。
        self._build_sidebar()
        self._build_pages()
        self._build_content_container()

        # 侧边栏保持固定宽度，内容容器伸展填满剩余窗口区域。
        main_layout.addWidget(self.sidebar_container)
        main_layout.addWidget(self.content_container, stretch=1)

        # 将组装完成的外壳设为 QMainWindow 唯一中央控件。
        self.setCentralWidget(central_widget)

    def _build_content_container(self) -> None:
        """创建右侧内容区，并放入窗口控制按钮和页面容器。"""
        # 右侧区域以零间隙纵向堆叠自绘控制栏和业务页面。
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 在加入布局前完成控制按钮属性和信号配置。
        self._build_window_controls()

        # 控制栏保持自身高度，页面栈伸展占据全部剩余空间。
        content_layout.addWidget(self.window_controls_container)
        content_layout.addWidget(self.page_stack, stretch=1)

    def _install_window_event_filters(self) -> None:
        """给窗口和子控件安装鼠标过滤器，用于无边框缩放。"""
        # 收集当前已创建的全部子控件，使鼠标位于其上方时仍可识别窗口边缘。
        widgets = [self, *self.findChildren(QWidget)]

        # QListWidget 的实际鼠标事件由 viewport 接收，必要时单独补入列表。
        if self.sidebar.viewport() not in widgets:
            widgets.append(self.sidebar.viewport())

        # 开启移动跟踪并由主窗口过滤事件，即使未按键也能更新缩放光标。
        for widget in widgets:
            widget.setMouseTracking(True)
            widget.installEventFilter(self)

    def _build_window_controls(self) -> None:
        """把原生标题栏按钮放到主界面右上角。"""
        # 控制栏使用固定高度与对象名，形成可由样式表定制的标题区域。
        self.window_controls_container.setObjectName("windowControlsContainer")
        self.window_controls_container.setFixedHeight(36)

        # 左侧伸缩项把三个控制按钮推到窗口右上角。
        controls_layout = QHBoxLayout(self.window_controls_container)
        controls_layout.setContentsMargins(0, 4, 8, 4)
        controls_layout.setSpacing(2)
        controls_layout.addStretch()

        # 工具提示补充符号按钮的含义，提升可理解性与可访问性。
        self.minimize_button.setToolTip("最小化")
        self.maximize_button.setToolTip("最大化")
        self.close_button.setToolTip("关闭")

        # 将按钮分别绑定到窗口最小化、自定义最大化切换和关闭动作。
        self.minimize_button.clicked.connect(self.showMinimized)
        self.maximize_button.clicked.connect(self._toggle_maximized)
        self.close_button.clicked.connect(self.close)

        # 按常见桌面窗口顺序排列最小化、最大化和关闭按钮。
        controls_layout.addWidget(self.minimize_button)
        controls_layout.addWidget(self.maximize_button)
        controls_layout.addWidget(self.close_button)

    def _build_sidebar(self) -> None:
        """创建侧边栏。

        侧边栏的条目会根据当前客户端模式动态生成，实际页面映射由
        ``self._sidebar_page_routes`` 维护。
        """
        # 固定导航宽度，避免页面切换或窗口拉伸造成入口位置跳动。
        self.sidebar_container.setFixedWidth(180)

        # 纵向布局让导航列表伸展、消息提示块固定在底部。
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(12, 14, 12, 10)
        sidebar_layout.setSpacing(10)

        # 列表只允许选择一个页面，并用对象名和间距统一导航样式。
        self.sidebar.setObjectName("sidebarNavigation")
        self.sidebar.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.sidebar.setSpacing(4)

        # 导航占据剩余高度，公共消息块始终位于侧边栏底部。
        sidebar_layout.addWidget(self.sidebar, stretch=1)
        sidebar_layout.addWidget(self.main_message_frame)

        # 单独构建消息块的内部标题与正文布局。
        self._build_main_message()

    def _build_pages(self) -> None:
        """把页面加入右侧页面容器。"""
        # 加入顺序须与模块顶部的 PAGE_* 常量一一对应。
        self.page_stack.addWidget(self.frpc_control_view)
        self.page_stack.addWidget(self.frpc_config_view)
        self.page_stack.addWidget(self.frps_control_view)
        self.page_stack.addWidget(self.frps_config_view)
        self.page_stack.addWidget(self.easyfrp_config_view)

    def _build_main_message(self) -> None:
        """创建主界面内的信息提示块，替代窗口底部状态栏。"""
        # 配置提示块表面和正文对象名，交由全局样式表控制层次。
        self.main_message_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.main_message_frame.setObjectName("mainMessageFrame")
        self.main_message_label.setObjectName("mainMessageText")

        # 使用紧凑纵向布局容纳固定标题和可变状态正文。
        message_layout = QVBoxLayout(self.main_message_frame)
        message_layout.setContentsMargins(10, 8, 10, 8)
        message_layout.setSpacing(4)

        # 标题用于标识区域用途，正文允许长错误信息自动换行。
        message_title = QLabel("运行提示", self.main_message_frame)
        message_title.setObjectName("mainMessageTitle")
        self.main_message_label.setWordWrap(True)

        # 先显示区域标题，再展示由各页面动态更新的消息。
        message_layout.addWidget(message_title)
        message_layout.addWidget(self.main_message_label)

    def _connect_signals(self) -> None:
        """连接主窗口级别的信号。"""
        # 侧边栏只提供可见行号，处理器负责映射到真实页面索引。
        self.sidebar.currentRowChanged.connect(self._handle_sidebar_row_changed)

        # 所有业务页面共用侧边栏底部的主消息展示函数。
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

        # 保存设置后按新的 frpc/frps 模式重建侧边栏入口。
        self.easyfrp_config_view.settings_changed.connect(
            self._handle_settings_changed
        )

    def _show_main_message(self, message: str) -> None:
        """把全局提示展示在主界面信息块里。"""
        # 直接替换旧消息，使提示区始终反映最近一次页面操作结果。
        self.main_message_label.setText(message)

    def _handle_filtered_mouse_press(
        self,
        event: QMouseEvent,
        local_position: QPoint,
    ) -> bool:
        """处理来自子控件的鼠标按下事件，并尝试开始缩放或拖动。

        Args:
            event: 事件过滤器捕获的鼠标按下事件。
            local_position: 鼠标位置换算到主窗口后的坐标。

        Returns:
            当前事件是否已被窗口手势接管。
        """
        # 只有左键用于桌面窗口拖动和缩放，其他按键继续向下传播。
        if event.button() != Qt.MouseButton.LeftButton:
            return False

        # 非最大化窗口优先检测边缘缩放手势。
        if not self.isMaximized():
            resize_edges = self._resize_edges_at_position(local_position)
            if resize_edges:
                # 缓存命中边缘及手势起点，供后续移动事件计算新几何。
                self._resize_edges = resize_edges
                self._resize_start_geometry = self.geometry()
                self._resize_start_position = event.globalPosition().toPoint()
                return True

        # 未命中边缘时，仅允许在自绘标题控制区启动窗口拖动。
        if self._is_window_drag_area(local_position):
            # 保存鼠标相对窗口左上角的偏移，确保拖动过程平滑无跳变。
            self._drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            return True

        # 普通页面区域不属于窗口手势，应保留原控件交互。
        return False

    def _handle_filtered_mouse_move(
        self,
        event: QMouseEvent,
        local_position: QPoint,
    ) -> bool:
        """处理来自子控件的鼠标移动事件并延续活动窗口手势。

        Args:
            event: 事件过滤器捕获的鼠标移动事件。
            local_position: 鼠标位置换算到主窗口后的坐标。

        Returns:
            移动事件是否已用于调整窗口。
        """
        # 已启动边缘缩放且左键仍按下时，实时更新窗口几何。
        if self._resize_edges and event.buttons() & Qt.MouseButton.LeftButton:
            self._resize_window(event.globalPosition().toPoint())
            return True

        # 已启动标题栏拖动时移动普通窗口，最大化状态不允许直接平移。
        if (
            self._drag_position is not None
            and event.buttons() & Qt.MouseButton.LeftButton
            and not self.isMaximized()
        ):
            self.move(event.globalPosition().toPoint() - self._drag_position)
            return True

        # 没有活动手势时只更新光标形状，不拦截子控件的移动事件。
        self._update_resize_cursor(local_position)
        return False

    def _handle_filtered_mouse_release(
        self,
        _event: QMouseEvent,
        local_position: QPoint,
    ) -> bool:
        """结束由事件过滤器接管的窗口手势并清理临时状态。

        Args:
            _event: 当前未读取、但为保持处理器签名而保留的释放事件。
            local_position: 鼠标释放位置换算到主窗口后的坐标。

        Returns:
            释放前是否存在需要拦截的拖动或缩放手势。
        """
        # 在清空状态前记录是否曾接管手势，以决定事件是否继续传播。
        was_handling_window = (
            bool(self._resize_edges) or self._drag_position is not None
        )

        # 释放鼠标后同时终止拖动和缩放，避免残留状态影响下一次操作。
        self._drag_position = None
        self._resize_edges = set()

        # 根据释放位置显示正确的边缘光标或恢复普通光标。
        self._update_resize_cursor(local_position)

        # 仅吞掉本次窗口手势的释放事件，普通点击仍交还原控件。
        return was_handling_window

    def _apply_startup_settings(self) -> None:
        """根据 config/config.json 应用启动时设置。"""
        # 读取失败不阻止窗口显示，而是回退到默认客户端导航并提示原因。
        try:
            settings = SettingsService().load_settings()
        except (OSError, ValueError) as error:
            self._refresh_sidebar_for_mode("frpc")
            self._show_main_message(f"读取 EasyFrp 设置失败：{error}")
            return

        # 仅认可明确的 frps 值，其余缺失或异常值统一按 frpc 处理。
        client_mode = settings.get("client_mode")
        if client_mode == "frps":
            self._refresh_sidebar_for_mode("frps")
        else:
            client_mode = "frpc"
            self._refresh_sidebar_for_mode("frpc")

        # 延迟到事件循环启动后再自动运行，确保全部控件已经完成初始化。
        if settings.get("auto_run") is True:
            QTimer.singleShot(0, lambda: self._auto_run_client_mode(client_mode))

    def _auto_run_client_mode(self, client_mode: str) -> None:
        """启动设置中选中的 frpc/frps 进程。"""
        # 服务端模式委托 frps 页面启动，成功时更新全局提示。
        if client_mode == "frps":
            if self.frps_control_view.start_frps():
                self._show_main_message("已按设置自动启动 frps")

            # frps 分支处理完即返回，避免继续执行默认客户端分支。
            return

        # 其他模式按 frpc 启动，并仅在成功时报告自动运行结果。
        if self.frpc_control_view.start_frpc():
            self._show_main_message("已按设置自动启动 frpc")

    def _refresh_sidebar_for_mode(
        self,
        client_mode: str,
        *,
        selected_page: int | None = None,
    ) -> None:
        """按 frpc/frps 模式刷新侧边栏显示内容。

        Args:
            client_mode: 期望展示的客户端或服务端模式标识。
            selected_page: 刷新后希望保留的固定页面索引；省略时选择控制页。
        """
        # 将任意非 frps 输入规范化为默认 frpc，保持内部状态可预测。
        self._client_mode = "frps" if client_mode == "frps" else "frpc"

        # 未指定保留页面时，默认定位到当前模式对应的控制页。
        if selected_page is None:
            selected_page = (
                PAGE_FRPS_CONTROL
                if self._client_mode == "frps"
                else PAGE_FRPC_CONTROL
            )

        # 两种模式只展示各自相关页面，同时都保留公共设置入口。
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

        # 重建列表期间屏蔽行变化信号，避免中间状态触发错误页面切换。
        self.sidebar.blockSignals(True)
        self.sidebar.clear()
        self._sidebar_page_routes = []

        # 同步创建可见条目和对应固定页面索引，维持严格的一一映射。
        for label, page_index in items:
            self.sidebar.addItem(QListWidgetItem(label))
            self._sidebar_page_routes.append(page_index)

        # 若期望页面不属于新模式，则安全回退到首个控制页入口。
        try:
            row = self._sidebar_page_routes.index(selected_page)
        except ValueError:
            row = 0

        # 设置选中行后恢复信号，并显式同步页面栈以弥补屏蔽期间的通知。
        self.sidebar.setCurrentRow(row)
        self.sidebar.blockSignals(False)
        self.page_stack.setCurrentIndex(self._sidebar_page_routes[row])

    def _handle_sidebar_row_changed(self, row: int) -> None:
        """把侧边栏行号映射到真实页面索引。"""
        # 清空或重建列表产生的无效行号不应访问路由数组。
        if row < 0 or row >= len(self._sidebar_page_routes):
            return

        # 使用动态路由表切换固定页面栈，而不是假定两者行号相同。
        self.page_stack.setCurrentIndex(self._sidebar_page_routes[row])

    def _handle_settings_changed(self, settings: dict) -> None:
        """设置保存后，根据客户端模式刷新侧边栏。"""
        # 记录刷新前页面，若用户仍在设置页则刷新后保留当前位置。
        current_page = self.page_stack.currentIndex()

        # 读取新模式，并对外部传入的异常值回退到当前有效模式。
        client_mode = settings.get("client_mode")
        if client_mode not in {"frpc", "frps"}:
            client_mode = self._client_mode

        # 仅公共设置页可跨模式保留，业务页应切换到新模式的默认控制页。
        selected_page = current_page if current_page == PAGE_SETTINGS else None
        self._refresh_sidebar_for_mode(client_mode, selected_page=selected_page)

    def _toggle_maximized(self) -> None:
        """切换窗口最大化和普通大小。"""
        # 当前已最大化时恢复普通尺寸，并同步按钮符号与辅助提示。
        if self.isMaximized():
            self.showNormal()
            self.maximize_button.setText("□")
            self.maximize_button.setToolTip("最大化")
            return

        # 普通状态切换为最大化，同时将按钮含义更新为“还原”。
        self.showMaximized()
        self.maximize_button.setText("❐")
        self.maximize_button.setToolTip("还原")

    def _is_window_drag_area(self, position: QPoint) -> bool:
        """判断鼠标位置是否落在可拖动的主界面顶部空白区域。"""
        # 将主窗口坐标转换到控制栏局部坐标，便于使用其矩形直接命中测试。
        local_position = self.window_controls_container.mapFrom(self, position)

        # 整个控制栏背景可拖动，按钮自身由事件过滤器提前排除。
        return self.window_controls_container.rect().contains(local_position)

    def _resize_edges_at_position(self, position: QPoint) -> set[str]:
        """返回鼠标所在位置对应的窗口缩放边。"""
        # 最大化窗口由系统固定占满工作区，不提供自定义边缘缩放。
        if self.isMaximized():
            return set()

        # 以主窗口矩形为基准，收集鼠标进入阈值范围内的水平和垂直边。
        rect = self.rect()
        edges: set[str] = set()

        # 左右边互斥；角落会再叠加一条垂直边形成对角缩放。
        if position.x() <= RESIZE_MARGIN:
            edges.add("left")
        elif position.x() >= rect.width() - RESIZE_MARGIN:
            edges.add("right")

        # 上下边同样互斥，与水平边组合后可识别四个窗口角。
        if position.y() <= RESIZE_MARGIN:
            edges.add("top")
        elif position.y() >= rect.height() - RESIZE_MARGIN:
            edges.add("bottom")

        # 空集合表示普通区域，单边或双边集合分别表示直线或角落缩放。
        return edges

    def _update_resize_cursor(self, position: QPoint) -> None:
        """根据鼠标位置更新无边框窗口的缩放光标。"""
        # 正在拖动或窗口最大化时不展示缩放暗示。
        if self._drag_position is not None or self.isMaximized():
            self.unsetCursor()
            return

        # 活动缩放期间保持起始边方向，否则根据当前鼠标位置即时判断。
        edges = self._resize_edges or self._resize_edges_at_position(position)

        # 左上和右下使用同一正对角线缩放光标。
        if {"top", "left"}.issubset(edges) or {"bottom", "right"}.issubset(edges):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)

        # 右上和左下使用另一方向的对角线缩放光标。
        elif {"top", "right"}.issubset(edges) or {"bottom", "left"}.issubset(edges):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)

        # 单独命中左右边时显示水平尺寸调整光标。
        elif "left" in edges or "right" in edges:
            self.setCursor(Qt.CursorShape.SizeHorCursor)

        # 单独命中上下边时显示垂直尺寸调整光标。
        elif "top" in edges or "bottom" in edges:
            self.setCursor(Qt.CursorShape.SizeVerCursor)

        # 离开所有缩放边缘后恢复控件或系统默认光标。
        else:
            self.unsetCursor()

    def _resize_window(self, global_position: QPoint) -> None:
        """按鼠标拖拽距离调整无边框窗口大小。"""
        # 使用全局坐标差计算本次手势相对按下位置的总位移。
        delta = global_position - self._resize_start_position

        # 从起始几何创建副本，避免连续事件累积舍入或边界误差。
        geometry = QRect(self._resize_start_geometry)

        # 拖动左边时限制其不越过满足最小宽度的最右位置。
        if "left" in self._resize_edges:
            max_left = geometry.right() - self.minimumWidth() + 1
            geometry.setLeft(
                min(max_left, self._resize_start_geometry.left() + delta.x())
            )

        # 拖动右边时限制其不越过满足最小宽度的最左位置。
        if "right" in self._resize_edges:
            min_right = geometry.left() + self.minimumWidth() - 1
            geometry.setRight(
                max(min_right, self._resize_start_geometry.right() + delta.x())
            )

        # 拖动上边时限制其不越过满足最小高度的最下位置。
        if "top" in self._resize_edges:
            max_top = geometry.bottom() - self.minimumHeight() + 1
            geometry.setTop(
                min(max_top, self._resize_start_geometry.top() + delta.y())
            )

        # 拖动下边时限制其不越过满足最小高度的最上位置。
        if "bottom" in self._resize_edges:
            min_bottom = geometry.top() + self.minimumHeight() - 1
            geometry.setBottom(
                max(min_bottom, self._resize_start_geometry.bottom() + delta.y())
            )

        # 四条边完成约束计算后一次性应用新几何，避免界面中间态闪烁。
        self.setGeometry(geometry)
