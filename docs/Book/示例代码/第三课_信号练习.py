"""第三课：使用自定义信号，让数值模型同步多个控件。"""

import sys

from PyQt6.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class Counter(QObject):
    # 信号必须定义在 QObject 子类的类体中。
    value_changed = pyqtSignal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._value = 0

    def value(self) -> int:
        return self._value

    @pyqtSlot(int)
    def set_value(self, value: int) -> None:
        value = max(0, min(value, 100))
        # 值没变就不发信号，这是防止循环同步的重要边界。
        if value == self._value:
            return
        self._value = value
        self.value_changed.emit(value)


class SignalWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("第三课：信号与槽")
        self.resize(480, 220)
        self.counter = Counter(self)

        self.value_label = QLabel()
        self.value_spin = QSpinBox()
        self.value_spin.setRange(0, 100)
        self.value_slider = QSlider(Qt.Orientation.Horizontal)
        self.value_slider.setRange(0, 100)
        self.add_button = QPushButton("加一")
        self.reset_button = QPushButton("归零")

        buttons = QHBoxLayout()
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.reset_button)
        root = QVBoxLayout(self)
        root.addWidget(self.value_label)
        root.addWidget(self.value_spin)
        root.addWidget(self.value_slider)
        root.addLayout(buttons)

        # 控件输入 -> 模型；模型变化 -> 所有显示控件。
        self.value_spin.valueChanged.connect(self.counter.set_value)
        self.value_slider.valueChanged.connect(self.counter.set_value)
        self.counter.value_changed.connect(self.value_spin.setValue)
        self.counter.value_changed.connect(self.value_slider.setValue)
        self.counter.value_changed.connect(self.show_value)
        self.add_button.clicked.connect(self.increase)
        self.reset_button.clicked.connect(self.reset)
        self.show_value(self.counter.value())

    @pyqtSlot(int)
    def show_value(self, value: int) -> None:
        self.value_label.setText(f"当前数值：{value}（范围 0～100）")

    def increase(self) -> None:
        self.counter.set_value(self.counter.value() + 1)

    def reset(self) -> None:
        self.counter.set_value(0)


def main() -> int:
    app = QApplication(sys.argv)
    window = SignalWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
