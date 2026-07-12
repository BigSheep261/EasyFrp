"""P2P 被访问端 frpc 代理的数据模型。"""

# 数据类用于声明配置结构，field 为每个实例创建独立的允许用户列表。
from dataclasses import dataclass, field
# Any 用于描述从 JSON 字典读取的原始值。
from typing import Any

# 角色和类型枚举共同区分 XTCP 被访问端与访问端配置。
from frp_gui.backend.models.frpc.profile_role import FrpcProfileRole
from frp_gui.backend.models.frpc.proxy_type import FrpcProxyType


def _validate_port(value: int, field_name: str) -> None:
    """校验端口是否为标准端口范围内的整数，并在错误中标明字段名。"""
    # 同时限制类型和取值范围，避免生成 frpc 无法连接的本地端口。
    if not isinstance(value, int) or not 1 <= value <= 65535:
        raise ValueError(f"{field_name} 必须是 1 到 65535 之间的整数。")


def _validate_string_list(values: list[str], field_name: str) -> None:
    """校验值是否为不含空白项的字符串列表。"""
    # 先检查容器类型，避免后续遍历将其他可迭代对象误当作用户列表。
    if not isinstance(values, list):
        raise ValueError(f"{field_name} 必须是字符串列表。")
    # 任一元素不是字符串或仅含空白，都说明访问授权项无效。
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{field_name} 不能包含空字符串。")


@dataclass(slots=True)
class P2PProxyConfig:
    """保存为单个 JSON 连接档案的 P2P 被访问端配置。"""

    # name 是访问端引用该被访问端代理时使用的名称。
    name: str
    # local_port 指向被访问端本机实际提供服务的端口。
    local_port: int
    # secret_key 用于验证尝试建立点对点隧道的访问端。
    secret_key: str
    # local_ip 默认指向回环地址，只转发本机服务。
    local_ip: str = "127.0.0.1"
    # allow_users 限定可连接用户；默认创建独立空列表表示未显式列出用户。
    allow_users: list[str] = field(default_factory=list)
    # P2P 被访问端基于 XTCP 协议建立隧道。
    type: FrpcProxyType = FrpcProxyType.XTCP
    # 角色字段固定默认为被访问端，用于反序列化时区分同为 XTCP 的模型。
    role: FrpcProfileRole = FrpcProfileRole.P2P_HOST

    def validate(self) -> None:
        """校验 XTCP 类型、被访问端角色、连接字段和授权用户列表。"""
        # P2P 被访问端当前只允许使用 XTCP 类型。
        if self.type != FrpcProxyType.XTCP:
            raise ValueError("P2P 被访问端配置的类型必须是 xtcp。")
        # 同为 XTCP 的访问端配置不能作为本模型保存。
        if self.role != FrpcProfileRole.P2P_HOST:
            raise ValueError("P2P 被访问端配置的角色必须是 p2p_host。")
        # 代理名称必须可供访问端引用。
        if not self.name.strip():
            raise ValueError("代理名称不能为空。")
        # 本地服务地址不能缺失或只包含空白。
        if not self.local_ip.strip():
            raise ValueError("本地 IP 不能为空。")
        # 密钥是建立受保护 P2P 隧道的必填信息。
        if not self.secret_key.strip():
            raise ValueError("P2P 密钥不能为空。")
        # 端口与授权用户分别复用对应的基础校验规则。
        _validate_port(self.local_port, "local_port")
        _validate_string_list(self.allow_users, "allow_users")

    def to_dict(self) -> dict[str, Any]:
        """校验并转换为结构化档案使用的 P2P 被访问端字典。"""
        # 序列化前确认模型的协议、角色及业务字段均有效。
        self.validate()
        # 按 frpc/档案约定输出驼峰键名，并将两个枚举转换为字符串值。
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
        """从结构化字典构造 P2P 被访问端配置，并验证转换结果。"""
        # 将 JSON 标量、列表和枚举逐项转换为模型字段，缺失值采用安全默认值。
        config = cls(
            name=str(data.get("name", "")),
            local_ip=str(data.get("localIP", "127.0.0.1")),
            local_port=int(data.get("localPort", 0)),
            secret_key=str(data.get("secretKey", "")),
            allow_users=list(data.get("allowUsers", [])),
            type=FrpcProxyType(data.get("type", FrpcProxyType.XTCP.value)),
            role=FrpcProfileRole(data.get("role", FrpcProfileRole.P2P_HOST.value)),
        )
        # 构造完成后统一检查 XTCP 被访问端的全部约束。
        config.validate()
        return config
