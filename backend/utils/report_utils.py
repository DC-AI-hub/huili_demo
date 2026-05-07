import datetime
import calendar
import re

def calculate_delivery_deadline(frequency: str, rule: str, report_date: datetime.date) -> datetime.datetime:
    """
    根据给定的报表日期和配置规则，计算出交付日期 (delivery_deadline)。
    """
    rule = str(rule).lower()
    deadline = None
    
    # 基础 datetime 用报表日期的最后一秒
    base_datetime = datetime.datetime.combine(report_date, datetime.time(23, 59, 59))
    
    if frequency == 'Weekly':
        # 这里逻辑尽量与 scheduler_tasks.py 保持同步
        # 如果 report_date 是周五，则 deadline 为周五 18:00
        deadline = base_datetime.replace(hour=18, minute=0, second=0, microsecond=0)
        
    elif frequency == 'Monthly':
        # 交付日期为 T + N (自然天)
        # 匹配 T + 8 等格式
        match = re.search(r't\s*\+\s*(\d+)', rule)
        days_to_add = int(match.group(1)) if match else 0
        
        deadline = base_datetime + datetime.timedelta(days=days_to_add)
        
    elif frequency == 'Annually':
        # 年度报表通常为 23:59:59
        deadline = base_datetime
        
    elif frequency == 'Ad-Hoc':
        # 即时生成的报表交付时间定为当天最后
        deadline = base_datetime
        
    if deadline is None:
        deadline = base_datetime
        
    return deadline
