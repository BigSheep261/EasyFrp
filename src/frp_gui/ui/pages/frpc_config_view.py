"""frpc TOML 配置编辑页面。"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from frp_gui.ui.panels.frpc_toml_editor import FrpcTomlEditorPanel


class FrpcConfigView(QWidget):
    """侧边栏中的完整页面，内部放置 frpc TOML 编辑面板。"""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_label = QLabel("frpc 配置编辑", self)
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.description_label = QLabel(
            "读取 config/frpc.toml，编辑后点击保存会写回原文件。",
            self,
        )
        self.description_label.setWordWrap(True)

        self.editor_panel = FrpcTomlEditorPanel(self)
        self.editor_panel.status_message_changed.connect(
            self.status_message_changed.emit
        )

        self._build_ui()

    def _build_ui(self) -> None:
        """创建页面级布局。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.editor_panel, stretch=1)
