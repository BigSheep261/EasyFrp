"""运行：python docs/Book/示例代码/第五课_模型表格.py"""

import sys
from dataclasses import dataclass

from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)


@dataclass
class Task:
    title: str
    priority: int = 3
    completed: bool = False


class TaskModel(QAbstractTableModel):
    HEADERS = ("任务名称", "优先级（1—5）", "已完成")

    def __init__(self, tasks: list[Task], parent=None):
        super().__init__(parent)
        self._tasks = list(tasks)

    def rowCount(self, parent=QModelIndex()):
        # 这是平面表格：一个单元格下面没有子行。
        return 0 if parent.isValid() else len(self._tasks)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        task = self._tasks[index.row()]
        values = (task.title, task.priority, task.completed)

        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()] if index.column() != 2 else ""
        if role == Qt.ItemDataRole.EditRole:
            return values[index.column()]
        if role == Qt.ItemDataRole.UserRole:
            # 供代理排序，保持数字和布尔值的原始类型。
            return values[index.column()]
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == 2:
            return Qt.CheckState.Checked if task.completed else Qt.CheckState.Unchecked
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return section + 1

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        common = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 2:
            return common | Qt.ItemFlag.ItemIsUserCheckable
        return common | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        task = self._tasks[index.row()]
        column = index.column()
        if role == Qt.ItemDataRole.EditRole and column == 0:
            title = str(value).strip()
            if not title:
                return False
            task.title = title
        elif role == Qt.ItemDataRole.EditRole and column == 1:
            # 验证不能只放在界面里；其他调用者也可能直接调用模型。
            if isinstance(value, bool):
                return False
            if isinstance(value, int):
                priority = value
            elif isinstance(value, str):
                try:
                    priority = int(value)
                except ValueError:
                    return False
            else:
                return False
            if not 1 <= priority <= 5:
                return False
            task.priority = priority
        elif role == Qt.ItemDataRole.CheckStateRole and column == 2:
            checked = (Qt.CheckState.Checked, Qt.CheckState.Checked.value)
            unchecked = (Qt.CheckState.Unchecked, Qt.CheckState.Unchecked.value)
            if value not in checked + unchecked:
                return False
            task.completed = value in checked
        else:
            return False

        self.dataChanged.emit(
            index,
            index,
            [
                Qt.ItemDataRole.DisplayRole,
                Qt.ItemDataRole.EditRole,
                Qt.ItemDataRole.CheckStateRole,
                Qt.ItemDataRole.UserRole,
            ],
        )
        return True

    def add_task(self, title: str) -> bool:
        title = title.strip()
        if not title:
            return False
        row = len(self._tasks)
        self.beginInsertRows(QModelIndex(), row, row)
        self._tasks.append(Task(title))
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        if parent.isValid() or row < 0 or count <= 0 or row + count > len(self._tasks):
            return False
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        del self._tasks[row : row + count]
        self.endRemoveRows()
        return True


class PriorityDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setRange(1, 5)
        return editor

    def setEditorData(self, editor, index):
        editor.setValue(int(index.data(Qt.ItemDataRole.EditRole)))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value(), Qt.ItemDataRole.EditRole)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("第五课：模型、代理与委托")
        self.resize(760, 430)
        self.model = TaskModel(
            [Task("学习信号与槽", 2, True), Task("完成模型练习", 4), Task("整理笔记", 1)],
            self,
        )
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.proxy.setDynamicSortFilter(True)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setItemDelegateForColumn(1, PriorityDelegate(self.table))
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.resizeColumnsToContents()

        add_button = QPushButton("添加任务")
        delete_button = QPushButton("删除选中任务")
        add_button.clicked.connect(self.add_task)
        delete_button.clicked.connect(self.delete_selected)
        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(delete_button)
        buttons.addStretch()

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("双击编辑；单击表头排序；按 Ctrl 或 Shift 选择多行。"))
        layout.addWidget(self.table)
        layout.addLayout(buttons)
        self.setCentralWidget(central)

    def add_task(self):
        title, accepted = QInputDialog.getText(self, "添加任务", "任务名称：")
        if accepted and not self.model.add_task(title):
            self.statusBar().showMessage("名称不能为空", 3000)

    def delete_selected(self):
        # 当前视图使用代理，选中的是代理索引，不能直接用它的 row() 删除源数据。
        selected = self.table.selectionModel().selectedRows()
        source_rows = {
            self.proxy.mapToSource(index).row()
            for index in selected
            if index.isValid()
        }
        # 先收集所有源行号，再从后往前删，避免前面的删除改变后面的行号。
        for row in sorted(source_rows, reverse=True):
            self.model.removeRows(row, 1)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
