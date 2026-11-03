"""QObject + QThread：进度、失败、协作取消，以及运行中安全关闭窗口。"""

import sys
import traceback

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QLabel, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)


class Worker(QObject):
    progress = pyqtSignal(int)
    failed = pyqtSignal(str)
    result = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, simulate_error=False):
        super().__init__()
        self.simulate_error = simulate_error

    @pyqtSlot()
    def run(self):
        try:
            for number in range(1, 101):
                if QThread.currentThread().isInterruptionRequested():
                    self.result.emit("任务已经取消")
                    return
                # 只在后台线程中模拟耗时；真实任务也需要短步骤和超时。
                QThread.msleep(40)
                if self.simulate_error and number == 50:
                    raise RuntimeError("教学用错误：处理第 50 项时失败")
                self.progress.emit(number)
            self.result.emit("任务正常完成")
        except Exception:
            self.failed.emit(traceback.format_exc())
        finally:
            # 不论成功、失败或取消，都通知线程结束。
            self.finished.emit()


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("第七课：后台任务")
        self.resize(420, 230)
        self._thread = None
        self._worker = None
        self._closing = False
        self.status = QLabel("准备就绪")
        self.status.setWordWrap(True)
        self.progress = QProgressBar()
        self.error_option = QCheckBox("模拟处理失败")
        self.start_button = QPushButton("开始")
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setEnabled(False)
        layout = QVBoxLayout(self)
        for widget in (self.status, self.progress, self.error_option,
                       self.start_button, self.cancel_button):
            layout.addWidget(widget)
        self.start_button.clicked.connect(self.start_task)
        self.cancel_button.clicked.connect(self.cancel_task)

    @pyqtSlot()
    def start_task(self):
        if self._thread is not None or self._closing:
            return
        self.progress.setValue(0)
        self.status.setText("正在处理……")
        self.start_button.setEnabled(False)
        self.error_option.setEnabled(False)
        self.cancel_button.setEnabled(True)
        thread = QThread(self)
        worker = Worker(self.error_option.isChecked())
        worker.moveToThread(thread)
        self._thread = thread
        self._worker = worker
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress.setValue)
        worker.result.connect(self.show_result)
        worker.failed.connect(self.show_failure)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self.thread_finished)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @pyqtSlot(str)
    def show_result(self, message):
        self.status.setText(message)

    @pyqtSlot(str)
    def show_failure(self, details):
        # 技术详情写到终端，界面给出简明状态。
        print(details, file=sys.stderr)
        self.status.setText("任务失败，详情见终端")

    @pyqtSlot()
    def cancel_task(self):
        if self._thread is not None:
            self._thread.requestInterruption()
            self.cancel_button.setEnabled(False)
            self.status.setText("正在等待当前步骤结束……")

    @pyqtSlot()
    def thread_finished(self):
        self._worker = None
        self._thread = None
        self.cancel_button.setEnabled(False)
        self.start_button.setEnabled(not self._closing)
        self.error_option.setEnabled(not self._closing)
        if self._closing:
            QTimer.singleShot(0, self.close)

    def closeEvent(self, event):
        if self._thread is not None:
            self._closing = True
            self.cancel_task()
            self.status.setText("正在结束后台任务，结束后自动关闭……")
            event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
