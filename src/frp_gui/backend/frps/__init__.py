"""frps 后端服务的公开入口。"""

# 公开服务端进程生命周期服务及其状态枚举。
from frp_gui.backend.frps.process_service import FrpsProcessService, FrpsProcessState

# 仅公开界面层需要使用的 frps 服务及状态枚举。
__all__ = [
    "FrpsProcessService",
    "FrpsProcessState",
]

