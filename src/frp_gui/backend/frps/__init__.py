"""frps 后端服务的公开入口。"""

# 汇集服务端配置文本服务和进程控制服务，供上层统一导入。
from frp_gui.backend.frps.config_service import FrpsConfigService
from frp_gui.backend.frps.process_service import FrpsProcessService, FrpsProcessState

# 仅公开界面层需要使用的 frps 服务及状态枚举。
__all__ = [
    "FrpsConfigService",
    "FrpsProcessService",
    "FrpsProcessState",
]

