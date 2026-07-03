"""Card-based frpc configuration management panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import tomlkit
from tomlkit.exceptions import TOMLKitError

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

from frp_gui.backend.frpc.config_service import FrpcConfigService


@dataclass(frozen=True)
class FrpcProxySummary:
    """Display-ready summary for one frpc proxy entry."""

    name: str
    proxy_type: str
    display_type: str
    fields: tuple[tuple[str, str], ...]


class FrpcProxyCard(QFrame):
    """A compact card that mirrors one frpc connection config."""

    def __init__(self, summary: FrpcProxySummary, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.summary = summary
        self.setObjectName("frpcProxyCard")
        self.setProperty("proxyType", summary.proxy_type)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(260, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._build_ui()

    def _build_ui(self) -> None:
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        header_widget = QWidget(self)
        header_widget.setObjectName("proxyCardHeader")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(10)

        name_label = QLabel(self.summary.name, header_widget)
        name_label.setObjectName("proxyCardTitle")
        name_label.setWordWrap(True)
        name_label.setToolTip(self.summary.name)
        name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        type_badge = QLabel(self.summary.display_type, header_widget)
        type_badge.setObjectName("proxyTypeBadge")
        type_badge.setProperty("proxyType", self.summary.proxy_type)
        type_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_badge.setFixedHeight(30)
        type_badge.setMinimumWidth(64)

        header_layout.addWidget(name_label, stretch=1)
        header_layout.addWidget(type_badge)

        divider = QFrame(self)
        divider.setObjectName("proxyCardDivider")
        divider.setFixedHeight(1)

        body_widget = QWidget(self)
        body_widget.setObjectName("proxyCardBody")
        body_layout = QGridLayout(body_widget)
        body_layout.setContentsMargins(16, 14, 16, 16)
        body_layout.setHorizontalSpacing(12)
        body_layout.setVerticalSpacing(12)

        if self.summary.fields:
            for row, (label, value) in enumerate(self.summary.fields):
                key_label = QLabel(label, body_widget)
                key_label.setObjectName("proxyFieldKey")
                key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                value_label = QLabel(value, body_widget)
                value_label.setObjectName("proxyFieldValue")
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                value_label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                )

                body_layout.addWidget(key_label, row, 0)
                body_layout.addWidget(value_label, row, 1)
        else:
            body_layout.setRowStretch(0, 1)

        body_layout.setColumnStretch(0, 1)
        body_layout.setColumnStretch(1, 1)

        card_layout.addWidget(header_widget)
        card_layout.addWidget(divider)
        card_layout.addWidget(body_widget, stretch=1)


class FrpcConfigManagerPanel(QWidget):
    """Read and display frpc proxy configs in a scrollable card grid."""

    status_message_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config_service = FrpcConfigService()
        self.card_widgets: list[FrpcProxyCard] = []
        self.current_columns = 0

        self.add_label_button = QPushButton("添加配置", self)
        self.add_label_button.setObjectName("addConfigTextButton")

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("frpcConfigScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.StyledPanel)

        self.grid_container = QWidget(self.scroll_area)
        self.grid_container.setObjectName("frpcConfigGridContainer")
        self.cards_layout = QGridLayout(self.grid_container)
        self.cards_layout.setContentsMargins(54, 36, 54, 36)
        self.cards_layout.setHorizontalSpacing(34)
        self.cards_layout.setVerticalSpacing(34)

        self.empty_label = QLabel("暂无连接配置", self.grid_container)
        self.empty_label.setObjectName("emptyConfigLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("inlineMessage")
        self.message_label.setWordWrap(True)

        self._build_ui()
        self._connect_signals()
        self.load_config()

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self._rebuild_cards_grid()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(18)

        toolbar_frame = QFrame(self)
        toolbar_frame.setObjectName("frpcManagerToolbar")
        toolbar_frame.setFrameShape(QFrame.Shape.StyledPanel)

        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(18, 10, 16, 10)
        toolbar_layout.setSpacing(10)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.add_label_button)

        self.scroll_area.setWidget(self.grid_container)

        main_layout.addWidget(toolbar_frame)
        main_layout.addWidget(self.scroll_area, stretch=1)
        main_layout.addWidget(self.message_label)

    def _connect_signals(self) -> None:
        self.add_label_button.clicked.connect(self._handle_add_clicked)

    def load_config(self) -> None:
        """Load current frpc.toml and render the proxy cards."""
        try:
            config_text = self.config_service.load_text()
            document = tomlkit.parse(config_text)
            proxies = document.get("proxies", [])
            summaries = [
                self._summary_from_proxy(proxy)
                for proxy in self._iter_proxy_objects(proxies)
            ]
        except (OSError, TOMLKitError, TypeError, ValueError) as error:
            self._set_cards([])
            self._show_error(f"读取 frpc 配置失败：{error}")
            return

        self._set_cards(summaries)
        self._show_info(f"已加载 {len(summaries)} 个连接配置")

    def _iter_proxy_objects(self, proxies: Any) -> Iterable[Any]:
        if proxies is None:
            return ()
        if isinstance(proxies, dict):
            return (proxies,)
        return proxies

    def _summary_from_proxy(self, proxy: Any) -> FrpcProxySummary:
        proxy_type = self._text(proxy, "type", "unknown").lower()
        role = self._text(proxy, "role", "").lower()
        name = self._text(proxy, "name", "未命名连接")

        if proxy_type == "xtcp":
            display_type = "P2P"
            normalized_type = "p2p"
            fields = self._p2p_fields(proxy, role)
        elif proxy_type == "tcp":
            display_type = "TCP"
            normalized_type = "tcp"
            fields = self._port_fields(proxy)
        elif proxy_type == "udp":
            display_type = "UDP"
            normalized_type = "udp"
            fields = self._port_fields(proxy)
        else:
            display_type = proxy_type.upper() if proxy_type else "UNKNOWN"
            normalized_type = "unknown"
            fields = ()

        return FrpcProxySummary(
            name=name,
            proxy_type=normalized_type,
            display_type=display_type,
            fields=fields,
        )

    def _port_fields(self, proxy: Any) -> tuple[tuple[str, str], ...]:
        return (
            ("localport", self._text(proxy, "localPort", "-")),
            ("remoteport", self._text(proxy, "remotePort", "-")),
        )

    def _p2p_fields(self, proxy: Any, role: str) -> tuple[tuple[str, str], ...]:
        if role == "p2p_visitor":
            return (
                ("server", self._text(proxy, "serverName", "-")),
                ("bindport", self._text(proxy, "bindPort", "-")),
            )
        return (
            ("localport", self._text(proxy, "localPort", "-")),
            ("secret", "已设置" if self._text(proxy, "secretKey", "") else "-"),
        )

    def _text(self, source: Any, key: str, default: str) -> str:
        try:
            value = source.get(key, default)
        except AttributeError:
            value = default
        if value is None or value == "":
            return default
        return str(value)

    def _set_cards(self, summaries: list[FrpcProxySummary]) -> None:
        for card in self.card_widgets:
            card.setParent(None)
        self.card_widgets = [FrpcProxyCard(summary, self.grid_container) for summary in summaries]
        self._rebuild_cards_grid(force=True)

    def _rebuild_cards_grid(self, *, force: bool = False) -> None:
        available_width = max(self.scroll_area.viewport().width(), self.width())
        columns = 2 if available_width >= 650 else 1
        if not force and columns == self.current_columns:
            return
        self.current_columns = columns

        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()

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

        self.empty_label.hide()
        for index, card in enumerate(self.card_widgets):
            row = index // columns
            column = index % columns
            card.show()
            self.cards_layout.addWidget(card, row, column)

        for column in range(3):
            self.cards_layout.setColumnStretch(column, 0)
        for column in range(columns):
            self.cards_layout.setColumnStretch(column, 1)

    def _handle_add_clicked(self) -> None:
        message = "添加配置流程尚未确定：请确认是新建表单、导入 JSON 档案，还是直接编辑 frpc.toml。"
        self._show_info(message)
        QMessageBox.information(self, "需要确认", message)

    def _show_info(self, message: str) -> None:
        self.message_label.setText(message)
        self.status_message_changed.emit(message)

    def _show_error(self, message: str) -> None:
        self.message_label.setText(message)
        self.status_message_changed.emit(message)
