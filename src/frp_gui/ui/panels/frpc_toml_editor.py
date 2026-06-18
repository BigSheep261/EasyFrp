"""frpc TOML 配置编辑面板。

panel 负责把多个 widget 组合成一个明确的业务模块。
这个面板持有文本编辑框和按钮，但把文件读取/保存委托给 FrpcConfigService。
"""

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

from frp_gui.core.frpc_config_service import FrpcConfigService


class FrpcTomlEditorPanel(QWidget):
    """加载、编辑、校验并保存 frpc.toml 的功能面板。"""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # service 是 UI 代码和文件业务代码之间的边界。
        # panel 可以请求 service 读写文件，但 service 不应该知道任何 QWidget。
        self.config_service = FrpcConfigService()

        self.path_label = QLabel(str(self.config_service.config_path), self)
        self.path_label.setWordWrap(True)

        self.editor = QPlainTextEdit(self)
        self.editor.setPlaceholderText("frpc.toml 内容会显示在这里。")
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.message_label = QLabel("", self)
        self.message_label.setWordWrap(True)

        self.reload_button = QPushButton("重新加载", self)
        self.validate_button = QPushButton("校验 TOML", self)
        self.save_button = QPushButton("保存修改", self)

        self._build_ui()
        self._connect_signals()
        self.load_config()

    def _build_ui(self) -> None:
        """创建功能面板内部布局。"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(14)

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

        main_layout.addWidget(toolbar_frame)
        main_layout.addWidget(self.editor, stretch=1)
        main_layout.addWidget(self.message_label)

    def _connect_signals(self) -> None:
        """把按钮点击信号连接到 panel 方法。

        在 PyQt 里，signal 是 widget 发出的事件，slot 是响应事件的函数。
        这里让按钮点击先进入 panel 方法，是为了让 panel 先收集编辑框文本，
        再调用 core service，并负责把成功或失败结果显示给用户。
        """
        self.reload_button.clicked.connect(self.load_config)
        self.validate_button.clicked.connect(self._handle_validate_clicked)
        self.save_button.clicked.connect(self._handle_save_clicked)

    def load_config(self) -> None:
        """从磁盘读取 frpc.toml，并显示到编辑框。"""
        try:
            text = self.config_service.load_text()
        except OSError as error:
            self._show_error(f"读取配置失败：{error}")
            return

        self.editor.setPlainText(text)
        self._show_info("已加载 frpc.toml")

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
        """把编辑框内容保存回 config/frpc.toml。"""
        text = self.editor.toPlainText()

        try:
            is_saved, error_message = self.config_service.save_text(text)
        except OSError as error:
            self._show_error(f"保存配置失败：{error}")
            return

        if not is_saved:
            self._show_error(f"TOML 格式错误，未保存：{error_message}")
            return

        self._show_info("frpc.toml 已保存")
        QMessageBox.information(self, "保存成功", "frpc.toml 已保存。")

    def _show_info(self, message: str) -> None:
        """在面板和主窗口状态栏里显示普通提示。"""
        self.message_label.setStyleSheet("color: #80cbc4;")
        self.message_label.setText(message)
        self.status_message_changed.emit(message)

    def _show_error(self, message: str) -> None:
        """在面板和主窗口状态栏里显示错误提示。"""
        self.message_label.setStyleSheet("color: #ef9a9a;")
        self.message_label.setText(message)
        self.status_message_changed.emit(message)
