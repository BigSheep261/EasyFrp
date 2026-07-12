"""结构化 frpc 配置档案的 JSON 持久化服务。"""

# JSONDecodeError 用于将底层解析失败转换为面向配置档案的业务错误。
from json import JSONDecodeError
# Path 表达可注入的档案目录和最终文件路径。
from pathlib import Path
# 正则表达式用于一次性检查 Windows 文件名中的非法字符。
import re
# Any 描述从 JSON 中取得、尚未分派给具体模型的字段值。
from typing import Any

# 默认目录常量分别保存全局配置档案与连接配置档案。
from frp_gui.utils.paths import FRPC_CONNECTION_PROFILE_DIR, FRPC_GLOBAL_PROFILE_DIR
# 结构化模型负责各类配置的字段转换和业务校验。
from frp_gui.backend.models.frpc import (
    FrpcGlobalConfig,
    FrpcProfileRole,
    FrpcProxyType,
    P2PProxyConfig,
    P2PVisitorsConfig,
    TcpProxyConfig,
    UdpProxyConfig,
)
# 统一文件工具封装 JSON 读写与档案名列表查询。
from frp_gui.utils import LocalFileUtils


# 类型别名汇总所有可由连接档案服务保存或返回的代理模型。
FrpcProxyConfig = TcpProxyConfig | UdpProxyConfig | P2PProxyConfig | P2PVisitorsConfig


