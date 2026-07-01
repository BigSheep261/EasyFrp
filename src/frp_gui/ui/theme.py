"""Application theme variants for the EasyFrp desktop UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from PyQt6.QtWidgets import QApplication, QWidget
from qt_material import apply_stylesheet


DEFAULT_THEME_KEY = "ops_dark"


@dataclass(frozen=True)
class ThemeVariant:
    """A selectable visual direction for the application."""

    key: str
    name: str
    description: str
    material_theme: str
    tokens: Mapping[str, str]

    @property
    def stylesheet(self) -> str:
        """Return the custom QSS layer for this variant."""
        return _build_qss(self.tokens)


THEME_VARIANTS: tuple[ThemeVariant, ...] = (
    ThemeVariant(
        key="ops_dark",
        name="深色运维",
        description="默认方案：深色高对比，强调运行状态、日志和长时间使用的稳定感。",
        material_theme="dark_blue.xml",
        tokens={
            "window": "#020617",
            "sidebar": "#08111f",
            "topbar": "#07111f",
            "page": "#0b1120",
            "logo_bg": "#08111f",
            "surface": "#111827",
            "surface_alt": "#172033",
            "editor": "#050a14",
            "editor_text": "#dbeafe",
            "text": "#f8fafc",
            "muted": "#94a3b8",
            "subtle": "#64748b",
            "border": "#263247",
            "border_strong": "#334155",
            "primary": "#38bdf8",
            "primary_hover": "#0ea5e9",
            "on_primary": "#03111f",
            "accent": "#22c55e",
            "accent_soft": "rgba(34, 197, 94, 0.12)",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "button": "#172033",
            "button_hover": "#1f2a44",
            "input": "#0f172a",
            "selection": "#075985",
            "switch_off": "#475569",
            "disabled": "#334155",
        },
    ),
    ThemeVariant(
        key="control_light",
        name="明亮控制台",
        description="白天办公方案：清爽白底、蓝色主操作、橙色强调，适合快速配置。",
        material_theme="light_blue.xml",
        tokens={
            "window": "#e9eff8",
            "sidebar": "#f8fafc",
            "topbar": "#ffffff",
            "page": "#f3f6fb",
            "logo_bg": "#0f172a",
            "surface": "#ffffff",
            "surface_alt": "#edf3fb",
            "editor": "#fbfdff",
            "editor_text": "#102033",
            "text": "#0f172a",
            "muted": "#475569",
            "subtle": "#64748b",
            "border": "#dbe4f0",
            "border_strong": "#bfd0e6",
            "primary": "#2563eb",
            "primary_hover": "#1d4ed8",
            "on_primary": "#ffffff",
            "accent": "#ea580c",
            "accent_soft": "rgba(37, 99, 235, 0.10)",
            "warning": "#b45309",
            "danger": "#dc2626",
            "button": "#f8fafc",
            "button_hover": "#edf3fb",
            "input": "#ffffff",
            "selection": "#bfdbfe",
            "switch_off": "#94a3b8",
            "disabled": "#cbd5e1",
        },
    ),
    ThemeVariant(
        key="terminal_compact",
        name="终端紧凑",
        description="日志/配置方案：更像控制台，视觉密度更高，青绿状态和琥珀操作更醒目。",
        material_theme="dark_cyan.xml",
        tokens={
            "window": "#060808",
            "sidebar": "#071010",
            "topbar": "#081211",
            "page": "#0b1212",
            "logo_bg": "#050808",
            "surface": "#101a19",
            "surface_alt": "#162221",
            "editor": "#030606",
            "editor_text": "#d1fae5",
            "text": "#ecfeff",
            "muted": "#9fb6b2",
            "subtle": "#718985",
            "border": "#24403d",
            "border_strong": "#315b55",
            "primary": "#2dd4bf",
            "primary_hover": "#14b8a6",
            "on_primary": "#031312",
            "accent": "#fbbf24",
            "accent_soft": "rgba(45, 212, 191, 0.12)",
            "warning": "#f59e0b",
            "danger": "#f87171",
            "button": "#14211f",
            "button_hover": "#1b302d",
            "input": "#0b1514",
            "selection": "#115e59",
            "switch_off": "#3f5f5a",
            "disabled": "#2c403d",
        },
    ),
)


def list_theme_variants() -> tuple[ThemeVariant, ...]:
    """Return all selectable UI variants in display order."""
    return THEME_VARIANTS


def get_theme_variant(theme_key: str | None) -> ThemeVariant:
    """Resolve a saved or requested theme key to a known variant."""
    for variant in THEME_VARIANTS:
        if variant.key == theme_key:
            return variant
    return THEME_VARIANTS[0]


def get_saved_theme_key() -> str:
    """Read the user's saved theme choice."""
    from frp_gui.core.easyfrp_config_service import EasyfrpConfigService

    try:
        value = EasyfrpConfigService().load_settings().get("theme_key")
    except (OSError, ValueError):
        return DEFAULT_THEME_KEY
    return value if isinstance(value, str) else DEFAULT_THEME_KEY


