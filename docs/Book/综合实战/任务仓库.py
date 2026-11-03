"""JSON 仓库：校验全部内容之后才返回；先写临时文件，再替换目标。"""

from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile

from 任务数据 import Task


class TaskRepository:
    MAX_TASKS = 10_000

    def load(self, path: Path) -> list[Task]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except RecursionError as exc:
            # 将解析器的深度限制翻译成界面能统一处理的数据格式错误。
            raise ValueError("JSON 嵌套过深，无法作为任务文件读取。") from exc
        if not isinstance(raw, dict):
            raise ValueError("文件最外层必须是对象。")
        if type(raw.get("version")) is not int or raw["version"] != 1:
            raise ValueError("不支持此文件版本，需要 version = 1。")
        records = raw.get("tasks")
        if not isinstance(records, list) or len(records) > self.MAX_TASKS:
            raise ValueError("tasks 必须是列表，且最多包含 10000 条任务。")

        tasks = []
        seen = set()
        for row, item in enumerate(records, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"第 {row} 条任务必须是对象。")
            if set(item) != {"id", "title", "priority", "done"}:
                raise ValueError(f"第 {row} 条任务的字段不完整或含未知字段。")
            task = Task(**item)
            if task.id in seen:
                raise ValueError(f"第 {row} 条任务编号重复。")
            seen.add(task.id)
            tasks.append(task)
        return tasks

    def save(self, path: Path, tasks: list[Task]) -> None:
        if len(tasks) > self.MAX_TASKS:
            raise ValueError("最多保存 10000 条任务。")
        if len({task.id for task in tasks}) != len(tasks):
            raise ValueError("任务编号不能重复。")
        content = json.dumps(
            {"version": 1, "tasks": [asdict(task) for task in tasks]},
            ensure_ascii=False,
            indent=2,
        )
        temp_path = None
        try:
            # 同一目录通常保证位于同一文件系统，避免跨盘替换。
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            # Windows 上必须先关闭临时文件，再执行替换。
            os.replace(temp_path, path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
