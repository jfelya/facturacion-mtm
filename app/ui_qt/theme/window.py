"""Best-effort native Windows dark title bar."""
import ctypes
import sys


def set_dark_title_bar(widget, dark):
    if sys.platform != "win32":
        return
    try:
        hwnd = int(widget.winId())
        value = ctypes.c_int(1 if dark else 0)
        for attribute in (20, 19):  # Win10 1903+ / Win10 1809
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
            ) == 0:
                return
    except Exception:
        # Older Windows: keep the native light title bar.
        pass
