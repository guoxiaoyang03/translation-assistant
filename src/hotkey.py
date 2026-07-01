"""Hotkey module — global hotkey listener + system-tray icon.

Provides :class:`HotkeyService` which registers two global hotkeys:

* ``Ctrl+Shift+Y`` — translate selected text (copy → clipboard → translate)
* ``Ctrl+Shift+S`` — start a screenshot region selection

A system-tray icon keeps the app alive in the background.
"""

# ═══════════════════════════════════════════════════════════════════
#  Change the hotkey here — the rest of the module reads this value
# ═══════════════════════════════════════════════════════════════════
HOTKEY = "ctrl+shift+y"
HOTKEY_SCREENSHOT = "ctrl+shift+s"

import threading
import time
import tkinter as tk
from typing import Callable

import keyboard
import pyperclip
import pystray
from PIL import Image, ImageDraw


# ── Tray icon (drawn programmatically — no external asset needed) ──

def _make_tray_image() -> Image.Image:
    """Return a 64×64 RGBA image — blue circle with a white 'T'."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Blue circle
    draw.ellipse([3, 3, 61, 61], fill="#4A90D9")
    # Stylised "T" letter using two rectangles
    draw.rectangle([17, 14, 47, 22], fill="white")   # horizontal bar
    draw.rectangle([28, 14, 36, 50], fill="white")   # vertical stem
    return img


# ═══════════════════════════════════════════════════════════════════
#  HotkeyService
# ═══════════════════════════════════════════════════════════════════

class HotkeyService:
    """Manages the global hotkey and the system-tray icon.

    Parameters
    ----------
    root:
        The tkinter root window (used to schedule main-thread callbacks).
    on_translate:
        ``on_translate(text: str)`` — called on the **main thread** when
        the translate hotkey (see ``HOTKEY``) is pressed.
    on_screenshot:
        ``on_screenshot()`` — called on the **main thread** when the
        screenshot hotkey (see ``HOTKEY_SCREENSHOT``) is pressed.
    on_show_window:
        ``on_show_window()`` — called when the user clicks "显示主窗口"
        in the tray menu or double-clicks the tray icon.
    on_exit:
        ``on_exit()`` — called when the user requests a full exit
        (tray "退出程序" menu item).
    """

    def __init__(
        self,
        root: tk.Tk,
        on_translate: Callable[[str], None],
        on_screenshot: Callable[[], None],
        on_show_window: Callable[[], None],
        on_exit: Callable[[], None],
    ):
        self._root = root
        self._on_translate = on_translate
        self._on_screenshot = on_screenshot
        self._on_show_window = on_show_window
        self._on_exit = on_exit

        self._tray_icon: pystray.Icon | None = None
        self._tray_thread: threading.Thread | None = None
        self._hotkey_id = None

    # ── Public API ──────────────────────────────────────────────

    def start(self) -> None:
        """Register the global hotkeys and launch the tray icon."""
        keyboard.add_hotkey(HOTKEY, self._on_hotkey, suppress=False)
        keyboard.add_hotkey(
            HOTKEY_SCREENSHOT, self._on_screenshot_hotkey, suppress=False
        )
        self._tray_thread = threading.Thread(
            target=self._run_tray, daemon=True, name="tray-thread"
        )
        self._tray_thread.start()

    def shutdown(self) -> None:
        """Unregister the hotkey and remove the tray icon.

        Does **not** destroy the tkinter root — the caller should do that
        after calling this method.
        """
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        if self._tray_icon is not None:
            self._tray_icon.stop()
            self._tray_icon = None

    # ── Internals ───────────────────────────────────────────────

    def _on_hotkey(self) -> None:
        """Hotkey callback — runs on the *keyboard* background thread.

        Only clipboard I/O happens here; everything else is dispatched
        to the main thread via ``root.after`` to stay tkinter-safe.
        """
        try:
            # Save old clipboard content for later comparison
            old_text = pyperclip.paste()

            # Copy the user's current text selection to the clipboard
            keyboard.send("ctrl+c")
            time.sleep(0.5)                     # wait for clipboard update
            text = pyperclip.paste()

            # If clipboard didn't change, the selection may not have
            # been copied — retry once
            if text == old_text:
                print("[热键] 剪贴板未变化，重试复制...")
                keyboard.send("ctrl+c")
                time.sleep(0.3)
                text = pyperclip.paste()

            print(f"[热键] 剪贴板读取完成，共 {len(text)} 字符")
        except Exception:
            return                               # silently ignore errors

        if text and text.strip():
            self._root.after(0, self._on_translate, text)

    def _on_screenshot_hotkey(self) -> None:
        """Screenshot hotkey callback — runs on the keyboard thread."""
        self._root.after(0, self._on_screenshot)

    def _run_tray(self) -> None:
        """Run the pystray event loop (blocking; called on a daemon thread)."""
        icon = pystray.Icon(
            "translation_assistant",
            _make_tray_image(),
            f"翻译助手\n{HOTKEY} 划词翻译 | {HOTKEY_SCREENSHOT} 截图",
            menu=pystray.Menu(
                pystray.MenuItem(
                    "显示主窗口",
                    self._on_tray_show,
                    default=True,               # double-click = show
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出程序", self._on_tray_exit),
            ),
        )
        self._tray_icon = icon
        icon.run()

    def _on_tray_show(self, *_args) -> None:
        self._root.after(0, self._on_show_window)

    def _on_tray_exit(self, *_args) -> None:
        # Stop the tray event loop first, then delegate to the full-exit handler
        if self._tray_icon is not None:
            self._tray_icon.stop()
            self._tray_icon = None
        self._root.after(0, self._on_exit)
