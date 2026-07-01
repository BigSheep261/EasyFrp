"""frpc 控制页面。

pages 层表示“一个完整页面”。
这个页面会导入 panels/frpc_open.py 中的 FrpcOpenPanel，
然后负责设置标题、说明文案，以及把功能模块摆放到合适的位置。
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from frp_gui.ui.panels.frpc_open import FrpcOpenPanel


class FrpcControlView(QWidget):
    """侧边栏中的 frpc 控制页面。"""

    # 页面把 panel 的状态消息继续向外转发。
    # main_window 不需要知道 panel 内部结构，只监听页面信号即可。
    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_label = QLabel("FRP 客户端控制", self)
        self.title_label.setObjectName("pageTitle")
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.description_label = QLabel(
            "默认使用 runtime/frpc.exe 和 config/frpc.toml 启动客户端。",
            self,
        )
        self.description_label.setObjectName("pageDescription")
        self.description_label.setWordWrap(True)

        self.frpc_open_panel = FrpcOpenPanel(self)
        self.frpc_open_panel.status_message_changed.connect(
            self.status_message_changed.emit
        )

        self._build_ui()

    def shutdown(self) -> None:
        """让页面内的功能模块释放运行中的资源。"""
        self.frpc_open_panel.shutdown()

    def start_frpc(self) -> bool:
        """请求页面内的功能模块启动 frpc。"""
        return self.frpc_open_panel.start_frpc()

    def _build_ui(self) -> None:
        """创建页面级布局。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.frpc_open_panel, stretch=1)
