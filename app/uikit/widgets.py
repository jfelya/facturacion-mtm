"""Small reusable widgets for the UI kit."""
import tkinter as tk


def hseparator(parent, color, height=1):
    """A 1 px horizontal rule (toolbar bottom / status top separators)."""
    f = tk.Frame(parent, height=height, bd=0, highlightthickness=0, bg=color)
    return f


class StatusDot(tk.Canvas):
    """Small coloured state dot (idle = muted, running = accent, done = success, error = danger)."""

    def __init__(self, parent, size=9, bg=None):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bd=0, bg=bg)
        self._size = size

    def set(self, color):
        self.delete("all")
        s = self._size
        self.create_oval(1, 1, s - 1, s - 1, fill=color, outline=color)
