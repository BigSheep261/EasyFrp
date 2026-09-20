"""运行：python docs/Book/示例代码/第四课_多页面窗口.py"""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class NameDialog(QDialog):
    """只负责收集并校验输入；是否更新主界面由调用者决定。"""

    def __init__(self, current_name: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("修改显示名称")
        self.name_edit = QLineEdit(current_name)
        self.error_label = QLabel()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.check_and_accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout()
        form.addRow("显示名称：", self.name_edit)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

    def check_and_accept(self):
        if not self.name_edit.text().strip():
            self.error_label.setText("名称不能为空，请输入后再确定。")
            self.name_edit.setFocus()
            return
        self.accept()

    def selected_name(self) -> str:
        return self.name_edit.text().strip()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.display_name = "学习者"
        self.setWindowTitle("第四课：多页面窗口")
        self.resize(780, 480)

        self.navigation = QListWidget()
        self.navigation.addItems(["学习首页", "临时笔记"])
        self.navigation.setMaximumWidth(160)

        self.pages = QStackedWidget()
        home = QWidget()
        home_layout = QVBoxLayout(home)
        self.welcome_label = QLabel()
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(self.welcome_label)
        self.pages.addWidget(home)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("这里的笔记只在本次运行中保留；第十三章再学习保存。")
        self.pages.addWidget(self.notes)

        center = QWidget()
        center_layout = QHBoxLayout(center)
        center_layout.addWidget(self.navigation)
        center_layout.addWidget(self.pages, 1)
        self.setCentralWidget(center)

        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.pages.currentChanged.connect(self.page_changed)

        rename_action = QAction("修改名称…", self)
        rename_action.setShortcut("Ctrl+R")
        rename_action.triggered.connect(self.rename_user)
        quit_action = QAction("退出", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        menu = self.menuBar().addMenu("应用(&A)")
        menu.addAction(rename_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        toolbar = self.addToolBar("常用操作")
        toolbar.addAction(rename_action)

        self.refresh_welcome()
        self.navigation.setCurrentRow(0)
        self.page_changed(0)

    def refresh_welcome(self):
        self.welcome_label.setText(f"你好，{self.display_name}！\n从左侧切换页面。")

    def rename_user(self):
        dialog = NameDialog(self.display_name, self)
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.display_name = dialog.selected_name()
                self.refresh_welcome()
                self.statusBar().showMessage("显示名称已修改", 3000)
        finally:
            # exec() 返回后先取值，再安排删除；避免反复打开时积累隐藏对象。
            dialog.deleteLater()

    def page_changed(self, index: int):
        if 0 <= index < self.navigation.count():
            self.statusBar().showMessage(
                f"当前页面：{self.navigation.item(index).text()}"
            )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
