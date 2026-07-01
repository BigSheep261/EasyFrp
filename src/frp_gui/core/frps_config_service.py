"""frps TOML 配置文件读写服务。"""

from pathlib import Path

import tomlkit
from tomlkit.exceptions import TOMLKitError

from frp_gui.core.paths import CONFIG_DIR
from frp_gui.utils import LocalFileUtils


class FrpsConfigService:
    """读取、校验并保存 ``config/frps.toml``。"""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or CONFIG_DIR / "frps.toml"

    def load_text(self) -> str:
        """从磁盘读取当前 TOML 文本。"""
        return LocalFileUtils.read_text(self.config_path, default="")

    def validate_text(self, text: str) -> tuple[bool, str]:
        """只校验 TOML 语法，不写入磁盘。"""
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

        LocalFileUtils.write_text(self.config_path, text)
        return True, ""
