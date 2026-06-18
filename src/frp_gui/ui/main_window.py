"""应用程序主窗口。"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from frp_gui.core.frpc_controller import FrpcController


class ToggleSwitch(QCheckBox):
    """用于启动和停止 frpc 的可切换开关。"""

    def __init__(
        self,
        off_text: str = "启动 frpc",
        on_text: str = "停止 frpc",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        # 文案跟随 checked 状态变化：未选中表示可启动，选中表示可停止。
        self._off_text = off_text
        self._on_text = on_text
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(144)
        self.toggled.connect(self._update_text)
        self._update_text(self.isChecked())
        self.setStyleSheet(
            """
            QCheckBox {
                spacing: 10px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 46px;
                height: 24px;
                border-radius: 12px;
                background-color: #546e7a;
            }
            QCheckBox::indicator:checked {
                background-color: #26a69a;
            }
            QCheckBox::indicator:unchecked {
                background-color: #546e7a;
            }
            QCheckBox::indicator:disabled {
                background-color: #455a64;
            }
            """
        )

    def _update_text(self, checked: bool) -> None:
        self.setText(self._on_text if checked else self._off_text)


class MainWindow(QMainWindow):
    """EasyFrp 的顶层窗口。"""

    def __init__(self) -> None:
        super().__init__()
        # 主窗口持有一个 controller 实例，所有 frpc 进程操作都通过它完成。
        self.frpc_controller = FrpcController(parent=self)

        # 代码主动同步开关状态时会触发 toggled 信号。
        # 这个标记用于区分“用户点击”和“程序同步状态”。
        self._syncing_toggle = False

        self.setWindowTitle("EasyFrp")
        self.resize(960, 640)
        self.status_label = QLabel("状态：未运行", self)
        self.path_label = QLabel(
            "默认使用 runtime/frpc.exe 和 config/frpc.toml 启动客户端。",
            self,
        )
        self.path_label.setWordWrap(True)
        self.frpc_switch = ToggleSwitch(parent=self)
        self.log_view = QTextEdit(self)
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("frpc 的标准输出和错误输出会显示在这里。")

        self._build_ui()
        self._connect_signals()
        self.statusBar().showMessage("就绪")

    def closeEvent(self, event: QCloseEvent) -> None:
        """确保关闭 GUI 时一并退出 frpc。"""
        self.frpc_controller.shutdown()
        super().closeEvent(event)

    def _build_ui(self) -> None:
        # 先搭一个简单的纵向布局：标题、路径说明、控制条、日志区。
        # 后续增加配置管理时，可以在这里继续扩展表单或分页。
        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(18)

        title_label = QLabel("FRP 客户端控制", self)
        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)

        control_frame = QFrame(self)
        control_frame.setFrameShape(QFrame.Shape.StyledPanel)
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(18, 16, 18, 16)
        control_layout.setSpacing(12)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.frpc_switch)

        main_layout.addWidget(title_label)
        main_layout.addWidget(self.path_label)
        main_layout.addWidget(control_frame)
        main_layout.addWidget(self.log_view, stretch=1)
        self.setCentralWidget(central_widget)

    def _connect_signals(self) -> None:
        # UI 触发 controller；controller 再用信号把运行结果回传给 UI。
        # 这样后续即使换成托盘、服务模式或多配置文件，也不需要重写进程控制逻辑。
        self.frpc_switch.toggled.connect(self._handle_switch_toggled)
        self.frpc_controller.state_changed.connect(self._handle_frpc_state_changed)
        self.frpc_controller.output_received.connect(self._append_log)
        self.frpc_controller.error_occurred.connect(self._handle_frpc_error)

    def _handle_switch_toggled(self, checked: bool) -> None:
        # 如果是程序为了同步状态而改动开关，就不再触发启动/停止。
        if self._syncing_toggle:
            return

        # 启动或停止期间临时禁用开关，避免连续点击造成状态竞争。
        self.frpc_switch.setEnabled(False)
        if checked:
            if not self.frpc_controller.start_frpc():
                self._set_switch_checked(False)
                self.frpc_switch.setEnabled(True)
            return

        if not self.frpc_controller.stop_frpc():
            self._set_switch_checked(False)
            self.frpc_switch.setEnabled(True)

    def _handle_frpc_state_changed(self, state: str) -> None:
        # controller 对外发的是稳定的英文状态值；UI 在这里转换成中文展示。
        labels = {
            "stopped": "未运行",
            "starting": "启动中",
            "running": "运行中",
            "stopping": "停止中",
        }
        state_text = labels.get(state, state)
        self.status_label.setText(f"状态：{state_text}")
        self.statusBar().showMessage(f"frpc {state_text}")

        # 只有进入最终状态后才重新允许点击：
        # running 表示可以停止，stopped 表示可以启动。
        if state == "running":
            self._set_switch_checked(True)
            self.frpc_switch.setEnabled(True)
        elif state == "stopped":
            self._set_switch_checked(False)
            self.frpc_switch.setEnabled(True)
        else:
            self.frpc_switch.setEnabled(False)

    def _handle_frpc_error(self, message: str) -> None:
        self._append_log(f"[ERROR] {message}")
        self.statusBar().showMessage(message)

    def _append_log(self, message: str) -> None:
        self.log_view.append(message)

    def _set_switch_checked(self, checked: bool) -> None:
        # setChecked 会触发 toggled，这里用保护标记避免递归调用启动/停止逻辑。
        self._syncing_toggle = True
        try:
            self.frpc_switch.setChecked(checked)
        finally:
            self._syncing_toggle = False
