"""运行：python docs/Book/综合实战/启动程序.py"""

import sys
from PyQt6.QtWidgets import QApplication
from 任务窗口 import TaskWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName("PyQt6学习书")
    app.setApplicationName("桌面任务管理器")
    window = TaskWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

