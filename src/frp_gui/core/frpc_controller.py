"""frpc 进程生命周期管理。"""

from enum import Enum
from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal

from frp_gui.core.paths import CONFIG_DIR, RUNTIME_DIR


class FrpcState(Enum):
    """受管 frpc 进程的运行状态。"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


class FrpcController(QObject):
    """启动、停止并观察单个 frpc 进程。"""

    # 这三个信号是 core 和 UI 之间的通信边界：
    # UI 只监听状态、输出和错误，不直接操作 QProcess 的内部细节。
    state_changed = pyqtSignal(str)
    output_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        executable_path: Path | None = None,
        config_path: Path | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        # 默认约定：frpc 可执行文件放在 runtime，配置文件放在 config。
        # 之后增加配置管理时，可以从外部传入这两个路径来覆盖默认值。
        self.executable_path = executable_path or RUNTIME_DIR / "frpc.exe"
        self.config_path = config_path or CONFIG_DIR / "frpc.toml"
        self._state = FrpcState.STOPPED
        self._process = QProcess(self)

        # QProcess 是异步的：启动、退出、输出和错误都通过信号回调处理，
        # 这样不会阻塞 Qt 主线程，也不会让窗口在 frpc 运行时卡住。
        self._process.readyReadStandardOutput.connect(self._read_stdout)
        self._process.readyReadStandardError.connect(self._read_stderr)
        self._process.started.connect(self._handle_started)
        self._process.finished.connect(self._handle_finished)
        self._process.errorOccurred.connect(self._handle_error)

    @property
    def state(self) -> FrpcState:
        """返回当前控制器状态。"""
        return self._state

    def is_running(self) -> bool:
        """返回 frpc 当前是否正在启动或运行。"""
        return self._process.state() != QProcess.ProcessState.NotRunning

    def start_frpc(self) -> bool:
        """使用配置好的可执行文件和配置文件启动 frpc。"""
        # 避免重复点击按钮时启动多个 frpc 进程。
        if self.is_running():
            self.error_occurred.emit("frpc 已经在运行中。")
            return False

        # 先做本地路径检查，把常见错误直接反馈给 UI。
        # 如果文件存在但权限不足，后续 QProcess.errorOccurred 会继续给出错误。
        if not self.executable_path.exists():
            self.error_occurred.emit(f"未找到 frpc 可执行文件：{self.executable_path}")
            self._set_state(FrpcState.STOPPED)
            return False

        if not self.config_path.exists():
            self.error_occurred.emit(f"未找到 frpc 配置文件：{self.config_path}")
            self._set_state(FrpcState.STOPPED)
            return False

        self._set_state(FrpcState.STARTING)
        # 工作目录设为 frpc.exe 所在目录，避免 frpc 依赖相对路径时找错位置。
        self._process.setWorkingDirectory(str(self.executable_path.parent))
        self._process.start(str(self.executable_path), ["-c", str(self.config_path)])
        return True

    def stop_frpc(self, force_after_ms: int = 3000) -> bool:
        """请求正在运行的 frpc 进程停止。"""
        if not self.is_running():
            self._set_state(FrpcState.STOPPED)
            return False

        self._set_state(FrpcState.STOPPING)
        # terminate 是温和退出请求；如果进程没有响应，稍后再强制 kill。
        self._process.terminate()
        QTimer.singleShot(force_after_ms, self._kill_if_still_running)
        return True

    def shutdown(self, timeout_ms: int = 3000) -> None:
        """在应用退出前停止 frpc。"""
        if not self.is_running():
            return

        self._set_state(FrpcState.STOPPING)
        # 应用退出时不能只发异步 terminate，否则 GUI 退出后 frpc 可能仍在后台。
        # 这里会短暂等待进程退出，超时后再强制结束。
        self._process.terminate()
        if not self._process.waitForFinished(timeout_ms):
            self._process.kill()
            self._process.waitForFinished(timeout_ms)

    def _set_state(self, state: FrpcState) -> None:
        # 状态不变时不重复发信号，避免 UI 做无意义刷新。
        if self._state == state:
            return

        self._state = state
        self.state_changed.emit(state.value)

    def _read_stdout(self) -> None:
        self._emit_process_output(self._process.readAllStandardOutput())

    def _read_stderr(self) -> None:
        self._emit_process_output(self._process.readAllStandardError())

    def _emit_process_output(self, data: bytes) -> None:
        # frpc 输出通常是 UTF-8；errors="replace" 可以避免异常字节导致日志显示崩溃。
        text = bytes(data).decode("utf-8", errors="replace").strip()
        if text:
            self.output_received.emit(text)

    def _handle_started(self) -> None:
        self._set_state(FrpcState.RUNNING)

    def _handle_finished(
        self,
        exit_code: int,
        exit_status: QProcess.ExitStatus,
    ) -> None:
        # 主动停止时，Qt 有时也会把强制结束报告成 CrashExit。
        # 这种情况对用户来说是“已停止”，不应该显示成异常崩溃。
        was_stopping = self._state == FrpcState.STOPPING
        if exit_status == QProcess.ExitStatus.CrashExit and not was_stopping:
            self.error_occurred.emit(f"frpc 异常退出，退出码：{exit_code}")
        elif was_stopping:
            self.output_received.emit("frpc 已停止。")
        else:
            self.output_received.emit(f"frpc 已退出，退出码：{exit_code}")
        self._set_state(FrpcState.STOPPED)

    def _handle_error(self, error: QProcess.ProcessError) -> None:
        # 用户主动停止后触发的 Crashed 信号不作为错误展示。
        if error == QProcess.ProcessError.Crashed and self._state == FrpcState.STOPPING:
            return

        messages = {
            QProcess.ProcessError.FailedToStart: "frpc 启动失败，请检查可执行文件权限和路径。",
            QProcess.ProcessError.Crashed: "frpc 进程已崩溃。",
            QProcess.ProcessError.Timedout: "frpc 进程操作超时。",
            QProcess.ProcessError.WriteError: "向 frpc 进程写入数据失败。",
            QProcess.ProcessError.ReadError: "读取 frpc 进程输出失败。",
            QProcess.ProcessError.UnknownError: "frpc 发生未知进程错误。",
        }
        self.error_occurred.emit(messages.get(error, f"frpc 进程错误：{error.name}"))
        if error in {
            QProcess.ProcessError.FailedToStart,
            QProcess.ProcessError.Crashed,
        }:
            self._set_state(FrpcState.STOPPED)

    def _kill_if_still_running(self) -> None:
        # stop_frpc 发出 terminate 后，如果 frpc 迟迟没有退出，就执行最后兜底。
        if self._state == FrpcState.STOPPING and self.is_running():
            self._process.kill()
