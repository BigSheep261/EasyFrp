"""单个 UDP frpc 代理的数据模型。"""

# 数据类用于以紧凑结构保存代理字段。
from dataclasses import dataclass
# Any 用于描述从 JSON 字典读取的原始值。
from typing import Any

# 类型枚举确保序列化值与 frpc 支持的代理名称一致。
from frp_gui.backend.models.frpc.proxy_type import FrpcProxyType


def _validate_port(value: int, field_name: str) -> None:
    """校验端口是否为标准端口范围内的整数，并在错误中标明字段名。"""
    # 同时检查数据类型和上下界，避免生成 frpc 无法监听或连接的端口。
    if not isinstance(value, int) or not 1 <= value <= 65535:
        raise ValueError(f"{field_name} 必须是 1 到 65535 之间的整数。")


@dataclass(slots=True)
class UdpProxyConfig:
    """保存为单个 JSON 连接档案的 UDP 代理配置。"""

    # name 是 frpc 配置中标识该代理的唯一业务名称。
    name: str
    # local_port 指向本机等待被转发的 UDP 服务端口。
    local_port: int
    # remote_port 是 frps 对外接收并转发数据报的端口。
    remote_port: int
    # local_ip 默认指向本机回环地址，减少服务意外暴露的范围。
    local_ip: str = "127.0.0.1"
    # UDP 模型的类型固定默认为 udp，仍保留字段以支持反序列化校验。
    type: FrpcProxyType = FrpcProxyType.UDP

    def validate(self) -> None:
        """校验代理类型、名称、本地地址以及两端端口。"""
        # 防止误把其他代理类型的数据包装为 UDP 配置。
        if self.type != FrpcProxyType.UDP:
            raise ValueError("UDP 代理配置的类型必须是 udp。")
        # 代理名称是 frpc 识别配置段的必填字段。
        if not self.name.strip():
            raise ValueError("代理名称不能为空。")
        # 本地目标地址必须包含实际内容。
        if not self.local_ip.strip():
            raise ValueError("本地 IP 不能为空。")
        # 本地服务端口和远端监听端口均使用完整端口边界校验。
        _validate_port(self.local_port, "local_port")
        _validate_port(self.remote_port, "remote_port")

    def to_dict(self) -> dict[str, Any]:
        """校验并转换为结构化档案使用的 UDP 代理字典。"""
        # 序列化前确保所有字段均满足 UDP 代理约束。
        self.validate()
        # 按 frpc 的驼峰键名输出，枚举类型转换为其字符串值。
        return {
            "name": self.name,
            "type": self.type.value,
            "localIP": self.local_ip,
            "localPort": self.local_port,
            "remotePort": self.remote_port,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UdpProxyConfig":
        """从结构化字典构造 UDP 代理配置，并验证转换结果。"""
        # 缺失字段使用安全默认值，随后由统一校验产生明确错误。
        config = cls(
            name=str(data.get("name", "")),
            local_ip=str(data.get("localIP", "127.0.0.1")),
            local_port=int(data.get("localPort", 0)),
            remote_port=int(data.get("remotePort", 0)),
            type=FrpcProxyType(data.get("type", FrpcProxyType.UDP.value)),
        )
        # 枚举和标量转换成功后再检查类型一致性及字段范围。
        config.validate()
        return config
