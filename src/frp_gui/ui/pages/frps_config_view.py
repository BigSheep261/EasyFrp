"""frps TOML 配置管理页面。"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FrpsConfigView(QWidget):
    """侧边栏中的 frps 配置管理页面。"""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_label = QLabel("frps 配置管理", self)
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.description_label = QLabel(
            "用于查看、编辑和保存 config/frps.toml 服务端配置。",
            self,
        )
        self.description_label.setWordWrap(True)

        self.path_label = QLabel("config/frps.toml", self)
        self.path_label.setWordWrap(True)

        self.editor = QPlainTextEdit(self)
        self.editor.setPlaceholderText(
            "frps.toml 内容会显示在这里，文件读写逻辑待接入。"
        )
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.message_label = QLabel("", self)
        self.message_label.setWordWrap(True)

        self.reload_button = QPushButton("重新加载", self)
        self.validate_button = QPushButton("校验 TOML", self)
        self.save_button = QPushButton("保存修改", self)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        """创建页面级布局。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        toolbar_frame = QFrame(self)
        toolbar_frame.setFrameShape(QFrame.Shape.StyledPanel)

        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(18, 14, 18, 14)
        toolbar_layout.setSpacing(10)
        toolbar_layout.addWidget(QLabel("配置文件：", self))
        toolbar_layout.addWidget(self.path_label, stretch=1)
        toolbar_layout.addWidget(self.reload_button)
        toolbar_layout.addWidget(self.validate_button)
        toolbar_layout.addWidget(self.save_button)

        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(toolbar_frame)
        layout.addWidget(self.editor, stretch=1)
        layout.addWidget(self.message_label)

    def _connect_signals(self) -> None:
        """连接页面内的基础交互。"""
        self.reload_button.clicked.connect(
            lambda: self._show_info("frps 配置加载逻辑待接入")
        )
        self.validate_button.clicked.connect(
            lambda: self._show_info("frps TOML 校验逻辑待接入")
        )
        self.save_button.clicked.connect(
            lambda: self._show_info("frps 配置保存逻辑待接入")
        )

    def _show_info(self, message: str) -> None:
        """在页面和主窗口运行提示里显示普通提示。"""
        self.message_label.setStyleSheet("color: #80cbc4;")
        self.message_label.setText(message)
        self.status_message_changed.emit(message)
