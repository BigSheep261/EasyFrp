"""以卡片网格展示和管理 frpc 代理配置的面板。"""

# 延迟解析类型注解，避免前向引用在模块导入阶段被立即求值。
from __future__ import annotations

# 数据类用于声明不可变的卡片摘要，类型工具用于兼容不同 TOML 容器。
from dataclasses import dataclass
from typing import Any, Iterable

# tomlkit 负责解析配置文本，并提供专用的格式错误类型。
import tomlkit
from tomlkit.exceptions import TOMLKitError

# 导入 Qt 对齐、信号机制及构建卡片管理界面所需的控件。
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# 配置服务统一负责定位和读取 frpc.toml。
from frp_gui.backend.frpc.config_service import FrpcConfigService


# 冻结数据类，防止卡片构造后摘要被意外修改而与界面显示失去同步。
@dataclass(frozen=True)
class FrpcProxySummary:
    """保存一条 frpc 代理配置在卡片中展示所需的只读摘要。"""

    # 连接名称用于卡片标题和完整名称提示。
    name: str
    # 规范化类型用于样式属性，保证样式表只处理有限取值。
    proxy_type: str
    # 展示类型是面向用户的短标签，例如 TCP、UDP 或 P2P。
    display_type: str
    # 字段元组按顺序保存卡片正文中的“标签—值”行。
    fields: tuple[tuple[str, str], ...]


class FrpcProxyCard(QFrame):
    """用紧凑卡片呈现一条 frpc 连接配置摘要。"""

    def __init__(self, summary: FrpcProxySummary, parent: QWidget | None = None) -> None:
        """保存代理摘要，设置卡片尺寸与样式属性，并创建内部界面。"""
        # 先初始化框架基类，使卡片可以加入父级网格布局。
        super().__init__(parent)
        # 保留只读摘要，供标题、类型徽标和正文构造共同使用。
        self.summary = summary
        # 对象名和动态类型属性为样式表提供稳定选择器。
        self.setObjectName("frpcProxyCard")
        self.setProperty("proxyType", summary.proxy_type)
        # 固定卡片高度下限并允许宽度随网格列宽伸展。
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(260, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # 完成基础属性设置后再创建标题区、分隔线和字段区。
        self._build_ui()

    def _build_ui(self) -> None:
        """根据摘要内容构建卡片标题、类型徽标和字段网格。"""
        # 卡片主布局无内边距和区块间距，使各视觉区域可以无缝衔接。
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 标题区横向放置可伸缩的连接名称与固定尺寸的类型徽标。
        header_widget = QWidget(self)
        header_widget.setObjectName("proxyCardHeader")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(10)

        # 名称标签允许换行，并用工具提示保留可能被布局压缩的完整名称。
        name_label = QLabel(self.summary.name, header_widget)
        name_label.setObjectName("proxyCardTitle")
        name_label.setWordWrap(True)
        name_label.setToolTip(self.summary.name)
        # 名称获得标题区剩余宽度，同时维持系统建议高度。
        name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        # 类型徽标携带同一规范化属性，以便按代理类型应用差异化样式。
        type_badge = QLabel(self.summary.display_type, header_widget)
        type_badge.setObjectName("proxyTypeBadge")
        type_badge.setProperty("proxyType", self.summary.proxy_type)
        # 居中文字并限定徽标尺寸，保持不同类型卡片的标题区一致。
        type_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_badge.setFixedHeight(30)
        type_badge.setMinimumWidth(64)

        # 名称优先伸展，徽标紧随其后并保持自身最小宽度。
        header_layout.addWidget(name_label, stretch=1)
        header_layout.addWidget(type_badge)

        # 一像素分隔线明确区分卡片标题区与正文区。
        divider = QFrame(self)
        divider.setObjectName("proxyCardDivider")
        divider.setFixedHeight(1)

        # 正文使用网格按行对齐字段名和值。
        body_widget = QWidget(self)
        body_widget.setObjectName("proxyCardBody")
        body_layout = QGridLayout(body_widget)
        body_layout.setContentsMargins(16, 14, 16, 16)
        body_layout.setHorizontalSpacing(12)
        body_layout.setVerticalSpacing(12)

        # 有摘要字段时逐行创建键和值标签。
        if self.summary.fields:
            for row, (label, value) in enumerate(self.summary.fields):
                # 字段名使用统一样式并在左侧单元格中居中。
                key_label = QLabel(label, body_widget)
                key_label.setObjectName("proxyFieldKey")
                key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # 字段值允许鼠标选取，便于复制端口等配置内容。
                value_label = QLabel(value, body_widget)
                value_label.setObjectName("proxyFieldValue")
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                value_label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                )

                # 将本行字段名和值分别放入网格的两列。
                body_layout.addWidget(key_label, row, 0)
                body_layout.addWidget(value_label, row, 1)
        else:
            # 未知类型没有可展示字段时，以空白伸展行维持正文区域高度。
            body_layout.setRowStretch(0, 1)

        # 两列分配相同伸展权重，使字段名和值在卡片内均衡排布。
        body_layout.setColumnStretch(0, 1)
        body_layout.setColumnStretch(1, 1)

        # 按视觉顺序装入标题、分隔线和可伸展正文。
        card_layout.addWidget(header_widget)
        card_layout.addWidget(divider)
        card_layout.addWidget(body_widget, stretch=1)


