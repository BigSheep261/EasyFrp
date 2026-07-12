"""frpc 代理类型定义。"""

# 使用字符串枚举，使枚举成员既可安全比较，也可直接对应 JSON/frpc 中的文本值。
from enum import StrEnum


class FrpcProxyType(StrEnum):
    """结构化 JSON 配置当前支持的 frpc 代理类型。"""

    # TCP 代理转发面向连接的字节流。
    TCP = "tcp"
    # UDP 代理转发无连接的数据报。
    UDP = "udp"
    # XTCP 代理通过访问端与被访问端建立点对点隧道。
    XTCP = "xtcp"


class FrpcProxyRole(StrEnum):
    """需要在 JSON 配置中进一步区分的 XTCP 端点角色。"""

    # 被访问端对外声明代理，并提供真实的本地服务。
    P2P_HOST = "p2p_host"
    # 访问端连接被访问端代理，并在本地暴露访问入口。
    P2P_VISITOR = "p2p_visitor"
