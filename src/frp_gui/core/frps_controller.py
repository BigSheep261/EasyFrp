"""frps 进程生命周期管理。"""

from enum import Enum
from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal

from frp_gui.core.paths import CONFIG_DIR, RUNTIME_DIR


class FrpsState(Enum):
    """受管 frps 进程的运行状态。"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


class FrpsController(QObject):
    """启动、停止并观察单个 frps 进程。"""

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
        self.executable_path = executable_path or RUNTIME_DIR / "frps.exe"
        self.config_path = config_path or CONFIG_DIR / "frps.toml"
        self._state = FrpsState.STOPPED
        self._process = QProcess(self)

        self._process.readyReadStandardOutput.connect(self._read_stdout)
        self._process.readyReadStandardError.connect(self._read_stderr)
        self._process.started.connect(self._handle_started)
        self._process.finished.connect(self._handle_finished)
        self._process.errorOccurred.connect(self._handle_error)

    @property
    def state(self) -> FrpsState:
        """返回当前控制器状态。"""
        return self._state

    def is_running(self) -> bool:
        """返回 frps 当前是否正在启动或运行。"""
        return self._process.state() != QProcess.ProcessState.NotRunning

    def start_frps(self) -> bool:
        """使用配置好的可执行文件和配置文件启动 frps。"""
        if self.is_running():
            self.error_occurred.emit("frps 已经在运行中。")
            return False

        if not self.executable_path.exists():
            self.error_occurred.emit(f"未找到 frps 可执行文件：{self.executable_path}")
            self._set_state(FrpsState.STOPPED)
            return False

        if not self.config_path.exists():
            self.error_occurred.emit(f"未找到 frps 配置文件：{self.config_path}")
            self._set_state(FrpsState.STOPPED)
            return False

        self._set_state(FrpsState.STARTING)
        self._process.setWorkingDirectory(str(self.executable_path.parent))
        self._process.start(str(self.executable_path), ["-c", str(self.config_path)])
        return True

    def stop_frps(self, force_after_ms: int = 3000) -> bool:
        """请求正在运行的 frps 进程停止。"""
        if not self.is_running():
            self._set_state(FrpsState.STOPPED)
            return False

        self._set_state(FrpsState.STOPPING)
        self._process.terminate()
        QTimer.singleShot(force_after_ms, self._kill_if_still_running)
        return True

    def shutdown(self, timeout_ms: int = 3000) -> None:
        """在应用退出前停止 frps。"""
        if not self.is_running():
            return

        self._set_state(FrpsState.STOPPING)
        self._process.terminate()
        if not self._process.waitForFinished(timeout_ms):
            self._process.kill()
            self._process.waitForFinished(timeout_ms)

    def _set_state(self, state: FrpsState) -> None:
        if self._state == state:
            return

        self._state = state
        self.state_changed.emit(state.value)

    def _read_stdout(self) -> None:
        self._emit_process_output(self._process.readAllStandardOutput())

    def _read_stderr(self) -> None:
        self._emit_process_output(self._process.readAllStandardError())

    def _emit_process_output(self, data: bytes) -> None:
        text = bytes(data).decode("utf-8", errors="replace").strip()
        if text:
            self.output_received.emit(text)

    def _handle_started(self) -> None:
        self._set_state(FrpsState.RUNNING)

    def _handle_finished(
        self,
        exit_code: int,
        exit_status: QProcess.ExitStatus,
    ) -> None:
        was_stopping = self._state == FrpsState.STOPPING
        if exit_status == QProcess.ExitStatus.CrashExit and not was_stopping:
            self.error_occurred.emit(f"frps 异常退出，退出码：{exit_code}")
        elif was_stopping:
            self.output_received.emit("frps 已停止。")
        else:
            self.output_received.emit(f"frps 已退出，退出码：{exit_code}")
        self._set_state(FrpsState.STOPPED)

    def _handle_error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.Crashed and self._state == FrpsState.STOPPING:
            return

        messages = {
            QProcess.ProcessError.FailedToStart: "frps 启动失败，请检查可执行文件权限和路径。",
            QProcess.ProcessError.Crashed: "frps 进程已崩溃。",
            QProcess.ProcessError.Timedout: "frps 进程操作超时。",
            QProcess.ProcessError.WriteError: "向 frps 进程写入数据失败。",
            QProcess.ProcessError.ReadError: "读取 frps 进程输出失败。",
            QProcess.ProcessError.UnknownError: "frps 发生未知进程错误。",
        }
        self.error_occurred.emit(messages.get(error, f"frps 进程错误：{error.name}"))
        if error in {
            QProcess.ProcessError.FailedToStart,
            QProcess.ProcessError.Crashed,
        }:
            self._set_state(FrpsState.STOPPED)

    def _kill_if_still_running(self) -> None:
        if self._state == FrpsState.STOPPING and self.is_running():
            self._process.kill()
