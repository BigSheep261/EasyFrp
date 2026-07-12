"""frps TOML 配置编辑页面。"""

# Qt 信号用于上报编辑状态，布局和标签构成页面级视觉结构。
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

# TOML 编辑面板集中处理配置文件读取、编辑与保存职责。
from frp_gui.ui.panels.frps_toml_editor import FrpsTomlEditorPanel


class FrpsConfigView(QWidget):
    """组合 frps TOML 编辑面板，并向主窗口转发编辑状态。"""

    # 向页面外暴露统一消息通道，隔离主窗口与编辑面板的内部结构。
    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化 frps 配置编辑页面及其子控件。

        Args:
            parent: 负责管理当前页面生命周期的父级 Qt 控件。
        """
        # 建立 Qt 父子关系，使页面销毁时一并清理内部控件。
        super().__init__(parent)

        # 创建页面标题，并设置突出显示的字号与字重。
        self.title_label = QLabel("frps 配置编辑", self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        # 说明编辑目标及保存行为，并允许文字按可用宽度换行。
        self.description_label = QLabel(
            "读取 config/frps.toml，编辑后点击保存会写回原文件。",
            self,
        )
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        # 嵌入负责文件读取、编辑和保存的业务面板。
        self.editor_panel = FrpsTomlEditorPanel(self)

        # 将编辑结果消息原样转发给主窗口的提示区域。
        self.editor_panel.status_message_changed.connect(
            self.status_message_changed.emit
        )

        # 所有子控件就绪后再创建布局。
        self._build_ui()

    def _build_ui(self) -> None:
        """创建页面级布局。"""
        # 页面纵向排列标题、说明和编辑器，并保持统一边距。
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        # 让编辑器占据剩余空间，尽可能扩大文本编辑区域。
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.editor_panel, stretch=1)
