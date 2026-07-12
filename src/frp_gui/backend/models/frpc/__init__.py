"""结构化 frpc 配置模型。"""

# 从各实现模块重导出全局配置、代理配置以及分类枚举。
from frp_gui.backend.models.frpc.global_config import FrpcGlobalConfig, FrpcLogConfig
from frp_gui.backend.models.frpc.p2p_proxy_config import P2PProxyConfig
from frp_gui.backend.models.frpc.p2p_visitors_config import P2PVisitorsConfig
from frp_gui.backend.models.frpc.profile_role import FrpcProfileRole, FrpcProxyRole
from frp_gui.backend.models.frpc.proxy_type import FrpcProxyType
from frp_gui.backend.models.frpc.tcp_proxy_config import TcpProxyConfig
from frp_gui.backend.models.frpc.udp_proxy_config import UdpProxyConfig


# 明确结构化配置模型包的稳定公开接口。
__all__ = [
    "FrpcGlobalConfig",
    "FrpcLogConfig",
    "FrpcProfileRole",
    "FrpcProxyRole",
    "FrpcProxyType",
    "P2PProxyConfig",
    "P2PVisitorsConfig",
    "TcpProxyConfig",
    "UdpProxyConfig",
]
