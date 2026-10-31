"""EasyFrp 应用自身设置的 JSON 读写服务。"""

# 路径对象支持将设置服务指向测试文件或其他自定义位置。
from pathlib import Path

# 默认配置目录、共用默认设置和 JSON 文件工具由基础设施层提供。
from frp_gui.utils.paths import CONFIG_DIR, DEFAULT_EASYFRP_SETTINGS
from frp_gui.utils import LocalFileUtils


class SettingsService:
    """直接读取和保存 ``config/config.json``。"""

    def __init__(self, config_path: Path | None = None) -> None:
        """初始化服务，并允许覆盖应用设置文件的默认路径。"""
        # 未传入路径时使用项目配置目录中的 config.json。
        self.config_path = config_path or CONFIG_DIR / "config.json"

    def load_settings(self) -> dict[str, str | bool]:
        """读取已由启动流程创建的设置，不补全字段或回写文件。"""
        # 使用统一文件工具解析 JSON，并先确认根节点符合设置对象结构。
        data = LocalFileUtils.read_json(self.config_path)
        # 数组、标量等根节点无法按设置键值处理，因此立即拒绝。
        if not isinstance(data, dict):
            raise ValueError("EasyFrp 配置文件根节点必须是对象。")

        # 原样返回文件中的设置，字段内容由界面保存流程负责。
        return data

    def save_settings(self, settings: dict[str, str | bool]) -> None:
        """保存设置到 JSON 文件。"""
        # 直接保存界面提交的数据，不补全、筛选或转换字段。
        LocalFileUtils.write_json(self.config_path, settings)

    def default_settings(self) -> dict[str, str | bool]:
        """返回一份可修改的默认设置副本。"""
        # 返回浅拷贝，防止调用方修改模块级默认值对象。
        return dict(DEFAULT_EASYFRP_SETTINGS)


# 保留旧服务名作为兼容别名，使已有导入无需立即迁移。
EasyfrpConfigService = SettingsService
