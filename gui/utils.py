"""GUI-Hilfsfunktionen."""

import sys
import tkinter as tk


def bind_mousewheel_to_canvas(canvas: tk.Canvas) -> None:
    """Bindet Mausrad-Scrolling an einen Canvas – nur wenn Maus darüber ist.

    Ersetzt canvas.bind_all("<MouseWheel>") durch Enter/Leave-gestütztes
    Widget-spezifisches Binding. Funktioniert auf Windows, macOS und Linux.
    """

    def _scroll(event):
        # Windows/macOS: event.delta; Linux: Button-4 / Button-5
        if event.num == 4 or event.delta > 0:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            canvas.yview_scroll(1, "units")

    def _bind(event):
        if sys.platform == "linux":
            canvas.bind("<Button-4>", _scroll)
            canvas.bind("<Button-5>", _scroll)
        else:
            canvas.bind("<MouseWheel>", _scroll)

    def _unbind(event):
        if sys.platform == "linux":
            canvas.unbind("<Button-4>")
            canvas.unbind("<Button-5>")
        else:
            canvas.unbind("<MouseWheel>")

    canvas.bind("<Enter>", _bind)
    canvas.bind("<Leave>", _unbind)
