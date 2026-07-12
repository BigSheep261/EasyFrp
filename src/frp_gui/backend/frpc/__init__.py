"""frpc 后端服务的公开入口。"""

# 汇集配置文本、进程生命周期和结构化档案服务，简化上层导入路径。
from frp_gui.backend.frpc.config_service import FrpcConfigService
from frp_gui.backend.frpc.process_service import FrpcProcessService, FrpcProcessState
from frp_gui.backend.frpc.profile_service import FrpcProfileService

# 仅公开界面层需要使用的 frpc 服务及状态枚举。
__all__ = [
    "FrpcConfigService",
    "FrpcProcessService",
    "FrpcProcessState",
    "FrpcProfileService",
]

