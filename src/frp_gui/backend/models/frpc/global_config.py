"""frpc 客户端全局配置数据模型。"""

# 数据类用于声明配置结构，field 用于安全地为嵌套日志配置创建独立实例。
from dataclasses import dataclass, field
# Any 用于描述从 JSON 字典读取、尚未完成类型转换的数据。
from typing import Any


def _validate_port(value: int, field_name: str) -> None:
    """校验端口是否为 TCP/UDP 可用范围内的整数，并在错误中标明字段名。"""
    # bool 虽是 int 的子类，但此处沿用既有 isinstance 规则并同时检查端口边界。
    if not isinstance(value, int) or not 1 <= value <= 65535:
        raise ValueError(f"{field_name} 必须是 1 到 65535 之间的整数。")


@dataclass(slots=True)
class FrpcLogConfig:
    """frpc 配置档案共享的日志相关设置。"""

    # 日志级别直接使用 frpc 接受的文本值，默认记录 info 及以上信息。
    level: str = "info"
    # 输出目标默认为控制台，也可由调用方配置为其他 frpc 支持的位置。
    to: str = "console"
    # 日志文件默认保留三天。
    max_days: int = 3

    def validate(self) -> None:
        """校验日志级别、输出目标和保留天数是否可用于生成配置。"""
        # 级别至少需要包含一个非空白字符。
        if not self.level.strip():
            raise ValueError("日志等级不能为空。")
        # 输出位置同样不能是空字符串或纯空白。
        if not self.to.strip():
            raise ValueError("日志输出位置不能为空。")
        # 保留天数必须是至少一天的整数。
        if not isinstance(self.max_days, int) or self.max_days < 1:
            raise ValueError("日志保留天数必须是正整数。")

    def to_dict(self) -> dict[str, Any]:
        """校验当前对象并转换为 frpc JSON 档案使用的键名格式。"""
        # 序列化前阻止无效对象进入持久化层。
        self.validate()
        # 输出键名保持与 frpc 配置约定一致，其中 maxDays 使用驼峰命名。
        return {
            "level": self.level,
            "to": self.to,
            "maxDays": self.max_days,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FrpcLogConfig":
        """从 JSON 风格字典构造日志配置，并对转换结果执行校验。"""
        # 缺失字段使用与数据类一致的默认值，并显式转换为目标标量类型。
        config = cls(
            level=str(data.get("level", "info")),
            to=str(data.get("to", "console")),
            max_days=int(data.get("maxDays", 3)),
        )
        # 完成类型转换后统一验证业务约束，再返回可用模型。
        config.validate()
        return config


@dataclass(slots=True)
class FrpcGlobalConfig:
    """不绑定到单个代理的 frpc 全局设置。"""

    # frps 服务端地址是建立客户端控制连接所必需的目标。
    server_addr: str
    # frps 服务端端口需落在标准端口范围内。
    server_port: int
    # 认证方式默认采用 token，与当前生成的认证字段结构对应。
    auth_method: str = "token"
    # 认证令牌由调用方提供，token 模式下不能为空。
    auth_token: str = ""
    # 每个全局配置都获得独立的日志配置对象，避免实例间共享可变状态。
    log: FrpcLogConfig = field(default_factory=FrpcLogConfig)

    def validate(self) -> None:
        """校验服务器连接、认证信息和嵌套日志配置。"""
        # 服务端地址不能缺失或只包含空白字符。
        if not self.server_addr.strip():
            raise ValueError("服务器地址不能为空。")
        # 端口校验复用统一边界规则。
        _validate_port(self.server_port, "server_port")
        # 认证方式名称必须存在，才能生成有效 auth 配置。
        if not self.auth_method.strip():
            raise ValueError("认证方式不能为空。")
        # token 认证依赖非空令牌；其他认证方式不强制该字段。
        if self.auth_method == "token" and not self.auth_token.strip():
            raise ValueError("认证方式为 token 时，认证 token 不能为空。")
        # 最后递归校验嵌套日志对象，保证整份配置均有效。
        self.log.validate()

    def to_dict(self) -> dict[str, Any]:
        """校验并转换为结构化档案使用的 frpc 全局配置字典。"""
        # 序列化前验证整个对象树，避免写出部分有效的配置。
        self.validate()
        # 按 frpc 的层级和驼峰键名组织服务器、认证与日志设置。
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
        """从结构化字典恢复全局配置，并验证嵌套对象和业务约束。"""
        # auth 缺失时使用空对象，以便后续字段采用各自默认值。
        auth_data = data.get("auth", {})
        # 非对象 auth 无法按键读取，直接给出明确的格式错误。
        if not isinstance(auth_data, dict):
            raise ValueError("auth 必须是对象。")

        # log 缺失时同样使用空对象，由日志模型填充默认值。
        log_data = data.get("log", {})
        # 日志节点必须是对象，才能交给嵌套模型解析。
        if not isinstance(log_data, dict):
            raise ValueError("log 必须是对象。")

        # 将 JSON 键逐项映射为 Python 字段，并构造嵌套日志模型。
        config = cls(
            server_addr=str(data.get("serverAddr", "")),
            server_port=int(data.get("serverPort", 0)),
            auth_method=str(auth_data.get("method", "token")),
            auth_token=str(auth_data.get("token", "")),
            log=FrpcLogConfig.from_dict(log_data),
        )
        # 类型转换完成后检查端口、必填文本和认证规则。
        config.validate()
        return config
