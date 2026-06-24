"""Utilities for local file reads and writes."""

from pathlib import Path
import json
from typing import Any


class LocalFileUtils:
    """Local file IO helpers shared by core services."""

    DEFAULT_ENCODING = "utf-8"

    @staticmethod
    def read_text(path: Path,*,encoding: str = DEFAULT_ENCODING,default: str | None = None) -> str:
        if not path.exists():
            if default is not None:
                return default
            raise FileNotFoundError(path)
        return path.read_text(encoding=encoding)

    @staticmethod
    def write_text(path: Path,text: str,*,encoding: str = DEFAULT_ENCODING) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding=encoding)

    @staticmethod
    def read_json(path: Path,*,encoding: str = DEFAULT_ENCODING) -> Any:
        return json.loads(LocalFileUtils.read_text(path, encoding=encoding))

    @staticmethod
    def write_json(path: Path,data: Any,*,encoding: str = DEFAULT_ENCODING,ensure_ascii: bool = False,indent: int | None = 2,trailing_newline: bool = True,) -> None:
        text = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
        if trailing_newline:
            text = f"{text}\n"
        LocalFileUtils.write_text(path, text, encoding=encoding)

    @staticmethod
    def list_file_stems(directory: Path, pattern: str) -> list[str]:
        if not directory.exists():
            return []
        return sorted(path.stem for path in directory.glob(pattern) if path.is_file())
