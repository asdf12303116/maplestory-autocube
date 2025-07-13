import win32gui
from PIL import ImageGrab
import numpy as np
import cv2

class Capture:
    """使用 win32gui 和 Pillow 高效捕捉窗口客户区。"""

    def __init__(self, window_manager, border_offsets):
        self.window_manager = window_manager
        self.border_offsets = border_offsets

    def capture_window_client_area(self):
        """捕捉目标窗口的客户区（移除了边框和标题栏）。"""
        if not self.window_manager.is_window_active():
            return None, None

        hwnd = self.window_manager.hwnd
        try:
            window_rect = win32gui.GetWindowRect(hwnd)
            client_left = window_rect[0] + self.border_offsets['left']
            client_top = window_rect[1] + self.border_offsets['top']
            client_right = window_rect[2] - self.border_offsets['right']
            client_bottom = window_rect[3] - self.border_offsets['bottom']

            bbox = (client_left, client_top, client_right, client_bottom)
            pil_image = ImageGrab.grab(bbox=bbox)
            frame_rgb = np.array(pil_image)
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            return frame_bgr, bbox

        except Exception as e:
            print(f"截图失败: {e}")
            return None, None

    def release(self):
        pass
