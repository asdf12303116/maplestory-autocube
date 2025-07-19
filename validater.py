def validate_result(check_list, result_list, match_two_lines, use_2_use=False):
    """
    验证结果列表是否符合检测列表的要求

    参数:
    check_list (list): 包含2或3个元素的检测列表
    result_list (list): 包含3个元素的结果列表
    switch (bool): 控制验证逻辑的开关

    返回:
    bool: 结果列表是否符合要求
    """
    print(f"原始校验结果: {check_list},原始结果列表{result_list}")
    if match_two_lines:  # 开关开启时的逻辑
        # 检查第一个元素是否匹配检测列表的第一个元素
        if result_list[0] != check_list[0]:
            return False

        # 检查第二和第三个元素是否在检测列表中
        if use_2_use:
            return any(elem in check_list for elem in result_list[1:3])
        else:
            return all(elem in check_list for elem in result_list[1:3])


    else:  # 开关关闭时的逻辑
        # 检查所有元素是否都在检测列表中
        return all(elem in check_list for elem in result_list)


def validate_main_result(check_str, result_list, use_2_use=False):
    check_result = False
    if use_2_use:
        check_result = result_list.count(check_str) >= 2
    else:
        check_result = all(check_str == arr_str for arr_str in result_list)
    print(f"结果: {check_result} 目标属性: {check_str},结果列表{result_list}")
    return check_result