"""frpc TOML 配置编辑面板。

面板负责把多个控件组合成一个明确的业务模块。
这个面板持有文本编辑框和按钮，但把文件读取和保存委托给 ``FrpcConfigService``。
"""

# 导入 Qt 信号机制与构建编辑面板所需的基础控件。
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

# 配置服务封装 frpc.toml 的路径、读取、校验和保存规则。
from frp_gui.backend.frpc.config_service import FrpcConfigService


class FrpcTomlEditorPanel(QWidget):
    """加载、编辑、校验并保存 frpc.toml 的功能面板。"""

    # 将面板内产生的操作结果转发给外层页面或主窗口。
    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化配置服务、编辑控件、操作按钮及其信号连接。"""
        # 先完成 QWidget 基类初始化，使后续控件可安全地以当前面板为父对象。
        super().__init__(parent)

        # 配置服务是界面代码和文件业务代码之间的边界。
        # 面板可以请求配置服务读写文件，但配置服务不应依赖任何 QWidget。
        self.config_service = FrpcConfigService()

        # 在工具栏展示实际配置路径，并允许长路径自动换行。
        self.path_label = QLabel(str(self.config_service.config_path), self)
        self.path_label.setObjectName("pathLabel")
        self.path_label.setWordWrap(True)

        # 创建不自动折行的纯文本编辑器，以保留 TOML 原始排版。
        self.editor = QPlainTextEdit(self)
        self.editor.setObjectName("configEditor")
        self.editor.setPlaceholderText("frpc.toml 内容会显示在这里。")
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # 行内消息用于持续展示最近一次加载、校验或保存结果。
        self.message_label = QLabel("", self)
        self.message_label.setObjectName("inlineMessage")
        self.message_label.setWordWrap(True)

        # 创建三个互相独立的配置操作入口。
        self.reload_button = QPushButton("重新加载", self)
        self.validate_button = QPushButton("校验 TOML", self)
        self.save_button = QPushButton("保存修改", self)
        # 通过对象名区分次要操作与主要保存操作，供样式表统一设置外观。
        self.reload_button.setObjectName("secondaryButton")
        self.validate_button.setObjectName("secondaryButton")
        self.save_button.setObjectName("primaryButton")

        # 控件准备完毕后构建布局并绑定交互行为。
        self._build_ui()
        self._connect_signals()
        # 首次进入面板时立即载入磁盘中的配置内容。
        self.load_config()

    def _build_ui(self) -> None:
        """创建功能面板内部布局。"""
        # 主布局纵向排列工具栏、编辑器和行内消息，并移除面板外围留白。
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(14)

        # 使用带样式标识的框架承载文件路径和操作按钮。
        toolbar_frame = QFrame(self)
        toolbar_frame.setObjectName("toolbarSurface")
        toolbar_frame.setFrameShape(QFrame.Shape.StyledPanel)

        # 工具栏从左到右排列路径信息及重新加载、校验、保存按钮。
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(18, 14, 18, 14)
        toolbar_layout.setSpacing(10)
        toolbar_layout.addWidget(QLabel("配置文件：", self))
        # 路径标签占用剩余空间，避免按钮被长路径挤出可视区域。
        toolbar_layout.addWidget(self.path_label, stretch=1)
        toolbar_layout.addWidget(self.reload_button)
        toolbar_layout.addWidget(self.validate_button)
        toolbar_layout.addWidget(self.save_button)

        # 编辑器获得纵向伸缩空间，消息标签固定排列在底部。
        main_layout.addWidget(toolbar_frame)
        main_layout.addWidget(self.editor, stretch=1)
        main_layout.addWidget(self.message_label)

    def _connect_signals(self) -> None:
        """把按钮点击信号连接到对应的面板方法。

        在 PyQt 中，信号是控件发出的事件，槽函数是响应事件的方法。
        这里让按钮点击先进入面板方法，以便面板先收集编辑框文本，
        再调用配置服务，并负责把成功或失败结果显示给用户。
        """
        # 重新加载直接复用公开加载方法，另外两个按钮进入各自的业务处理器。
        self.reload_button.clicked.connect(self.load_config)
        self.validate_button.clicked.connect(self._handle_validate_clicked)
        self.save_button.clicked.connect(self._handle_save_clicked)

    def load_config(self) -> None:
        """从磁盘读取 frpc.toml，并显示到编辑框。"""
        # 文件系统错误由面板转换为可见提示，避免异常越过 UI 事件循环。
        try:
            text = self.config_service.load_text()
        except OSError as error:
            self._show_error(f"读取配置失败：{error}")
            return

        # 只有读取成功才覆盖编辑器，随后同步报告加载结果。
        self.editor.setPlainText(text)
        self._show_info("已加载 frpc.toml")

    def _handle_validate_clicked(self) -> None:
        """只校验当前编辑框内容，不保存。"""
        # 将当前未保存的编辑内容交给服务校验，并保留服务返回的错误详情。
        is_valid, error_message = self.config_service.validate_text(
            self.editor.toPlainText()
        )
        # 根据校验结果显示成功消息或带原因的格式错误。
        if is_valid:
            self._show_info("TOML 格式校验通过")
        else:
            self._show_error(f"TOML 格式错误：{error_message}")

    def _handle_save_clicked(self) -> None:
        """把编辑框内容保存回 config/frpc.toml。"""
        # 在调用服务前取得一次完整快照，确保本次保存校验的是同一份文本。
        text = self.editor.toPlainText()

        # 服务可能因磁盘访问失败抛出异常，面板负责向用户呈现该错误。
        try:
            is_saved, error_message = self.config_service.save_text(text)
        except OSError as error:
            self._show_error(f"保存配置失败：{error}")
            return

        # 格式校验失败时服务不会落盘，因此仅报告原因并终止成功流程。
        if not is_saved:
            self._show_error(f"TOML 格式错误，未保存：{error_message}")
            return

        # 保存成功后同时更新常驻行内消息，并弹出一次明确确认。
        self._show_info("frpc.toml 已保存")
        QMessageBox.information(self, "保存成功", "frpc.toml 已保存。")

    def _show_info(self, message: str) -> None:
        """在面板和主窗口运行提示里显示普通提示。"""
        # 面板内保留提示文本，同时通过信号让外层界面同步显示。
        self.message_label.setText(message)
        self.status_message_changed.emit(message)

    def _show_error(self, message: str) -> None:
        """在面板和主窗口运行提示里显示错误提示。"""
        # 错误与普通消息共用展示通道，保证面板和主窗口内容一致。
        self.message_label.setText(message)
        self.status_message_changed.emit(message)
