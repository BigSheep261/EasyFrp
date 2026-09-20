"""只读检查本书源码语法、中文文件名和 Markdown 本地文件链接。"""

import ast
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import warnings


BOOK = Path(__file__).resolve().parents[1]


def main() -> int:
    errors = []
    sources = sorted(BOOK.rglob("*.py"))
    documents = sorted(BOOK.rglob("*.md"))
    sources = [path for path in sources if ".venv" not in path.parts]
    documents = [path for path in documents if ".venv" not in path.parts]
    for path in sources:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeError, Warning) as exc:
            errors.append(f"源码解析失败：{path.relative_to(BOOK)}：{exc}")
    link_count = 0
    for path in documents:
        content = path.read_text(encoding="utf-8")
        # 本书使用行内 Markdown 链接；跳过代码围栏以免把代码当成链接。
        prose = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", prose):
            target = target.strip().strip("<>")
            if urlsplit(target).scheme or target.startswith("#"):
                continue
            local = unquote(target.split("#", 1)[0])
            if local:
                link_count += 1
                if not (path.parent / local).resolve().exists():
                    errors.append(f"本地链接不存在：{path.relative_to(BOOK)} → {target}")
    for path in sources + documents:
        if not re.search(r"[\u4e00-\u9fff]", path.stem):
            errors.append(f"文件名缺少中文：{path.relative_to(BOOK)}")
    for error in errors:
        print(error)
    print(f"检查 {len(sources)} 个 Python 文件，{len(documents)} 个 Markdown 文件，"
          f"{link_count} 个本地链接；问题数：{len(errors)}")
    print("此检查不验证外部网站、标题锚点、代码片段运行结果或真实桌面交互。")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
