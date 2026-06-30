"""GUI module — provides a topmost overlay window for interactive translation."""

import tkinter as tk
from pathlib import Path

from src.screenshot import capture_region
from src.translator import translate_image


def create_gui():
    """Create and run the main GUI loop."""

    root = tk.Tk()
    root.title("翻译助手")
    root.attributes("-topmost", True)

    # ── Helpers (defined here so they can close over widgets) ──

    def set_output(text: str) -> None:
        """Write *text* into the read-only output area."""
        text_output.configure(state=tk.NORMAL)
        text_output.delete("1.0", tk.END)
        text_output.insert("1.0", text)
        text_output.configure(state=tk.DISABLED)

    def on_translate() -> None:
        """OCR the screenshot, translate it, and show the result."""
        screenshot = Path("data/raw/screenshot.png")
        if not screenshot.is_file():
            set_output("请先截图")
            return

        btn_start.configure(text="翻译中...", state=tk.DISABLED)
        root.update_idletasks()  # immediately reflect the button change

        try:
            result = translate_image(str(screenshot))
        finally:
            btn_start.configure(text="▶️ 开始翻译", state=tk.NORMAL)

        set_output(result)

    # ── Buttons ──────────────────────────────────────────────
    btn_select = tk.Button(
        root,
        text="📷 选择翻译区块",
        font=("Microsoft YaHei", 11),
        padx=12,
        pady=6,
        command=lambda: capture_region(root),
    )
    btn_select.pack(pady=(16, 4), padx=20, fill=tk.X)

    btn_start = tk.Button(
        root,
        text="▶️ 开始翻译",
        font=("Microsoft YaHei", 11),
        padx=12,
        pady=6,
        command=on_translate,
    )
    btn_start.pack(pady=4, padx=20, fill=tk.X)

    btn_exit = tk.Button(
        root,
        text="❌ 退出关闭",
        font=("Microsoft YaHei", 11),
        padx=12,
        pady=6,
        command=root.destroy,
    )
    btn_exit.pack(pady=4, padx=20, fill=tk.X)

    # ── Translation output + scrollbar ───────────────────────
    frame_output = tk.Frame(root)
    frame_output.pack(pady=(8, 16), padx=20, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(frame_output)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text_output = tk.Text(
        frame_output,
        height=12,
        width=50,
        font=("Microsoft YaHei", 10),
        wrap=tk.WORD,
        state=tk.DISABLED,
        yscrollcommand=scrollbar.set,
    )
    text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.configure(command=text_output.yview)

    root.mainloop()
