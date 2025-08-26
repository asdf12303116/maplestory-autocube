from typing import List

import cv2
import numpy as np
from rapidocr import RapidOCR, OCRVersion ,ModelType
from thefuzz import process, fuzz
import re
def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    if image is None: return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 3)
    _, threshed = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return threshed


from typing import List

CHINESE_COLON = "："
ENGLISH_COLON = ":"
PERCENTAGE_SIGN = "%"
PLUS_TWO = "+2"
PLUS_TWO_PREFIX = "角色每10级"



class OCREngine:
    """封装 RapidOCR 和 TheFuzz 校正逻辑。"""

    def __init__(self, valid_stats: list, score_cutoff=80,use_plus_two=False,use_high_level=False):
        try:
            self.params = None
            if use_high_level:
                self.params = {
                "Det.ocr_version": OCRVersion.PPOCRV5,
                "Rec.ocr_version": OCRVersion.PPOCRV5,
                "Rec.model_type": ModelType.SERVER,
            }
            else:
                self.params = {
                    "Det.ocr_version": OCRVersion.PPOCRV5,
                    "Rec.ocr_version": OCRVersion.PPOCRV5,
                }
            self.engine = RapidOCR(
                params=self.params
            )
        except Exception as e:
            self.engine = None
            print(f"RapidOCR 引擎初始化失败: {e}")
        self.valid_stats = valid_stats
        self.score_cutoff = score_cutoff
        self.use_plus_two = use_plus_two

    def _correct_text(self, text: str):
        if not self.valid_stats: return text
        # 去除所有非中文英文数字字符
        clean_text = ''.join(char for char in text if char.isalnum() or '\u4e00' <= char <= '\u9fff')
        match = process.extractOne(clean_text, self.valid_stats,scorer=fuzz.ratio)
        return match[0] if match and match[1] >= self.score_cutoff else text

    def _correct_value(self, text: str):
        match = re.search(r'(\d{1,3}%)', text)
        return match.group(1) if match else text

    def get_cut_param(self,height,width,cube_type):
        bbox = None
        match cube_type:
            case 'additional':
                bbox = (0.61,0.81,0.1,0.9)
            case 'additional_choose':
                bbox = (0.71, 0.87, 0.08, 0.9)
            case 'main':
                bbox = (0.63,0.88,0.1,0.9)
            case _:
                bbox = ( 0.63,0.88,0.1,0.9)

        return int(height * bbox[0]),int(height * bbox[1]),int(width * bbox[2]),int(width * bbox[3])

    def get_text_from_image(self, image: np.ndarray, cube_type='additional'):
        if self.engine is None or image is None: return []
        try:
            # 获取匹配区域的高度
            height = image.shape[0]
            width = image.shape[1]
            start_height, end_height, start_width, end_width = self.get_cut_param(height,width,cube_type)

            cropped_area = image[start_height:end_height, start_width:end_width]
            per_height = int(cropped_area.shape[0] / 4)




            # 词条
            level = cropped_area[0:per_height, :]
            str1 = cropped_area[per_height:per_height * 2, :]
            str2 = cropped_area[per_height * 2:per_height * 3, :]
            str3 = cropped_area[per_height * 3:per_height * 4, :]

            # text
            level_txt = self.engine(level, use_det=False, use_cls=False, use_rec=True)
            str1_txt = self.engine(str1, use_det=False, use_cls=False, use_rec=True)
            str2_txt = self.engine(str2, use_det=False, use_cls=False, use_rec=True)
            str3_txt = self.engine(str3, use_det=False, use_cls=False, use_rec=True)

            level_str = ''
            str1_str = ''
            str2_str = ''
            str3_str = ''

            if level_txt :
                level_str = level_txt.txts[0]
            if str1_txt :
                str1_str = str1_txt.txts[0]
            if str2_txt :
                str2_str = str2_txt.txts[0]
            if str3_txt :
                str3_str = str3_txt.txts[0]

            # result
            result = []
            result.append(level_str)
            result.append(str1_str)
            result.append(str2_str)
            result.append(str3_str)
            # print(f"原始数据: {result}")
            return self.format_text(result)
        except Exception as e:
            print(f"OCR发生未知错误: {e}")
            return []

    def format_text(self, text_arr: List[str]) -> List[str]:
        """
        格式化文本数组，处理冒号格式并检查百分比值。

        Args:
            text_arr: 包含待处理文本的列表

        Returns:
            处理后的文本列表，百分比值保留键名，非百分比值替换为空字符串
        """

        def process_text_line(text: str) -> tuple[str, str]:
            """处理单行文本，标准化冒号并分割键值对"""
            normalized_text = text.replace(CHINESE_COLON, ENGLISH_COLON)
            parts = normalized_text.split(ENGLISH_COLON, 1)
            return (self._correct_text(parts[0]), parts[1]) if len(parts) > 1 else (text, "")

        result = []
        raw_format_data = []

        # 处理第一个元素（标题）
        if text_arr:
            raw_text = text_arr[0]
            #去除空白字符，全角字符转为半角字符
            format_text = ''

            # 去除空白字符
            raw_text = ''.join(raw_text.split())

            # 全角字符转半角字符
            for char in raw_text:
                code_point = ord(char)
                # 全角字符范围通常在FF00-FFEF
                if 0xFF01 <= code_point <= 0xFF5E:
                    # 转换为对应的半角字符
                    format_text += chr(code_point - 0xFEE0)
                else:
                    format_text += char
            format_text = format_text.upper()
            result.append(format_text)
            raw_format_data.append(format_text)

        # 处理剩余元素
        for text in text_arr[1:]:
            key, value = process_text_line(text)

            if value:
                raw_format_data.append(f"{key}{ENGLISH_COLON}{value}")
                if self.use_plus_two:
                    if PERCENTAGE_SIGN in value:
                        result.append(key)
                    elif value == PLUS_TWO:
                        fixed_key = key.replace(PLUS_TWO_PREFIX, "")
                        result.append(fixed_key)
                    else:
                        result.append("")
                else:
                    result.append(key if PERCENTAGE_SIGN in value else "")

            else:
                raw_format_data.append(text)
                result.append("")

        # print(f"原始格式化数据: {raw_format_data}")
        return result