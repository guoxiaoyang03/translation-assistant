"""Screenshot module — fullscreen overlay region selector and screen capture."""

import tkinter as tk
from pathlib import Path

from PIL import ImageGrab


def capture_region(root: tk.Tk) -> None:
    """Hide the main window, let the user drag a rectangle on a semi-transparent
    overlay, then save the selected screen region to ``data/raw/screenshot.png``.
    Press ``Esc`` to cancel without saving."""

    # ── Hide the main window ─────────────────────────────────
    root.withdraw()
    root.update_idletasks()  # let the WM finish hiding

    # ── Fullscreen semi-transparent overlay ───────────────────
    overlay = tk.Toplevel(root)
    overlay.overrideredirect(True)
    overlay.attributes("-alpha", 0.35)         # ~35 % opacity
    overlay.attributes("-topmost", True)
    overlay.configure(bg="#C0C0C0")            # light grey

    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()
    overlay.geometry(f"{sw}x{sh}+0+0")

    # Canvas filling the overlay for drawing the selection rect
    canvas = tk.Canvas(
        overlay,
        width=sw,
        height=sh,
        bg="#C0C0C0",
        highlightthickness=0,
        cursor="cross",
    )
    canvas.pack()

    # ── State variables captured by the nested handlers ───────
    start_x = 0
    start_y = 0
    rect_id = None

    def on_press(event: tk.Event) -> None:
        nonlocal start_x, start_y, rect_id
        start_x = event.x
        start_y = event.y
        # Create a zero-size rectangle that will be resized during drag
        rect_id = canvas.create_rectangle(
            start_x, start_y, start_x, start_y,
            outline="#00FF00",
            width=3,
        )

    def on_drag(event: tk.Event) -> None:
        if rect_id is not None:
            canvas.coords(rect_id, start_x, start_y, event.x, event.y)

    def on_release(event: tk.Event) -> None:
        end_x, end_y = event.x, event.y

        # Normalize so (x1,y1) is top-left and (x2,y2) is bottom-right
        x1, x2 = sorted((start_x, end_x))
        y1, y2 = sorted((start_y, end_y))

        overlay.destroy()
        root.update_idletasks()

        # Only save when the selected area is meaningful
        if x2 - x1 >= 5 and y2 - y1 >= 5:
            out_dir = Path("data/raw")
            out_dir.mkdir(parents=True, exist_ok=True)

            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            img.save(out_dir / "screenshot.png")

        root.deiconify()

    def on_escape(_event: tk.Event) -> None:
        overlay.destroy()
        root.update_idletasks()
        root.deiconify()

    # ── Bind events ──────────────────────────────────────────
    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    overlay.bind("<Escape>", on_escape)

    # Grab focus so Escape reaches the overlay immediately
    overlay.focus_force()
    overlay.grab_set()
