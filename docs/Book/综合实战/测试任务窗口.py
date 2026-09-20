"""关键交互测试：QTest 触发点击，用 mock 代替需要人工选择的对话框。"""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox

from 任务数据 import Task
from 任务窗口 import TaskWindow


class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "测试任务.json"
        self.window = TaskWindow()
        self.window.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.window.dirty = False
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def add(self, title: str) -> None:
        self.window.title_input.setText(title)
        QTest.mouseClick(self.window.add_button, Qt.MouseButton.LeftButton)

    def test_click_add_and_mark_dirty(self) -> None:
        self.add("  学习布局  ")
        self.assertEqual(self.window.tasks[0].title, "学习布局")
        self.assertEqual(self.window.task_list.count(), 1)
        self.assertTrue(self.window.dirty)
        self.assertEqual(self.window.title_input.text(), "")

    def test_blank_input_keeps_data(self) -> None:
        with patch("任务窗口.QMessageBox.warning") as warning:
            self.add("   ")
        warning.assert_called_once()
        self.assertEqual(self.window.tasks, [])
        self.assertFalse(self.window.dirty)

    def test_filter_then_toggle_and_delete_uses_identity(self) -> None:
        self.add("保留的任务")
        self.add("目标任务")
        kept_id = self.window.tasks[0].id
        self.window.search_input.setText("目标")
        self.window.task_list.setCurrentRow(0)
        QTest.mouseClick(self.window.toggle_button, Qt.MouseButton.LeftButton)
        self.assertFalse(self.window.tasks[0].done)
        self.assertTrue(self.window.tasks[1].done)
        with patch("任务窗口.QMessageBox.question", return_value=QMessageBox.StandardButton.Yes):
            QTest.mouseClick(self.window.delete_button, Qt.MouseButton.LeftButton)
        self.assertEqual([task.id for task in self.window.tasks], [kept_id])
        self.assertEqual(self.window.task_list.count(), 0)

    def test_save_cancel_preserves_dirty(self) -> None:
        self.add("不要丢失")
        with patch("任务窗口.QFileDialog.getSaveFileName", return_value=("", "")):
            self.assertFalse(self.window.save_document())
        self.assertTrue(self.window.dirty)
        self.assertIsNone(self.window.current_path)

    def test_unselect_current_item_disables_actions(self) -> None:
        self.add("取消选中的任务")
        item = self.window.task_list.item(0)
        point = self.window.task_list.visualItemRect(item).center()
        QTest.mouseClick(self.window.task_list.viewport(), Qt.MouseButton.LeftButton, pos=point)
        self.assertTrue(self.window.toggle_button.isEnabled())
        QTest.mouseClick(
            self.window.task_list.viewport(), Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.ControlModifier, pos=point,
        )
        self.assertEqual(self.window.task_list.selectedItems(), [])
        self.assertIsNone(self.window._selected_id())
        self.assertFalse(self.window.toggle_button.isEnabled())
        self.assertFalse(self.window.delete_button.isEnabled())

    def test_save_then_reopen_round_trip(self) -> None:
        self.add("保存我")
        with patch("任务窗口.QFileDialog.getSaveFileName", return_value=(str(self.path), "")):
            # 使用 QAction 路径，覆盖 triggered 的参数适配。
            self.window.save_as_action.trigger()
        self.assertFalse(self.window.dirty)
        self.window.new_document()
        with patch("任务窗口.QFileDialog.getOpenFileName", return_value=(str(self.path), "")):
            self.window.open_document()
        self.assertEqual(self.window.tasks[0].title, "保存我")
        self.assertEqual(self.window.current_path, self.path)

    def test_bad_file_keeps_document(self) -> None:
        self.add("当前数据")
        previous = list(self.window.tasks)
        self.path.write_text("not json", encoding="utf-8")
        with patch("任务窗口.QFileDialog.getOpenFileName", return_value=(str(self.path), "")), \
             patch("任务窗口.QMessageBox.critical") as critical:
            self.window.open_document()
        critical.assert_called_once()
        self.assertEqual(self.window.tasks, previous)
        self.assertTrue(self.window.dirty)
        self.assertIsNone(self.window.current_path)

    def test_cancel_close_keeps_window(self) -> None:
        self.add("尚未保存")
        with patch("任务窗口.QMessageBox.question", return_value=QMessageBox.StandardButton.Cancel):
            self.assertFalse(self.window.close())
        self.assertTrue(self.window.isVisible())
        self.assertTrue(self.window.dirty)

    def test_failed_save_prevents_close(self) -> None:
        self.add("保存会失败")
        self.window.current_path = self.path
        with patch("任务窗口.QMessageBox.question", return_value=QMessageBox.StandardButton.Save), \
             patch.object(self.window.repository, "save", side_effect=PermissionError("模拟无权限")), \
             patch("任务窗口.QMessageBox.critical"):
            self.assertFalse(self.window.close())
        self.assertTrue(self.window.isVisible())
        self.assertTrue(self.window.dirty)

    def test_open_same_path_after_save_uses_latest_data(self) -> None:
        self.window.repository.save(self.path, [Task.create("旧记录")])
        self.window.current_path = self.path
        self.add("新记录")
        with patch("任务窗口.QFileDialog.getOpenFileName", return_value=(str(self.path), "")), \
             patch("任务窗口.QMessageBox.question", return_value=QMessageBox.StandardButton.Save):
            self.window.open_document()
        self.assertEqual([task.title for task in self.window.tasks], ["新记录"])
        self.assertFalse(self.window.dirty)


if __name__ == "__main__":
    unittest.main(verbosity=2)
