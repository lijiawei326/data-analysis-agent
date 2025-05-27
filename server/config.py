"""
排序配置文件
定义各种数据类型的自定义排序规则
"""

# 季节排序：春夏秋冬
SEASON_ORDER = ["春", "夏", "秋", "冬"]

# 月份排序（中文）
MONTH_ORDER_CN = ["一月", "二月", "三月", "四月", "五月", "六月", 
                  "七月", "八月", "九月", "十月", "十一月", "十二月"]

# 月份排序（数字）
MONTH_ORDER_NUM = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# 星期排序（中文）
WEEKDAY_ORDER_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
WEEKDAY_ORDER_CN_SHORT = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 风向排序（8个方向）
WIND_DIRECTION_ORDER = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]

# 时间段排序
TIME_PERIOD_ORDER = ["凌晨", "早晨", "上午", "中午", "下午", "傍晚", "晚上", "深夜"]

# 等级排序
LEVEL_ORDER = ["低", "中", "高"]
GRADE_ORDER = ["优", "良", "中", "差"]

# 大小排序
SIZE_ORDER = ["小", "中", "大"]

# 温度等级排序
TEMP_LEVEL_ORDER = ["严寒", "寒冷", "凉爽", "适宜", "温暖", "炎热", "酷热"]

# 主排序规则字典 - 将所有排序规则集中管理
SORT_RULES = {
    # 季节相关
    "季节": SEASON_ORDER,
    "season": SEASON_ORDER,
    
    # 月份相关
    "月份": MONTH_ORDER_CN,
    "month": MONTH_ORDER_NUM,
    "月": MONTH_ORDER_NUM,
    
    # 星期相关
    "星期": WEEKDAY_ORDER_CN,
    "周": WEEKDAY_ORDER_CN_SHORT,
    "weekday": WEEKDAY_ORDER_CN,
    
    # 风向相关
    "风向": WIND_DIRECTION_ORDER,
    "风向方位": WIND_DIRECTION_ORDER,
    "wind_direction": WIND_DIRECTION_ORDER,
    
    # 时间段相关
    "时间段": TIME_PERIOD_ORDER,
    "time_period": TIME_PERIOD_ORDER,
    
    # 等级相关
    "等级": LEVEL_ORDER,
    "级别": LEVEL_ORDER,
    "level": LEVEL_ORDER,
    "评级": GRADE_ORDER,
    "grade": GRADE_ORDER,
    
    # 大小相关
    "大小": SIZE_ORDER,
    "尺寸": SIZE_ORDER,
    "size": SIZE_ORDER,
    
    # 温度等级
    "温度等级": TEMP_LEVEL_ORDER,
    "气温等级": TEMP_LEVEL_ORDER,
    "temp_level": TEMP_LEVEL_ORDER,
}


def get_sort_order(column_name: str, values: list = None):
    """
    根据列名获取排序规则
    
    Args:
        column_name: 列名
        values: 实际的值列表，用于匹配最合适的排序规则
    
    Returns:
        排序规则列表，如果没有匹配则返回None
    """
    # 直接匹配列名
    if column_name in SORT_RULES:
        return SORT_RULES[column_name]
    
    # 如果提供了实际值，尝试智能匹配
    if values:
        unique_values = list(set(values))
        
        # 检查是否完全包含在某个排序规则中
        for rule_name, rule_order in SORT_RULES.items():
            if all(val in rule_order for val in unique_values if val is not None):
                return rule_order
        
        # 部分匹配 - 如果超过一半的值在排序规则中
        for rule_name, rule_order in SORT_RULES.items():
            match_count = sum(1 for val in unique_values if val in rule_order and val is not None)
            if len(unique_values) > 0 and match_count / len(unique_values) > 0.5:
                return rule_order
    
    return None


def custom_sort_key(value, sort_order):
    """
    生成自定义排序的key函数
    
    Args:
        value: 要排序的值
        sort_order: 排序规则列表
    
    Returns:
        排序key，不在规则中的值排在最后
    """
    if value in sort_order:
        return sort_order.index(value)
    else:
        return len(sort_order)  # 不在规则中的值排在最后
