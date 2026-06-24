"""结构化 frpc 配置档案的 JSON 持久化服务。"""

from json import JSONDecodeError
from pathlib import Path
import re
from typing import Any

from frp_gui.core.paths import FRPC_CONNECTION_PROFILE_DIR, FRPC_GLOBAL_PROFILE_DIR
from frp_gui.models.frpc import (
    FrpcGlobalConfig,
    FrpcProfileRole,
    FrpcProxyType,
    P2PProxyConfig,
    P2PVisitorsConfig,
    TcpProxyConfig,
    UdpProxyConfig,
)
from frp_gui.utils import LocalFileUtils


FrpcProxyConfig = TcpProxyConfig | UdpProxyConfig | P2PProxyConfig | P2PVisitorsConfig


class FrpcProfileService:
    """保存和读取结构化 frpc JSON 配置档案。

    全局配置和连接配置分开保存，方便未来启动时把一个全局配置和被选中的连接配置组合起来。
    """

    _VALID_PROFILE_NAME = re.compile(r"^[^<>:\"/\\|?*\x00-\x1f]+$")

    def __init__(self, global_dir: Path | None = None, connection_dir: Path | None = None ) -> None:
        self.global_dir = global_dir or FRPC_GLOBAL_PROFILE_DIR
        self.connection_dir = connection_dir or FRPC_CONNECTION_PROFILE_DIR

    def save_global_config(self, profile_name: str, config: FrpcGlobalConfig) -> Path:
        """保存一个 frpc 全局配置 JSON 文件。"""
        config.validate()
        path = self._profile_path(self.global_dir, profile_name)
        LocalFileUtils.write_json(path, config.to_dict())
        return path

    def load_global_config(self, profile_name: str) -> FrpcGlobalConfig:
        """读取一个 frpc 全局配置 JSON 文件。"""
        path = self._profile_path(self.global_dir, profile_name)
        data = self._read_json_object(path)
        return FrpcGlobalConfig.from_dict(data)

    def save_proxy_config(self, profile_name: str, config: FrpcProxyConfig) -> Path:
        """保存一个连接配置 JSON 文件。"""
        config.validate()
        path = self._profile_path(self.connection_dir, profile_name)
        LocalFileUtils.write_json(path, config.to_dict())
        return path

    def load_proxy_config(self, profile_name: str) -> FrpcProxyConfig:
        """读取一个连接配置，并按 type 和 role 解析成对应模型。"""
        path = self._profile_path(self.connection_dir, profile_name)
        data = self._read_json_object(path)

        proxy_type = data.get("type")
        if proxy_type == FrpcProxyType.TCP.value:
            return TcpProxyConfig.from_dict(data)
        if proxy_type == FrpcProxyType.UDP.value:
            return UdpProxyConfig.from_dict(data)
        if proxy_type == FrpcProxyType.XTCP.value:
            return self._load_xtcp_config(data)

        raise ValueError(f"不支持的 frpc 代理类型：{proxy_type!r}")

    def _load_xtcp_config(self, data: dict[str, Any]) -> P2PProxyConfig | P2PVisitorsConfig:
        role = data.get("role")
        if role == FrpcProfileRole.P2P_HOST.value:
            return P2PProxyConfig.from_dict(data)
        if role == FrpcProfileRole.P2P_VISITOR.value:
            return P2PVisitorsConfig.from_dict(data)

        raise ValueError(f"不支持的 xtcp 配置角色：{role!r}")

    def list_global_profiles(self) -> list[str]:
        """返回已保存的全局配置名称，不包含 .json 后缀。"""
        return LocalFileUtils.list_file_stems(self.global_dir, "*.json")

    def list_proxy_profiles(self) -> list[str]:
        """返回已保存的连接配置名称，不包含 .json 后缀。"""
        return LocalFileUtils.list_file_stems(self.connection_dir, "*.json")

    def _profile_path(self, directory: Path, profile_name: str) -> Path:
        safe_name = self._validate_profile_name(profile_name)
        return directory / f"{safe_name}.json"

    def _validate_profile_name(self, profile_name: str) -> str:
        name = profile_name.strip()
        if not name:
            raise ValueError("配置名称不能为空。")
        if name in {".", ".."} or not self._VALID_PROFILE_NAME.match(name):
            raise ValueError("配置名称包含无效的文件名字符。")
        return name

    def _read_json_object(self, path: Path) -> dict[str, Any]:
        try:
            data = LocalFileUtils.read_json(path)
        except JSONDecodeError as error:
            raise ValueError(f"JSON 配置档案格式无效：{path}") from error

        if not isinstance(data, dict):
            raise ValueError("JSON 配置档案根节点必须是对象。")
        return data
