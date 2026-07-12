"""P2P 配置档案角色的兼容导出定义。"""

# 角色枚举的实际定义与代理类型位于同一模块，此处保留历史导入路径。
from frp_gui.backend.models.frpc.proxy_type import FrpcProxyRole


# 使用别名表达“配置档案角色”这一业务名称，且不创建新的枚举类型。
FrpcProfileRole = FrpcProxyRole


# 同时公开新旧名称，兼容现有调用方。
__all__ = ["FrpcProfileRole", "FrpcProxyRole"]
