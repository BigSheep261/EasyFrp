"""纯 Python 测试，无需启动图形界面，只使用临时目录。"""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from 任务仓库 import TaskRepository
from 任务数据 import Task


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "任务.json"
        self.repository = TaskRepository()

    def write_raw(self, data) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_round_trip_preserves_chinese_and_done(self) -> None:
        tasks = [Task.create("学习信号", "高"), Task.create("练习保存").toggled()]
        self.repository.save(self.path, tasks)
        self.assertEqual(self.repository.load(self.path), tasks)

    def test_empty_list_is_valid(self) -> None:
        self.repository.save(self.path, [])
        self.assertEqual(self.repository.load(self.path), [])

    def test_blank_title_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Task.create("   ")

    def test_long_title_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Task.create("长" * 81)

    def test_missing_file_is_not_silently_empty(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.repository.load(self.path)

    def test_invalid_json_is_reported(self) -> None:
        self.path.write_text("{坏掉的文件", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.repository.load(self.path)

    def test_unsupported_version_is_rejected(self) -> None:
        self.write_raw({"version": 2, "tasks": []})
        with self.assertRaises(ValueError):
            self.repository.load(self.path)

    def test_excessive_nesting_becomes_a_format_error(self) -> None:
        self.path.write_text("[" * 5000 + "0" + "]" * 5000, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "嵌套过深"):
            self.repository.load(self.path)

    def test_boolean_version_is_rejected(self) -> None:
        self.write_raw({"version": True, "tasks": []})
        with self.assertRaises(ValueError):
            self.repository.load(self.path)

    def test_wrong_done_type_is_rejected(self) -> None:
        self.write_raw({"version": 1, "tasks": [
            {"id": "1", "title": "测试", "priority": "中", "done": "false"},
        ]})
        with self.assertRaises(ValueError):
            self.repository.load(self.path)

    def test_missing_field_is_rejected(self) -> None:
        self.write_raw({"version": 1, "tasks": [{"id": "1", "title": "测试"}]})
        with self.assertRaises(ValueError):
            self.repository.load(self.path)

    def test_duplicate_ids_are_rejected(self) -> None:
        item = {"id": "1", "title": "测试", "priority": "中", "done": False}
        self.write_raw({"version": 1, "tasks": [item, item]})
        with self.assertRaises(ValueError):
            self.repository.load(self.path)

    def test_failed_replace_keeps_old_file_and_cleans_temp(self) -> None:
        old = [Task.create("原任务")]
        self.repository.save(self.path, old)
        before = self.path.read_bytes()
        with patch("任务仓库.os.replace", side_effect=PermissionError("模拟无权限")):
            with self.assertRaises(PermissionError):
                self.repository.save(self.path, [Task.create("新任务")])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


if __name__ == "__main__":
    unittest.main(verbosity=2)
