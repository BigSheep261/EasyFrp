"""EasyFrp 应用自身设置的 JSON 读写服务。"""

# 路径对象支持将设置服务指向测试文件或其他自定义位置。
from pathlib import Path
# Any 用于描述尚未经过格式归一化的 JSON 字段值。
from typing import Any

# 默认配置目录和统一 JSON 文件工具由基础设施层提供。
from frp_gui.utils.paths import CONFIG_DIR
from frp_gui.utils import LocalFileUtils

# 默认值覆盖应用启动所需的全部设置项，新建或缺项配置都会以此补齐。
DEFAULT_EASYFRP_SETTINGS: dict[str, str | bool] = {
    "client_mode": "frpc",
    "launch_at_start": False,
    "auto_run": False,
}

# 客户端模式只允许在 frpc 客户端和 frps 服务端之间选择。
VALID_CLIENT_MODES = {"frpc", "frps"}


class SettingsService:
    """读取、补全并保存 ``config/config.json``。"""

    def __init__(self, config_path: Path | None = None) -> None:
        """初始化服务，并允许覆盖应用设置文件的默认路径。"""
        # 未传入路径时使用项目配置目录中的 config.json。
        self.config_path = config_path or CONFIG_DIR / "config.json"

    def load_settings(self) -> dict[str, str | bool]:
        """读取设置；文件缺失或为空时写入默认设置。"""
        # 首次启动或空文件都没有可用设置，此时创建并持久化一份完整默认值。
        if not self.config_path.exists() or self.config_path.stat().st_size == 0:
            settings = self.default_settings()
            self.save_settings(settings)
            return settings

        # 使用统一文件工具解析 JSON，并先确认根节点符合设置对象结构。
        data = LocalFileUtils.read_json(self.config_path)
        # 数组、标量等根节点无法按设置键值处理，因此立即拒绝。
        if not isinstance(data, dict):
            raise ValueError("EasyFrp 配置文件根节点必须是对象。")

        # 归一化旧配置或非法字段；内容被修正时同步回写，完成配置迁移。
        settings = self._normalize_settings(data)
        # 只在归一化结果发生变化时回写，避免每次读取都重写文件。
        if settings != data:
            self.save_settings(settings)
        # 始终向调用方返回字段完整、类型稳定的设置字典。
        return settings

    def save_settings(self, settings: dict[str, str | bool]) -> None:
        """保存设置到 JSON 文件。"""
        # 写入前再次归一化，保证外部传入的字典也不会破坏持久化格式。
        LocalFileUtils.write_json(
            self.config_path,
            self._normalize_settings(settings),
        )

    def default_settings(self) -> dict[str, str | bool]:
        """返回一份可修改的默认设置副本。"""
        # 返回浅拷贝，防止调用方修改模块级默认值对象。
        return dict(DEFAULT_EASYFRP_SETTINGS)

    def _normalize_settings(self, data: dict[str, Any]) -> dict[str, str | bool]:
        """筛选并规范原始设置，只保留受支持且类型正确的字段。"""
        # 先以完整默认值为基线，再用经过校验的输入字段逐项覆盖。
        settings = self.default_settings()

        # 模式字段必须是字符串，并在去除首尾空白后属于允许集合。
        client_mode = data.get("client_mode")
        # 非字符串值不参与模式解析，保留默认的 frpc 模式。
        if isinstance(client_mode, str):
            normalized_mode = client_mode.strip()
            # 只有明确列入允许集合的模式才能覆盖默认值。
            if normalized_mode in VALID_CLIENT_MODES:
                settings["client_mode"] = normalized_mode

        # 布尔开关通过统一转换函数处理，非布尔输入一律回退为 False。
        settings["launch_at_start"] = self._as_bool(data.get("launch_at_start"))
        settings["auto_run"] = self._as_bool(data.get("auto_run"))
        # 返回仅包含已知设置项的规范字典，顺便移除未知的遗留字段。
        return settings

    def _as_bool(self, value: Any) -> bool:
        """仅接受真正的布尔值，其他 JSON 值统一转换为 ``False``。"""
        # 不使用 bool(value)，避免字符串或非零数字被误判为已启用。
        return value if isinstance(value, bool) else False


# 保留旧服务名作为兼容别名，使已有导入无需立即迁移。
EasyfrpConfigService = SettingsService
