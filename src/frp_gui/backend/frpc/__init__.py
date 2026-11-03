"""frpc 后端服务的公开入口。"""

# 公开客户端进程生命周期服务及其状态枚举。
from frp_gui.backend.frpc.process_service import FrpcProcessService, FrpcProcessState

# 仅公开界面层需要使用的 frpc 服务及状态枚举。
__all__ = [
    "FrpcProcessService",
    "FrpcProcessState",
]

