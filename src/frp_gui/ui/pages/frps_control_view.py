"""frps 控制页面。"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frp_gui.ui.widgets.switch_button import SwitchButton


class FrpsControlView(QWidget):
    """侧边栏中的 frps 控制页面。"""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_label = QLabel("FRP 服务端控制", self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.description_label = QLabel(
            "用于启动和停止 frps 服务端，默认面向 runtime/frps.exe 和 config/frps.toml。",
            self,
        )
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        self.status_label = QLabel("状态：待接入启动逻辑", self)
        self.status_label.setObjectName("statusBadge")
        self.open_switch = SwitchButton(
            off_text="启动 frps",
            on_text="停止 frps",
            parent=self,
        )

        self.log_view = QTextEdit(self)
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("frps 的标准输出和错误输出会显示在这里。")

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        """创建页面级布局。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        control_frame = QFrame(self)
        control_frame.setObjectName("controlSurface")
        control_frame.setFrameShape(QFrame.Shape.StyledPanel)

        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(18, 16, 18, 16)
        control_layout.setSpacing(12)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.open_switch)

        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(control_frame)
        layout.addWidget(self.log_view, stretch=1)

    def _connect_signals(self) -> None:
        """连接页面内的基础交互。"""
        self.open_switch.toggled.connect(self._handle_switch_toggled)

    def _handle_switch_toggled(self, checked: bool) -> None:
        """只更新界面提示，不启动或停止真实 frps 进程。"""
        if checked:
            message = "已点击启动 frps，业务逻辑待接入"
            self.status_label.setText("状态：启动操作待接入")
        else:
            message = "已点击停止 frps，业务逻辑待接入"
            self.status_label.setText("状态：停止操作待接入")

        self.log_view.append(f"[UI] {message}")
        self.status_message_changed.emit(message)
