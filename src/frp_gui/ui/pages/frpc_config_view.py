"""frpc 配置管理页面。"""

# Qt 信号用于向外转发状态，基础控件负责组织页面标题与内容表面。
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

# 配置管理面板封装页面中的实际配置查看和启动配置操作。
from frp_gui.ui.panels.frpc_config_manager import FrpcConfigManagerPanel


class FrpcConfigView(QWidget):
    """组合页面标题与配置管理面板，并向主窗口转发操作状态。"""

    # 统一暴露页面状态信号，使主窗口不必了解内部面板的实现细节。
    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化 frpc 配置管理页面及其子控件。

        Args:
            parent: 负责管理当前页面生命周期的父级 Qt 控件。
        """
        # 建立 Qt 父子关系，确保页面销毁时自动回收其子控件。
        super().__init__(parent)

        # 创建醒目的页面标题，并单独调整字号和字重。
        self.title_label = QLabel("Frpc 配置管理", self)
        self.title_label.setObjectName("frpcManagerTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(26)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        # 用辅助说明概括页面用途，并允许窄窗口下自动换行。
        self.description_label = QLabel(
            "查看当前配置和启动配置",
            self,
        )
        self.description_label.setObjectName("frpcManagerDescription")
        self.description_label.setWordWrap(True)

        # 嵌入承担实际配置管理工作的面板。
        self.config_panel = FrpcConfigManagerPanel(self)

        # 将面板消息原样上抛，供主窗口的统一提示区展示。
        self.config_panel.status_message_changed.connect(
            self.status_message_changed.emit
        )

        # 子控件准备完成后再统一组装布局。
        self._build_ui()

    def _build_ui(self) -> None:
        """创建页面级布局。"""
        # 外层布局提供页面与主窗口边缘之间的统一留白。
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(28, 28, 28, 28)
        page_layout.setSpacing(0)

        # 使用带对象名的框架承载内容，便于样式表绘制独立表面。
        shell_frame = QFrame(self)
        shell_frame.setObjectName("frpcConfigPageShell")
        shell_frame.setFrameShape(QFrame.Shape.StyledPanel)

        # 内层布局控制标题、说明和配置面板之间的间距。
        shell_layout = QVBoxLayout(shell_frame)
        shell_layout.setContentsMargins(24, 24, 24, 24)
        shell_layout.setSpacing(18)

        # 按视觉阅读顺序排列页面信息，并让配置面板占用剩余空间。
        shell_layout.addWidget(self.title_label)
        shell_layout.addWidget(self.description_label)
        shell_layout.addWidget(self.config_panel, stretch=1)

        # 让内容表面随页面一起伸展，维持完整可编辑区域。
        page_layout.addWidget(shell_frame, stretch=1)
