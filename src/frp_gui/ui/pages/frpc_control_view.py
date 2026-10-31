"""frpc 手动进程控制与状态页面。"""

# 导入 Qt 信号机制与构建进程控制页面所需的基础控件。
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

# 进程服务封装 frpc 的启动、停止、状态通知和错误提示。
from frp_gui.backend.frpc.process_service import FrpcProcessService


class FrpcControlView(QWidget):
    """直接管理 frpc 手动启停控件，并将进程操作委托给后端服务。"""

    # 页面内部的状态变化可以通知外层页面或主窗口。
    # 主窗口会用这个信号更新主界面内的运行提示。
    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化进程服务、状态控件和信号连接。"""
        # 完成 QWidget 基类初始化，使子控件和服务可托管在当前页面下。
        super().__init__(parent)

        # 进程服务负责真正的进程生命周期管理。
        # 界面不直接操作 QProcess，而是调用进程服务公开的方法。
        self.frpc_process_service = FrpcProcessService(parent=self)

        # 当程序主动同步开关状态时，setChecked() 也会触发 toggled 信号。
        # 这个标记用来区分“用户点击”和“程序同步状态”，避免递归触发启动/停止。
        self._syncing_switch = False

        # 状态标签以“未运行”为初始展示，并通过对象名应用徽标样式。
        self.status_label = QLabel("状态：未运行", self)
        self.status_label.setObjectName("statusBadge")
        # 开关文案随选中状态变化，为用户提供启动或停止入口。
        self.open_switch = QPushButton("启动 frpc", self)
        self.open_switch.setCheckable(True)
        self.open_switch.setObjectName("primaryButton")
        self.open_switch.setMinimumWidth(144)

        # 控件创建完成后再组织布局并建立事件连接。
        self._build_ui()
        self._connect_signals()

    def shutdown(self) -> None:
        """页面关闭或应用退出时，停止正在运行的 frpc。"""
        # 将退出清理委托给服务，避免 UI 层直接干预底层进程对象。
        self.frpc_process_service.shutdown()

    def start_frpc(self) -> bool:
        """由外部页面请求启动 frpc，并返回是否成功发起启动。"""
        # 已运行时只修正界面状态，不重复创建进程。
        if self.frpc_process_service.is_running():
            self._set_switch_checked(True)
            return False

        # 启动结果尚未确定前禁用开关，防止连续点击产生并发请求。
        self.open_switch.setEnabled(False)
        # 服务拒绝或无法启动时恢复未选中状态及用户操作能力。
        if not self.frpc_process_service.start_frpc():
            self._set_switch_checked(False)
            self.open_switch.setEnabled(True)
            return False
        # 真正的运行状态稍后由服务的状态信号继续同步。
        return True

    def stop_frpc(self) -> bool:
        """由外部页面请求停止 frpc，并返回是否成功发起停止。"""
        # 停止结果尚未确定前禁用开关，防止用户重复提交请求。
        self.open_switch.setEnabled(False)
        # 无法发起停止时按服务当前约定恢复界面，并重新允许操作。
        if not self.frpc_process_service.stop_frpc():
            self._set_switch_checked(False)
            self.open_switch.setEnabled(True)
            return False
        # 最终停止状态由后续状态信号负责更新。
        return True

    def _build_ui(self) -> None:
        """创建本页面布局。"""
        # 主布局纵向排列标题与控制区，并保留统一页面边距。
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(18)

        # 页面直接承载标题和业务控件，直接调用后端服务。
        self.title_label = QLabel('FRP 客户端控制', self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.description_label = QLabel('默认使用 runtime/frpc.exe 和 config/frpc.toml 启动客户端。', self)
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.description_label)

        # 控制框架集中承载状态徽标与启动开关，并提供统一表面样式。
        control_frame = QFrame(self)
        control_frame.setObjectName("controlSurface")
        control_frame.setFrameShape(QFrame.Shape.StyledPanel)

        # 水平布局把状态放在左侧、开关推到右侧。
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(18, 16, 18, 16)
        control_layout.setSpacing(12)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.open_switch)

        # 多余空间留在底部，保持控制区靠上排列。
        main_layout.addWidget(control_frame)
        main_layout.addStretch()

    def _connect_signals(self) -> None:
        """连接开关交互以及进程服务的状态和错误信号。"""
        # 用户切换开关时进入统一处理器，以区分启动和停止操作。
        self.open_switch.toggled.connect(self._handle_switch_toggled)
        # 服务状态变化驱动标签、开关选中态和可用态同步更新。
        self.frpc_process_service.state_changed.connect(self._handle_frpc_state_changed)
        # 服务错误通知主窗口的状态栏。
        self.frpc_process_service.error_occurred.connect(self._handle_frpc_error)

    def _handle_switch_toggled(self, checked: bool) -> None:
        """用户点击开关后，启动或停止 frpc。"""
        # 程序主动同步选中态时忽略伴随产生的 toggled 信号。
        if self._syncing_switch:
            return

        # 选中表示请求启动；启动方法会在异步状态确定前管理开关可用性。
        if checked:
            self.start_frpc()
            return

        # 取消选中表示请求停止。
        self.stop_frpc()

    def _handle_frpc_state_changed(self, state: str) -> None:
        """根据进程服务返回的内部状态更新页面和外层提示。"""
        # 将稳定的内部状态值映射为面向用户的中文文案。
        labels = {
            "stopped": "未运行",
            "starting": "启动中",
            "running": "运行中",
            "stopping": "停止中",
        }
        # 未知状态保留原值，便于诊断服务新增或异常状态。
        state_text = labels.get(state, state)
        # 同步更新页面徽标，并向外层广播带进程名的状态消息。
        self.status_label.setText(f"状态：{state_text}")
        self.status_message_changed.emit(f"frpc {state_text}")

        # 只有进入最终状态后才重新允许点击。
        # 运行中：开关应该处于选中状态，下一次点击表示停止。
        if state == "running":
            self._set_switch_checked(True)
            self.open_switch.setEnabled(True)
        # 已停止：开关应该处于未选中状态，下一次点击表示启动。
        elif state == "stopped":
            self._set_switch_checked(False)
            self.open_switch.setEnabled(True)
        # 启动中或停止中都保持禁用，避免状态转换期间收到相反操作。
        else:
            self.open_switch.setEnabled(False)

    def _handle_frpc_error(self, message: str) -> None:
        """将进程服务错误交给主窗口状态栏显示。"""
        # 外层页面可使用同一消息更新全局运行提示。
        self.status_message_changed.emit(message)

    def _set_switch_checked(self, checked: bool) -> None:
        """由程序主动同步开关状态，避免触发业务逻辑。"""
        # 先开启同步保护，使 setChecked 触发的信号不会再次启动或停止进程。
        self._syncing_switch = True
        try:
            # 按服务真实状态更新开关外观。
            self.open_switch.setChecked(checked)
            self.open_switch.setText("停止 frpc" if checked else "启动 frpc")
        finally:
            # 即使控件更新异常也必须解除保护，避免后续用户操作永久失效。
            self._syncing_switch = False
