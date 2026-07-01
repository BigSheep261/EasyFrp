"""应用程序核心服务。"""

from typing import Any


__all__ = ["FrpcController", "FrpcState", "FrpsController", "FrpsState"]


def __getattr__(name: str) -> Any:
    """仅在调用方请求时才加载依赖 Qt 的控制器导出。"""
    if name in {"FrpcController", "FrpcState"}:
        from frp_gui.core.frpc_controller import FrpcController, FrpcState

        exports = {
            "FrpcController": FrpcController,
            "FrpcState": FrpcState,
        }
        return exports[name]
    if name in {"FrpsController", "FrpsState"}:
        from frp_gui.core.frps_controller import FrpsController, FrpsState

        exports = {
            "FrpsController": FrpsController,
            "FrpsState": FrpsState,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
