"""提供 EasyFrp 运行模式与启动偏好的读取、编辑和保存页面。"""

# Qt 信号负责跨页面通知，表单与布局控件共同构建设置界面。
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

# 设置服务负责持久化，复用开关负责一致地表达布尔选项。
from frp_gui.backend.settings.settings_service import SettingsService
from frp_gui.ui.widgets.switch_button import SwitchButton


class EasyfrpConfigView(QWidget):
    """在侧边栏中展示并维护 EasyFrp 全局设置。"""

    # 将页面内的提示消息交给主窗口统一展示。
    status_message_changed = pyqtSignal(str)

    # 设置保存成功后通知主窗口立即刷新与模式相关的导航内容。
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化设置服务、表单控件及其交互关系。

        Args:
            parent: 负责管理当前页面生命周期的父级 Qt 控件。
        """
        # 建立 Qt 父子关系，确保页面关闭时自动回收全部子控件。
        super().__init__(parent)

        # 使用独立服务封装配置文件的默认值、读取和持久化行为。
        self.config_service = SettingsService()

        # 缓存最后一次成功加载或保存的设置，供页面外部按需读取。
        self.current_settings: dict[str, str | bool] = {}

        # 创建页面标题，并设置与其他一级页面一致的字体层级。
        self.title_label = QLabel("EasyFrp 设置", self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        # 用简短说明概括可配置内容，并允许在窄窗口中自动换行。
        self.description_label = QLabel(
            "配置 frpc/frps 模式和启动偏好。",
            self,
        )
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        # 下拉框保存展示文案与内部模式值之间的映射。
        self.client_mode_select = QComboBox(self)
        self.client_mode_select.setObjectName("clientModeSelect")
        self._populate_client_mode_select()

        # 两个复用开关分别表示系统启动项和应用启动后的自动运行偏好。
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

        # 行内消息在表单附近即时反馈读取、重置或保存结果。
        self.message_label = QLabel("", self)
        self.message_label.setObjectName("inlineMessage")
        self.message_label.setWordWrap(True)

        # 重置仅修改当前表单，应用按钮才负责将选项写入配置文件。
        self.reset_button = QPushButton("重置", self)
        self.apply_button = QPushButton("应用设置", self)

        # 通过稳定对象名区分次要与主要操作的视觉样式。
        self.reset_button.setObjectName("secondaryButton")
        self.apply_button.setObjectName("primaryButton")

        # 先建立界面，再加载数据，最后连接用户操作信号。
        self._build_ui()
        self._load_settings()
        self._connect_signals()

    def _build_ui(self) -> None:
        """构建设置页的标题、表单、操作按钮和反馈区域。"""
        # 页面外层布局统一四周留白与主要区域之间的间距。
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        # 使用独立表面容纳表单和按钮，便于样式表绘制卡片效果。
        form_frame = QFrame(self)
        form_frame.setObjectName("formSurface")
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)

        # 卡片内层布局负责隔开设置项与底部操作按钮。
        frame_layout = QVBoxLayout(form_frame)
        frame_layout.setContentsMargins(20, 18, 20, 18)
        frame_layout.setSpacing(18)

        # 表单布局负责对齐字段名称与对应控件。
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(14)

        # 允许输入控件随窗口横向扩展，充分利用可用宽度。
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

        # 按运行模式、系统启动行为和自动运行行为的顺序组织设置项。
        form_layout.addRow("客户端模式", self.client_mode_select)
        form_layout.addRow("开机自启动", self.launch_at_start_switch)
        form_layout.addRow("自动运行", self.auto_run_switch)

        # 将操作按钮靠右排列，突出主要的应用操作。
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.apply_button)

        # 把表单和操作区装入同一个卡片表面。
        frame_layout.addLayout(form_layout)
        frame_layout.addLayout(button_layout)

        # 页面依次展示说明、设置卡片和反馈消息，并把多余空间留在底部。
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(form_frame)
        layout.addWidget(self.message_label)
        layout.addStretch()

    def _connect_signals(self) -> None:
        """把表单操作按钮连接到对应的页面处理方法。"""
        # 重置按钮只恢复表单显示，避免误触时立即覆盖配置文件。
        self.reset_button.clicked.connect(self._reset_form)

        # 应用按钮收集当前表单值并执行持久化。
        self.apply_button.clicked.connect(self._apply_settings)

    def _load_settings(self) -> None:
        """读取持久化设置并同步到表单，失败时安全回退到默认值。"""
        # 配置内容或文件系统异常都不能阻止设置页面正常打开。
        try:
            settings = self.config_service.load_settings()
        except (OSError, ValueError) as error:
            # 回退结果同时写入表单和内存缓存，保持页面状态一致。
            settings = self.config_service.default_settings()
            self._apply_settings_to_form(settings)
            self.current_settings = settings

            # 明确提示用户当前展示的是默认值，而非已保存设置。
            self._show_error(f"读取设置失败，已使用默认值：{error}")
            return

        # 成功读取后同步可见表单与缓存，作为后续编辑的基准状态。
        self._apply_settings_to_form(settings)
        self.current_settings = settings

    def _reset_form(self) -> None:
        """把表单恢复为默认设置，但暂不写入配置文件。"""
        # 仅更新控件值，保留用户确认后再应用的交互语义。
        self._apply_settings_to_form(self.config_service.default_settings())

        # 提醒用户还需点击应用，避免把表单重置误解为已经保存。
        self._show_info("EasyFrp 设置已重置为默认值，点击应用后生效")

    def _apply_settings(self) -> None:
        """收集并保存当前表单设置，成功后广播最新配置。"""
        # 先生成结构稳定的配置字典，作为保存和通知的同一份数据。
        settings = self._collect_settings()

        # 捕获文件系统错误，在页面内反馈而不让异常中断 GUI 事件循环。
        try:
            self.config_service.save_settings(settings)
        except OSError as error:
            self._show_error(f"保存设置失败：{error}")
            return

        # 只在持久化成功后更新缓存并通知主窗口，防止界面与文件不一致。
        self.current_settings = settings
        self.settings_changed.emit(settings)

        # 同时在行内区域和主窗口提示区报告保存成功。
        self._show_info("EasyFrp 设置已保存到 config/config.json")

    def _apply_settings_to_form(self, settings: dict[str, str | bool]) -> None:
        """把设置字典中的受支持字段安全地映射到表单控件。"""
        # 非字符串模式值视为无效数据，并回退到默认的 frpc 模式。
        client_mode = settings.get("client_mode")
        self._set_current_client_mode(
            client_mode if isinstance(client_mode, str) else "frpc"
        )

        # 缺失的布尔设置按关闭处理，同时规范化意外的真值类型。
        self.launch_at_start_switch.setChecked(
            bool(settings.get("launch_at_start", False))
        )
        self.auto_run_switch.setChecked(bool(settings.get("auto_run", False)))

    def _collect_settings(self) -> dict[str, str | bool]:
        """从当前表单读取值并构造可持久化的设置字典。"""
        # 使用内部模式标识和真实选中状态，避免把界面文案写入配置。
        return {
            "client_mode": self._current_client_mode(),
            "launch_at_start": self.launch_at_start_switch.isChecked(),
            "auto_run": self.auto_run_switch.isChecked(),
        }

    def _show_info(self, message: str) -> None:
        """在页面内显示普通消息，并同步通知主窗口。"""
        # 行内提示让用户在设置表单附近立即看到操作结果。
        self.message_label.setText(message)

        # 页面级信号让主窗口的公共提示区域显示同一条消息。
        self.status_message_changed.emit(message)

    def _show_error(self, message: str) -> None:
        """在页面内显示错误消息，并同步通知主窗口。"""
        # 当前样式体系通过消息内容和统一区域反馈错误信息。
        self.message_label.setText(message)

        # 向外转发错误，确保用户切换注意区域后仍能看到反馈。
        self.status_message_changed.emit(message)

    def _populate_client_mode_select(self) -> None:
        """注册客户端模式的展示文案及其稳定内部标识。"""
        # 每个选项同时保存用户可见名称与配置文件使用的简短值。
        self.client_mode_select.addItem("frpc 客户端", "frpc")
        self.client_mode_select.addItem("frps 服务端", "frps")

    def _set_current_client_mode(self, client_mode: str) -> None:
        """选择给定内部模式值，不受支持时回退到 frpc。"""
        # 按选项附带的数据查找，而不是依赖可能变化的展示文案。
        index = self.client_mode_select.findData(client_mode)

        # 配置中的未知模式不能导致下拉框处于无选中项状态。
        if index < 0:
            index = self.client_mode_select.findData("frpc")

        # 将经过校验的索引反映到可见表单。
        self.client_mode_select.setCurrentIndex(index)

    def _current_client_mode(self) -> str:
        """返回当前选择的内部模式值，异常数据时使用 frpc。"""
        # 读取选项附带的配置值，避免将本地化界面文案传给后端。
        mode = self.client_mode_select.currentData()

        # 类型不符合约定时使用稳定默认值，保证返回类型始终为字符串。
        return mode if isinstance(mode, str) else "frpc"