class FrpcProfileService:
    """保存和读取结构化 frpc JSON 配置档案。

    全局配置和连接配置分开保存，方便未来启动时把一个全局配置和被选中的连接配置组合起来。
    """

    # 档案名不得包含 Windows 禁用字符、控制字符或路径分隔符。
    _VALID_PROFILE_NAME = re.compile(r"^[^<>:\"/\\|?*\x00-\x1f]+$")

    def __init__(
        self,
        global_dir: Path | None = None,
        connection_dir: Path | None = None,
    ) -> None:
        """初始化服务，并允许分别覆盖全局档案和连接档案目录。"""
        # 未传入目录时使用项目约定的两个独立档案目录。
        self.global_dir = global_dir or FRPC_GLOBAL_PROFILE_DIR
        self.connection_dir = connection_dir or FRPC_CONNECTION_PROFILE_DIR

    def save_global_config(self, profile_name: str, config: FrpcGlobalConfig) -> Path:
        """保存一个 frpc 全局配置 JSON 文件。"""
        # 写入前由模型验证服务器、认证与日志字段。
        config.validate()
        # 校验档案名并在全局配置目录中生成目标 JSON 路径。
        path = self._profile_path(self.global_dir, profile_name)
        # 使用模型定义的稳定字典格式进行 JSON 持久化。
        LocalFileUtils.write_json(path, config.to_dict())
        # 返回实际落盘路径，便于调用方展示或后续处理。
        return path

    def load_global_config(self, profile_name: str) -> FrpcGlobalConfig:
        """读取一个 frpc 全局配置 JSON 文件。"""
        # 档案名先经过与保存流程相同的安全检查。
        path = self._profile_path(self.global_dir, profile_name)
        # 只接受以对象为根节点的有效 JSON 档案。
        data = self._read_json_object(path)
        # 交给全局配置模型完成字段转换、嵌套解析和业务校验。
        return FrpcGlobalConfig.from_dict(data)

    def save_proxy_config(self, profile_name: str, config: FrpcProxyConfig) -> Path:
        """保存一个连接配置 JSON 文件。"""
        # 联合类型中的每个模型都提供同名校验入口。
        config.validate()
        # 校验档案名并在连接配置目录中生成目标 JSON 路径。
        path = self._profile_path(self.connection_dir, profile_name)
        # 由具体模型决定序列化键名和 type/role 标识。
        LocalFileUtils.write_json(path, config.to_dict())
        # 返回实际落盘路径，便于调用方展示或后续处理。
        return path

    def load_proxy_config(self, profile_name: str) -> FrpcProxyConfig:
        """读取一个连接配置，并按 type 和 role 解析成对应模型。"""
        # 档案名先经过安全检查，再从连接配置目录读取 JSON 对象。
        path = self._profile_path(self.connection_dir, profile_name)
        data = self._read_json_object(path)

        # type 是选择 TCP、UDP 或 XTCP 模型的第一层判别字段。
        proxy_type = data.get("type")
        # TCP 档案直接交给 TCP 模型转换和校验。
        if proxy_type == FrpcProxyType.TCP.value:
            return TcpProxyConfig.from_dict(data)
        # UDP 档案直接交给 UDP 模型转换和校验。
        if proxy_type == FrpcProxyType.UDP.value:
            return UdpProxyConfig.from_dict(data)
        # XTCP 同时包含两种端点角色，需要继续依据 role 分派。
        if proxy_type == FrpcProxyType.XTCP.value:
            return self._load_xtcp_config(data)

        # 缺失或未知 type 均不能安全推断模型，因此明确拒绝加载。
        raise ValueError(f"不支持的 frpc 代理类型：{proxy_type!r}")

    def _load_xtcp_config(self, data: dict[str, Any]) -> P2PProxyConfig | P2PVisitorsConfig:
        """依据 XTCP 档案中的角色构造被访问端或访问端模型。"""
        # role 是在 XTCP 类型内部区分两个配置结构的第二层判别字段。
        role = data.get("role")
        # 被访问端负责暴露实际本地服务，使用 P2PProxyConfig 解析。
        if role == FrpcProfileRole.P2P_HOST.value:
            return P2PProxyConfig.from_dict(data)
        # 访问端负责本地绑定入口，使用 P2PVisitorsConfig 解析。
        if role == FrpcProfileRole.P2P_VISITOR.value:
            return P2PVisitorsConfig.from_dict(data)

        # 未知角色可能对应不兼容的数据结构，不能默认选择任一模型。
        raise ValueError(f"不支持的 xtcp 配置角色：{role!r}")

    def list_global_profiles(self) -> list[str]:
        """返回已保存的全局配置名称，不包含 .json 后缀。"""
        # 文件工具仅枚举 JSON 文件并直接返回文件主名。
        return LocalFileUtils.list_file_stems(self.global_dir, "*.json")

    def list_proxy_profiles(self) -> list[str]:
        """返回已保存的连接配置名称，不包含 .json 后缀。"""
        # 文件工具仅枚举 JSON 文件并直接返回文件主名。
        return LocalFileUtils.list_file_stems(self.connection_dir, "*.json")

    def _profile_path(self, directory: Path, profile_name: str) -> Path:
        """校验档案名，并在指定目录下生成对应的 JSON 文件路径。"""
        # 使用清理后的安全名称，避免原始输入形成路径穿越或非法文件名。
        safe_name = self._validate_profile_name(profile_name)
        # 档案扩展名固定为 .json，调用方只需提供不带后缀的业务名称。
        return directory / f"{safe_name}.json"

    def _validate_profile_name(self, profile_name: str) -> str:
        """去除档案名首尾空白，并拒绝空名称、路径片段和非法字符。"""
        # 首尾空白不属于业务名称，统一清理后再执行检查。
        name = profile_name.strip()
        # 空字符串无法形成可识别档案名。
        if not name:
            raise ValueError("配置名称不能为空。")
        # 单点、双点和禁用字符可能形成目录引用或不合法的系统文件名。
        if name in {".", ".."} or not self._VALID_PROFILE_NAME.match(name):
            raise ValueError("配置名称包含无效的文件名字符。")
        # 返回规范名称，确保保存和加载使用相同路径规则。
        return name

    def _read_json_object(self, path: Path) -> dict[str, Any]:
        """读取 JSON 档案，并保证解析结果的根节点是对象。"""
        # 捕获 JSON 语法错误，以附带具体档案路径的业务异常重新抛出。
        try:
            data = LocalFileUtils.read_json(path)
        # 将底层解析异常转换为调用方可统一处理的配置格式错误。
        except JSONDecodeError as error:
            raise ValueError(f"JSON 配置档案格式无效：{path}") from error

        # 各配置模型都要求以键值对象为输入，数组或标量根节点不可接受。
        if not isinstance(data, dict):
            raise ValueError("JSON 配置档案根节点必须是对象。")
        # 类型确认后返回给具体模型完成字段级解析。
        return data
