"""共用工具辅助函数。"""

# 将常用的本地文件工具提升到工具包命名空间，简化外部导入路径。
from frp_gui.utils.fileIO import LocalFileUtils


# 明确工具包的公共接口，避免通配符导入泄露内部名称。
__all__ = ["LocalFileUtils"]
