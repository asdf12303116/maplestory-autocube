import win32gui
import pygetwindow as gw

class WindowManager:
    """通过窗口类名管理目标应用程序窗口。"""

    def __init__(self, window_class):
        self.window_class = window_class
        self.hwnd = None
        self.window = None
        self._find_window()

    def _find_window(self):
        try:
            self.hwnd = win32gui.FindWindow(self.window_class, None)
            self.window = gw.Win32Window(self.hwnd) if self.hwnd != 0 else None
        except Exception:
            self.hwnd, self.window = None, None

    def get_geometry(self):
        if self.is_window_active():
            return self.window.left, self.window.top, self.window.width, self.window.height
        self._find_window()
        if self.is_window_active():
            return self.window.left, self.window.top, self.window.width, self.window.height
        return None

    def is_window_active(self):
        return self.hwnd != 0 and self.window and win32gui.IsWindowVisible(self.hwnd)
