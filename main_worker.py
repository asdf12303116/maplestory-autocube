import time


from input_automation_controller import InputController
from ocr_text_correction_engine import OCREngine
from template_matcher import TemplateMatcher
from window_client_area_capture import Capture
from window_manager import WindowManager


def main_worker(main, desired_stats,show_image_var,keep_all_useable=False):
    """后台自动化工作线程。"""
    try:
        # --- 初始化 ---
        main.log("--- 初始化模块 ---")
        cfg = main.config_manager

        threshold = cfg.get("template_match_threshold")
        resolution = main.resolution.get()
        file_end = cfg.get("file_end")
        potential_matcher = TemplateMatcher(cfg.get("main_area_template_path_prefix") + resolution + file_end,
                                            threshold)
        button_matcher = TemplateMatcher(cfg.get("main_button_template_path_prefix") + resolution + file_end, threshold)
        button_fail_matcher = TemplateMatcher(cfg.get("main_button_fail_template_path_prefix") + resolution + file_end,
                                              threshold)
        main.log("模板匹配器已加载。")
        use_high_level = main.use_high_level.get() == 1
        print(f"use_high_level: {use_high_level}")
        ocr_engine = OCREngine(cfg.get("valid_potentials"), cfg.get("ocr_settings", {}).get("score_cutoff"),
                               bool(main.use_plus_two_var), use_high_level)
        if not ocr_engine.engine: main.log("错误: OCR 引擎初始化失败。"); return

        win_manager = WindowManager(cfg.get("window_class", "MapleStoryClassSG"))
        main.log(f"等待游戏窗口 (类名: '{win_manager.window_class}')...")
        while not win_manager.is_window_active() and not main.stop_event.is_set(): time.sleep(1)
        if main.stop_event.is_set(): return
        main.log("成功找到游戏窗口。")

        capture = Capture(win_manager, cfg.get("client_area_border_offsets"))

        delay_after_click = cfg.get("delays").get("after_click")
        delay_after_enter = cfg.get("delays").get("after_enter")

        input_controller = InputController(delay_after_click, delay_after_enter)
        mouse_move_arg = main.mouse_move_arg

        all_useable_stat = cfg.get("all_use")
        if keep_all_useable:
            main.log(f"目标属性: {all_useable_stat}")
        else:
            main.log(f"目标属性: {desired_stats}")
        main.log("--- 初始化完成, 3秒后开始 ---")
        time.sleep(3)

        # --- 主循环 ---
        last_level_not_top = False
        attempt = 0
        while not main.stop_event.is_set():
            attempt += 1

            main.log(f"--- 第 {attempt} 次尝试 ---")
            interval_var = int(main.interval_var.get()) / 1000
            if interval_var > 0:
                time.sleep(interval_var)
            else:
                time.sleep(0.1)

            # 捕捉游戏客户区
            client_area_capture, client_origin = capture.capture_window_client_area()
            if client_area_capture is None:
                main.log("警告: 无法捕捉窗口画面。")
                time.sleep(1)
                continue

            if last_level_not_top:
                last_level_not_top = False
                input_controller.click(client_origin[0] + mouse_move_arg[0], client_origin[1] + mouse_move_arg[1])
                time.sleep(0.1)
                client_area_capture, client_origin = capture.capture_window_client_area()
                if client_area_capture is None:
                    main.log("警告: 无法捕捉窗口画面。")
                    time.sleep(1)
                    continue
            # main.log(f"当前获取图像分辨率{client_origin[2] - client_origin[0]}x{client_origin[3] - client_origin[1]}")
            potential_loc, potential_size, potential_threshold = potential_matcher.find_match(client_area_capture)
            button_loc, button_size, button_threshold = button_matcher.find_match(client_area_capture)
            button_fail_loc, button_fail_size, button_fail_threshold = button_fail_matcher.find_match(
                client_area_capture, True)
            button_fail = button_fail_threshold > button_threshold

            # print(f"原始匹配置信度: 框体:{potential_threshold} 正常按钮:{button_threshold} 失败按钮:{button_fail_threshold}")

            if button_fail:
                main.log("警告: 按钮无法点击，无剩余魔方或卡住")
                time.sleep(2)
                break
            # 如果任一模板匹配失败

            if not potential_loc:
                main.log("警告: 模板匹配失败。请检查装备窗口是否打开且未被遮挡。")
                if show_image_var.get():
                    main.log("正在预览完整客户区截图以供调试...")
                    main.image_queue.put(client_area_capture)
                time.sleep(2)
                continue
            if not button_loc:
                main.log("警告: 按钮模板匹配失败。请检查界面。")
                if show_image_var.get():
                    main.log("正在预览截图以供调试...")
                    main.image_queue.put(client_area_capture)
                time.sleep(2)
                continue

            # --- 模板匹配成功，继续流程 ---
            p_x, p_y = potential_loc
            p_w, p_h = potential_size

            button_x, button_y = button_loc
            button_w, button_h = button_size

            # 移动鼠标到潜能区域中心以供视觉确认
            # center_x_abs = client_origin[0] + p_x + p_w // 2
            # center_y_abs = client_origin[1] + p_y + p_h // 2
            # main.log(f"移动鼠标至潜能区域中心 ({center_x_abs}, {center_y_abs})")
            # input_controller.move_to(center_x_abs, center_y_abs)

            potential_frame = client_area_capture[p_y: p_y + p_h, p_x: p_x + p_w]
            main.image_queue.put(potential_frame)
            if potential_frame.size == 0: main.log("警告: 裁剪后的潜能区域为空。"); continue
            if show_image_var.get(): main.image_queue.put(potential_frame.copy())

            recognized_lines = ocr_engine.get_text_from_image(potential_frame,'main')
            main.log(f"识别结果: {recognized_lines}")

            # main.log(f"测试再次使用");
            center_x_abs = client_origin[0] + button_x + button_w // 2
            center_y_abs = client_origin[1] + button_y + button_h // 2
            # print(f"client_origin: {client_origin[0]},{client_origin[1]}, center_abs: {center_x_abs},{center_y_abs}")
            # main.log(f"移动鼠标至按钮中心 ({center_x_abs}, {center_y_abs})")
            # input_controller.press_button_confirm(center_x_abs, center_y_abs)

            if len(recognized_lines) < 2: main.log("警告: 未能识别到足够的潜能行。"); time.sleep(
                cfg.get("delays").get("after_click")); continue

            level_ok = recognized_lines[0].startswith("L")

            if not level_ok:
                last_level_not_top = True
                main.log("警告: 等级未达到最高级")
                time.sleep(0.1)
                input_controller.press_button_confirm(center_x_abs, center_y_abs)
                continue

            result_check = all(desired_stats == arr_str for arr_str in recognized_lines)


            if result_check:
                main.log(f"成功! 找到目标属性: {desired_stats}");
                break
            # 未找到 使用魔方
            if not main.stop_event.is_set():
                input_controller.press_button_confirm(center_x_abs, center_y_abs)
                input_controller.click(client_origin[0] + mouse_move_arg[0], client_origin[1] + mouse_move_arg[1])
            continue



    except Exception as e:
        main.log(f"工作线程发生未知错误: {e}")
    finally:
        if 'capture' in locals() and capture: capture.release()
        main.after(0, main.on_worker_finished)