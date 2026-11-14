"""Translated QMessageBox helpers."""
from PySide6.QtWidgets import QMessageBox


def _box(parent, icon, title, text, buttons=QMessageBox.StandardButton.Ok):
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(buttons)
    return box


def info(parent, title, text):
    _box(parent, QMessageBox.Icon.Information, title, text).exec()


def error(parent, title, text):
    _box(parent, QMessageBox.Icon.Critical, title, text).exec()


def confirm(parent, title, text):
    box = _box(
        parent,
        QMessageBox.Icon.Question,
        title,
        text,
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
    )
    box.setDefaultButton(QMessageBox.StandardButton.Ok)
    return box.exec() == QMessageBox.StandardButton.Ok


def yes_no(parent, title, text):
    box = _box(
        parent,
        QMessageBox.Icon.Question,
        title,
        text,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    box.setDefaultButton(QMessageBox.StandardButton.Yes)
    return box.exec() == QMessageBox.StandardButton.Yes
