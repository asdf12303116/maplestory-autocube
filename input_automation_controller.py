import random
import time

import pyautogui

from enum import Enum
class InputType(Enum):
    Click = 1
    Enter = 2


class InputController:
    """模拟游戏内的鼠标输入。"""

    def __init__(self, delay_after_click, delay_after_enter):
        pyautogui.PAUSE = 0.05
        self.random = random.Random()
        self.random_keyboard_start = 10
        self.random_keyboard_end = 50
        self.random_mouse_start = 1
        self.random_mouse_end = 10
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
            self.wait(InputType.Click)
            pyautogui.press('enter')
            self.wait(InputType.Enter)
            pyautogui.press('enter')
            self.wait(InputType.Enter)
            pyautogui.press('enter')
            self.wait(InputType.Enter)
        except Exception as e:
            print(f"点击时发生错误: {e}")
    def press_button_confirm_main(self, x, y):
        """在指定的绝对屏幕坐标执行点击。"""
        try:
            pyautogui.click(x, y)
            self.wait(InputType.Click)
            pyautogui.press('enter')
            self.wait(InputType.Enter)
        except Exception as e:
            print(f"点击时发生错误: {e}")
    def move_to(self, x, y):
        """将鼠标移动到指定的绝对屏幕坐标。"""
        try:
            pyautogui.moveTo(x, y)
        except Exception as e:
            print(f"移动鼠标时发生错误: {e}")

    def wait(self,input_type:InputType):
        match input_type:
            case InputType.Click:
                time.sleep(self.delay_after_click + self.get_random_int(True))
            case InputType.Enter:
                time.sleep(self.delay_after_enter + self.get_random_int())
    def get_random_int(self,is_mouse=False):
        if is_mouse:
            return self.random.randint(self.random_mouse_start, self.random_mouse_end) / 1000
        else:
            return self.random.randint(self.random_keyboard_start, self.random_keyboard_end)  / 1000
