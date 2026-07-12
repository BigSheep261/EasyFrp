"""frpc TOML 配置文件读写服务。

UI 层不应该直接关心文件路径、读写异常和 TOML 解析细节。
这个 service 把配置文件业务集中起来，让 page 和 panel 专心负责界面。
"""

# 路径对象用于允许调用方注入自定义配置文件位置。
from pathlib import Path

# tomlkit 负责解析 TOML，同时提供可精确识别的语法异常类型。
import tomlkit
from tomlkit.exceptions import TOMLKitError

# 默认路径与统一文件工具由基础设施层提供，避免在服务中重复实现读写细节。
from frp_gui.utils.paths import CONFIG_DIR
from frp_gui.utils import LocalFileUtils


class FrpcConfigService:
    """读取、校验并保存 ``config/frpc.toml``。

    第一版先把整个 TOML 当作文本编辑。
    这样比字段化表单更简单，也不会因为 frpc 配置项很多而漏掉某些 proxy 类型。
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """初始化服务，并允许使用自定义路径替代默认 frpc 配置文件。"""
        # 未传入路径时遵循项目约定，使用配置目录中的 frpc.toml。
        self.config_path = config_path or CONFIG_DIR / "frpc.toml"

    def load_text(self) -> str:
        """从磁盘读取当前 TOML 文本。

        Windows 的系统默认编码不一定是 UTF-8，所以这里显式指定编码，
        避免中文注释或后续中文配置内容被错误读取。
        """
        # 文件不存在时返回空文本，便于界面直接展示一个可编辑的空配置。
        return LocalFileUtils.read_text(self.config_path, default="")

    def validate_text(self, text: str) -> tuple[bool, str]:
        """只校验 TOML 语法，不写入磁盘。

        入门级代码里先使用简单的返回值：
        ``(True, "")`` 表示校验通过，``(False, message)`` 表示校验失败。
        """
        # 尝试完整解析输入文本，仅检查语法而不保留或修改解析结果。
        try:
            tomlkit.parse(text)
        # 将解析器异常转换为界面层易于处理的“状态 + 消息”返回值。
        except TOMLKitError as error:
            return False, str(error)
        # 没有发生语法异常即表示校验成功，成功时错误消息保持为空。
        return True, ""

    def save_text(self, text: str) -> tuple[bool, str]:
        """先校验，再把 TOML 文本写回原配置文件。"""
        # 在落盘前复用同一校验入口，防止保存不可解析的配置。
        is_valid, error_message = self.validate_text(text)
        # 校验失败时原样返回解析器消息，并保持磁盘文件不变。
        if not is_valid:
            return False, error_message

        # 校验通过后交给统一文件工具写入，并返回无错误的成功结果。
        LocalFileUtils.write_text(self.config_path, text)
        return True, ""