class FrpcConfigManagerPanel(QWidget):
    """读取 frpc 代理配置，并在可滚动的自适应卡片网格中展示。"""

    # 将加载、提示和错误消息同步给外层页面或主窗口。
    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """初始化配置服务、工具栏、滚动网格及首批配置卡片。"""
        # 完成 QWidget 基类初始化，使全部子控件归当前面板管理。
        super().__init__(parent)
        # 配置服务负责读取磁盘文本，卡片列表保存当前已构造的视图对象。
        self.config_service = FrpcConfigService()
        self.card_widgets: list[FrpcProxyCard] = []
        # 记录最近一次布局列数，以跳过无必要的重复网格重排。
        self.current_columns = 0

        # 工具栏按钮保留未来新增配置流程的入口。
        self.add_label_button = QPushButton("添加配置", self)
        self.add_label_button.setObjectName("addConfigTextButton")

        # 滚动区域允许内部容器跟随视口调整，并使用统一边框样式。
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("frpcConfigScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.StyledPanel)

        # 网格容器承载所有配置卡片，其留白和间距控制卡片之间的视觉节奏。
        self.grid_container = QWidget(self.scroll_area)
        self.grid_container.setObjectName("frpcConfigGridContainer")
        self.cards_layout = QGridLayout(self.grid_container)
        self.cards_layout.setContentsMargins(54, 36, 54, 36)
        self.cards_layout.setHorizontalSpacing(34)
        self.cards_layout.setVerticalSpacing(34)

        # 没有有效代理配置时，用居中的空状态标签替代卡片列表。
        self.empty_label = QLabel("暂无连接配置", self.grid_container)
        self.empty_label.setObjectName("emptyConfigLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 行内消息持续展示最近一次加载或操作的结果。
        self.message_label = QLabel("", self)
        self.message_label.setObjectName("inlineMessage")
        self.message_label.setWordWrap(True)

        # 控件创建后依次组织布局、连接交互，并加载磁盘中的初始配置。
        self._build_ui()
        self._connect_signals()
        self.load_config()

    # 该 Qt 回调沿用框架传入的动态事件参数，因此保留未标注参数的类型检查豁免。
    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        """在面板尺寸变化后按最新可用宽度重新计算卡片列数。"""
        # 保留 QWidget 默认尺寸事件处理，确保框架内部状态正常更新。
        super().resizeEvent(event)
        # 尺寸变化可能跨越单双列阈值，因此尝试重建网格。
        self._rebuild_cards_grid()

    def _build_ui(self) -> None:
        """构建顶部工具栏、可滚动卡片区和底部消息区。"""
        # 主布局纵向排列三个功能区，并去除面板外侧额外边距。
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(18)

        # 工具栏框架为新增配置入口提供独立的样式表面。
        toolbar_frame = QFrame(self)
        toolbar_frame.setObjectName("frpcManagerToolbar")
        toolbar_frame.setFrameShape(QFrame.Shape.StyledPanel)

        # 弹性占位把新增按钮推到工具栏最右侧。
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(18, 10, 16, 10)
        toolbar_layout.setSpacing(10)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.add_label_button)

        # 将网格容器设为滚动区域的唯一内容控件。
        self.scroll_area.setWidget(self.grid_container)

        # 滚动区取得主要伸展空间，工具栏与消息区按内容高度展示。
        main_layout.addWidget(toolbar_frame)
        main_layout.addWidget(self.scroll_area, stretch=1)
        main_layout.addWidget(self.message_label)

    def _connect_signals(self) -> None:
        """把新增配置按钮连接到当前的流程说明处理器。"""
        # 点击入口后由面板统一展示尚待确认的新增方式。
        self.add_label_button.clicked.connect(self._handle_add_clicked)

    def load_config(self) -> None:
        """读取当前 frpc.toml，并将其中的代理条目渲染为卡片。"""
        # 读取、解析和摘要转换属于一次完整加载过程，任一步失败都统一清空旧卡片。
        try:
            # 配置服务返回原始 TOML 文本，再由 tomlkit 构造可查询文档。
            config_text = self.config_service.load_text()
            document = tomlkit.parse(config_text)
            # 缺少 proxies 键时按空集合处理，避免把正常空配置视为错误。
            proxies = document.get("proxies", [])
            # 兼容单个映射与代理序列，并逐条转换为纯展示摘要。
            summaries = [
                self._summary_from_proxy(proxy)
                for proxy in self._iter_proxy_objects(proxies)
            ]
        except (OSError, TOMLKitError, TypeError, ValueError) as error:
            # 文件、格式或结构错误发生时移除可能过期的卡片并报告具体原因。
            self._set_cards([])
            self._show_error(f"读取 frpc 配置失败：{error}")
            return

        # 加载成功后一次性替换卡片，并报告实际解析出的连接数量。
        self._set_cards(summaries)
        self._show_info(f"已加载 {len(summaries)} 个连接配置")

    def _iter_proxy_objects(self, proxies: Any) -> Iterable[Any]:
        """把空值、单个代理映射或代理序列统一转换为可迭代对象。"""
        # 显式空值表示没有配置，返回空元组便于调用方直接遍历。
        if proxies is None:
            return ()
        # 单个字典本身可迭代的是键，因此包装成单元素元组以保留完整代理对象。
        if isinstance(proxies, dict):
            return (proxies,)
        # 列表或 tomlkit 容器已经可按代理条目遍历，原样返回。
        return proxies

    def _summary_from_proxy(self, proxy: Any) -> FrpcProxySummary:
        """从一条原始代理配置提取类型、名称及适合卡片展示的字段。"""
        # 类型和角色统一转为小写，避免配置大小写差异影响分支选择。
        proxy_type = self._text(proxy, "type", "unknown").lower()
        role = self._text(proxy, "role", "").lower()
        # 缺少名称时使用稳定的中文占位，保证卡片标题始终可读。
        name = self._text(proxy, "name", "未命名连接")

        # XTCP 在界面中归类为 P2P，并按服务端或访问端角色选择字段。
        if proxy_type == "xtcp":
            display_type = "P2P"
            normalized_type = "p2p"
            fields = self._p2p_fields(proxy, role)
        # TCP 卡片展示本地端口和远程端口。
        elif proxy_type == "tcp":
            display_type = "TCP"
            normalized_type = "tcp"
            fields = self._port_fields(proxy)
        # UDP 与 TCP 使用相同端口字段结构，但保留独立类型和样式标识。
        elif proxy_type == "udp":
            display_type = "UDP"
            normalized_type = "udp"
            fields = self._port_fields(proxy)
        else:
            # 未识别类型仅展示大写类型名，不臆测其专有字段。
            display_type = proxy_type.upper() if proxy_type else "UNKNOWN"
            normalized_type = "unknown"
            fields = ()

        # 将分支计算出的展示信息封装为不可变摘要，供卡片安全复用。
        return FrpcProxySummary(
            name=name,
            proxy_type=normalized_type,
            display_type=display_type,
            fields=fields,
        )

    def _port_fields(self, proxy: Any) -> tuple[tuple[str, str], ...]:
        """提取普通端口代理的本地端口与远程端口展示字段。"""
        # 缺失端口统一显示短横线，保持两行字段结构稳定。
        return (
            ("localport", self._text(proxy, "localPort", "-")),
            ("remoteport", self._text(proxy, "remotePort", "-")),
        )

    def _p2p_fields(self, proxy: Any, role: str) -> tuple[tuple[str, str], ...]:
        """按 P2P 代理角色提取访问端或服务端所需的展示字段。"""
        # 访问端关心目标服务名称和本地绑定端口。
        if role == "p2p_visitor":
            return (
                ("server", self._text(proxy, "serverName", "-")),
                ("bindport", self._text(proxy, "bindPort", "-")),
            )
        # 其他 P2P 角色展示本地端口，并仅说明密钥是否存在以避免泄露敏感值。
        return (
            ("localport", self._text(proxy, "localPort", "-")),
            ("secret", "已设置" if self._text(proxy, "secretKey", "") else "-"),
        )

    def _text(self, source: Any, key: str, default: str) -> str:
        """从类映射对象安全取值，并将空值规范化为指定默认文本。"""
        # 通过 get 兼容字典和 tomlkit 表；非映射对象则回退到默认值。
        try:
            value = source.get(key, default)
        except AttributeError:
            value = default
        # None 与空字符串都视为缺失，避免卡片出现不可见内容。
        if value is None or value == "":
            return default
        # 统一转为字符串，使数字端口等 TOML 标量可以直接交给 QLabel。
        return str(value)

    def _set_cards(self, summaries: list[FrpcProxySummary]) -> None:
        """移除旧卡片，根据新摘要列表创建卡片并强制重建网格。"""
        # 解除旧卡片与容器的父子关系，让 Qt 安全回收不再使用的控件。
        for card in self.card_widgets:
            card.setParent(None)
        # 每条摘要对应一个以网格容器为父对象的新卡片。
        self.card_widgets = [FrpcProxyCard(summary, self.grid_container) for summary in summaries]
        # 即使列数未变也需重建，确保新卡片真正加入布局。
        self._rebuild_cards_grid(force=True)

    def _rebuild_cards_grid(self, *, force: bool = False) -> None:
        """按可用宽度选择一列或两列，并重新排列当前全部卡片。"""
        # 视口和面板宽度取较大值，避免初始化阶段视口尚未完成布局而误判列数。
        available_width = max(self.scroll_area.viewport().width(), self.width())
        # 650 像素以上使用双列，否则退化为单列保证卡片可读宽度。
        columns = 2 if available_width >= 650 else 1
        # 非强制调用且列数未变化时保留现有布局，减少尺寸事件中的重复工作。
        if not force and columns == self.current_columns:
            return
        # 保存本次列数，供后续尺寸变化快速判断。
        self.current_columns = columns

        # 先从布局中逐项取出并隐藏控件，避免旧位置与新位置同时参与排版。
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            # 布局项也可能是间隔项，因此只对真实控件执行隐藏。
            if widget is not None:
                widget.hide()

        # 没有卡片时让空状态横跨当前全部列并居中显示。
        if not self.card_widgets:
            self.empty_label.show()
            self.cards_layout.addWidget(
                self.empty_label,
                0,
                0,
                1,
                columns,
                Qt.AlignmentFlag.AlignCenter,
            )
            return

        # 存在配置时隐藏空状态，再按行优先顺序放回所有卡片。
        self.empty_label.hide()
        for index, card in enumerate(self.card_widgets):
            # 整除得到行号，取余得到当前单双列布局中的列号。
            row = index // columns
            column = index % columns
            # 重新显示此前隐藏的卡片，并加入计算出的网格单元格。
            card.show()
            self.cards_layout.addWidget(card, row, column)

        # 先清除最多三列可能遗留的伸展权重，避免从旧布局继承无效列宽。
        for column in range(3):
            self.cards_layout.setColumnStretch(column, 0)
        # 仅为本次实际使用的列设置等比例伸展，使卡片均匀占满横向空间。
        for column in range(columns):
            self.cards_layout.setColumnStretch(column, 1)

    def _handle_add_clicked(self) -> None:
        """提示用户新增配置流程尚待确定，并同步展示说明消息。"""
        # 使用同一段说明文本，确保行内提示与弹窗内容完全一致。
        message = "添加配置流程尚未确定：请确认是新建表单、导入 JSON 档案，还是直接编辑 frpc.toml。"
        self._show_info(message)
        # 弹窗使当前尚不可执行的操作得到即时、明确反馈。
        QMessageBox.information(self, "需要确认", message)

    def _show_info(self, message: str) -> None:
        """在面板内显示普通提示，并将相同内容广播给外层界面。"""
        # 行内标签保留消息，信号则供主窗口同步全局状态提示。
        self.message_label.setText(message)
        self.status_message_changed.emit(message)

    def _show_error(self, message: str) -> None:
        """在面板内显示错误提示，并将相同内容广播给外层界面。"""
        # 错误与普通消息沿用相同展示通道，由调用方决定具体文案。
        self.message_label.setText(message)
        self.status_message_changed.emit(message)
