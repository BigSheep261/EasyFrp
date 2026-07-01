"""frps 控制页面。"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from frp_gui.ui.panels.frps_open import FrpsOpenPanel


class FrpsControlView(QWidget):
    """侧边栏中的 frps 控制页面。"""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_label = QLabel("FRP 服务端控制", self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.description_label = QLabel(
            "默认使用 runtime/frps.exe 和 config/frps.toml 启动服务端。",
            self,
        )
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        self.frps_open_panel = FrpsOpenPanel(self)
        self.frps_open_panel.status_message_changed.connect(
            self.status_message_changed.emit
        )

        self._build_ui()

    def shutdown(self) -> None:
        """让页面内的功能模块释放运行中的资源。"""
        self.frps_open_panel.shutdown()

    def _build_ui(self) -> None:
        """创建页面级布局。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.frps_open_panel, stretch=1)
