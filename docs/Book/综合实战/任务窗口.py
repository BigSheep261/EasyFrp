"""界面负责收集输入、调用规则与仓库、显示结果。"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from 任务仓库 import TaskRepository
from 任务数据 import PRIORITIES, Task


class TaskWindow(QMainWindow):
    def __init__(self, repository: TaskRepository | None = None) -> None:
        super().__init__()
        self.repository = repository if repository is not None else TaskRepository()
        self.tasks: list[Task] = []
        self.current_path: Path | None = None
        self.dirty = False
        self.resize(720, 500)
        self._build_ui()
        self._build_actions()
        self._connect_signals()
        self._refresh()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        form = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("输入任务，最多 80 字；回车添加")
        self.title_input.setMaxLength(80)
        name_label = QLabel("任务名称(&T)：")
        name_label.setBuddy(self.title_input)
        self.priority_input = QComboBox()
        self.priority_input.addItems(PRIORITIES)
        self.priority_input.setCurrentText("中")
        self.priority_input.setAccessibleName("任务优先级")
        self.add_button = QPushButton("添加")
        form.addWidget(name_label)
        form.addWidget(self.title_input, 1)
        form.addWidget(self.priority_input)
        form.addWidget(self.add_button)
        layout.addLayout(form)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("按名称搜索，不会删除原始任务")
        self.search_input.setAccessibleName("搜索任务")
        layout.addWidget(self.search_input)
        self.task_list = QListWidget()
        self.task_list.setAccessibleName("任务列表")
        layout.addWidget(self.task_list, 1)
        operations = QHBoxLayout()
        self.toggle_button = QPushButton("切换完成状态")
        self.delete_button = QPushButton("删除选中任务")
        operations.addWidget(self.toggle_button)
        operations.addWidget(self.delete_button)
        operations.addStretch()
        layout.addLayout(operations)

    def _build_actions(self) -> None:
        menu = self.menuBar().addMenu("文件(&F)")
        self.new_action = QAction("新建", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.open_action = QAction("打开…", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.save_action = QAction("保存", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_as_action = QAction("另存为…", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.exit_action = QAction("退出", self)
        for action in (self.new_action, self.open_action, self.save_action,
                       self.save_as_action, self.exit_action):
            menu.addAction(action)

    def _connect_signals(self) -> None:
        self.add_button.clicked.connect(self.add_task)
        self.title_input.returnPressed.connect(self.add_task)
        self.search_input.textChanged.connect(self._refresh)
        self.task_list.itemSelectionChanged.connect(self._update_selection)
        self.toggle_button.clicked.connect(self.toggle_task)
        self.delete_button.clicked.connect(self.delete_task)
        self.new_action.triggered.connect(self.new_document)
        self.open_action.triggered.connect(self.open_document)
        self.save_action.triggered.connect(self.save_document)
        # triggered 会带 checked 参数，适配后才传给“另存为”参数。
        self.save_as_action.triggered.connect(lambda: self.save_document(save_as=True))
        self.exit_action.triggered.connect(self.close)

    def _selected_id(self) -> str | None:
        # 当前项可以仍有键盘焦点但未被选中，例如 Ctrl+单击取消选择后。
        selected = self.task_list.selectedItems()
        return None if not selected else selected[0].data(Qt.ItemDataRole.UserRole)

    def _refresh(self) -> None:
        selected_id = self._selected_id()
        self.task_list.clear()
        query = self.search_input.text().strip().casefold()
        for task in self.tasks:
            if query not in task.title.casefold():
                continue
            mark = "已完成" if task.done else "未完成"
            item = QListWidgetItem(f"[{mark}] [{task.priority}] {task.title}")
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            self.task_list.addItem(item)
            if task.id == selected_id:
                self.task_list.setCurrentItem(item)
        self._update_selection()
        name = self.current_path.name if self.current_path else "未命名"
        self.setWindowTitle(f"{'*' if self.dirty else ''}{name} — 桌面任务管理器")
        done = sum(task.done for task in self.tasks)
        self.statusBar().showMessage(
            f"共 {len(self.tasks)} 项，完成 {done} 项，当前显示 {self.task_list.count()} 项"
        )

    def _update_selection(self) -> None:
        enabled = self._selected_id() is not None
        self.toggle_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)

    def add_task(self) -> None:
        try:
            if len(self.tasks) >= self.repository.MAX_TASKS:
                raise ValueError("任务数量已达教学版上限 10000。")
            task = Task.create(self.title_input.text(), self.priority_input.currentText())
        except ValueError as exc:
            QMessageBox.warning(self, "无法添加", str(exc))
            return
        self.tasks.append(task)
        self.dirty = True
        self.title_input.clear()
        self._refresh()
        self.title_input.setFocus()

    def toggle_task(self) -> None:
        task_id = self._selected_id()
        if task_id is None:
            return
        self.tasks = [task.toggled() if task.id == task_id else task for task in self.tasks]
        self.dirty = True
        self._refresh()

    def delete_task(self) -> None:
        task_id = self._selected_id()
        if task_id is None:
            return
        answer = QMessageBox.question(
            self, "删除任务", "确定删除选中的任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.tasks = [task for task in self.tasks if task.id != task_id]
        self.dirty = True
        self._refresh()

    def _allow_discard(self) -> bool:
        if not self.dirty:
            return True
        answer = QMessageBox.question(
            self, "尚未保存", "当前内容已修改，是否先保存？",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.save_document()
        return answer == QMessageBox.StandardButton.Discard

    def new_document(self) -> None:
        if not self._allow_discard():
            return
        self.tasks = []
        self.current_path = None
        self.dirty = False
        self.search_input.clear()
        self._refresh()

    def open_document(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "打开任务文件", "", "JSON 文件 (*.json)")
        if not filename:
            return
        candidate = Path(filename)
        # 先校验文件。读取失败时不弹“放弃修改”，也不丢掉当前内容。
        try:
            loaded = self.repository.load(candidate)
        except (OSError, ValueError, UnicodeError) as exc:
            QMessageBox.critical(self, "打开失败", str(exc))
            return
        if not self._allow_discard():
            return
        # “先保存”可能刚写入同一文件，因此重新读取，避免使用过期快照。
        try:
            loaded = self.repository.load(candidate)
        except (OSError, ValueError, UnicodeError) as exc:
            QMessageBox.critical(self, "打开失败", str(exc))
            return
        self.tasks = loaded
        self.current_path = candidate
        self.dirty = False
        self.search_input.clear()
        self._refresh()

    def save_document(self, checked: bool = False, *, save_as: bool = False) -> bool:
        path = self.current_path
        if path is None or save_as:
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存任务文件", str(path or "任务清单.json"), "JSON 文件 (*.json)"
            )
            if not filename:
                return False
            path = Path(filename)
            # 保留对话框最终选中的路径，不在覆盖确认后偷偷改目标文件名。
        try:
            self.repository.save(path, self.tasks)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "保存失败", str(exc))
            return False
        self.current_path = path
        self.dirty = False
        self._refresh()
        self.statusBar().showMessage(f"已保存到 {path}", 5000)
        return True

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_discard():
            event.accept()
        else:
            event.ignore()
