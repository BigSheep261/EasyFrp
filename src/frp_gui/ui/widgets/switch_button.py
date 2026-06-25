"""开关按钮组件。

这个文件放在 widgets 目录下，表示它是一个“通用小组件”。
它只负责自己的显示效果和基础交互，不直接绑定 frpc/frps 之类的业务逻辑。
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QWidget


class SwitchButton(QCheckBox):
    """带开关文案的按钮。

    PyQt 中所有可显示在界面上的元素，基本都要放在某个 QWidget 子类里。
    这里继承 QCheckBox，是因为 QCheckBox 天然有 checked/unchecked 两种状态，
    很适合用来做“启动/停止”这种开关。

    这个类只处理两件事：
    1. 用户切换 checked 状态时，同步显示不同文案。
    2. 提供一个统一样式，方便其他模块直接复用。

    注意：这个组件不知道 frpc 是什么，也不会调用 start_frpc()。
    具体业务应该由 panels 或 pages 层绑定。
    """

    def __init__(
        self,
        off_text: str = "启动",
        on_text: str = "停止",
        parent: QWidget | None = None,
    ) -> None:
        """初始化开关。

        Args:
            off_text: 未选中时显示的文案，通常表示“可以启动”。
            on_text: 选中时显示的文案，通常表示“可以停止”。
            parent: PyQt 的父组件。传入父组件后，Qt 会帮忙管理生命周期。
        """
        super().__init__(parent)
        self._off_text = off_text
        self._on_text = on_text

        # 鼠标悬停时显示手型，暗示这是一个可以点击的控件。
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(144)
        self.setObjectName("switchButton")

        # QCheckBox 自带 toggled(bool) 信号。
        # 每次 checked 状态变化时，更新按钮旁边的文案。
        self.toggled.connect(self._update_text)
        self._update_text(self.isChecked())

    def _update_text(self, checked: bool) -> None:
        """根据开关状态更新显示文案。"""
        self.setText(self._on_text if checked else self._off_text)
