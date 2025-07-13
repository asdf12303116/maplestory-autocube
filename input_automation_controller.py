import pyautogui
import time

class InputController:
    """模拟游戏内的鼠标输入。"""

    def __init__(self, delay_after_click, delay_after_enter):
        pyautogui.PAUSE = 0.05
        self.delay_after_enter = delay_after_enter
        self.delay_after_click = delay_after_click

    def click(self, x, y):
        """在指定的绝对屏幕坐标执行点击。"""
        try:
            pyautogui.click(x, y)
        except Exception as e:
            print(f"点击时发生错误: {e}")

    def press_button_confirm(self, x, y):
        """在指定的绝对屏幕坐标执行点击。"""
        try:
            pyautogui.click(x, y)
            time.sleep(self.delay_after_click)
            pyautogui.press('enter')
            time.sleep(self.delay_after_enter)
            pyautogui.press('enter')
            time.sleep(self.delay_after_enter)
            pyautogui.press('enter')
            time.sleep(self.delay_after_enter)
        except Exception as e:
            print(f"点击时发生错误: {e}")
    def press_button_confirm_main(self, x, y):
        """在指定的绝对屏幕坐标执行点击。"""
        try:
            pyautogui.click(x, y)
            time.sleep(self.delay_after_click)
            pyautogui.press('enter')
            time.sleep(self.delay_after_enter)
        except Exception as e:
            print(f"点击时发生错误: {e}")
    def move_to(self, x, y):
        """将鼠标移动到指定的绝对屏幕坐标。"""
        try:
            pyautogui.moveTo(x, y)
        except Exception as e:
            print(f"移动鼠标时发生错误: {e}")
