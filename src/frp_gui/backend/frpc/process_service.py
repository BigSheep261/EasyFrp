"""frpc 子进程生命周期管理服务。"""

# 枚举用于向界面层提供有限且稳定的进程状态集合。
from enum import Enum
# 路径对象用于保存可执行文件和配置文件位置。
from pathlib import Path

# Qt 的进程、计时器和信号机制使外部程序控制不会阻塞界面线程。
from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal

# 默认运行时目录和配置目录遵循项目统一路径约定。
from frp_gui.utils.paths import CONFIG_DIR, RUNTIME_DIR


class FrpcProcessState(Enum):
    """受管 frpc 进程的运行状态。"""

    # 进程尚未启动或已经退出。
    STOPPED = "stopped"
    # 启动命令已提交，仍在等待 QProcess 的 started 信号。
    STARTING = "starting"
    # QProcess 已确认外部 frpc 进程成功启动。
    RUNNING = "running"
    # 已发出终止请求，正在等待进程退出或强制结束。
    STOPPING = "stopping"


class FrpcProcessService(QObject):
    """启动、停止并观察单个 frpc 进程。"""

    # 状态信号以枚举字符串值通知 UI/ViewModel 更新控件。
    state_changed = pyqtSignal(str)
    # 输出信号统一承载 frpc 的标准输出、标准错误和生命周期提示。
    output_received = pyqtSignal(str)
    # 错误信号向上层报告启动检查或 QProcess 运行错误。
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        executable_path: Path | None = None,
        config_path: Path | None = None,
        parent: QObject | None = None,
    ) -> None:
        """初始化进程服务、默认文件路径以及全部 QProcess 信号连接。"""
        # 将可选父对象交给 QObject，使 Qt 对服务实例执行正常的对象树管理。
        super().__init__(parent)
        # 默认约定：frpc 可执行文件放在 runtime，配置文件放在 config。
        # 之后增加配置管理时，可以从外部传入这两个路径来覆盖默认值。
        self.executable_path = executable_path or RUNTIME_DIR / "frpc.exe"
        self.config_path = config_path or CONFIG_DIR / "frpc.toml"
        # 服务初始状态与尚未运行的 QProcess 保持一致。
        self._state = FrpcProcessState.STOPPED
        # 将 QProcess 挂到当前 QObject 下，确保服务销毁时资源一并释放。
        self._process = QProcess(self)

        # QProcess 是异步的：启动、退出、输出和错误都通过信号回调处理，
        # 这样不会阻塞 Qt 主线程，也不会让窗口在 frpc 运行时卡住。
        self._process.readyReadStandardOutput.connect(self._read_stdout)
        self._process.readyReadStandardError.connect(self._read_stderr)
        # 生命周期信号分别驱动启动确认、退出分类和错误翻译逻辑。
        self._process.started.connect(self._handle_started)
        self._process.finished.connect(self._handle_finished)
        self._process.errorOccurred.connect(self._handle_error)

    @property
    def state(self) -> FrpcProcessState:
        """返回当前进程服务状态。"""
        # 对外只暴露只读枚举，状态修改统一经过 _set_state。
        return self._state

    def is_running(self) -> bool:
        """返回 frpc 当前是否正在启动或运行。"""
        # QProcess 只要不是 NotRunning，就仍需视为占用中的受管进程。
        return self._process.state() != QProcess.ProcessState.NotRunning

    def start_frpc(self) -> bool:
        """使用配置好的可执行文件和配置文件启动 frpc。"""
        # 避免重复点击按钮时启动多个 frpc 进程。
        if self.is_running():
            # 通过信号反馈重复启动原因，并用 False 表明本次未提交新进程。
            self.error_occurred.emit("frpc 已经在运行中。")
            return False

        # 先做本地路径检查，把常见错误直接反馈给调用方。
        # 如果文件存在但权限不足，后续 QProcess.errorOccurred 会继续给出错误。
        if not self.executable_path.exists():
            # 缺少程序时立即报告具体路径并确保状态回到已停止。
            self.error_occurred.emit(f"未找到 frpc 可执行文件：{self.executable_path}")
            self._set_state(FrpcProcessState.STOPPED)
            return False

        # 配置文件同样必须在启动前存在，否则 frpc 无法解析 -c 参数目标。
        if not self.config_path.exists():
            # 缺少配置时立即报告具体路径并确保状态回到已停止。
            self.error_occurred.emit(f"未找到 frpc 配置文件：{self.config_path}")
            self._set_state(FrpcProcessState.STOPPED)
            return False

        # 在调用 QProcess.start 前发布“启动中”，供界面禁用重复操作。
        self._set_state(FrpcProcessState.STARTING)
        # 工作目录设为 frpc.exe 所在目录，避免 frpc 依赖相对路径时找错位置。
        self._process.setWorkingDirectory(str(self.executable_path.parent))
        # 通过 -c 参数把选定 TOML 配置交给 frpc；实际成功由 started 信号确认。
        self._process.start(str(self.executable_path), ["-c", str(self.config_path)])
        # True 表示启动请求已成功提交，而非保证子进程已进入运行态。
        return True

    def stop_frpc(self, force_after_ms: int = 3000) -> bool:
        """请求正在运行的 frpc 进程停止。"""
        # 没有活动进程时只修正内部状态，不安排终止或计时任务。
        if not self.is_running():
            self._set_state(FrpcProcessState.STOPPED)
            return False

        # 先进入停止中状态，后续退出回调据此区分主动停止与异常崩溃。
        self._set_state(FrpcProcessState.STOPPING)
        # terminate 是温和退出请求；如果进程没有响应，稍后再强制 kill。
        self._process.terminate()
        # 单次计时回调不会阻塞 Qt 事件循环，到期后只在仍运行时执行兜底。
        QTimer.singleShot(force_after_ms, self._kill_if_still_running)
        # True 表示已对活动进程提交停止请求。
        return True

    def shutdown(self, timeout_ms: int = 3000) -> None:
        """在应用退出前停止 frpc。"""
        # 进程已经结束时无需等待，直接完成关闭流程。
        if not self.is_running():
            return

        # 标记主动停止，避免 Qt 将后续强制结束展示为意外崩溃。
        self._set_state(FrpcProcessState.STOPPING)
        # 应用退出时不能只发异步 terminate，否则 GUI 退出后 frpc 可能仍在后台。
        # 这里会短暂等待进程退出，超时后再强制结束。
        self._process.terminate()
        # 温和终止在时限内失败时强制结束，并再次等待资源回收。
        if not self._process.waitForFinished(timeout_ms):
            self._process.kill()
            self._process.waitForFinished(timeout_ms)

    def _set_state(self, state: FrpcProcessState) -> None:
        """更新内部状态，并仅在状态实际变化时向外发送通知。"""
        # 状态不变时不重复发信号，避免 UI 做无意义刷新。
        if self._state == state:
            return

        # 先保存新状态，再发送其字符串值，确保监听器读取到一致状态。
        self._state = state
        self.state_changed.emit(state.value)

    def _read_stdout(self) -> None:
        """读取当前全部标准输出，并交给统一解码与发送逻辑。"""
        # QProcess 返回 QByteArray 兼容对象，统一由输出函数转换为文本。
        self._emit_process_output(self._process.readAllStandardOutput())

    def _read_stderr(self) -> None:
        """读取当前全部标准错误，并交给统一解码与发送逻辑。"""
        # 标准错误与标准输出采用相同的日志展示通道。
        self._emit_process_output(self._process.readAllStandardError())

    def _emit_process_output(self, data: bytes) -> None:
        """将进程字节输出安全解码、清理后通过日志信号发送。"""
        # frpc 输出通常是 UTF-8；errors="replace" 可以避免异常字节导致日志显示崩溃。
        text = bytes(data).decode("utf-8", errors="replace").strip()
        # 忽略空白输出，避免界面日志出现无意义空行。
        if text:
            self.output_received.emit(text)

    def _handle_started(self) -> None:
        """响应 QProcess 启动成功信号，将服务状态切换为运行中。"""
        # started 信号表明操作系统已成功创建子进程。
        self._set_state(FrpcProcessState.RUNNING)

    def _handle_finished(
        self,
        exit_code: int,
        exit_status: QProcess.ExitStatus,
    ) -> None:
        """根据退出状态和停止意图分类通知，并将服务恢复为已停止。"""
        # 主动停止时，Qt 有时也会把强制结束报告成 CrashExit。
        # 这种情况对用户来说是“已停止”，不应该显示成异常崩溃。
        was_stopping = self._state == FrpcProcessState.STOPPING
        # 非主动停止的 CrashExit 才属于需要展示的异常退出。
        if exit_status == QProcess.ExitStatus.CrashExit and not was_stopping:
            self.error_occurred.emit(f"frpc 异常退出，退出码：{exit_code}")
        # 主动停止不论正常退出还是被 kill，都统一报告为已停止。
        elif was_stopping:
            self.output_received.emit("frpc 已停止。")
        # 其余情况属于子进程自行正常退出，保留退出码供用户判断。
        else:
            self.output_received.emit(f"frpc 已退出，退出码：{exit_code}")
        # 所有 finished 分支最终都清除运行状态并通知界面。
        self._set_state(FrpcProcessState.STOPPED)

    def _handle_error(self, error: QProcess.ProcessError) -> None:
        """将 QProcess 错误枚举转换为中文业务消息并修正终止状态。"""
        # 用户主动停止后触发的 Crashed 信号不作为错误展示。
        if error == QProcess.ProcessError.Crashed and self._state == FrpcProcessState.STOPPING:
            return

        # 为 Qt 定义的每种进程错误提供可直接展示给用户的中文说明。
        messages = {
            QProcess.ProcessError.FailedToStart: "frpc 启动失败，请检查可执行文件权限和路径。",
            QProcess.ProcessError.Crashed: "frpc 进程已崩溃。",
            QProcess.ProcessError.Timedout: "frpc 进程操作超时。",
            QProcess.ProcessError.WriteError: "向 frpc 进程写入数据失败。",
            QProcess.ProcessError.ReadError: "读取 frpc 进程输出失败。",
            QProcess.ProcessError.UnknownError: "frpc 发生未知进程错误。",
        }
        # 未命中的未来枚举值回退为包含枚举名称的通用错误消息。
        self.error_occurred.emit(messages.get(error, f"frpc 进程错误：{error.name}"))
        # 启动失败或崩溃意味着进程已不可继续运行，需要同步清除服务状态。
        if error in {
            QProcess.ProcessError.FailedToStart,
            QProcess.ProcessError.Crashed,
        }:
            self._set_state(FrpcProcessState.STOPPED)

    def _kill_if_still_running(self) -> None:
        """在温和终止超时后，仅对仍处于停止流程的活动进程执行强制结束。"""
        # stop_frpc 发出 terminate 后，如果 frpc 迟迟没有退出，就执行最后兜底。
        if self._state == FrpcProcessState.STOPPING and self.is_running():
            self._process.kill()


# 保留简短状态名称，兼容早期调用代码。
FrpcState = FrpcProcessState
# 保留控制器名称，实际实现统一由进程服务类承担。
FrpcController = FrpcProcessService
