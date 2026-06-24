"""P2P 访问端 frpc visitor 的数据模型。"""

from dataclasses import dataclass
from typing import Any

from frp_gui.models.frpc.profile_role import FrpcProfileRole
from frp_gui.models.frpc.proxy_type import FrpcProxyType


def _validate_port(value: int, field_name: str) -> None:
    if not isinstance(value, int) or not 1 <= value <= 65535:
        raise ValueError(f"{field_name} 必须是 1 到 65535 之间的整数。")


@dataclass(slots=True)
class P2PVisitorsConfig:
    """保存为单个 JSON 连接档案的 P2P 访问端配置。"""

    name: str
    server_name: str
    secret_key: str
    bind_port: int
    bind_addr: str = "127.0.0.1"
    keep_tunnel_open: bool = False
    max_retries_an_hour: int = 8
    min_retry_interval: int = 90
    type: FrpcProxyType = FrpcProxyType.XTCP
    role: FrpcProfileRole = FrpcProfileRole.P2P_VISITOR

    def validate(self) -> None:
        if self.type != FrpcProxyType.XTCP:
            raise ValueError("P2P 访问端配置的类型必须是 xtcp。")
        if self.role != FrpcProfileRole.P2P_VISITOR:
            raise ValueError("P2P 访问端配置的角色必须是 p2p_visitor。")
        if not self.name.strip():
            raise ValueError("访问端名称不能为空。")
        if not self.server_name.strip():
            raise ValueError("被访问端代理名称不能为空。")
        if not self.secret_key.strip():
            raise ValueError("P2P 密钥不能为空。")
        if not self.bind_addr.strip():
            raise ValueError("绑定地址不能为空。")
        _validate_port(self.bind_port, "bind_port")
        if not isinstance(self.keep_tunnel_open, bool):
            raise ValueError("keep_tunnel_open 必须是布尔值。")
        if not isinstance(self.max_retries_an_hour, int) or self.max_retries_an_hour < 0:
            raise ValueError("max_retries_an_hour 必须是非负整数。")
        if not isinstance(self.min_retry_interval, int) or self.min_retry_interval < 1:
            raise ValueError("min_retry_interval 必须是正整数。")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
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
        config.validate()
        return config
