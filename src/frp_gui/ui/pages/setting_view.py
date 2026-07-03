"""EasyFrp application settings page."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from frp_gui.backend.settings.settings_service import SettingsService
from frp_gui.ui.widgets.switch_button import SwitchButton


class EasyfrpConfigView(QWidget):
    """Settings page shown from the sidebar."""

    status_message_changed = pyqtSignal(str)
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.config_service = SettingsService()
        self.current_settings: dict[str, str | bool] = {}

        self.title_label = QLabel("EasyFrp 设置", self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.description_label = QLabel(
            "配置 frpc/frps 模式和启动偏好。",
            self,
        )
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        self.client_mode_select = QComboBox(self)
        self.client_mode_select.setObjectName("clientModeSelect")
        self._populate_client_mode_select()

        self.launch_at_start_switch = SwitchButton(
            off_text="关闭",
            on_text="开启",
            parent=self,
        )
        self.auto_run_switch = SwitchButton(
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

        self._build_ui()
        self._load_settings()
        self._connect_signals()

    def _build_ui(self) -> None:
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
        form_layout.addRow("客户端模式", self.client_mode_select)
        form_layout.addRow("开机自启动", self.launch_at_start_switch)
        form_layout.addRow("自动运行", self.auto_run_switch)

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
        self.reset_button.clicked.connect(self._reset_form)
        self.apply_button.clicked.connect(self._apply_settings)

    def _load_settings(self) -> None:
        try:
            settings = self.config_service.load_settings()
        except (OSError, ValueError) as error:
            settings = self.config_service.default_settings()
            self._apply_settings_to_form(settings)
            self.current_settings = settings
            self._show_error(f"读取设置失败，已使用默认值：{error}")
            return

        self._apply_settings_to_form(settings)
        self.current_settings = settings

    def _reset_form(self) -> None:
        self._apply_settings_to_form(self.config_service.default_settings())
        self._show_info("EasyFrp 设置已重置为默认值，点击应用后生效")

    def _apply_settings(self) -> None:
        settings = self._collect_settings()
        try:
            self.config_service.save_settings(settings)
        except OSError as error:
            self._show_error(f"保存设置失败：{error}")
            return

        self.current_settings = settings
        self.settings_changed.emit(settings)
        self._show_info("EasyFrp 设置已保存到 config/config.json")

    def _apply_settings_to_form(self, settings: dict[str, str | bool]) -> None:
        client_mode = settings.get("client_mode")
        self._set_current_client_mode(
            client_mode if isinstance(client_mode, str) else "frpc"
        )
        self.launch_at_start_switch.setChecked(
            bool(settings.get("launch_at_start", False))
        )
        self.auto_run_switch.setChecked(bool(settings.get("auto_run", False)))

    def _collect_settings(self) -> dict[str, str | bool]:
        return {
            "client_mode": self._current_client_mode(),
            "launch_at_start": self.launch_at_start_switch.isChecked(),
            "auto_run": self.auto_run_switch.isChecked(),
        }

    def _show_info(self, message: str) -> None:
        self.message_label.setText(message)
        self.status_message_changed.emit(message)

    def _show_error(self, message: str) -> None:
        self.message_label.setText(message)
        self.status_message_changed.emit(message)

    def _populate_client_mode_select(self) -> None:
        self.client_mode_select.addItem("frpc 客户端", "frpc")
        self.client_mode_select.addItem("frps 服务端", "frps")

    def _set_current_client_mode(self, client_mode: str) -> None:
        index = self.client_mode_select.findData(client_mode)
        if index < 0:
            index = self.client_mode_select.findData("frpc")
        self.client_mode_select.setCurrentIndex(index)

    def _current_client_mode(self) -> str:
        mode = self.client_mode_select.currentData()
        return mode if isinstance(mode, str) else "frpc"
