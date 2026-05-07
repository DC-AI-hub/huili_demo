"""
列名语义映射器 — 从原 huili/惠理基金/src/etl_excel/column_mapper.py 迁移
根据打平后的列名，提取周期类型、规模类型、日期范围、指标角色等信息。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class ColumnMapping:
    source_column: str        # 原始列名
    period_type: str | None   # 周期类型（如 YTD / 1m / 1y）
    period_label: str | None  # 周期标签（列名首个下划线前缀）
    start_date: str | None    # 周期开始日期（ISO格式）
    end_date: str | None      # 周期结束日期（ISO格式）
    metric_kind: str | None   # 指标种类（如 return_cum / return_ann）
    value_role: str | None    # 值角色（value / peer_group_rank / peer_group_quartile / size_value）
    size_type: str | None     # 规模类型（daily / monthly）
    source_column_name: str   # 原始列名（冗余，便于溯源）


def _load_mapping_rules() -> Dict[str, Any]:
    """从同目录下的 mapping_rules.json 加载匹配规则"""
    rules_path = Path(__file__).with_name("mapping_rules.json")
    return json.loads(rules_path.read_text(encoding="utf-8"))


def _extract_dates(column_name: str, date_pattern: str) -> tuple[str | None, str | None]:
    """从列名中提取最多两个日期（start_date, end_date）"""
    matches = re.findall(date_pattern, column_name)
    if len(matches) >= 2:
        start = datetime.strptime(matches[-2], "%m/%d/%Y").date().isoformat()
        end = datetime.strptime(matches[-1], "%m/%d/%Y").date().isoformat()
        return start, end
    if len(matches) == 1:
        one = datetime.strptime(matches[0], "%m/%d/%Y").date().isoformat()
        return one, one
    return None, None


def parse_period_label(column_name: str) -> str | None:
    """提取列名第一个下划线前的周期标签（如 'YTD'）"""
    parts = column_name.split("_")
    if not parts:
        return None
    head = parts[0].strip()
    if head:
        return head
    return None


def map_column(column_name: str, rules: Dict[str, Any] | None = None) -> ColumnMapping:
    """
    对单个列名进行完整语义解析，返回 ColumnMapping 对象。
    解析优先级：metric_patterns > peer_patterns > size_patterns > period_patterns
    """
    rules = rules or _load_mapping_rules()
    metric_kind = None
    value_role = None
    size_type = None
    period_type = None
    period_label = parse_period_label(column_name)
    start_date = None
    end_date = None

    # 1. 匹配收益指标（Return Cumulative / Annualized）
    for kind, pattern in rules["metric_patterns"].items():
        if re.search(pattern, column_name):
            metric_kind = kind
            value_role = "value"
            break

    # 2. 匹配同类排名/四分位
    if metric_kind is None:
        for role, pattern in rules["peer_patterns"].items():
            if re.search(pattern, column_name):
                value_role = role
                break

    # 3. 匹配基金规模
    for size_kind, pattern in rules["size_patterns"].items():
        if re.search(pattern, column_name):
            size_type = size_kind
            value_role = "size_value"
            break

    # 4. 匹配周期类型（YTD / 1m / 1y / since inception）
    if period_label:
        for pattern in rules["period_patterns"]:
            if re.search(pattern, period_label):
                period_type = period_label
                break

    # 5. 提取日期区间
    try:
        start_date, end_date = _extract_dates(column_name, rules["date_pattern"])
    except ValueError:
        start_date, end_date = None, None

    return ColumnMapping(
        source_column=column_name,
        period_type=period_type,
        period_label=period_label if period_type else None,
        start_date=start_date,
        end_date=end_date,
        metric_kind=metric_kind,
        value_role=value_role,
        size_type=size_type,
        source_column_name=column_name,
    )
