"""应用程序主窗口。"""

from PyQt6.QtWidgets import QMainWindow, QWidget


class MainWindow(QMainWindow):
    """EasyFrp 的顶层窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EasyFrp")
        self.resize(960, 640)
        self.setCentralWidget(QWidget(self))
        self.statusBar().showMessage("就绪")
