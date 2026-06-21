"""frpc 客户端全局配置数据模型。"""

from dataclasses import dataclass, field
from typing import Any


def _validate_port(value: int, field_name: str) -> None:
    if not isinstance(value, int) or not 1 <= value <= 65535:
        raise ValueError(f"{field_name} 必须是 1 到 65535 之间的整数。")


@dataclass(slots=True)
class FrpcLogConfig:
    """frpc 配置档案共享的日志相关设置。"""

    level: str = "info"
    to: str = "console"
    max_days: int = 3

    def validate(self) -> None:
        if not self.level.strip():
            raise ValueError("日志等级不能为空。")
        if not self.to.strip():
            raise ValueError("日志输出位置不能为空。")
        if not isinstance(self.max_days, int) or self.max_days < 1:
            raise ValueError("日志保留天数必须是正整数。")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "level": self.level,
            "to": self.to,
            "maxDays": self.max_days,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrpcLogConfig":
        config = cls(
            level=str(data.get("level", "info")),
            to=str(data.get("to", "console")),
            max_days=int(data.get("maxDays", 3)),
        )
        config.validate()
        return config


@dataclass(slots=True)
class FrpcGlobalConfig:
    """不绑定到单个代理的 frpc 全局设置。"""

    server_addr: str
    server_port: int
    auth_method: str = "token"
    auth_token: str = ""
    log: FrpcLogConfig = field(default_factory=FrpcLogConfig)

    def validate(self) -> None:
        if not self.server_addr.strip():
            raise ValueError("服务器地址不能为空。")
        _validate_port(self.server_port, "server_port")
        if not self.auth_method.strip():
            raise ValueError("认证方式不能为空。")
        if self.auth_method == "token" and not self.auth_token.strip():
            raise ValueError("认证方式为 token 时，认证 token 不能为空。")
        self.log.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "serverAddr": self.server_addr,
            "serverPort": self.server_port,
            "auth": {
                "method": self.auth_method,
                "token": self.auth_token,
            },
            "log": self.log.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrpcGlobalConfig":
        auth_data = data.get("auth", {})
        if not isinstance(auth_data, dict):
            raise ValueError("auth 必须是对象。")

        log_data = data.get("log", {})
        if not isinstance(log_data, dict):
            raise ValueError("log 必须是对象。")

        config = cls(
            server_addr=str(data.get("serverAddr", "")),
            server_port=int(data.get("serverPort", 0)),
            auth_method=str(auth_data.get("method", "token")),
            auth_token=str(auth_data.get("token", "")),
            log=FrpcLogConfig.from_dict(log_data),
        )
        config.validate()
        return config
