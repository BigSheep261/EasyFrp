"""frpc 子进程生命周期管理服务。"""
from enum import Enum
from unittest import case

# Qt 的进程、计时器和信号机制使外部程序控制不会阻塞界面线程。
from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal
# 默认运行时目录和配置目录遵循项目统一路径约定。
from frp_gui.utils.paths import CONFIG_DIR, RUNTIME_DIR

""" frpc的状态枚举 """
class FrpCStateEnum(Enum):
    # 连接状态
    Disconnected = "Disconnected"   # 离线
    Connecting = "Connecting"       # 连接中
    Online = "Online"               # 在线
    Reconnecting = "Reconnecting"   # 重连中

    # 进程状态
    NotFound = "NotFound"   # 未找到软件
    Stopped = "Stopped"     # 未运行
    Starting = "Starting"   # 启动中
    Running = "Running"     # 运行中
    Stopping = "Stopping"   # 停止中

class FrpcProcessService(QObject):
    """启动、停止并观察单个 frpc 进程。"""

    process_state_changed = pyqtSignal(str) # 进程状态
    connect_state_changed = pyqtSignal(str) # 连接状态

    # 当前路径写死，frpc 可执行文件放在 runtime，配置文件放在 config。
    executable_path = RUNTIME_DIR / "frpc.exe"
    config_path = CONFIG_DIR / "frpc.toml"

    # 初始的进程状态和连接状态
    _process_state = FrpCStateEnum.NotFound
    _connect_state = FrpCStateEnum.Disconnected


    def __init__(self, parent: QObject | None = None,) -> None:
        """初始化进程服务、默认文件路径以及全部 QProcess 信号连接。"""
        # 将可选父对象交给 QObject，使 Qt 对服务实例执行正常的对象树管理。
        super().__init__(parent)

        # 将 QProcess 挂到当前 QObject 下，确保服务销毁时资源一并释放。
        self._process = QProcess(self)

        # 不采集或保存进程输出，直接丢弃，避免未消费的输出占用内存。
        self._process.setStandardOutputFile(QProcess.nullDevice())
        self._process.setStandardErrorFile(QProcess.nullDevice())
        # 监听进程生命周期供界面更新状态。
        self._process.stateChanged.connect(self._handle_state_change)


    def switch_frpc_state(self):
        """切换frpc的启动状态"""
        match self._process.state():
            case QProcess.ProcessState.NotRunning:
                # TODO::切换到启动状态
                self.start_frpc()

            case QProcess.ProcessState.Running:
                # TODO::切换到关闭状态
                self.stop_frpc()

            case _:
                # TODO::启动中/关闭中，不进行处理
                print("未知状态")

    def _handle_state_change(self):
        match self._process_state:
            case QProcess.ProcessState.NotRunning:
                return
            case QProcess.ProcessState.Running:
                return
            case _:
                return


    def start_frpc(self) -> bool:
        """使用配置好的可执行文件和配置文件启动 frpc。"""

        # 工作目录设为 frpc.exe 所在目录，避免 frpc 依赖相对路径时找错位置。
        self._process.setWorkingDirectory(str(self.executable_path.parent))
        # 通过 -c 参数把选定 TOML 配置交给 frpc；实际成功由 started 信号确认。
        self._process.start(str(self.executable_path), ["-c", str(self.config_path)])
        # True 表示启动请求已成功提交，而非保证子进程已进入运行态。
        return True


    def stop_frpc(self, force_after_ms: int = 3000) -> bool:
        """请求正在运行的 frpc 进程停止。"""
        self.shutdown(force_after_ms)
        return True

    @property
    def process_state(self) -> FrpCStateEnum:
        return self._process_state

    @property
    def connect_state(self) -> FrpCStateEnum:
        return self._connect_state

    def shutdown(self, timeout_ms: int = 3000) -> None:
        self._process.terminate()
        # 温和终止在时限内失败时强制结束
        if not self._process.waitForFinished(timeout_ms):
            self._process.kill()

# 保留控制器名称，实际实现统一由进程服务类承担。
FrpcController = FrpcProcessService
