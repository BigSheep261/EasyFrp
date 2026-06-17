"""Qt application bootstrap."""

import sys
from collections.abc import Sequence

from PyQt6.QtWidgets import QApplication

from frp_gui.core.paths import ensure_runtime_directories
from frp_gui.ui.main_window import MainWindow


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create and configure the Qt application instance."""
    arguments = list(argv) if argv is not None else sys.argv
    application = QApplication(arguments)
    application.setApplicationName("EasyFrp")
    application.setOrganizationName("EasyFrp")
    return application


def run(argv: Sequence[str] | None = None) -> int:
    """Start the desktop application event loop."""
    ensure_runtime_directories()
    application = create_application(argv)
    window = MainWindow()
    window.show()
    return application.exec()
