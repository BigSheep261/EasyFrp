"""
EasyFrp 设置页面


本页面负责对程序本身进行设置
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
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

from frp_gui.ui.theme import (
    DEFAULT_THEME_KEY,
    get_saved_theme_key,
    get_theme_variant,
    list_theme_variants,
    set_widget_state,
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
    theme_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_label = QLabel("EasyFrp 设置", self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.description_label = QLabel(
            "配置 EasyFrp 自身的常用路径、监听端口和运行偏好。",
            self,
        )
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        self.theme_select = QComboBox(self)
        self.theme_select.setObjectName("themeSelect")
        self.theme_description_label = QLabel("", self)
        self.theme_description_label.setObjectName("themeDescription")
        self.theme_description_label.setWordWrap(True)
        self._populate_theme_select()

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
        self.message_label.setObjectName("inlineMessage")
        self.message_label.setWordWrap(True)

        self.reset_button = QPushButton("重置", self)
        self.apply_button = QPushButton("应用设置", self)
        self.reset_button.setObjectName("secondaryButton")
        self.apply_button.setObjectName("primaryButton")
        self.current_settings: dict[str, str | int | bool] = {}

        self._set_default_values(theme_key=get_saved_theme_key())
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        """创建页面级布局和设置表单。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        form_frame = QFrame(self)
        form_frame.setObjectName("formSurface")
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
        form_layout.addRow("界面风格", self.theme_select)
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
        frame_layout.addWidget(self.theme_description_label)
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
        self.theme_select.currentIndexChanged.connect(self._handle_theme_changed)

    def _reset_form(self) -> None:
        """恢复表单默认值。"""
        self._set_default_values()
        self._show_info("EasyFrp 设置已重置为默认值")

    def _set_default_values(self, *, theme_key: str = DEFAULT_THEME_KEY) -> None:
        """填充表单默认值。"""
        self._set_current_theme_key(theme_key)
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
            "theme_key": self._current_theme_key(),
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
        set_widget_state(self.message_label, "info")
        self.message_label.setText(message)
        self.status_message_changed.emit(message)

    def _populate_theme_select(self) -> None:
        """Fill the UI variant selector."""
        for variant in list_theme_variants():
            self.theme_select.addItem(variant.name, variant.key)
            index = self.theme_select.count() - 1
            self.theme_select.setItemData(
                index,
                variant.description,
                Qt.ItemDataRole.ToolTipRole,
            )

    def _set_current_theme_key(self, theme_key: str) -> None:
        """Select a theme option if it exists."""
        index = self.theme_select.findData(theme_key)
        if index < 0:
            index = self.theme_select.findData(DEFAULT_THEME_KEY)
        self.theme_select.setCurrentIndex(index)
        self._update_theme_description()

    def _current_theme_key(self) -> str:
        """Return the selected theme key."""
        key = self.theme_select.currentData()
        return key if isinstance(key, str) else DEFAULT_THEME_KEY

    def _handle_theme_changed(self, _index: int) -> None:
        """Emit the selected visual direction for immediate preview."""
        theme_key = self._current_theme_key()
        variant = get_theme_variant(theme_key)
        self._update_theme_description()
        self.theme_changed.emit(theme_key)
        self._show_info(f"界面风格已切换为：{variant.name}")

    def _update_theme_description(self) -> None:
        """Show the selected variant's intent below the form."""
        variant = get_theme_variant(self._current_theme_key())
        self.theme_description_label.setText(variant.description)
