"""GUI-Hilfsfunktionen."""

import sys
import tkinter as tk


def bind_mousewheel_to_canvas(canvas: tk.Canvas) -> None:
    """Bindet Mausrad-Scrolling an einen Canvas.

    Registriert einen Root-Level-Handler, der bei jedem Scroll-Event prüft,
    ob das Ereignis-Widget ein Nachkomme dieses Canvas ist. So scrollt nur
    der Canvas, über dem die Maus tatsächlich schwebt – auch wenn Kinder-Widgets
    (ttk.Label, ttk.Entry, …) den direkten Canvas-Bereich überdecken.
    """

    def _on_mousewheel(event):
        w = event.widget
        while w is not None:
            if w is canvas:
                if event.num == 4 or getattr(event, 'delta', 0) > 0:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5 or getattr(event, 'delta', 0) < 0:
                    canvas.yview_scroll(1, "units")
                return
            w = getattr(w, 'master', None)

    if sys.platform == "linux":
        canvas.bind_all("<Button-4>", _on_mousewheel, add="+")
        canvas.bind_all("<Button-5>", _on_mousewheel, add="+")
    else:
        canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")
