"""frpc 手动进程控制与状态页面。"""

from PyQt6.QtWidgets import QWidget

from frp_gui.ui.generated.ui_frpc_control import Ui_Frpc_Control_Form
# 进程服务封装 frpc 的启动、停止、状态通知和错误提示。
from frp_gui.backend.frpc.process_service import FrpcProcessService


class FrpcControlView(QWidget):
    """直接管理 frpc 手动启停控件，并将进程操作委托给后端服务。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化进程服务、状态控件和信号连接。"""
        super().__init__(parent)

        self.frpc_process_service = FrpcProcessService(parent=self)
        self._build_ui()
        self._connect_signals()

    def switch_frpc_state(self) -> bool:
        """切换frpc的启动状态"""
        self.frpc_process_service.switch_frpc_state()
        return True

    def _build_ui(self) -> None:
        """使用 Designer 生成的界面代码装配当前页面。"""
        self.ui = Ui_Frpc_Control_Form()
        self.ui.setupUi(self)


    def _connect_signals(self) -> None:
        """连接开关交互以及进程服务的状态和错误信号。"""
        self.ui.Frpc_Control_Button_Start.clicked.connect(self.switch_frpc_state)

    def shutdown(self) -> None:
        """页面关闭或应用退出时，停止正在运行的 frpc。"""
        # 将退出清理委托给服务，避免 UI 层直接干预底层进程对象。
        self.frpc_process_service.shutdown()