"""P2P 访问端 frpc visitor 的数据模型。"""

# 数据类用于以紧凑结构保存 visitor 配置字段。
from dataclasses import dataclass
# Any 用于描述从 JSON 字典读取的原始值。
from typing import Any

# 角色和类型枚举共同区分 XTCP 访问端与被访问端配置。
from frp_gui.backend.models.frpc.profile_role import FrpcProfileRole
from frp_gui.backend.models.frpc.proxy_type import FrpcProxyType


def _validate_port(value: int, field_name: str) -> None:
    """校验端口是否为标准端口范围内的整数，并在错误中标明字段名。"""
    # 同时限制类型和取值范围，避免 visitor 绑定无效的本地端口。
    if not isinstance(value, int) or not 1 <= value <= 65535:
        raise ValueError(f"{field_name} 必须是 1 到 65535 之间的整数。")


@dataclass(slots=True)
class P2PVisitorsConfig:
    """保存为单个 JSON 连接档案的 P2P 访问端配置。"""

    # name 标识当前 visitor 配置自身。
    name: str
    # server_name 指向远端被访问端声明的代理名称。
    server_name: str
    # secret_key 必须与被访问端密钥匹配才能建立隧道。
    secret_key: str
    # bind_port 是本地应用访问远端服务时连接的监听端口。
    bind_port: int
    # bind_addr 默认仅监听回环地址，避免将访问入口暴露给局域网。
    bind_addr: str = "127.0.0.1"
    # keep_tunnel_open 控制是否持续维持隧道，而不是按需连接。
    keep_tunnel_open: bool = False
    # max_retries_an_hour 限制一小时内的最大重试次数。
    max_retries_an_hour: int = 8
    # min_retry_interval 指定两次重试之间至少等待的秒数。
    min_retry_interval: int = 90
    # P2P visitor 使用 XTCP 代理类型。
    type: FrpcProxyType = FrpcProxyType.XTCP
    # 角色字段固定默认为访问端，以便与被访问端模型区分。
    role: FrpcProfileRole = FrpcProfileRole.P2P_VISITOR

    def validate(self) -> None:
        """校验 XTCP 类型、访问端角色、连接字段和重试策略。"""
        # P2P 访问端当前只允许使用 XTCP 类型。
        if self.type != FrpcProxyType.XTCP:
            raise ValueError("P2P 访问端配置的类型必须是 xtcp。")
        # 同为 XTCP 的被访问端配置不能作为本模型保存。
        if self.role != FrpcProfileRole.P2P_VISITOR:
            raise ValueError("P2P 访问端配置的角色必须是 p2p_visitor。")
        # visitor 自身名称不能为空或纯空白。
        if not self.name.strip():
            raise ValueError("访问端名称不能为空。")
        # 必须指定要连接的被访问端代理名称。
        if not self.server_name.strip():
            raise ValueError("被访问端代理名称不能为空。")
        # 访问端密钥不能为空，且应由业务层确保与被访问端一致。
        if not self.secret_key.strip():
            raise ValueError("P2P 密钥不能为空。")
        # 本地监听地址必须包含实际内容。
        if not self.bind_addr.strip():
            raise ValueError("绑定地址不能为空。")
        # 本地监听端口使用统一边界规则校验。
        _validate_port(self.bind_port, "bind_port")
        # 隧道保持开关只接受明确的布尔值。
        if not isinstance(self.keep_tunnel_open, bool):
            raise ValueError("keep_tunnel_open 必须是布尔值。")
        # 每小时最大重试次数允许为零，但不能为负数或非整数。
        if not isinstance(self.max_retries_an_hour, int) or self.max_retries_an_hour < 0:
            raise ValueError("max_retries_an_hour 必须是非负整数。")
        # 最小重试间隔至少为一秒，并且必须是整数。
        if not isinstance(self.min_retry_interval, int) or self.min_retry_interval < 1:
            raise ValueError("min_retry_interval 必须是正整数。")

    def to_dict(self) -> dict[str, Any]:
        """校验并转换为结构化档案使用的 P2P 访问端字典。"""
        # 序列化前确认模型的协议、角色、监听字段及重试策略均有效。
        self.validate()
        # 按 frpc/档案约定输出驼峰键名，并将两个枚举转换为字符串值。
        return {
            "name": self.name,
            "type": self.type.value,
            "role": self.role.value,
            "serverName": self.server_name,
            "secretKey": self.secret_key,
            "bindAddr": self.bind_addr,
            "bindPort": self.bind_port,
            "keepTunnelOpen": self.keep_tunnel_open,
            "maxRetriesAnHour": self.max_retries_an_hour,
            "minRetryInterval": self.min_retry_interval,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "P2PVisitorsConfig":
        """从结构化字典构造 P2P 访问端配置，并验证转换结果。"""
        # 将 JSON 字段转换为模型标量和枚举，缺失值采用数据类对应默认值。
        config = cls(
            name=str(data.get("name", "")),
            server_name=str(data.get("serverName", "")),
            secret_key=str(data.get("secretKey", "")),
            bind_addr=str(data.get("bindAddr", "127.0.0.1")),
            bind_port=int(data.get("bindPort", 0)),
            keep_tunnel_open=bool(data.get("keepTunnelOpen", False)),
            max_retries_an_hour=int(data.get("maxRetriesAnHour", 8)),
            min_retry_interval=int(data.get("minRetryInterval", 90)),
            type=FrpcProxyType(data.get("type", FrpcProxyType.XTCP.value)),
            role=FrpcProfileRole(
                data.get("role", FrpcProfileRole.P2P_VISITOR.value)
            ),
        )
        # 构造完成后统一检查 XTCP 访问端的全部约束。
        config.validate()
        return config
