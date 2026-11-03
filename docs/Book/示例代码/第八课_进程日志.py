"""QProcess：异步读取 UTF-8 日志，处理失败、停止和关闭。"""

import codecs
import sys

from PyQt6.QtCore import QProcess, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)


CHILD_CODE = """
import sys
import time
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
for index in range(1, 31):
    print(f'中文日志：正在处理第 {index} 项', flush=True)
    if index == 10:
        print('演示：这是一条标准错误日志', file=sys.stderr, flush=True)
    time.sleep(0.2)
"""


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("第八课：外部进程日志")
        self.resize(620, 400)
        self._closing = False
        self._busy = False
        self._decoder = None
        self._decoder_finalized = True
        self.process = QProcess(self)
        # 合并流以后只读取标准输出；不再逐行区分来源。
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.kill_timer = QTimer(self)
        self.kill_timer.setSingleShot(True)
        self.kill_timer.timeout.connect(self.force_stop)
        self.status = QLabel("准备就绪")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.document().setMaximumBlockCount(2000)
        self.start_button = QPushButton("启动演示子进程")
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        layout = QVBoxLayout(self)
        for widget in (self.status, self.output, self.start_button, self.stop_button):
            layout.addWidget(widget)
        self.start_button.clicked.connect(self.start_process)
        self.stop_button.clicked.connect(self.stop_process)
        self.process.started.connect(self.process_started)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.errorOccurred.connect(self.process_error)
        self.process.finished.connect(self.process_finished)

    def append_text(self, text):
        # insertPlainText 不擅自为每个数据块补一行。
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    @pyqtSlot()
    def start_process(self):
        if self._busy or self._closing:
            return
        self._busy = True
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._decoder_finalized = False
        self.output.clear()
        self.status.setText("正在启动……")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # 程序与参数分开传入；不拼接 shell 命令。
        self.process.start(sys.executable, ["-u", "-c", CHILD_CODE])

    @pyqtSlot()
    def process_started(self):
        # 启动尚未完成时也可能已经收到停止请求。
        if self._closing or self.kill_timer.isActive():
            self.stop_process()
        else:
            self.status.setText("子进程正在运行")

    @pyqtSlot()
    def read_output(self):
        data = bytes(self.process.readAllStandardOutput())
        if self._decoder is not None and not self._decoder_finalized:
            self.append_text(self._decoder.decode(data, final=False))

    def finish_decoder(self):
        if self._decoder is not None and not self._decoder_finalized:
            self.read_output()
            self.append_text(self._decoder.decode(b"", final=True))
            self._decoder_finalized = True

    @pyqtSlot(QProcess.ProcessError)
    def process_error(self, error):
        self.append_text(f"\n进程错误：{self.process.errorString()}\n")
        if error == QProcess.ProcessError.FailedToStart:
            # 启动失败不保证发出 finished，必须单独复位。
            self.finish_decoder()
            self.status.setText("启动失败")
            self.reset_controls()

    @pyqtSlot(int, QProcess.ExitStatus)
    def process_finished(self, exit_code, exit_status):
        self.finish_decoder()
        self.status.setText(f"进程已结束：退出码 {exit_code}，状态 {exit_status.name}")
        self.reset_controls()

    def reset_controls(self):
        self.kill_timer.stop()
        self._busy = False
        self.start_button.setEnabled(not self._closing)
        self.stop_button.setEnabled(False)
        if self._closing:
            QTimer.singleShot(0, self.close)

    @pyqtSlot()
    def stop_process(self):
        if self.process.state() == QProcess.ProcessState.NotRunning:
            return
        self.status.setText("正在停止，2 秒后仍未退出则强制结束……")
        self.stop_button.setEnabled(False)
        self.process.terminate()
        self.kill_timer.start(2000)

    @pyqtSlot()
    def force_stop(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

    def closeEvent(self, event):
        if self._busy:
            self._closing = True
            self.stop_process()
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
