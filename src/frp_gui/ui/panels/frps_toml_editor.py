"""frps TOML 配置编辑面板。"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from frp_gui.core.frps_config_service import FrpsConfigService
from frp_gui.ui.theme import set_widget_state


class FrpsTomlEditorPanel(QWidget):
    """加载、编辑、校验并保存 frps.toml 的功能面板。"""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.config_service = FrpsConfigService()

        self.path_label = QLabel(str(self.config_service.config_path), self)
        self.path_label.setObjectName("pathLabel")
        self.path_label.setWordWrap(True)

        self.editor = QPlainTextEdit(self)
        self.editor.setObjectName("configEditor")
        self.editor.setPlaceholderText("frps.toml 内容会显示在这里。")
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("inlineMessage")
        self.message_label.setWordWrap(True)

        self.reload_button = QPushButton("重新加载", self)
        self.validate_button = QPushButton("校验 TOML", self)
        self.save_button = QPushButton("保存修改", self)
        self.reload_button.setObjectName("secondaryButton")
        self.validate_button.setObjectName("secondaryButton")
        self.save_button.setObjectName("primaryButton")

        self._build_ui()
        self._connect_signals()
        self.load_config()

    def _build_ui(self) -> None:
        """创建功能面板内部布局。"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(14)

        toolbar_frame = QFrame(self)
        toolbar_frame.setObjectName("toolbarSurface")
        toolbar_frame.setFrameShape(QFrame.Shape.StyledPanel)

        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(18, 14, 18, 14)
        toolbar_layout.setSpacing(10)
        toolbar_layout.addWidget(QLabel("配置文件：", self))
        toolbar_layout.addWidget(self.path_label, stretch=1)
        toolbar_layout.addWidget(self.reload_button)
        toolbar_layout.addWidget(self.validate_button)
        toolbar_layout.addWidget(self.save_button)

        main_layout.addWidget(toolbar_frame)
        main_layout.addWidget(self.editor, stretch=1)
        main_layout.addWidget(self.message_label)

    def _connect_signals(self) -> None:
        """把按钮点击信号连接到 panel 方法。"""
        self.reload_button.clicked.connect(self.load_config)
        self.validate_button.clicked.connect(self._handle_validate_clicked)
        self.save_button.clicked.connect(self._handle_save_clicked)

    def load_config(self) -> None:
        """从磁盘读取 frps.toml，并显示到编辑框。"""
        try:
            text = self.config_service.load_text()
        except OSError as error:
            self._show_error(f"读取配置失败：{error}")
            return

        self.editor.setPlainText(text)
        self._show_info("已加载 frps.toml")

    def _handle_validate_clicked(self) -> None:
        """只校验当前编辑框内容，不保存。"""
        is_valid, error_message = self.config_service.validate_text(
            self.editor.toPlainText()
        )
        if is_valid:
            self._show_info("TOML 格式校验通过")
        else:
            self._show_error(f"TOML 格式错误：{error_message}")

    def _handle_save_clicked(self) -> None:
        """把编辑框内容保存回 config/frps.toml。"""
        text = self.editor.toPlainText()

        try:
            is_saved, error_message = self.config_service.save_text(text)
        except OSError as error:
            self._show_error(f"保存配置失败：{error}")
            return

        if not is_saved:
            self._show_error(f"TOML 格式错误，未保存：{error_message}")
            return

        self._show_info("frps.toml 已保存")
        QMessageBox.information(self, "保存成功", "frps.toml 已保存。")

    def _show_info(self, message: str) -> None:
        """在面板和主窗口运行提示里显示普通提示。"""
        set_widget_state(self.message_label, "info")
        self.message_label.setText(message)
        self.status_message_changed.emit(message)

    def _show_error(self, message: str) -> None:
        """在面板和主窗口运行提示里显示错误提示。"""
        set_widget_state(self.message_label, "error")
        self.message_label.setText(message)
        self.status_message_changed.emit(message)
