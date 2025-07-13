# -*- coding: utf-8 -*-
import threading

from pynput import keyboard
import shutil
from gui import AutoCuberGUI
import os
import ctypes
if __name__ == '__main__':
    try:
        is_admin = (os.getuid() == 0)
    except AttributeError:
        is_admin = (ctypes.windll.shell32.IsUserAnAdmin() != 0)
    if not is_admin:
        print("警告: 未以管理员权限运行。为确保能向游戏发送点击，请以管理员身份运行。")



    app = AutoCuberGUI()
    if app.winfo_exists():
        app.mainloop()
