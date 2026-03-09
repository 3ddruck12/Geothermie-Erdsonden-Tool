"""GUI-Hilfsfunktionen."""

import sys
import tkinter as tk


def bind_mousewheel_to_canvas(canvas: tk.Canvas) -> None:
    """Bindet Mausrad-Scrolling an einen Canvas über Geometrie-Prüfung.

    Statt Widget-Ancestor-Check wird die tatsächliche Mausposition mit den
    Bildschirmkoordinaten des Canvas verglichen. Damit scrollt genau der Canvas,
    über dem der Mauszeiger gerade ist – unabhängig davon welches Kind-Widget
    das Event ursprünglich erhielt (Entry, Combobox, Label, …).

    Funktioniert auf Windows, macOS und Linux.
    """

    def _on_mousewheel(event):
        try:
            # Nur scrollen wenn Canvas gerade sichtbar ist
            if not canvas.winfo_ismapped():
                return

            # Mauszeiger-Position auf dem Bildschirm
            ptr_x, ptr_y = canvas.winfo_pointerxy()

            # Canvas-Bereich auf dem Bildschirm
            cx = canvas.winfo_rootx()
            cy = canvas.winfo_rooty()
            cw = canvas.winfo_width()
            ch = canvas.winfo_height()

            if cx <= ptr_x <= cx + cw and cy <= ptr_y <= cy + ch:
                if event.num == 4 or getattr(event, 'delta', 0) > 0:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5 or getattr(event, 'delta', 0) < 0:
                    canvas.yview_scroll(1, "units")
        except Exception:
            pass

    if sys.platform == "linux":
        canvas.bind_all("<Button-4>", _on_mousewheel, add="+")
        canvas.bind_all("<Button-5>", _on_mousewheel, add="+")
    else:
        canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")
