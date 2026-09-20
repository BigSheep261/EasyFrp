r"""第一课：一个完整、可运行的 PyQt6 窗口。

在项目根目录使用学习虚拟环境运行：
    .\docs\Book\.venv\Scripts\python.exe .\docs\Book\示例代码\第一课_你好窗口.py
"""

import sys

from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget


class GreetingWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.click_count = 0
        self.setWindowTitle("第一课：你好，PyQt6")
        self.resize(420, 200)

        self.message_label = QLabel("欢迎！试着点击下面的按钮。")
        self.greet_button = QPushButton("打个招呼")

        layout = QVBoxLayout(self)
        layout.addWidget(self.message_label)
        layout.addWidget(self.greet_button)
        self.greet_button.clicked.connect(self.say_hello)

    def say_hello(self) -> None:
        self.click_count += 1
        self.message_label.setText(f"你好！你已经点击了 {self.click_count} 次。")


def main() -> int:
    app = QApplication(sys.argv)
    window = GreetingWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
