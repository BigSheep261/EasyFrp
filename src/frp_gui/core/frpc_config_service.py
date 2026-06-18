"""frpc TOML 配置文件读写服务。

UI 层不应该直接关心文件路径、读写异常和 TOML 解析细节。
这个 service 把配置文件业务集中起来，让 page 和 panel 专心负责界面。
"""

from pathlib import Path

import tomlkit
from tomlkit.exceptions import TOMLKitError

from frp_gui.core.paths import CONFIG_DIR


class FrpcConfigService:
    """读取、校验并保存 ``config/frpc.toml``。

    第一版先把整个 TOML 当作文本编辑。
    这样比字段化表单更简单，也不会因为 frpc 配置项很多而漏掉某些 proxy 类型。
    """

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or CONFIG_DIR / "frpc.toml"

    def load_text(self) -> str:
        """从磁盘读取当前 TOML 文本。

        Windows 的系统默认编码不一定是 UTF-8，所以这里显式指定编码，
        避免中文注释或后续中文配置内容被错误读取。
        """
        if not self.config_path.exists():
            return ""
        return self.config_path.read_text(encoding="utf-8")

    def validate_text(self, text: str) -> tuple[bool, str]:
        """只校验 TOML 语法，不写入磁盘。

        入门级代码里先使用简单的返回值：
        ``(True, "")`` 表示校验通过，``(False, message)`` 表示校验失败。
        """
        try:
            tomlkit.parse(text)
        except TOMLKitError as error:
            return False, str(error)
        return True, ""

    def save_text(self, text: str) -> tuple[bool, str]:
        """先校验，再把 TOML 文本写回原配置文件。"""
        is_valid, error_message = self.validate_text(text)
        if not is_valid:
            return False, error_message

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(text, encoding="utf-8")
        return True, ""
