"""frpc 代理类型定义。"""

from enum import StrEnum


class FrpcProxyType(StrEnum):
    """结构化 JSON 配置当前支持的 frpc 代理类型。"""

    TCP = "tcp"
    UDP = "udp"
