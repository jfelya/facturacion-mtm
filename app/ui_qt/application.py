"""Qt application bootstrap."""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow
from .theme import icons
from .theme.qss import apply_theme

APP_VERSION = "3.0.0"


def _font():
    families = set(QFontDatabase.families())
    for name in ("Segoe UI Variable Text", "Segoe UI", "Arial"):
        if name in families:
            font = QFont(name)
            font.setPixelSize(13)
            font.setWeight(QFont.Weight.Medium)
            return font
    font = QFont()
    font.setPixelSize(13)
    return font


def main():
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Facturación MTM")
    app.setApplicationDisplayName("Facturación MTM")
    app.setOrganizationName("Disma Transportation")
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setFont(_font())
    app.setWindowIcon(icons.icon("icon"))
    apply_theme(app, "dark")

    window = MainWindow(app)
    window.showMaximized()
    return app.exec()
