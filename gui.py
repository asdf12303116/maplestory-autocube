import ctypes
import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk, scrolledtext, messagebox

import cv2
from PIL import Image, ImageTk
from pynput import keyboard

from additional_choose_worker import additional_choose_worker
from additional_worker import additional_worker
from config_manager import ConfigManager
from main_worker import main_worker

package_version="{version}"

# 告诉操作系统使用程序自身的dpi适配


class AutoCuberGUI(tk.Tk):
    """应用程序的主GUI窗口。"""

    def __init__(self):
        super().__init__()
        if package_version.startswith("{"):
            self.title("魔方-local")
        else:
            self.title(f"魔方-{package_version}")
        self.geometry("740x850")  # 调整初始尺寸
        self.resizable(True, True)
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        # 调用api获得当前的缩放因子
        ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
        # 设置缩放因子
        test = self.tk.call('tk', 'scaling')
        self.tk.call('tk', 'scaling', ScaleFactor / 75)

        self.log_queue = queue.Queue()
        self.image_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = None

        self.config_manager = ConfigManager()
        if not self.config_manager.config:
            self.withdraw()
            messagebox.showerror("错误", "config.json 文件未找到或格式错误。")
            self.destroy()
            return

        self.create_widgets()
        self.process_queues()
        self._toggle_third_line()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # 启动键盘监听器（在单独的线程中）
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press
        )
        self.keyboard_listener.daemon = True  # 设为守护线程，这样主程序退出时，线程也会结束
        self.keyboard_listener.start()

    def on_press(self, key):
        target_key = None
        try:
            target_key = f'{key.char}'
        except AttributeError:
            target_key = f'{key}'
        if target_key == 'q':
            self.after(0, self.key_exit)

    def key_exit(self):
        if not self.stop_event.is_set():
            print("key exit")
            self.stop_cubing()

    # 在 AutoCuberGUI 类中添加新的辅助方法
    def _toggle_third_line(self):
        """处理仅匹配前两行选项的切换"""
        if not self.keep_all_useable.get():
            if self.match_two_lines_var.get():
                self.desired_stats_vars[2].set('')  # 清空第三行
                self.stats_combos[2].configure(state='disabled')  # 禁用第三行
            else:
                self.stats_combos[2].configure(state='readonly')  # 启用第三行

    def _toggle_all_line(self):
        """
        处理所有属性行的启用/禁用状态
        根据魔方类型和'保留所有可用属性'选项来控制属性选择组件的状态
        """
        cube_type = self.cube_type.get()
        keep_all_useable = self.keep_all_useable.get()

        def disable_all_lines():
            """禁用所有属性行并清空内容"""
            for i in range(3):
                self.desired_stats_vars[i].set('')
                self.stats_combos[i].configure(state='disabled')

        def enable_lines(count=3):
            """启用指定数量的属性行"""
            for i in range(count):
                self.stats_combos[i].configure(state='readonly')

        if keep_all_useable:
            disable_all_lines()
        else:
            if cube_type == 1:  # 平等魔方
                enable_lines(1)  # 只启用第一行
                # 禁用其他行
                for i in range(1, 3):
                    self.desired_stats_vars[i].set('')
                    self.stats_combos[i].configure(state='disabled')
            else:
                enable_lines()  # 启用所有行

    def create_widgets(self):
        # 主框架布局
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 配置主框架的行列权重
        main_frame.grid_rowconfigure(0, weight=1)  # 内容区域可扩展
        main_frame.grid_rowconfigure(1, weight=0)  # 日志区域固定高度
        main_frame.grid_columnconfigure(0, weight=0, minsize=220)  # 左侧面板
        main_frame.grid_columnconfigure(1, weight=3)  # 右侧图像区域

        # ================= 内容区域 =================
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0)
        content_frame.grid_columnconfigure(1, weight=1)

        # 左侧面板
        left_panel = ttk.Frame(content_frame, padding=(0, 5, 5, 0))
        left_panel.grid(row=0, column=0, sticky="nsew")

        # 期望属性设置区域
        options_frame = ttk.LabelFrame(left_panel, text="期望属性设置", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # 引用
        self.chk_var = []  # checkbox引用
        self.stats_combos = []  # 保存所有下拉框的引用
        # 潜能输入框部分的修改
        cfg = self.config_manager
        potentials = cfg.get("valid_potentials")
        self.desired_stats_vars = []

        # 类型选择 '附加','平等','火花'
        show_cube_type = ['附加', '平等','选择附加']
        self.cube_type = tk.IntVar(value=0)


        def cube_type_change(args):
            sel_cube_type = cube_type.get()
            match sel_cube_type:
                case '附加':
                    self.cube_type.set(0)
                    set_add_type()
                case '平等':
                    self.cube_type.set(1)
                    self.interval_var.set(value="1300")
                    self.keep_2_useable.set(0)
                    self.chk_2_use.config(state=tk.NORMAL)
                    for chk in self.chk_var:
                        chk.config(state=tk.DISABLED)
                        for i in range(3):
                            if i == 0:
                                pass
                            else:
                                self.desired_stats_vars[i].set('')
                                self.stats_combos[i].configure(state='disabled')
                case '选择附加':
                    self.cube_type.set(2)
                    set_add_type()
        def set_add_type():
            self.interval_var.set(value="200")
            self.keep_2_useable.set(0)
            self.chk_2_use.config(state=tk.NORMAL)
            for chk in self.chk_var:
                chk.config(state=tk.NORMAL)
            for i in range(3):
                self.desired_stats_vars[i].set('')
                self.stats_combos[i].configure(state='readonly')
            self._toggle_third_line()
        row_frame = ttk.Frame(options_frame)
        row_frame.pack(fill=tk.X, pady=3)
        ttk.Label(row_frame, text=f"类型:", width=8, anchor="e").pack(side=tk.LEFT, padx=(0, 5))

        cube_type = tk.StringVar(value=show_cube_type[0])
        combo = ttk.Combobox(row_frame, textvariable=cube_type, values=show_cube_type, state='readonly')
        combo.bind('<<ComboboxSelected>>', cube_type_change)
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        for i in range(3):
            row_frame = ttk.Frame(options_frame)
            row_frame.pack(fill=tk.X, pady=3)

            ttk.Label(row_frame, text=f"潜能 {i + 1}:", width=8, anchor="e").pack(side=tk.LEFT, padx=(0, 5))

            var = tk.StringVar()
            combo = ttk.Combobox(row_frame, textvariable=var, values=potentials, state='readonly')
            combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.desired_stats_vars.append(var)
            self.stats_combos.append(combo)

        # 额外设置

        row_frame = ttk.Frame(options_frame)
        row_frame.pack(fill=tk.X, pady=3)
        self.keep_all_useable = tk.IntVar(value=0)
        chk1 = ttk.Checkbutton(row_frame,
                               text="保留所有可用属性",
                               variable=self.keep_all_useable,
                               command=self._toggle_all_line)
        chk1.pack(side=tk.LEFT)
        self.stats_combos.append(chk1)

        row_frame.pack(fill=tk.X, pady=3)
        self.keep_2_useable = tk.IntVar(value=0)
        chk_2_use = ttk.Checkbutton(row_frame,
                                    text="保留两条可用",
                                    variable=self.keep_2_useable)
        chk_2_use.pack(side=tk.LEFT)
        self.chk_2_use = chk_2_use

        # 控制选项部分的修改
        control_options_frame = ttk.Frame(options_frame)
        control_options_frame.pack(fill=tk.X, pady=(8, 0))

        # 验证函数 - 只允许输入数字
        def validate_number(P):
            if P == "": return True
            return P.isdigit()

        vcmd = self.register(validate_number)

        # 添加间隔输入框
        self.interval_var = tk.StringVar(value="200")
        interval_frame = ttk.Frame(options_frame)
        interval_frame.pack(fill=tk.X, pady=3)
        ttk.Label(interval_frame, text="每轮间隔:", width=8, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        interval_entry = ttk.Entry(interval_frame,
                                   textvariable=self.interval_var,
                                   validate="key",
                                   validatecommand=(vcmd, '%P'))
        interval_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 鼠标点击间隔
        self.interval_mouse_var = tk.StringVar(value="50")
        interval_frame = ttk.Frame(options_frame)
        interval_frame.pack(fill=tk.X, pady=3)
        ttk.Label(interval_frame, text="鼠标间隔:", width=8, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        interval_entry = ttk.Entry(interval_frame,
                                   textvariable=self.interval_mouse_var,
                                   validate="key",
                                   validatecommand=(vcmd, '%P'))
        interval_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 键盘输入间隔
        self.interval_keyboard_var = tk.StringVar(value="100")
        interval_frame = ttk.Frame(options_frame)
        interval_frame.pack(fill=tk.X, pady=3)
        ttk.Label(interval_frame, text="键盘间隔:", width=8, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        interval_entry = ttk.Entry(interval_frame,
                                   textvariable=self.interval_keyboard_var,
                                   validate="key",
                                   validatecommand=(vcmd, '%P'))
        interval_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.resolution = tk.StringVar(value="2560")
        row_frame = ttk.Frame(options_frame)
        row_frame.pack(fill=tk.X, pady=3)

        ttk.Label(row_frame, text=f"分辨率:", width=8, anchor="e").pack(side=tk.LEFT, padx=(0, 5))
        resolution_frame = ttk.Frame(row_frame)
        resolution_frame.pack(fill=tk.X, pady=3)
        res_data = cfg.get("res_config")
        resolution_combo = ttk.Combobox(resolution_frame, textvariable=self.resolution, values=res_data,
                                        state='readonly')
        resolution_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 修改仅匹配前两行的复选框，添加命令回调
        self.match_two_lines_var = tk.IntVar(value=1)
        chk1 = ttk.Checkbutton(control_options_frame,
                               text="仅匹配前两行",
                               variable=self.match_two_lines_var,
                               command=self._toggle_third_line)
        chk1.pack(side=tk.LEFT)
        self.chk_var.append(chk1)

        self.show_image_var = tk.IntVar(value=1)
        chk2 = ttk.Checkbutton(control_options_frame, text="显示图像",
                               variable=self.show_image_var)
        chk2.pack(side=tk.LEFT, padx=(10, 0))

        self.use_plus_two_var = tk.IntVar(value=0)
        chk3 = ttk.Checkbutton(control_options_frame, text="启用+2",
                               variable=self.use_plus_two_var)
        chk3.pack(side=tk.LEFT, padx=(20, 0))
        self.chk_var.append(chk3)

        row2_frame = ttk.Frame(options_frame)
        row2_frame.pack(fill=tk.X, pady=3)
        self.use_high_level = tk.IntVar(value=0)
        chk_high_level = ttk.Checkbutton(row2_frame, text="启用高精度OCR模型",
                                         variable=self.use_high_level)
        chk_high_level.pack(side=tk.LEFT)

        def validate_number(P):
            if P == "": return True
            return P.isdigit()

        vcmd = self.register(validate_number)

        # 按钮区域 - 固定宽度按钮
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill=tk.X, pady=(0, 5))

        # 使用固定宽度按钮
        self.start_button = ttk.Button(button_frame, text="开始", width=8, command=self.start_cubing)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_button = ttk.Button(button_frame, text="停止", width=8, command=self.stop_cubing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

        # 右侧图像面板
        right_panel = ttk.Frame(content_frame)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # 图像预览区域
        image_frame = ttk.LabelFrame(right_panel, text="识别图像预览", padding=10)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.image_label = ttk.Label(image_frame, text="预览区域将在此显示",
                                     anchor=tk.CENTER,
                                     background='#f0f0f0',
                                     relief="solid",
                                     padding=10)
        self.image_label.pack(fill=tk.BOTH, expand=True)

        # ================= 日志区域 =================
        log_frame = ttk.LabelFrame(main_frame, text="实时日志", padding=5)
        log_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(5, 0))

        # 配置日志区域的行列权重
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                                  state=tk.DISABLED, height=8,
                                                  padx=5, pady=5)
        self.log_text.grid(row=0, column=0, sticky="nsew")

    def log(self, message):
        self.log_queue.put(f"[{datetime.now().strftime('%H:%M:%S.%f')}] {message}")

    def process_queues(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.config(state=tk.DISABLED)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass

        try:
            img_data = self.image_queue.get_nowait()
            img_rgb = cv2.cvtColor(img_data, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            label_w, label_h = self.image_label.winfo_width(), self.image_label.winfo_height()
            if label_w > 1 and label_h > 1:
                img_w, img_h = pil_img.size
                if img_w > 0 and img_h > 0:
                    scale = min(label_w / img_w, label_h / img_h)
                    new_w, new_h = int(img_w * scale * 0.95), int(img_h * scale * 0.95)
                    if new_w > 0 and new_h > 0:
                        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image=pil_img)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
        except queue.Empty:
            pass
        self.after(100, self.process_queues)

    def start_cubing(self):
        mouse_move_to_arg = (500,30)
        self.mouse_move_arg = mouse_move_to_arg
        desired_stats = [var.get().strip() for var in self.desired_stats_vars if var.get().strip()]
        keep_all_useable = self.keep_all_useable.get() == 1
        if not desired_stats and not keep_all_useable:
            self.log("错误: 请至少输入一个期望的潜能属性。")
            return
        is_main_cube = self.cube_type.get() == 1
        # if is_main_cube:
        #     if not keep_all_useable:
        #         self.log("错误: 请至少输入一个期望的潜能属性。")
        #         return
        #     else:
        #         desired_stats = desired_stats[0]
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log("启动自动化核心...")
        self.stop_event.clear()
        self.worker_thread = threading.Thread(
            target=self.cubing_worker,
            args=(desired_stats, self.match_two_lines_var.get(), self.show_image_var, keep_all_useable),
            daemon=True
        )
        self.worker_thread.start()

    def stop_cubing(self):
        self.log("正在请求停止...")
        self.stop_event.set()
        self.stop_button.config(state=tk.DISABLED)

    def on_worker_finished(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.worker_thread = None
        self.log("自动化流程已停止。")

    def on_closing(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.stop_cubing()
            self.worker_thread.join(timeout=2.0)
        self.destroy()

    def cubing_worker(self, desired_stats, match_two_lines, show_image_var, keep_all_useable=False):
        curr_type = self.cube_type.get()
        match curr_type:
            case 0:
                additional_worker(self, desired_stats, match_two_lines, show_image_var, keep_all_useable)
            case 1:
                main_worker(self, desired_stats, show_image_var, keep_all_useable)
            case 2:
                additional_choose_worker(self, desired_stats, match_two_lines, show_image_var, keep_all_useable)

    # def cubing_worker1(self, desired_stats, match_two_lines, show_image_var,keep_all_useable=False):
    #     """后台自动化工作线程。"""
    #     try:
    #         # --- 初始化 ---
    #         self.log("--- 初始化模块 ---")
    #         cfg = self.config_manager
    #
    #         threshold = cfg.get("template_match_threshold")
    #         resolution = self.resolution.get()
    #         file_end = cfg.get("file_end")
    #         potential_matcher = TemplateMatcher(cfg.get("add_area_template_path_prefix")+ resolution + file_end, threshold)
    #         button_matcher = TemplateMatcher(cfg.get("cube_button_template_path_prefix")+ resolution + file_end, threshold)
    #         button_fail_matcher = TemplateMatcher(cfg.get("cube_button_fail_template_path_prefix")+ resolution + file_end, threshold)
    #         self.log("模板匹配器已加载。")
    #         use_high_level = self.use_high_level.get() == 1
    #         print(f"use_high_level: {use_high_level}")
    #         ocr_engine = OCREngine(cfg.get("valid_potentials"), cfg.get("ocr_settings", {}).get("score_cutoff"),bool(self.use_plus_two_var),use_high_level)
    #         if not ocr_engine.engine: self.log("错误: OCR 引擎初始化失败。"); return
    #
    #         win_manager = WindowManager(cfg.get("window_class", "MapleStoryClassSG"))
    #         self.log(f"等待游戏窗口 (类名: '{win_manager.window_class}')...")
    #         while not win_manager.is_window_active() and not self.stop_event.is_set(): time.sleep(1)
    #         if self.stop_event.is_set(): return
    #         self.log("成功找到游戏窗口。")
    #
    #         capture = Capture(win_manager, cfg.get("client_area_border_offsets"))
    #
    #
    #
    #
    #
    #         delay_after_click = cfg.get("delays").get("after_click")
    #         delay_after_enter = cfg.get("delays").get("after_enter")
    #
    #         input_controller = InputController(delay_after_click, delay_after_enter)
    #
    #         all_useable_stat  = cfg.get("all_use")
    #         if  keep_all_useable :
    #             self.log(f"目标属性: {all_useable_stat}")
    #         else:
    #            self.log(f"目标属性: {desired_stats}")
    #         self.log("--- 初始化完成, 3秒后开始 ---")
    #         time.sleep(3)
    #
    #         # --- 主循环 ---
    #         last_level_not_top = False
    #         attempt = 0
    #         while not self.stop_event.is_set():
    #             attempt += 1
    #
    #             self.log(f"--- 第 {attempt} 次尝试 ---")
    #             interval_var = int(self.interval_var.get()) / 1000
    #             if interval_var > 0 :
    #                 time.sleep(interval_var)
    #             else:
    #                 time.sleep(0.1)
    #
    #
    #             # 捕捉游戏客户区
    #             client_area_capture, client_origin = capture.capture_window_client_area()
    #             if client_area_capture is None:
    #                 self.log("警告: 无法捕捉窗口画面。")
    #                 time.sleep(1)
    #                 continue
    #
    #             if last_level_not_top:
    #                 last_level_not_top = False
    #                 input_controller.click(client_origin[0] + 100, client_origin[1] + 5)
    #                 time.sleep(0.1)
    #                 client_area_capture, client_origin = capture.capture_window_client_area()
    #                 if client_area_capture is None:
    #                     self.log("警告: 无法捕捉窗口画面。")
    #                     time.sleep(1)
    #                     continue
    #
    #             potential_loc, potential_size, potential_threshold = potential_matcher.find_match(client_area_capture)
    #             button_loc, button_size, button_threshold = button_matcher.find_match(client_area_capture)
    #             button_fail_loc, button_fail_size, button_fail_threshold = button_fail_matcher.find_match(
    #                 client_area_capture,True)
    #             button_fail = button_fail_threshold > button_threshold
    #
    #             # print(f"原始匹配置信度: 框体:{potential_threshold} 正常按钮:{button_threshold} 失败按钮:{button_fail_threshold}")
    #
    #             if  button_fail:
    #                 self.log("警告: 按钮无法点击，无剩余魔方或卡住")
    #                 time.sleep(2)
    #                 break
    #             # 如果任一模板匹配失败
    #
    #             if not potential_loc:
    #                 self.log("警告: 模板匹配失败。请检查装备窗口是否打开且未被遮挡。")
    #                 if show_image_var.get():
    #                     self.log("正在预览完整客户区截图以供调试...")
    #                     self.image_queue.put(client_area_capture)
    #                 time.sleep(2)
    #                 continue
    #             if not button_loc:
    #                 self.log("警告: 按钮模板匹配失败。请检查界面。")
    #                 if show_image_var.get():
    #                     self.log("正在预览截图以供调试...")
    #                     self.image_queue.put(client_area_capture)
    #                 time.sleep(2)
    #                 continue
    #
    #             # --- 模板匹配成功，继续流程 ---
    #             p_x, p_y = potential_loc
    #             p_w, p_h = potential_size
    #
    #             button_x, button_y = button_loc
    #             button_w, button_h = button_size
    #
    #             # 移动鼠标到潜能区域中心以供视觉确认
    #             # center_x_abs = client_origin[0] + p_x + p_w // 2
    #             # center_y_abs = client_origin[1] + p_y + p_h // 2
    #             # self.log(f"移动鼠标至潜能区域中心 ({center_x_abs}, {center_y_abs})")
    #             # input_controller.move_to(center_x_abs, center_y_abs)
    #
    #             potential_frame = client_area_capture[p_y: p_y + p_h, p_x: p_x + p_w]
    #             self.image_queue.put(potential_frame)
    #             if potential_frame.size == 0: self.log("警告: 裁剪后的潜能区域为空。"); continue
    #             if show_image_var.get(): self.image_queue.put(potential_frame.copy())
    #
    #
    #             recognized_lines = ocr_engine.get_text_from_image(potential_frame)
    #             self.log(f"识别结果: {recognized_lines}")
    #
    #             # self.log(f"测试再次使用");
    #             center_x_abs = client_origin[0] + button_x + button_w // 2
    #             center_y_abs = client_origin[1] + button_y + button_h // 2
    #             # print(f"client_origin: {client_origin[0]},{client_origin[1]}, center_abs: {center_x_abs},{center_y_abs}")
    #             # self.log(f"移动鼠标至按钮中心 ({center_x_abs}, {center_y_abs})")
    #             # input_controller.press_button_confirm(center_x_abs, center_y_abs)
    #
    #             if len(recognized_lines) < 2: self.log("警告: 未能识别到足够的潜能行。"); time.sleep(
    #                 cfg.get("delays").get("after_click")); continue
    #
    #             level_ok = recognized_lines[0].startswith("L")
    #
    #             if not level_ok:
    #                 last_level_not_top = True
    #                 self.log("警告: 等级未达到最高级")
    #                 time.sleep(0.1)
    #                 input_controller.press_button_confirm(center_x_abs, center_y_abs)
    #                 continue
    #             if keep_all_useable:
    #                 keep_result = False
    #                 curr_stat = []
    #                 for stat in all_useable_stat:
    #                     curr_stat = stat
    #                     result = self.validate_result([stat], recognized_lines[1:4], True)
    #                     if result:
    #                         keep_result = True
    #                         break
    #                 if keep_result:
    #                     self.log(f"成功! 找到所有目标属性: {curr_stat}")
    #                     break
    #             else:
    #                 result_check = self.validate_result(desired_stats, recognized_lines[1:4], match_two_lines)
    #                 if result_check:
    #                     self.log(f"成功! 找到所有目标属性: {desired_stats}");
    #                     break
    #             # 未找到 使用魔方
    #             if  not self.stop_event.is_set():
    #                 input_controller.press_button_confirm(center_x_abs, center_y_abs)
    #                 input_controller.click(client_origin[0] + 100,client_origin[1]+5)
    #             continue
    #
    #
    #
    #     except Exception as e:
    #         self.log(f"工作线程发生未知错误: {e}")
    #     finally:
    #         if 'capture' in locals() and capture: capture.release()
    #         self.after(0, self.on_worker_finished)

