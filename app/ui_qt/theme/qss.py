"""QSS generated from the Qt token module.

Qt style sheets have no variables, so one complete stylesheet is generated per
theme and applied to the QApplication.  The static structure lives here; all
colour values come from `tokens.py`.
"""
from string import Template

from PySide6.QtGui import QColor, QPalette

from .tokens import THEMES


QSS = r"""
QWidget {
    color: $text;
    font-family: "Segoe UI Variable Text", "Segoe UI", Arial;
    font-size: 13px;
}
QMainWindow, QWidget#Root {
    background: $background;
}
QFrame#TopBar {
    background: $surface;
    border: 0;
    border-bottom: 1px solid $border;
}
QFrame#Sidebar {
    background: $surface;
    border: 0;
    border-right: 1px solid $border;
}
QScrollArea#SidebarScroll, QWidget#SidebarContent {
    background: transparent;
    border: 0;
}
QFrame#Card {
    background: $surface;
    border: 1px solid $border;
    border-radius: 8px;
}
QFrame#SummaryStrip {
    background: $background;
    border: 0;
}
QFrame#DetailDrawer {
    background: $surface;
    border: 1px solid $border;
    border-radius: 8px;
}
QFrame#HLine {
    background: $border;
    border: 0;
    max-height: 1px;
    min-height: 1px;
}
QLabel#PageTitle {
    font-size: 20px;
    font-weight: 600;
    color: $text;
}
QLabel#Subtitle {
    font-size: 11px;
    color: $text_dim;
}
QLabel#SectionTitle {
    font-size: 12px;
    font-weight: 600;
    color: $text_dim;
}
QLabel#PickerTitle {
    font-size: 12px;
    font-weight: 600;
    color: $text;
}
QLabel#Hint {
    font-size: 11px;
    color: $text_dim;
}
QLabel#FieldLabel {
    font-size: 11px;
    color: $text_dim;
}
QLabel#FieldValue {
    font-size: 12px;
    color: $text;
}
QLabel#Version {
    font-size: 11px;
    color: $text_dim;
}
QPushButton {
    background: $surface;
    color: $text;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 7px 14px;
    min-height: 18px;
}
QPushButton:hover {
    background: $surface_alt;
    border-color: $accent;
}
QPushButton:pressed {
    background: $selection;
}
QPushButton:focus {
    border: 2px solid $accent;
    padding: 6px 13px;
}
QPushButton:disabled {
    color: $text_dim;
    border-color: $border;
    background: $surface;
}
QPushButton[role="primary"] {
    background: $accent;
    color: $accent_fg;
    border-color: $accent;
    font-weight: 600;
    min-width: 112px;
}
QPushButton[role="primary"]:hover {
    background: $accent_hover;
    border-color: $accent_hover;
}
QPushButton[role="primary"]:pressed {
    background: $accent_pressed;
    border-color: $accent_pressed;
}
QPushButton[role="primary"]:disabled {
    background: $border;
    color: $text_dim;
    border-color: $border;
}
QPushButton[role="ghost"] {
    background: transparent;
    border-color: transparent;
    color: $text_dim;
}
QPushButton[role="ghost"]:hover {
    background: $surface_alt;
    color: $text;
}
QPushButton[chip="true"] {
    background: $surface;
    border: 1px solid $border;
    border-radius: 11px;
    padding: 3px 10px;
    min-height: 16px;
    font-size: 11px;
}
QPushButton[chip="true"]:hover {
    border-color: $accent;
}
QPushButton[chip="true"][active="true"] {
    background: $accent;
    color: $accent_fg;
    border-color: $accent;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px;
}
QToolButton:hover {
    background: $surface_alt;
    border-color: $border;
}
QToolButton:pressed {
    background: $selection;
}
QLineEdit, QComboBox, QSpinBox {
    background: $surface;
    color: $text;
    border: 1px solid $border;
    border-radius: 5px;
    padding: 6px 8px;
    min-height: 20px;
    selection-background-color: $accent;
    selection-color: $accent_fg;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 2px solid $accent;
    padding: 5px 7px;
}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
    color: $text_dim;
    background: $surface_alt;
}
QComboBox::drop-down {
    border: 0;
    width: 22px;
}
QComboBox QAbstractItemView {
    background: $surface;
    color: $text;
    border: 1px solid $border;
    selection-background-color: $selection;
    selection-color: $text;
    outline: 0;
}
QCheckBox, QRadioButton {
    color: $text;
    spacing: 7px;
}
QCheckBox:disabled, QRadioButton:disabled {
    color: $text_dim;
}
QTabWidget::pane {
    border: 1px solid $border;
    border-radius: 8px;
    background: $surface;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    color: $text_dim;
    border: 0;
    border-bottom: 2px solid transparent;
    padding: 8px 16px;
    margin-right: 4px;
}
QTabBar::tab:hover {
    color: $text;
    background: $surface_alt;
}
QTabBar::tab:selected {
    color: $accent;
    border-bottom: 2px solid $accent;
    background: $surface;
}
QTableView, QTableWidget {
    background: $surface;
    alternate-background-color: $surface_alt;
    color: $text;
    border: 1px solid $border;
    border-radius: 8px;
    gridline-color: $border;
    selection-background-color: $selection;
    selection-color: $text;
    outline: 0;
}
QTableView::item, QTableWidget::item {
    padding: 4px 8px;
    border: 0;
    background: transparent;
}
QTableView::item:selected, QTableWidget::item:selected {
    background: $selection;
    color: $text;
}
QHeaderView::section {
    background: $surface_alt;
    color: $text_dim;
    border: 0;
    border-bottom: 1px solid $border;
    border-right: 1px solid $border;
    padding: 8px 10px;
    font-size: 11px;
    font-weight: 600;
}
QHeaderView::section:last {
    border-right: 0;
}
QTableCornerButton::section {
    background: $surface_alt;
    border: 0;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: $border;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: $text_dim;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    border: 0;
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: $border;
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: $text_dim;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
    border: 0;
    width: 0;
}
QStatusBar {
    background: $surface;
    color: $text_dim;
    border-top: 1px solid $border;
}
QStatusBar::item {
    border: 0;
}
QStatusBar QLabel {
    color: $text_dim;
    font-size: 11px;
}
QSplitter::handle {
    background: $border;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}
QToolTip {
    background: $surface_alt;
    color: $text;
    border: 1px solid $border;
    border-radius: 5px;
    padding: 6px 9px;
}
QDialog, QMessageBox {
    background: $background;
    color: $text;
}
QMessageBox QLabel {
    color: $text;
}
QMessageBox QPushButton {
    min-width: 90px;
}
QProgressBar {
    background: $surface_alt;
    border: 0;
    border-radius: 3px;
    max-height: 6px;
    min-height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: $accent;
    border-radius: 3px;
}
QMenu {
    background: $surface;
    color: $text;
    border: 1px solid $border;
}
QMenu::item {
    padding: 6px 20px;
}
QMenu::item:selected {
    background: $selection;
}
"""


def build_qss(theme):
    """Return one complete stylesheet for `theme`."""
    values = THEMES.get(theme, THEMES["dark"])
    return Template(QSS).substitute(values)


def build_palette(theme):
    """QPalette fallback for native controls and file dialogs."""
    t = THEMES.get(theme, THEMES["dark"])
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(t["background"]))
    p.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Base, QColor(t["surface"]))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(t["surface_alt"]))
    p.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Button, QColor(t["surface"]))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Highlight, QColor(t["accent"]))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(t["accent_fg"]))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(t["surface_alt"]))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(t["text_dim"]))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(t["text_dim"]))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(t["text_dim"]))
    return p


def apply_theme(app, theme):
    """Apply QSS + palette to the whole application."""
    app.setStyleSheet(build_qss(theme))
    app.setPalette(build_palette(theme))
