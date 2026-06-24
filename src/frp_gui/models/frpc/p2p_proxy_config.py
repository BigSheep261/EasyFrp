"""P2P 被访问端 frpc 代理的数据模型。"""

from dataclasses import dataclass, field
from typing import Any

from frp_gui.models.frpc.profile_role import FrpcProfileRole
from frp_gui.models.frpc.proxy_type import FrpcProxyType


def _validate_port(value: int, field_name: str) -> None:
    if not isinstance(value, int) or not 1 <= value <= 65535:
        raise ValueError(f"{field_name} 必须是 1 到 65535 之间的整数。")


def _validate_string_list(values: list[str], field_name: str) -> None:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} 必须是字符串列表。")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{field_name} 不能包含空字符串。")


@dataclass(slots=True)
class P2PProxyConfig:
    """保存为单个 JSON 连接档案的 P2P 被访问端配置。"""

    name: str
    local_port: int
    secret_key: str
    local_ip: str = "127.0.0.1"
    allow_users: list[str] = field(default_factory=list)
    type: FrpcProxyType = FrpcProxyType.XTCP
    role: FrpcProfileRole = FrpcProfileRole.P2P_HOST

    def validate(self) -> None:
        if self.type != FrpcProxyType.XTCP:
            raise ValueError("P2P 被访问端配置的类型必须是 xtcp。")
        if self.role != FrpcProfileRole.P2P_HOST:
            raise ValueError("P2P 被访问端配置的角色必须是 p2p_host。")
        if not self.name.strip():
            raise ValueError("代理名称不能为空。")
        if not self.local_ip.strip():
            raise ValueError("本地 IP 不能为空。")
        if not self.secret_key.strip():
            raise ValueError("P2P 密钥不能为空。")
        _validate_port(self.local_port, "local_port")
        _validate_string_list(self.allow_users, "allow_users")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "name": self.name,
            "type": self.type.value,
            "role": self.role.value,
            "localIP": self.local_ip,
            "localPort": self.local_port,
            "secretKey": self.secret_key,
            "allowUsers": self.allow_users,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "P2PProxyConfig":
        config = cls(
            name=str(data.get("name", "")),
            local_ip=str(data.get("localIP", "127.0.0.1")),
            local_port=int(data.get("localPort", 0)),
            secret_key=str(data.get("secretKey", "")),
            allow_users=list(data.get("allowUsers", [])),
            type=FrpcProxyType(data.get("type", FrpcProxyType.XTCP.value)),
            role=FrpcProfileRole(data.get("role", FrpcProfileRole.P2P_HOST.value)),
        )
        config.validate()
        return config
