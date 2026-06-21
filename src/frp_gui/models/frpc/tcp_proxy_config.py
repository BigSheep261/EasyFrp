"""单个 TCP frpc 代理的数据模型。"""

from dataclasses import dataclass
from typing import Any

from frp_gui.models.frpc.proxy_type import FrpcProxyType


def _validate_port(value: int, field_name: str) -> None:
    if not isinstance(value, int) or not 1 <= value <= 65535:
        raise ValueError(f"{field_name} 必须是 1 到 65535 之间的整数。")


@dataclass(slots=True)
class TcpProxyConfig:
    """保存为单个 JSON 连接档案的 TCP 代理配置。"""

    name: str
    local_port: int
    remote_port: int
    local_ip: str = "127.0.0.1"
    type: FrpcProxyType = FrpcProxyType.TCP

    def validate(self) -> None:
        if self.type != FrpcProxyType.TCP:
            raise ValueError("TCP 代理配置的类型必须是 tcp。")
        if not self.name.strip():
            raise ValueError("代理名称不能为空。")
        if not self.local_ip.strip():
            raise ValueError("本地 IP 不能为空。")
        _validate_port(self.local_port, "local_port")
        _validate_port(self.remote_port, "remote_port")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "name": self.name,
            "type": self.type.value,
            "localIP": self.local_ip,
            "localPort": self.local_port,
            "remotePort": self.remote_port,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TcpProxyConfig":
        config = cls(
            name=str(data.get("name", "")),
            local_ip=str(data.get("localIP", "127.0.0.1")),
            local_port=int(data.get("localPort", 0)),
            remote_port=int(data.get("remotePort", 0)),
            type=FrpcProxyType(data.get("type", FrpcProxyType.TCP.value)),
        )
        config.validate()
        return config
