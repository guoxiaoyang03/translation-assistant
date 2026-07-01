"""Translation Assistant — launch the GUI.

The GUI initialises the translation-history database and starts the
global-hotkey / system-tray service internally.
"""

import time

from src.gui import create_gui


def main():
    t_start = time.time()
    print(f"[启动] main.py 开始执行  {time.strftime('%H:%M:%S')}")
    create_gui()
    print(f"[启动] 程序退出，总运行时间 {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
