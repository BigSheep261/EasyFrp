"""EasyFrp 应用设置后端服务的公开入口。"""

# 从具体实现模块重导出设置服务，供调用方通过包路径统一导入。
from frp_gui.backend.settings.settings_service import SettingsService

# 明确该子包承诺公开的服务类型，避免内部实现被意外依赖。
__all__ = ["SettingsService"]

