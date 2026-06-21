"""frpc 代理类型定义。"""

from enum import StrEnum


class FrpcProxyType(StrEnum):
    """结构化 JSON 配置当前支持的 frpc 代理类型。"""

    TCP = "tcp"
    UDP = "udp"
    XTCP = "xtcp"

class FrpcProxyRole(StrEnum):
    """JSON配置中，需要按照角色进一步划分的类型"""

    P2P_HOST = "p2p_host"
    P2P_VISITOR = "p2p_visitor"
