"""纯 Python 数据规则：此文件不依赖 PyQt6。"""

from dataclasses import dataclass, replace
from uuid import uuid4


PRIORITIES = ("低", "中", "高")


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    priority: str = "中"
    done: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("任务编号必须是非空字符串。")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("任务名称不能为空。")
        if self.title != self.title.strip() or len(self.title) > 80:
            raise ValueError("任务名称不能有首尾空白，且最多为 80 个字符。")
        if self.priority not in PRIORITIES:
            raise ValueError("优先级必须为低、中或高。")
        if type(self.done) is not bool:
            raise ValueError("完成状态必须是布尔值。")

    @classmethod
    def create(cls, title: str, priority: str = "中") -> "Task":
        return cls(id=uuid4().hex, title=title.strip(), priority=priority)

    def toggled(self) -> "Task":
        return replace(self, done=not self.done)

