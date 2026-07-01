"""frpc 启动/停止功能模块。

panels 层负责把 widgets 组合成一个明确的业务功能。
这个模块会导入 widgets/switch_button.py 中的 SwitchButton，
并把它和 FrpcController 的启动、停止函数绑定起来。
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget

from frp_gui.core.frpc_controller import FrpcController
from frp_gui.ui.widgets.switch_button import SwitchButton


class FrpcOpenPanel(QWidget):
    """frpc 进程控制面板。

    这个类属于“功能模块”，所以它可以知道 frpc 业务，并持有 FrpcController。
    它负责：
    1. 展示当前 frpc 状态。
    2. 响应开关按钮的打开/关闭。
    3. 调用 controller 启动或停止 frpc。
    4. 展示 frpc 输出日志和错误信息。

    它不负责页面整体布局，也不负责侧边栏切换。
    这些属于 pages/main_window 层的职责。
    """

    # panel 内部的状态变化可以通知外层页面或主窗口。
    # main_window 会用这个信号更新主界面内的运行提示。
    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # controller 负责真正的进程生命周期管理。
        # UI 不直接操作 QProcess，而是调用 controller 暴露出来的方法。
        self.frpc_controller = FrpcController(parent=self)

        # 当程序主动同步开关状态时，setChecked() 也会触发 toggled 信号。
        # 这个标记用来区分“用户点击”和“程序同步状态”，避免递归触发启动/停止。
        self._syncing_switch = False

        self.status_label = QLabel("状态：未运行", self)
        self.status_label.setObjectName("statusBadge")
        self.open_switch = SwitchButton(
            off_text="启动 frpc",
            on_text="停止 frpc",
            parent=self,
        )

        self.log_view = QTextEdit(self)
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("frpc 的标准输出和错误输出会显示在这里。")

        self._build_ui()
        self._connect_signals()

    def shutdown(self) -> None:
        """页面关闭或应用退出时，停止正在运行的 frpc。"""
        self.frpc_controller.shutdown()

    def start_frpc(self) -> bool:
        """由外部页面请求启动 frpc。"""
        if self.frpc_controller.is_running():
            self._set_switch_checked(True)
            return False

        self.open_switch.setEnabled(False)
        if not self.frpc_controller.start_frpc():
            self._set_switch_checked(False)
            self.open_switch.setEnabled(True)
            return False
        return True

    def stop_frpc(self) -> bool:
        """由外部页面请求停止 frpc。"""
        self.open_switch.setEnabled(False)
        if not self.frpc_controller.stop_frpc():
            self._set_switch_checked(False)
            self.open_switch.setEnabled(True)
            return False
        return True

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
        self.frpc_controller.state_changed.connect(self._handle_frpc_state_changed)
        self.frpc_controller.output_received.connect(self._append_log)
        self.frpc_controller.error_occurred.connect(self._handle_frpc_error)

    def _handle_switch_toggled(self, checked: bool) -> None:
        """用户点击开关后，启动或停止 frpc。"""
        if self._syncing_switch:
            return

        # 启动/停止是异步过程。
        # 在 controller 返回最终状态前，先禁用开关，避免用户连续点击造成状态混乱。
        if checked:
            self.start_frpc()
            return

        self.stop_frpc()

    def _handle_frpc_state_changed(self, state: str) -> None:
        """根据 controller 返回的状态更新界面。"""
        labels = {
            "stopped": "未运行",
            "starting": "启动中",
            "running": "运行中",
            "stopping": "停止中",
        }
        state_text = labels.get(state, state)
        self.status_label.setText(f"状态：{state_text}")
        self.status_message_changed.emit(f"frpc {state_text}")

        # 只有进入最终状态后才重新允许点击。
        # running: 当前已经运行，开关应该处于选中状态，下一次点击表示停止。
        # stopped: 当前已经停止，开关应该处于未选中状态，下一次点击表示启动。
        if state == "running":
            self._set_switch_checked(True)
            self.open_switch.setEnabled(True)
        elif state == "stopped":
            self._set_switch_checked(False)
            self.open_switch.setEnabled(True)
        else:
            self.open_switch.setEnabled(False)

    def _handle_frpc_error(self, message: str) -> None:
        """展示 controller 抛出的错误信息。"""
        self._append_log(f"[ERROR] {message}")
        self.status_message_changed.emit(message)

    def _append_log(self, message: str) -> None:
        """把 frpc 输出追加到日志区域。"""
        self.log_view.append(message)

    def _set_switch_checked(self, checked: bool) -> None:
        """由程序主动同步开关状态，避免触发业务逻辑。"""
        self._syncing_switch = True
        try:
            self.open_switch.setChecked(checked)
        finally:
            self._syncing_switch = False