def apply_app_theme(
    application: QApplication,
    theme_key: str | None = None,
    *,
    persist: bool = False,
) -> ThemeVariant:
    """Apply a qt-material base theme plus EasyFrp's custom polish layer."""
    variant = get_theme_variant(theme_key or get_saved_theme_key())
    apply_stylesheet(application, theme=variant.material_theme)
    application.setStyleSheet(f"{application.styleSheet()}\n{variant.stylesheet}")
    application.setProperty("easyfrpTheme", variant.key)

    if persist:
        from frp_gui.core.easyfrp_config_service import EasyfrpConfigService

        service = EasyfrpConfigService()
        settings = service.load_settings()
        settings["theme_key"] = variant.key
        service.save_settings(settings)

    return variant


def set_widget_state(widget: QWidget, state: str) -> None:
    """Set a dynamic QSS state and refresh one widget."""
    widget.setProperty("state", state)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def _build_qss(tokens: Mapping[str, str]) -> str:
    return f"""
    QMainWindow {{
        background-color: {tokens["window"]};
    }}

    QWidget {{
        font-family: "Microsoft YaHei UI", "Segoe UI", "PingFang SC", "Noto Sans CJK SC", sans-serif;
    }}

    QWidget#sidebarContainer {{
        background-color: {tokens["sidebar"]};
        border-right: 1px solid {tokens["border"]};
    }}

    QLabel#logoLabel {{
        border: 1px solid {tokens["border"]};
        border-radius: 8px;
        background-color: {tokens["logo_bg"]};
        padding: 4px;
    }}

    QWidget#contentContainer,
    QStackedWidget#pageStack {{
        background-color: {tokens["page"]};
    }}

    QWidget#windowControlsContainer {{
        background-color: {tokens["topbar"]};
        border-bottom: 1px solid {tokens["border"]};
    }}

    QPushButton#windowButton,
    QPushButton#closeButton {{
        min-width: 34px;
        min-height: 28px;
        border: none;
        border-radius: 4px;
        padding: 0;
        color: {tokens["muted"]};
        background: transparent;
        font-size: 14px;
    }}

    QPushButton#windowButton:hover {{
        color: {tokens["text"]};
        background-color: {tokens["button_hover"]};
    }}

    QPushButton#closeButton:hover {{
        color: #ffffff;
        background-color: {tokens["danger"]};
    }}

    QLabel#pageTitle {{
        color: {tokens["text"]};
        font-size: 22px;
        font-weight: 700;
    }}

    QLabel#pageDescription,
    QLabel#themeDescription {{
        color: {tokens["muted"]};
        font-size: 13px;
    }}

    QLabel#pathLabel {{
        color: {tokens["muted"]};
        font-size: 12px;
    }}

    QLabel#statusBadge {{
        color: {tokens["text"]};
        font-weight: 600;
    }}

    QListWidget#sidebarNavigation {{
        background: transparent;
        border: none;
        color: {tokens["muted"]};
        padding: 6px 0 0 0;
        outline: none;
    }}

    QListWidget#sidebarNavigation::item {{
        min-height: 40px;
        padding: 8px 12px;
        margin: 2px 0;
        border-radius: 6px;
        color: {tokens["muted"]};
    }}

    QListWidget#sidebarNavigation::item:hover {{
        background-color: {tokens["button_hover"]};
        color: {tokens["text"]};
    }}

    QListWidget#sidebarNavigation::item:selected {{
        background-color: {tokens["primary"]};
        color: {tokens["on_primary"]};
        font-weight: 600;
    }}

    QFrame#mainMessageFrame,
    QFrame#controlSurface,
    QFrame#toolbarSurface,
    QFrame#formSurface {{
        border: 1px solid {tokens["border"]};
        border-radius: 8px;
        background-color: {tokens["surface"]};
    }}

    QFrame#mainMessageFrame {{
        background-color: {tokens["accent_soft"]};
    }}

    QLabel#mainMessageTitle {{
        color: {tokens["accent"]};
        font-weight: 700;
        font-size: 12px;
    }}

    QLabel#mainMessageText {{
        color: {tokens["muted"]};
        font-size: 12px;
    }}

    QLabel#inlineMessage {{
        color: {tokens["muted"]};
        font-size: 13px;
    }}

    QLabel#inlineMessage[state="info"] {{
        color: {tokens["accent"]};
    }}

    QLabel#inlineMessage[state="error"] {{
        color: {tokens["danger"]};
    }}

    QLineEdit,
    QSpinBox,
    QComboBox {{
        min-height: 34px;
        padding: 5px 10px;
        border: 1px solid {tokens["border"]};
        border-radius: 6px;
        background-color: {tokens["input"]};
        color: {tokens["text"]};
        selection-background-color: {tokens["selection"]};
    }}

    QLineEdit:focus,
    QSpinBox:focus,
    QComboBox:focus {{
        border: 1px solid {tokens["primary"]};
    }}

    QComboBox::drop-down,
    QSpinBox::up-button,
    QSpinBox::down-button {{
        border: none;
        width: 22px;
    }}

    QTextEdit#logView,
    QPlainTextEdit#configEditor {{
        border: 1px solid {tokens["border"]};
        border-radius: 8px;
        padding: 10px;
        background-color: {tokens["editor"]};
        color: {tokens["editor_text"]};
        selection-background-color: {tokens["selection"]};
        font-family: "Cascadia Mono", "Consolas", monospace;
        font-size: 12px;
    }}

    QPushButton {{
        min-height: 34px;
        padding: 6px 14px;
        border: 1px solid {tokens["border"]};
        border-radius: 6px;
        background-color: {tokens["button"]};
        color: {tokens["text"]};
        font-weight: 600;
    }}

    QPushButton:hover {{
        border-color: {tokens["border_strong"]};
        background-color: {tokens["button_hover"]};
    }}

    QPushButton:pressed {{
        background-color: {tokens["surface_alt"]};
    }}

    QPushButton:disabled {{
        color: {tokens["subtle"]};
        background-color: {tokens["disabled"]};
        border-color: {tokens["disabled"]};
    }}

    QPushButton#primaryButton {{
        color: {tokens["on_primary"]};
        background-color: {tokens["primary"]};
        border-color: {tokens["primary"]};
    }}

    QPushButton#primaryButton:hover {{
        background-color: {tokens["primary_hover"]};
        border-color: {tokens["primary_hover"]};
    }}

    QPushButton#secondaryButton {{
        color: {tokens["text"]};
        background-color: {tokens["button"]};
    }}

    QCheckBox#switchButton {{
        min-height: 34px;
        spacing: 10px;
        color: {tokens["text"]};
        font-size: 14px;
        font-weight: 600;
    }}

    QCheckBox#switchButton::indicator {{
        width: 46px;
        height: 24px;
        border-radius: 12px;
        border: 1px solid {tokens["border_strong"]};
        background-color: {tokens["switch_off"]};
        image: none;
    }}

    QCheckBox#switchButton::indicator:checked {{
        border-color: {tokens["accent"]};
        background-color: {tokens["accent"]};
    }}

    QCheckBox#switchButton::indicator:disabled {{
        border-color: {tokens["disabled"]};
        background-color: {tokens["disabled"]};
    }}
    """
