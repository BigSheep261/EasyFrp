"""EasyFrp 应用自身设置的 JSON 读写服务。"""

from pathlib import Path
from typing import Any

from frp_gui.core.paths import CONFIG_DIR
from frp_gui.utils import LocalFileUtils

DEFAULT_EASYFRP_SETTINGS: dict[str, str | bool] = {
    "theme_key": "ops_dark",
    "client_mode": "frpc",
    "launch_at_start": False,
    "auto_run": False,
}

VALID_CLIENT_MODES = {"frpc", "frps"}


class EasyfrpConfigService:
    """读取、补全并保存 ``config/config.json``。"""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or CONFIG_DIR / "config.json"

    def load_settings(self) -> dict[str, str | bool]:
        """读取设置；文件缺失或为空时写入默认设置。"""
        if not self.config_path.exists() or self.config_path.stat().st_size == 0:
            settings = self.default_settings()
            self.save_settings(settings)
            return settings

        data = LocalFileUtils.read_json(self.config_path)
        if not isinstance(data, dict):
            raise ValueError("EasyFrp 配置文件根节点必须是对象。")

        settings = self._normalize_settings(data)
        if settings != data:
            self.save_settings(settings)
        return settings

    def save_settings(self, settings: dict[str, str | bool]) -> None:
        """保存设置到 JSON 文件。"""
        LocalFileUtils.write_json(
            self.config_path,
            self._normalize_settings(settings),
        )

    def default_settings(self) -> dict[str, str | bool]:
        """返回一份可修改的默认设置副本。"""
        return dict(DEFAULT_EASYFRP_SETTINGS)

    def _normalize_settings(self, data: dict[str, Any]) -> dict[str, str | bool]:
        settings = self.default_settings()

        theme_key = data.get("theme_key")
        if isinstance(theme_key, str) and theme_key.strip():
            settings["theme_key"] = theme_key.strip()

        client_mode = data.get("client_mode")
        if isinstance(client_mode, str):
            normalized_mode = client_mode.strip()
            if normalized_mode in VALID_CLIENT_MODES:
                settings["client_mode"] = normalized_mode

        settings["launch_at_start"] = self._as_bool(data.get("launch_at_start"))
        settings["auto_run"] = self._as_bool(data.get("auto_run"))
        return settings

    def _as_bool(self, value: Any) -> bool:
        return value if isinstance(value, bool) else False
