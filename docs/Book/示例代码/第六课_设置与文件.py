"""运行：python docs/Book/示例代码/第六课_设置与文件.py"""

import sys
from pathlib import Path

from PyQt6.QtCore import QByteArray, QIODevice, QSaveFile, QSettings, QStandardPaths
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QPlainTextEdit


class MainWindow(QMainWindow):
    def __init__(self, data_directory: Path):
        super().__init__()
        self.data_directory = data_directory
        self.current_path: Path | None = None
        self.settings = QSettings()
        self.last_directory = self.settings.value(
            "files/last_directory", str(data_directory), type=str
        )
        self.editor = QPlainTextEdit()
        self.setCentralWidget(self.editor)
        self.resize(800, 520)
        geometry = self.settings.value("window/geometry")
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        self.editor.document().modificationChanged.connect(self.update_title)

        file_menu = self.menuBar().addMenu("文件(&F)")
        actions = [
            ("打开…", QKeySequence.StandardKey.Open, self.open_file),
            ("保存", QKeySequence.StandardKey.Save, self.save_file),
            ("另存为…", QKeySequence.StandardKey.SaveAs, self.save_as),
        ]
        for text, shortcut, slot in actions:
            action = QAction(text, self)
            action.setShortcut(shortcut)
            action.triggered.connect(slot)
            file_menu.addAction(action)
        self.update_title()
        self.statusBar().showMessage(f"默认数据目录：{data_directory}")

    def update_title(self, modified: bool = False):
        name = self.current_path.name if self.current_path else "未命名"
        marker = " *" if self.editor.document().isModified() else ""
        self.setWindowTitle(f"{name}{marker} — 第六课：设置与文件")

    def confirm_discard_or_save(self) -> bool:
        if not self.editor.document().isModified():
            return True
        result = QMessageBox.question(
            self,
            "尚有未保存的修改",
            "是否先保存当前内容？",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if result == QMessageBox.StandardButton.Save:
            return self.save_file()
        return result == QMessageBox.StandardButton.Discard

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "打开 UTF-8 文本", self.last_directory, "文本文件 (*.txt);;所有文件 (*)"
        )
        if not filename:
            return
        if not self.confirm_discard_or_save():
            return
        path = Path(filename)
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(self, "打开失败", f"无法读取文件：\n{error}")
            return
        self.editor.setPlainText(content)
        self.editor.document().setModified(False)
        self.current_path = path
        self.last_directory = str(path.parent)
        self.update_title()

    def save_file(self) -> bool:
        if self.current_path is None:
            return self.save_as()
        return self.write_file(self.current_path)

    def save_as(self) -> bool:
        suggested_path = self.current_path or Path(self.last_directory) / "笔记.txt"
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存 UTF-8 文本", str(suggested_path), "文本文件 (*.txt);;所有文件 (*)"
        )
        if not filename:
            return False
        return self.write_file(Path(filename))

    def write_file(self, path: Path) -> bool:
        data = self.editor.toPlainText().encode("utf-8")
        file = QSaveFile(str(path))
        # 不启用 directWriteFallback：尽量保留临时文件+提交替换的保存方式。
        if not file.open(QIODevice.OpenModeFlag.WriteOnly):
            QMessageBox.critical(self, "保存失败", file.errorString())
            return False
        if file.write(data) != len(data):
            error = file.errorString()
            file.cancelWriting()
            QMessageBox.critical(self, "保存失败", error)
            return False
        if not file.commit():
            QMessageBox.critical(self, "保存失败", file.errorString())
            return False
        # 只有 commit 成功，才能把当前文档标记为已保存。
        self.current_path = path
        self.last_directory = str(path.parent)
        self.editor.document().setModified(False)
        self.update_title()
        self.statusBar().showMessage(f"已保存：{path}", 4000)
        return True

    def closeEvent(self, event: QCloseEvent):
        if not self.confirm_discard_or_save():
            event.ignore()
            return
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("files/last_directory", self.last_directory)
        self.settings.sync()
        if self.settings.status() != QSettings.Status.NoError:
            QMessageBox.warning(self, "偏好设置未保存", "窗口位置等偏好设置写入失败。")
        event.accept()


def main():
    app = QApplication(sys.argv)
    # 必须在创建 QSettings 和查询 AppDataLocation 之前设置应用身份。
    app.setOrganizationName("PyQt6Learning")
    app.setApplicationName("TextFileLesson")
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if not location:
        QMessageBox.critical(None, "启动失败", "系统未提供可用的应用数据目录。")
        sys.exit(1)
    data_directory = Path(location)
    try:
        data_directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        QMessageBox.critical(None, "启动失败", f"无法创建应用数据目录：\n{error}")
        sys.exit(1)
    window = MainWindow(data_directory)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
