
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QLabel


class EasyFrpDashBoard(QWidget):

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self.title_label = QLabel("DashBoard", self)