"""Main application window."""

from PyQt6.QtWidgets import QMainWindow, QWidget


class MainWindow(QMainWindow):
    """Top-level window for EasyFrp."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EasyFrp")
        self.resize(960, 640)
        self.setCentralWidget(QWidget(self))
        self.statusBar().showMessage("就绪")
