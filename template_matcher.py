import cv2

class TemplateMatcher:
    """使用OpenCV模板匹配来定位UI元素。"""
    
    def __init__(self, template_path: str, threshold: float = 0.75):
        """
        初始化模板匹配器
        
        Args:
            template_path: 模板图片路径
            threshold: 匹配阈值(0-1之间)
        
        Raises:
            FileNotFoundError: 模板图片未找到
            ValueError: 阈值超出有效范围
        """
        if not 0 <= threshold <= 1:
            raise ValueError("阈值必须在0到1之间")
            
        self.template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if self.template is None:
            raise FileNotFoundError(f"模板图片未找到: '{template_path}'")
            
        self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
        self.t_h, self.t_w = self.template.shape[:2]
        self.threshold = threshold

    def find_match(self, screen_frame, use_color: bool = False):
        """
        在屏幕截图中寻找模板
        
        Args:
            screen_frame: 要搜索的图像帧
            use_color: 是否使用彩色图像匹配
        
        Returns:
            tuple: (位置元组, 尺寸元组, 匹配置信度) 或 (None, None, 置信度)
        """
        if screen_frame is None:
            raise ValueError("输入图像不能为None")

        if use_color:
            template = self.template
            frame = screen_frame
            # 分离通道分别匹配再取平均值
            b1, g1, r1 = cv2.split(frame)
            b2, g2, r2 = cv2.split(template)
            res_b = cv2.matchTemplate(b1, b2, cv2.TM_CCOEFF_NORMED)
            res_g = cv2.matchTemplate(g1, g2, cv2.TM_CCOEFF_NORMED)
            res_r = cv2.matchTemplate(r1, r2, cv2.TM_CCOEFF_NORMED)
            res = (res_b + res_g + res_r) / 3
        else:
            template = self.template_gray
            frame = cv2.cvtColor(screen_frame, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)

        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val >= self.threshold:
            return max_loc, (self.t_w, self.t_h), max_val
        return None, None, max_val
