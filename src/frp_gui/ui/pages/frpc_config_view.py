"""frpc 配置管理页面。"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from frp_gui.ui.panels.frpc_config_manager import FrpcConfigManagerPanel


class FrpcConfigView(QWidget):
    """侧边栏中的 frpc 配置管理页面。"""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_label = QLabel("Frpc 配置管理", self)
        self.title_label.setObjectName("frpcManagerTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(26)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.description_label = QLabel(
            "查看当前配置和启动配置",
            self,
        )
        self.description_label.setObjectName("frpcManagerDescription")
        self.description_label.setWordWrap(True)

        self.config_panel = FrpcConfigManagerPanel(self)
        self.config_panel.status_message_changed.connect(
            self.status_message_changed.emit
        )

        self._build_ui()

    def _build_ui(self) -> None:
        """创建页面级布局。"""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(28, 28, 28, 28)
        page_layout.setSpacing(0)

        shell_frame = QFrame(self)
        shell_frame.setObjectName("frpcConfigPageShell")
        shell_frame.setFrameShape(QFrame.Shape.StyledPanel)

        shell_layout = QVBoxLayout(shell_frame)
        shell_layout.setContentsMargins(24, 24, 24, 24)
        shell_layout.setSpacing(18)

        shell_layout.addWidget(self.title_label)
        shell_layout.addWidget(self.description_label)
        shell_layout.addWidget(self.config_panel, stretch=1)

        page_layout.addWidget(shell_frame, stretch=1)
