"""EasyFrp 仪表盘页面。"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EasyFrpDashBoard(QWidget):
    """展示 EasyFrp 的总体运行状态和快捷信息。"""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_label = QLabel("Dashboard", self)
        self.title_label.setObjectName("pageTitle")

        self.description_label = QLabel(
            "查看 EasyFrp 的运行状态和常用信息。",
            self,
        )
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        self._build_ui()

    def _build_ui(self) -> None:
        """构建 Dashboard 页面布局。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addStretch()