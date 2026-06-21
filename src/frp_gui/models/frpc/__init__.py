"""结构化 frpc 配置模型。"""

from frp_gui.models.frpc.global_config import FrpcGlobalConfig, FrpcLogConfig
from frp_gui.models.frpc.proxy_type import FrpcProxyType
from frp_gui.models.frpc.tcp_proxy_config import TcpProxyConfig
from frp_gui.models.frpc.udp_proxy_config import UdpProxyConfig


__all__ = [
    "FrpcGlobalConfig",
    "FrpcLogConfig",
    "FrpcProxyType",
    "TcpProxyConfig",
    "UdpProxyConfig",
]
