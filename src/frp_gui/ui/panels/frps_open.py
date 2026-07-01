"""frps 启动/停止功能模块。"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget

from frp_gui.core.frps_controller import FrpsController
from frp_gui.ui.widgets.switch_button import SwitchButton


class FrpsOpenPanel(QWidget):
    """frps 进程控制面板。"""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.frps_controller = FrpsController(parent=self)
        self._syncing_switch = False

        self.status_label = QLabel("状态：未运行", self)
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

    def shutdown(self) -> None:
        """页面关闭或应用退出时，停止正在运行的 frps。"""
        self.frps_controller.shutdown()

    def _build_ui(self) -> None:
        """创建本功能模块内部布局。"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(18)

        control_frame = QFrame(self)
        control_frame.setObjectName("controlSurface")
        control_frame.setFrameShape(QFrame.Shape.StyledPanel)

        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(18, 16, 18, 16)
        control_layout.setSpacing(12)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.open_switch)

        main_layout.addWidget(control_frame)
        main_layout.addWidget(self.log_view, stretch=1)

    def _connect_signals(self) -> None:
        """连接 UI 信号和 controller 信号。"""
        self.open_switch.toggled.connect(self._handle_switch_toggled)
        self.frps_controller.state_changed.connect(self._handle_frps_state_changed)
        self.frps_controller.output_received.connect(self._append_log)
        self.frps_controller.error_occurred.connect(self._handle_frps_error)

    def _handle_switch_toggled(self, checked: bool) -> None:
        """用户点击开关后，启动或停止 frps。"""
        if self._syncing_switch:
            return

        self.open_switch.setEnabled(False)

        if checked:
            if not self.frps_controller.start_frps():
                self._set_switch_checked(False)
                self.open_switch.setEnabled(True)
            return

        if not self.frps_controller.stop_frps():
            self._set_switch_checked(False)
            self.open_switch.setEnabled(True)

    def _handle_frps_state_changed(self, state: str) -> None:
        """根据 controller 返回的状态更新界面。"""
        labels = {
            "stopped": "未运行",
            "starting": "启动中",
            "running": "运行中",
            "stopping": "停止中",
        }
        state_text = labels.get(state, state)
        self.status_label.setText(f"状态：{state_text}")
        self.status_message_changed.emit(f"frps {state_text}")

        if state == "running":
            self._set_switch_checked(True)
            self.open_switch.setEnabled(True)
        elif state == "stopped":
            self._set_switch_checked(False)
            self.open_switch.setEnabled(True)
        else:
            self.open_switch.setEnabled(False)

    def _handle_frps_error(self, message: str) -> None:
        """展示 controller 抛出的错误信息。"""
        self._append_log(f"[ERROR] {message}")
        self.status_message_changed.emit(message)

    def _append_log(self, message: str) -> None:
        """把 frps 输出追加到日志区域。"""
        self.log_view.append(message)

    def _set_switch_checked(self, checked: bool) -> None:
        """由程序主动同步开关状态，避免触发业务逻辑。"""
        self._syncing_switch = True
        try:
            self.open_switch.setChecked(checked)
        finally:
            self._syncing_switch = False
