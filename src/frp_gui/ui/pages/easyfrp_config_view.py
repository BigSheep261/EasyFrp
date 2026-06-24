"""
EasyFrp 设置页面


本页面负责对程序本身进行设置
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from frp_gui.ui.widgets.switch_button import SwitchButton

DEFAULT_RUNTIME_PATH = "runtime/frpc.exe"
DEFAULT_CONFIG_PATH = "config/frpc.toml"
DEFAULT_LOG_PATH = "logs"
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 7400


class EasyfrpConfigView(QWidget):
    """侧边栏中的 设置"""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_label = QLabel("EasyFrp 设置", self)
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.description_label = QLabel(
            "配置 EasyFrp 自身的常用路径、监听端口和运行偏好。",
            self,
        )
        self.description_label.setWordWrap(True)

        self.runtime_path_input = QLineEdit(self)
        self.runtime_path_input.setPlaceholderText(DEFAULT_RUNTIME_PATH)

        self.config_path_input = QLineEdit(self)
        self.config_path_input.setPlaceholderText(DEFAULT_CONFIG_PATH)

        self.log_path_input = QLineEdit(self)
        self.log_path_input.setPlaceholderText(DEFAULT_LOG_PATH)

        self.api_host_input = QLineEdit(self)
        self.api_host_input.setPlaceholderText(DEFAULT_API_HOST)

        self.api_port_input = QSpinBox(self)
        self.api_port_input.setRange(1, 65535)
        self.api_port_input.setValue(DEFAULT_API_PORT)

        self.launch_at_start_switch = SwitchButton(
            off_text="关闭",
            on_text="开启",
            parent=self,
        )
        self.minimize_to_tray_switch = SwitchButton(
            off_text="关闭",
            on_text="开启",
            parent=self,
        )
        self.auto_start_frpc_switch = SwitchButton(
            off_text="关闭",
            on_text="开启",
            parent=self,
        )
        self.auto_reconnect_switch = SwitchButton(
            off_text="关闭",
            on_text="开启",
            parent=self,
        )

        self.message_label = QLabel("", self)
        self.message_label.setWordWrap(True)

        self.reset_button = QPushButton("重置", self)
        self.apply_button = QPushButton("应用设置", self)
        self.current_settings: dict[str, str | int | bool] = {}

        self._set_default_values()
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        """创建页面级布局和设置表单。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        form_frame = QFrame(self)
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)

        frame_layout = QVBoxLayout(form_frame)
        frame_layout.setContentsMargins(20, 18, 20, 18)
        frame_layout.setSpacing(18)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(14)
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        form_layout.addRow("frpc 程序路径", self.runtime_path_input)
        form_layout.addRow("默认配置文件", self.config_path_input)
        form_layout.addRow("日志目录", self.log_path_input)
        form_layout.addRow("API 地址", self.api_host_input)
        form_layout.addRow("API 端口", self.api_port_input)
        form_layout.addRow("开机自启动", self.launch_at_start_switch)
        form_layout.addRow("关闭时最小化到托盘", self.minimize_to_tray_switch)
        form_layout.addRow("启动后自动运行 frpc", self.auto_start_frpc_switch)
        form_layout.addRow("异常退出后自动重连", self.auto_reconnect_switch)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.apply_button)

        frame_layout.addLayout(form_layout)
        frame_layout.addLayout(button_layout)

        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(form_frame)
        layout.addWidget(self.message_label)
        layout.addStretch()

    def _connect_signals(self) -> None:
        """连接表单按钮事件。"""
        self.reset_button.clicked.connect(self._reset_form)
        self.apply_button.clicked.connect(self._apply_settings)

    def _reset_form(self) -> None:
        """恢复表单默认值。"""
        self._set_default_values()
        self._show_info("EasyFrp 设置已重置为默认值")

    def _set_default_values(self) -> None:
        """填充表单默认值。"""
        self.runtime_path_input.setText(DEFAULT_RUNTIME_PATH)
        self.config_path_input.setText(DEFAULT_CONFIG_PATH)
        self.log_path_input.setText(DEFAULT_LOG_PATH)
        self.api_host_input.setText(DEFAULT_API_HOST)
        self.api_port_input.setValue(DEFAULT_API_PORT)
        self.launch_at_start_switch.setChecked(False)
        self.minimize_to_tray_switch.setChecked(False)
        self.auto_start_frpc_switch.setChecked(False)
        self.auto_reconnect_switch.setChecked(False)

    def _apply_settings(self) -> None:
        """应用当前表单设置。"""
        self.current_settings = self._collect_settings()
        self._show_info("EasyFrp 设置已应用")

    def _collect_settings(self) -> dict[str, str | int | bool]:
        """收集当前表单值，留给后续持久化或业务逻辑使用。"""
        return {
            "runtime_path": self.runtime_path_input.text().strip(),
            "config_path": self.config_path_input.text().strip(),
            "log_path": self.log_path_input.text().strip(),
            "api_host": self.api_host_input.text().strip(),
            "api_port": self.api_port_input.value(),
            "launch_at_start": self.launch_at_start_switch.isChecked(),
            "minimize_to_tray": self.minimize_to_tray_switch.isChecked(),
            "auto_start_frpc": self.auto_start_frpc_switch.isChecked(),
            "auto_reconnect": self.auto_reconnect_switch.isChecked(),
        }

    def _show_info(self, message: str) -> None:
        """在页面和主窗口运行提示里显示普通提示。"""
        self.message_label.setStyleSheet("color: #80cbc4;")
        self.message_label.setText(message)
        self.status_message_changed.emit(message)
