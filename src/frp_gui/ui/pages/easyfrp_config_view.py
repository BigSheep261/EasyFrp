"""EasyFrp 应用设置页面。"""

from PyQt6.QtCore import Qt, pyqtSignal
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

from frp_gui.core.easyfrp_config_service import EasyfrpConfigService
from frp_gui.ui.theme import (
    DEFAULT_THEME_KEY,
    get_theme_variant,
    list_theme_variants,
    set_widget_state,
)
from frp_gui.ui.widgets.switch_button import SwitchButton


class EasyfrpConfigView(QWidget):
    """侧边栏中的 EasyFrp 设置页面。"""

    status_message_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str)
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.config_service = EasyfrpConfigService()
        self.current_settings: dict[str, str | bool] = {}

        self.title_label = QLabel("EasyFrp 设置", self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.description_label = QLabel(
            "配置界面风格、frpc/frps 模式和启动偏好。",
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

    def _load_settings(self) -> None:
        """从 config/config.json 读取设置并填入表单。"""
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
        """恢复表单默认值，点击应用后写回配置文件。"""
        self._apply_settings_to_form(self.config_service.default_settings())
        self._show_info("EasyFrp 设置已重置为默认值，点击应用后生效")

    def _apply_settings(self) -> None:
        """保存当前表单设置到 config/config.json。"""
        settings = self._collect_settings()
        try:
            self.config_service.save_settings(settings)
        except OSError as error:
            self._show_error(f"保存设置失败：{error}")
            return

        self.current_settings = settings
        self.theme_changed.emit(self._current_theme_key())
        self.settings_changed.emit(settings)
        self._show_info("EasyFrp 设置已保存到 config/config.json")

    def _apply_settings_to_form(self, settings: dict[str, str | bool]) -> None:
        """把设置字典同步到表单控件。"""
        theme_key = settings.get("theme_key")
        self._set_current_theme_key(theme_key if isinstance(theme_key, str) else None)

        client_mode = settings.get("client_mode")
        self._set_current_client_mode(
            client_mode if isinstance(client_mode, str) else "frpc"
        )
        self.launch_at_start_switch.setChecked(
            bool(settings.get("launch_at_start", False))
        )
        self.auto_run_switch.setChecked(bool(settings.get("auto_run", False)))

    def _collect_settings(self) -> dict[str, str | bool]:
        """收集当前表单值。"""
        return {
            "theme_key": self._current_theme_key(),
            "client_mode": self._current_client_mode(),
            "launch_at_start": self.launch_at_start_switch.isChecked(),
            "auto_run": self.auto_run_switch.isChecked(),
        }

    def _show_info(self, message: str) -> None:
        """在页面和主窗口运行提示里显示普通提示。"""
        set_widget_state(self.message_label, "info")
        self.message_label.setText(message)
        self.status_message_changed.emit(message)

    def _show_error(self, message: str) -> None:
        """在页面和主窗口运行提示里显示错误提示。"""
        set_widget_state(self.message_label, "error")
        self.message_label.setText(message)
        self.status_message_changed.emit(message)

    def _populate_theme_select(self) -> None:
        """填充界面风格选项。"""
        for variant in list_theme_variants():
            self.theme_select.addItem(variant.name, variant.key)
            index = self.theme_select.count() - 1
            self.theme_select.setItemData(
                index,
                variant.description,
                Qt.ItemDataRole.ToolTipRole,
            )

    def _populate_client_mode_select(self) -> None:
        """填充 frpc/frps 模式选项。"""
        self.client_mode_select.addItem("frpc 客户端", "frpc")
        self.client_mode_select.addItem("frps 服务端", "frps")

    def _set_current_theme_key(self, theme_key: str | None) -> None:
        """选中指定界面风格。"""
        index = self.theme_select.findData(theme_key or DEFAULT_THEME_KEY)
        if index < 0:
            index = self.theme_select.findData(DEFAULT_THEME_KEY)
        self.theme_select.setCurrentIndex(index)
        self._update_theme_description()

    def _current_theme_key(self) -> str:
        """返回当前界面风格 key。"""
        key = self.theme_select.currentData()
        return key if isinstance(key, str) else DEFAULT_THEME_KEY

    def _set_current_client_mode(self, client_mode: str) -> None:
        """选中指定 frpc/frps 模式。"""
        index = self.client_mode_select.findData(client_mode)
        if index < 0:
            index = self.client_mode_select.findData("frpc")
        self.client_mode_select.setCurrentIndex(index)

    def _current_client_mode(self) -> str:
        """返回当前 frpc/frps 模式。"""
        mode = self.client_mode_select.currentData()
        return mode if isinstance(mode, str) else "frpc"

    def _handle_theme_changed(self, _index: int) -> None:
        """切换时即时预览界面风格。"""
        theme_key = self._current_theme_key()
        variant = get_theme_variant(theme_key)
        self._update_theme_description()
        self.theme_changed.emit(theme_key)
        self._show_info(f"界面风格已切换为：{variant.name}")

    def _update_theme_description(self) -> None:
        """显示当前界面风格说明。"""
        variant = get_theme_variant(self._current_theme_key())
        self.theme_description_label.setText(variant.description)
