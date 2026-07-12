"""frpc 控制页面。

pages 层表示“一个完整页面”。
这个页面会导入 panels/frpc_open.py 中的 FrpcOpenPanel，
然后负责设置标题、说明文案，以及把功能模块摆放到合适的位置。
"""

# Qt 信号和基础控件用于构建页面外壳并将内部状态传递给主窗口。
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

# 控制面板封装 frpc 进程的启动、停止与运行状态管理。
from frp_gui.ui.panels.frpc_open import FrpcOpenPanel


class FrpcControlView(QWidget):
    """组合 frpc 控制面板，并为主窗口提供启动与关闭入口。"""

    # 页面把 panel 的状态消息继续向外转发。
    # main_window 不需要知道 panel 内部结构，只监听页面信号即可。
    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化 frpc 控制页面及其业务面板。

        Args:
            parent: 负责管理当前页面生命周期的父级 Qt 控件。
        """
        # 建立 Qt 父子关系，使页面与主窗口共享生命周期。
        super().__init__(parent)

        # 创建页面标题，并调整为适合一级标题的字体样式。
        self.title_label = QLabel("FRP 客户端控制", self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        # 告知用户默认使用的程序和配置路径，并支持自动换行。
        self.description_label = QLabel(
            "默认使用 runtime/frpc.exe 和 config/frpc.toml 启动客户端。",
            self,
        )
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        # 实际的进程控制和状态展示由独立面板负责。
        self.frpc_open_panel = FrpcOpenPanel(self)

        # 将面板产生的运行消息转发到页面外部的统一提示区。
        self.frpc_open_panel.status_message_changed.connect(
            self.status_message_changed.emit
        )

        # 控件创建完成后统一组装页面布局。
        self._build_ui()

    def shutdown(self) -> None:
        """让页面内的功能模块释放运行中的资源。"""
        # 委托面板终止其管理的进程，避免窗口退出后留下后台任务。
        self.frpc_open_panel.shutdown()

    def start_frpc(self) -> bool:
        """请求页面内的功能模块启动 frpc。"""
        # 直接返回面板的启动结果，供自动运行流程判断是否成功。
        return self.frpc_open_panel.start_frpc()

    def _build_ui(self) -> None:
        """创建页面级布局。"""
        # 外层纵向布局统一页面留白和各区域间距。
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        # 按标题、说明、操作面板的阅读顺序排列，并扩展操作区。
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.frpc_open_panel, stretch=1)
