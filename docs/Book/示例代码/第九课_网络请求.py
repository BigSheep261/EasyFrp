"""QNetworkAccessManager：主线程异步请求、总超时、取消与资源释放。"""

import sys

from PyQt6.QtCore import QTimer, QUrl, pyqtSlot
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import (
    QApplication, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QVBoxLayout, QWidget,
)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("第九课：异步网络请求")
        self.resize(700, 430)
        self.manager = QNetworkAccessManager(self)
        self._reply = None
        self._timed_out = False
        self._cancelled = False
        self._closing = False
        self._too_large = False
        self._body = bytearray()
        self._max_bytes = 128 * 1024
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_timeout)
        self.url_input = QLineEdit("https://example.com")
        self.status = QLabel("输入 HTTP 或 HTTPS 地址后点击请求")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.get_button = QPushButton("请求")
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setEnabled(False)
        layout = QVBoxLayout(self)
        for widget in (self.url_input, self.status, self.output,
                       self.get_button, self.cancel_button):
            layout.addWidget(widget)
        self.get_button.clicked.connect(self.start_request)
        self.cancel_button.clicked.connect(self.cancel_request)

    @pyqtSlot()
    def start_request(self):
        if self._reply is not None or self._closing:
            return
        url = QUrl(self.url_input.text().strip())
        if not url.isValid() or url.scheme() not in ("http", "https") or not url.host():
            self.status.setText("请输入完整地址，例如 https://example.com")
            return
        self._timed_out = False
        self._cancelled = False
        self._too_large = False
        self._body.clear()
        self.output.clear()
        self.status.setText("请求中，界面仍可以操作……")
        self.get_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.url_input.setEnabled(False)
        request = QNetworkRequest(url)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        self._reply = self.manager.get(request)
        self._reply.readyRead.connect(self.read_body)
        self._reply.finished.connect(self.request_finished)
        # 这是整个请求的时间上限，不是单次读取的超时。
        self.timer.start(10000)

    @pyqtSlot()
    def read_body(self):
        reply = self._reply
        if reply is None:
            return
        chunk = bytes(reply.readAll())
        remaining = self._max_bytes - len(self._body)
        self._body.extend(chunk[:remaining])
        if len(chunk) > remaining and not self._too_large:
            self._too_large = True
            reply.abort()

    @pyqtSlot()
    def on_timeout(self):
        if self._reply is not None:
            self._timed_out = True
            self._reply.abort()

    @pyqtSlot()
    def cancel_request(self):
        if self._reply is not None:
            self._cancelled = True
            self._reply.abort()

    @pyqtSlot()
    def request_finished(self):
        reply = self._reply
        if reply is None:
            return
        self.timer.stop()
        self.read_body()
        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if self._timed_out:
            message = "请求超过 10 秒，已取消"
        elif self._cancelled:
            message = "请求已取消"
        elif self._too_large:
            message = "响应超过 128 KiB，已停止接收"
        elif reply.error() != QNetworkReply.NetworkError.NoError:
            message = f"请求失败，HTTP 状态 {status_code}：{reply.errorString()}"
        elif status_code is None or not 200 <= int(status_code) < 300:
            message = f"服务器返回非成功状态：{status_code}"
        else:
            message = f"请求成功，HTTP 状态 {status_code}，收到 {len(self._body)} 字节"
        self.status.setText(message)
        # 演示文本按 UTF-8 解码，真实接口应遵循其编码约定。
        self.output.setPlainText(bytes(self._body).decode("utf-8", errors="replace"))
        self._reply = None
        reply.deleteLater()
        self.get_button.setEnabled(not self._closing)
        self.cancel_button.setEnabled(False)
        self.url_input.setEnabled(not self._closing)

    def closeEvent(self, event):
        self._closing = True
        self.timer.stop()
        if self._reply is not None:
            self._cancelled = True
            self._reply.abort()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
