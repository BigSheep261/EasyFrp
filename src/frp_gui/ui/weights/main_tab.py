from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPaintEvent
from PyQt6.QtWidgets import (
    QTabBar,
    QTabWidget,
    QStyle,
    QStyleOptionTab,
    QStylePainter,
    QWidget,
)

# 重绘TabBar，横向排列
class HorizontalTabBar(QTabBar):
    """标签位于侧边时，保留原生背景并横向绘制文字。"""
    def __init__(self, parent: QTabWidget | None = None) -> None:
        super().__init__(parent)

    def tabSizeHint(self, index: int) -> QSize:
        size = super().tabSizeHint(index)
        if self.shape() in (
            QTabBar.Shape.RoundedWest,
            QTabBar.Shape.RoundedEast,
            QTabBar.Shape.TriangularWest,
            QTabBar.Shape.TriangularEast,
        ):
            size.transpose()
        return size.expandedTo(QSize(140, 44))

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QStylePainter(self)
        indices = [index for index in range(self.count()) if index != self.currentIndex()]
        # 最后绘制选中标签，保持原生标签边缘的叠放顺序。
        if self.currentIndex() >= 0:
            indices.append(self.currentIndex())
        for index in indices:
            option = QStyleOptionTab()
            self.initStyleOption(option, index)
            if not event.region().intersects(option.rect):
                continue
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, option)
            # 仅按顶部标签的方向绘制文字，保留真实侧边标签的背景形状。
            option.shape = QTabBar.Shape.RoundedNorth
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabLabel, option)


class EasyFrpTabWidget(QTabWidget):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("EasyFrp_TabWidget")

        TabBar = HorizontalTabBar(self)
        TabBar.setObjectName("EasyFrp_TabBar")

        self.setTabBar(TabBar)
        self.setTabPosition(QTabWidget.TabPosition.West)