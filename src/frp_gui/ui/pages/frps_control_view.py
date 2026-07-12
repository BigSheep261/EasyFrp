"""frps 控制页面。"""

# Qt 信号和基础控件用于构建页面外壳并向主窗口转发运行消息。
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

# 控制面板封装 frps 服务端进程及其状态管理。
from frp_gui.ui.panels.frps_open import FrpsOpenPanel


class FrpsControlView(QWidget):
    """组合 frps 控制面板，并为主窗口提供启动与关闭入口。"""

    # 将内部面板的运行消息提升为页面级信号，供主窗口统一消费。
    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化 frps 控制页面及其业务面板。

        Args:
            parent: 负责管理当前页面生命周期的父级 Qt 控件。
        """
        # 建立 Qt 父子关系，使页面和主窗口同步释放资源。
        super().__init__(parent)

        # 创建页面标题，并调整为醒目的一级标题样式。
        self.title_label = QLabel("FRP 服务端控制", self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        # 提示默认可执行文件与配置文件位置，并允许窄窗口下换行。
        self.description_label = QLabel(
            "默认使用 runtime/frps.exe 和 config/frps.toml 启动服务端。",
            self,
        )
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        # 实际的服务端进程控制逻辑由独立面板封装。
        self.frps_open_panel = FrpsOpenPanel(self)

        # 将面板产生的消息转发给主窗口中的全局提示区。
        self.frps_open_panel.status_message_changed.connect(
            self.status_message_changed.emit
        )

        # 子控件准备好后统一创建页面布局。
        self._build_ui()

    def shutdown(self) -> None:
        """让页面内的功能模块释放运行中的资源。"""
        # 委托面板停止其管理的服务端进程，保证应用能够干净退出。
        self.frps_open_panel.shutdown()

    def start_frps(self) -> bool:
        """请求页面内的功能模块启动 frps。"""
        # 保留面板返回的成功状态，供主窗口自动运行逻辑使用。
        return self.frps_open_panel.start_frps()

    def _build_ui(self) -> None:
        """创建页面级布局。"""
        # 外层纵向布局为各控制页面提供一致的留白和节奏。
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        # 按标题、说明、操作面板排列，并让操作面板填充剩余区域。
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.frps_open_panel, stretch=1)
