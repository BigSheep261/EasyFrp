"""封装本地文本和 JSON 文件读写的通用工具。"""

# 使用面向对象路径接口，统一处理文件存在性和编码读写。
from pathlib import Path
# 调用标准 JSON 编解码器，保持配置格式的通用兼容性。
import json
# ``Any`` 用于表示 JSON 可接受的任意嵌套数据结构。
from typing import Any


class LocalFileUtils:
    """供各核心服务复用的无状态本地文件读写工具。"""

    # 所有方法默认使用 UTF-8，避免不同操作系统默认编码造成乱码。
    DEFAULT_ENCODING = "utf-8"

    @staticmethod
    def read_text(
        path: Path,
        *,
        encoding: str = DEFAULT_ENCODING,
        default: str | None = None,
    ) -> str:
        """读取文本文件，必要时为缺失文件提供默认内容。

        Args:
            path: 待读取的文件路径。
            encoding: 文本编码，默认统一为 UTF-8。
            default: 文件不存在时返回的备用文本；省略则抛出异常。

        Returns:
            文件中的完整文本，或调用方指定的默认文本。

        Raises:
            FileNotFoundError: 文件不存在且未提供 ``default`` 时抛出。
        """
        # 先显式处理缺失文件，以便区分“返回默认值”和“读取空文件”。
        if not path.exists():
            # 调用方提供默认内容时，将缺失视为可恢复状态。
            if default is not None:
                # 直接返回备用文本，不在磁盘上创建任何文件。
                return default
            # 保留缺失路径作为异常参数，方便上层定位问题文件。
            raise FileNotFoundError(path)
        # 文件存在时使用指定编码一次性读取全部内容。
        return path.read_text(encoding=encoding)

    @staticmethod
    def write_text(
        path: Path,
        text: str,
        *,
        encoding: str = DEFAULT_ENCODING,
    ) -> None:
        """将完整文本写入文件，并自动创建缺失的父目录。

        Args:
            path: 目标文件路径。
            text: 需要覆盖写入的完整文本。
            encoding: 写入时使用的字符编码。
        """
        # 确保目标目录存在，使首次保存嵌套配置时无需额外准备目录。
        path.parent.mkdir(parents=True, exist_ok=True)
        # 使用明确编码覆盖写入目标文件。
        path.write_text(text, encoding=encoding)

    @staticmethod
    def read_json(
        path: Path,
        *,
        encoding: str = DEFAULT_ENCODING,
    ) -> Any:
        """读取并解析 JSON 文件。

        Args:
            path: JSON 文件路径。
            encoding: 读取源文本时使用的字符编码。

        Returns:
            由 JSON 文档解析得到的 Python 数据结构。
        """
        # 复用文本读取逻辑后交给标准库完成严格的 JSON 解析。
        return json.loads(LocalFileUtils.read_text(path, encoding=encoding))

    @staticmethod
    def write_json(
        path: Path,
        data: Any,
        *,
        encoding: str = DEFAULT_ENCODING,
        ensure_ascii: bool = False,
        indent: int | None = 2,
        trailing_newline: bool = True,
    ) -> None:
        """将 Python 数据序列化为 JSON 并写入文件。

        Args:
            path: 目标 JSON 文件路径。
            data: 可由标准 JSON 编码器序列化的数据。
            encoding: 输出文件使用的字符编码。
            ensure_ascii: 是否把非 ASCII 字符转义为 Unicode 序列。
            indent: 缩进空格数；为 ``None`` 时输出紧凑格式。
            trailing_newline: 是否在文档末尾保留换行，便于版本控制查看。
        """
        # 按调用方指定的字符和缩进策略生成 JSON 文本。
        text = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
        # 文本配置通常保留末尾换行，但调用方可为特殊协议关闭它。
        if trailing_newline:
            # 统一只追加一个由本方法管理的行结束符。
            text = f"{text}\n"
        # 复用文本写入逻辑，自动创建父目录并应用指定编码。
        LocalFileUtils.write_text(path, text, encoding=encoding)

    @staticmethod
    def list_file_stems(directory: Path, pattern: str) -> list[str]:
        """列出目录中匹配文件的名称主干。

        Args:
            directory: 要搜索的目录。
            pattern: 交给 ``Path.glob`` 的匹配模式。

        Returns:
            按名称排序且不含扩展名的文件列表；目录不存在时返回空列表。
        """
        # 缺失目录表示尚无可用档案，按正常空结果处理。
        if not directory.exists():
            # 返回新列表，避免调用方额外捕获文件系统异常。
            return []
        # 过滤掉同名目录，仅返回匹配文件的主干并确保结果稳定排序。
        return sorted(path.stem for path in directory.glob(pattern) if path.is_file())
